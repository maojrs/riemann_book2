"""Interactive matplotlib figures, shared by the notebooks and the web book.

LiveFigure: a figure that is built once and then only redraws what the controls change
(matplotlib "blitting"). In the web book, frame() gives the pixels the page paints; in a
notebook, the same pixels are shown as a PNG image.

InteractiveFigure: a LiveFigure class together with its controls (sliders, number boxes,
dropdowns) and their layout. The same description gives the ipywidgets controls in a
notebook and the controls of the web book.
"""
import io
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


# --- Controls ---------------------------------------------------------------------------
def slider(name, min, max, value, label=None, step=0.1):
    return dict(name=name, kind='slider', min=min, max=max, value=value, step=step, label=label or name)


def number(name, value, label=None, min=None, max=None):
    """A number box; with min and max, values outside them are not accepted."""
    return dict(name=name, kind='number', value=value, label=label or name, min=min, max=max)


def dropdown(name, options, value, label=None):
    return dict(name=name, kind='dropdown', options=list(options), value=value, label=label or name)


@dataclass
class InteractiveFigure:
    """A LiveFigure class with its controls.

    controls: list of slider(), number() and dropdown(), whose labels are LaTeX (without $);
    rows: names of the controls shown
    side by side, row by row; options: names of controls shown apart (under "Plot options"
    on the web, in a second tab in the notebook, titled tab_titles).
    """
    figure: type
    controls: list
    rows: list
    options: list = field(default_factory=list)
    tab_titles: tuple = ('Parameters', 'Plot options')

    def initial_values(self, **values):
        """The control values, with the given ones replacing the defaults."""
        return {c['name']: values.get(c['name'], c['value']) for c in self.controls}

    def show(self, setup=None, **values):
        """Draw the figure once, in a notebook."""
        from IPython.display import display
        live = self.figure(**(setup or {}))
        live.update(**self.initial_values(**values))
        display(live.fig)

    def notebook_widgets(self, **values):
        """One ipywidgets control per entry of controls, by name."""
        from ipywidgets import BoundedFloatText, Dropdown, FloatSlider, FloatText
        widgets = {}
        for c, value in zip(self.controls, self.initial_values(**values).values()):
            description = f"${c['label']}$" if c['kind'] != 'dropdown' else c['label']
            if c['kind'] == 'slider':
                widgets[c['name']] = FloatSlider(value=value, min=c['min'], max=c['max'], step=c['step'],
                                                 description=description)
            elif c['kind'] == 'number' and c['min'] is not None:
                widgets[c['name']] = BoundedFloatText(value=value, min=c['min'], max=c['max'],
                                                      description=description)
            elif c['kind'] == 'number':
                widgets[c['name']] = FloatText(value=value, description=description)
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
        live = self.figure(**(setup or {}))

        def draw(**values):
            live.update(**values)
            display(Image(data=live.png()))

        display(controls, interactive_output(draw, widgets))
