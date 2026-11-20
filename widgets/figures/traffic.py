"""
Interactive figures of Traffic_flow, for the web book (utils.live_figure).
The figures of traffic_demos and traffic_LWR.py, with the controls of the notebook cells.
"""
from exact_solvers import traffic_LWR
from exact_solvers.traffic_demos import green_light, jam
from utils.live_figure import InteractiveFigure, slider

JAM = InteractiveFigure.redraw(
    jam, [slider('rho_l', 0.1, 0.9, 0.5, label=r'$\rho_l$'), slider('t', 0., 1., 0.5)],
    fixed=dict(fig=0))
GREEN_LIGHT = InteractiveFigure.redraw(
    green_light, [slider('rho_r', 0., 0.9, 0.3, label=r'$\rho_r$'), slider('t', 0., 1., 0.)],
    fixed=dict(fig=0))
RIEMANN_SOLUTION = InteractiveFigure.redraw(       # traffic_LWR.riemann_solution_interact()
    traffic_LWR.plot_riemann_traffic,
    [slider('rho_l', 0., 1., 0.5, label=r'$\rho_l$'), slider('rho_r', 0., 1., 0., label=r'$\rho_r$'),
     slider('t', 0., 1., 0.1), slider('xrange', 0.1, 5., 1., label='x-axis range')],
    [['t', 'rho_l', 'xrange'], [None, 'rho_r', None]])      # rho_r under rho_l
