"""Shallow water equations h_t + (hu)_x = 0, (hu)_t + (hu^2 + g h^2/2)_x = 0."""

import numpy as np
import pytest

from exact_solvers import shallow_water
from helpers import (assert_conserves, assert_far_field, assert_rankine_hugoniot,
                     evaluate, max_speed)


def swe_flux(g):
    def flux(q):
        h, hu = q
        u = hu / h if h > 0 else 0.0
        return np.array([hu, hu * u + 0.5 * g * h**2])
    return flux


def primitive(q):
    h, hu = q
    return h, (hu / h if h > 0 else 0.0)


# (h_l, u_l, h_r, u_r, expected wave types)
WET_CASES = [
    (3.0, 0.0, 1.0, 0.0, ['raref', 'shock']),     # dam break
    (1.0, 0.0, 3.0, 0.0, ['shock', 'raref']),     # reversed dam break
    (1.0, 0.8, 1.0, -0.8, ['shock', 'shock']),    # colliding flows
    (1.0, -0.8, 1.0, 0.8, ['raref', 'raref']),    # separating flows
]


def solve(h_l, u_l, h_r, u_r, g):
    q_l = np.array([h_l, h_l * u_l])
    q_r = np.array([h_r, h_r * u_r])
    return q_l, q_r, shallow_water.exact_riemann_solution(q_l, q_r, grav=g)


@pytest.mark.parametrize("g", [1.0, 9.81])
@pytest.mark.parametrize("h_l, u_l, h_r, u_r, expected_types", WET_CASES)
def test_wave_structure_and_jump_conditions(h_l, u_l, h_r, u_r, expected_types, g):
    q_l, q_r, (states, speeds, reval, wave_types) = solve(h_l, u_l, h_r, u_r, g)
    assert wave_types == expected_types
    q_m = states[:, 1]
    h_m, u_m = primitive(q_m)
    flux = swe_flux(g)
    for family, (q_side, s) in enumerate([(q_l, speeds[0]), (q_r, speeds[1])], start=1):
        h_s, u_s = primitive(q_side)
        sign = -1 if family == 1 else 1     # lambda_1 = u - c, lambda_2 = u + c
        if wave_types[family - 1] == 'shock':
            assert_rankine_hugoniot(flux, q_side, q_m, s)
            # Lax entropy condition: characteristics of the family enter the shock.
            lam_side = u_s + sign * np.sqrt(g * h_s)
            lam_m = u_m + sign * np.sqrt(g * h_m)
            if family == 1:
                assert lam_side > s > lam_m
            else:
                assert lam_m > s > lam_side
        else:
            # The Riemann invariant u -/+ 2 sqrt(g h) is constant across the fan.
            assert u_m - sign * 2 * np.sqrt(g * h_m) == pytest.approx(
                u_s - sign * 2 * np.sqrt(g * h_s))


@pytest.mark.parametrize("g", [1.0, 9.81])
@pytest.mark.parametrize("h_l, u_l, h_r, u_r, expected_types", WET_CASES)
def test_conservation(h_l, u_l, h_r, u_r, expected_types, g):
    q_l, q_r, (states, speeds, reval, wave_types) = solve(h_l, u_l, h_r, u_r, g)
    assert_far_field(reval, q_l, q_r)
    assert_conserves(reval, swe_flux(g), swe_flux(g), q_l, q_r, L=max_speed(speeds) + 2)


def test_rarefaction_profile():
    """Inside a 1-rarefaction u - sqrt(g h) = x/t and u + 2 sqrt(g h) = u_l + 2 sqrt(g h_l)."""
    g = 1.0
    q_l, q_r, (states, speeds, reval, _) = solve(3.0, 0.0, 1.0, 0.0, g)
    xi = np.linspace(*speeds[0], 9)[1:-1]
    h, hu = evaluate(reval, xi)
    u = hu / h
    np.testing.assert_allclose(u - np.sqrt(g * h), xi)
    np.testing.assert_allclose(u + 2 * np.sqrt(g * h), 2 * np.sqrt(g * 3.0))


def test_dam_break_onto_dry_bed():
    """Ritter's solution: h = (2 sqrt(g h_l) - x/t)^2 / (9 g) for
    -sqrt(g h_l) < x/t < 2 sqrt(g h_l), and dry beyond the front."""
    g, h_l = 1.0, 2.0
    q_l, q_r, (states, speeds, reval, _) = solve(h_l, 0.0, 0.0, 0.0, g)
    c_l = np.sqrt(g * h_l)
    xi = np.linspace(-c_l, 2 * c_l, 13)[1:-1]
    h, _ = evaluate(reval, xi)
    np.testing.assert_allclose(h, (2 * c_l - xi)**2 / (9 * g))
    assert evaluate(reval, [2 * c_l + 0.1])[0, 0] == 0.0
    assert_conserves(reval, swe_flux(g), swe_flux(g), q_l, q_r, L=3 * c_l + 1)


def test_dry_middle_state():
    """If u_r - u_l > 2 (sqrt(g h_l) + sqrt(g h_r)) the flows separate leaving a dry region."""
    g = 1.0
    q_l, q_r, (states, speeds, reval, wave_types) = solve(1.0, -3.0, 1.0, 3.0, g)
    assert states[0, 1] == 0.0
    assert evaluate(reval, [0.0])[0, 0] == 0.0
    assert_conserves(reval, swe_flux(g), swe_flux(g), q_l, q_r, L=max_speed(speeds) + 2)


def test_primitive_conservative_round_trip():
    h, hu = shallow_water.primitive_to_conservative(2.0, -0.5)
    assert (h, hu) == (2.0, -1.0)
    assert shallow_water.conservative_to_primitive(h, hu) == pytest.approx((2.0, -0.5))
