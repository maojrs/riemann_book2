"""Approximate Riemann solvers for the shallow water equations
    h_t + (hu)_x = 0,   (hu)_t + (hu^2 + g h^2/2)_x = 0,
with g = problem_data['grav'] (as Clawpack's rp1_shallow_roe_with_efix, rp1_shallow_hlle
and rp1_shallow_roe_tracer).
"""

import numpy as np

from miniclaw.riemann.solver_info import riemann_solver, wave_sum


def _split_by_sign(wave, s):
    """A-dQ = sum of s_p W_p over s_p < 0, A+dQ over s_p >= 0."""
    return wave_sum(s * (s < 0), wave), wave_sum(s * (s >= 0), wave)


def _roe_waves(q_l, q_r, g):
    """Roe linearization: Roe-averaged velocity u_hat and celerity c_hat, and the two waves
    W_p = a_p (1, u_hat -/+ c_hat) with speeds u_hat -/+ c_hat."""
    h_l, hu_l, h_r, hu_r = q_l[0], q_l[1], q_r[0], q_r[1]
    u_hat = (hu_l / np.sqrt(h_l) + hu_r / np.sqrt(h_r)) / (np.sqrt(h_l) + np.sqrt(h_r))
    c_hat = np.sqrt(0.5 * g * (h_l + h_r))
    dh, dhu = h_r - h_l, hu_r - hu_l
    a1 = 0.5 * (-dhu + (u_hat + c_hat) * dh) / c_hat
    a2 = 0.5 * (dhu - (u_hat - c_hat) * dh) / c_hat
    wave = np.array([[a1, a2],
                     [a1 * (u_hat - c_hat), a2 * (u_hat + c_hat)]])
    s = np.array([u_hat - c_hat, u_hat + c_hat])
    return wave, s, u_hat


def _harten_hyman_amdq(q_l, q_r, wave, s, g):
    """Left-going fluctuation with the Harten-Hyman entropy fix.

    If a wave is a transonic rarefaction (characteristic speed negative on its left and
    positive on its right), only the part of it moving left contributes to A-dQ:
    s_fract = s_left (s_right - s) / (s_right - s_left)."""
    with np.errstate(divide='ignore', invalid='ignore'):
        # 1-wave: from q_l to q_l + W1
        s0 = q_l[1] / q_l[0] - np.sqrt(g * q_l[0])
        h1, hu1 = q_l[0] + wave[0, 0], q_l[1] + wave[1, 0]
        s1 = hu1 / h1 - np.sqrt(g * h1)
        transonic1 = (s0 < 0) & (s1 > 0)
        sfract1 = np.where(transonic1, s0 * (s1 - s[0]) / (s1 - s0), np.where(s[0] < 0, s[0], 0.0))
        # 2-wave: from q_r - W2 to q_r
        s3 = q_r[1] / q_r[0] + np.sqrt(g * q_r[0])
        h2, hu2 = q_r[0] - wave[0, 1], q_r[1] - wave[1, 1]
        s2 = hu2 / h2 + np.sqrt(g * h2)
        transonic2 = (s2 < 0) & (s3 > 0)
        sfract2 = np.where(transonic2, s2 * (s3 - s[1]) / (s3 - s2), np.where(s[1] < 0, s[1], 0.0))
    # Entirely right-going flow: no left-going fluctuation at all.
    supersonic_right = (s0 >= 0) & (s[0] > 0)
    sfract1 = np.where(supersonic_right, 0.0, sfract1)
    sfract2 = np.where(supersonic_right, 0.0, sfract2)
    return sfract1 * wave[:, 0, :] + sfract2 * wave[:, 1, :]


@riemann_solver(num_eqn=2, num_waves=2)
def shallow_roe_with_efix_1D(q_l, q_r, aux_l, aux_r, problem_data):
    """Roe solver with the Harten-Hyman entropy fix."""
    g = problem_data['grav']
    wave, s, _ = _roe_waves(q_l, q_r, g)
    amdq = _harten_hyman_amdq(q_l, q_r, wave, s, g)
    apdq = wave_sum(s, wave) - amdq     # A-dQ + A+dQ = sum_p s_p W_p
    return wave, s, amdq, apdq


@riemann_solver(num_eqn=3, num_waves=3)
def shallow_roe_tracer_1D(q_l, q_r, aux_l, aux_r, problem_data):
    """Roe solver with entropy fix plus a passive tracer (q[2]) carried at the Roe velocity.

    Clawpack's Fortran version adds the tracer wave using a stale loop index and an
    uninitialized apdq(3); here the tracer wave simply goes to A-dQ or A+dQ by its sign."""
    g = problem_data['grav']
    flow_wave, flow_s, u_hat = _roe_waves(q_l[:2], q_r[:2], g)
    n = q_l.shape[1]
    wave = np.zeros((3, 3, n))
    wave[:2, :2] = flow_wave
    wave[2, 2] = q_r[2] - q_l[2]
    s = np.vstack([flow_s, u_hat])
    amdq = np.zeros((3, n))
    amdq[:2] = _harten_hyman_amdq(q_l, q_r, flow_wave, flow_s, g)
    apdq = np.zeros((3, n))
    apdq[:2] = wave_sum(flow_s, flow_wave) - amdq[:2]
    amdq[2] = np.minimum(u_hat, 0.0) * wave[2, 2]
    apdq[2] = np.maximum(u_hat, 0.0) * wave[2, 2]
    return wave, s, amdq, apdq


@riemann_solver(num_eqn=2, num_waves=2)
def shallow_hlle_1D(q_l, q_r, aux_l, aux_r, problem_data):
    """HLLE solver: two waves with Einfeldt's speed estimates
        s1 = min(u_l - c_l, u_hat - c_hat),  s2 = max(u_r + c_r, u_hat + c_hat),
    separated by the single middle state that makes the scheme conservative."""
    g = problem_data['grav']
    h_l, hu_l, h_r, hu_r = q_l[0], q_l[1], q_r[0], q_r[1]
    dry = (h_l < 1e-14) & (h_r < 1e-14)
    with np.errstate(divide='ignore', invalid='ignore'):
        u_l, u_r = hu_l / h_l, hu_r / h_r
        c_l, c_r = np.sqrt(g * h_l), np.sqrt(g * h_r)
        u_hat = (np.sqrt(h_l) * u_l + np.sqrt(h_r) * u_r) / (np.sqrt(h_l) + np.sqrt(h_r))
        c_hat = np.sqrt(g * 0.5 * (h_l + h_r))
        s1 = np.minimum(u_l - c_l, u_hat - c_hat)
        s2 = np.maximum(u_r + c_r, u_hat + c_hat)
        h_m = (hu_r - hu_l - s2 * h_r + s1 * h_l) / (s1 - s2)
        hu_m = (hu_r * (u_r - s2) - hu_l * (u_l - s1) + 0.5 * g * (h_r**2 - h_l**2)) / (s1 - s2)
    wave = np.array([[h_m - h_l, h_r - h_m],
                     [hu_m - hu_l, hu_r - hu_m]])
    s = np.array([s1, s2])
    wave[:, :, dry] = 0.0
    s[:, dry] = 0.0
    amdq, apdq = _split_by_sign(wave, s)
    return wave, s, amdq, apdq
