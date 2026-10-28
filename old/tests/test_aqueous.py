import math
import pytest
from thermo import Chemical
from app.calculations import calculate

@pytest.mark.parametrize("temperature,pressure,expected",[(310,101325,"LL"),(360,80000,"VLL"),(400,101325,"V")])
def test_ternary_flash_preserves_components_and_phase_fugacity(temperature,pressure,expected):
    r=calculate("aqueous_flash",{"temperature_K":temperature,"pressure_Pa":pressure})
    assert r["phase"]==expected
    assert r["validation"]["passed"]
    for i,name in enumerate(r["components"]):
        assert sum(phase["component_flows_kmol_h"][i] for phase in r["phases"])==pytest.approx(100*[.8,.08,.12][i],abs=1e-7)
        fugacities=[]
        for phase in r["phases"]:
            x=phase["mole_fractions"][i]
            if phase["phase"]=="vapor":
                fugacities.append(x*pressure)
            else:
                fugacities.append(x*phase["activity_coefficients"][i]*Chemical(name,T=temperature).Psat)
        assert max(fugacities)==pytest.approx(min(fugacities),rel=1e-5)
    assert sum(phase["flow_kmol_h"] for phase in r["phases"])==pytest.approx(100)
    if expected=="LL":
        aqueous=next(phase for phase in r["phases"] if phase["phase"]=="aqueous_liquid")
        organic=next(phase for phase in r["phases"] if phase["phase"]=="organic_liquid")
        assert aqueous["component_flows_kmol_h"][1]>0
        assert aqueous["component_flows_kmol_h"][2]>0
        assert 0<organic["mole_fractions"][0]<.1

@pytest.mark.parametrize("args",[{"mole_fractions":[.8,.2]}, {"mole_fractions":[.8,.1,.2]},
    {"mole_fractions":[1.,0.,0.]},{"mole_fractions":[.8,.1,math.nan]},
    {"temperature_K":500},{"compounds":["water","ethylbenzene","hydrogen"]}])
def test_ternary_model_rejects_invalid_or_unsupported_feed(args):
    with pytest.raises(ValueError):
        calculate("aqueous_flash",args)
