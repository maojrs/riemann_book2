"""LWR traffic with an on-ramp at x = 0 that adds a flux D of cars:
    q_t + (q (1 - q))_x = D delta(x)."""

import numpy as np
import pytest

from exact_solvers import traffic_ramps
from helpers import assert_conserves, assert_far_field, evaluate, max_speed

flux = lambda q: q * (1 - q)

# One case per branch of exact_riemann_solution: (q_l, q_r, D, wave types)
CASES = [
    (0.1, 0.6, 0.1, ['contact', 'shock']),             # q_r >= 1/2: right-going shock
    (0.9, 0.6, 0.1, ['raref', 'contact']),             # q_r >= 1/2: left-going rarefaction
    (0.7, 0.6, 0.1, ['shock', 'contact']),             # q_r >= 1/2: left-going shock
    (0.9, 0.1, 0.04, ['raref', 'contact', 'raref']),   # congestion at the ramp
    (0.4, 0.1, 0.04, ['shock', 'contact', 'raref']),   # congestion, left-going shock
    (0.1, 0.3, 0.04, ['contact', 'shock']),            # right-going shock only
    (0.1, 0.05, 0.04, ['contact', 'raref']),           # right-going rarefaction only
]


@pytest.mark.parametrize("q_l, q_r, D, types", CASES)
def test_branches(q_l, q_r, D, types):
    _, _, _, wave_types = traffic_ramps.exact_riemann_solution(q_l, q_r, D)
    assert wave_types == types


@pytest.mark.parametrize("q_l, q_r, D, types", CASES)
def test_ramp_adds_flux_D(q_l, q_r, D, types):
    """At x = 0 the flux jumps by exactly the ramp inflow: f(q(0+)) - f(q(0-)) = D."""
    _, _, reval, _ = traffic_ramps.exact_riemann_solution(q_l, q_r, D)
    q_minus, q_plus = evaluate(reval, [-1e-9, 1e-9])[0]
    assert flux(q_plus) - flux(q_minus) == pytest.approx(D, abs=1e-12)


@pytest.mark.parametrize("q_l, q_r, D, types", CASES)
def test_conservation_with_source(q_l, q_r, D, types):
    _, speeds, reval, _ = traffic_ramps.exact_riemann_solution(q_l, q_r, D)
    speeds = [s for s in speeds if s is not None]
    assert_far_field(reval, q_l, q_r)
    assert_conserves(reval, flux, flux, q_l, q_r, L=max_speed(speeds) + 1, source=D)


def test_no_ramp_reduces_to_LWR():
    from exact_solvers import traffic_LWR
    for q_l, q_r in [(0.2, 0.4), (0.6, 0.1), (0.3, 0.8)]:
        _, _, reval, _ = traffic_ramps.exact_riemann_solution(q_l, q_r, 0.0)
        _, _, reval_lwr, _ = traffic_LWR.riemann_traffic_exact(q_l, q_r)
        xi = np.linspace(-1.5, 1.5, 301)
        np.testing.assert_allclose(evaluate(reval, xi), evaluate(reval_lwr, xi), atol=1e-12)
