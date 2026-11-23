"""Interactive matplotlib figures, shared by the notebooks and the web book.

LiveFigure: a figure that is built once and then only redraws what the controls change
(matplotlib "blitting"). In the web book, frame() gives the pixels the page paints; in a
notebook, the same pixels are shown as a PNG image.

RedrawFigure: any of the book's plotting functions (pyplot), drawn again in full at every
change. Slower than a LiveFigure, but no new plotting code is needed. KeptAxesFigure: the
same, but the figure and its axes are made only once.

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

    def __init__(self, fig=None, **figure_options):
        """A new figure (figure_options), or fig drawn again from scratch."""
        self.fig = fig if fig is not None else Figure(**figure_options)
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
        where it is: the figure as Jupyter shows it (bbox_inches='tight'). The text is laid
        out to measure it, but nothing is painted."""
        self.fig.draw_without_rendering()
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
    notebook plotting functions.

    live: the names of the values given to at_time (by name) instead of building the figure
    again; by default only the time. If at_time moves an axis, the rest of the figure is
    drawn again too. background: names of values also given to at_time, which changes (e.g.
    shows or hides) parts of the figure that are not returned as live; a new value draws
    the figure again but does not build it again.

    axes: with axes(fig), which makes the axes and returns them, the figure and its axes are
    made once (KeptAxes) and draw(ax, ...) draws on them, emptied, at each build; the fit
    to the contents is measured once for each layout (layout_of): quicker."""

    def __init__(self, draw, figsize, live=('t',), background=(), axes=None):
        self.draw = draw
        self.figsize = figsize
        self.live_names = live
        self.background_names = background
        self.axes = axes
        self._kept = None
        self._fits = {}          # kept axes: the fit of each layout (layout_of), measured once
        self._live = []
        self._values = None

    def update(self, fig=None, **values):
        live = {name: values.pop(name) for name in self.live_names if name in values}
        shown = {name: values.pop(name) for name in self.background_names if name in values}
        live.update(shown)
        if values != self._values:
            if self.axes is None:
                super().__init__(figsize=self.figsize)
                target = self.fig
            else:
                if self._kept is None:
                    self._kept = KeptAxes(self.axes, self.figsize)
                for artist in self._live:         # part of the next picture as a whole
                    artist.set_animated(False)
                target = self._kept.empty()
                super().__init__(self._kept.fig)
            self._values = values
            self._shown = shown
            self._at_time = self.draw(target, **live, **values)
            self._live = self._time_artists(live)
            for ax in self.fig.axes:
                ax.set_xlim(ax.get_xlim())
                ax.set_ylim(ax.get_ylim())
            return
        limits = [(ax.get_xlim(), ax.get_ylim()) for ax in self.fig.axes]
        artists = self._time_artists(live)
        for artist in self._live:
            if not any(artist is a for a in artists):
                artist.remove()
        if limits != [(ax.get_xlim(), ax.get_ylim()) for ax in self.fig.axes]:
            self.static_changed(refit=True)   # new ticks: draw and fit the figure again
        elif shown != self._shown:
            self.static_changed()             # draw the rest of the figure again
        self._shown = shown
        if self._fitted:                      # see frame(): not in the saved background
            for artist in artists:
                artist.set_animated(True)
        self._live = artists

    def _fit_to_contents(self, pad=0.1):
        if self._kept is None:
            return super()._fit_to_contents(pad)
        layout = layout_of(self.fig)
        if layout not in self._fits:
            super()._fit_to_contents(pad)
            self._fits[layout] = (self.fig.get_size_inches(), [ax.get_position() for ax in self.fig.axes])
            return
        size, places = self._fits[layout]
        self.fig.set_size_inches(size)
        for ax, place in zip(self.fig.axes, places):
            ax.set_position(place)
        self._fitted = True

    def _time_artists(self, live):
        """at_time(**live), each artist once (two curves may share a title)."""
        return list({id(a): a for a in self._at_time(**live)}.values())

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
        self._measured = set()   # layouts (layout_of) whose crop is already in _box

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

    def frame(self):
        """The figure as RGBA pixels: {'width', 'height', 'rgba'}."""
        from matplotlib.transforms import Bbox
        if self._key not in self._frames:
            layout = layout_of(self.fig)
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
            self._frames[self._key] = {'width': int(renderer.width), 'height': int(renderer.height),
                                       'rgba': buffer.getvalue()}
        return self._frames[self._key]

    def png(self):
        """frame() as PNG data: for showing the figure in a notebook."""
        return png(self.frame())


class KeptAxes:
    """A figure whose axes are made once, by axes(fig), which returns them, and emptied for
    each new plot (KeptAxesFigure, TimeFigure(axes=...)). Quicker than a new figure: making
    the axes and their ticks is much of the time of a plot."""

    def __init__(self, axes, figsize):
        self.figsize = figsize
        self.fig = Figure(figsize=figsize)
        self.ax = axes(self.fig)
        params = self.fig.subplotpars
        self._layout = {name: getattr(params, name)
                        for name in ('left', 'right', 'bottom', 'top', 'wspace', 'hspace')}

    def empty(self):
        """The axes, emptied, with the figure's size and the axes' places as axes() made them,
        so that a draw that lays them out again (tight_layout) starts from the same place
        each time. Returns the axes."""
        self.fig.set_size_inches(self.figsize)
        self.fig.subplots_adjust(**self._layout)
        for ax in self.ax:
            clear_contents(ax)
        return self.ax


class KeptAxesFigure(RedrawFigure):
    """A RedrawFigure whose figure and axes are made once (KeptAxes): at every change only
    their contents are drawn again, by draw(ax, **values), with the same plotting functions
    as the notebook (given ax)."""

    def __init__(self, axes, draw, figsize, pad=0.1):
        super().__init__(None, pad)
        self.kept = KeptAxes(axes, figsize)
        self.fig = self.kept.fig
        FigureCanvasAgg(self.fig)
        self.draw = draw

    def update(self, **values):
        self._key = repr(sorted(values.items()))
        if self._key in self._frames:
            return
        self.draw(self.kept.empty(), **values)


def clear_contents(ax):
    """Remove what is plotted on ax (lines, collections, texts, patches, legend), so that it
    is as a new axes for the next plot (autoscaled, colours from the first one); its ticks
    are kept."""
    for artist in [*ax.lines, *ax.collections, *ax.texts, *ax.patches, *ax.images]:
        artist.remove()
    if ax.get_legend():
        ax.get_legend().remove()
    ax.relim()
    ax.autoscale()
    ax.set_prop_cycle(None)


def layout_of(fig):
    """What the crop of a figure depends on: the places of the axes, the lengths of their
    tick labels and of the titles. Figures that differ only inside the axes, or in numbers
    that keep their length (ticks "0.5" and "1.5", "t = 0.5"), share it."""
    def label_lengths(axis):
        low, high = sorted(axis.get_view_interval())
        ticks = [t for t in axis.get_major_locator()() if low <= t <= high]
        return tuple(len(label) for label in axis.get_major_formatter().format_ticks(ticks))
    return tuple((tuple(ax.get_position().bounds), label_lengths(ax.xaxis), label_lengths(ax.yaxis),
                  len(ax.get_title()), len(ax.get_xlabel()), len(ax.get_ylabel()))
                 for ax in fig.axes) + tuple(len(t.get_text()) for t in fig.texts)


def png(frame):
    """A frame (RGBA pixels) as PNG data, quickly compressed."""
    from PIL import Image
    image = Image.frombuffer('RGBA', (frame['width'], frame['height']), frame['rgba'], 'raw', 'RGBA', 0, 1)
    buffer = io.BytesIO()
    image.save(buffer, format='png', compress_level=1)
    return buffer.getvalue()


# --- Controls ---------------------------------------------------------------------------
def slider(name, min, max, value, label=None, step=0.1, integer=False):
    """A slider; integer=True for whole numbers (ipywidgets' IntSlider, step 1)."""
    if integer:
        step = 1
    return dict(name=name, kind='slider', min=min, max=max, value=value, step=step, label=label or name,
                integer=integer)


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
        from ipywidgets import BoundedFloatText, Checkbox, Dropdown, FloatSlider, FloatText, IntSlider, RadioButtons
        widgets = {}
        for c, value in zip(self.controls, self.initial_values(**values).values()):
            description = c['label']
            if c['kind'] == 'slider':
                kind = IntSlider if c['integer'] else FloatSlider
                widgets[c['name']] = kind(value=value, min=c['min'], max=c['max'], step=c['step'],
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
