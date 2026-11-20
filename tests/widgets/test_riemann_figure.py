"""riemann_tools.make_plot_function on a live figure (utils.riemann_figure) draws the same
picture as the whole-figure pyplot version it replaced (tests/reference), at every time and
for every choice of characteristics, also after other times were shown."""
import io
import os
import sys
import warnings

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from exact_solvers import acoustics, advection, burgers, euler, shallow_water  # noqa: E402
from utils import riemann_tools  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'reference'))
import riemann_tools_before as before  # noqa: E402


def euler_solution(rho_l, u_l, p_l, rho_r, u_r, p_r, gamma=1.4):
    q_l = euler.primitive_to_conservative(rho_l, u_l, p_l)
    q_r = euler.primitive_to_conservative(rho_r, u_r, p_r)
    return euler.exact_riemann_solution(q_l, q_r, gamma)


def cases():
    """(name, positional arguments, keyword arguments, which_char values) of make_plot_function,
    as the chapters call it."""
    sod = euler_solution(1., 0., 1., .125, 0., .1)
    other = euler_solution(1., 0., 1., .125, 0., .1, gamma=1.67)
    euler_options = dict(layout='vertical', vertical_spacing=0.15, variable_names=euler.primitive_variables,
                         derived_variables=euler.cons_to_prim)
    sw = [shallow_water.exact_riemann_solution(np.array([3., 0.]), np.array([1., 0.]), g)[:4] for g in (1., 2.)]
    return [
        ('advection', advection.riemann_solution(0., 1., 1.), dict(plot_chars=[lambda q, xi: 1.]), [True]),
        ('burgers shock', burgers.exact_riemann_solution(1., 0.),
         dict(plot_chars=[burgers.speed], layout='horizontal', variable_names=['q']), [None, 1]),
        ('euler', sod, dict(plot_chars=[euler.lambda1, euler.lambda2, euler.lambda3], **euler_options),
         [None, 1, 2, 3]),
        ('acoustics', acoustics.exact_riemann_solution(np.array([1., 0.]), np.array([0., 0.]), [1., 4.])[:3],
         dict(layout='vertical', variable_names=['pressure', 'velocity']), [None]),
        ('two euler solutions, named', ([sod[0], other[0]], [sod[1], other[1]], [sod[2], other[2]],
                                        [sod[3], other[3]]),
         dict(names=['gamma = 1.4', 'gamma = 1.67'], **euler_options), [None]),
        ('two shallow water solutions, time legend', tuple(list(x) for x in zip(*sw)),
         dict(show_time_legend=True, layout='horizontal'), [None]),
    ]


def pixels(png):
    return np.asarray(Image.open(io.BytesIO(png)).convert('RGBA')).astype(int)


def legend_outside(fig, kwargs):
    """The one change from before: the legend is outside the plots, right of the last one
    (or of the top one in the vertical layout), instead of loc='best' in the first."""
    ax = fig.axes
    legend = ax[1].get_legend()
    if legend is None:
        return
    title = legend.get_title().get_text()
    legend.remove()
    target = ax[1] if kwargs.get('layout', 'horizontal') == 'vertical' else ax[-1]
    target.legend(kwargs.get('names') or [], title=title or None, loc='upper left',
                  bbox_to_anchor=(1.02, 1), borderaxespad=0)


def before_picture(args, kwargs, t, which_char):
    plt.close('all')
    plot_function = before.make_plot_function(*args, **kwargs)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        plot_function(t, which_char) if kwargs.get('plot_chars') else plot_function(t)
    legend_outside(plt.gcf(), kwargs)
    buffer = io.BytesIO()
    plt.gcf().savefig(buffer, format='png', bbox_inches='tight')
    plt.close('all')
    return pixels(buffer.getvalue())


@pytest.mark.parametrize('name, args, kwargs, which_chars', cases(), ids=[c[0] for c in cases()])
def test_live_figure_is_the_whole_figure(name, args, kwargs, which_chars):
    figure = riemann_tools.make_plot_function(*args, **kwargs).live_figure()
    for which_char in which_chars:
        figure.update(t=0.9, which_char=which_char)          # built at another time
        figure.png()
        for t in (0.1, 0.45, 0.8):
            figure.update(t=t, which_char=which_char)
            live = pixels(figure.png())
            expected = before_picture(args, kwargs, t, which_char)
            assert live.shape == expected.shape, (t, which_char)
            differing = (np.abs(live - expected).max(axis=2) > 40).mean()
            assert differing < 0.0005, f't={t} which_char={which_char}: {100*differing:.3f}% of the pixels differ'


def test_plot_function_shows_the_figure(monkeypatch):
    import IPython.display
    shown = []
    monkeypatch.setattr(IPython.display, 'display', shown.append)
    plot_function = riemann_tools.make_plot_function(*advection.riemann_solution(0., 1., 1.))
    plot_function(0.5)
    figure = plot_function.live_figure()
    figure.update(t=0.5)
    assert len(shown) == 1 and shown[0].data == figure.png()


def test_only_the_time_dependent_parts_are_drawn_again():
    figure = riemann_tools.make_plot_function(*euler_solution(1., 0., 1., .125, 0., .1),
                                              plot_chars=[euler.lambda1, euler.lambda2, euler.lambda3]).live_figure()
    figure.update(t=0.5, which_char=2)
    built = figure.fig
    figure.update(t=0.6, which_char=2)
    assert figure.fig is built                                 # same figure, new curves
    figure.update(t=0.6, which_char=3)
    assert figure.fig is built                                 # other characteristics: added on top
    figure.update(t=0.6, which_char=None)
    assert figure.fig is built and not any(line.get_visible() for line in figure.fig.axes[0].lines
                                           if line.get_linewidth() < 0.5)       # hidden again
