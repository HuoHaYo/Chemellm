import math
import pytest
from app.calculations import calculate


def test_distillation_matches_saturated_liquid_pinch():
    z,xd,xb,alpha=0.4,0.99,0.005,1.35
    result=calculate("distillation_shortcut",{})
    # Independent binary q=1 McCabe–Thiele minimum reflux, feed pinch at x=z.
    equilibrium_y=alpha*z/(1+(alpha-1)*z)
    minimum_reflux=(xd-equilibrium_y)/(equilibrium_y-z)
    assert result["minimum_reflux_ratio"]==pytest.approx(minimum_reflux)
    assert result["minimum_stages"]==pytest.approx(math.log(xd*(1-xb)/(xb*(1-xd)))/math.log(alpha))
    d,b=result["distillate_kmol_h"],result["bottoms_kmol_h"]
    assert d+b==pytest.approx(400)
    assert d*xd+b*xb==pytest.approx(400*z)
    assert result["theoretical_stages_including_reboiler"]>result["minimum_stages"]
    higher_reflux=calculate("distillation_shortcut",{"reflux_multiple":5})
    assert higher_reflux["theoretical_stages_including_reboiler"]<result["theoretical_stages_including_reboiler"]


@pytest.mark.parametrize("args",[{"relative_volatility":1},{"bottoms_light_fraction":0.5},{"feed_liquid_fraction":1.1}])
def test_distillation_rejects_invalid_design_basis(args):
    with pytest.raises(ValueError):
        calculate("distillation_shortcut",args)


def test_pipe_laminar_matches_hagen_poiseuille():
    args={"volume_flow_m3_h":0.001,"inner_diameter_m":0.01,"length_m":2,
          "roughness_m":0,"density_kg_m3":1000,"viscosity_Pa_s":0.001,
          "minor_loss_K":0,"elevation_rise_m":0}
    result=calculate("pipe_pressure_drop",args)
    q=args["volume_flow_m3_h"]/3600
    expected=128*args["viscosity_Pa_s"]*args["length_m"]*q/(math.pi*args["inner_diameter_m"]**4)
    assert result["regime"]=="laminar"
    assert result["friction_loss_Pa"]==pytest.approx(expected)
    assert result["shaft_power_kW"]==pytest.approx(expected*q/0.7/1000)


def test_pipe_transition_and_roughness_rejected():
    with pytest.raises(ValueError,match="过渡区"):
        calculate("pipe_pressure_drop",{"volume_flow_m3_h":0.08482300164692443,"inner_diameter_m":0.01,"density_kg_m3":1000,"viscosity_Pa_s":.001})
    with pytest.raises(ValueError,match="粗糙度"):
        calculate("pipe_pressure_drop",{"inner_diameter_m":.01,"roughness_m":.01})


def test_pinch_recovery_and_thermally_separated_streams():
    hot={"name":"H1","kind":"hot","supply_C":180,"target_C":40,"heat_capacity_flow_kW_K":2}
    cold={"name":"C1","kind":"cold","supply_C":20,"target_C":160,"heat_capacity_flow_kW_K":1}
    result=calculate("pinch_analysis",{"streams":[hot,cold],"delta_T_min_K":20})
    assert result["minimum_hot_utility_kW"]==0
    assert result["minimum_cold_utility_kW"]==140
    assert result["maximum_heat_recovery_kW"]==140
    # No heat recovery possible if the cold stream is entirely hotter than the hot stream.
    hot.update(supply_C=60,target_C=40)
    cold.update(supply_C=100,target_C=120)
    separated=calculate("pinch_analysis",{"streams":[hot,cold]})
    assert separated["minimum_hot_utility_kW"]==20
    assert separated["minimum_cold_utility_kW"]==40
    assert separated["maximum_heat_recovery_kW"]==0
    assert separated["validation"]["passed"]
    assert min(interval["cascade_out_kW"] for interval in separated["intervals"])>=0


def test_high_temperature_properties_are_not_extrapolated(project_id):
    result=calculate("properties",{"compound":"styrene","temperature_K":873.15})
    assert result["properties"]["liquid_density"]["value"] is None
    assert result["properties"]["liquid_Cp"]["value"] is None
    assert result["properties"]["vapor_pressure"]["value"] is None
    assert result["properties"]["MW"]["value"]>100
    assert not result["correlations"]["VaporPressure"]["within_temperature_range"]
