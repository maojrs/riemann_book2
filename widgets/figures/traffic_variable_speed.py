"""
Interactive figures of Traffic_variable_speed, for the web book (utils.live_figure).
The chapter defines its plotting functions in its own cells; here they are drawn on live
figures with the same calls: the axes, waves, characteristics and phase plane once, and a
new time only moves the time line and the curves. plot_all keeps its axes and draws their
contents again.
"""
import numpy as np

from exact_solvers import traffic_variable_speed
from miniclaw import pyclaw, riemann
from utils import riemann_tools
from utils.live_figure import InteractiveFigure, KeptAxesFigure, TimeFigure, checkbox, slider
from utils.riemann_figure import plot_riemann_at_time, riemann_axes


def c(rho, xi, v):
    return v*(1.-2*rho)


def riemann_plot(rho_l, rho_r, v_l, v_r, connect=True):
    """The chapter's make_plot_function(rho_l, rho_r, v_l, v_r, connect): its plot_function(t)."""
    states, speeds, reval, wave_types = \
        traffic_variable_speed.exact_riemann_solution(rho_l,rho_r,v_l,v_r)

    def draw(fig, t):
        ax, at_time = plot_riemann_at_time(states, speeds, reval, wave_types, t, fig=fig,
                                           t_pointer=0, extra_axes=True, variable_names=['Density'])
        riemann_tools.plot_characteristics(reval,c,(v_l,v_r),ax[0],
                          extra_lines=[[[0,0],[0,1]]])
        traffic_variable_speed.phase_plane_plot(rho_l,rho_r,v_l,v_r,
                          axes=ax[2],connect=connect,show=False)
        return at_time

    def plot_function(t):
        figure.show(t=t)
    plot_function.live_figure = lambda: TimeFigure(draw, (9, 3))
    figure = plot_function.live_figure()
    return plot_function


def plot_all(ax, rho_l,rho_r,v_l,v_r,connect=False):
    """The chapter's plot_all, on the axes ax (riemann_axes), which are kept from one change
    to the next."""
    states, speeds, reval, wave_types = \
        traffic_variable_speed.exact_riemann_solution(rho_l,rho_r,v_l,v_r)
    riemann_tools.plot_riemann(states,speeds,reval,wave_types,t=0.5,ax=ax,emptied=True,
                       extra_axes=True,variable_names=[r'$\rho$'])
    riemann_tools.plot_characteristics(reval,c,(v_l,v_r),ax[0],
                                       extra_lines=[[[0,0],[0,1]]])
    ax[1].set_ylim(0,1)
    traffic_variable_speed.phase_plane_plot(rho_l,rho_r,v_l,v_r,
                                            axes=ax[2],connect=connect,show=False)


def test_solver(rho_l, rho_r, v_l, v_r, riemann_solver):
    """The chapter's test_solver, verbatim."""
    solver = pyclaw.ClawSolver1D(riemann_solver)

    solver.bc_lower[0] = pyclaw.BC.extrap
    solver.bc_upper[0] = pyclaw.BC.extrap
    solver.aux_bc_lower[0] = pyclaw.BC.extrap
    solver.aux_bc_upper[0] = pyclaw.BC.extrap

    x = pyclaw.Dimension(-1.0,1.0,50,name='x')
    domain = pyclaw.Domain(x)
    num_aux = 1
    state = pyclaw.State(domain,solver.num_eqn,num_aux)

    grid = state.grid
    xc=grid.p_centers[0]

    state.q[0,:] = rho_l*(xc<0) + rho_r*(xc>=0.)
    state.aux[0,:] = v_l*(xc<0) + v_r*(xc>=0.)  # Speed limit

    claw = pyclaw.Controller()
    claw.tfinal = 1.0
    claw.solution = pyclaw.Solution(state,domain)
    claw.solver = solver
    claw.keep_copy = True
    claw.verbosity = 0

    claw.run()
    return xc, claw.frames


def frames_plot(rho_l, rho_r, v_l, v_r, fwave=False):
    """The chapter's plot_frame(t): the exact solution and miniclaw's (traffic_vc_1D), and
    with fwave=True also traffic_vc_fwave_1D (the second cell)."""
    states, speeds, reval, wave_types = \
        traffic_variable_speed.exact_riemann_solution(rho_l,rho_r,v_l,v_r)
    x, frames = test_solver(rho_l,rho_r,v_l,v_r,riemann.traffic_vc_1D)
    if fwave:
        x, fframes = test_solver(rho_l,rho_r,v_l,v_r,riemann.traffic_vc_fwave_1D)

    def draw(fig, t):
        ax, exact_at_time = plot_riemann_at_time(states, speeds, reval, wave_types, t, fig=fig,
                                                 layout='horizontal', extra_axes=True)
        if fwave:
            riemann_tools.plot_characteristics(reval,c,(v_l,v_r),ax[0])
        else:
            riemann_tools.plot_characteristics(reval,c,(v_l,v_r),ax[0],
                                               extra_lines=[[[0,0],[0,1]]])
        approx, = ax[1].plot(x,frames[int(t*10)].q[0,:],'-sg')
        curves = [approx]
        if fwave:
            fw, = ax[1].plot(x,fframes[int(t*10)].q[0,:],'-or')
            curves.append(fw)
            ax[1].legend(['Exact','Approx','$f$-wave'],loc='upper right',
                         fontsize=10);
            ax[1].set_xlim(-0.2,0.2)
        else:
            ax[1].set_xlim(-0.7, 0.7)
            ax[1].legend(['Exact','Approx'],loc='upper right',fontsize=10);
        traffic_variable_speed.phase_plane_plot(rho_l,rho_r,v_l,v_r,axes=ax[2],show=False)

        def at_time(t):
            curves[0].set_ydata(frames[int(t*10)].q[0,:])
            if fwave:
                curves[1].set_ydata(fframes[int(t*10)].q[0,:])
            return exact_at_time(t) + curves
        return at_time

    def plot_frame(t):
        figure.show(t=t)
    plot_frame.live_figure = lambda: TimeFigure(draw, (9, 3))
    figure = plot_frame.live_figure()
    return plot_frame


RIEMANN = InteractiveFigure.redraw(riemann_plot, [slider('t', 0., 0.9, 0.5)], factory=True)
ALL = InteractiveFigure(
    lambda: KeptAxesFigure(lambda fig: riemann_axes(fig, 3), plot_all, (9, 3)),
    [slider('rho_l', 0., 1., 0.4, label=r'$\rho_l$', step=0.01),
     slider('rho_r', 0., 1., 0.7, label=r'$\rho_r$', step=0.01),
     slider('v_l', 0.1, 2., 1.), slider('v_r', 0.1, 2., 0.4),
     checkbox('connect', False, 'Connect states')],
    [['rho_l', 'rho_r'], ['v_l', 'v_r'], ['connect']])
FRAMES = InteractiveFigure.redraw(frames_plot, [slider('t', 0., 1., 0.5)], factory=True)
