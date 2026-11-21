"""
Interactive figures of Acoustics_heterogeneous, for the web book (utils.live_figure).
The phase plane of acoustics_heterogeneous_demos.interactive_phase_plane, with its controls,
and the Riemann solution of acoustics_heterogeneous.riemann_plot_func.
"""
import numpy as np

from exact_solvers import acoustics_heterogeneous, acoustics_heterogeneous_demos
from utils.live_figure import InteractiveFigure, checkbox, dropdown, number, slider

def riemann_plot(q_l, q_r, auxl, auxr):
    """acoustics_heterogeneous.riemann_plot_func, with the states as arrays (as the cells give them)."""
    return acoustics_heterogeneous.riemann_plot_func(np.array(q_l), np.array(q_r), auxl, auxr)


RIEMANN = InteractiveFigure.redraw(
    riemann_plot,
    [slider('t', 0., 1., 0.), dropdown('which_char', [None, 1, 2], None, label='Show characteristics')],
    factory=True)

# The tabs "Left and right states" and "Material parameters" above the figure, "Plot options"
# apart. The notebook's boxes for the slider ranges (rho_max, K_max) are left out.
PHASE_PLANE = InteractiveFigure.redraw(
    acoustics_heterogeneous_demos.phase_plane_plot,
    [slider('pl', 0.01, 50., 10., label='$p_l$'), slider('ul', -30., 30., -5., label='$u_l$'),
     slider('pr', 0.01, 50., 40., label='$p_r$'), slider('ur', -30., 30., 5., label='$u_r$'),
     slider('rhol', 0.01, 10., 1., label=r'$\rho_l$'), slider('bulkl', 0.01, 10., 2., label='$K_l$'),
     slider('rhor', 0.01, 10., 2., label=r'$\rho_r$'), slider('bulkr', 0.01, 10., 8., label='$K_r$'),
     number('xmin', 0.0000001, label='$p_{min}:$', min=0., max=100.),
     number('xmax', 50., label='$p_{max}:$'),
     number('ymin', -30., label='$u_{min}:$'), number('ymax', 30., label='$u_{max}:$'),
     checkbox('show_phys', True, 'Physical solution'),
     checkbox('show_unphys', True, 'Unphysical solution')],
    [['pl', 'ul'], ['pr', 'ur'], ['rhol', 'rhor'], ['bulkl', 'bulkr']],
    factory=True,
    options=['show_phys', 'show_unphys', 'xmin', 'xmax', 'ymin', 'ymax'])
