"""riemann_tools.make_plot_function as it was before it drew on a live figure (riemann_book
master plus the changes in CHANGES.md): the whole figure drawn with pyplot at every call.
Reference for test_riemann_figure.py."""
from utils.riemann_tools import plot_characteristics, plot_riemann


def make_plot_function(states_list, speeds_list, riemann_eval_list,
                       wave_types_list=None, names=None, layout='horizontal',
                       variable_names=None, colors=('multi', 'green', 'orange'),
                       plot_chars=None, derived_variables=None, aux=None, contact_index=None,
                       vertical_spacing=0, show_time_legend=False):
    """
    Utility function to create a plot_function that takes a single argument t,
    or (if plot_chars is specified) an argument t and an integer argument indicating
    which characteristic family to plot.
    This function can then be used with ipywidgets.interact.

    Most of the arguments are explained in the docstring for plot_riemann.

    Optional arguments:
        plot_chars: If provided, ordinary characteristics are included in the x-t plot.
                    The value of this argument should be a list of functions c(q,x) that give
                    the characteristic speeds of the wave families (in order).
        aux: auxiliary variables to be passed to plot_characteristics
        contact_index: see docstring for plot_characteristics
        show_time_legend: show time in legend
    """
    import matplotlib.pyplot as plt
    if type(states_list) is not list:
        states_list = [states_list]
        speeds_list = [speeds_list]
        riemann_eval_list = [riemann_eval_list]
        if wave_types_list is not None:
            wave_types_list = [wave_types_list]

    if wave_types_list is None:
        wave_types_list= [['contact']*len(speeds_list[0])]*len(speeds_list)

    num_eqn = states_list[0].shape[0]

    num_axes = num_eqn + 1

    def plot_function(t, which_char=None):
        if layout == 'horizontal':
            fig_width = 9
            fig, ax = plt.subplots(1,num_axes,figsize=(fig_width, 3))
        elif layout == 'vertical':
            fig_width = 6
            fig_height = (2 + vertical_spacing)*(num_axes-1)
            fig, ax = plt.subplots(num_axes,1,figsize=(fig_width, fig_height),sharex=True)
            plt.subplots_adjust(hspace=vertical_spacing)
            ax[-1].set_xlabel('x')
            ax[0].set_ylabel('t')

        for i in range(len(states_list)):
            states = states_list[i]
            speeds = speeds_list[i]
            riemann_eval = riemann_eval_list[i]
            wave_types = wave_types_list[i]

            plot_riemann(states, speeds, riemann_eval, wave_types, t, ax,
                         colors[i], layout=layout,
                         variable_names=variable_names, t_pointer=False,
                         derived_variables=derived_variables)

            if names is not None and show_time_legend:
                # We could use fig.legend here if we had the line plot handles
                ax[1].legend(names,loc='best', title='time = %.2f' % t)
            if names is not None and not show_time_legend:
                ax[1].legend(names,loc='best')
            if names is None and show_time_legend:
                ax[1].legend([],loc='best', title='time = %.2f' % t)

            if which_char:
                plot_characteristics(riemann_eval, plot_chars[which_char-1],
                                     aux=aux, axes=ax[0], speeds=speeds,
                                     contact_index=contact_index)

        plt.show()
        return None

    if plot_chars:
        return plot_function
    else:
        def real_plot_function(t):
            plot_function(t,None)

        return real_plot_function
