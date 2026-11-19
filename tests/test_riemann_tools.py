"""utils.riemann_tools: building, analysing and plotting Riemann solutions."""

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from exact_solvers import acoustics, burgers, traffic_LWR  # noqa: E402
from miniclaw import riemann  # noqa: E402
from utils import riemann_tools  # noqa: E402


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')


def test_convert_to_list():
    assert riemann_tools.convert_to_list(3) == [3]
    assert riemann_tools.convert_to_list((1, 2)) == (1, 2)


# --- riemann_solution -----------------------------------------------------------------
def test_riemann_solution_from_linear_solver_is_exact():
    """For acoustics the Roe/linear solver is exact: same states as the exact solver."""
    rho, bulk = 2.0, 0.5
    problem_data = {'rho': rho, 'bulk': bulk, 'zz': np.sqrt(rho * bulk), 'cc': np.sqrt(bulk / rho)}
    q_l, q_r = np.array([1.0, 0.5]), np.array([0.2, -0.3])
    states, s, reval = riemann_tools.riemann_solution(riemann.acoustics_1D, q_l, q_r,
                                                      problem_data=problem_data)
    exact_states, exact_speeds, exact_reval = acoustics.exact_riemann_solution(q_l, q_r, (rho, bulk))
    np.testing.assert_allclose(states, exact_states)
    np.testing.assert_allclose(s[:, 0], exact_speeds)
    xi = np.linspace(-1, 1, 40)    # avoids xi = -c, c exactly (the two use different conventions there)
    np.testing.assert_allclose(reval(xi), np.array(exact_reval(xi)))


def test_riemann_solution_docstring_example():
    """The example in the docstring (HLL solver for Euler)."""
    problem_data = {'gamma': 1.4, 'gamma1': 0.4}
    states, speeds, reval = riemann_tools.riemann_solution(
        riemann.euler_1D_py.euler_hll_1D, (3., -0.5, 2.), (1., 0., 1.), problem_data=problem_data)
    np.testing.assert_allclose(states[:, 1], [1.686068, 0.053321, 1.202282], atol=1e-6)


def test_riemann_solution_warns_if_waves_do_not_reach_right_state(capsys):
    def bad_solver(q_l, q_r, aux_l, aux_r, problem_data):
        wave = 0.5 * (q_r - q_l)[:, None, :]
        s = np.ones((1, q_l.shape[1]))
        return wave, s, 0 * wave[:, 0], wave[:, 0]

    riemann_tools.riemann_solution(bad_solver, [0.0], [1.0])
    assert "does not match" in capsys.readouterr().out


# --- Particle trajectories ------------------------------------------------------------
def test_particles_move_with_the_flow_velocity():
    """LWR traffic: cars in a constant state move with velocity u = 1 - q."""
    states, speeds, reval, wave_types = traffic_LWR.riemann_traffic_exact(0.2, 0.4)

    def reval_with_velocity(xi):
        q = reval(xi)
        return np.vstack((q, 1 - q))

    x_traj, t_traj, xmax = riemann_tools.compute_riemann_trajectories(
        states, speeds, reval_with_velocity, wave_types, i_vel=1, xmax=1.0)
    assert x_traj.shape == (len(t_traj), x_traj.shape[1]) and t_traj[-1] == 1.0
    s = speeds[0]
    far_left = x_traj[0] < -1.5 * abs(s) - 0.01          # never reached by the shock
    np.testing.assert_allclose(x_traj[-1, far_left], x_traj[0, far_left] + 0.8, atol=1e-12)
    # Cars never pass each other
    assert np.all(np.diff(x_traj, axis=1) >= -1e-12)


# --- Smoothness detection -------------------------------------------------------------
def test_detect_waves_in_a_sampled_solution():
    """Recover the shock and rarefaction of a Burgers solution from samples of q(xi)."""
    xi = np.linspace(-3, 3, 601)
    dx = xi[1] - xi[0]
    # q = 2 for xi < -1 (shock at xi = -1), 0 on (-1, 0), fan q = xi on (0, 1), 1 for xi > 1
    q = np.where(xi < -1, 2.0, np.where(xi < 0, 0.0, np.where(xi < 1, xi, 1.0)))
    smoothness = riemann_tools.detect_smoothness(q, dx)
    values, ranges = riemann_tools.intervals(smoothness)
    wave_types, speeds = riemann_tools.make_waves(values, ranges, xi)
    assert wave_types == ['shock', 'raref']
    assert speeds[0] == pytest.approx(-1.0, abs=2 * dx)
    assert speeds[1][0] == pytest.approx(0.0, abs=2 * dx)
    assert speeds[1][1] == pytest.approx(1.0, abs=2 * dx)


def test_intervals_groups_equal_values():
    values, ranges = riemann_tools.intervals([0, 0, 2, 1, 1, 1])
    assert values == [0, 2, 1] and ranges == [(0, 1), (2, 2), (3, 5)]


# --- Plotting ---------------------------------------------------------------------------
def lines_of(ax):
    return [(line.get_xdata(), line.get_ydata()) for line in ax.get_lines()]


def test_plot_waves_draws_each_wave_with_its_speed():
    states, speeds, reval, wave_types = burgers.exact_riemann_solution(2.0, 1.0)   # shock, s = 1.5
    fig, ax = plt.subplots()
    riemann_tools.plot_waves(states, speeds, reval, wave_types, t=0.5, ax=ax)
    x, t = lines_of(ax)[0]
    assert list(x) == [0, 1.5] and list(t) == [0, 1.0]
    # A rarefaction is drawn as a fan of 5 lines between its edge speeds
    states, speeds, reval, wave_types = burgers.exact_riemann_solution(1.0, 2.0)
    fig, ax = plt.subplots()
    riemann_tools.plot_waves(states, speeds, reval, wave_types, t=0.5, ax=ax)
    ends = sorted(x[1] for x, _ in lines_of(ax)[:5])
    np.testing.assert_allclose(ends, np.linspace(1.0, 2.0, 5))


def test_plot_riemann_plots_the_solution_at_time_t():
    states, speeds, reval, wave_types = burgers.exact_riemann_solution(1.0, 2.0)
    t = 0.4
    ax = riemann_tools.plot_riemann(states, speeds, reval, wave_types, t=t, extra_axes=True)
    assert len(ax) == 3                          # x-t plane, q, extra axis
    x, q = lines_of(ax[1])[-1]
    np.testing.assert_allclose(q, reval(x / t)[0], atol=1e-6)


def test_plot_riemann_with_derived_variables():
    q_l, q_r = np.array([1.0, 0.5]), np.array([0.2, -0.3])
    states, speeds, reval = acoustics.exact_riemann_solution(q_l, q_r, (1.0, 1.0))
    ax = riemann_tools.plot_riemann(states, speeds, lambda xi: np.array(reval(xi)), t=0.5,
                                    derived_variables=lambda q: np.array([q[0] * q[1]]))
    assert len(ax) == 2
    x, pu = lines_of(ax[1])[-1]
    p, u = reval(x / 0.5)
    np.testing.assert_allclose(pu, p * u, atol=1e-6)


@pytest.mark.filterwarnings("ignore:FigureCanvasAgg is non-interactive")
def test_make_plot_function():
    states, speeds, reval, wave_types = burgers.exact_riemann_solution(2.0, 1.0)
    plot = riemann_tools.make_plot_function(states, speeds, reval, wave_types)
    plot(0.3)
    assert len(plt.gcf().axes) == 2
    plot_chars = riemann_tools.make_plot_function(states, speeds, reval, wave_types,
                                                  plot_chars=[burgers.speed])
    plot_chars(0.3, 1)                           # with the characteristics of family 1


def test_plot_riemann_trajectories():
    states, speeds, reval, wave_types = traffic_LWR.riemann_traffic_exact(0.6, 0.1)
    x_traj = np.linspace(-1, 1, 5)[None, :] + np.zeros((11, 1))
    t_traj = np.linspace(0, 1, 11)
    ax = riemann_tools.plot_riemann_trajectories(x_traj, t_traj, speeds, wave_types, t=0.5)
    assert ax.get_title() == 'Waves and particle trajectories in x-t plane'


def test_characteristics_in_a_constant_state_are_straight_lines():
    """For Burgers with constant q = 0.5, every characteristic is x = x0 + 0.5 t."""
    states, speeds, reval, wave_types = burgers.exact_riemann_solution(0.5, 0.5)
    fig, ax = plt.subplots()
    ax.axis((-1, 1, 0, 1))
    riemann_tools.plot_characteristics(reval, burgers.speed, axes=ax)
    for x, t in lines_of(ax):
        np.testing.assert_allclose(x - x[0], 0.5 * (t - t[0]), atol=1e-12)


def test_characteristics_with_array_valued_speed():
    """char_speed may return a 1-element array (as traffic_LWR.c does); this used to crash
    with NumPy >= 2.4."""
    states, speeds, reval, wave_types = traffic_LWR.riemann_traffic_exact(0.2, 0.4)
    fig, ax = plt.subplots()
    ax.axis((-1, 1, 0, 1))
    riemann_tools.plot_characteristics(reval, traffic_LWR.c, axes=ax)
    assert len(ax.get_lines()) == 60
