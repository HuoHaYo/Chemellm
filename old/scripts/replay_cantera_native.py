"""Standalone native Cantera replay. Put next to input.json/mechanism.yaml/result.json."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import cantera as ct
import numpy as np


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--directory",type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args();folder=args.directory
    request=json.loads((folder/"input.json").read_text(encoding="utf-8"))
    reference=json.loads((folder/"result.json").read_text(encoding="utf-8"))
    if ct.__version__!=reference["backend_version"]:
        raise ValueError("Cantera version differs from recorded version")
    model=folder/"mechanism.yaml"
    model_hash=hashlib.sha256(model.read_bytes()).hexdigest()
    source=reference["source_mechanism"]
    source_hash=hashlib.sha256((folder/("source-"+source["filename"])).read_bytes()).hexdigest()
    gas=ct.Solution(str(model))
    p=request["arguments"]
    gas.TPX=p["temperature_K"],p["pressure_Pa"],p["composition"]
    trajectory=[]
    if request["tool"]=="cantera_equilibrium":
        gas.equilibrate(p["constraint"],solver="gibbs",rtol=1e-10,max_steps=1000)
    else:
        cls=ct.IdealGasConstPressureReactor if p["constraint"]=="constant_pressure" else ct.IdealGasReactor
        reactor=cls(gas,volume=1.,energy="on" if p["energy"]=="adiabatic" else "off",clone=False)
        network=ct.ReactorNet([reactor]);network.rtol=1e-10;network.atol=1e-18;network.max_steps=20000
        times=np.concatenate(([0.],np.geomspace(p["end_time_s"]*1e-7,p["end_time_s"],p["samples"])))
        for t in times:
            if t>0:network.advance(float(t))
            trajectory.append([float(network.time),float(gas.T),float(gas.P),*gas.X.tolist()])
        with (folder/"replayed-trajectory.csv").open("w",encoding="utf-8",newline="") as stream:
            writer=csv.writer(stream);writer.writerow(["time_s","temperature_K","pressure_Pa",*gas.species_names]);writer.writerows(trajectory)
    actual={"temperature_K":float(gas.T),"pressure_Pa":float(gas.P),"density_kg_m3":float(gas.density),
            "enthalpy_J_kg":float(gas.enthalpy_mass),"internal_energy_J_kg":float(gas.int_energy_mass),
            "mean_molecular_weight_kg_kmol":float(gas.mean_molecular_weight),"mole_fractions":dict(zip(gas.species_names,gas.X.tolist()))}
    def close(a,b):
        if isinstance(a,dict):return a.keys()==b.keys() and all(close(a[k],b[k]) for k in a)
        return math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-8)
    checks={"native_model_sha256":model_hash==reference["native_model_sha256"],
            "source_mechanism_sha256":source_hash==source["sha256"],
            "recorded_numerical_validation":reference["validation"]["passed"] is True,
            "final_state":close(actual,reference["final"])}
    if trajectory:
        expected=reference["trajectory"]
        checks["trajectory"]=len(expected)==len(trajectory) and all(
            close(dict(time_s=row[0],temperature_K=row[1],pressure_Pa=row[2],**dict(zip(gas.species_names,row[3:]))),
                  dict(time_s=entry["time_s"],temperature_K=entry["temperature_K"],pressure_Pa=entry["pressure_Pa"],**entry["mole_fractions"]))
            for row,entry in zip(trajectory,expected))
    output={"passed":all(checks.values()),"checks":checks,"final":actual,"cantera_version":ct.__version__,
            "scope":"native YAML replay against stored numerical result; not independent physical validation"}
    (folder/"native-replay-results.json").write_text(json.dumps(output,indent=2),encoding="utf-8")
    print(json.dumps({"passed":output["passed"],"checks":checks}))
    return 0 if output["passed"] else 1


if __name__=="__main__":raise SystemExit(main())
