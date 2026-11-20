import matplotlib.pyplot as plt
import numpy as np
from . import traffic_LWR
from utils.live_figure import TimeFigure
figsize =(8,4)

def plot_flux(fun):
    plt.figure(figsize=(4,2))
    rho = np.linspace(0,1)
    f = fun(rho)
    plt.plot(rho,f,linewidth=2)
    plt.xlabel(r'$\rho$')
    plt.ylabel(r'flux $f(\rho) = \rho(1-\rho)$')
    plt.ylim(0,0.3)
    plt.xlim(0,1); plt.grid(linestyle='--')

def jam(rho_l=0.4,t=0.1,fig=0):
    if fig==0:
        return jam.figure.show(rho_l=rho_l, t=t)
    draw_jam(fig, rho_l, t)

def draw_jam(fig, rho_l=0.4, t=0.1):
    """jam on fig; returns at_time(t) (utils.live_figure.TimeFigure)."""
    shock_speed = -rho_l
    axes = (fig.add_subplot(121), fig.add_subplot(122))

    lines = [axes[0].plot([],[],'k',lw=2)[0] for i in range(3)]
    axes[0].set_xlabel('$x$'); axes[0].set_ylabel(r'$\rho$')
    axes[0].set_xlim(shock_speed,-shock_speed); axes[0].set_ylim(0,1.1)
    traffic_LWR.plot_car_trajectories(rho_l,1.,axes[1],t=t)
    time_line = axes[1].lines[-1]
    axes[1].set_ylim(0,1); axes[1].set_xlim(-0.6,0.6)
    axes[1].set_xlabel('$x$'); axes[1].set_ylabel(r'$t$')

    def at_time(t):
        shock_location = t*shock_speed
        lines[0].set_data([-1,shock_location],[rho_l,rho_l])
        lines[1].set_data([shock_location,shock_location],[rho_l,1.])
        lines[2].set_data([shock_location,1.],[1.,1.])
        axes[0].set_title(r'$t= $'+str(t))
        time_line.set_ydata([t,t])
        return lines + [axes[0].title, time_line]
    return at_time

# jam draws on a figure built once; moving t only redraws what depends on it
jam.live_figure = lambda: TimeFigure(draw_jam, figsize)
jam.figure = jam.live_figure()

def green_light(rho_r=0.,t=0.1,fig=0):
    if fig==0:
        return green_light.figure.show(rho_r=rho_r, t=t)
    draw_green_light(fig, rho_r, t)

def draw_green_light(fig, rho_r=0., t=0.1):
    """green_light on fig; returns at_time(t) (utils.live_figure.TimeFigure)."""
    rho_l = 1.
    axes = (fig.add_subplot(121), fig.add_subplot(122))
    lines = [axes[0].plot([],[],'k',lw=2)[0] for i in range(3)]
    axes[0].set_xlabel('$x$'); axes[0].set_ylabel(r'$\rho$');
    axes[0].set_xlim(-1,1);  axes[0].set_ylim(-0.1,1.1)
    axes[1].set_xlabel('$x$'); axes[1].set_ylabel(r'$t$')
    traffic_LWR.plot_car_trajectories(1.,rho_r,axes[1],t=t,xmax=1.)
    time_line = axes[1].lines[-1]
    axes[1].set_ylim(0,1)

    def at_time(t):
        left_edge = -t
        right_edge = -t*(2*rho_r - 1)
        lines[0].set_data([-1,left_edge],[rho_l,rho_l])
        lines[1].set_data([left_edge,right_edge],[rho_l,rho_r])
        lines[2].set_data([right_edge,1.],[rho_r,rho_r])
        axes[0].set_title(r'$t= $'+str(t))
        time_line.set_ydata([t,t])
        return lines + [axes[0].title, time_line]
    return at_time

# green_light draws on a figure built once; moving t only redraws what depends on it
green_light.live_figure = lambda: TimeFigure(draw_green_light, figsize)
green_light.figure = green_light.live_figure()
