"""Advection q_t + a q_x = 0: the jump moves unchanged with velocity a."""

import numpy as np
import pytest

from exact_solvers import advection
from helpers import assert_conserves, assert_far_field, evaluate


@pytest.mark.parametrize("q_l, q_r, a", [(1.0, 0.0, 1.0), (0.2, 0.7, -0.5), (2.0, 1.0, 0.0)])
def test_jump_moves_with_velocity_a(q_l, q_r, a):
    states, speeds, reval, wave_types = advection.riemann_solution(q_l, q_r, a)
    np.testing.assert_array_equal(states, [[q_l, q_r]])
    assert speeds == [a] and wave_types == ['contact']
    q = evaluate(reval, [a - 1e-9, a + 1e-9])[0]
    np.testing.assert_array_equal(q, [q_l, q_r])


@pytest.mark.parametrize("q_l, q_r, a", [(1.0, 0.0, 1.0), (0.2, 0.7, -0.5)])
def test_conservation(q_l, q_r, a):
    _, _, reval, _ = advection.riemann_solution(q_l, q_r, a)
    flux = lambda q: a * q
    assert_far_field(reval, q_l, q_r)
    assert_conserves(reval, flux, flux, q_l, q_r, L=3.0)
