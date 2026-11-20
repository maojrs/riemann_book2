"""Riemann solution figures with a time slider, drawn on a utils.live_figure.TimeFigure:
the x-t plane, waves and characteristics are drawn once, and a new time only moves the
time line and the solution curves q(x, t) (and the titles and legend that show t)."""
from utils.live_figure import TimeFigure
from utils.riemann_tools import plot_characteristics, plot_riemann, sample_riemann


def plot_riemann_at_time(states, s, riemann_eval, wave_types, t, ax=None, derived_variables=None,
                         **options):
    """riemann_tools.plot_riemann(states, s, riemann_eval, wave_types, t, ax, ...); returns
    its axes and at_time(t), which moves the time line and the solution curves (and the
    'q at t = ...' titles of the horizontal layout) to time t and returns them."""
    ax = plot_riemann(states, s, riemann_eval, wave_types, t, ax, derived_variables=derived_variables,
                      **options)
    num_vars = len(derived_variables(states[:, 0])) if derived_variables else states.shape[0]
    time_line = ax[0].lines[-1]                   # drawn last by plot_waves
    curves = [a.lines[-1] for a in ax[1:1 + num_vars]]       # q(x, t), drawn last in each axes
    xmax = ax[0].get_xlim()[1]                     # the x range plot_riemann sampled
    horizontal = options.get('layout', 'horizontal') == 'horizontal'
    titles = [a.title for a in ax[1:1 + num_vars]] if horizontal else []

    def at_time(t):
        x, q = sample_riemann(s, riemann_eval, t, xmax, derived_variables)
        for i, curve in enumerate(curves):
            curve.set_data(x, q[i])
        time_line.set_ydata([t, t])
        for title in titles:                       # "q at t =  0.500"
            text = title.get_text()
            title.set_text(text[:text.rindex(' at t = ')] + ' at t = %6.3f' % t)
        return [time_line, *curves, *titles]
    return ax, at_time


def riemann_solution_figure(solutions, names=None, layout='horizontal', variable_names=None,
                            colors=('multi', 'green', 'orange'), plot_chars=None,
                            derived_variables=None, aux=None, contact_index=None,
                            vertical_spacing=0, show_time_legend=False):
    """The figure of riemann_tools.make_plot_function (same arguments; solutions is a list of
    (states, speeds, riemann_eval, wave_types)), for update(t=..., which_char=...)."""
    num_axes = solutions[0][0].shape[0] + 1
    if layout == 'horizontal':
        figsize = (9, 3)
    else:
        figsize = (6, (2 + vertical_spacing)*(num_axes - 1))

    def draw(fig, which_char=None, t=None):
        if layout == 'horizontal':
            ax = fig.subplots(1, num_axes)
        else:
            ax = fig.subplots(num_axes, 1, sharex=True)
            fig.subplots_adjust(hspace=vertical_spacing)
            ax[-1].set_xlabel('x')
            ax[0].set_ylabel('t')
        at_times = []
        for i, (states, speeds, riemann_eval, wave_types) in enumerate(solutions):
            at_times.append(plot_riemann_at_time(
                states, speeds, riemann_eval, wave_types, t, ax, derived_variables, color=colors[i],
                layout=layout, variable_names=variable_names, t_pointer=False)[1])
            if which_char:
                plot_characteristics(riemann_eval, plot_chars[which_char - 1], aux=aux, axes=ax[0],
                                     speeds=speeds, contact_index=contact_index)
        # The legend stands outside the plots (right of the last one, or of the top one in the
        # vertical layout), so that it does not jump around as the curves move
        legend = None
        if names is not None or show_time_legend:
            legend_ax = ax[-1] if layout == 'horizontal' else ax[1]
            legend = legend_ax.legend(names or [], loc='upper left', bbox_to_anchor=(1.02, 1),
                                      borderaxespad=0)

        def at_time(t):
            artists = [a for at in at_times for a in at(t)]
            if not show_time_legend:
                return artists
            legend.set_title('time = %.2f' % t)
            return artists + [legend]
        return at_time

    return TimeFigure(draw, figsize)
