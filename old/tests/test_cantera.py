"""Gas-backend qualification, native files and numerical replay boundaries."""
import hashlib
import io
import json
import subprocess
import sys
import zipfile
from copy import deepcopy

import cantera as ct
import pytest
from pydantic import ValidationError

from app.cantera_backend import GasEquilibriumInput, GasReactorInput, isolated, solve
from app.db import one
from scripts.cantera_benchmark import evaluate
from scripts.replay import compare_result


WGS={"mechanism":"wgs4","constraint":"TP","temperature_K":1000,
     "pressure_Pa":101325,"composition":{"CO":1,"H2O":1,"CO2":.1,"H2":.1}}


def test_external_thermodynamic_and_analytic_protocol():
    report=evaluate()
    assert report["passed"]
    assert len(report["thermodynamic_cases"])==3
    assert len(report["analytic_cases"])==4
    assert all(row["passed"] for row in report["thermodynamic_cases"]+report["analytic_cases"])
    assert report["limitations"]


@pytest.mark.parametrize("constraint",["TP","HP"])
def test_wgs_equilibrium_constraints_and_native_model(constraint,tmp_path):
    p=GasEquilibriumInput(**{**WGS,"constraint":constraint})
    result=solve("equilibrium",p)
    assert result["validation"]["passed"]
    initial,final=result["initial"],result["final"]
    assert final["pressure_Pa"]==pytest.approx(p.pressure_Pa,rel=1e-10)
    if constraint=="TP":
        assert final["temperature_K"]==pytest.approx(1000)
        # Frozen independent NIST-Shomate calculation, with protocol tolerance.
        extent=final["mole_fractions"]["CO2"]*2.2-.1
        assert abs(extent-.49985446631884356)<.0075
    else:
        assert final["temperature_K"]>initial["temperature_K"]
        assert final["enthalpy_J_kg"]==pytest.approx(initial["enthalpy_J_kg"],rel=2e-7)
    assert set(final["mole_fractions"])=={"CO","H2O","CO2","H2"}
    assert result["reaction_count"]==0  # Thermodynamics, not a kinetic mechanism.
    model=tmp_path/"mechanism.yaml"
    model.write_bytes(result["native_model_yaml"].encode("utf-8"))
    native=ct.Solution(str(model))
    assert native.n_species==4 and native.n_reactions==0
    assert native.T==pytest.approx(p.temperature_K)
    assert hashlib.sha256(model.read_bytes()).hexdigest()==result["native_model_sha256"]
    assert solve("equilibrium",p)["native_model_sha256"]==result["native_model_sha256"]


def test_full_gri30_retains_its_additional_species_and_reactions():
    result=solve("equilibrium",GasEquilibriumInput(**{**WGS,"mechanism":"gri30"}))
    assert result["validation"]["passed"]
    assert result["species_count"]==53 and result["reaction_count"]==325
    assert result["final"]["mole_fractions"]["CH4"]>1e-8
    assert result["source_mechanism"]["filename"]=="gri30.yaml"


@pytest.mark.parametrize("constraint",["constant_pressure","constant_volume"])
@pytest.mark.parametrize("energy",["adiabatic","isothermal"])
def test_hydrogen_reactor_closed_mass_energy_and_endpoints(constraint,energy):
    p=GasReactorInput(constraint=constraint,energy=energy,samples=24)
    result=solve("reactor",p)
    assert result["validation"]["passed"]
    trajectory=result["trajectory"]
    assert len(trajectory)==25 and trajectory[0]["time_s"]==0
    assert trajectory[-1]["time_s"]==pytest.approx(p.end_time_s)
    assert all(a["time_s"]<b["time_s"] for a,b in zip(trajectory,trajectory[1:]))
    initial=trajectory[0]
    initial_mass=initial["density_kg_m3"]*initial["volume_m3"]
    energy_key="enthalpy_J_kg" if constraint=="constant_pressure" else "internal_energy_J_kg"
    for row in trajectory:
        assert row["density_kg_m3"]*row["volume_m3"]==pytest.approx(initial_mass,rel=1e-8)
        assert sum(row["mole_fractions"].values())==pytest.approx(1,abs=1e-10)
        assert min(row["mole_fractions"].values())>=-1e-10
        if constraint=="constant_pressure":assert row["pressure_Pa"]==pytest.approx(p.pressure_Pa,rel=1e-8)
        else:assert row["volume_m3"]==pytest.approx(1,abs=1e-10)
        if energy=="isothermal":assert row["temperature_K"]==pytest.approx(p.temperature_K,abs=1e-8)
        else:assert row[energy_key]==pytest.approx(initial[energy_key],rel=2e-7)
    assert result["final"]["mole_fractions"]["H2"]<result["initial"]["mole_fractions"]["H2"]
    assert "not equilibrium" in result["sampling_note"]


@pytest.mark.parametrize("values",[
    {"mechanism":"../../custom"},
    {"mechanism":"wgs4"},
    {"composition":{"H2":-1}},
    {"composition":{"H2":0}},
    {"composition":{"H2":float("nan")}},
    {"end_time_s":11},
    {"samples":601},
])
def test_invalid_kinetic_inputs_rejected(values):
    with pytest.raises(ValidationError):GasReactorInput(**values)


def test_unknown_species_and_missing_or_timed_out_worker(monkeypatch):
    with pytest.raises(ValueError,match="不存在"):
        isolated("equilibrium",GasEquilibriumInput(composition={"fictional":1}))
    monkeypatch.setattr("app.cantera_backend.importlib.util.find_spec",lambda name:None)
    with pytest.raises(ValueError,match="未安装"):
        isolated("equilibrium",GasEquilibriumInput())
    monkeypatch.setattr("app.cantera_backend.importlib.util.find_spec",lambda name:True)
    def timeout(*args,**kwargs):
        assert kwargs["timeout"]==60
        raise subprocess.TimeoutExpired(args[0],60)
    monkeypatch.setattr("app.cantera_backend.subprocess.run",timeout)
    with pytest.raises(ValueError,match="60秒"):
        isolated("reactor",GasReactorInput())


def test_packaged_mechanism_is_not_shadowed_by_working_directory(tmp_path,monkeypatch):
    (tmp_path/"h2o2.yaml").write_text("not a valid mechanism",encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result=solve("equilibrium",GasEquilibriumInput())
    assert result["validation"]["passed"] and result["species_count"]==10
    assert result["source_mechanism"]["filename"]=="h2o2.yaml"


@pytest.mark.parametrize("tool,arguments",[("cantera_equilibrium",WGS),("cantera_reactor",{"samples":24})])
def test_http_artifacts_and_standalone_replay(client,project_id,tmp_path,tool,arguments):
    response=client.post(f"/api/projects/{project_id}/tools/{tool}",json={"arguments":arguments})
    assert response.status_code==200,response.text
    result=response.json()
    assert result["validation"]["passed"]
    assert "native_model_yaml" not in result
    files={item["name"]:item for item in result["artifacts"]}
    for item in files.values():
        content=client.get(item["download_url"]).content
        assert hashlib.sha256(content).hexdigest()==item["metadata"]["sha256"]
    native=client.get(files["cantera-native-study.zip"]["download_url"]).content
    with zipfile.ZipFile(io.BytesIO(native)) as archive:
        assert {"mechanism.yaml","simulation.py","input.json","result.json","LICENSE-Cantera.txt"}<=set(archive.namelist())
        archive.extractall(tmp_path)
    assert hashlib.sha256((tmp_path/"mechanism.yaml").read_bytes()).hexdigest()==result["native_model_sha256"]
    original_model=(tmp_path/"mechanism.yaml").read_bytes()
    source=tmp_path/("source-"+result["source_mechanism"]["filename"])
    assert hashlib.sha256(source.read_bytes()).hexdigest()==result["source_mechanism"]["sha256"]
    assert "Redistribution" in (tmp_path/"LICENSE-Cantera.txt").read_text(encoding="utf-8")
    if tool=="cantera_reactor":
        svg=client.get(files["reactor-profile.svg"]["preview_url"])
        assert svg.status_code==200 and "<svg" in svg.text
        assert client.get(files["reactor-profile.pdf"]["download_url"]).content.startswith(b"%PDF")
        assert len((tmp_path/"trajectory.csv").read_text(encoding="utf-8-sig").splitlines())==26
    proc=subprocess.run([sys.executable,"-X","utf8","simulation.py"],cwd=tmp_path,
                        capture_output=True,text=True,encoding="utf-8",timeout=30)
    assert proc.returncode==0,proc.stdout+proc.stderr
    replay=json.loads((tmp_path/"native-replay-results.json").read_text())
    assert replay["passed"] and replay["checks"]["native_model_sha256"] and replay["checks"]["source_mechanism_sha256"]
    # A harmless YAML comment still invalidates the archived model's integrity.
    with (tmp_path/"mechanism.yaml").open("ab") as stream:stream.write(b"\n# altered after export\n")
    proc=subprocess.run([sys.executable,"-X","utf8","simulation.py"],cwd=tmp_path,
                        capture_output=True,text=True,encoding="utf-8",timeout=30)
    assert proc.returncode==1,proc.stdout+proc.stderr
    replay=json.loads((tmp_path/"native-replay-results.json").read_text())
    assert not replay["checks"]["native_model_sha256"]
    (tmp_path/"mechanism.yaml").write_bytes(original_model)
    with source.open("ab") as stream:stream.write(b"\n# altered distribution source\n")
    proc=subprocess.run([sys.executable,"-X","utf8","simulation.py"],cwd=tmp_path,
                        capture_output=True,text=True,encoding="utf-8",timeout=30)
    assert proc.returncode==1,proc.stdout+proc.stderr
    replay=json.loads((tmp_path/"native-replay-results.json").read_text())
    assert replay["checks"]["native_model_sha256"] and not replay["checks"]["source_mechanism_sha256"]


def test_http_invalid_species_creates_no_success_record(client,project_id):
    response=client.post(f"/api/projects/{project_id}/tools/cantera_equilibrium",
                         json={"arguments":{**WGS,"composition":{"CO":1,"CH4":1}}})
    assert response.status_code==422 and "CH4" in response.json()["detail"]
    assert one("SELECT COUNT(*) AS n FROM calculations WHERE project_id=?",(project_id,))["n"]==0
    assert one("SELECT COUNT(*) AS n FROM artifacts WHERE project_id=?",(project_id,))["n"]==0


def test_generic_bundle_replays_gas_calculation(client,project_id,tmp_path):
    for tool,arguments in [("cantera_equilibrium",WGS),("cantera_reactor",{"samples":24})]:
        response=client.post(f"/api/projects/{project_id}/tools/{tool}",json={"arguments":arguments})
        assert response.status_code==200,response.text
    bundle=client.post(f"/api/projects/{project_id}/bundle").json()
    with zipfile.ZipFile(io.BytesIO(client.get(bundle["download_url"]).content)) as archive:
        archive.extractall(tmp_path)
    proc=subprocess.run([sys.executable,"-X","utf8","replay.py"],cwd=tmp_path/"reproduce",
                        capture_output=True,text=True,encoding="utf-8",timeout=60)
    assert proc.returncode==0,proc.stdout+proc.stderr
    output=json.loads((tmp_path/"reproduce/replay-results.json").read_text(encoding="utf-8"))
    assert len(output["results"])==2 and all(row["reproduced"] for row in output["results"])


def test_gas_replay_preserves_trajectory_and_rejects_failed_validation():
    reference=solve("reactor",GasReactorInput(samples=20))
    actual=deepcopy(reference)
    actual["solver"]["stats"]={"steps":999}
    assert compare_result("cantera_reactor",actual,reference)
    actual["trajectory"][5]["temperature_K"]+=1
    assert not compare_result("cantera_reactor",actual,reference)
    actual=deepcopy(reference);actual["validation"]["passed"]=False
    assert not compare_result("cantera_reactor",actual,reference)
