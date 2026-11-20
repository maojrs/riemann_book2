import matplotlib.pyplot as plt
import numpy as np
from . import traffic_LWR
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
    shock_speed = -rho_l
    shock_location = t*shock_speed
    
    if fig==0:
        fig = plt.figure(figsize=figsize)
    axes = (fig.add_subplot(121), fig.add_subplot(122))
    
    #_, axes = plt.subplots(1,2,figsize=figsize)
    
    axes[0].plot([-1,shock_location],[rho_l,rho_l],'k',lw=2)
    axes[0].plot([shock_location,shock_location],[rho_l,1.],'k',lw=2)
    axes[0].plot([shock_location,1.],[1.,1.],'k',lw=2)
    axes[0].set_xlabel('$x$'); axes[0].set_ylabel(r'$\rho$')
    axes[0].set_xlim(shock_speed,-shock_speed); axes[0].set_ylim(0,1.1)
    traffic_LWR.plot_car_trajectories(rho_l,1.,axes[1],t=t)
    axes[1].set_ylim(0,1); axes[1].set_xlim(-0.6,0.6)
    axes[0].set_title(r'$t= $'+str(t))
    plt.xlabel('$x$'); plt.ylabel(r'$t$')
    if fig==0: plt.show()  

def green_light(rho_r=0.,t=0.1,fig=0):
    rho_l = 1.
    left_edge = -t
    right_edge = -t*(2*rho_r - 1)
    if fig==0:
        fig = plt.figure(figsize=figsize)
    axes = (fig.add_subplot(121), fig.add_subplot(122))
    #fig, axes = plt.subplots(1,2,figsize=figsize)
    axes[0].plot([-1,left_edge],[rho_l,rho_l],'k',lw=2)
    axes[0].plot([left_edge,right_edge],[rho_l,rho_r],'k',lw=2)
    axes[0].plot([right_edge,1.],[rho_r,rho_r],'k',lw=2)
    axes[0].set_xlabel('$x$'); axes[0].set_ylabel(r'$\rho$');
    axes[0].set_xlim(-1,1);  axes[0].set_ylim(-0.1,1.1)
    axes[0].set_title(r'$t= $'+str(t))
    plt.xlabel('$x$'); plt.ylabel(r'$t$')
    traffic_LWR.plot_car_trajectories(1.,rho_r,axes[1],t=t,xmax=1.)
    axes[1].set_ylim(0,1)
    if fig==0: plt.show()


# --- Interactive figures for the web book (utils.live_figure): the controls of the notebook
from utils.live_figure import InteractiveFigure, slider  # noqa: E402

JAM = InteractiveFigure.redraw(
    jam, [slider('rho_l', 0.1, 0.9, 0.5, label=r'$\rho_l$'), slider('t', 0., 1., 0.5)],
    fixed=dict(fig=0))
GREEN_LIGHT = InteractiveFigure.redraw(
    green_light, [slider('rho_r', 0., 0.9, 0.3, label=r'$\rho_r$'), slider('t', 0., 1., 0.)],
    fixed=dict(fig=0))
RIEMANN_SOLUTION = InteractiveFigure.redraw(       # traffic_LWR.riemann_solution_interact()
    traffic_LWR.plot_riemann_traffic,
    [slider('rho_l', 0., 1., 0.5, label=r'$\rho_l$'), slider('rho_r', 0., 1., 0., label=r'$\rho_r$'),
     slider('t', 0., 1., 0.1), slider('xrange', 0.1, 5., 1., label='x-axis range')],
    [['t', 'rho_l', 'xrange'], [None, 'rho_r', None]])      # rho_r under rho_l
