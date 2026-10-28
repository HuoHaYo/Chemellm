import math
import numpy as np
import pytest
from CoolProp.CoolProp import PropsSI
from app.calculations import calculate
from app.hydrogen import HydrogenThermo, CondenserInput, COMPONENTS
from app.reaction import gas_state, R

def test_hydrogen_water_unit_conversion_and_organic_prediction():
    model=HydrogenThermo(310,100000)
    hscp=7.8e-6*math.exp(530*(1/310-1/298.15))
    cwater=PropsSI("D","T",310,"P",100000,"Water")/.01801528
    assert model.henry[0]==pytest.approx(cwater/hscp,rel=1e-6)
    # Broad physical scale only; these organic values are PR predictions.
    assert all(1e8<h<3e8 for h in model.henry[1:])

def test_dilute_henry_mixture_obeys_gibbs_duhem_and_caloric_derivative():
    x=np.array([.025,.4,.5745,.0005])
    direction=np.array([.02,-.05,.0301,-.0001])
    model=HydrogenThermo(310,100000)
    step=1e-4
    derivative=(model.liquid_logf(x+step*direction)-model.liquid_logf(x-step*direction))/(2*step)
    assert abs(float(x@derivative))<1e-7
    dt=.003
    warm=HydrogenThermo(310+dt,100000)
    cool=HydrogenThermo(310-dt,100000)
    dchemical=(warm.liquid_logf(x)-cool.liquid_logf(x))/(2*dt)
    expected=sum(v*gas_state(name,310)[0] for name,v in zip(COMPONENTS,x))-R*310**2*float(x@dchemical)
    assert model.liquid_enthalpy(x)==pytest.approx(expected,abs=.01)

@pytest.mark.parametrize("pressure",[50000,100000,200000])
def test_hydrogen_condenser_independent_component_and_fugacity_closure(pressure):
    result=calculate("condenser_flash",{"pressure_Pa":pressure})
    assert result["validation"]["passed"]
    assert {p["phase"] for p in result["phases"]}=={"vapor","aqueous_liquid","organic_liquid"}
    for i in range(4):
        assert sum(p["component_flows_kmol_h"][i] for p in result["phases"])==pytest.approx(100*CondenserInput().mole_fractions[i],abs=1e-7)
        f=[p["component_fugacities_Pa"][i] for p in result["phases"]]
        assert max(f)==pytest.approx(min(f),rel=1e-6)
    liquid_h2=sum(p["component_flows_kmol_h"][3] for p in result["phases"] if p["phase"]!="vapor")
    assert 0<liquid_h2<.1
    organic=next(p for p in result["phases"] if p["phase"]=="organic_liquid")
    assert organic["component_flows_kmol_h"][0]>0

def test_reactor_condenser_links_all_components_and_common_enthalpy():
    result=calculate("frontend_process",{})
    assert result["validation"]["passed"]
    inlet,outlet=result["streams"][:2]
    exits=result["streams"][2:]
    for name in COMPONENTS:
        assert sum(s["component_flows_kmol_h"][name] for s in exits)==pytest.approx(outlet["component_flows_kmol_h"][name],abs=1e-7)
    assert sum(s["mass_kg_h"] for s in exits)==pytest.approx(inlet["mass_kg_h"],rel=1e-10)
    assert result["reactor_heat_input_kW"]==pytest.approx(outlet["enthalpy_flow_kW"]-inlet["enthalpy_flow_kW"],abs=1e-6)
    assert result["condenser_heat_removed_kW"]==pytest.approx(outlet["enthalpy_flow_kW"]-sum(s["enthalpy_flow_kW"] for s in exits),abs=1e-6)
    # Gas-sensible + condensation heat scale, not just an algebraic zero.
    assert 70000<result["condenser_heat_removed_kW"]<85000
    assert 11000<result["reactor_heat_input_kW"]<12500

@pytest.mark.parametrize("fractions,pressure,expected",[([.01,.045,.045,.9],100000,{"vapor","organic_liquid"}),
    ([.099,.0005,.0005,.9],100000,{"vapor","aqueous_liquid"}),([.08,.01,.01,.9],50000,{"vapor"})])
def test_fewer_phase_branches_do_not_create_a_spurious_phase(fractions,pressure,expected):
    result=calculate("condenser_flash",{"mole_fractions":fractions,"pressure_Pa":pressure})
    assert result["validation"]["passed"]
    assert {p["phase"] for p in result["phases"]}==expected
    for i in range(4):
        assert sum(p["component_flows_kmol_h"][i] for p in result["phases"])==pytest.approx(100*fractions[i],abs=1e-7)

def test_organic_hydrogen_sensitivity_changes_dissolution_without_losing_mass():
    low=calculate("condenser_flash",{"organic_henry_multiplier":.5})
    high=calculate("condenser_flash",{"organic_henry_multiplier":2})
    def organic_h2(r):return next(p["component_flows_kmol_h"][3] for p in r["phases"] if p["phase"]=="organic_liquid")
    assert organic_h2(low)>3*organic_h2(high)>0
    assert low["validation"]["passed"] and high["validation"]["passed"]

@pytest.mark.parametrize("tool,args",[("condenser_flash",{"temperature_K":298.15}),
    ("condenser_flash",{"pressure_Pa":1e6}),("condenser_flash",{"mole_fractions":[.8,.08,.12]}),
    ("condenser_flash",{"mole_fractions":[.8,.08,.119,.001]}),
    ("frontend_process",{"conversion":.99}),("frontend_process",{"conversion":.01})])
def test_refuses_unsupported_conditions_or_infeasible_reactor(tool,args):
    with pytest.raises(ValueError):calculate(tool,args)
