"""Scalar conservation laws with general (possibly nonconvex) flux, solved with
Osher's formula: q(xi) minimizes (q_l <= q_r) or maximizes (q_l > q_r)
f(q) - xi q over q between q_l and q_r."""

import numpy as np
import pytest

from exact_solvers import burgers, nonconvex
from helpers import assert_conserves, evaluate

burgers_flux = lambda q: 0.5 * q**2
a = 0.5
buckley_leverett_flux = lambda q: q**2 / (q**2 + a * (1 - q)**2)
cubic_flux = lambda q: q**3


def as_reval(qtilde):
    """Wrap Osher's qtilde(xi) in the (num_eqn, len(xi)) convention."""
    return lambda xi: qtilde(np.asarray(xi, dtype=float)).reshape(1, -1)


# The solution is sampled at n = 1000 values of q, so it is accurate to
# about |q_r - q_l| / 1000.
Q_TOL = 2e-3


@pytest.mark.parametrize("q_l, q_r", [(2.0, 1.0), (1.0, 2.0), (-1.0, 1.0), (1.0, -1.0)])
def test_convex_flux_matches_burgers(q_l, q_r):
    qtilde = nonconvex.osher_solution(burgers_flux, q_l, q_r)
    _, _, reval, _ = burgers.exact_riemann_solution(q_l, q_r)
    xi = np.linspace(-3, 3, 601)
    xi = xi[np.abs(xi - (q_l + q_r) / 2) > 1e-2]   # avoid the shock location itself
    np.testing.assert_allclose(qtilde(xi), evaluate(reval, xi)[0], atol=Q_TOL)


def test_buckley_leverett_shock_rarefaction():
    """For q_l = 1, q_r = 0 the solution is a rarefaction from 1 down to q*,
    followed by a shock from q* to 0, where the shock speed equals the
    characteristic speed at q*: f'(q*) = f(q*)/q*, giving q* = sqrt(a/(1+a))."""
    qtilde = nonconvex.osher_solution(buckley_leverett_flux, 1.0, 0.0)
    q_star = np.sqrt(a / (1 + a))
    s = buckley_leverett_flux(q_star) / q_star
    q = qtilde(np.array([s - 1e-3, s + 1e-3]))
    assert q[0] == pytest.approx(q_star, abs=Q_TOL)
    assert q[1] == pytest.approx(0.0, abs=Q_TOL)


@pytest.mark.parametrize("flux, q_l, q_r", [
    (buckley_leverett_flux, 1.0, 0.0),
    (buckley_leverett_flux, 0.0, 1.0),
    (cubic_flux, 1.0, -1.0),
    (cubic_flux, -0.5, 1.0),
])
def test_conservation(flux, q_l, q_r):
    reval = as_reval(nonconvex.osher_solution(flux, q_l, q_r))
    assert_conserves(reval, flux, flux, q_l, q_r, L=5.0, rtol=Q_TOL, num_points=20001)


def test_nonconvex_solutions_with_given_xi_range():
    xi, q, q_char, xi_char = nonconvex.nonconvex_solutions(cubic_flux, 1.0, -1.0, -4.0, 4.0)
    assert xi[0] == -4.0 and xi[-1] == 4.0
    np.testing.assert_allclose(q, nonconvex.osher_solution(cubic_flux, 1.0, -1.0)(xi))
    # Characteristic tracing: each q_char moves with speed f'(q) (interior values).
    np.testing.assert_allclose(xi_char[1:-1], 3 * q_char[1:-1]**2, atol=1e-2)


def test_nonconvex_solutions_with_default_xi_range():
    xi, q, _, _ = nonconvex.nonconvex_solutions(cubic_flux, 1.0, -1.0)
    assert np.all(np.isfinite(xi)) and np.all(np.isfinite(q))
