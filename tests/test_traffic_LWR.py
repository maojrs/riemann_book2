"""LWR traffic model q_t + (q(1-q))_x = 0, with velocity u = 1 - q."""

import numpy as np
import pytest

from exact_solvers import traffic_LWR
from helpers import (assert_conserves, assert_far_field, assert_rankine_hugoniot,
                     evaluate, max_speed)

flux = lambda q: q * (1 - q)


def test_characteristic_speed():
    assert traffic_LWR.c(0.25, xi=0.0) == pytest.approx(0.5)


@pytest.mark.parametrize("q_l, q_r", [(0.2, 0.4), (0.0, 1.0), (0.4, 0.9)])
def test_shock_when_density_increases(q_l, q_r):
    states, speeds, reval, wave_types = traffic_LWR.riemann_traffic_exact(q_l, q_r)
    assert wave_types == ['shock']
    s = speeds[0]
    assert s == pytest.approx(1 - q_l - q_r)
    assert_rankine_hugoniot(flux, q_l, q_r, s)
    assert 1 - 2 * q_l > s > 1 - 2 * q_r                 # Lax entropy condition


@pytest.mark.parametrize("q_l, q_r", [(0.6, 0.1), (1.0, 0.0), (0.5, 0.2)])
def test_rarefaction_when_density_decreases(q_l, q_r):
    _, speeds, reval, wave_types = traffic_LWR.riemann_traffic_exact(q_l, q_r)
    assert wave_types == ['rarefaction']
    c_l, c_r = speeds[0]
    assert (c_l, c_r) == pytest.approx((1 - 2 * q_l, 1 - 2 * q_r))
    xi = np.linspace(c_l, c_r, 11)[1:-1]
    np.testing.assert_allclose(evaluate(reval, xi)[0], (1 - xi) / 2)   # 1 - 2q = x/t


@pytest.mark.parametrize("q_l, q_r", [(0.2, 0.4), (0.0, 1.0), (0.6, 0.1), (1.0, 0.0)])
def test_conservation(q_l, q_r):
    _, speeds, reval, _ = traffic_LWR.riemann_traffic_exact(q_l, q_r)
    assert_far_field(reval, q_l, q_r)
    assert_conserves(reval, flux, flux, q_l, q_r, L=max_speed(speeds) + 2)
