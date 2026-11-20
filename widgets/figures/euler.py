"""
Interactive figures of Euler, for the web book (utils.live_figure).
The figures of euler_demos and euler.py, with the controls of the notebook cells.
"""
from exact_solvers import euler
from exact_solvers.euler_demos import plot_with_stripes, stripes_demo
from utils import riemann_tools
from utils.live_figure import InteractiveFigure, checkbox, dropdown, slider

CURVE_SLIDERS = [slider('gamma', 1.1, 3., 1.4), slider('rho_0', 0.1, 3., 1., label=r'$\rho_0$')]
INTEGRAL_CURVES = InteractiveFigure.redraw(
    euler.plot_integral_curves,
    [checkbox('plot_1', True, '1-wave curves'), checkbox('plot_3', False, '3-wave curves')] + CURVE_SLIDERS)
HUGONIOT_LOCI = InteractiveFigure.redraw(
    euler.plot_hugoniot_loci,
    [checkbox('plot_1', True, 'Plot 1-loci'), checkbox('plot_3', False, 'Plot 3-loci')] + CURVE_SLIDERS)


def riemann_solution_plot(left_state, right_state, gamma=1.4):
    """The plotting function of euler.riemann_solution(left_state, right_state, gamma)."""
    q_left = euler.primitive_to_conservative(*left_state)
    q_right = euler.primitive_to_conservative(*right_state)
    ex_states, ex_speeds, reval, wave_types = euler.exact_riemann_solution(q_left, q_right, gamma)
    return riemann_tools.make_plot_function(ex_states, ex_speeds, reval, wave_types,
                                            layout='vertical',
                                            vertical_spacing=0.15,
                                            variable_names=euler.primitive_variables,
                                            plot_chars=[euler.lambda1, euler.lambda2, euler.lambda3],
                                            derived_variables=euler.cons_to_prim)


RIEMANN_SOLUTION = InteractiveFigure.redraw(
    riemann_solution_plot,
    [slider('t', 0., 0.9, 0.5),
     dropdown('which_char', [None, 1, 2, 3], None, label='Show characteristics:')],
    factory=True)

# plot_with_stripes with only a time slider (the cell's plot_with_stripes_t_slider)
STRIPES = InteractiveFigure.redraw(plot_with_stripes, [slider('t', 0., 1., 0.5)])

# euler_demo1(...)
DEMO1 = InteractiveFigure.redraw(
    stripes_demo,
    [slider('rho_l', 1., 10., 2., label=r'$\rho_l$'), slider('u_l', -10., 10., 0., label='$u_l$'),
     slider('p_l', 1., 10., 2.5, label='$p_l$'), slider('rho_r', 1., 10., 3., label=r'$\rho_r$'),
     slider('u_r', -10., 10., 0., label='$u_r$'), slider('p_r', 1., 10., 5., label='$p_r$'),
     slider('gamma', 1.1, 2., 1.4, label=r'$\gamma$'), slider('t', 0., 1., 0.5)],
    [['t'], ['rho_l', 'rho_r', 'gamma'], ['u_l', 'u_r'], ['p_l', 'p_r']])
