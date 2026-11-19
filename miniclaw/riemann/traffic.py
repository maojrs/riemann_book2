"""Riemann solvers for LWR traffic with a speed limit v(x) stored in aux[0]:
    q_t + (v(x) q (1 - q))_x = 0,
as Clawpack's rp1_traffic_vc (Godunov flux) and rp1_traffic_vc_fwave (f-wave).
The flux is f = v q (1 - q), with characteristic speed v (1 - 2q) and maximum v/4 at q = 1/2.
"""

import numpy as np

from miniclaw.riemann.solver_info import riemann_solver


def _flux_and_speed(q, v):
    return v * q * (1.0 - q), v * (1.0 - 2.0 * q)


@riemann_solver(num_eqn=1, num_waves=1)
def traffic_vc_1D(q_l, q_r, aux_l, aux_r, problem_data):
    """Godunov's method: the fluctuations are A-dQ = f0 - f_l and A+dQ = f_r - f0, where f0 is
    the flux at x = 0 of the exact Riemann solution with speed limits v_l and v_r."""
    q_l, q_r, v_l, v_r = q_l[0], q_r[0], aux_l[0], aux_r[0]
    f_l, s_l = _flux_and_speed(q_l, v_l)
    f_r, s_r = _flux_and_speed(q_r, v_r)
    # The first true condition gives the interface flux (as the if/elseif chain in Clawpack).
    f0 = np.select(
        [(f_l >= 0.25 * v_r) & (s_r > 0),     # right side cannot take more than its maximum flux
         (f_r >= 0.25 * v_l) & (s_l < 0),     # left side cannot supply more than its maximum
         (s_r <= 0) & (f_l > f_r),            # left-going shock
         (s_l >= 0) & (f_r > f_l),            # right-going shock
         (s_l <= 0) & (s_r >= 0),             # transonic rarefaction: maximum flux
         f_l <= f_r],
        [0.25 * v_r,
         0.25 * v_l,
         f_r,
         f_l,
         0.25 * np.minimum(v_l, v_r),
         f_r],
        default=f_l)
    wave = (q_r - q_l)[np.newaxis, np.newaxis, :]
    s = (0.5 * (s_l + s_r))[np.newaxis, :]
    return wave, s, (f0 - f_l)[np.newaxis, :], (f_r - f0)[np.newaxis, :]


@riemann_solver(num_eqn=1, num_waves=1, fwave=True)
def traffic_vc_fwave_1D(q_l, q_r, aux_l, aux_r, problem_data):
    """f-wave solver: the single f-wave is Z = f_r - f_l. It goes left or right by the sign of
    the characteristic speeds; at a transonic rarefaction it is split at the maximum flux."""
    q_l, q_r, v_l, v_r = q_l[0], q_r[0], aux_l[0], aux_r[0]
    f_l, s_l = _flux_and_speed(q_l, v_l)
    f_r, s_r = _flux_and_speed(q_r, v_r)
    fwave = f_r - f_l
    left_going = (s_l < 0) & (s_r <= 0)
    right_going = (s_l >= 0) & (s_r > 0)
    transonic = (s_l < 0) & (s_r > 0)
    f0 = 0.25 * np.minimum(v_l, v_r)
    s = np.select([left_going, right_going], [s_l, s_r], default=0.5 * (s_l + s_r))
    amdq = np.select([left_going, right_going, transonic, fwave < 0, fwave > 0],
                     [fwave, 0.0, f0 - f_l, fwave, 0.0], default=0.5 * fwave)
    apdq = np.select([left_going, right_going, transonic, fwave < 0, fwave > 0],
                     [0.0, fwave, f_r - f0, 0.0, fwave], default=0.5 * fwave)
    return fwave[np.newaxis, np.newaxis, :], s[np.newaxis, :], amdq[np.newaxis, :], apdq[np.newaxis, :]
