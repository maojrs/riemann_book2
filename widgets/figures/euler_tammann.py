"""
Interactive figures of Euler_Tammann, for the web book (utils.live_figure).
The phase plane of interactive_pplanes.euler_tammann_interactive_phase_plane, with its
controls, and the chapter's Riemann solution plot (plot_riemann_solution).
"""
import numpy as np

from exact_solvers import euler_tammann, interactive_pplanes
from utils import riemann_tools
from utils.live_figure import InteractiveFigure, checkbox, dropdown, number, slider


def riemann_plot(q_l, q_r, auxl, auxr):
    """The plot function of the chapter's plot_riemann_solution(q_l, q_r, auxl, auxr)."""
    ex_states, ex_speeds, reval, wave_types, varsout = \
        euler_tammann.exact_riemann_solution(q_l ,q_r, auxl, auxr,
                                             varin='primitive',
                                             varout='primitive')
    varnames = euler_tammann.primitive_variables
    return riemann_tools.make_plot_function(ex_states, ex_speeds,
                                            reval, wave_types,
                                            layout='vertical',
                                            variable_names=varnames,
                                            aux=(np.array(auxl), np.array(auxr)),
                                            plot_chars=[euler_tammann.lambda1,
                                                        euler_tammann.lambda2,
                                                        euler_tammann.lambda3],
                                            contact_index=1)


RIEMANN = InteractiveFigure.redraw(
    riemann_plot,
    [slider('t', 0., 1., 0.), dropdown('which_char', [None, 1, 2, 3], None, label='Show characteristics')],
    factory=True)

# The tabs "Left and right states" and "Tammann EOS" above the figure, "Plot options" apart.
# The notebook's boxes for the slider ranges (rho_max, gamma_max, p_inf max) are left out.
PHASE_PLANE = InteractiveFigure.redraw(
    interactive_pplanes.euler_tammann_phase_plane_plot,
    [slider('rhol', 0.01, 1000., 600., label=r'$\rho_l$'), slider('ul', -15., 15., 10., label='$u_l$'),
     slider('pl', 1., 200000., 50000., label='$p_l$'),
     slider('rhor', 0.01, 1000., 50., label=r'$\rho_r$'), slider('ur', -15., 15., -10., label='$u_r$'),
     slider('pr', 1., 200000., 25000., label='$p_r$'),
     slider('gammal', 0.01, 10., 1.4, label=r'$\gamma_l$'),
     slider('pinfl', 0., 300000., 0., label=r'$p_{\infty l}$'),
     slider('gammar', 0.01, 10., 7., label=r'$\gamma_r$'),
     slider('pinfr', 0., 300000., 100., label=r'$p_{\infty r}$'),
     number('xmin', 0.0000001, label='$p_{min}:$', min=0., max=100.),
     number('xmax', 200000., label='$p_{max}:$'),
     number('ymin', -15., label='$u_{min}:$'), number('ymax', 15., label='$u_{max}:$'),
     checkbox('show_phys', True, 'Physical solution'),
     checkbox('show_unphys', True, 'Unphysical solution')],
    [['rhol', 'ul', 'pl'], ['rhor', 'ur', 'pr'], ['gammal', 'pinfl'], ['gammar', 'pinfr']],
    factory=True,
    options=['show_phys', 'show_unphys', 'xmin', 'xmax', 'ymin', 'ymax'])
