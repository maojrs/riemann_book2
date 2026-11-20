"""
Interactive figures of Burgers, for the web book (utils.live_figure).
The figures of burgers_demos and burgers.py, with the controls of the notebook cells.
"""
from exact_solvers import burgers
from exact_solvers.burgers_demos import (multivalued_solution, rarefaction, rarefaction_figure, shock,
                                         shock_location, unphysical)
from utils.live_figure import InteractiveFigure, checkbox, slider

SHOW_CHARACTERISTICS = checkbox('which_char', True, 'Show characteristics')
MULTIVALUED_SOLUTION = InteractiveFigure.redraw(
    multivalued_solution, [slider('t', 0., 9., 7.75)], fixed=dict(fig=0))
SHOCK_LOCATION = InteractiveFigure.redraw(
    shock_location, [slider('xshock', 6., 10., 7.75, step=0.25)], fixed=dict(fig=0))
SHOCK = InteractiveFigure.redraw(
    shock, [slider('t', 0., 1., 0.5), SHOW_CHARACTERISTICS], factory=True)
RAREFACTION_FIGURE = InteractiveFigure.redraw(rarefaction_figure, [slider('t', 0., 9., 5.)])
RAREFACTION = InteractiveFigure.redraw(
    rarefaction, [slider('t', 0., 1., 0.5), SHOW_CHARACTERISTICS], factory=True)
UNPHYSICAL = InteractiveFigure.redraw(
    unphysical, [slider('t', 0., 1., 0.5), SHOW_CHARACTERISTICS], factory=True)
RIEMANN_SOLUTION = InteractiveFigure.redraw(       # burgers.riemann_solution_interact()
    burgers.plot_riemann,
    [slider('q_l', 0., 1., 0.5, label='$q_l$'), slider('q_r', 0., 1., 0., label='$q_r$'),
     slider('t', 0., 1., 0.1, label='$t$'),
     slider('x_range', 0.1, 5., 1., label='x-axis range')],
    [['q_l', 't'], ['q_r', 'x_range']])
