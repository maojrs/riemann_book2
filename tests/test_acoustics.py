"""Linear acoustics p_t + K u_x = 0, rho u_t + p_x = 0, in homogeneous and
heterogeneous media (different (rho, K) for x < 0 and x > 0)."""

import numpy as np
import pytest

from exact_solvers import acoustics, acoustics_heterogeneous
from helpers import assert_conserves, assert_far_field

CASES = [
    # q_l = (p, u), q_r, aux_l = (rho, K), aux_r
    ((1.0, 0.0), (0.0, 0.0), (1.0, 1.0), (1.0, 1.0)),
    ((10.0, -5.0), (40.0, 5.0), (2.0, 1.0), (2.0, 1.0)),
    ((1.0, 0.5), (0.2, -0.3), (1.0, 1.0), (4.0, 0.5)),
    ((0.0, 1.0), (0.0, 0.0), (2.0, 8.0), (1.0, 1.0)),
]


def impedance_middle_state(q_l, q_r, aux_l, aux_r):
    """Middle state from continuity of p and u across the material interface:
    p_m = (Z_r p_l + Z_l p_r + Z_l Z_r (u_l - u_r)) / (Z_l + Z_r),
    u_m = (Z_l u_l + Z_r u_r + p_l - p_r) / (Z_l + Z_r)."""
    (p_l, u_l), (p_r, u_r) = q_l, q_r
    Z_l = np.sqrt(aux_l[0] * aux_l[1])
    Z_r = np.sqrt(aux_r[0] * aux_r[1])
    p_m = (Z_r * p_l + Z_l * p_r + Z_l * Z_r * (u_l - u_r)) / (Z_l + Z_r)
    u_m = (Z_l * u_l + Z_r * u_r + p_l - p_r) / (Z_l + Z_r)
    return np.array([p_m, u_m])


def acoustics_flux(aux):
    """f(q) = (K u, p / rho)."""
    rho, K = aux
    return lambda q: np.array([K * q[1], q[0] / rho])


@pytest.mark.parametrize("q_l, q_r, aux, _", [c for c in CASES if c[2] == c[3]])
def test_homogeneous(q_l, q_r, aux, _):
    q_l, q_r = np.array(q_l), np.array(q_r)
    states, speeds, reval = acoustics.exact_riemann_solution(q_l, q_r, aux)
    c = np.sqrt(aux[1] / aux[0])
    np.testing.assert_allclose(speeds, [-c, c])
    assert acoustics.lambda1(q_l, 0, aux) == pytest.approx(-c)
    assert acoustics.lambda2(q_l, 0, aux) == pytest.approx(c)
    np.testing.assert_allclose(states[:, 1], impedance_middle_state(q_l, q_r, aux, aux))
    assert_far_field(reval, q_l, q_r)
    flux = acoustics_flux(aux)
    assert_conserves(reval, flux, flux, q_l, q_r, L=2 * c + 1)


@pytest.mark.parametrize("q_l, q_r, aux_l, aux_r", CASES)
def test_heterogeneous(q_l, q_r, aux_l, aux_r):
    q_l, q_r = np.array(q_l), np.array(q_r)
    states, speeds, reval = acoustics_heterogeneous.exact_riemann_solution(q_l, q_r, aux_l, aux_r)
    c_l, c_r = np.sqrt(aux_l[1] / aux_l[0]), np.sqrt(aux_r[1] / aux_r[0])
    np.testing.assert_allclose(speeds, [-c_l, c_r])
    assert acoustics_heterogeneous.lambda1_het(q_l, 0, aux_l) == pytest.approx(-c_l)
    assert acoustics_heterogeneous.lambda2_het(q_r, 0, aux_r) == pytest.approx(c_r)
    np.testing.assert_allclose(states[:, 1], impedance_middle_state(q_l, q_r, aux_l, aux_r))
    assert_far_field(reval, q_l, q_r)

    # With piecewise-constant (rho, K) the conserved quantities are the strain
    # p/K and the momentum rho u, with fluxes (u, p) that are continuous at x = 0.
    def conserved(q, aux):
        rho, K = aux
        return np.array([q[0] / K, rho * q[1]])

    def conserved_reval(xi):
        p, u = reval(xi)
        rho = np.where(xi < 0, aux_l[0], aux_r[0])
        K = np.where(xi < 0, aux_l[1], aux_r[1])
        return p / K, rho * u

    def flux(aux):
        rho, K = aux
        return lambda w: np.array([w[1] / rho, K * w[0]])

    assert_conserves(conserved_reval, flux(aux_l), flux(aux_r),
                     conserved(q_l, aux_l), conserved(q_r, aux_r), L=2 * max(c_l, c_r) + 1)
