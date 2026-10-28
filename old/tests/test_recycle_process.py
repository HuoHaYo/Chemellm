import numpy as np
import pytest
from app.calculations import calculate
from app.hydrogen import COMPONENTS


def test_actual_recycle_closes_components_energy_and_purity_mass_basis():
    r=calculate("recycle_process",{})
    assert r["validation"]["passed"]
    feeds=[s for s in r["streams"] if s["boundary"]=="feed"]
    exits=[s for s in r["streams"] if s["boundary"]=="outlet"]
    assert len(feeds)==2 and len(exits)==6
    inlet=sum((np.array([s["component_flows_kmol_h"][k] for k in COMPONENTS]) for s in feeds),start=np.zeros(4))
    outlet=sum((np.array([s["component_flows_kmol_h"][k] for k in COMPONENTS]) for s in exits),start=np.zeros(4))
    assert outlet-inlet==pytest.approx(r["reaction_extent_kmol_h"]*np.array([0.,-1.,1.,1.]),abs=1e-6)
    assert sum(s["mass_kg_h"] for s in exits)==pytest.approx(sum(s["mass_kg_h"] for s in feeds),rel=1e-9)
    ext_h_in=sum(s["enthalpy_flow_kW"] for s in feeds)
    ext_h_out=sum(s["enthalpy_flow_kW"] for s in exits)
    assert ext_h_in+r["total_heat_input_kW"]+r["recycle_pump_work_kW"]-r["total_heat_removed_kW"]==pytest.approx(ext_h_out,abs=1e-5)
    distillate=next(s for s in r["column"]["outlets"] if s["outlet"]=="organic_distillate")
    recycled=np.array([r["recycle_component_kmol_h"][k] for k in COMPONENTS])
    assert recycled==pytest.approx(.99*np.array([distillate["component_flows_kmol_h"][k] for k in COMPONENTS]),abs=1e-6)
    assert all(recycled>0)
    reactor_in=np.array([r["reactor"]["inlet_kmol_h"][k] for k in COMPONENTS])
    assert reactor_in==pytest.approx(inlet+recycled,abs=1e-8)
    assert reactor_in[0]/reactor_in[1]==pytest.approx(8.)
    # Sum reported component masses independently, including EB impurity.
    bottom=next(s for s in r["streams"] if s["id"]=="S09")
    expected=bottom["component_flows_kmol_h"]["styrene"]*104.14912/bottom["mass_kg_h"]
    assert r["product_specification"]["predicted_styrene_mass_fraction"]==pytest.approx(expected,abs=1e-7)
    assert r["product_specification"]["meets_assumed_purity_target"] is True
    assert .99<expected<1
    assert 20000<r["feed_conditioning_heat_kW"]<40000
    assert 0<r["recycle_pump_work_kW"]<5


def test_full_purge_removes_recycle_but_keeps_cold_feed_conditioning():
    r=calculate("recycle_process",{"recycle_purge_fraction":1,"column_stages":6,"column_feed_stage":3,"column_reflux_ratio":3})
    assert r["validation"]["passed"]
    assert all(v==0 for v in r["recycle_component_kmol_h"].values())
    assert r["recycle_pump_work_kW"]==0
    assert r["feed_conditioning_heat_kW"]>10000
    assert r["product_specification"]["meets_assumed_purity_target"] is False


@pytest.mark.parametrize("args",[{"recycle_purge_fraction":0},{"recycle_pump_efficiency":0},
    {"column_pressure_Pa":80000,"pressure_Pa":50000},{"target_styrene_mass_fraction":1}])
def test_recycle_rejects_unsupported_specifications(args):
    with pytest.raises(ValueError):calculate("recycle_process",args)
