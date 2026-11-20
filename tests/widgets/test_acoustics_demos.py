"""acoustics_demos: the interactive figures, rewritten on utils.live_figure, must look like
the original ones (tests/reference/acoustics_demos_before.py), in the notebook and on the web."""

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

from exact_solvers import acoustics_demos  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'reference'))
import acoustics_demos_before as before  # noqa: E402

DPI = 100


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')


def png_pixels(fig):
    """The figure as Jupyter shows it: PNG with a tight bounding box."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=DPI, bbox_inches='tight')
    return np.asarray(Image.open(buffer).convert('RGBA')).astype(int)


def original_pixels(plot, **values):
    """Pixels of the original plotting function's figure."""
    plt.close('all')
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='FigureCanvasAgg is non-interactive')
        plot(**values)
    return png_pixels(plt.gcf())


def frame_pixels(frame):
    return np.frombuffer(frame['rgba'], np.uint8).reshape(frame['height'], frame['width'], 4).astype(int)


def assert_same_picture(new, original):
    """Same size; pixels may only differ where overlapping lines are drawn in another order."""
    assert new.shape == original.shape
    differing = (np.abs(new - original).max(axis=2) > 40).mean()
    assert differing < 0.002, f'{100*differing:.3f}% of the pixels differ'


# Each case: interactive figure, setup, original plotting function, list of control values.
# The values change several things at once, so the web frames also exercise redrawing
# after the axis limits or the characteristics change.
CASES = {
    'decompose_q': (acoustics_demos.DECOMPOSE_Q, None, lambda: before.decompose_q,
                    [dict(p=1., u=0.3, K=1., rho=1.), dict(p=-0.4, u=0.8, K=1.7, rho=0.3),
                     dict(p=0.9, u=-1., K=0.1, rho=2.)]),
    'char_solution': (acoustics_demos.CHAR_SOLUTION, None, lambda: before.char_solution,
                      [dict(t=0., K=1., rho=1.), dict(t=0.7, K=1.9, rho=0.4), dict(t=1.2, K=1.9, rho=0.4)]),
    'phase_plane': (acoustics_demos.PHASE_PLANE, None, before.phase_plane_plot,
                    [dict(pl=3., ul=2., pr=3., ur=-2., rho=0.5, bulk=2., xmin=1e-7, xmax=10., ymin=-5., ymax=5.),
                     dict(pl=8., ul=-1., pr=2., ur=3., rho=1.5, bulk=2., xmin=1e-7, xmax=10., ymin=-5., ymax=5.),
                     dict(pl=8., ul=-1., pr=2., ur=3., rho=1.5, bulk=2., xmin=1., xmax=20., ymin=-8., ymax=3.)]),
    'riemann_plot_pplane': (acoustics_demos.RIEMANN_PLOT_PPLANE, dict(ql=[5, 0], qr=[1, 0], rho=1., bulk=4.),
                            lambda: before.full_riemann_solution_plot_fixed(np.array([5, 0]), np.array([1, 0]), 1., 4.),
                            [dict(t=0., which_char=None), dict(t=0.6, which_char=1),
                             dict(t=0.3, which_char=2), dict(t=0.9, which_char=None)]),
}


@pytest.mark.parametrize('name', CASES)
def test_notebook_figure_looks_like_the_original(name):
    figure, setup, original, value_list = CASES[name]
    for values in value_list:
        live = figure.figure(**(setup or {}))
        live.update(**values)
        assert_same_picture(png_pixels(live.fig), original_pixels(original(), **values))


@pytest.mark.parametrize('name', CASES)
def test_web_frames_look_like_the_original(name):
    """One live figure updated in turn with each set of values, as on the web."""
    figure, setup, original, value_list = CASES[name]
    live = figure.figure(**(setup or {}))
    for values in value_list:
        live.update(**values)
        assert_same_picture(frame_pixels(live.frame()), original_pixels(original(), **values))


def test_phase_plane_hides_the_middle_state_outside_the_plot():
    live = acoustics_demos.PhasePlane()
    live.update(pl=1., ul=0., pr=9., ur=0., rho=1., bulk=1., xmin=0, xmax=10, ymin=-1, ymax=1)
    lines, points, labels = live.artists
    np.testing.assert_allclose(points[2].get_data(), [[5.], [-4.]])    # p_m = 5, u_m = -4 < u_min
    assert not points[2].get_visible() and not labels[2].get_visible()


def test_riemann_plot_pplane_solution_at_time_t():
    """The plotted pressure and velocity are the exact solution at time t."""
    live = acoustics_demos.FullRiemannFixed(ql=[5, 0], qr=[1, 0], rho=1., bulk=4.)
    live.update(t=0.4, which_char=None)
    x, p = live.curves[0].get_data()
    reval = live.riemann_eval
    np.testing.assert_allclose(p, reval(x/(0.4 + 1e-10))[0])
    assert list(live.t_line.get_ydata()) == [0.4, 0.4]


# --- Controls ---------------------------------------------------------------------------
def test_notebook_widgets_follow_the_controls():
    widgets = acoustics_demos.PHASE_PLANE.notebook_widgets(pl=3., ul=2., pr=3., ur=-2., rho=0.5, bulk=2.)
    assert (widgets['pl'].min, widgets['pl'].max, widgets['pl'].value) == (0.01, 10., 3.)
    assert widgets['rho'].description == r'$\rho$'
    assert (widgets['xmin'].min, widgets['xmin'].max) == (0, 100)            # BoundedFloatText
    widgets = acoustics_demos.RIEMANN_PLOT_PPLANE.notebook_widgets()
    assert widgets['which_char'].options == (None, 1, 2) and widgets['which_char'].value is None


@pytest.mark.parametrize('show', [
    acoustics_demos.decompose_q_interactive,
    acoustics_demos.char_solution_interactive,
    lambda: acoustics_demos.interactive_phase_plane(np.array([3, 2]), np.array([3, -2]), 0.5, 2.),
    lambda: acoustics_demos.riemann_plot_pplane(np.array([5, 0]), np.array([1, 0]), 1., 4.),
])
def test_notebook_interactive_functions_run(show):
    show()


def test_original_plot_functions_still_work():
    """The names the original module offered still draw the figures."""
    acoustics_demos.decompose_q(1., 0.3, 1., 1.)
    acoustics_demos.char_solution(0.5, 1., 1.)
    acoustics_demos.phase_plane_plot()(3., 2., 3., -2., 0.5, 2.)
    acoustics_demos.full_riemann_solution_plot_fixed(np.array([5, 0]), np.array([1, 0]), 1., 4.)(0.5, 1)


def test_importing_the_demos_does_not_need_ipywidgets():
    """The browser has no ipywidgets or IPython; only the notebook functions use them."""
    import subprocess
    code = ("import sys; from exact_solvers import acoustics_demos; "
            "assert 'ipywidgets' not in sys.modules and 'IPython' not in sys.modules, "
            "[m for m in sys.modules if m.startswith(('ipywidgets', 'IPython'))]")
    subprocess.run([sys.executable, '-c', code], check=True)


def test_notebook_figure_is_built_once_and_updated():
    """Moving a notebook slider only updates the figure, as on the web."""
    import dataclasses

    built, updated = [], []

    class Counting(acoustics_demos.DecomposeQ):
        def __init__(self):
            built.append(1)
            super().__init__()

        def update(self, **values):
            updated.append(values)
            super().update(**values)

    spec = dataclasses.replace(acoustics_demos.DECOMPOSE_Q, figure=Counting)
    widgets = spec.notebook_widgets()
    spec.interact(widgets=widgets)
    widgets['p'].value = 0.5
    widgets['rho'].value = 1.5
    assert len(built) == 1 and len(updated) == 3
    assert updated[-1] == dict(p=0.5, u=0.3, K=1., rho=1.5)


def test_notebook_png_shows_the_web_frame():
    live = acoustics_demos.PhasePlane()
    live.update(pl=3., ul=2., pr=3., ur=-2., rho=0.5, bulk=2., xmin=1e-7, xmax=10., ymin=-5., ymax=5.)
    png = np.asarray(Image.open(io.BytesIO(live.png())).convert('RGBA')).astype(int)
    np.testing.assert_array_equal(png, frame_pixels(live.frame()))
