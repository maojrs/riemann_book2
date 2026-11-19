"""Shared checks for exact Riemann solutions.

Every exact solver returns a self-similar solution q(x/t) through a function
``reval(xi)``. The checks below test properties that any correct solution of
a conservation law must have, independently of how it was computed.
"""

import numpy as np


def evaluate(reval, xi):
    """Return reval(xi) as an array of shape (num_eqn, len(xi))."""
    q = np.array(reval(np.asarray(xi, dtype=float)), dtype=float)
    return q.reshape(-1, len(xi))


def conservation_residual(reval, flux_l, flux_r, q_l, q_r, L, t=1.0, source=0.0,
                          num_points=400001):
    """Integral form of q_t + f(q, x)_x = source * delta(x) on [-L, L].

    For a Riemann problem whose waves stay inside [-L, L] up to time t,
        int_{-L}^{L} q(x, t) dx = L (q_l + q_r) + t (f_l(q_l) - f_r(q_r) + source).
    flux_l and flux_r are the fluxes at x < 0 and x > 0 (they differ for
    spatially varying coefficients). Returns the difference between the
    numerical integral of the solution and this value, one entry per equation.
    """
    x = np.linspace(-L, L, num_points)
    q = evaluate(reval, x / t)
    integral = np.trapezoid(q, x, axis=1)
    q_l, q_r = np.atleast_1d(q_l).astype(float), np.atleast_1d(q_r).astype(float)
    expected = L * (q_l + q_r) + t * (np.atleast_1d(flux_l(q_l)) - np.atleast_1d(flux_r(q_r))
                                      + source)
    return integral - expected


def assert_conserves(reval, flux_l, flux_r, q_l, q_r, L, source=0.0, rtol=1e-4,
                     num_points=400001):
    """Assert the integral conservation law holds up to quadrature error."""
    residual = conservation_residual(reval, flux_l, flux_r, q_l, q_r, L, source=source,
                                     num_points=num_points)
    # Quadrature error scales with the size of the terms in the balance.
    q_l, q_r = np.atleast_1d(q_l).astype(float), np.atleast_1d(q_r).astype(float)
    scale = (L * (np.abs(q_l) + np.abs(q_r))
             + np.abs(np.atleast_1d(flux_l(q_l))) + np.abs(np.atleast_1d(flux_r(q_r))) + 1.0)
    np.testing.assert_array_less(np.abs(residual), rtol * scale,
                                 err_msg=f"conservation residual {residual}")


def assert_far_field(reval, q_l, q_r, xi_far=1e3):
    """Far from the origin the solution equals the initial left/right states."""
    q = evaluate(reval, [-xi_far, xi_far])
    np.testing.assert_allclose(q[:, 0], np.atleast_1d(q_l), rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(q[:, 1], np.atleast_1d(q_r), rtol=1e-12, atol=1e-12)


def assert_rankine_hugoniot(flux, q_minus, q_plus, speed, rtol=1e-8, atol=1e-10):
    """Jump condition s (q+ - q-) = f(q+) - f(q-) across a discontinuity."""
    q_minus, q_plus = np.atleast_1d(q_minus), np.atleast_1d(q_plus)
    np.testing.assert_allclose(speed * (q_plus - q_minus),
                               np.atleast_1d(flux(q_plus)) - np.atleast_1d(flux(q_minus)),
                               rtol=rtol, atol=atol)


def max_speed(speeds):
    """Largest |wave speed|, with rarefactions given as (left, right) pairs."""
    return max(abs(float(s)) for s in np.hstack([np.atleast_1d(s) for s in speeds]))
