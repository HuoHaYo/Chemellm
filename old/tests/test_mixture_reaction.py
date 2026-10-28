import numpy as np
import pytest
from app.calculations import calculate


def test_pure_ethylbenzene_and_steam_reduce_to_original_reaction_model():
    mixed=calculate("mixture_reaction",{"feed_component_kmol_h":[3200,400,0,0]})
    pure=calculate("reaction_thermo",{})
    assert mixed["validation"]["passed"]
    assert mixed["outlet_kmol_h"]==pytest.approx(pure["outlet_kmol_h"])
    assert mixed["heat_duty_kW"]==pytest.approx(pure["heat_duty_kW"],abs=1e-8)
    assert mixed["equilibrium_conversion"]==pytest.approx(pure["equilibrium_conversion"],abs=1e-10)


def test_recycle_products_are_preserved_and_inhibit_equilibrium():
    inlet=np.array([800.,100.,20.,.05])
    r=calculate("mixture_reaction",{"feed_component_kmol_h":inlet.tolist()})
    assert r["validation"]["passed"]
    outlet=np.array([r["outlet_kmol_h"][k] for k in r["components"]])
    assert outlet==pytest.approx(inlet+np.array([0.,-60.,60.,60.]))
    atom=np.array([[0,8,8,0],[2,10,8,2],[1,0,0,0]])
    assert atom@outlet==pytest.approx(atom@inlet,abs=1e-9)
    e=r["equilibrium_extent_kmol_h"]
    equilibrium=inlet+np.array([0.,-e,e,e])
    q=equilibrium[2]*equilibrium[3]/equilibrium[1]/equilibrium.sum()
    assert q==pytest.approx(r["thermodynamics"]["Kp_dimensionless"],rel=1e-10)
    assert r["equilibrium_conversion"]<calculate("reaction_thermo",{})["equilibrium_conversion"]
    assert r["heat_duty_kW"]==pytest.approx(r["sensible_heat_kW"]+r["reaction_heat_kW"],abs=1e-8)


def test_product_rich_feed_can_have_negative_equilibrium_extent():
    r=calculate("mixture_reaction",{"feed_component_kmol_h":[0,10,100,100],"conversion":0})
    assert r["equilibrium_extent_kmol_h"]<0
    assert r["validation"]["passed"] is False


@pytest.mark.parametrize("feed",[[800,0,1,1],[800,100,-1,0],[800,100,0],[1e7,1,0,0]])
def test_mixture_reaction_rejects_invalid_feed(feed):
    with pytest.raises(ValueError):calculate("mixture_reaction",{"feed_component_kmol_h":feed})
