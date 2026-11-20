"""
Interactive figures of Nonconvex_scalar, for the web book (utils.live_figure).
The figures of nonconvex_demos, with the controls of the notebook cells.
"""
import numpy as np

from exact_solvers.nonconvex_demos import make_plot_function, make_plot_function_qsliders
from utils.live_figure import InteractiveFigure, slider

def buckley_leverett(q, a=0.5):
    """The Buckley-Leverett flux of the chapter (f_buckley_leverett, a = 0.5)."""
    return q**2 / (q**2 + a*(1-q)**2)


# The fluxes the chapter defines as lambdas, by name (the web book passes names, not functions)
FLUXES = {
    'buckley_leverett': buckley_leverett,
    'buckley_leverett_leftward': lambda q: -buckley_leverett(q),     # f_BL_leftward
    'sin': lambda q: np.sin(q),                                       # f_sin
    'damped_sin': lambda q: 0.25*(1. - q)*np.sin(1.5*q),              # the last example
}


def riemann_plot(flux, q_left, q_right, xi_left, xi_right):
    """make_plot_function(f, q_left, q_right, xi_left, xi_right) for the flux named `flux`."""
    return make_plot_function(FLUXES[flux], q_left, q_right, xi_left, xi_right)


def riemann_plot_qsliders(flux):
    """make_plot_function_qsliders(f) for the flux named `flux`."""
    return make_plot_function_qsliders(FLUXES[flux])


RIEMANN = InteractiveFigure.redraw(
    riemann_plot, [slider('t', 0., 0.9, 0.8)], factory=True, fixed=dict(fig=0))
RIEMANN_QSLIDERS = InteractiveFigure.redraw(
    riemann_plot_qsliders,
    [slider('t', 0., 0.9, 0.8), slider('q_left', -4., 4., -3.5), slider('q_right', -4., 4., 3.5)],
    factory=True, fixed=dict(fig=0))
