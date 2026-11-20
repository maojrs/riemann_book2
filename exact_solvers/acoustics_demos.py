"""
Additional functions and demos for acoustics equations.

The interactive figures are live figures (utils.live_figure): the same figure is used by
the notebook sliders and by the web book.
"""
from miniclaw import pyclaw
from miniclaw import riemann
from matplotlib import animation
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from utils import riemann_tools
from utils.live_figure import LiveFigure, InteractiveFigure, slider, number, dropdown
from . import acoustics
colors = ['g','orange']


# --- Decomposition of q into eigenvectors ------------------------------------------------
class DecomposeQ(LiveFigure):
    """The eigenvectors r1, r2 in the phase plane, and q = w1 r1 + w2 r2."""

    def __init__(self):
        super().__init__(figsize=(8, 4))
        axes = self.fig.subplots(1, 2)
        self.r1 = self.live(axes[0].arrow(0, 0, -1, 1, head_width=0.07, head_length=0.15,
                                          color=colors[0], lw=3))
        self.r2 = self.live(axes[0].arrow(0, 0, 1, 1, head_width=0.07, head_length=0.15,
                                          color=colors[1], lw=3))
        axes[0].plot([], [], colors[0])
        axes[0].plot([], [], '-', color=colors[1])
        axes[0].set_xlim(-2, 2)
        axes[0].set_ylim(-2, 2)
        axes[0].set_aspect('equal')
        axes[0].set_title('Eigenvectors in phase plane', fontsize=10)
        axes[0].legend(['$r_1$', '$r_2$'], loc=3)
        axes[0].plot([0, 0], [-2, 2], '--k', alpha=0.2)
        axes[0].plot([-2, 2], [0, 0], '--k', alpha=0.2)
        axes[0].set_xlabel('p')
        axes[0].set_ylabel('u')

        self.q = self.live(axes[1].plot([], [], 'k-', lw=3, markersize=8)[0])
        self.w1 = self.live(axes[1].plot([], [], color=colors[0], lw=3)[0])
        self.w2 = self.live(axes[1].plot([], [], color=colors[1], lw=3)[0])
        axes[1].set_xlim(-1.2, 1.2)
        axes[1].set_ylim(-1.2, 1.2)
        self.live(axes[1].legend(['$q$', r'$w_1 r_1$', r'$w_2 r_2$'], loc='best'))
        self.point = self.live(axes[1].plot([], [], 'ko', markersize=6)[0])
        axes[1].plot([0, 0], [-2, 2], '--k', alpha=0.2)
        axes[1].plot([-2, 2], [0, 0], '--k', alpha=0.2)
        axes[1].set_xlabel('p')
        axes[1].set_title('Decomposition of q', fontsize=10)
        self.fig.tight_layout()

    def update(self, p, u, K, rho):
        Z = np.sqrt(K*rho)
        self.r1.set_data(dx=-Z, dy=1)
        self.r2.set_data(dx=Z, dy=1)
        alpha1 = (Z*u-p)/(2.*Z)
        alpha2 = (Z*u+p)/(2.*Z)
        self.q.set_data([0, p], [0, u])
        self.w1.set_data([0, -Z*alpha1], [0, 1*alpha1])
        self.w2.set_data([-Z*alpha1, -Z*alpha1+Z*alpha2], [1*alpha1, alpha1+alpha2])
        self.point.set_data([p], [u])


DECOMPOSE_Q = InteractiveFigure(
    DecomposeQ,
    controls=[slider('p', -1, 1, 1.), slider('u', -1, 1, 0.3),
              slider('rho', 0.1, 2, 1., label=r'$\rho$'), slider('K', 0.1, 2, 1.)],
    rows=[['p', 'rho'], ['u', 'K']])


def decompose_q_interactive():
    """plots interactive decomposed eigenvectors."""
    DECOMPOSE_Q.interact()


def decompose_q(p,u,K,rho):
    r"""Plotting function for decompose_q_interactive. It 
    should also print the eigenvectors and the values w_1, w_2."""
    DECOMPOSE_Q.show(p=p, u=u, K=K, rho=rho)


# --- Solution by characteristics ---------------------------------------------------------
class CharSolution(LiveFigure):
    """Characteristic variables w1, w2 advected along the characteristics, and the
    velocity they give."""

    def __init__(self):
        super().__init__(figsize=(8, 4))
        axes = self.fig.subplots(1, 2)
        # 41 pairs of characteristics x -/+ c t; they only change with c
        self.chars = [axes[0].plot([], [], '-', lw=0.5, color=colors[k % 2])[0] for k in range(82)]
        axes[0].set_xlim(-1, 1)
        axes[0].set_ylim(-0.2, 1.2)
        axes[0].set_title('Characteristics')
        axes[0].set_xlabel('$x$')
        axes[0].set_ylabel('$t$')
        self.l1 = self.live(axes[0].plot([], [], color=colors[0], lw=2, label='$w_{1}$')[0])
        self.l2 = self.live(axes[0].plot([], [], color=colors[1], lw=2, label='$w_{2}$')[0])
        axes[0].legend(handles=[self.l1, self.l2], loc=4)
        self.velocity = self.live(axes[1].plot([], [], '-k', lw=2)[0])
        axes[1].set_xlim(-1, 1)
        axes[1].set_ylim(-0.2, 1.2)
        axes[1].set_title('Velocity')
        axes[1].set_xlabel('$x$')
        self.fig.tight_layout()
        self.c = None

    def update(self, t, K, rho):
        c = np.sqrt(K/rho)
        if c != self.c:
            self.c = c
            tt = np.linspace(0, 1.2, 20)
            for k, ix in enumerate(np.linspace(-2*c-1, 2*c+1, 41)):
                self.chars[2*k].set_data(ix-c*tt, tt)
                self.chars[2*k+1].set_data(ix+c*tt, tt)
            self.static_changed()
        xx = np.linspace(-2*c-1, 2*c+1, 1000)
        w120 = lambda x: -0.1*np.exp(-50*x**2)
        w220 = lambda x:  0.1*np.exp(-50*x**2)
        spacing = 1
        self.l1.set_data(xx, w120(xx+c*spacing*t)+spacing*t)
        self.l2.set_data(xx, w220(xx-c*spacing*t)+spacing*t)
        self.velocity.set_data(xx, w120(xx-c*spacing*t)+w220(xx+c*spacing*t)+spacing*t)


CHAR_SOLUTION = InteractiveFigure(
    CharSolution,
    controls=[slider('t', 0., 1.2, 0.), slider('rho', 0.1, 2, 1., label=r'$\rho$'), slider('K', 0.1, 2, 1.)],
    rows=[['t'], ['rho', 'K']])


def char_solution_interactive():
    """Plots interactive characteristics solution."""
    CHAR_SOLUTION.interact()


def char_solution(t, K, rho):
    """Plotting function for char_solution_interactive."""
    CHAR_SOLUTION.show(t=t, K=K, rho=rho)


# --- Phase plane --------------------------------------------------------------------------
def phase_plane_artists(ax):
    """The lines, points and labels of the acoustics phase plane, to be set by
    draw_phase_plane: the 2 incorrect solutions (dashed), the 2 lines of the solution,
    and q_l, q_r, q_m with their labels."""
    lines = [ax.plot([], [], style)[0] for style in ('--k', '--k', '-k', '-k')]
    points = [ax.plot([], [], '-ok', markersize=10)[0] for _ in range(3)]
    labels = [ax.text(0, 0, label, fontsize=15) for label in ('$q_l$', '$q_r$', '$q_m$')]
    return lines, points, labels


def draw_phase_plane(artists, pl, ul, pr, ur, rho, bulk, xmin, xmax, ymin, ymax):
    """Lines u = u_0 -/+ (p - p_0)/Z in the directions of the eigenvectors through q_l and
    q_r; they meet at the middle state q_m, shown if it is inside the plot."""
    lines, points, labels = artists
    dp = pr - pl
    du = ur - ul
    c = np.sqrt(bulk/rho)
    Z = rho*c
    lin1l = lambda p: ul - 1./Z*(p-pl)
    lin2l = lambda p: ul + 1./Z*(p-pl)
    lin1r = lambda p: ur - 1./Z*(p-pr)
    lin2r = lambda p: ur + 1./Z*(p-pr)

    # Solve Riemann problem
    al1 = (-dp + du*Z)/(2*Z)
    pm = pl - al1*Z
    um = ul + al1

    p = np.linspace(xmin,xmax,500)
    for line, f in zip(lines, (lin2l, lin1r, lin1l, lin2r)):
        line.set_data(p, f(p))
    dx, dy = xmax - xmin, ymax - ymin
    middle_shown = pm >= 0 and pm <= xmax and um > ymin and um < ymax
    for point, label, (x, y), shown in zip(points, labels, [(pl, ul), (pr, ur), (pm, um)],
                                          [True, True, middle_shown]):
        point.set_data([x], [y])
        label.set_position((x + 0.03*dx, y + 0.03*dy))
        point.set_visible(shown)
        label.set_visible(shown)


class PhasePlane(LiveFigure):
    """The phase plane of interactive_phase_plane."""

    def __init__(self):
        super().__init__(figsize=(5, 4))
        self.ax = self.fig.subplots()
        self.ax.set_xlabel('Pressure (p)', fontsize=15)
        self.ax.set_ylabel('Velocity (u)', fontsize=15)
        self.artists = phase_plane_artists(self.ax)
        for group in self.artists:
            for artist in group:
                self.live(artist)
        self.limits = None

    def update(self, pl, ul, pr, ur, rho, bulk, xmin=0, xmax=6, ymin=-6, ymax=6):
        if (xmin, xmax, ymin, ymax) != self.limits:
            self.limits = (xmin, xmax, ymin, ymax)
            self.ax.set_xlim(min(0.00000001,xmin),xmax)
            self.ax.set_ylim(ymin,ymax)
            self.static_changed(refit=True)
        draw_phase_plane(self.artists, pl, ul, pr, ur, rho, bulk, xmin, xmax, ymin, ymax)


PHASE_PLANE = InteractiveFigure(
    PhasePlane,
    controls=[slider('pl', 0.01, 10., 10., label=r'$p_l$'), slider('ul', -10, 10., -5., label=r'$u_l$'),
              slider('pr', 0.01, 10., 40., label=r'$p_r$'), slider('ur', -10, 10., 5., label=r'$u_r$'),
              slider('rho', 0.01, 10., 2., label=r'$\rho$'), slider('bulk', 0.01, 10., 1., label=r'$K$'),
              number('xmin', 0.0000001, label=r'$p_{min}$', min=0, max=100),
              number('xmax', 10, label=r'$p_{max}$'),
              number('ymin', -5, label=r'$u_{min}$'), number('ymax', 5, label=r'$u_{max}$')],
    rows=[['pl', 'ul', 'rho'], ['pr', 'ur', 'bulk']],
    options=['xmin', 'xmax', 'ymin', 'ymax'],
    tab_titles=('Left and right states', 'Plot options'))


def phase_plane_plot():
    """Plots phase plane, also used by interactive_phase_plane
    since it returns phase plane function ready to use with interact."""

    def plot_function(pl,ul,pr,ur,rho,bulk,
                      xmin=0,xmax=6,ymin=-6,ymax=6):
        "Subfunction required for interactive (function of only interactive parameters)."
        PHASE_PLANE.show(pl=pl, ul=ul, pr=pr, ur=ur, rho=rho, bulk=bulk,
                         xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
    return plot_function


def interactive_phase_plane(ql=(10.0, -5.0), qr=(40.0, 5.0), rho=2.0, bulk=1.0):
    """Plots interactive phase plane plot."""
    widgets = PHASE_PLANE.notebook_widgets(pl=ql[0], ul=ql[1], pr=qr[0], ur=qr[1], rho=rho, bulk=bulk)

    # The p and u sliders follow the plot range
    def follow(limit, sliders, attribute):
        def update(*args):
            for name in sliders:
                setattr(widgets[name], attribute, widgets[limit].value)
        widgets[limit].observe(update, 'value')
    follow('xmin', ['pl', 'pr'], 'min')
    follow('xmax', ['pl', 'pr'], 'max')
    follow('ymin', ['ul', 'ur'], 'min')
    follow('ymax', ['ul', 'ur'], 'max')

    PHASE_PLANE.interact(widgets=widgets)


# --- Riemann solution with its phase plane ------------------------------------------------
class FullRiemannFixed(LiveFigure):
    """For fixed q_l, q_r, rho, bulk: the waves in the x-t plane, pressure and velocity
    at time t, and the phase plane."""

    def __init__(self, ql, qr, rho, bulk, xmin=0, xmax=6, ymin=-6, ymax=6):
        super().__init__(figsize=(10, 5))
        pl, ul = ql
        pr, ur = qr
        self.aux = [rho, bulk]
        self.states, self.speeds, self.riemann_eval = acoustics.exact_riemann_solution(
            np.array([pl, ul]), np.array([pr, ur]), self.aux)

        outer_grid = gridspec.GridSpec(1, 2, wspace=0.15, hspace=0.15)
        inner_grid = gridspec.GridSpecFromSubplotSpec(3, 1, subplot_spec=outer_grid[0], wspace=0.0, hspace=0.0)
        ax1 = self.fig.add_subplot(inner_grid[0]) # x-t plane
        ax2 = self.fig.add_subplot(inner_grid[1]) # x vs pressure
        ax3 = self.fig.add_subplot(inner_grid[2]) # x vs velocity
        ax4 = self.fig.add_subplot(outer_grid[1]) # phase plane
        ax1.set_ylabel("t", fontsize=10)
        ax2.set_ylabel("pressure", fontsize=10)
        ax3.set_ylabel("velocity", fontsize=10)
        ax3.set_xlabel("x", fontsize=10)
        ax1.set_xticks([])
        ax2.set_xticks([])

        # Riemann solution on ax1, ax2 and ax3; the time line (drawn last by plot_waves)
        # and the solution curves move with t
        self.ax = np.array([ax1, ax2, ax3])
        riemann_tools.plot_riemann(self.states, self.speeds, self.riemann_eval, wave_types=None, t=0,
                                   ax=self.ax, layout='vertical', variable_names=['pressure', 'velocity'])
        self.t_line = self.live(ax1.lines[-1])
        self.curves = [self.live(ax2.lines[-1]), self.live(ax3.lines[-1])]
        self.xmax = ax1.get_xlim()[1]
        self.characteristics = {}             # lines of each family, computed when first shown
        self.which_char = None

        # Phase plane on ax4 (does not change with t)
        ax4.set_xlim(min(0.00000001,xmin),xmax)
        ax4.set_ylim(ymin,ymax)
        ax4.set_xlabel('Pressure (p)', fontsize=10)
        ax4.set_ylabel('Velocity (u)', fontsize=10)
        ax4.set_title('Phase plane', fontsize=12)
        draw_phase_plane(phase_plane_artists(ax4), pl, ul, pr, ur, rho, bulk, xmin, xmax, ymin, ymax)

    def show_characteristics(self, which_char):
        """Characteristics of family which_char (1 or 2) in the x-t plane, or none."""
        for lines in self.characteristics.values():
            for line in lines:
                line.set_visible(False)
        if which_char and which_char not in self.characteristics:
            before = len(self.ax[0].lines)
            plot_chars = [acoustics.lambda1, acoustics.lambda2]
            riemann_tools.plot_characteristics(self.riemann_eval, plot_chars[which_char-1],
                                               aux=(np.array(self.aux), np.array(self.aux)),
                                               axes=self.ax[0], speeds=self.speeds)
            self.characteristics[which_char] = self.ax[0].lines[before:]
        for line in self.characteristics.get(which_char, []):
            line.set_visible(True)
        self.static_changed()

    def update(self, t, which_char):
        if which_char != self.which_char:
            self.which_char = which_char
            self.show_characteristics(which_char)
        self.t_line.set_ydata([t, t])
        x, q = riemann_tools.sample_riemann(self.speeds, self.riemann_eval, t, self.xmax)
        for curve, qi in zip(self.curves, q):
            curve.set_data(x, qi)


RIEMANN_PLOT_PPLANE = InteractiveFigure(
    FullRiemannFixed,
    controls=[slider('t', 0., 1., 0.), dropdown('which_char', [None, 1, 2], None, label='Characs.')],
    rows=[['t', 'which_char']])


def full_riemann_solution_plot_fixed(ql,qr,rho,bulk):
    """Plots full Riemann solution (with some fixed parameters), including the phase 
    plane, also used by full_riemann_interactive  and riemann_plot_func_pplane since it 
    returns plot function ready to use with interact."""

    def plot_function(t,which_char, xmin=0,xmax=6,ymin=-6,ymax=6):
        "Subfunction required for interactive (function of only interactive parameters)."
        setup = dict(ql=ql, qr=qr, rho=rho, bulk=bulk, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
        RIEMANN_PLOT_PPLANE.show(setup, t=t, which_char=which_char)
    return plot_function


def riemann_plot_pplane(ql=(10.0, -5.0), qr=(40.0, 5.0), rho=2.0, bulk=1.0):
    """Plots interactive riemann solution with time dependence and phase plane plot."""
    RIEMANN_PLOT_PPLANE.interact(setup=dict(ql=ql, qr=qr, rho=rho, bulk=bulk))


# --- Not used in the book ---------------------------------------------------------------
def full_riemann_solution_plot():
    """Plots full Riemann solution, including the phase plane, also used by 
    full_riemann_interactive  and riemann_plot_func_pplane since it returns plot 
    function ready to use with interact."""
    
    def plot_function(t,pl,ul,pr,ur,rho,bulk,which_char, xmin=0,xmax=6,ymin=-6,ymax=6):
        "Subfunction required for interactive (function of only interactive parameters)."
    
        # Define parameters
        dp = pr - pl
        du = ur - ul
        c = np.sqrt(bulk/rho)
        Z = rho*c
        
        # Define eigenvectors and functions
        eig1 = np.array([-Z, 1])
        eig2 = np.array([Z, 1])
        lin1l = lambda p: ul - 1./Z*(p-pl) 
        lin2l = lambda p: ul + 1./Z*(p-pl) 
        lin1r = lambda p: ur - 1./Z*(p-pr) 
        lin2r = lambda p: ur + 1./Z*(p-pr) 
        
        
        # Solve Riemann problem       
        aux = [rho,bulk]
        states, speeds, riemann_eval = acoustics.exact_riemann_solution(np.array([pl,ul]), np.array([pr,ur]), aux)
        pm = states[0][1]
        um = states[1][1]

        
        # Set figure grid
        fig = plt.figure(figsize=(10,5)) #figsize=(11.5, 5.5))
        outer_grid = gridspec.GridSpec(1, 2, wspace=0.15, hspace=0.15)
        inner_grid = gridspec.GridSpecFromSubplotSpec(3, 1, subplot_spec=outer_grid[0], wspace=0.0, hspace=0.0)
        ax1 = plt.Subplot(fig, inner_grid[0]) # x-t plane
        ax2 = plt.Subplot(fig, inner_grid[1]) # x vs pressure
        ax3 = plt.Subplot(fig, inner_grid[2]) # x vs velocity
        ax4 = plt.Subplot(fig, outer_grid[1]) # phase plane
        ax1.set_ylabel("t", fontsize=10)
        ax2.set_ylabel("pressure", fontsize=10)
        ax3.set_ylabel("velocity", fontsize=10)
        ax3.set_xlabel("x", fontsize=10)
        ax1.set_xticks([])
        ax2.set_xticks([])

        # Plot Riemann solution on ax1, ax2 and ax3
        ax = np.array([ax1, ax2, ax3])
        riemann_tools.plot_riemann(states, speeds, riemann_eval, wave_types=None, t=t, ax=ax, 
                                   layout='vertical', variable_names=['pressure', 'velocity'])
        
        # Plot characteristics on ax1 if required
        if which_char:
            plot_chars=[acoustics.lambda1, acoustics.lambda2]
            riemann_tools.plot_characteristics(riemann_eval, plot_chars[which_char-1],
                                     aux=(np.array(aux),np.array(aux)), axes=ax[0], speeds=speeds)
        
        # Plot solution in phase plane plot ion ax4
        x = (pl, pr, pm)
        y = (ul, ur, um)
        dx, dy = xmax - xmin, ymax - ymin
        ax4.set_xlim(min(0.00000001,xmin),xmax)
        ax4.set_ylim(ymin,ymax)
        ax4.set_xlabel('Pressure (p)', fontsize=10)
        ax4.set_ylabel('Velocity (u)', fontsize=10)
        ax4.set_title('Phase plane', fontsize=12)
        p = np.linspace(xmin,xmax,500)

        # Plot incorrect solution
        ax4.plot(p,lin2l(p),'--k')
        ax4.plot(p,lin1r(p),'--k')

        # Plot physical solution
        ax4.plot(p,lin1l(p),'-k')
        ax4.plot(p,lin2r(p),'-k')
        if (pm>=0 and pm <= xmax and um > ymin and um < ymax):
            ax4.plot(pm, um, '-ok', markersize=10)
            ax4.text(x[2] + 0.03*dx,y[2] + 0.03*dy, '$q_m$', fontsize=15)

        # Plot initial states and markers
        ax4.plot(pl, ul, '-ok', markersize=10)
        ax4.plot(pr, ur, '-ok', markersize=10)
        for i,label in enumerate(('$q_l$', '$q_r$')):
            ax4.text(x[i] + 0.03*dx,y[i] + 0.03*dy,label, fontsize=15)
            
        # Add all plots to fig and show    
        fig.add_subplot(ax1)
        fig.add_subplot(ax2)
        fig.add_subplot(ax3)
        fig.add_subplot(ax4)
        plt.show()
    return plot_function



def full_riemann_interactive(ql=(10.0, -5.0), qr=(40.0, 5.0), rho=2.0, bulk=1.0):
    """Plots interactive full riemann solution with phase plane plot."""
    from ipywidgets import interact, widgets
    from IPython.display import display

    # Create plot function for interact
    pp_plot = full_riemann_solution_plot()

    # Declare all widget sliders
    t_widget = widgets.FloatSlider(value=0,min=0.0,max=1.0, description='$t$')
    ql1_widget = widgets.FloatSlider(value=ql[0],min=0.01,max=50.0, description='$p_l$')
    ql2_widget = widgets.FloatSlider(value=ql[1],min=-30,max=30.0, description='$u_l$')
    qr1_widget = widgets.FloatSlider(value=qr[0],min=0.01,max=50.0, description='$p_r$')
    qr2_widget = widgets.FloatSlider(value=qr[1],min=-30,max=30.0, description='$u_r$')
    rho_widget = widgets.FloatSlider(value=rho,min=0.01,max=10.0, description=r'$\rho$')
    bulk_widget = widgets.FloatSlider(value=bulk,min=0.01,max=10.0, description='$K$')
    xmin_widget = widgets.BoundedFloatText(value=0.0000001, description='$p_{min}:$')
    xmax_widget = widgets.FloatText(value=50, description='$p_{max}:$')
    ymin_widget = widgets.FloatText(value=-30, description='$u_{min}:$')
    ymax_widget = widgets.FloatText(value=30, description='$u_{max}:$')
    which_char_widget = widgets.Dropdown(options=[None,1,2],description='Characs.')

    # Allow for dependent widgets to update
    def update_xmin(*args):
        ql1_widget.min = xmin_widget.value
        qr1_widget.min = xmin_widget.value
    def update_xmax(*args):
        ql1_widget.max = xmax_widget.value
        qr1_widget.max = xmax_widget.value
    def update_ymin(*args):
        ql2_widget.min = ymin_widget.value
        qr2_widget.min = ymin_widget.value
    def update_ymax(*args):
        ql2_widget.max = ymax_widget.value
        qr2_widget.max = ymax_widget.value
    xmin_widget.observe(update_xmin, 'value')
    xmax_widget.observe(update_xmax, 'value')
    ymin_widget.observe(update_ymin, 'value')
    ymax_widget.observe(update_ymax, 'value')

    # Organize slider widgets into boxes
    qleftright = widgets.VBox([widgets.HBox([t_widget, which_char_widget]), 
                               widgets.HBox([ql1_widget, ql2_widget, rho_widget]),
                               widgets.HBox([qr1_widget, qr2_widget, bulk_widget])])
    plot_opts = widgets.VBox([widgets.HBox([xmin_widget, xmax_widget]),
                              widgets.HBox([ymin_widget, ymax_widget])])

    # Set up interactive GUI (tab style)
    interact_gui = widgets.Tab(children=[qleftright, plot_opts])
    interact_gui.set_title(0, 'Left and right states')
    interact_gui.set_title(1, 'Plot options')

    # Define interactive widget and run GUI
    ppwidget = interact(pp_plot, t=t_widget, 
                        pl=ql1_widget, ul=ql2_widget,
                        pr=qr1_widget, ur=qr2_widget,
                        rho=rho_widget, bulk=bulk_widget,
                        which_char=which_char_widget,
                        xmin=xmin_widget, xmax=xmax_widget,
                        ymin=ymin_widget, ymax=ymax_widget)
    try:
        ppwidget.widget.close()
        display(interact_gui)
        display(ppwidget.widget.out)
    except:
        pass


# --- Animation ------------------------------------------------------------------------------
def bump_animation(numframes):
    """Plots animation of solution with bump initial condition, 
    using pyclaw (calls bump_pyclaw)."""
    x, frames = bump_pyclaw(numframes) 
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9,4))
    ax1.set_xlim(-2, 2)
    ax1.set_ylim(-3, 5)
    ax1.set_xlabel('$x$')
    ax1.set_ylabel('Pressure: $p$')
    ax2.set_xlim(-2, 2)
    ax2.set_ylim(-3, 3)
    ax2.set_xlabel('$x$')
    ax2.set_ylabel('Velocity: $u$')
    line1, = ax1.plot([], [], '-k', lw=2)
    line2, = ax2.plot([], [], '-k', lw=2)
    line = [line1, line2]

    def fplot(frame_number):
        frame = frames[frame_number]
        pressure = frame.q[0,:]
        velocity = frame.q[1,:]
        line[0].set_data(x,pressure)
        line[1].set_data(x,velocity)
        return line,

    anim = animation.FuncAnimation(fig, fplot, frames=len(frames), interval=30)
    plt.close('all')
    return anim.to_jshtml()


def bump_pyclaw(numframes):
    """Returns pyclaw solution of bump initial condition."""
    # Set pyclaw for burgers equation 1D
    claw = pyclaw.Controller()
    claw.tfinal = 5.0          # Set final time
    claw.keep_copy = True       # Keep solution data in memory for plotting
    claw.output_format = None   # Don't write solution data to file
    claw.num_output_times = numframes  # Number of output frames
    claw.solver = pyclaw.ClawSolver1D(riemann.acoustics_1D)  # Choose acoustics 1D Riemann solver
    claw.solver.all_bcs = pyclaw.BC.wall              # Choose periodic BCs
    claw.verbosity = False                                 # Don't print pyclaw output
    domain = pyclaw.Domain( (-2.,), (2.,), (800,))         # Choose domain and mesh resolution
    claw.solution = pyclaw.Solution(claw.solver.num_eqn, domain)
    # Set initial condition
    x=domain.grid.x.centers
    claw.solution.q[0,:] = 4.0*np.exp(-10 * (x-1.0)**2)  
    claw.solution.q[1,:] = 0.0        
    claw.solver.dt_initial = 1.e99
    # Set parameters
    rho = 1.0
    bulk = 1.0
    claw.solution.problem_data['rho'] = rho
    claw.solution.problem_data['bulk'] = bulk
    claw.solution.problem_data['zz'] = np.sqrt(rho*bulk)
    claw.solution.problem_data['cc'] = np.sqrt(bulk/rho)
    # Run pyclaw
    status = claw.run()
    
    return x, claw.frames

