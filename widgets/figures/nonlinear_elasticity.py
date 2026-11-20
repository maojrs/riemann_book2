"""
Interactive figures of Nonlinear_elasticity, for the web book (utils.live_figure).
The chapter defines its plot function in its own cells; riemann_plot draws it on a live
figure: a new time moves the time line and the curves, and the characteristics are shown or
hidden without building the figure again.
"""
import numpy as np

from exact_solvers import nonlinear_elasticity
from miniclaw import riemann
from utils import riemann_tools
from utils.live_figure import InteractiveFigure, TimeFigure, dropdown, slider
from utils.riemann_figure import drawn_by, plot_riemann_at_time


def dsigma(eps, K1, K2):
    "Derivative of stress w.r.t. strain."
    return K1 + 2*K2*eps

def lambda1(q, xi, aux):
    eps = q[0]
    rho, K1, K2 = aux
    return -np.sqrt(dsigma(eps, K1, K2)/rho)

def lambda2(q, xi, aux):
    return -lambda1(q,xi,aux)


def riemann_plot(q_l, q_r, aux_l, aux_r):
    """The chapter's make_plot_function(q_l, q_r, aux_l, aux_r): its plot_function(t, which_char)."""
    q_l, q_r, aux_l, aux_r = map(np.asarray, (q_l, q_r, aux_l, aux_r))
    states, speeds, reval, wave_types = \
        nonlinear_elasticity.exact_riemann_solution(q_l,q_r,aux_l,aux_r)

    def draw(fig, t, which_char):
        ax, solution_at_time = plot_riemann_at_time(states, speeds, reval, wave_types, t, fig=fig,
                                                    t_pointer=0, extra_axes=True,
                                                    variable_names=['Strain','Momentum'])
        nonlinear_elasticity.phase_plane_plot(q_l, q_r, aux_l, aux_r, ax[3])
        shown = {}                                 # family: its characteristics

        def at_time(t, which_char):
            lambdas = {1: lambda1, 2: lambda2}
            if which_char in lambdas and which_char not in shown:
                shown[which_char] = drawn_by(ax[:1], lambda: riemann_tools.plot_characteristics(
                    reval, lambdas[which_char], (aux_l,aux_r), ax[0]))
            for family, lines in shown.items():    # in the background, under the waves
                for line in lines:
                    line.set_visible(family == which_char)
            return solution_at_time(t)
        return at_time

    def plot_function(t, which_char):
        figure.show(t=t, which_char=which_char)
    plot_function.live_figure = lambda: TimeFigure(draw, (10, 3), background=('which_char',))
    figure = plot_function.live_figure()
    return plot_function


def fwave_solution(q_l, q_r, aux_l, aux_r):
    """The chapter's f-wave solution (miniclaw's nonlinear_elasticity_1D, quadratic stress)."""
    q_l, q_r, aux_l, aux_r = map(np.asarray, (q_l, q_r, aux_l, aux_r))
    solver = riemann.nonlinear_elasticity_1D_py.nonlinear_elasticity_1D
    problem_data = {'stress_relation' : 'quadratic'}
    return riemann_tools.riemann_solution(solver,q_l,q_r,aux_l,aux_r,
                                          problem_data=problem_data,
                                          verbose=False,
                                          stationary_wave=True,
                                          fwave=True)


def fwave_plot(q_l, q_r, aux_l, aux_r):
    """The plot function of the cell that shows the f-wave solution."""
    fw_states, fw_speeds, fw_reval = fwave_solution(q_l, q_r, aux_l, aux_r)
    return riemann_tools.make_plot_function(fw_states,fw_speeds, fw_reval,
                                            layout='vertical',
                                            variable_names=('Strain','Momentum'))


def comparison_plot(q_l, q_r, aux_l, aux_r):
    """The plot function of the cell that compares the exact and f-wave solutions."""
    fw_states, fw_speeds, fw_reval = fwave_solution(q_l, q_r, aux_l, aux_r)
    ex_states, ex_speeds, ex_reval, wave_types = \
        nonlinear_elasticity.exact_riemann_solution(*map(np.asarray, (q_l, q_r, aux_l, aux_r)))
    varnames = nonlinear_elasticity.conserved_variables
    return riemann_tools.make_plot_function([ex_states,fw_states],
                                            [ex_speeds,fw_speeds],
                                            [ex_reval,fw_reval],
                                            [wave_types,['contact']*3],
                                            ['Exact','$f$-wave'],
                                            layout='vertical',
                                            variable_names=varnames)


RIEMANN = InteractiveFigure.redraw(
    riemann_plot,
    [slider('t', 0., 1., 0., step=0.1),
     dropdown('which_char', [None, 1, 2], None, label='Show characteristics')],
    factory=True)
TIME = slider('t', 0., 0.9, 0.4)
FWAVE = InteractiveFigure.redraw(fwave_plot, [TIME], factory=True)
COMPARISON = InteractiveFigure.redraw(comparison_plot, [TIME], factory=True)
