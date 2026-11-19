"""Euler equations with the stiffened-gas (Tammann) equation of state
    p = (gamma - 1)(E - rho u^2 / 2) - gamma p_inf,
i.e. E = (p + gamma p_inf)/(gamma - 1) + rho u^2 / 2, with possibly different
materials (gamma, p_inf) on the left and right of the contact."""

import numpy as np
import pytest

from exact_solvers import euler_tammann
from helpers import assert_conserves, assert_far_field, assert_rankine_hugoniot, max_speed

PATM = 101325.0
WATER = (7.15, 3.0e8)
AIR = (1.4, 0.0)

# The examples of the Euler_Tammann chapter: (left (rho, u, p), right, aux_l, aux_r)
BOOK_CASES = [
    ([1500.0, 0.0, 3000 * PATM], [1000.0, 0.0, PATM], WATER, WATER),   # shock tube in water
    ([1.0, 350.0, 300 * PATM], [1000.0, 0.0, PATM], AIR, WATER),       # shock in air hits water
    ([1000.0, 350.0, 300 * PATM], [1.0, 0.0, PATM], WATER, AIR),       # water hits air
    ([1000.0, -350.0, 2 * PATM], [1000.0, 350.0, 2 * PATM], WATER, WATER),  # cavitation
    ([600.0, 10.0, 50000.0], [50.0, -10.0, 25000.0], (1.4, 0.0), (7.0, 100.0)),
]


def energy(rho, u, p, gamma, pinf):
    return (p + gamma * pinf) / (gamma - 1) + 0.5 * rho * u**2


def conserved(prim, aux):
    rho, u, p = prim
    return np.array([rho, rho * u, energy(rho, u, p, *aux)])


def flux(aux):
    gamma, pinf = aux
    def f(q):
        rho, mom, E = q
        u = mom / rho
        p = (gamma - 1) * (E - 0.5 * rho * u**2) - gamma * pinf
        return np.array([mom, mom * u + p, u * (E + p)])
    return f


def solve(left, right, aux_l, aux_r):
    return euler_tammann.exact_riemann_solution(np.array(left), np.array(right), aux_l, aux_r,
                                                varin='primitive', varout='primitive')


@pytest.mark.parametrize("left, right, aux_l, aux_r", BOOK_CASES)
def test_contact_and_jump_conditions(left, right, aux_l, aux_r):
    states, speeds, reval, wave_types, outvars = solve(left, right, aux_l, aux_r)
    assert outvars == euler_tammann.primitive_variables
    (rho_ls, u_ls, p_ls), (rho_rs, u_rs, p_rs) = states[:, 1], states[:, 2]
    # Velocity and pressure are continuous across the contact, which moves with the fluid.
    assert u_ls == pytest.approx(u_rs, rel=1e-8, abs=1e-8)
    assert p_ls == pytest.approx(p_rs, rel=1e-8)
    assert speeds[1] == pytest.approx(u_ls)
    for k, side, star, aux in [(0, left, states[:, 1], aux_l), (2, right, states[:, 2], aux_r)]:
        if wave_types[k] == 'shock':
            assert_rankine_hugoniot(flux(aux), conserved(side, aux), conserved(star, aux),
                                    speeds[k], rtol=1e-7)
        else:
            # Isentropic rarefaction: (p + p_inf)/rho^gamma is constant.
            gamma, pinf = aux
            assert (star[2] + pinf) / star[0]**gamma == pytest.approx(
                (side[2] + pinf) / side[0]**gamma, rel=1e-8)


@pytest.mark.parametrize("left, right, aux_l, aux_r", BOOK_CASES)
def test_conservation(left, right, aux_l, aux_r):
    states, speeds, reval, wave_types, _ = solve(left, right, aux_l, aux_r)
    u_contact = speeds[1]

    def conserved_reval(xi):
        rho, u, p = reval(xi)
        left_material = xi <= u_contact
        gamma = np.where(left_material, aux_l[0], aux_r[0])
        pinf = np.where(left_material, aux_l[1], aux_r[1])
        return rho, rho * u, energy(rho, u, p, gamma, pinf)

    assert_far_field(reval, left, right, xi_far=10 * max_speed(speeds))
    assert_conserves(conserved_reval, flux(aux_l), flux(aux_r),
                     conserved(left, aux_l), conserved(right, aux_r), L=max_speed(speeds) + 1)


def test_ideal_gas_limit_matches_sod():
    """With p_inf = 0 and gamma = 1.4 this is the Sod shock tube (Toro, Table 4.2, Test 1)."""
    states, *_ = solve([1.0, 0.0, 1.0], [0.125, 0.0, 0.1], (1.4, 0.0), (1.4, 0.0))
    assert states[2, 1] == pytest.approx(0.30313, rel=1e-4)
    assert states[1, 1] == pytest.approx(0.92745, rel=1e-4)
    assert states[0, 1] == pytest.approx(0.42632, rel=1e-4)
    assert states[0, 2] == pytest.approx(0.26557, rel=1e-4)


def test_characteristic_speeds():
    gamma, pinf = WATER
    q = (1000.0, 2.0, PATM)
    c = np.sqrt(gamma * (PATM + pinf) / 1000.0)
    assert euler_tammann.sound_speed(1000.0, PATM, gamma, pinf) == pytest.approx(c)
    assert euler_tammann.lambda1(q, 0, WATER) == pytest.approx(2.0 - c)
    assert euler_tammann.lambda2(q, 0, WATER) == pytest.approx(2.0)
    assert euler_tammann.lambda3(q, 0, WATER) == pytest.approx(2.0 + c)


def test_primitive_conservative_round_trip():
    q = euler_tammann.primitive_to_conservative(1000.0, 2.0, PATM, *WATER)
    np.testing.assert_allclose(euler_tammann.conservative_to_primitive(*q, *WATER),
                               (1000.0, 2.0, PATM))
