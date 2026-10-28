import math
import pytest
from app.calculations import calculate

def test_units_and_offset_temperature():
    assert calculate("convert_units",{"value":1,"from_unit":"bar","to_unit":"Pa"})["value"]==100000
    assert calculate("convert_units",{"value":0,"from_unit":"degC","to_unit":"K"})["value"]==pytest.approx(273.15)
    with pytest.raises(Exception):
        calculate("convert_units",{"value":1,"from_unit":"kg","to_unit":"K"})

def test_recycle_limits_and_independent_stoichiometry():
    once=calculate("material_balance",{"conversion":0.5,"ethylbenzene_recovery":0})
    closed=calculate("material_balance",{"conversion":0.5,"ethylbenzene_recovery":1,"recycle_purge":0})
    assert once["streams"]["fresh_ethylbenzene_kg_h"]==pytest.approx(2*closed["streams"]["fresh_ethylbenzene_kg_h"])
    s=closed["streams"]
    assert s["fresh_ethylbenzene_kg_h"]==pytest.approx(s["styrene_kg_h"]+s["hydrogen_kg_h"])
    assert s["styrene_kg_h"]/104.14912==pytest.approx(s["hydrogen_kg_h"]/2.01588,rel=1e-5)
    assert once["validation"]["passed"] and closed["validation"]["passed"]

@pytest.mark.parametrize("args",[{"conversion":0},{"operating_hours":9000},{"product_t_per_year":float("nan")}])
def test_invalid_balance_inputs(args):
    with pytest.raises(ValueError):
        calculate("material_balance",args)

def test_lmtd_equal_end_temperatures_and_crossing():
    result=calculate("heat_exchanger",{})
    assert result["LMTD_K"]==90
    assert result["area_m2"]==pytest.approx(5000000/(500*.9*90))
    with pytest.raises(ValueError):
        calculate("heat_exchanger",{"cold_out_C":200})

def test_steam_reference_at_one_atmosphere():
    result=calculate("steam",{"pressure_Pa":101325,"quality":1})
    assert result["temperature_K"]==pytest.approx(373.124,abs=.02)
    assert result["enthalpy_J_kg"]==pytest.approx(2675500,rel=.001)

def test_flash_conservation_and_volatility():
    r=calculate("flash",{})
    assert 0<r["vapor_fraction"]<1
    assert r["vapor_mole_fractions"][0]>r["liquid_mole_fractions"][0]
    for x,y in zip(r["liquid_mole_fractions"],r["vapor_mole_fractions"]):
        assert (1-r["vapor_fraction"])*x+r["vapor_fraction"]*y==pytest.approx(.5,abs=1e-8)
    with pytest.raises(ValueError):
        calculate("flash",{"mole_fractions":[.5,.6]})

def test_economic_analytical_zero_discount():
    r=calculate("economics",{"capital_CNY":100,"annual_revenue_CNY":20,"annual_cost_CNY":10,"years":10,"discount_rate":0})
    assert r["NPV_CNY"]==0
    assert r["simple_payback_years"]==10

def test_styrene_identity_and_source(project_id):
    r=calculate("properties",{"compound":"苯乙烯"})
    assert r["CAS"]=="100-42-5"
    assert r["properties"]["MW"]["value"]==pytest.approx(104.15,abs=.01)
    assert r["correlations"]["VaporPressure"]["method"]

def test_reaction_reference_heat_and_entropy():
    from app.reaction import thermodynamics,tabular_integrals
    r=thermodynamics(298.15)
    assert r["delta_H_J_mol"]==pytest.approx(117100)
    assert r["delta_S_J_mol_K"]==pytest.approx(115.18)
    assert tabular_integrals("styrene",298.15)==(0,0)
    # Independently integrate the single linear table interval 300–400 K.
    h400,_=tabular_integrals("styrene",400)
    h300,_=tabular_integrals("styrene",300)
    assert h400-h300==pytest.approx((120.94+159.79)*100/2)
    with pytest.raises(ValueError):
        tabular_integrals("styrene",1600)

def test_reaction_equilibrium_trends_and_heat_balance():
    from app.reaction import equilibrium_conversion
    base=equilibrium_conversion(873.15,100000,8)
    assert equilibrium_conversion(900,100000,8)>base
    assert equilibrium_conversion(873.15,200000,8)<base
    assert equilibrium_conversion(873.15,100000,12)>base
    r=calculate("reaction_thermo",{"conversion":0.1})
    assert r["validation"]["passed"]
    assert r["heat_duty_kW"]==pytest.approx(r["reaction_heat_kW"]+r["sensible_heat_kW"])
    impossible=calculate("reaction_thermo",{"conversion":0.999,"reactor_temperature_K":500})
    assert not impossible["equilibrium_feasible"]
    assert not impossible["validation"]["passed"]
