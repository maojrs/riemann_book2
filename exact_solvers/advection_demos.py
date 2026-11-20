"""
Interactive figures of the chapter Advection, for the web book (utils.live_figure).
The figures are drawn by the functions of advection.py, with the controls of the notebook.
"""
from utils import riemann_tools
from utils.live_figure import InteractiveFigure, slider
from . import advection

# interact(f) makes this slider for the default a=1.
SPEED = slider('a', -1., 3., 1.)

CHARACTERISTICS = InteractiveFigure.redraw(advection.characteristics, [SPEED])
SOLUTION = InteractiveFigure.redraw(advection.solution, [SPEED])
RIEMANN_DEMO = InteractiveFigure.redraw(advection.riemann_demo, [SPEED])


def riemann_solution_plot(q_l, q_r, a=1.):
    """The plotting function of advection.plot_riemann_solution(q_l, q_r, a)."""
    c = lambda q, xi: a
    soln = advection.riemann_solution(q_l, q_r, a)
    return riemann_tools.make_plot_function(*soln, plot_chars=[c])


RIEMANN_SOLUTION = InteractiveFigure.redraw(
    riemann_solution_plot, [slider('t', 0., 1., 0.)], factory=True,
    fixed=dict(which_char=True))

