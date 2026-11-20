"""
Interactive figures of the chapter Shallow_water_approximate, for the web book
(utils.live_figure). The approximate solvers are the chapter's own, verbatim; the functions
below them return the plot function each interactive cell builds (riemann_tools.make_plot_function).
"""
import numpy as np

from exact_solvers import shallow_water as sw
from utils import riemann_tools as rt
from utils.live_figure import InteractiveFigure, slider


def shallow_water_roe(q_l, q_r, grav=1.):
    """
    Approximate Roe solver for the shallow water equations.
    """
    
    h_l = q_l[0]
    hu_l = q_l[1]
    u_l = hu_l/h_l
    h_r = q_r[0]
    hu_r = q_r[1]
    u_r = hu_r/h_r
    
    delta = q_r - q_l
    
    # Roe averages
    h_hat = (h_r + h_l)/2.
    u_hat = (np.sqrt(h_r)*u_r + np.sqrt(h_l)*u_l) \
                / (np.sqrt(h_r) + np.sqrt(h_l))
    c_hat = np.sqrt(grav*h_hat)
    
    s1 = u_hat - c_hat
    s2 = u_hat + c_hat
    
    alpha1 = ( (u_hat+c_hat)*delta[0] - delta[1])/(2*c_hat)
    alpha2 = (-(u_hat-c_hat)*delta[0] + delta[1])/(2*c_hat)
    
    h_m = q_l[0] + alpha1
    hu_m = q_l[1] + alpha1 * (u_hat - c_hat)
    q_m = np.array([h_m, hu_m])
    
    states = np.column_stack([q_l,q_m,q_r])
    speeds = [s1, s2]
    wave_types = ['contact','contact']
    
    def reval(xi):
        h_out  = (xi<s1)*h_l + (s1<=xi)*(xi<=s2)*h_m + (s2<xi)*h_r
        hu_out = (xi<s1)*hu_l + (s1<=xi)*(xi<=s2)*hu_m + (s2<xi)*hu_r
        return h_out, hu_out
    
    return states, speeds, reval, wave_types

def shallow_water_roe_with_efix(q_l, q_r, grav=1., efix=True):
    """
    Approximate Roe solver for the shallow water equations,
    with entropy fix.
    """
    
    h_l = q_l[0]
    hu_l = q_l[1]
    u_l = hu_l/h_l
    h_r = q_r[0]
    hu_r = q_r[1]
    u_r = hu_r/h_r
    
    delta = q_r - q_l
    
    # Roe averages
    h_hat = (h_r + h_l)/2.
    u_hat = (np.sqrt(h_r)*u_r + np.sqrt(h_l)*u_l) /  \
            (np.sqrt(h_r) + np.sqrt(h_l))
    c_hat = np.sqrt(grav*h_hat)
    
    s1 = u_hat - c_hat
    s2 = u_hat + c_hat
    
    alpha1 = ( (u_hat+c_hat)*delta[0] - delta[1])/(2*c_hat)
    alpha2 = (-(u_hat-c_hat)*delta[0] + delta[1])/(2*c_hat)
    
    h_m = q_l[0] + alpha1
    hu_m = q_l[1] + alpha1 * (u_hat - c_hat)
    u_m = hu_m/h_m
    q_m = np.array([h_m, hu_m])
        
    transonic = None
    if efix:
        # Check if either wave appears transonic
        lambda_1_l = u_l - np.sqrt(grav*h_l)
        lambda_1_m = u_m - np.sqrt(grav*h_m)
        lambda_2_m = u_m + np.sqrt(grav*h_m)
        lambda_2_r = u_r + np.sqrt(grav*h_r)
        
        if lambda_1_l < 0 < lambda_1_m: # 1-wave appears transonic
            transonic = 1
        elif lambda_2_m < 0 < lambda_2_r: # 2-wave appears transonic
            transonic = 2
    
    if transonic == 1:
        beta = (lambda_1_m - s1)/(lambda_1_m - lambda_1_l)
        alpha1_l = beta*alpha1
        #alpha_1_r = (1-beta)*alpha1
        h_m_new = q_l[0] + alpha1_l
        hu_m_new = q_l[1] + alpha1_l * (u_hat-c_hat)
        q_m_new = np.array([h_m_new, hu_m_new])
        states = np.column_stack([q_l,q_m_new,q_m,q_r])
        speeds = [lambda_1_l, lambda_1_m, s2]
        wave_types = ['contact']*3
        
        def reval(xi):
            h_out  = (xi<speeds[0])*states[0,0] + \
                     (speeds[0]<=xi)*(xi<speeds[1])*states[0,1] + \
                     (speeds[1]<=xi)*(xi<speeds[2])*states[0,2] + \
                     (speeds[2]<=xi)*states[0,3]
            hu_out = (xi<speeds[0])*states[1,0] + \
                     (speeds[0]<=xi)*(xi<speeds[1])*states[1,1] + \
                     (speeds[1]<=xi)*(xi<speeds[2])*states[1,2] + \
                     (speeds[2]<=xi)*states[1,3]
            return h_out, hu_out
        
    elif transonic == 2:
        beta = (lambda_2_r - s2)/(lambda_2_r - lambda_2_m)
        #alpha2_l = beta*alpha2
        alpha2_r = (1-beta)*alpha2
        h_m_new = q_r[0] - alpha2_r
        hu_m_new = q_r[1] - alpha2_r*(u_hat+c_hat)
        q_m_new = np.array([h_m_new, hu_m_new])
        states = np.column_stack([q_l,q_m,q_m_new,q_r])
        speeds = [s1,lambda_2_m, lambda_2_r]
        wave_types = ['contact']*3

        def reval(xi):
            h_out  = (xi<speeds[0])*states[0,0] + \
                     (speeds[0]<=xi)*(xi<speeds[1])*states[0,1] + \
                     (speeds[1]<=xi)*(xi<speeds[2])*states[0,2] + \
                     (speeds[2]<=xi)*states[0,3]
            hu_out = (xi<speeds[0])*states[1,0] + \
                     (speeds[0]<=xi)*(xi<speeds[1])*states[1,1] + \
                     (speeds[1]<=xi)*(xi<speeds[2])*states[1,2] + \
                     (speeds[2]<=xi)*states[1,3]
            return h_out, hu_out
        
    else:    
        states = np.column_stack([q_l,q_m,q_r])
        speeds = [s1, s2]
        wave_types = ['contact','contact']
    
        def reval(xi):
            h  = (xi<s1)*h_l + (s1<=xi)*(xi<=s2)*h_m + (s2<xi)*h_r
            hu = (xi<s1)*hu_l + (s1<=xi)*(xi<=s2)*hu_m + (s2<xi)*hu_r
            return h, hu
    
    return states, speeds, reval, wave_types

def shallow_water_hll(q_l, q_r, grav=1.):
    """
    HLLE approximate solver for the shallow water equations.
    """
    h_l = q_l[0]
    hu_l = q_l[1]
    u_l = hu_l/h_l
    h_r = q_r[0]
    hu_r = q_r[1]
    u_r = hu_r/h_r
        
    # Roe averages
    h_hat = (h_r + h_l)/2.
    u_hat = (np.sqrt(h_r)*u_r + np.sqrt(h_l)*u_l) / \
            (np.sqrt(h_r) + np.sqrt(h_l))
    c_hat = np.sqrt(grav*h_hat)

    lambda_1_l = u_l - np.sqrt(grav*h_l)
    lambda_2_r = u_r + np.sqrt(grav*h_r)
    
    s1 = min(lambda_1_l, u_hat - c_hat)
    s2 = max(lambda_2_r, u_hat + c_hat)
    
    h_m = (hu_r - hu_l - s2*h_r + s1*h_l)/(s1-s2)
    hu_m = (hu_r*u_r - hu_l*u_l + 0.5*grav*(h_r**2 - h_l**2) \
            - s2*hu_r + s1*hu_l)/(s1-s2)
    q_m = np.array([h_m, hu_m])
    
    states = np.column_stack([q_l,q_m,q_r])
    speeds = [s1, s2]
    wave_types = ['contact','contact']
    
    def reval(xi):
        h_out  = (xi<s1)*h_l + (s1<=xi)*(xi<=s2)*h_m + (s2<xi)*h_r
        hu_out = (xi<s1)*hu_l + (s1<=xi)*(xi<=s2)*hu_m + (s2<xi)*hu_r
        return h_out, hu_out
    
    return states, speeds, reval, wave_types


def roe_comparison(h_l, u_l, h_r, u_r):
    """The comparison of make_plot_functions(h_l, u_l, h_r, u_r): exact and Roe solutions."""
    hu_l = h_l*u_l; hu_r = h_r*u_r
    q_l = np.array([h_l, hu_l]); q_r = np.array([h_r, hu_r])
    ex_states, ex_speeds, ex_reval, ex_wave_types = \
                                    sw.exact_riemann_solution(q_l,q_r)
    states, speeds, reval, wave_types = shallow_water_roe(q_l, q_r)

    return rt.make_plot_function([ex_states, states],
                                 [ex_speeds, speeds],
                                 [ex_reval, reval],
                                 [ex_wave_types, wave_types],
                                 variable_names=sw.conserved_variables)


def efix_comparison(h_l, u_l, h_r, u_r):
    """The plot function of compare_efix(h_l, u_l, h_r, u_r)."""
    hu_l = h_l*u_l; hu_r = h_r*u_r
    q_l = np.array([h_l, hu_l]); q_r = np.array([h_r, hu_r])
    ex_states, ex_speeds, ex_reval, ex_wave_types = \
                        sw.exact_riemann_solution(q_l,q_r)
    states, speeds, reval, wave_types = \
                        shallow_water_roe_with_efix(q_l, q_r)
    no_efix_states, no_efix_speeds, no_efix_reval, no_efix_wave_types = \
                        shallow_water_roe(q_l, q_r)

    return rt.make_plot_function([ex_states, no_efix_states, states],
                                 [ex_speeds, no_efix_speeds, speeds],
                                 [ex_reval, no_efix_reval, reval],
                                 [ex_wave_types, no_efix_wave_types, wave_types],
                                 ['Exact','Roe w/o fix','Roe with fix'],
                                 layout='vertical', vertical_spacing=0.1,
                                 variable_names=sw.conserved_variables)


def roe_efix_comparison(h_l, u_l, h_r, u_r):
    """Exact and Roe (with entropy fix) solutions, as in the cell of the
    transonic rarefaction."""
    hu_l = h_l*u_l; hu_r = h_r*u_r
    q_l = np.array([h_l, hu_l]); q_r = np.array([h_r, hu_r])
    ex_states, ex_speeds, ex_reval, ex_wave_types = \
                    sw.exact_riemann_solution(q_l,q_r)
    states, speeds, reval, wave_types = \
                    shallow_water_roe_with_efix(q_l, q_r)

    return rt.make_plot_function([ex_states, states],
                                 [ex_speeds, speeds],
                                 [ex_reval, reval],
                                 [ex_wave_types, wave_types],
                                 variable_names=sw.conserved_variables)


def comparison(q_l, q_r, solvers):
    """The plot function of compare_solutions(q_l, q_r, solvers)."""
    q_l, q_r = np.asarray(q_l, float), np.asarray(q_r, float)
    outputs = []
    for solver in solvers:
        if solver.lower() == 'exact':
            outputs.append(sw.exact_riemann_solution(q_l,q_r))
        if solver.lower() == 'hll':
            outputs.append(shallow_water_hll(q_l, q_r))
        if solver.lower() == 'roe':
            outputs.append(shallow_water_roe_with_efix(q_l, q_r))
        if solver.lower() == 'roe no efix':
            outputs.append(shallow_water_roe(q_l, q_r))

    return rt.make_plot_function([val[0] for val in outputs],
                                 [val[1] for val in outputs],
                                 [val[2] for val in outputs],
                                 [val[3] for val in outputs],
                                 solvers, layout='horizontal',
                                 variable_names=sw.conserved_variables)


TIME = slider('t', 0., 0.9, 0.4)
ROE = InteractiveFigure.redraw(roe_comparison, [TIME], factory=True)
EFIX = InteractiveFigure.redraw(efix_comparison, [TIME], factory=True)
ROE_EFIX = InteractiveFigure.redraw(roe_efix_comparison, [TIME], factory=True)
COMPARISON = InteractiveFigure.redraw(comparison, [TIME], factory=True)
