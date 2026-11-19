"""Burgers' equation q_t + (q^2/2)_x = 0."""

import numpy as np
import pytest

from exact_solvers import burgers
from helpers import (assert_conserves, assert_far_field, assert_rankine_hugoniot,
                     evaluate, max_speed)

flux = lambda q: 0.5 * q**2


def test_characteristic_speed():
    assert burgers.speed(0.7, xi=0.0) == 0.7


@pytest.mark.parametrize("q_l, q_r", [(2.0, 1.0), (1.0, -1.0), (0.5, 0.0)])
def test_shock_when_q_l_greater_than_q_r(q_l, q_r):
    states, speeds, reval, wave_types = burgers.exact_riemann_solution(q_l, q_r)
    assert wave_types == ['shock']
    s = speeds[0]
    assert s == pytest.approx((q_l + q_r) / 2)          # Rankine-Hugoniot for Burgers
    assert_rankine_hugoniot(flux, q_l, q_r, s)
    assert q_l > s > q_r                                 # Lax entropy condition
    np.testing.assert_array_equal(evaluate(reval, [s - 1e-9, s + 1e-9])[0], [q_l, q_r])


@pytest.mark.parametrize("q_l, q_r", [(1.0, 2.0), (-1.0, 1.0), (0.0, 0.5)])
def test_rarefaction_when_q_l_less_than_q_r(q_l, q_r):
    states, speeds, reval, wave_types = burgers.exact_riemann_solution(q_l, q_r)
    assert wave_types == ['rarefaction']
    assert list(speeds[0]) == [q_l, q_r]
    xi = np.linspace(q_l, q_r, 11)[1:-1]
    np.testing.assert_allclose(evaluate(reval, xi)[0], xi)   # q = x/t inside the fan


@pytest.mark.parametrize("q_l, q_r", [(2.0, 1.0), (1.0, -1.0), (1.0, 2.0), (-1.0, 1.0), (0.3, 0.3)])
def test_conservation(q_l, q_r):
    _, speeds, reval, _ = burgers.exact_riemann_solution(q_l, q_r)
    assert_far_field(reval, q_l, q_r)
    assert_conserves(reval, flux, flux, q_l, q_r, L=max_speed(speeds) + 2)


@pytest.mark.parametrize("q_l, q_r", [(1.0, 2.0), (-1.0, 1.0)])
def test_unphysical_solution_is_an_entropy_violating_shock(q_l, q_r):
    _, speeds, reval, wave_types = burgers.unphysical_riemann_solution(q_l, q_r)
    assert wave_types == ['shock']
    assert_rankine_hugoniot(flux, q_l, q_r, speeds[0])   # still a weak solution
    assert not q_l > speeds[0] > q_r                      # but violates the entropy condition
    assert_conserves(reval, flux, flux, q_l, q_r, L=4.0)
