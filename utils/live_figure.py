"""Interactive matplotlib figures, shared by the notebooks and the web book.

LiveFigure: a figure that is built once and then only redraws what the controls change
(matplotlib "blitting"). In the web book, frame() gives the pixels the page paints; in a
notebook, the same pixels are shown as a PNG image.

RedrawFigure: any of the book's plotting functions (pyplot), drawn again in full at every
change. Slower than a LiveFigure, but no new plotting code is needed.

InteractiveFigure: a figure (LiveFigure class or plotting function) together with its controls
(sliders, number boxes, checkboxes, dropdowns) and their layout. The same description gives
the ipywidgets controls in a notebook and the controls of the web book.
"""
import io
import functools
import warnings
from dataclasses import dataclass, field

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


class LiveFigure:
    """Subclasses build the figure in __init__, register the artists that change with
    live(), and implement update(**values)."""

    def __init__(self, **figure_options):
        self.fig = Figure(**figure_options)
        self.canvas = FigureCanvasAgg(self.fig)
        self._live = []
        self._background = None
        self._fitted = False

    def live(self, artist):
        """Register an artist that changes from frame to frame; returns it."""
        self._live.append(artist)
        return artist

    def static_changed(self, refit=False):
        """Call after changing anything that is not live (extra lines, axis limits...).
        refit=True fits the figure to its contents again (e.g. new tick labels)."""
        self._background = None
        if refit:
            self._fitted = False

    def update(self, **values):
        raise NotImplementedError

    def _fit_to_contents(self, pad=0.1):
        """Resize the figure to its tight bounding box plus pad inches, keeping every axes
        where it is: the figure as Jupyter shows it (bbox_inches='tight')."""
        self.canvas.draw()
        box = self.fig.get_tightbbox(self.canvas.get_renderer()).padded(pad)
        width, height = self.fig.get_size_inches()
        for ax in self.fig.axes:
            pos = ax.get_position()
            ax.set_position([(pos.x0*width - box.x0)/box.width, (pos.y0*height - box.y0)/box.height,
                             pos.width*width/box.width, pos.height*height/box.height])
        self.fig.set_size_inches(box.width, box.height)
        self._fitted = True

    def frame(self):
        """The figure as RGBA pixels: {'width', 'height', 'rgba'}. Only the live artists
        are drawn again, on top of a saved picture of everything else."""
        if not self._fitted:
            self._fit_to_contents()
            for artist in self._live:          # left out of the saved picture from now on
                artist.set_animated(True)
            self._background = None
        if self._background is None:
            self.canvas.draw()
            self._background = self.canvas.copy_from_bbox(self.fig.bbox)
        else:
            self.canvas.restore_region(self._background)
        for artist in self._live:
            self.fig.draw_artist(artist)
        width, height = self.canvas.get_width_height()
        return {'width': width, 'height': height, 'rgba': bytes(self.canvas.buffer_rgba())}

    def png(self):
        """frame() as PNG data, quickly compressed: for showing the figure in a notebook."""
        from PIL import Image
        frame = self.frame()
        image = Image.frombuffer('RGBA', (frame['width'], frame['height']), frame['rgba'], 'raw', 'RGBA', 0, 1)
        buffer = io.BytesIO()
        image.save(buffer, format='png', compress_level=1)
        return buffer.getvalue()


class RedrawFigure:
    """A figure drawn by one of the book's plotting functions (with pyplot), drawn again in
    full at every change. Same interface as LiveFigure: update(**values), frame(), png()."""

    def __init__(self, plot):
        self.plot = plot
        self.fig = None
        self._pngs = {}          # figures already drawn, by control values
        self._key = None

    def update(self, **values):
        import matplotlib.pyplot as plt
        self._key = repr(sorted(values.items()))
        if self._key in self._pngs:
            return
        if self.fig is not None:
            plt.close(self.fig)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='FigureCanvasAgg is non-interactive')
            self.plot(**values)
        self.fig = plt.gcf()

    def png(self):
        """The figure as Jupyter shows it: PNG cropped to its contents."""
        if self._key not in self._pngs:
            buffer = io.BytesIO()
            self.fig.savefig(buffer, format='png', bbox_inches='tight')
            self._pngs[self._key] = buffer.getvalue()
        return self._pngs[self._key]

    def frame(self):
        from PIL import Image
        image = Image.open(io.BytesIO(self.png())).convert('RGBA')
        return {'width': image.width, 'height': image.height, 'rgba': image.tobytes()}


# --- Controls ---------------------------------------------------------------------------
def slider(name, min, max, value, label=None, step=0.1):
    return dict(name=name, kind='slider', min=min, max=max, value=value, step=step, label=label or name)


def number(name, value, label=None, min=None, max=None):
    """A number box; with min and max, values outside them are not accepted."""
    return dict(name=name, kind='number', value=value, label=label or name, min=min, max=max)


def dropdown(name, options, value, label=None):
    return dict(name=name, kind='dropdown', options=list(options), value=value, label=label or name)


def checkbox(name, value, label):
    return dict(name=name, kind='checkbox', value=value, label=label)


@dataclass
class InteractiveFigure:
    """A figure with its controls: a LiveFigure class (figure), or a plotting function drawn
    again in full at every change (InteractiveFigure.redraw).

    controls: list of slider(), number(), checkbox() and dropdown); labels are written as
    ipywidgets descriptions (math between $...$, e.g. r'$\\rho_l$');
    rows: names of the controls shown
    side by side, row by row; options: names of controls shown apart (under "Plot options"
    on the web, in a second tab in the notebook, titled tab_titles).
    """
    figure: type
    controls: list
    rows: list
    options: list = field(default_factory=list)
    tab_titles: tuple = ('Parameters', 'Plot options')
    function: object = None          # for redraw figures
    factory: bool = False
    fixed: dict = field(default_factory=dict)

    @classmethod
    def redraw(cls, function, controls, rows, factory=False, fixed=None, **options):
        """A figure drawn by `function(**setup, **fixed, **values)` or, with factory=True,
        by `function(**setup)(**fixed, **values)`: one of the book's plotting functions as
        the notebook cell calls it; `fixed` holds the cell's fixed() arguments."""
        return cls(None, controls, rows, function=function, factory=factory, fixed=fixed or {}, **options)

    def build(self, setup=None):
        """The figure for this setup (LiveFigure or RedrawFigure), ready for update()."""
        setup = setup or {}
        if self.function is None:
            return self.figure(**setup)
        plot = self.function(**setup) if self.factory else functools.partial(self.function, **setup)
        return RedrawFigure(functools.partial(plot, **self.fixed))

    def initial_values(self, **values):
        """The control values, with the given ones replacing the defaults."""
        return {c['name']: values.get(c['name'], c['value']) for c in self.controls}

    def show(self, setup=None, **values):
        """Draw the figure once, in a notebook."""
        from IPython.display import display
        live = self.build(setup)
        live.update(**self.initial_values(**values))
        display(live.fig)

    def notebook_widgets(self, **values):
        """One ipywidgets control per entry of controls, by name."""
        from ipywidgets import BoundedFloatText, Checkbox, Dropdown, FloatSlider, FloatText
        widgets = {}
        for c, value in zip(self.controls, self.initial_values(**values).values()):
            description = c['label']
            if c['kind'] == 'slider':
                widgets[c['name']] = FloatSlider(value=value, min=c['min'], max=c['max'], step=c['step'],
                                                 description=description)
            elif c['kind'] == 'number' and c['min'] is not None:
                widgets[c['name']] = BoundedFloatText(value=value, min=c['min'], max=c['max'],
                                                      description=description)
            elif c['kind'] == 'number':
                widgets[c['name']] = FloatText(value=value, description=description)
            elif c['kind'] == 'checkbox':
                widgets[c['name']] = Checkbox(value=value, description=description)
            else:
                widgets[c['name']] = Dropdown(options=c['options'], value=value, description=description)
        return widgets

    def interact(self, setup=None, widgets=None, **values):
        """The figure with its controls, in a notebook (ipywidgets)."""
        from IPython.display import Image, display
        from ipywidgets import HBox, Tab, VBox, interactive_output
        widgets = widgets or self.notebook_widgets(**values)
        rows = VBox([HBox([widgets[name] for name in row]) for row in self.rows])
        if self.options:
            options = VBox([HBox([widgets[name] for name in self.options[i:i+2]])
                            for i in range(0, len(self.options), 2)])
            controls = Tab(children=[rows, options], titles=self.tab_titles)
        else:
            controls = rows
        # Built once; each change only redraws what changed, as on the web
        live = self.build(setup)

        def draw(**values):
            live.update(**values)
            display(Image(data=live.png()))

        display(controls, interactive_output(draw, widgets))
