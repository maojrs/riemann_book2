"""
Interactive figures of the chapter FV_compare, for the web book (utils.live_figure).
setup, shocktube and blastwave are the chapter's own functions, verbatim, except that each
imports the constants it uses (the chapter imports the shallow water and the Euler
constants in turn, with the same names); the *_frames functions run the cells' examples and
return their plot_frame.
"""
import matplotlib.pyplot as plt
import numpy as np

from exact_solvers import euler
from exact_solvers import shallow_water as sw
from miniclaw import riemann
from utils.live_figure import InteractiveFigure, slider


def setup(riemann_solver='roe',N=20,IC='dam-break'):

    from miniclaw import pyclaw
    from miniclaw.riemann.shallow_roe_with_efix_1D_constants import depth, momentum, num_eqn

    if riemann_solver.lower() == 'roe':
        rs = riemann.shallow_roe_with_efix_1D
    elif riemann_solver.lower() == 'hlle':
        rs = riemann.shallow_hlle_1D
 
    solver = pyclaw.ClawSolver1D(rs)
        
    solver.bc_lower[0] = pyclaw.BC.extrap
    solver.bc_upper[0] = pyclaw.BC.extrap

    xlower = -5.0
    xupper = 5.0
    x = pyclaw.Dimension(xlower,xupper,N,name='x')
    domain = pyclaw.Domain(x)
    state = pyclaw.State(domain,num_eqn)

    # Gravitational constant
    state.problem_data['grav'] = 1.0
    state.problem_data['dry_tolerance'] = 1e-3
    state.problem_data['sea_level'] = 0.0
    
    xc = state.grid.x.centers

    x0=0.

    hl = 10.
    ul = 0.
    hr = 0.5
    ur = 0.
    state.q[depth,:] = hl * (xc <= x0) + hr * (xc > x0)
    state.q[momentum,:] = hl*ul * (xc <= x0) + hr*ur * (xc > x0)

    claw = pyclaw.Controller()
    claw.keep_copy = True
    claw.output_format = None
    claw.tfinal = 1.0
    claw.solution = pyclaw.Solution(state,domain)
    claw.solver = solver

    return claw


def shocktube(q_l, q_r, N=50, riemann_solver='HLL', 
              solver_type='classic'):

    from miniclaw import pyclaw
    from miniclaw import riemann
    from miniclaw.riemann.euler_with_efix_1D_constants import density, momentum, energy, num_eqn

    if riemann_solver == 'Roe':
        rs = riemann.euler_1D_py.euler_roe_1D
    elif riemann_solver == 'HLL':
        rs = riemann.euler_1D_py.euler_hll_1D

    if solver_type == 'classic':
        solver = pyclaw.ClawSolver1D(rs)        
        solver.limiters = pyclaw.limiters.tvd.MC
    else:
        solver = pyclaw.SharpClawSolver1D(rs)

    solver.kernel_language = 'Python'
    
    solver.bc_lower[0]=pyclaw.BC.extrap
    solver.bc_upper[0]=pyclaw.BC.extrap

    x = pyclaw.Dimension(-1.0,1.0,N,name='x')
    domain = pyclaw.Domain([x])
    state = pyclaw.State(domain,num_eqn)

    gamma = 1.4
    state.problem_data['gamma']= gamma
    state.problem_data['gamma1']= gamma-1.

    state.problem_data['efix'] = False

    xc = state.grid.p_centers[0]
    
    velocity = (xc<=0)*q_l[1] + (xc>0)*q_r[1]
    pressure = (xc<=0)*q_l[2] + (xc>0)*q_r[2]

    state.q[density ,:] = (xc<=0)*q_l[0] + (xc>0)*q_r[0]
    state.q[momentum,:] = velocity * state.q[density,:]
    state.q[energy  ,:] = pressure/(gamma - 1.) + \
                          0.5 * state.q[density,:] * velocity**2

    claw = pyclaw.Controller()
    claw.tfinal = 0.5
    claw.solution = pyclaw.Solution(state,domain)
    claw.solver = solver
    claw.num_output_times = 10
    claw.keep_copy = True
    claw.verbosity=0

    return claw


def blastwave(N=400, riemann_solver='HLL', solver_type='classic'):

    from miniclaw import pyclaw
    from miniclaw import riemann
    from miniclaw.riemann.euler_with_efix_1D_constants import density, momentum, energy, num_eqn

    if riemann_solver == 'Roe':
        kernel_language = 'Fortran'
        rs = riemann.euler_with_efix_1D
    elif riemann_solver == 'HLL':
        kernel_language = 'Python'
        rs = riemann.euler_1D_py.euler_hll_1D

    if solver_type == 'classic':
        solver = pyclaw.ClawSolver1D(rs)
        solver.limiters = pyclaw.limiters.tvd.MC
    else:
        solver = pyclaw.SharpClawSolver1D(rs)

    solver.kernel_language = kernel_language
    
    solver.bc_lower[0]=pyclaw.BC.wall
    solver.bc_upper[0]=pyclaw.BC.wall

    x = pyclaw.Dimension(0.0,1.0,N,name='x')
    domain = pyclaw.Domain([x])
    state = pyclaw.State(domain,num_eqn)

    gamma = 1.4
    state.problem_data['gamma']= gamma
    state.problem_data['gamma1']= gamma-1.

    state.problem_data['efix'] = False

    xc = state.grid.p_centers[0]

    pressure = (xc<0.1)*1.e3 + (0.1<=xc)*(xc<0.9)*1.e-2 + (0.9<=xc)*1.e2
    
    state.q[density ,:] = 1.
    state.q[momentum,:] = 0.
    state.q[energy  ,:] = pressure / (gamma - 1.)

    claw = pyclaw.Controller()
    claw.tfinal = 0.038
    claw.solution = pyclaw.Solution(state,domain)
    claw.solver = solver
    claw.num_output_times = 30
    claw.keep_copy = True
    claw.verbosity=0

    return claw


def dam_break_frames(N=40):
    """The shallow water dam break: Roe, HLLE and exact solutions; returns plot_frame(i)."""
    from miniclaw.riemann.shallow_roe_with_efix_1D_constants import depth, momentum
    q_l = [10,0]
    q_r = [0.5,0]

    # Roe solution
    roe_sw = setup(riemann_solver='roe',N=N)
    roe_sw.verbosity = 0
    roe_sw.run()
    xc_sw = roe_sw.grid.x.centers

    # HLLE solution
    hlle_sw = setup(riemann_solver='hlle',N=N)
    hlle_sw.verbosity = 0
    hlle_sw.run()

    # Exact solution
    xc_exact_sw = np.linspace(-5,5,2000)
    states_sw, speeds_sw, reval_sw, wave_types_sw = \
                    sw.exact_riemann_solution(q_l, q_r)
    def plot_frame(i):
        t = roe_sw.frames[i].t+1.e-13
        fig, ax = plt.subplots(2,1, sharex=True, figsize=(8,5))
        variablenames = ["Depth", "Momentum"]
        variables = [depth, momentum]
        ylims = [[-1,12], [-5,12]]
        plt.subplots_adjust(hspace=0)
        ax[0].title.set_text('Solutions at t={:.2f}'.format(t))
        ax[0].set_xlim((-5,5))
        ax[1].set(xlabel = 'x')
        for j, variable in enumerate(variables):
            ax[j].set_ylim(ylims[j])
            ax[j].plot(xc_exact_sw,reval_sw(xc_exact_sw/(t+1.e-16))[j],'-k',lw=1)
            ax[j].plot(xc_sw, hlle_sw.frames[i].q[variable,:],'-ob',lw=2,markersize=4)
            ax[j].plot(xc_sw, roe_sw.frames[i].q[variable,:],'-or',lw=0.5,markersize=3)
            ax[j].set(ylabel=variablenames[j])
        ax[0].legend(['Exact','HLLE','Roe'],loc='upper left',bbox_to_anchor=(1.01,1))
        plt.show()
    return plot_frame


def shocktube_frames(N=80, solver_type='classic'):
    """Sod's shock tube: HLL, Roe and exact solutions, with the classic or the SharpClaw
    solver (the two cells draw the same figure); returns plot_frame(i)."""
    from miniclaw.riemann.euler_with_efix_1D_constants import density, momentum, energy
    prim_l = [1.,0.,1.]
    prim_r = [1./8,0.,1./10]
    q_l = euler.conservative_to_primitive(*prim_l)
    q_r = euler.conservative_to_primitive(*prim_r)

    roe_st = shocktube(q_l,q_r,N=N,riemann_solver='Roe',solver_type=solver_type)
    roe_st.run()
    hll_st = shocktube(q_l,q_r,N=N,riemann_solver='HLL',solver_type=solver_type)
    hll_st.run()
    xc_st = roe_st.solution.state.grid.p_centers[0]

    # Exact solution
    xc_exact_st = np.linspace(-1,1,2000)
    states_st, speeds_st, reval_st, wave_types_st = euler.exact_riemann_solution(prim_l, prim_r)
    def plot_frame(i):
        t = roe_st.frames[i].t
        fig, ax = plt.subplots(3,1, sharex=True, figsize=(8,6))
        variablenames = ["Density", "Momentum", "Energy"]
        variables = [density, momentum, energy]
        ylims = [[0,1.1], [-0.05,0.35], [0,1.1]]
        plt.subplots_adjust(hspace=0)
        ax[0].title.set_text('Solutions at t={:.2f}'.format(t))
        ax[0].set_xlim((-1,1))
        ax[2].set(xlabel = 'x')
        for j, variable in enumerate(variables):
            ax[j].set_ylim(ylims[j])
            ax[j].plot(xc_exact_st,reval_st(xc_exact_st/(t+1.e-16))[j],'-k',lw=1)
            ax[j].plot(xc_st,hll_st.frames[i].q[variable,:],'-ob',lw=2,markersize=4)
            ax[j].plot(xc_st,roe_st.frames[i].q[variable,:],'-or',lw=0.5,markersize=3)
            ax[j].set(ylabel=variablenames[j])
        ax[0].legend(['Exact','HLL','Roe'],loc='upper left',bbox_to_anchor=(1.01,1))
        plt.show()
    return plot_frame


def blastwave_frames(N=400):
    """The blast wave: HLL, Roe and a fine Roe solution; returns plot_frame(i)."""
    from miniclaw.riemann.euler_with_efix_1D_constants import density, momentum, energy
    roe_bw = blastwave(N=N, riemann_solver='Roe')
    roe_bw.run()
    hll_bw = blastwave(N=N, riemann_solver='HLL')
    hll_bw.run()
    fine_bw = blastwave(N=4000,riemann_solver='Roe')
    fine_bw.run()
    xc_bw = roe_bw.solution.state.grid.p_centers[0]
    xc_fine_bw = fine_bw.solution.state.grid.p_centers[0]
    def plot_frame(i):
        t = roe_bw.frames[i].t
        fig, ax = plt.subplots(3,1, sharex=True, figsize=(8,6))
        variablenames = ["Density", "Momentum", "Energy"]
        variables = [density, momentum, energy]
        ylims = [[-1,10], [-50,120], [-300,3000]]
        plt.subplots_adjust(hspace=0)
        ax[0].title.set_text('Solutions at t={:.3f}'.format(t))
        ax[0].set_xlim((0,1))
        ax[2].set(xlabel = 'x')
        for j, variable in enumerate(variables):
            ax[j].set_ylim(ylims[j])
            ax[j].plot(xc_fine_bw,fine_bw.frames[i].q[variable,:],'-k',lw=1)
            ax[j].plot(xc_bw,hll_bw.frames[i].q[variable,:],'-b',lw=2)
            ax[j].plot(xc_bw,roe_bw.frames[i].q[variable,:],'--r',lw=2)
            ax[j].set(ylabel=variablenames[j])
        ax[0].legend(['Fine','HLL','Roe'],loc='upper left',bbox_to_anchor=(1.01,1))
        plt.show()
    return plot_frame


DAM_BREAK = InteractiveFigure.redraw(
    dam_break_frames, [slider('i', 0, 10, 5, integer=True)], factory=True)
SHOCKTUBE = InteractiveFigure.redraw(
    shocktube_frames, [slider('i', 0, 10, 5, label='Frame', integer=True)], factory=True)
BLASTWAVE = InteractiveFigure.redraw(
    blastwave_frames, [slider('i', 0, 30, 15, label='Frame', integer=True)], factory=True)
