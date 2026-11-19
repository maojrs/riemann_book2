"""miniclaw's SharpClaw solver: WENO5 reconstruction and SSP(10,4) time stepping."""

import numpy as np
import pytest

from exact_solvers import burgers
from miniclaw import pyclaw, riemann
from miniclaw.sharpclaw import weno5
from test_miniclaw_solver import advection, centers


def cell_averages(F, edges):
    """Cell averages of the function with antiderivative F."""
    return (F(edges[1:]) - F(edges[:-1])) / np.diff(edges)


def test_weno5_is_exact_for_quadratics():
    """Every candidate stencil reproduces a quadratic exactly, so WENO5 does too."""
    edges = np.linspace(0, 1, 21)
    q = cell_averages(lambda x: x**3 / 3 - x**2 + x, edges)[None, :]    # q(x) = x^2 - 2x + 1
    ql, qr = weno5(q)
    f = lambda x: x**2 - 2 * x + 1
    np.testing.assert_allclose(ql[0, 3:-2], f(edges[3:-3]), atol=1e-12)
    np.testing.assert_allclose(qr[0, 2:-3], f(edges[3:-3]), atol=1e-12)


def test_weno5_is_fifth_order_for_smooth_data():
    errors = []
    for N in (40, 80, 160):
        edges = np.linspace(0, 1, N + 1)
        q = cell_averages(lambda x: -np.cos(2 * np.pi * x) / (2 * np.pi), edges)[None, :]
        _, qr = weno5(q)
        errors.append(np.abs(qr[0, 2:-3] - np.sin(2 * np.pi * edges[3:-3])).max())
    rates = np.log2(np.array(errors[:-1]) / errors[1:])
    assert np.all(rates > 4.5), rates


def test_weno5_does_not_oscillate_at_a_jump():
    q = np.where(np.arange(30) < 15, 1.0, 0.0)[None, :]
    ql, qr = weno5(q)
    for edge_values in (ql, qr):
        assert edge_values.min() > -1e-6 and edge_values.max() < 1 + 1e-6


def run_sharpclaw(rs, q0, x_range=(0.0, 1.0), bc=pyclaw.BC.periodic, tfinal=1.0, problem_data=None):
    solver = pyclaw.SharpClawSolver1D(rs)
    solver.all_bcs = bc
    domain = pyclaw.Domain(pyclaw.Dimension(*x_range, len(q0[0])))
    # Start near the right Courant number: with PyClaw's default dt_initial = 0.1 the first
    # (rejected) step on a fine grid overflows before being redone, as in PyClaw.
    solver.dt_initial = domain.grid.delta[0]
    state = pyclaw.State(domain, rs.num_eqn)
    state.q[:] = q0
    state.problem_data.update(problem_data or {})
    claw = pyclaw.Controller()
    claw.solution = pyclaw.Solution(state, domain)
    claw.solver = solver
    claw.tfinal = tfinal
    claw.keep_copy = True
    claw.run()
    return claw


def test_conservation_with_periodic_boundaries():
    claw = run_sharpclaw(riemann.burgers_1D, [1.5 + np.sin(2 * np.pi * centers(100))], tfinal=0.5)
    totals = [f.q.sum() for f in claw.frames]
    np.testing.assert_allclose(totals, totals[0], rtol=1e-13)
    assert claw.solver.cfl <= claw.solver.cfl_max


def test_high_order_accuracy_for_smooth_advection():
    """WENO5 in space with 4th-order SSP104 in time: error rate of at least about 4."""
    errors = []
    for N in (20, 40, 80):
        x = centers(N)
        q0 = cell_averages(lambda x: -np.cos(2 * np.pi * x) / (2 * np.pi), np.linspace(0, 1, N + 1))
        claw = run_sharpclaw(advection, [q0], problem_data={'u': 1.0})
        errors.append(np.abs(claw.frames[-1].q[0] - q0).mean())
    rates = np.log2(np.array(errors[:-1]) / errors[1:])
    assert np.all(rates > 3.8), rates


@pytest.mark.parametrize("q_l, q_r", [(2.0, 1.0), (1.0, 2.0), (-1.0, 2.0)])
def test_converges_to_exact_burgers_solution(q_l, q_r):
    _, _, reval, _ = burgers.exact_riemann_solution(q_l, q_r)
    errors = []
    for N in (100, 200, 400):
        x = centers(N, -1, 1)
        claw = run_sharpclaw(riemann.burgers_1D, [np.where(x <= 0, q_l, q_r)], x_range=(-1, 1),
                             bc=pyclaw.BC.extrap, tfinal=0.5)
        errors.append(2 * np.abs(claw.frames[-1].q[0] - reval(x / 0.5)[0]).mean())
    assert errors[0] > errors[1] > errors[2]
    assert errors[-1] < 0.01
