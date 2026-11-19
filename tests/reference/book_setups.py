"""The PyClaw runs used in the book's chapters (copied from the notebooks and demos of
clawpack/riemann_book, master), written once for both implementations:

    book_setups.use(pyclaw, riemann)   # clawpack's (generate_reference.py) or miniclaw's (tests)
    claw = book_setups.shallow_dam_break('roe')

Each function returns a finished Controller with all frames kept.
"""

import numpy as np
from scipy import integrate

pyclaw = riemann = None


def use(pyclaw_module, riemann_module):
    """Select the implementation of pyclaw and riemann to run the setups with."""
    global pyclaw, riemann
    pyclaw, riemann = pyclaw_module, riemann_module


def controller(state, domain, solver, tfinal, num_output_times=10):
    claw = pyclaw.Controller()
    claw.tfinal = tfinal
    claw.solution = pyclaw.Solution(state, domain)
    claw.solver = solver
    claw.num_output_times = num_output_times
    claw.keep_copy = True
    claw.output_format = None
    claw.verbosity = 0
    return claw


# --- Burgers_approximate.ipynb -------------------------------------------------------
def burgers_approximate(q_l, q_r, N=200, efix=False):
    solver = pyclaw.ClawSolver1D(riemann.burgers_1D_py.burgers_1D)
    solver.order = 1
    solver.kernel_language = 'Python'
    solver.bc_lower[0] = pyclaw.BC.extrap
    solver.bc_upper[0] = pyclaw.BC.extrap
    x = pyclaw.Dimension(-1.0, 1.0, N, name='x')
    domain = pyclaw.Domain([x])
    state = pyclaw.State(domain, 1)
    state.problem_data['efix'] = efix
    xc = state.grid.p_centers[0]
    state.q[0, :] = (xc <= 0) * q_l + (xc > 0) * q_r
    claw = controller(state, domain, solver, tfinal=0.5)
    claw.run()
    return claw


# --- FV_compare.ipynb ----------------------------------------------------------------
def shallow_dam_break(riemann_solver, N=40):
    rs = {'roe': riemann.shallow_roe_with_efix_1D, 'hlle': riemann.shallow_hlle_1D}[riemann_solver]
    solver = pyclaw.ClawSolver1D(rs)
    solver.bc_lower[0] = pyclaw.BC.extrap
    solver.bc_upper[0] = pyclaw.BC.extrap
    x = pyclaw.Dimension(-5.0, 5.0, N, name='x')
    domain = pyclaw.Domain(x)
    state = pyclaw.State(domain, 2)
    state.problem_data['grav'] = 1.0
    state.problem_data['dry_tolerance'] = 1e-3
    state.problem_data['sea_level'] = 0.0
    xc = state.grid.x.centers
    state.q[0, :] = 10.0 * (xc <= 0) + 0.5 * (xc > 0)
    state.q[1, :] = 0.0
    claw = controller(state, domain, solver, tfinal=1.0)
    claw.run()
    return claw


def euler_solver(riemann_solver, solver_type, kernel_language='Python'):
    if riemann_solver == 'Roe' and kernel_language == 'Fortran':
        rs = riemann.euler_with_efix_1D
    else:
        rs = {'Roe': riemann.euler_1D_py.euler_roe_1D, 'HLL': riemann.euler_1D_py.euler_hll_1D}[riemann_solver]
    if solver_type == 'classic':
        solver = pyclaw.ClawSolver1D(rs)
        solver.limiters = pyclaw.limiters.tvd.MC
    else:
        solver = pyclaw.SharpClawSolver1D(rs)
    solver.kernel_language = kernel_language
    return solver


def euler_state(domain, gamma=1.4):
    state = pyclaw.State(domain, 3)
    state.problem_data['gamma'] = gamma
    state.problem_data['gamma1'] = gamma - 1.
    state.problem_data['efix'] = False
    return state


def shocktube(riemann_solver, solver_type, N=80):
    """Sod shock tube; the book passes (rho, u, p) = (1, 0, 0.4) and (1/8, 0, 0.04)."""
    q_l, q_r = (1.0, 0.0, 0.4), (0.125, 0.0, 0.04)
    gamma = 1.4
    solver = euler_solver(riemann_solver, solver_type)
    solver.bc_lower[0] = pyclaw.BC.extrap
    solver.bc_upper[0] = pyclaw.BC.extrap
    domain = pyclaw.Domain([pyclaw.Dimension(-1.0, 1.0, N, name='x')])
    state = euler_state(domain, gamma)
    xc = state.grid.p_centers[0]
    rho = (xc <= 0) * q_l[0] + (xc > 0) * q_r[0]
    u = (xc <= 0) * q_l[1] + (xc > 0) * q_r[1]
    p = (xc <= 0) * q_l[2] + (xc > 0) * q_r[2]
    state.q[0, :] = rho
    state.q[1, :] = rho * u
    state.q[2, :] = p / (gamma - 1.) + 0.5 * rho * u**2
    claw = controller(state, domain, solver, tfinal=0.5)
    claw.run()
    return claw


def blastwave(riemann_solver, N=400):
    kernel = 'Fortran' if riemann_solver == 'Roe' else 'Python'
    gamma = 1.4
    solver = euler_solver(riemann_solver, 'classic', kernel)
    solver.bc_lower[0] = pyclaw.BC.wall
    solver.bc_upper[0] = pyclaw.BC.wall
    domain = pyclaw.Domain([pyclaw.Dimension(0.0, 1.0, N, name='x')])
    state = euler_state(domain, gamma)
    xc = state.grid.p_centers[0]
    pressure = (xc < 0.1) * 1.e3 + (0.1 <= xc) * (xc < 0.9) * 1.e-2 + (0.9 <= xc) * 1.e2
    state.q[0, :] = 1.
    state.q[1, :] = 0.
    state.q[2, :] = pressure / (gamma - 1.)
    claw = controller(state, domain, solver, tfinal=0.038, num_output_times=30)
    claw.run()
    return claw


# --- Traffic_variable_speed.ipynb ----------------------------------------------------
def traffic_variable_speed(rho_l, rho_r, v_l, v_r, riemann_solver):
    solver = pyclaw.ClawSolver1D(riemann_solver)
    solver.bc_lower[0] = pyclaw.BC.extrap
    solver.bc_upper[0] = pyclaw.BC.extrap
    solver.aux_bc_lower[0] = pyclaw.BC.extrap
    solver.aux_bc_upper[0] = pyclaw.BC.extrap
    domain = pyclaw.Domain(pyclaw.Dimension(-1.0, 1.0, 50, name='x'))
    state = pyclaw.State(domain, solver.num_eqn, 1)
    xc = state.grid.p_centers[0]
    state.q[0, :] = rho_l * (xc < 0) + rho_r * (xc >= 0.)
    state.aux[0, :] = v_l * (xc < 0) + v_r * (xc >= 0.)
    claw = controller(state, domain, solver, tfinal=1.0)
    claw.run()
    return claw


# --- Kitchen_sink_problem.ipynb ------------------------------------------------------
def steady_rhs(h, r, alpha, g=1.):
    return h / (g / alpha**2 * r**3 * h**3 - r)


def kitchen_sink_initial_data(r_jump=1., r_inner=0.5, r_outer=5., num_cells=501, g=1.,
                              h_in=1., u_in=2.):
    r = pyclaw.Dimension(r_inner, r_outer, num_cells, name='r')
    rc = r.centers
    i_jump = np.argmin(np.abs(rc - r_jump))
    h = 0 * rc
    u = 0 * rc
    d = r.delta
    rvals = np.insert(rc[:i_jump + 1], (0), [rc[0] - 2 * d, rc[0] - d])
    beta = rvals[0] * h_in * u_in
    hh = np.squeeze(integrate.odeint(steady_rhs, h_in, rvals, args=(beta, g)))
    uu = beta / (hh * rvals)
    h[:i_jump + 1] = np.squeeze(hh[2:])
    u[:i_jump + 1] = uu[2:]
    lower_bc_data = [hh[:2], uu[:2]]
    h_m = h[i_jump]
    u_m = u[i_jump]
    aleph = (-3 * h_m + np.sqrt(h_m**2 + 8 * h_m * u_m**2 / g)) / 2.
    h_p = h_m + aleph
    u_p = h_m * u_m / h_p
    h[i_jump + 1] = h_p
    u[i_jump + 1] = u_p
    beta_outer = rc[i_jump + 1] * h[i_jump + 1] * u[i_jump + 1]
    rvals = np.append(rc[i_jump + 1:], [rc[-1] + d, rc[-1] + 2 * d])
    hh = np.squeeze(integrate.odeint(steady_rhs, h_p, rvals, args=(beta_outer, g)))
    uu = beta_outer / (rvals * hh)
    h[i_jump + 1:] = hh[:-2]
    u[i_jump + 1:] = uu[:-2]
    upper_bc_data = [hh[-2:], uu[-2:]]
    return h, u, upper_bc_data, lower_bc_data


def step_radial_src(solver, state, dt):
    dt2 = dt / 2.
    q = state.q
    rad = state.grid.r.centers
    h = q[0, :]
    u = q[1, :] / h
    qstar = np.empty(q.shape)
    qstar[0, :] = q[0, :] - dt2 / rad * h * u
    qstar[1, :] = q[1, :] - dt2 / rad * h * u * u
    h = qstar[0, :]
    u = qstar[1, :] / h
    q[0, :] = q[0, :] - dt / rad * h * u
    q[1, :] = q[1, :] - dt / rad * h * u * u


def inner_state(state, dim, t, qbc, auxbc, num_ghost):
    h, u = state.problem_data['lower_bc_data']
    qbc[0, :num_ghost] = h
    qbc[1, :num_ghost] = h * u


def outer_state(state, dim, t, qbc, auxbc, num_ghost):
    h, u = state.problem_data['upper_bc_data']
    qbc[0, -num_ghost:] = h
    qbc[1, -num_ghost:] = h * u


def kitchen_sink(constant_initial_data=False, r_inner=0.5, r_outer=3., num_cells=501, g=1.):
    r = pyclaw.Dimension(r_inner, r_outer, num_cells=num_cells, name='r')
    solver = pyclaw.ClawSolver1D(riemann_solver=riemann.shallow_roe_with_efix_1D)
    solver.bc_lower[0] = pyclaw.BC.custom
    solver.user_bc_lower = inner_state
    solver.bc_upper[0] = pyclaw.BC.custom
    solver.user_bc_upper = outer_state
    solver.step_source = step_radial_src
    domain = pyclaw.Domain([r])
    state = pyclaw.State(domain, solver.num_eqn)
    state.problem_data['grav'] = g
    # Required by shallow_roe_with_efix_1D in current Clawpack (not set in the notebook,
    # which therefore fails with Clawpack 5.14); values as in FV_compare.
    state.problem_data['dry_tolerance'] = 1e-3
    state.problem_data['sea_level'] = 0.0
    if constant_initial_data:
        state.problem_data['lower_bc_data'] = np.array([[0.5, 0.5], [3., 3.]])
        state.problem_data['upper_bc_data'] = np.array([[2., 2.], [0.1, 0.1]])
        state.q[0, :] = 1.
        state.q[1, :] = 0.
    else:
        h, u, upper, lower = kitchen_sink_initial_data(r_inner=r_inner, r_outer=r_outer,
                                                       num_cells=num_cells, g=g)
        state.problem_data['lower_bc_data'] = lower
        state.problem_data['upper_bc_data'] = upper
        state.q[0, :] = h
        state.q[1, :] = h * u
    claw = controller(state, domain, solver, tfinal=15.0, num_output_times=50)
    claw.run()
    return claw


# --- exact_solvers/acoustics_demos.py and burgers_demos.py (bump_pyclaw) -------------
def acoustics_bump(numframes=50):
    claw = pyclaw.Controller()
    claw.tfinal = 5.0
    claw.keep_copy = True
    claw.output_format = None
    claw.num_output_times = numframes
    claw.solver = pyclaw.ClawSolver1D(riemann.acoustics_1D)
    claw.solver.all_bcs = pyclaw.BC.wall
    claw.verbosity = False
    domain = pyclaw.Domain((-2.,), (2.,), (800,))
    claw.solution = pyclaw.Solution(claw.solver.num_eqn, domain)
    x = domain.grid.x.centers
    claw.solution.q[0, :] = 4.0 * np.exp(-10 * (x - 1.0)**2)
    claw.solution.q[1, :] = 0.0
    claw.solver.dt_initial = 1.e99
    rho, bulk = 1.0, 1.0
    claw.solution.problem_data['rho'] = rho
    claw.solution.problem_data['bulk'] = bulk
    claw.solution.problem_data['zz'] = np.sqrt(rho * bulk)
    claw.solution.problem_data['cc'] = np.sqrt(bulk / rho)
    claw.run()
    return claw


def burgers_bump(numframes=50):
    claw = pyclaw.Controller()
    claw.tfinal = 1.5
    claw.keep_copy = True
    claw.output_format = None
    claw.num_output_times = numframes
    claw.solver = pyclaw.ClawSolver1D(riemann.burgers_1D)
    claw.solver.all_bcs = pyclaw.BC.periodic
    claw.verbosity = False
    domain = pyclaw.Domain((-1.,), (1.,), (500,))
    claw.solution = pyclaw.Solution(claw.solver.num_eqn, domain)
    x = domain.grid.x.centers
    claw.solution.q[0, :] = np.exp(-10 * x**2)
    claw.solver.dt_initial = 1.e99
    claw.run()
    return claw
