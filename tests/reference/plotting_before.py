"""The book's plotting functions with a time slider as they were before they were drawn on
live figures (riemann_book master plus the changes in CHANGES.md), verbatim: the whole
figure drawn with pyplot at every call. Reference for test_time_figures.py. Each uses the
helpers of its own module, which did not change; only the two exact_riemann_solution calls
(Burgers, shallow water) are renamed apart."""
import matplotlib.pyplot as plt
import numpy as np

from exact_solvers import nonconvex, traffic_LWR
from exact_solvers.burgers import exact_riemann_solution as burgers_exact_riemann_solution, speed
from exact_solvers.nonconvex_demos import plot_waves
from exact_solvers.shallow_water import (conservative_to_primitive, exact_riemann_solution as sw_exact_riemann_solution,
                                         primitive_to_conservative, primitive_variables)
from exact_solvers.traffic_LWR import c, plot_car_trajectories, riemann_traffic_exact
from utils import riemann_tools

figsize = (8, 4)        # traffic_demos


def plot_riemann(q_l,q_r,t,x_range=1):
    states, speeds, reval, wave_types = burgers_exact_riemann_solution(q_l,q_r)
    ax = riemann_tools.plot_riemann(states, speeds, reval,
                                    wave_types,t=t,
                                    layout='horizontal',
                                    t_pointer=0, 
                                    extra_axes=False,
                                    variable_names=['q'],
                                    xmax=x_range);
    riemann_tools.plot_characteristics(reval, speed, axes=ax[0])
    ax[1].set_ylim(-0.05,1.05)
    for a in ax:
        a.set_xlim(-x_range,x_range)
    plt.show()


def plot_riemann_traffic(rho_l,rho_r,t,xrange=1.):
    states, speeds, reval, wave_types = \
            riemann_traffic_exact(rho_l,rho_r)
    ax = riemann_tools.plot_riemann(states,speeds,reval,
                                    wave_types,t=t,
                                    t_pointer=0,extra_axes=True,
                                    variable_names=['Density'],
                                    xmax=xrange)
    riemann_tools.plot_characteristics(reval,c,axes=ax[0])
    plot_car_trajectories(rho_l,rho_r,ax[2],t=t,xmax=xrange)
    ax[1].set_ylim(-0.05,1.05); ax[2].set_ylim(0,1)
    for a in ax:
        a.set_xlim(-xrange,xrange)
    plt.show()


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


def make_plot_function(f, q_left, q_right, xi_left, xi_right):
    
    xi, qxi, q_char, xi_char = nonconvex.nonconvex_solutions(f, q_left, q_right, 
                                                             xi_left, xi_right)
    def plot_function(t=0.2, fig=0):
        """
        Create plot at time t.
        Nonzero fig is used only by jsanimate_widgets when
        converting to html files.
        """
        if fig==0: 
            plt.figure(figsize=figsize);
            
        # plot solution q(x,t):
        plt.subplot(1,3,1)
        # from characteristic-based solution:
        plt.plot(xi_char*t,q_char,'k--') 

        # single-valued solution, extended full domain:
        xi_plot = np.hstack((xi_left,xi*t,xi_right))
        q_plot = np.hstack((q_left,qxi,q_right))
        plt.plot(xi_plot, q_plot, 'k', linewidth=2)
        plt.title('Solution q(x,t)\n at t = %4.2f' % t)
        plt.xlabel('x')
        plt.xlim(xi_left,xi_right)
        
        ax = plt.subplot(1,3,2)
        plot_waves(f,q_left,q_right,xi_left,xi_right,n=1000,axes=ax,t=t)
        #ax.set_xlim(xi_left,xi_right)
                
        # plot flux function and convex hull:
        plt.subplot(1,3,3)
        q_plot = np.linspace(q_left, q_right, 1000)
        f_plot = f(q_plot)
        plt.plot(q_plot, f_plot, 'k--', label='f(q)')
        plt.plot(qxi, f(qxi),'k', label='Convex hull')
        plt.plot([q_left,q_right],[f(q_left),f(q_right)],'bo')
        plt.title('Flux function (dashed)\n Convex hull (solid)')
        plt.xlabel('q')
        plt.tight_layout()
        #plt.legend()

        if fig==0: plt.show()
        return None
    return plot_function


def make_plot_function_qsliders(f):
    
    def plot_function(t=0.2, q_left=1, q_right=0, fig=0):
        """
        Create plot at time t.
        Nonzero fig is used only by jsanimate_widgets when
        converting to html files.
        """
        if fig==0: 
            plt.figure(figsize=figsize)

        xi_left = -3.
        xi_right = 3.
        xi, qxi, q_char, xi_char = \
                    nonconvex.nonconvex_solutions(f, q_left, q_right, 
                                                  xi_left, xi_right)
        # plot solution q(x,t):
        plt.subplot(1,3,1)
        # from characteristic-based solution:
        plt.plot(xi_char*t,q_char,'k--') 

        # single-valued solution, extended full domain:
        xi_plot = np.hstack((xi_left,xi*t,xi_right))
        q_plot = np.hstack((q_left,qxi,q_right))
        plt.plot(xi_plot, q_plot, 'k', linewidth=2)
        plt.title('Solution q(x,t)\n at t = %4.2f' % t)
        plt.xlabel('x')
        plt.ylim(-4,4)

        plt.xlim(xi_left,xi_right)
        
        ax = plt.subplot(1,3,2)
        plot_waves(f,q_left,q_right,xi_left,xi_right,n=1000,axes=ax,t=t)
        ax.set_xlim(-1.5,1.5)

        # plot flux function and convex hull:
        plt.subplot(1,3,3)
        ql_plot = -4
        qr_plot = 4
        q_plot = np.linspace(ql_plot,qr_plot, 1000)
        f_plot = f(q_plot)
        plt.plot(q_plot, f_plot, 'k--', label='f(q)')
        plt.plot(qxi, f(qxi),'k', label='Convex hull')
        plt.plot([q_left,q_right],[f(q_left),f(q_right)],'bo')
        plt.title('Flux function (dashed)\n Convex hull (solid)')
        plt.xlabel('q')
        plt.xlim(ql_plot,qr_plot)
        plt.ylim(-0.8,1.2)
        plt.tight_layout()
        #plt.legend()


        
        if fig==0: plt.show()
        return None
    return plot_function


def make_demo_plot_function(h_l=3., h_r=1., u_l=0., u_r=0,
                            figsize=(10,3), hlim=(0,3.5), ulim=(-1,1),
                            force_waves=None, stripes=True):

    g = 1.

    q_l = primitive_to_conservative(h_l,u_l)
    q_r = primitive_to_conservative(h_r,u_r)

    x = np.linspace(-1.,1.,1000)
    states, speeds, reval, wave_types = \
        sw_exact_riemann_solution(q_l,q_r,g,force_waves=force_waves)

    # compute particle trajectories:
    def reval_rho_u(x):
        q = reval(x)
        rho = q[0]
        with np.errstate(divide='ignore', invalid='ignore'):  # u is undefined (nan) where dry
            u = q[1]/q[0]
        rho_u = np.vstack((rho,u))
        return rho_u

    if stripes:
        x_traj, t_traj, xmax = \
            riemann_tools.compute_riemann_trajectories(states, speeds, 
                                                       reval_rho_u,
                                                       wave_types, i_vel=1, 
                                                       xmax=2,
                                                       rho_left=h_l/4.,
                                                       rho_right=h_r/4.)
    else:
        x_traj, t_traj, xmax = \
            riemann_tools.compute_riemann_trajectories(states, speeds, 
                                                       reval_rho_u,
                                                       wave_types, i_vel=1, 
                                                       xmax=2,
                                                       num_left=3,
                                                       num_right=3)

    num_vars = len(primitive_variables)

    def plot_shallow_water_demo(t=0.5, fig=0):
        if t == 0:
            q = np.zeros((2,len(x)))
            q[0,:] = q_l[0]*(x<=0) + q_r[0]*(x>0)
            q[1,:] = q_l[1]*(x<=0) + q_r[1]*(x>0)
        else:
            q = np.array(reval(x/t))

        if t<0.02:
            q[1] = np.where(x<0, q_l[1], q_r[1])

        primitive = conservative_to_primitive(q[0],q[1])

        if fig == 0:
            fig = plt.figure(figsize=figsize)
            show_fig = True
        else:
            show_fig = False

        axes = [0]*num_vars
        for i in range(num_vars):
            axes[i] = fig.add_subplot(1,num_vars,i+1)
            q = primitive[i]
            plt.plot(x,q,'-k',linewidth=3)
            plt.title(primitive_variables[i])
            if t != 0:
                plt.suptitle('Solution at time $t='+str(t)+'$',fontsize=12)
            else:
                plt.suptitle('Initial data',fontsize=12)
            axes[i].set_xlim(-1,1)

            if i==0 and force_waves != 'raref':
                # plot stripes only on depth plot
                # (and suppress if nonphysical solution plotted)
                n = np.where(t > t_traj)[0]
                if len(n)==0:
                    n = 0
                else:
                    n = min(n.max(), len(t_traj)-1)

                for j in range(1, x_traj.shape[1]-1):
                    j1 = np.where(x_traj[n,j] > x)[0]
                    if len(j1)==0:
                        j1 = 0
                    else:
                        j1 = min(j1.max(), len(x)-1)
                    j2 = np.where(x_traj[n,j+1] > x)[0]
                    if len(j2)==0:
                        j2 = 0
                    else:
                        j2 = min(j2.max(), len(x)-1)

                    # set advected color for density plot:
                    if x_traj[0,j]<0:
                        # shades of blue for fluid starting from x<0
                        if np.mod(j,2)==0:
                            c = 'dodgerblue'
                            alpha = 1.0
                        else:
                            c = 'lightblue'
                            alpha = 1.0
                    else:
                        # shades of blue for fluid starting from x<0
                        if np.mod(j,2)==0:
                            c = 'blue'
                            alpha = 1.0
                        else:
                            c = 'cornflowerblue'
                            alpha = 1.0
                    plt.fill_between(x[j1:j2],q[j1:j2],0,color=c,alpha=alpha)

        axes[0].set_ylim(hlim)
        axes[1].set_ylim(ulim)
        if show_fig:
            plt.show()

    return plot_shallow_water_demo


def plot_with_stripes(rho_l=3.,u_l=0.,p_l=3.,
                      rho_r=1.,u_r=0.,p_r=1.,gamma=1.4,t=0.4):  
    import matplotlib.pyplot as plt
    import numpy as np
    from exact_solvers import euler  
    from utils import riemann_tools
    q_l = euler.primitive_to_conservative(rho_l,u_l,p_l)
    q_r = euler.primitive_to_conservative(rho_r,u_r,p_r)
        
    x = np.linspace(-1.,1.,1000)
    states, speeds, reval, wave_types = euler.exact_riemann_solution(q_l, q_r, gamma=gamma)
    if t == 0:
        q = np.zeros((3,len(x)))
        q[0,:] = q_l[0]*(x<=0) + q_r[0]*(x>0)
        q[1,:] = q_l[1]*(x<=0) + q_r[1]*(x>0)
        q[1,:] = q_l[2]*(x<=0) + q_r[2]*(x>0)
    else:
        q = reval(x/t)
    primitive = euler.conservative_to_primitive(q[0],q[1],q[2])
    
    # compute particle trajectories:
    def reval_rho_u(x): 
        eps = 1.e-16
        q = reval(x)
        rho = q[0]
        u = q[1]/(q[0]+eps)
        rho_u = np.vstack((rho,u))
        return rho_u
    
    # Specify density of trajectories to left and right:
    num_left = 10
    num_right = 10
    rho_left = q_l[0] / 10.
    rho_right = q_r[0] / 10.
    x_traj, t_traj, xmax = riemann_tools.compute_riemann_trajectories(states, speeds, reval_rho_u, wave_types,
                                  i_vel=1, xmax=1, rho_left=rho_left, rho_right=rho_right)
                                                                          
    fig = plt.figure(figsize=(9,8))
    names = ['Density','Velocity','Pressure']
    axes = [0]*3
    for i in range(3):
        axes[i] = fig.add_subplot(3,1,i+1)
        q = primitive[i]
        plt.plot(x,q,'-k',linewidth=3)
        plt.title(names[i])
        qmax = max(q)
        qmin = min(q)
        qdiff = qmax - qmin
        if qdiff == 0: qdiff = qmin*0.5
        axes[i].set_ylim((qmin-0.1*qdiff,qmax+0.1*qdiff))
        axes[i].set_xlim(-xmax,xmax)
                
        if i==0:
            # plot stripes only on density plot
            n = np.array([j for j,v in enumerate(t > t_traj) if v])
            if len(n)==0:
                n = 0
            else:
                n = min(n.max(), len(t_traj)-1)

            for i in range(1, x_traj.shape[1]-1):
                j1 = np.array([j for j,v in enumerate(x_traj[n,i] > x) if v])
                if len(j1)==0:
                    j1 = 0
                else:
                    j1 = min(j1.max(), len(x)-1)
                j2 = np.array([j for j,v in enumerate(x_traj[n,i+1] > x) if v])
                if len(j2)==0:
                    j2 = 0
                else:
                    j2 = min(j2.max(), len(x)-1)

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
                plt.fill_between(x[j1:j2],q[j1:j2],0,color=c)
    plt.tight_layout()
    plt.show()
