from copy import deepcopy
from scripts.replay import compare_result

def test_replay_normalizes_json_object_keys():
    assert compare_result("aqueous_flash",{"groups":[{16:1}]},{"groups":[{"16":1}]})

def test_mesh_replay_accepts_different_diagnostics_but_preserves_physics():
    original={"validation":{"passed":True,"global_energy_residual_kW":1e-9},
        "solver":{"success":True,"residual_evaluations":100,"algorithm":"test"},
        "distillate_light_fraction":.96,"reboiler_duty_kW":1700.,
        "stages":[{"temperature_K":350.,"total_residual_kmol_h":1e-10}]}
    actual=deepcopy(original)
    actual["solver"]["residual_evaluations"]=123
    actual["validation"]["global_energy_residual_kW"]=2e-9
    assert compare_result("column_mesh",actual,original)
    actual["distillate_light_fraction"]=.95
    assert not compare_result("column_mesh",actual,original)
    actual=deepcopy(original)
    actual["validation"]["passed"]=False
    assert not compare_result("column_mesh",actual,original)

def test_hydrogen_replay_compares_physical_outcomes_and_requires_validation():
    original={"validation":{"passed":True,"minimum_liquid_TPD":1e-10},
        "solver":{"method":"test","accepted_nfev":8,"attempts":[]},"phases":[{"flow_kmol_h":10.}]}
    actual=deepcopy(original)
    actual["solver"]["accepted_nfev"]=9
    actual["validation"]["minimum_liquid_TPD"]=2e-10
    assert compare_result("condenser_flash",actual,original)
    actual["phases"][0]["flow_kmol_h"]=11
    assert not compare_result("condenser_flash",actual,original)
    actual=deepcopy(original)
    actual["validation"]["passed"]=False
    assert not compare_result("condenser_flash",actual,original)


def test_wet_replay_retains_physics_and_ignores_only_accepted_diagnostics():
    original={"validation":{"passed":True,"max_scaled_equation_residual":1e-9},
        "solver":{"method":"wet","residual_evaluations":100,"elapsed_seconds":12.},
        "stages":[{"temperature_K":350.,"component_residuals_kmol_h":[0.]*4,"minimum_searched_liquid_TPD":0.}],
        "outlets":[{"flow_kmol_h":40.}]}
    actual=deepcopy(original)
    actual["solver"]["elapsed_seconds"]=18.
    actual["stages"][0]["component_residuals_kmol_h"]=[1e-9]*4
    assert compare_result("wet_column",actual,original)
    actual["outlets"][0]["flow_kmol_h"]=41.
    assert not compare_result("wet_column",actual,original)
    actual=deepcopy(original)
    actual["validation"]["passed"]=False
    assert not compare_result("wet_column",actual,original)


def test_recycle_replay_requires_nested_validation_and_compares_loop_flows():
    original={"validation":{"passed":True},"column":{"validation":{"passed":True},"solver":{"method":"wet"},"stages":[]},
        "recycle_solver":{"method":"loop","elapsed_seconds":10.,"history":[1,2]},"recycle_component_kmol_h":{"water":2.}}
    actual=deepcopy(original)
    actual["recycle_solver"]["elapsed_seconds"]=20.
    actual["recycle_solver"]["history"]=[1,2,3]
    assert compare_result("recycle_process",actual,original)
    actual["recycle_component_kmol_h"]["water"]=3.
    assert not compare_result("recycle_process",actual,original)
    actual=deepcopy(original)
    actual["column"]["validation"]["passed"]=False
    assert not compare_result("recycle_process",actual,original)
    actual=deepcopy(original)
    actual["validation"]["passed"]=False
    assert not compare_result("recycle_process",actual,original)
