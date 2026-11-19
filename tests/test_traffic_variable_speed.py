"""LWR traffic with a speed limit that jumps at x = 0:
    q_t + (v(x) q (1 - q))_x = 0,  v = v_l for x < 0 and v_r for x > 0."""

import numpy as np
import pytest

from exact_solvers import traffic_LWR, traffic_variable_speed as tvs
from helpers import assert_conserves, assert_far_field, evaluate, max_speed


def flux(v):
    return lambda q: v * q * (1 - q)


# One case per branch of exact_riemann_solution: (q_l, q_r, v_l, v_r, wave types)
CASES = [
    (0.3, 0.3, 1.0, 1.0, ['contact']),                       # equal fluxes
    (0.4, 0.9, 1.0, 1.5, ['shock', 'contact']),              # (1) left-going shock
    (0.1, 0.3, 1.0, 1.5, ['contact', 'shock']),              # (2) right-going shock
    (0.3, 0.2, 1.0, 0.5, ['shock', 'contact', 'raref']),     # (3)
    (0.7, 0.6, 0.5, 1.0, ['raref', 'contact', 'shock']),     # (4)
    (0.9, 0.1, 1.0, 0.8, ['raref', 'contact', 'raref']),     # (5a) transonic, v_r < v_l
    (0.9, 0.1, 0.8, 1.0, ['raref', 'contact', 'raref']),     # (5b) transonic, v_r > v_l
    (0.9, 0.6, 1.0, 1.0, ['raref', 'contact']),              # (6) left-going rarefaction
    (0.4, 0.1, 1.0, 1.0, ['contact', 'raref']),              # (7) right-going rarefaction
]


@pytest.mark.parametrize("q_l, q_r, v_l, v_r, types", CASES)
def test_branches(q_l, q_r, v_l, v_r, types):
    states, speeds, reval, wave_types = tvs.exact_riemann_solution(q_l, q_r, v_l, v_r)
    assert wave_types == types


@pytest.mark.parametrize("q_l, q_r, v_l, v_r, types", CASES)
def test_flux_continuous_at_interface(q_l, q_r, v_l, v_r, types):
    """No cars are created at x = 0: v_l f(q(0-)) = v_r f(q(0+))."""
    _, _, reval, _ = tvs.exact_riemann_solution(q_l, q_r, v_l, v_r)
    q_minus, q_plus = evaluate(reval, [-1e-9, 1e-9])[0]
    assert flux(v_l)(q_minus) == pytest.approx(flux(v_r)(q_plus), abs=1e-12)


@pytest.mark.parametrize("q_l, q_r, v_l, v_r, types", CASES)
def test_conservation(q_l, q_r, v_l, v_r, types):
    _, speeds, reval, _ = tvs.exact_riemann_solution(q_l, q_r, v_l, v_r)
    assert_far_field(reval, q_l, q_r)
    assert_conserves(reval, flux(v_l), flux(v_r), q_l, q_r, L=max_speed(speeds) + 1)


@pytest.mark.parametrize("q_l, q_r", [(0.2, 0.4), (0.6, 0.1), (0.9, 0.6), (0.4, 0.1), (0.9, 0.1),
                                      (0.75, 0.25)])
def test_equal_speed_limits_reduce_to_LWR(q_l, q_r):
    _, _, reval, _ = tvs.exact_riemann_solution(q_l, q_r, 1.0, 1.0)
    _, _, reval_lwr, _ = traffic_LWR.riemann_traffic_exact(q_l, q_r)
    xi = np.linspace(-1.5, 1.5, 301)
    np.testing.assert_allclose(evaluate(reval, xi), evaluate(reval_lwr, xi), atol=1e-12)
