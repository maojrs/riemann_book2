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
        for text in self.fig.texts:           # suptitle: placed in figure fractions too
            x, y = text.get_position()
            text.set_position(((x*width - box.x0)/box.width, (y*height - box.y0)/box.height))
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
        for artist in sorted(self._live, key=lambda a: a.get_zorder()):   # as matplotlib orders them
            self.fig.draw_artist(artist)
        width, height = self.canvas.get_width_height()
        return {'width': width, 'height': height, 'rgba': bytes(self.canvas.buffer_rgba())}

    def png(self):
        """frame() as PNG data: for showing the figure in a notebook."""
        return png(self.frame())


class TimeFigure(LiveFigure):
    """A figure with a time slider: draw(fig, t=..., **values) draws the figure on fig at
    time t and returns at_time(t), which draws (or moves) what depends on the time and
    returns those artists. A new time only calls at_time; new values of anything else build
    the figure again. The axis limits found in the first frame of a build are kept, so the
    axes do not move with t. update() ignores `fig`, the figure argument of the book's
    notebook plotting functions."""

    def __init__(self, draw, figsize, time='t'):
        self.draw = draw
        self.figsize = figsize
        self.time = time
        self._values = None

    def update(self, fig=None, **values):
        t = values.pop(self.time)
        if values != self._values:
            super().__init__(figsize=self.figsize)
            self._values = values
            self._at_time = self.draw(self.fig, **{self.time: t}, **values)
            self._live = self._time_artists(t)
            for ax in self.fig.axes:
                ax.set_xlim(ax.get_xlim())
                ax.set_ylim(ax.get_ylim())
            return
        artists = self._time_artists(t)
        for artist in self._live:
            if not any(artist is a for a in artists):
                artist.remove()
        if self._fitted:                      # see frame(): not in the saved background
            for artist in artists:
                artist.set_animated(True)
        self._live = artists

    def _time_artists(self, t):
        """at_time(t), each artist once (two curves may share a title)."""
        return list({id(a): a for a in self._at_time(t)}.values())

    def show(self, **values):
        """Draw the figure for these values, as an image in the notebook."""
        from IPython.display import Image, display
        self.update(**values)
        display(Image(data=self.png()))


class RedrawFigure:
    """A figure drawn by one of the book's plotting functions (with pyplot), drawn again in
    full at every change. Same interface as LiveFigure: update(**values), frame(), png().

    The picture is cropped as Jupyter crops it (savefig with bbox_inches='tight'), but the
    crop only grows from one frame to the next, so the figure does not jump when a tick
    label gets wider. It is drawn once per frame, straight to pixels (no PNG).
    """
    CACHE = 100              # frames kept, so that going back to earlier values is instant

    def __init__(self, plot, pad=0.1):
        self.plot = plot
        self.pad = pad
        self.fig = None
        self._frames = {}    # frames, by control values
        self._key = None
        self._box = None     # the crop, in inches
        self._measured = set()   # layouts (see _layout) whose crop is already in _box

    def update(self, **values):
        import matplotlib.pyplot as plt
        self._key = repr(sorted(values.items()))
        if self._key in self._frames:
            return
        if self.fig is not None:
            plt.close(self.fig)
        # A figure of its own: some plotting functions draw on pyplot's current figure,
        # which may belong to another figure of the page
        blank = plt.figure()
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='FigureCanvasAgg is non-interactive')
            self.plot(**values)
        self.fig = plt.gcf()
        if self.fig is not blank:
            plt.close(blank)

    def _layout(self):
        """What the crop depends on: the axes (their places, limits and so tick labels) and
        the length of the titles. Frames that differ only inside the axes, or in a number in
        a title ("t = 0.5"), share it."""
        return tuple((tuple(ax.get_position().bounds), ax.get_xlim(), ax.get_ylim(), len(ax.get_title()))
                     for ax in self.fig.axes) + tuple(len(t.get_text()) for t in self.fig.texts)

    def frame(self):
        """The figure as RGBA pixels: {'width', 'height', 'rgba'}."""
        from matplotlib.transforms import Bbox
        if self._key not in self._frames:
            layout = self._layout()
            if layout not in self._measured:           # measuring the crop takes a while
                self._measured.add(layout)
                box = self.fig.get_tightbbox().padded(self.pad)
                inside = self._box is not None and (self._box.contains(box.x0, box.y0)
                                                    and self._box.contains(box.x1, box.y1))
                if not inside:
                    self._box = box if self._box is None else Bbox.union([self._box, box])
                    self._frames.clear()               # drawn with a smaller crop
            if len(self._frames) >= self.CACHE:
                self._frames.pop(next(iter(self._frames)))
            buffer = io.BytesIO()
            self.fig.savefig(buffer, format='rgba', bbox_inches=self._box)
            renderer = self.fig.canvas.renderer           # the one savefig drew with
            self._frames[self._key] = {'width': renderer.width, 'height': renderer.height,
                                       'rgba': buffer.getvalue()}
        return self._frames[self._key]

    def png(self):
        """frame() as PNG data: for showing the figure in a notebook."""
        return png(self.frame())


def png(frame):
    """A frame (RGBA pixels) as PNG data, quickly compressed."""
    from PIL import Image
    image = Image.frombuffer('RGBA', (frame['width'], frame['height']), frame['rgba'], 'raw', 'RGBA', 0, 1)
    buffer = io.BytesIO()
    image.save(buffer, format='png', compress_level=1)
    return buffer.getvalue()


# --- Controls ---------------------------------------------------------------------------
def slider(name, min, max, value, label=None, step=0.1):
    return dict(name=name, kind='slider', min=min, max=max, value=value, step=step, label=label or name)


def number(name, value, label=None, min=None, max=None):
    """A number box; with min and max, values outside them are not accepted."""
    return dict(name=name, kind='number', value=value, label=label or name, min=min, max=max)


def dropdown(name, options, value, label=None):
    return dict(name=name, kind='dropdown', options=list(options), value=value, label=label or name)


def radio(name, options, value, label=None):
    """Radio buttons, one per option."""
    return dict(name=name, kind='radio', options=list(options), value=value, label=label or name)


def checkbox(name, value, label):
    return dict(name=name, kind='checkbox', value=value, label=label)


@dataclass
class InteractiveFigure:
    """A figure with its controls: a LiveFigure class (figure), or a plotting function drawn
    again in full at every change (InteractiveFigure.redraw).

    controls: list of slider(), number(), checkbox(), dropdown() and radio(); labels are written as
    ipywidgets descriptions (math between $...$, e.g. r'$\\rho_l$');
    rows: names of the controls shown
    side by side, row by row (None leaves a column empty); options: names of controls shown apart (under "Plot options"
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
    def redraw(cls, function, controls, rows=None, factory=False, fixed=None, **options):
        """A figure drawn by `function(**setup, **fixed, **values)` or, with factory=True,
        by `function(**setup)(**fixed, **values)`: one of the book's plotting functions as
        the notebook cell calls it; `fixed` holds the cell's fixed() arguments. Without rows,
        the controls are shown one per line, in order, as interact() shows them."""
        rows = rows or [[c['name']] for c in controls]
        return cls(None, controls, rows, function=function, factory=factory, fixed=fixed or {}, **options)

    def build(self, setup=None):
        """The figure for this setup (LiveFigure or RedrawFigure), ready for update()."""
        setup = setup or {}
        if self.function is None:
            return self.figure(**setup)
        plot = self.function(**setup) if self.factory else functools.partial(self.function, **setup)
        function = plot.func if isinstance(plot, functools.partial) else plot
        if hasattr(function, 'live_figure'):      # a plotting function drawn on a live figure
            figure = function.live_figure()
            arguments = {**(plot.keywords if plot is not function else {}), **self.fixed}
            if arguments:                         # setup and fixed() arguments, at every update
                figure.update = functools.partial(figure.update, **arguments)
            return figure
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
        from ipywidgets import BoundedFloatText, Checkbox, Dropdown, FloatSlider, FloatText, RadioButtons
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
            elif c['kind'] == 'radio':
                widgets[c['name']] = RadioButtons(options=c['options'], value=value, description=description)
            else:
                widgets[c['name']] = Dropdown(options=c['options'], value=value, description=description)
        return widgets

    def interact(self, setup=None, widgets=None, **values):
        """The figure with its controls, in a notebook (ipywidgets)."""
        from IPython.display import Image, display
        from ipywidgets import HBox, Tab, VBox, interactive_output
        widgets = widgets or self.notebook_widgets(**values)
        rows = VBox([HBox([widgets[name] for name in row if name]) for row in self.rows])
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
