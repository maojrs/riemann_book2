import sys, os
from IPython.display import display
from ipywidgets import widgets
from ipywidgets import interact
from utils.live_figure import TimeFigure

def plot_with_stripes(rho_l=3.,u_l=0.,p_l=3.,
                      rho_r=1.,u_r=0.,p_r=1.,gamma=1.4,t=0.4):  
    plot_with_stripes.figure.show(rho_l=rho_l, u_l=u_l, p_l=p_l, rho_r=rho_r, u_r=u_r, p_r=p_r,
                                  gamma=gamma, t=t)

def draw_with_stripes(fig, **values):
    """The axes of plot_with_stripes on fig; returns at_values(...), which draws the solution
    for those values: t, and the states and gamma if they are live (utils.live_figure.TimeFigure). The vertical ranges
    hold every value the solution takes, at all times; they change only when the solution
    no longer fits or fills less than a quarter of them."""
    import numpy as np
    from matplotlib.collections import PolyCollection
    from exact_solvers import euler  
    from utils import riemann_tools
    x = np.linspace(-1.,1.,1000)
    names = ['Density','Velocity','Pressure']
    axes = [0]*3
    curves = [0]*3
    for i in range(3):
        axes[i] = fig.add_subplot(3,1,i+1)
        curves[i], = axes[i].plot(x,0*x,'-k',linewidth=3)
        axes[i].set_title(names[i])
        axes[i].set_xlim(-1,1)
    solutions = {}
    ranged = set()

    def solution(rho_l,u_l,p_l,rho_r,u_r,p_r,gamma):
        """The Riemann solution, its particle paths and the range of each variable."""
        q_l = euler.primitive_to_conservative(rho_l,u_l,p_l)
        q_r = euler.primitive_to_conservative(rho_r,u_r,p_r)
        states, speeds, reval, wave_types = euler.exact_riemann_solution(q_l, q_r, gamma=gamma)

        # every value of the solution: q(x/t) for all x/t, from the left state to the right one
        all_speeds = np.hstack([np.atleast_1d(s) for s in speeds])
        xi = np.linspace(all_speeds.min() - 1., all_speeds.max() + 1., 2001)
        with np.errstate(divide='ignore', invalid='ignore'):
            all_values = [np.asarray(v) for v in euler.conservative_to_primitive(*reval(xi))]
        ranges = [(v[np.isfinite(v)].min(), v[np.isfinite(v)].max()) for v in all_values]

        # compute particle trajectories:
        def reval_rho_u(x): 
            eps = 1.e-16
            q = reval(x)
            rho = q[0]
            u = q[1]/(q[0]+eps)
            rho_u = np.vstack((rho,u))
            return rho_u

        # Specify density of trajectories to left and right, starting far enough out that
        # the fluid in [-1, 1] at any time t <= 1 has a trajectory (same spacing as on [-1, 1])
        reach = 1. + np.abs(ranges[1]).max()
        rho_left = q_l[0] / 10. * reach
        rho_right = q_r[0] / 10. * reach
        x_traj, t_traj, xmax = riemann_tools.compute_riemann_trajectories(states, speeds, reval_rho_u, wave_types,
                                      i_vel=1, xmax=reach, rho_left=rho_left, rho_right=rho_right)
        return q_l, q_r, reval, x_traj, t_traj, ranges

    built = dict(values)

    def at_values(t, **live):
        values = {**built, **live}
        values.pop('t')
        key = tuple(sorted(values.items()))
        if key not in solutions:
            solutions.clear()
            solutions[key] = solution(**values)
        q_l, q_r, reval, x_traj, t_traj, ranges = solutions[key]
        for ax, (qmin, qmax) in zip(axes, ranges):
            low, high = ax.get_ylim()
            if not (low <= qmin and qmax <= high and qmax - qmin >= (high - low)/4):
                qdiff = qmax - qmin
                if qdiff == 0: qdiff = abs(qmin)*0.5 or 1.
                margin = 0.1 if ax not in ranged else 0.5     # more room once it had to change
                ranged.add(ax)
                ax.set_ylim((qmin-margin*qdiff,qmax+margin*qdiff))

        if t == 0:
            q = np.zeros((3,len(x)))
            q[0,:] = q_l[0]*(x<=0) + q_r[0]*(x>0)
            q[1,:] = q_l[1]*(x<=0) + q_r[1]*(x>0)
            q[2,:] = q_l[2]*(x<=0) + q_r[2]*(x>0)
        else:
            q = reval(x/t)
        primitive = euler.conservative_to_primitive(q[0],q[1],q[2])
        for i in range(3):
            curves[i].set_ydata(primitive[i])

        # plot stripes only on density plot (one collection of polygons, as fill_between makes)
        q = primitive[0]
        stripes, colors = [], []
        n = np.where(t > t_traj)[0]
        if len(n)==0:
            n = 0
        else:
            n = min(n.max(), len(t_traj)-1)

        for i in range(1, x_traj.shape[1]-1):
            j1 = np.where(x_traj[n,i] > x)[0]
            if len(j1)==0:
                j1 = 0
            else:
                j1 = min(j1.max(), len(x)-1)
            j2 = np.where(x_traj[n,i+1] > x)[0]
            if len(j2)==0:
                j2 = 0
            else:
                j2 = min(j2.max(), len(x)-1)
            if j2 <= j1:             # outside [-1, 1]
                continue

            # set advected color for density plot:
            if x_traj[0,i]<0: 
                # shades of red for fluid starting from x<0
                if np.mod(i,2)==0:
                    c = [1,0,0]
                else:
                    c = [1,0.8,0.8]
            else:
                # shades of blue for fluid starting from x<0
                if np.mod(i,2)==0:
                    c = [0,0,1]
                else:
                    c = [0.8,0.8,1]
            xs, qs = x[j1:j2+1], q[j1:j2+1]
            stripes.append(np.vstack(([xs[0], 0.], np.column_stack((xs, qs)), [xs[-1], 0.])))
            colors.append(c)
        tracer = axes[0].add_collection(PolyCollection(stripes, facecolors=colors, edgecolors=colors),
                                        autolim=False)
        return curves + [tracer]

    for artist in at_values(**values)[3:]:     # the first ranges, for the layout (the
        artist.remove()                         # stripes come with the first frame)
    fig.tight_layout()
    return at_values

# plot_with_stripes draws on a figure built once for the states; moving t only redraws the solution
plot_with_stripes.live_figure = lambda: TimeFigure(draw_with_stripes, figsize=(9,8))
plot_with_stripes.figure = plot_with_stripes.live_figure()

def stripes_demo(rho_l=2.,u_l=0.,p_l=2.5,rho_r=3.,u_r=0.,p_r=5.,gamma=1.4,t=0.5):
    """plot_with_stripes for euler_demo1: every slider only redraws the solution."""
    stripes_demo.figure.show(rho_l=rho_l, u_l=u_l, p_l=p_l, rho_r=rho_r, u_r=u_r, p_r=p_r,
                             gamma=gamma, t=t)

stripes_demo.live_figure = lambda: TimeFigure(
    draw_with_stripes, figsize=(9,8), live=('t', 'rho_l', 'u_l', 'p_l', 'rho_r', 'u_r', 'p_r', 'gamma'))
stripes_demo.figure = stripes_demo.live_figure()

def euler_demo1(rho_l=2.,u_l=0.,p_l=2.5,
                rho_r=3.,u_r=0.,p_r=5., gamma=1.4):
    
    rhol_widget=widgets.FloatSlider(min=1.,max=10.,step=0.1,value=rho_l,description=r'$\rho_l$')
    ul_widget=widgets.FloatSlider(min=-10.,max=10.,step=0.1,value=u_l,description=r'$u_l$')
    pl_widget=widgets.FloatSlider(min=1.,max=10.,step=0.1,value=p_l,description=r'$p_l$')
    rhor_widget=widgets.FloatSlider(min=1.,max=10.,step=0.1,value=rho_r,description=r'$\rho_r$')
    ur_widget=widgets.FloatSlider(min=-10.,max=10.,step=0.1,value=u_r,description=r'$u_r$')
    pr_widget=widgets.FloatSlider(min=1.,max=10.,step=0.1,value=p_r,description=r'$p_r$')
    gamma_widget=widgets.FloatSlider(min=1.1,max=2.,step=0.1,value=gamma,description=r'$\gamma$')
    t_widget=widgets.FloatSlider(min=0.,max=1.,step=0.1,value=0.5,
                                 layout=widgets.Layout(width='100%'))

    # the time on top, as wide as the figure
    interact_gui = widgets.VBox(\
         [t_widget,
          widgets.HBox([rhol_widget, rhor_widget, gamma_widget]),
          widgets.HBox([ul_widget, ur_widget]),
          widgets.HBox([pl_widget, pr_widget])]);

    mainwidget = interact(stripes_demo,
                          rho_l=rhol_widget,u_l=ul_widget,p_l=pl_widget,
                          rho_r=rhor_widget,u_r=ur_widget,p_r=pr_widget,
                          gamma=gamma_widget,t=t_widget);

    try:
        mainwidget.widget.close()
        display(interact_gui)
        display(mainwidget.widget.out)
    except:
        pass


# --- Interactive figures for the web book (utils.live_figure): the controls of the notebook
from utils import riemann_tools  # noqa: E402
from utils.live_figure import InteractiveFigure, checkbox, dropdown, slider  # noqa: E402
from . import euler  # noqa: E402

CURVE_SLIDERS = [slider('gamma', 1.1, 3., 1.4), slider('rho_0', 0.1, 3., 1., label=r'$\rho_0$')]
INTEGRAL_CURVES = InteractiveFigure.redraw(
    euler.plot_integral_curves,
    [checkbox('plot_1', True, '1-wave curves'), checkbox('plot_3', False, '3-wave curves')] + CURVE_SLIDERS)
HUGONIOT_LOCI = InteractiveFigure.redraw(
    euler.plot_hugoniot_loci,
    [checkbox('plot_1', True, 'Plot 1-loci'), checkbox('plot_3', False, 'Plot 3-loci')] + CURVE_SLIDERS)


def riemann_solution_plot(left_state, right_state, gamma=1.4):
    """The plotting function of euler.riemann_solution(left_state, right_state, gamma)."""
    q_left = euler.primitive_to_conservative(*left_state)
    q_right = euler.primitive_to_conservative(*right_state)
    ex_states, ex_speeds, reval, wave_types = euler.exact_riemann_solution(q_left, q_right, gamma)
    return riemann_tools.make_plot_function(ex_states, ex_speeds, reval, wave_types,
                                            layout='vertical',
                                            vertical_spacing=0.15,
                                            variable_names=euler.primitive_variables,
                                            plot_chars=[euler.lambda1, euler.lambda2, euler.lambda3],
                                            derived_variables=euler.cons_to_prim)


RIEMANN_SOLUTION = InteractiveFigure.redraw(
    riemann_solution_plot,
    [slider('t', 0., 0.9, 0.5),
     dropdown('which_char', [None, 1, 2, 3], None, label='Show characteristics:')],
    factory=True)

# plot_with_stripes with only a time slider (the cell's plot_with_stripes_t_slider)
STRIPES = InteractiveFigure.redraw(plot_with_stripes, [slider('t', 0., 1., 0.5)])

# euler_demo1(...)
DEMO1 = InteractiveFigure.redraw(
    stripes_demo,
    [slider('rho_l', 1., 10., 2., label=r'$\rho_l$'), slider('u_l', -10., 10., 0., label='$u_l$'),
     slider('p_l', 1., 10., 2.5, label='$p_l$'), slider('rho_r', 1., 10., 3., label=r'$\rho_r$'),
     slider('u_r', -10., 10., 0., label='$u_r$'), slider('p_r', 1., 10., 5., label='$p_r$'),
     slider('gamma', 1.1, 2., 1.4, label=r'$\gamma$'), slider('t', 0., 1., 0.5)],
    [['t'], ['rho_l', 'rho_r', 'gamma'], ['u_l', 'u_r'], ['p_l', 'p_r']])
