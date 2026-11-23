"""TVD wave limiters for the high-resolution wave-propagation method.

Each wave W_{i-1/2} is multiplied by phi(theta), where theta compares it with the
wave of the same family at the neighbouring interface in the upwind direction:
    theta = (W_upwind . W_{i-1/2}) / (W_{i-1/2} . W_{i-1/2}).
(LeVeque, Finite Volume Methods for Hyperbolic Problems, 2002, Sections 6.12 and 9.13.)
"""

import numpy as np

# Limiter codes, as in Clawpack.
minmod = 1
superbee = 2
vanleer = 3
MC = 4


def phi(theta, limiter):
    """Limiter function phi(theta) for the limiter code ``limiter``."""
    if limiter == minmod:
        return np.maximum(0.0, np.minimum(1.0, theta))
    if limiter == superbee:
        return np.maximum.reduce([np.zeros_like(theta), np.minimum(1.0, 2.0 * theta),
                                  np.minimum(2.0, theta)])
    if limiter == vanleer:
        return (theta + np.abs(theta)) / (1.0 + np.abs(theta))
    if limiter == MC:
        return np.maximum(0.0, np.minimum.reduce([(1.0 + theta) / 2.0,
                                                  np.full_like(theta, 2.0), 2.0 * theta]))
    raise ValueError(f"Unknown limiter {limiter}")


def limit(wave, s, limiters):
    """Return limited copies of the waves.

    wave has shape (num_eqn, num_waves, num_interfaces) and s (num_waves, num_interfaces).
    ``limiters`` is one limiter code, or one per wave family (0 = no limiting).
    The first and last interfaces have no upwind neighbour on one side and are not limited.
    """
    num_waves = wave.shape[1]
    codes = np.broadcast_to(np.atleast_1d(limiters), (num_waves,))
    limited = wave.copy()
    norm2 = np.sum(wave**2, axis=0)                         # (num_waves, n)
    dot = np.sum(wave[:, :, 1:] * wave[:, :, :-1], axis=0)  # W_k . W_{k+1}, (num_waves, n-1)
    upwind_dot = np.where(s[:, 1:-1] > 0, dot[:, :-1], dot[:, 1:])
    inner_norm2 = norm2[:, 1:-1]
    nonzero = inner_norm2 > 0
    theta = np.divide(upwind_dot, inner_norm2, out=np.zeros_like(upwind_dot), where=nonzero)
    for mw, code in enumerate(codes):
        if code > 0:
            factor = np.where(nonzero[mw], phi(theta[mw], code), 1.0)
            limited[:, mw, 1:-1] *= factor
    return limited
