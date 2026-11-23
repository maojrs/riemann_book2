import sys, os
import numpy as np
from utils import riemann_tools
import matplotlib.pyplot as plt
from utils.live_figure import TimeFigure
from ipywidgets import widgets, FloatSlider
from ipywidgets import interact


def riemann_traffic_exact(q_l,q_r):
    r"""Exact solution to the Riemann problem for the LWR traffic model."""
    f = lambda q: q*(1-q)
    states = np.array([[q_l, q_r]])
    if q_r > q_l:  # Shock wave
        shock_speed = (f(q_l)-f(q_r))/(q_l-q_r)
        speeds = [shock_speed]
        wave_types = ['shock']
        def reval(xi):
            q = np.zeros((1,len(xi)))
            q[0,:] = (xi < shock_speed)*q_l \
              + (xi >=shock_speed)*q_r
            return q

    else:  # Rarefaction wave
        c_l  = 1-2*q_l
        c_r = 1-2*q_r

        speeds = [[c_l,c_r]]
        wave_types = ['rarefaction']

        def reval(xi):
            q = np.zeros((1,len(xi)))
            q[0,:] = (xi<=c_l)*q_l \
              + (xi>c_r)*q_r \
              + (c_l<xi)*(xi<=c_r)*(1.-xi)/2.
            return q

    return states, speeds, reval, wave_types

def plot_car_trajectories(q_l,q_r,ax=None,t=None,xmax=None):
    states, speeds, reval, wave_types = riemann_traffic_exact(q_l,q_r)
    def reval_with_speed(xi):
        q = reval(xi)
        u = 1-q
        qu = np.vstack((q,u))
        return qu

    # density of particles for trajectories:
    rho_left = q_l / 3.
    rho_right = q_r / 3.

    # compute trajectories:
    x_traj, t_traj, xmax = riemann_tools.compute_riemann_trajectories(states, 
            speeds, reval_with_speed, wave_types,
            xmax=xmax,rho_left=rho_left, rho_right=rho_right)

    # plot trajectories along with waves in the x-t plane:
    riemann_tools.plot_riemann_trajectories(x_traj, t_traj, speeds, wave_types, 
            xmax=xmax, ax=ax, t=t)
    ax.set_title('Vehicle trajectories')

def c(rho, xi):
    "Characteristic speed."
    return 1.-2*rho

def plot_riemann_traffic(rho_l,rho_r,t,xrange=1.):
    plot_riemann_traffic.figure.show(rho_l=rho_l, rho_r=rho_r, t=t, xrange=xrange)

def draw_riemann_traffic(fig,rho_l,rho_r,t,xrange=1.):
    """plot_riemann_traffic on fig; returns at_time(t) (utils.live_figure.TimeFigure)."""
    from utils.riemann_figure import plot_riemann_at_time
    states, speeds, reval, wave_types = \
            riemann_traffic_exact(rho_l,rho_r)
    ax, solution_at_time = plot_riemann_at_time(states,speeds,reval,
                                    wave_types,t=t,
                                    t_pointer=0,extra_axes=True,
                                    variable_names=['Density'],
                                    xmax=xrange, fig=fig)
    riemann_tools.plot_characteristics(reval,c,axes=ax[0])
    plot_car_trajectories(rho_l,rho_r,ax[2],t=t,xmax=xrange)
    time_line = ax[2].lines[-1]     # drawn last by plot_riemann_trajectories
    ax[1].set_ylim(-0.05,1.05); ax[2].set_ylim(0,1)
    for a in ax:
        a.set_xlim(-xrange,xrange)

    def at_time(t):
        time_line.set_ydata([t,t])
        return solution_at_time(t) + [time_line]
    return at_time

# plot_riemann_traffic draws on a figure built once; moving t only redraws what depends on it
plot_riemann_traffic.live_figure = lambda: TimeFigure(draw_riemann_traffic, figsize=(9,3))
plot_riemann_traffic.figure = plot_riemann_traffic.live_figure()

def riemann_solution_interact():
    rho_l_widget = widgets.FloatSlider(min=0., max=1., value=0.5, description=r'$\rho_l$')
    rho_r_widget = widgets.FloatSlider(min=0., max=1., value=0., description=r'$\rho_r$')
    t_widget = widgets.FloatSlider(min=0., max=1., value=0.1)
    x_range_widget = widgets.FloatSlider(min=0.1,max=5,value=1.,description=r'x-axis range')
    params = widgets.HBox([t_widget,widgets.VBox([rho_l_widget,rho_r_widget]),x_range_widget])

    traffic_widget = interact(plot_riemann_traffic,
             rho_l=rho_l_widget, rho_r=rho_r_widget,
             t=t_widget,xrange=x_range_widget);
    if traffic_widget:  # Avoid crash when using snapshot_widgets
        try:
            traffic_widget.widget.close()
            display(params)
            display(traffic_widget.widget.out)
        except:
            pass
