"""Certified external results and statistical/units failure modes."""
import math

import pytest
from pydantic import ValidationError

from app.benchmarks import CASES, TOLERANCES, reference_case
from app.experimental import FitInput, fit_data


@pytest.mark.parametrize("name", CASES)
def test_nist_certified_numerical_regression(name):
    reference = reference_case(name)
    result = fit_data(FitInput(x=reference["x"], y=reference["y"], model=reference["model"]))
    assert [p["value"] for p in result["parameters"]] == pytest.approx(reference["certified_parameters"], rel=TOLERANCES["parameter_relative"])
    assert [p["standard_error"] for p in result["parameters"]] == pytest.approx(reference["certified_standard_errors"], rel=TOLERANCES["standard_error_relative"])
    assert result["metrics"]["SSE"] == pytest.approx(reference["certified_SSE"], rel=TOLERANCES["SSE_relative"])
    assert result["validation"]["physical_model_validated"] is False


def test_arrhenius_temperature_units_and_activation_energy():
    temperatures = [290, 305, 320, 340, 360, 380]
    values = [1e7*math.exp(-42000/(8.31446261815324*t)) for t in temperatures]
    kelvin = fit_data(FitInput(x=temperatures, y=values, model="arrhenius", x_unit="K", y_unit="1/s"))
    celsius = fit_data(FitInput(x=[t-273.15 for t in temperatures], y=values, model="arrhenius", x_unit="degC", y_unit="1/s"))
    assert kelvin["parameters"][1]["value"] == pytest.approx(42000, rel=1e-8)
    assert [p["value"] for p in celsius["parameters"]] == pytest.approx([p["value"] for p in kelvin["parameters"]], rel=1e-8)
    assert celsius["reference_temperature_K"] == pytest.approx(kelvin["reference_temperature_K"])


def test_known_observation_error_is_not_erased_by_exact_fit():
    base = dict(x=[0,1,2,3,4,5], y=[1,3,5,7,9,11], model="linear", absolute_sigma=True)
    first = fit_data(FitInput(**base, sigma_y=[1]*6))
    second = fit_data(FitInput(**base, sigma_y=[2]*6))
    assert first["parameters"][0]["standard_error"] > 0
    for a, b in zip(first["parameters"], second["parameters"]):
        assert b["standard_error"] == pytest.approx(2*a["standard_error"])
    assert first["uncertainty_method"] == "known_sigma_normal_local"


@pytest.mark.parametrize("override", [
    {"y":[1,2,3]}, {"x":[1,1,1,1]}, {"sigma_y":[1,0,1,1]},
    {"absolute_sigma":True}, {"y":[1,2,float("nan"),4]},
    {"x_unit":"unknown_invalid_unit"}, {"prediction_x":[9]},
])
def test_reject_invalid_data_or_unapproved_extrapolation(override):
    with pytest.raises(ValidationError):
        FitInput.model_validate({"x":[1,2,3,4],"y":[2,3,4,5],**override})


def test_reject_invalid_model_domain():
    with pytest.raises(ValueError, match="温度单位"):
        fit_data(FitInput(x=[1,2,3,4], y=[1,2,3,4], model="arrhenius", x_unit="second"))
    with pytest.raises(ValueError, match="绝对温度"):
        fit_data(FitInput(x=[-300,-290,20,30], y=[1,2,3,4], model="arrhenius", x_unit="degC"))
    with pytest.raises(ValueError, match="x>0"):
        fit_data(FitInput(x=[0,1,2,3], y=[1,2,3,4], model="power_law"))


def test_explicit_extrapolation_is_identified_and_warned():
    result = fit_data(FitInput(x=[1,2,3,4], y=[2,4,6,8], prediction_x=[1,5], allow_extrapolation=True))
    assert [v["extrapolated"] for v in result["curve"]] == [False, True]
    assert any("范围外" in w for w in result["warnings"])


def test_replicated_conditions_enable_lack_of_fit_test():
    result = fit_data(FitInput(x=[1,1,2,2,3,3,4,4], y=[1,1.1,4,4.1,9,9.1,16,16.1]))
    assert result["diagnostics"]["lack_of_fit"]["p_value"] < .001
