"""ianimate: an animation of the frames of a run, as Clawpack's visclaw.ianimate draws it."""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation

from miniclaw.controller import Controller


def ianimate(frame_list, ivar=0, varname=None, figsize=(10, 6), xlim=None, ylim=None, interval=200):
    """Animation of component ivar of q over the frames (a Controller or a list of
    Solutions), on a fixed y range 10% wider than the values, one frame every interval ms; the
    title shows the time with two decimals (always as long, so it does not jump).
    Returns the matplotlib animation (for anim.to_jshtml())."""
    if isinstance(frame_list, Controller):
        frame_list = frame_list.frames
    xc = frame_list[0].state.grid.p_centers[0]

    fig = plt.figure(figsize=figsize)
    ax = plt.axes()
    line, = ax.plot([], [], lw=2)
    ax.set_xlim(xlim if xlim is not None else (xc[0], xc[-1]))
    if ylim is None:
        ymax = max(np.max(f.q[ivar, :]) for f in frame_list)
        ymin = min(np.min(f.q[ivar, :]) for f in frame_list)
        ydiff = ymax - ymin
        ylim = (ymin - ydiff/10., ymax + ydiff/10.)
    ax.set_ylim(ylim)
    ax.set_xlabel('x')
    if varname is not None:
        ax.set_ylabel(varname)

    def fplot(frame_number):
        frame = frame_list[frame_number]
        if varname is not None:
            fig.suptitle(varname + ' at time t = %.2f' % frame.t)
        else:
            fig.suptitle('Time t = %.2f' % frame.t)
        line.set_data(xc, frame.q[ivar, :])
        return line,

    plt.close(fig)
    return animation.FuncAnimation(fig, fplot, frames=len(frame_list), interval=interval)
