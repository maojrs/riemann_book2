"""Approximate Riemann solvers for the Euler equations of an ideal gas,
    rho_t + (rho u)_x = 0,  (rho u)_t + (rho u^2 + p)_x = 0,  E_t + (u (E + p))_x = 0,
    p = (gamma - 1)(E - rho u^2/2),
as Clawpack's euler_1D_py.euler_roe_1D / euler_hll_1D (problem_data['gamma1'] = gamma - 1)
and the Fortran rp1_euler_with_efix (problem_data['gamma']).
"""

import numpy as np

from miniclaw.riemann.solver_info import riemann_solver, wave_sum


def _pressure(q, gamma1):
    return gamma1 * (q[2] - 0.5 * q[1]**2 / q[0])


def roe_averages(q_l, q_r, gamma1):
    """Roe-averaged velocity u, sound speed a and enthalpy H, and the pressures p_l, p_r."""
    sqrt_rho_l, sqrt_rho_r = np.sqrt(q_l[0]), np.sqrt(q_r[0])
    p_l, p_r = _pressure(q_l, gamma1), _pressure(q_r, gamma1)
    weight = sqrt_rho_l + sqrt_rho_r
    u = (q_l[1] / sqrt_rho_l + q_r[1] / sqrt_rho_r) / weight
    H = ((q_l[2] + p_l) / sqrt_rho_l + (q_r[2] + p_r) / sqrt_rho_r) / weight
    a = np.sqrt(gamma1 * (H - 0.5 * u**2))
    return u, a, H, p_l, p_r


def _roe_waves(q_l, q_r, gamma1):
    """Project the jump on the eigenvectors of the Roe matrix:
    r1 = (1, u-a, H-ua), r2 = (1, u, u^2/2), r3 = (1, u+a, H+ua)."""
    u, a, H, _, _ = roe_averages(q_l, q_r, gamma1)
    delta = q_r - q_l
    a2 = gamma1 / a**2 * ((H - u**2) * delta[0] + u * delta[1] - delta[2])
    a3 = (delta[1] + (a - u) * delta[0] - a * a2) / (2.0 * a)
    a1 = delta[0] - a2 - a3
    wave = np.array([[a1, a2, a3],
                     [a1 * (u - a), a2 * u, a3 * (u + a)],
                     [a1 * (H - u * a), a2 * 0.5 * u**2, a3 * (H + u * a)]])
    s = np.array([u - a, u, u + a])
    return wave, s


def _split_by_sign(wave, s):
    return wave_sum(np.minimum(s, 0.0), wave), wave_sum(np.maximum(s, 0.0), wave)


@riemann_solver(num_eqn=3, num_waves=3)
def euler_roe_1D(q_l, q_r, aux_l, aux_r, problem_data):
    """Roe solver (no entropy fix; Clawpack's Python version raises an error if efix is set)."""
    if problem_data.get('efix', False):
        raise NotImplementedError("Use euler_with_efix_1D for the entropy fix")
    wave, s = _roe_waves(q_l, q_r, problem_data['gamma1'])
    amdq, apdq = _split_by_sign(wave, s)
    return wave, s, amdq, apdq


@riemann_solver(num_eqn=3, num_waves=2)
def euler_hll_1D(q_l, q_r, aux_l, aux_r, problem_data):
    """HLL solver: speeds s1 = min(u_l - a_l, u_hat - a_hat), s2 = max(u_r + a_r, u_hat + a_hat)
    and the middle state q_hat = (f(q_r) - f(q_l) - s2 q_r + s1 q_l) / (s1 - s2)."""
    gamma1 = problem_data['gamma1']
    u, a, _, p_l, p_r = roe_averages(q_l, q_r, gamma1)
    u_l, u_r = q_l[1] / q_l[0], q_r[1] / q_r[0]
    a_l = np.sqrt(gamma1 * ((q_l[2] + p_l) / q_l[0] - 0.5 * u_l**2))
    a_r = np.sqrt(gamma1 * ((q_r[2] + p_r) / q_r[0] - 0.5 * u_r**2))
    s1 = np.min([u + a, u - a, u_l + a_l, u_l - a_l], axis=0)
    s2 = np.max([u + a, u - a, u_r + a_r, u_r - a_r], axis=0)
    flux_l = np.array([q_l[1], q_l[1]**2 / q_l[0] + p_l, (q_l[2] + p_l) * q_l[1] / q_l[0]])
    flux_r = np.array([q_r[1], q_r[1]**2 / q_r[0] + p_r, (q_r[2] + p_r) * q_r[1] / q_r[0]])
    q_hat = (flux_r - flux_l - s2 * q_r + s1 * q_l) / (s1 - s2)
    wave = np.stack([q_hat - q_l, q_r - q_hat], axis=1)
    s = np.array([s1, s2])
    amdq, apdq = _split_by_sign(wave, s)
    return wave, s, amdq, apdq


@riemann_solver(num_eqn=3, num_waves=3)
def euler_with_efix_1D(q_l, q_r, aux_l, aux_r, problem_data):
    """Roe solver with the Harten-Hyman entropy fix (as Clawpack's Fortran rp1_euler_with_efix).

    A transonic 1- or 3-rarefaction contributes to A-dQ only with
    s_fract = s_left (s_right - s) / (s_right - s_left)."""
    gamma = problem_data['gamma']
    gamma1 = gamma - 1.0
    wave, s = _roe_waves(q_l, q_r, gamma1)

    def u_minus_c(q):
        return q[1] / q[0] - np.sqrt(gamma * _pressure(q, gamma1) / q[0])

    def u_plus_c(q):
        return q[1] / q[0] + np.sqrt(gamma * _pressure(q, gamma1) / q[0])

    with np.errstate(divide='ignore', invalid='ignore'):
        # 1-wave: from q_l to q_l + W1
        s0, s1 = u_minus_c(q_l), u_minus_c(q_l + wave[:, 0])
        sfract1 = np.where((s0 < 0) & (s1 > 0), s0 * (s1 - s[0]) / (s1 - s0),
                           np.where(s[0] < 0, s[0], 0.0))
        # 3-wave: from q_r - W3 to q_r
        s2, s3 = u_plus_c(q_r - wave[:, 2]), u_plus_c(q_r)
        sfract3 = np.where((s2 < 0) & (s3 > 0), s2 * (s3 - s[2]) / (s3 - s2),
                           np.where(s[2] < 0, s[2], 0.0))
    supersonic_right = (s0 >= 0) & (s[0] > 0)       # everything moves right: A-dQ = 0
    contact_right = s[1] >= 0                       # then the 3-wave moves right too
    sfract1 = np.where(supersonic_right, 0.0, sfract1)
    sfract2 = np.where(supersonic_right | contact_right, 0.0, s[1])
    sfract3 = np.where(supersonic_right | contact_right, 0.0, sfract3)
    amdq = wave_sum(np.array([sfract1, sfract2, sfract3]), wave)
    apdq = wave_sum(s, wave) - amdq
    return wave, s, amdq, apdq
