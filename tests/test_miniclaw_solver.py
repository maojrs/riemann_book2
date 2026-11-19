"""miniclaw's classic wave-propagation solver: limiters, boundary conditions,
time stepping, conservation, accuracy and convergence."""

import numpy as np
import pytest

from exact_solvers import burgers
from miniclaw import pyclaw, riemann
from miniclaw.limiters import tvd
from miniclaw.riemann.solver_info import riemann_solver


@riemann_solver(num_eqn=1, num_waves=1)
def advection(q_l, q_r, aux_l, aux_r, problem_data):
    """Advection q_t + u q_x = 0 with constant velocity u."""
    u = problem_data['u']
    wave = (q_r - q_l)[:, None, :]
    s = np.full((1, q_l.shape[1]), u)
    return wave, s, min(u, 0) * wave[:, 0, :], max(u, 0) * wave[:, 0, :]


@riemann_solver(num_eqn=1, num_waves=1, fwave=True)
def advection_fwave(q_l, q_r, aux_l, aux_r, problem_data):
    """Same problem split into f-waves Z = f(q_r) - f(q_l)."""
    u = problem_data['u']
    wave = (u * (q_r - q_l))[:, None, :]
    s = np.full((1, q_l.shape[1]), u)
    return wave, s, (u < 0) * wave[:, 0, :], (u >= 0) * wave[:, 0, :]


def run(rs, q0, x_range=(0.0, 1.0), bc=pyclaw.BC.periodic, tfinal=1.0, num_output_times=10,
        problem_data=None, **solver_options):
    """Run a 1D problem; returns the controller."""
    N = len(q0[0])
    solver = pyclaw.ClawSolver1D(rs)
    solver.all_bcs = bc
    for key, val in solver_options.items():
        setattr(solver, key, val)
    domain = pyclaw.Domain(pyclaw.Dimension(*x_range, N))
    state = pyclaw.State(domain, rs.num_eqn)
    state.q[:] = q0
    state.problem_data.update(problem_data or {})
    claw = pyclaw.Controller()
    claw.solution = pyclaw.Solution(state, domain)
    claw.solver = solver
    claw.tfinal = tfinal
    claw.num_output_times = num_output_times
    claw.keep_copy = True
    claw.run()
    return claw


def centers(N, lower=0.0, upper=1.0):
    return pyclaw.Dimension(lower, upper, N).centers


# --- Grid ----------------------------------------------------------------------------
def test_grid():
    x = pyclaw.Dimension(-1.0, 1.0, 4, name='r')
    np.testing.assert_allclose(x.centers, [-0.75, -0.25, 0.25, 0.75])
    assert x.delta == 0.5
    domain = pyclaw.Domain([x])
    assert domain.grid.r is x and domain.grid.num_cells == [4]
    assert pyclaw.Domain((-1.,), (1.,), (4,)).grid.x.num_cells == 4
    state = pyclaw.State(domain, 2, 1)
    assert state.q.shape == (2, 4) and state.aux.shape == (1, 4)
    solution = pyclaw.Solution(3, domain)
    assert solution.q.shape == (3, 4) and solution.t == 0.0


# --- Limiters -------------------------------------------------------------------------
@pytest.mark.parametrize("limiter, theta, expected", [
    (tvd.minmod, [-1, 0.5, 1, 3], [0, 0.5, 1, 1]),
    (tvd.superbee, [-1, 0.25, 0.75, 1.5, 3], [0, 0.5, 1, 1.5, 2]),
    (tvd.vanleer, [-1, 1, 3], [0, 1, 1.5]),
    (tvd.MC, [-1, 0.25, 1, 2, 5], [0, 0.5, 1, 1.5, 2]),
])
def test_limiter_functions(limiter, theta, expected):
    np.testing.assert_allclose(tvd.phi(np.array(theta, float), limiter), expected)


def test_limiter_uses_upwind_neighbour():
    # Waves 1, 2, 4 with positive speed: theta at the middle interface is 1*2/(2*2) = 1/2.
    wave = np.array([[[1.0, 2.0, 4.0]]])
    limited = tvd.limit(wave, np.ones((1, 3)), tvd.minmod)
    assert limited[0, 0, 1] == pytest.approx(1.0)     # 2 * phi(1/2)
    limited = tvd.limit(wave, -np.ones((1, 3)), tvd.minmod)
    assert limited[0, 0, 1] == pytest.approx(2.0)     # theta = 4*2/4 = 2, phi = 1


# --- Boundary conditions --------------------------------------------------------------
def ghost_cells(bc):
    solver = pyclaw.ClawSolver1D(riemann.acoustics_1D)
    solver.all_bcs = bc
    state = pyclaw.State(pyclaw.Domain(pyclaw.Dimension(0, 1, 4)), 2)
    state.q[:] = [[1, 2, 3, 4], [5, 6, 7, 8]]
    qbc, _ = solver._with_ghost_cells(state)
    return qbc


def test_extrapolation_boundary():
    np.testing.assert_array_equal(ghost_cells(pyclaw.BC.extrap),
                                  [[1, 1, 1, 2, 3, 4, 4, 4], [5, 5, 5, 6, 7, 8, 8, 8]])


def test_periodic_boundary():
    np.testing.assert_array_equal(ghost_cells(pyclaw.BC.periodic),
                                  [[3, 4, 1, 2, 3, 4, 1, 2], [7, 8, 5, 6, 7, 8, 5, 6]])


def test_wall_boundary_mirrors_and_negates_velocity():
    np.testing.assert_array_equal(ghost_cells(pyclaw.BC.wall),
                                  [[2, 1, 1, 2, 3, 4, 4, 3], [-6, -5, 5, 6, 7, 8, -8, -7]])


def test_custom_boundary():
    solver = pyclaw.ClawSolver1D(riemann.burgers_1D)
    solver.bc_lower[0] = pyclaw.BC.custom
    solver.bc_upper[0] = pyclaw.BC.extrap

    def inflow(state, dim, t, qbc, auxbc, num_ghost):
        qbc[0, :num_ghost] = 9.0

    solver.user_bc_lower = inflow
    state = pyclaw.State(pyclaw.Domain(pyclaw.Dimension(0, 1, 3)), 1)
    qbc, _ = solver._with_ghost_cells(state)
    np.testing.assert_array_equal(qbc[0, :2], [9, 9])


def test_unset_boundary_condition_is_an_error():
    solver = pyclaw.ClawSolver1D(riemann.burgers_1D)
    state = pyclaw.State(pyclaw.Domain(pyclaw.Dimension(0, 1, 3)), 1)
    with pytest.raises(ValueError):
        solver._with_ghost_cells(state)


# --- Time stepping -------------------------------------------------------------------
def test_output_times_are_hit_exactly():
    claw = run(advection, [np.sin(2 * np.pi * centers(50))], tfinal=0.7, num_output_times=7,
               problem_data={'u': 1.0})
    np.testing.assert_allclose([f.t for f in claw.frames], np.linspace(0, 0.7, 8), rtol=0, atol=1e-15)


def test_time_step_respects_cfl_max():
    """Starting from a huge dt_initial, the step is rejected and redone at cfl_desired."""
    claw = run(advection, [np.sin(2 * np.pi * centers(50))], problem_data={'u': 1.0},
               dt_initial=1e99)
    assert claw.solver.cfl <= claw.solver.cfl_max


def test_source_term_godunov_splitting():
    """With q_t = -q as source and zero flux, q decays like exp(-t) (to first order in dt)."""
    def decay(solver, state, dt):
        state.q *= 1 - dt

    claw = run(advection, [np.ones(20)], problem_data={'u': 0.0}, step_source=decay,
               dt_variable=False, dt_initial=1e-3)
    np.testing.assert_allclose(claw.frames[-1].q, np.exp(-1.0), rtol=1e-3)


# --- Conservation and accuracy -------------------------------------------------------
@pytest.mark.parametrize("order", [1, 2])
@pytest.mark.parametrize("limiter", [tvd.minmod, tvd.superbee, tvd.vanleer, tvd.MC, 0])
def test_conservation_with_periodic_boundaries(order, limiter):
    x = centers(100)
    claw = run(riemann.burgers_1D, [1.5 + np.sin(2 * np.pi * x)], order=order, limiters=limiter)
    totals = [f.q.sum() for f in claw.frames]
    np.testing.assert_allclose(totals, totals[0], rtol=1e-13)


def test_advection_at_cfl_one_is_exact():
    """With dt = dx and speed 1 the method shifts the data one cell per step."""
    N = 40
    q0 = np.where(np.abs(centers(N) - 0.3) < 0.1, 1.0, 0.0)
    claw = run(advection, [q0], tfinal=0.25, num_output_times=1, problem_data={'u': 1.0},
               dt_variable=False, dt_initial=1 / N, cfl_max=1.0)
    np.testing.assert_allclose(claw.frames[-1].q[0], np.roll(q0, N // 4), atol=1e-14)


@pytest.mark.parametrize("limiter", [tvd.minmod, tvd.superbee, tvd.vanleer, tvd.MC])
def test_limited_solutions_are_tvd(limiter):
    """Total variation does not increase, and no new extrema appear."""
    q0 = np.where(np.abs(centers(100) - 0.5) < 0.2, 1.0, 0.0)
    claw = run(advection, [q0], problem_data={'u': 1.0}, limiters=limiter)
    tv = [np.abs(np.diff(f.q[0], append=f.q[0, 0])).sum() for f in claw.frames]
    assert np.all(np.diff(tv) <= 1e-12)
    for f in claw.frames:
        assert f.q.min() >= -1e-14 and f.q.max() <= 1 + 1e-14


def test_unlimited_second_order_is_second_order_accurate():
    """Lax-Wendroff (no limiter) on a smooth wave: error ratio about 4 per refinement."""
    errors = []
    for N in (50, 100, 200):
        x = centers(N)
        claw = run(advection, [np.sin(2 * np.pi * x)], problem_data={'u': 1.0}, limiters=0)
        errors.append(np.abs(claw.frames[-1].q[0] - np.sin(2 * np.pi * x)).mean())
    rates = np.log2(np.array(errors[:-1]) / errors[1:])
    assert np.all(rates > 1.9)


def test_fwave_and_wave_forms_agree_for_constant_coefficients():
    q0 = [np.where(np.abs(centers(80) - 0.5) < 0.2, 1.0, 0.0)]
    for u in (1.0, -0.7):
        a = run(advection, q0, problem_data={'u': u}, limiters=tvd.MC)
        b = run(advection_fwave, q0, problem_data={'u': u}, limiters=tvd.MC)
        np.testing.assert_allclose(a.frames[-1].q, b.frames[-1].q, atol=1e-13)


@pytest.mark.parametrize("q_l, q_r", [(2.0, 1.0), (1.0, 2.0), (-1.0, 2.0)])
@pytest.mark.parametrize("order", [1, 2])
def test_converges_to_exact_burgers_solution(q_l, q_r, order):
    """L1 error to the exact Riemann solution decreases under grid refinement."""
    _, _, reval, _ = burgers.exact_riemann_solution(q_l, q_r)
    errors = []
    for N in (100, 200, 400):
        x = centers(N, -1, 1)
        q0 = np.where(x <= 0, q_l, q_r)
        claw = run(riemann.burgers_1D, [q0], x_range=(-1, 1), bc=pyclaw.BC.extrap, tfinal=0.5,
                   num_output_times=1, order=order)
        errors.append(2 * np.abs(claw.frames[-1].q[0] - reval(x / 0.5)[0]).mean())
    assert errors[0] > errors[1] > errors[2]
    assert errors[-1] < 0.05
