"""The figure of riemann_tools.make_plot_function as a live figure (utils.live_figure).

The figure shows the x-t plane and each variable q(x, t) at time t, for one or more Riemann
solutions. Only the time line, the solution curves, the titles and the legend depend on t:
they are the live artists. The rest (waves, characteristics, axes) is drawn once for each
choice of characteristics.
"""
from utils.live_figure import LiveFigure
from utils.riemann_tools import plot_characteristics, plot_riemann, sample_riemann


class RiemannSolutionFigure(LiveFigure):
    """solutions: list of (states, speeds, riemann_eval, wave_types); the other arguments are
    those of make_plot_function."""

    def __init__(self, solutions, names=None, layout='horizontal', variable_names=None,
                 colors=('multi', 'green', 'orange'), plot_chars=None, derived_variables=None,
                 aux=None, contact_index=None, vertical_spacing=0, show_time_legend=False):
        self.solutions = solutions
        self.names = names
        self.layout = layout
        self.variable_names = variable_names
        self.colors = colors
        self.plot_chars = plot_chars
        self.derived_variables = derived_variables
        self.aux = aux
        self.contact_index = contact_index
        self.vertical_spacing = vertical_spacing
        self.show_time_legend = show_time_legend
        self.which_char = 'not built'

    def update(self, t, which_char=None):
        if which_char != self.which_char:
            self._build(t, which_char)
        for curves, time_line, (states, speeds, riemann_eval, wave_types), xmax in self._parts:
            x, q = sample_riemann(speeds, riemann_eval, t, xmax, self.derived_variables)
            for i, curve in enumerate(curves):
                curve.set_data(x, q[i])
            time_line.set_ydata([t, t])
        for title in self._titles:        # "q at t =  0.500"
            text = title.get_text()
            title.set_text(text[:text.rindex(' at t = ')] + ' at t = %6.3f' % t)
        if self.show_time_legend:
            self._legend.set_title('time = %.2f' % t)

    def _build(self, t, which_char):
        """Draw the whole figure at time t, as make_plot_function's plot_function(t, which_char)."""
        num_axes = self.solutions[0][0].shape[0] + 1
        if self.layout == 'horizontal':
            super().__init__(figsize=(9, 3))
            ax = self.fig.subplots(1, num_axes)
        else:
            super().__init__(figsize=(6, (2 + self.vertical_spacing)*(num_axes - 1)))
            ax = self.fig.subplots(num_axes, 1, sharex=True)
            self.fig.subplots_adjust(hspace=self.vertical_spacing)
            ax[-1].set_xlabel('x')
            ax[0].set_ylabel('t')
        self.which_char = which_char
        self._parts = []
        for i, solution in enumerate(self.solutions):
            states, speeds, riemann_eval, wave_types = solution
            plot_riemann(states, speeds, riemann_eval, wave_types, t, ax, self.colors[i],
                         layout=self.layout, variable_names=self.variable_names, t_pointer=False,
                         derived_variables=self.derived_variables)
            # the curves q(x, t) and the time line it just drew, and the x range it sampled
            self._parts.append(([a.lines[-1] for a in ax[1:]], ax[0].lines[-1], solution,
                                ax[0].get_xlim()[1]))
            if self.names is not None and self.show_time_legend:
                ax[1].legend(self.names, loc='best', title='time = %.2f' % t)
            if self.names is not None and not self.show_time_legend:
                ax[1].legend(self.names, loc='best')
            if self.names is None and self.show_time_legend:
                ax[1].legend([], loc='best', title='time = %.2f' % t)
            if which_char:
                plot_characteristics(riemann_eval, self.plot_chars[which_char - 1], aux=self.aux,
                                     axes=ax[0], speeds=speeds, contact_index=self.contact_index)
        for curves, time_line, _, _ in self._parts:
            self.live(time_line)
            for curve in curves:
                self.live(curve)
        self._titles = [self.live(a.title) for a in ax[1:]] if self.layout == 'horizontal' else []
        self._legend = ax[1].get_legend()
        if self._legend is not None:      # its place (loc='best') depends on the curves
            self.live(self._legend)
