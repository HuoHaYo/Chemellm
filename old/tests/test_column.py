import pytest
from thermo import Chemical
from app.calculations import calculate

def test_column_component_balances_and_raoult_independently():
    p={"equilibrium_stages":8,"feed_stage":4,"feed_kmol_h":100,"reflux_ratio":3,"distillate_fraction":0.5}
    r=calculate("column_mesh",p)
    assert r["validation"]["passed"]
    stages=r["stages"]
    d,b=r["distillate_kmol_h"],r["bottoms_kmol_h"]
    assert d+b==pytest.approx(100)
    assert d*r["distillate_light_fraction"]+b*r["bottoms_light_fraction"]==pytest.approx(50,abs=1e-6)
    assert r["distillate_light_fraction"]>0.85
    assert r["bottoms_light_fraction"]<0.15
    chemicals=[Chemical("benzene"),Chemical("toluene")]
    for j,stage in enumerate(stages):
        x,y,t=stage["liquid_light_fraction"],stage["vapor_light_fraction"],stage["temperature_K"]
        p1,p2=[c.VaporPressure(t) for c in chemicals]
        assert x*p1+(1-x)*p2==pytest.approx(101325,abs=1e-5)
        assert y==pytest.approx(x*p1/101325,abs=1e-8)
        lin=stages[j-1]["liquid_kmol_h"] if j else 3*d
        xin=stages[j-1]["liquid_light_fraction"] if j else r["distillate_light_fraction"]
        vin=stages[j+1]["vapor_kmol_h"] if j+1<len(stages) else 0
        yin=stages[j+1]["vapor_light_fraction"] if j+1<len(stages) else 0
        feed=100 if stage["feed"] else 0
        assert lin+vin+feed==pytest.approx(stage["liquid_kmol_h"]+stage["vapor_kmol_h"],abs=1e-6)
        assert lin*xin+vin*yin+feed*.5==pytest.approx(stage["liquid_kmol_h"]*x+stage["vapor_kmol_h"]*y,abs=1e-6)
    assert r["condenser_duty_removed_kW"]>0 and r["reboiler_duty_kW"]>0
    assert abs(r["validation"]["global_energy_residual_kW"])<1e-5

def test_vacuum_styrene_column_sparse_solver():
    r=calculate("column_mesh",{"light_component":"乙苯","heavy_component":"苯乙烯",
        "feed_light_fraction":0.4,"equilibrium_stages":50,"feed_stage":25,"pressure_Pa":20000,
        "distillate_fraction":0.4,"reflux_ratio":10})
    assert r["validation"]["passed"]
    assert r["distillate_light_fraction"]>0.98
    assert r["bottoms_light_fraction"]<0.01
    assert all(303<s["temperature_K"]<420 for s in r["stages"])
    assert len(r["stages"])==50
    assert r["stages"][-1]["role"]=="partial_reboiler"

@pytest.mark.parametrize("args",[
    {"feed_stage":10,"equilibrium_stages":10},
    {"light_component":"styrene","heavy_component":"ethylbenzene"},
    {"light_component":"methanol"},
    {"light_component":"ethylbenzene","heavy_component":"styrene","pressure_Pa":1000},
])
def test_column_refuses_invalid_basis_or_property_extrapolation(args):
    with pytest.raises(ValueError):
        calculate("column_mesh",args)

def test_thermodynamic_table_refuses_unavailable_bubble_point():
    from app.column import BinaryThermo
    with pytest.raises(ValueError,match="温度范围"):
        BinaryThermo("ethylbenzene","styrene",1000)
