"""utils.live_figure.RedrawFigure: a plotting function drawn again in full at each change;
KeptAxesFigure: the same, on axes that are kept."""
import io

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from utils.live_figure import KeptAxesFigure, RedrawFigure  # noqa: E402


def line_on_current_figure(a):
    """A plotting function that draws on pyplot's current figure, as several of the book's do."""
    plt.plot([0, 1], [0, a])
    plt.ylim(0, 1000)


def pixels(frame):
    return np.frombuffer(frame['rgba'], np.uint8).reshape(frame['height'], frame['width'], 4)


def test_frame_is_the_figure_as_jupyter_shows_it():
    figure = RedrawFigure(line_on_current_figure)
    figure.update(a=500)
    buffer = io.BytesIO()
    figure.fig.savefig(buffer, format='png', bbox_inches='tight')
    jupyter = np.asarray(Image.open(buffer).convert('RGBA'))
    assert np.array_equal(pixels(figure.frame()), jupyter)


def test_figures_do_not_draw_on_each_other():
    alone = RedrawFigure(line_on_current_figure)
    alone.update(a=3)
    expected = pixels(alone.frame())
    plt.close('all')
    first, second = RedrawFigure(line_on_current_figure), RedrawFigure(line_on_current_figure)
    first.update(a=1)
    second.update(a=2)
    first.update(a=3)               # drawn while the second figure is pyplot's current one
    assert [len(f.fig.axes[0].lines) for f in (first, second)] == [1, 1]
    assert np.array_equal(pixels(first.frame()), expected)
    plt.close('all')


def test_crop_only_grows():
    """A wider tick label widens the crop, and the figure keeps that width."""
    def plot(top):
        plt.plot([0, 1], [0, 1])
        plt.ylim(0, top)
    figure = RedrawFigure(plot)
    figure.update(top=1)
    narrow = figure.frame()['width']
    figure.update(top=100000)
    wide = figure.frame()['width']
    figure.update(top=2)
    assert wide > narrow and figure.frame()['width'] == wide
    plt.close('all')


def test_frames_are_kept():
    figure = RedrawFigure(line_on_current_figure)
    figure.update(a=1)
    first = figure.frame()
    figure.update(a=2)
    figure.frame()
    figure.update(a=1)
    assert figure.frame() is first
    plt.close('all')



def curve_and_label(ax, a, b):
    """Draws a curve (autoscaled), a legend and a text on two axes, and lays them out."""
    ax[0].plot(np.linspace(0, a, 20), np.sin(np.linspace(0, a, 20)), label='sin')
    ax[0].legend()
    ax[1].plot([0, b], [b, 0])
    ax[1].text(0, 0, 'a = %g' % a)
    ax[1].set_title('b')
    ax[0].figure.tight_layout()


def test_kept_axes_draw_as_new_axes():
    """Each picture of a KeptAxesFigure is the same as that of a new figure with the same
    contents (limits, ticks, legend), and its axes are kept."""
    def new_figure(a, b):
        curve_and_label(plt.figure(figsize=(6, 3)).subplots(1, 2), a, b)
    kept = KeptAxesFigure(lambda fig: fig.subplots(1, 2), curve_and_label, (6, 3))
    new = RedrawFigure(new_figure)        # the same crop, which only grows
    axes = list(kept.kept.ax)
    for a, b in [(3., 1.), (10., 50.), (0.5, 0.2)]:
        kept.update(a=a, b=b)
        new.update(a=a, b=b)
        assert np.array_equal(pixels(kept.frame()), pixels(new.frame()))
        assert list(kept.kept.ax) == axes and len(axes[1].texts) == 1
