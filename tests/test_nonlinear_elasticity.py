"""Nonlinear elasticity in a heterogeneous medium:
    eps_t - u_x = 0,   (rho u)_t - sigma(eps, x)_x = 0,
with stress sigma = K1 eps + K2 eps^2 and material aux = (rho, K1, K2)
different for x < 0 and x > 0. The conserved variables are q = (eps, rho u)."""

import numpy as np
import pytest

from exact_solvers import nonlinear_elasticity as ne
from helpers import assert_conserves, assert_far_field, assert_rankine_hugoniot, max_speed


def flux(aux):
    rho, K1, K2 = aux
    return lambda q: np.array([-q[1] / rho, -ne.sigma(q[0], K1, K2)])


AUX_L, AUX_R = (1.0, 5.0, 1.0), (1.0, 2.0, 1.0)     # materials used in the chapter
CASES = [
    ((2.1, 0.0), (0.0, 0.0)),     # example from the chapter
    ((0.0, 0.0), (2.1, 0.0)),
    ((0.5, 1.0), (0.5, -1.0)),
    ((0.5, -0.5), (0.5, 0.5)),
]


def solve(q_l, q_r, aux_l=AUX_L, aux_r=AUX_R):
    return ne.exact_riemann_solution(np.array(q_l), np.array(q_r), np.array(aux_l), np.array(aux_r))


def test_stress_and_sound_speed():
    assert ne.sigma(2.0, 5.0, 1.0) == pytest.approx(14.0)
    assert ne.dsigma(2.0, 5.0, 1.0) == pytest.approx(9.0)
    assert ne.sound_speed(2.0, 5.0, 1.0, 4.0) == pytest.approx(1.5)


@pytest.mark.parametrize("q_l, q_r", CASES)
def test_interface_conditions(q_l, q_r):
    """Velocity and stress are continuous across the material interface at x = 0."""
    states, speeds, reval, wave_types = solve(q_l, q_r)
    eps_ls, mom_ls = states[:, 1]
    eps_rs, mom_rs = states[:, 2]
    assert speeds[1] == 0.0
    assert mom_ls / AUX_L[0] == pytest.approx(mom_rs / AUX_R[0], abs=1e-8)
    assert ne.sigma(eps_ls, *AUX_L[1:]) == pytest.approx(ne.sigma(eps_rs, *AUX_R[1:]), abs=1e-8)


@pytest.mark.parametrize("q_l, q_r", CASES)
def test_waves_move_in_the_right_direction(q_l, q_r):
    """The 1-wave travels left and the 2-wave right; shocks satisfy Rankine-Hugoniot."""
    states, speeds, reval, wave_types = solve(q_l, q_r)
    for k, sign, q_a, q_b, aux in [(0, -1, np.array(q_l), states[:, 1], AUX_L),
                                   (2, +1, states[:, 2], np.array(q_r), AUX_R)]:
        assert np.all(sign * np.atleast_1d(speeds[k]) > 0), (wave_types[k], speeds[k])
        if wave_types[k] == 'shock':
            assert_rankine_hugoniot(flux(aux), q_a, q_b, speeds[k])


@pytest.mark.parametrize("q_l, q_r", CASES)
def test_conservation(q_l, q_r):
    states, speeds, reval, wave_types = solve(q_l, q_r)
    assert_far_field(reval, q_l, q_r)
    assert_conserves(reval, flux(AUX_L), flux(AUX_R), q_l, q_r, L=max_speed(speeds) + 1)


def test_primitive_conservative_round_trip():
    eps, mom = ne.primitive_to_conservative(0.3, -2.0, 4.0)
    assert (eps, mom) == (0.3, -8.0)
    assert ne.conservative_to_primitive(eps, mom, 4.0) == (0.3, -2.0)
