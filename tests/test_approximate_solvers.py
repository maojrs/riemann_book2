"""The chapters' approximate solvers (copied in exact_solvers/*_approximate_demos.py)."""
import numpy as np
import pytest

from exact_solvers.shallow_water_approximate_demos import shallow_water_roe_with_efix

GRAV = 1.


def flux(q):
    """Shallow water flux f(q) = (hu, hu^2/h + g h^2/2)."""
    h, hu = q
    return np.array([hu, hu**2/h + GRAV*h**2/2])


def mirror(q):
    """The reflection x -> -x: (h, hu) -> (h, -hu); it swaps the 1- and 2-waves."""
    return np.array([q[0], -q[1]])


# The chapter's transonic 1-rarefaction (h_l=4, u_l=1, h_r=1, u_r=1) and its mirror image, a
# transonic 2-rarefaction
TRANSONIC_1 = (np.array([4., 4.]), np.array([1., 1.]))
TRANSONIC_2 = (mirror(TRANSONIC_1[1]), mirror(TRANSONIC_1[0]))


@pytest.mark.parametrize('q_l, q_r', [TRANSONIC_1, TRANSONIC_2])
def test_roe_efix_conservative(q_l, q_r):
    """With the entropy fix the wave jumps still add up to the flux difference:
    sum s_p (q_{p+1} - q_p) = f(q_r) - f(q_l)."""
    states, speeds, reval, wave_types = shallow_water_roe_with_efix(q_l, q_r, grav=GRAV)
    assert len(speeds) == 3
    jumps = np.diff(states, axis=1)
    assert np.allclose(jumps @ speeds, flux(q_r) - flux(q_l), atol=1e-13)


def test_roe_efix_2_wave_mirrors_1_wave():
    """The transonic 2-wave fix is the mirror image of the transonic 1-wave fix."""
    states1, speeds1, reval1, _ = shallow_water_roe_with_efix(*TRANSONIC_1, grav=GRAV)
    states2, speeds2, reval2, _ = shallow_water_roe_with_efix(*TRANSONIC_2, grav=GRAV)
    assert np.allclose(speeds2, -np.array(speeds1)[::-1])
    assert np.allclose(states2, mirror(states1)[:, ::-1])
    xi = np.linspace(-2, 2, 41) + 0.013   # off the wave speeds
    h1, hu1 = reval1(-xi)
    h2, hu2 = reval2(xi)
    assert np.allclose(h2, h1) and np.allclose(hu2, -hu1)
