"""Euler equations of gas dynamics for an ideal gas, p = (gamma - 1)(E - rho u^2 / 2)."""

import numpy as np
import pytest

from exact_solvers import euler
from helpers import (assert_conserves, assert_far_field, assert_rankine_hugoniot,
                     evaluate, max_speed)


def euler_flux(gamma):
    def flux(q):
        rho, mom, E = q
        u = mom / rho
        p = (gamma - 1) * (E - 0.5 * rho * u**2)
        return np.array([mom, mom * u + p, u * (E + p)])
    return flux


def conserved(rho, u, p, gamma=1.4):
    return np.array([rho, rho * u, p / (gamma - 1) + 0.5 * rho * u**2])


# Reference solutions from E. F. Toro, "Riemann Solvers and Numerical Methods
# for Fluid Dynamics", 3rd ed., Table 4.2 (gamma = 1.4):
# (left (rho, u, p), right (rho, u, p), p*, u*, rho*_L, rho*_R, wave types)
TORO_TESTS = [
    ((1.0, 0.0, 1.0), (0.125, 0.0, 0.1), 0.30313, 0.92745, 0.42632, 0.26557,
     ['raref', 'contact', 'shock']),                                    # Test 1 (Sod)
    ((1.0, -2.0, 0.4), (1.0, 2.0, 0.4), 0.00189, 0.0, 0.02185, 0.02185,
     ['raref', 'contact', 'raref']),                                    # Test 2 (123 problem)
    ((1.0, 0.0, 1000.0), (1.0, 0.0, 0.01), 460.894, 19.5975, 0.57506, 5.99924,
     ['raref', 'contact', 'shock']),                                    # Test 3
    ((1.0, 0.0, 0.01), (1.0, 0.0, 100.0), 46.0950, -6.19633, 5.99242, 0.57511,
     ['shock', 'contact', 'raref']),                                    # Test 4
    ((5.99924, 19.5975, 460.894), (5.99242, -6.19633, 46.0950), 1691.64, 8.68975,
     14.2823, 31.0426, ['shock', 'contact', 'shock']),                  # Test 5
]


@pytest.mark.parametrize("left, right, p_star, u_star, rho_l_star, rho_r_star, types", TORO_TESTS)
def test_toro_reference_solutions(left, right, p_star, u_star, rho_l_star, rho_r_star, types):
    states, speeds, reval, wave_types = euler.exact_riemann_solution(
        conserved(*left), conserved(*right))
    assert wave_types == types
    rho_ls, u_ls, p_ls = euler.conservative_to_primitive(*states[:, 1])
    rho_rs, u_rs, p_rs = euler.conservative_to_primitive(*states[:, 2])
    # Toro gives 5-6 significant digits.
    assert p_ls == pytest.approx(p_star, rel=1e-4, abs=1e-5)
    assert p_rs == pytest.approx(p_star, rel=1e-4, abs=1e-5)
    assert u_ls == pytest.approx(u_star, rel=1e-4, abs=1e-5)
    assert u_rs == pytest.approx(u_star, rel=1e-4, abs=1e-5)
    assert rho_ls == pytest.approx(rho_l_star, rel=1e-4)
    assert rho_rs == pytest.approx(rho_r_star, rel=1e-4)


@pytest.mark.parametrize("left, right, p_star, u_star, rho_l_star, rho_r_star, types", TORO_TESTS)
def test_jump_conditions_and_conservation(left, right, p_star, u_star, rho_l_star, rho_r_star,
                                          types):
    q_l, q_r = conserved(*left), conserved(*right)
    states, speeds, reval, wave_types = euler.exact_riemann_solution(q_l, q_r)
    flux = euler_flux(1.4)
    # Contact: velocity and pressure continuous, moves with the fluid velocity.
    assert_rankine_hugoniot(flux, states[:, 1], states[:, 2], speeds[1], rtol=1e-7)
    for k, (q_a, q_b) in [(0, (q_l, states[:, 1])), (2, (states[:, 2], q_r))]:
        if wave_types[k] == 'shock':
            assert_rankine_hugoniot(flux, q_a, q_b, speeds[k], rtol=1e-7)
    assert_far_field(reval, q_l, q_r)
    assert_conserves(reval, flux, flux, q_l, q_r, L=max_speed(speeds) + 1)


def test_rarefaction_isentropic_and_riemann_invariant():
    """Across a 1-rarefaction p/rho^gamma and u + 2c/(gamma-1) are constant,
    and inside the fan u - c = x/t."""
    gamma = 1.4
    rho_l, u_l, p_l = 1.0, 0.0, 1.0
    states, speeds, reval, _ = euler.exact_riemann_solution(
        conserved(rho_l, u_l, p_l), conserved(0.125, 0.0, 0.1))
    xi = np.linspace(*speeds[0], 9)[1:-1]
    rho, u, p = euler.conservative_to_primitive(*evaluate(reval, xi))
    c = np.sqrt(gamma * p / rho)
    np.testing.assert_allclose(p / rho**gamma, p_l / rho_l**gamma)
    np.testing.assert_allclose(u + 2 * c / (gamma - 1), u_l + 2 * np.sqrt(gamma * p_l / rho_l) / (gamma - 1))
    np.testing.assert_allclose(u - c, xi)


def test_vacuum_middle_state():
    """Strongly separating flow: u_r - u_l > 2(c_l + c_r)/(gamma - 1) creates a vacuum."""
    q_l, q_r = conserved(1.0, -5.0, 0.4), conserved(1.0, 5.0, 0.4)
    states, speeds, reval, wave_types = euler.exact_riemann_solution(q_l, q_r)
    assert wave_types == ['raref', 'contact', 'raref']
    np.testing.assert_allclose(evaluate(reval, [0.0])[:, 0], 0.0, atol=1e-12)
    assert_conserves(reval, euler_flux(1.4), euler_flux(1.4), q_l, q_r, L=max_speed(speeds) + 1)


def test_characteristic_speeds():
    q = conserved(1.0, 0.5, 1.4)    # sound speed c = 1.4
    assert euler.lambda1(q, 0) == pytest.approx(0.5 - 1.4)
    assert euler.lambda2(q, 0) == pytest.approx(0.5)
    assert euler.lambda3(q, 0) == pytest.approx(0.5 + 1.4)


def test_primitive_conservative_round_trip():
    q = euler.primitive_to_conservative(1.2, -0.3, 2.5)
    np.testing.assert_allclose(euler.conservative_to_primitive(*q), (1.2, -0.3, 2.5))


@pytest.mark.parametrize("gamma", [5 / 3, 1.2])
def test_other_gamma(gamma):
    """The solver should also be correct for gamma != 1.4."""
    q_l, q_r = conserved(1.0, 0.0, 1.0, gamma), conserved(0.125, 0.0, 0.1, gamma)
    states, speeds, reval, _ = euler.exact_riemann_solution(q_l, q_r, gamma=gamma)
    assert_far_field(reval, q_l, q_r)
    assert_conserves(reval, euler_flux(gamma), euler_flux(gamma), q_l, q_r,
                     L=max_speed(speeds) + 1)
