"""miniclaw Riemann solvers: Burgers and acoustics."""

import numpy as np
import pytest

from miniclaw import riemann


def states(*rows):
    return np.array(rows, dtype=float)


BURGERS_SOLVERS = [riemann.burgers_1D, riemann.burgers_1D_py.burgers_1D]


@pytest.mark.parametrize("rs", BURGERS_SOLVERS)
def test_burgers_wave_is_jump_and_speed_is_rankine_hugoniot(rs):
    q_l, q_r = states([2.0, 1.0, -1.0, 0.5]), states([1.0, 2.0, 2.0, 0.5])
    wave, s, amdq, apdq = rs(q_l, q_r, None, None, {'efix': False})
    np.testing.assert_array_equal(wave[:, 0, :], q_r - q_l)
    np.testing.assert_allclose(s[0], (q_l[0] + q_r[0]) / 2)


@pytest.mark.parametrize("rs", BURGERS_SOLVERS)
@pytest.mark.parametrize("efix", [False, True])
def test_burgers_fluctuations_sum_to_flux_difference(rs, efix):
    rng = np.random.default_rng(0)
    q_l, q_r = rng.uniform(-2, 2, (1, 50)), rng.uniform(-2, 2, (1, 50))
    _, _, amdq, apdq = rs(q_l, q_r, None, None, {'efix': efix})
    np.testing.assert_allclose(amdq + apdq, 0.5 * q_r**2 - 0.5 * q_l**2, atol=1e-14)


@pytest.mark.parametrize("rs", BURGERS_SOLVERS)
def test_burgers_entropy_fix_only_changes_transonic_rarefactions(rs):
    q_l, q_r = states([-1.0, 1.0, -1.0, 2.0]), states([2.0, 2.0, -2.0, -1.0])
    _, _, amdq_fix, apdq_fix = rs(q_l, q_r, None, None, {'efix': True})
    _, _, amdq, apdq = rs(q_l, q_r, None, None, {'efix': False})
    # Only the first interface (q_l = -1 < 0 < 2 = q_r) is a transonic rarefaction:
    # the flux difference is split at the sonic point q = 0.
    np.testing.assert_allclose([amdq_fix[0, 0], apdq_fix[0, 0]], [-0.5, 2.0])
    np.testing.assert_array_equal(amdq_fix[:, 1:], amdq[:, 1:])
    np.testing.assert_array_equal(apdq_fix[:, 1:], apdq[:, 1:])


def test_burgers_default_entropy_fix_matches_clawpack():
    """Fortran burgers_1D always uses the entropy fix; burgers_1D_py only when asked."""
    q_l, q_r = states([-1.0]), states([2.0])
    assert riemann.burgers_1D(q_l, q_r, None, None, {})[2][0, 0] == -0.5
    assert riemann.burgers_1D_py.burgers_1D(q_l, q_r, None, None, {})[2][0, 0] == 0.0   # s = 0.5 > 0


ACOUSTICS = {'rho': 2.0, 'bulk': 0.5, 'zz': 1.0, 'cc': 0.5}


def test_acoustics_waves_are_eigenvectors_summing_to_jump():
    rng = np.random.default_rng(1)
    q_l, q_r = rng.normal(size=(2, 30)), rng.normal(size=(2, 30))
    wave, s, amdq, apdq = riemann.acoustics_1D(q_l, q_r, None, None, ACOUSTICS)
    Z, c = ACOUSTICS['zz'], ACOUSTICS['cc']
    np.testing.assert_allclose(wave.sum(axis=1), q_r - q_l, atol=1e-14)
    np.testing.assert_allclose(wave[0, 0], -Z * wave[1, 0])     # r1 = (-Z, 1)
    np.testing.assert_allclose(wave[0, 1], Z * wave[1, 1])      # r2 = (Z, 1)
    np.testing.assert_allclose(s, [[-c] * 30, [c] * 30])
    # A-dQ + A+dQ = A (q_r - q_l) with A = [[0, K], [1/rho, 0]]
    A = np.array([[0.0, ACOUSTICS['bulk']], [1 / ACOUSTICS['rho'], 0.0]])
    np.testing.assert_allclose(amdq + apdq, A @ (q_r - q_l), atol=1e-14)


def test_acoustics_matches_exact_solver_middle_state():
    from exact_solvers import acoustics
    q_l, q_r = np.array([1.0, 0.5]), np.array([0.2, -0.3])
    wave, *_ = riemann.acoustics_1D(q_l[:, None], q_r[:, None], None, None, ACOUSTICS)
    states_exact, _, _ = acoustics.exact_riemann_solution(q_l, q_r, (ACOUSTICS['rho'], ACOUSTICS['bulk']))
    np.testing.assert_allclose(q_l + wave[:, 0, 0], states_exact[:, 1])


@pytest.mark.parametrize("rs, num_eqn", [(riemann.burgers_1D, 1), (riemann.acoustics_1D, 2)])
def test_equal_states_give_no_waves(rs, num_eqn):
    q = np.ones((num_eqn, 5))
    wave, s, amdq, apdq = rs(q, q, None, None, ACOUSTICS)
    assert not wave.any() and not amdq.any() and not apdq.any()
    assert rs.num_eqn == num_eqn and rs.num_waves == wave.shape[1]


# --- Shallow water --------------------------------------------------------------------
G = {'grav': 1.0}


def swe_flux(q, g=1.0):
    h, hu = q[0], q[1]
    return np.array([hu, hu**2 / h + 0.5 * g * h**2])


def random_swe_states(n, seed):
    rng = np.random.default_rng(seed)
    h = rng.uniform(0.3, 3.0, (2, n))
    u = rng.uniform(-2.0, 2.0, (2, n))
    return np.array([h[0], h[0] * u[0]]), np.array([h[1], h[1] * u[1]])


@pytest.mark.parametrize("rs", [riemann.shallow_roe_with_efix_1D, riemann.shallow_hlle_1D])
def test_shallow_water_fluctuations_sum_to_flux_difference(rs):
    q_l, q_r = random_swe_states(200, seed=2)
    wave, s, amdq, apdq = rs(q_l, q_r, None, None, G)
    np.testing.assert_allclose(wave.sum(axis=1), q_r - q_l, atol=1e-12)
    np.testing.assert_allclose(amdq + apdq, swe_flux(q_r) - swe_flux(q_l), atol=1e-12)


def test_shallow_roe_resolves_an_isolated_shock_exactly():
    """For states joined by a single 2-shock, the Roe solver gives one wave with the
    Rankine-Hugoniot speed (Roe property)."""
    from exact_solvers import shallow_water
    q_l, q_r = np.array([3.0, 0.0]), np.array([1.0, 0.0])    # dam break: 1-rarefaction, 2-shock
    states, speeds, _, wave_types = shallow_water.exact_riemann_solution(q_l, q_r)
    assert wave_types[1] == 'shock'
    q_m = states[:, 1]   # the 2-shock joins q_m and q_r
    wave, s, _, _ = riemann.shallow_roe_with_efix_1D(q_m[:, None], q_r[:, None], None, None, G)
    np.testing.assert_allclose(wave[:, 0, 0], 0.0, atol=1e-12)
    assert s[1, 0] == pytest.approx(speeds[1])


def test_shallow_roe_entropy_fix_only_acts_on_transonic_rarefactions():
    q_l, q_r = random_swe_states(500, seed=3)
    wave, s, amdq, _ = riemann.shallow_roe_with_efix_1D(q_l, q_r, None, None, G)
    amdq_no_fix = (s * (s < 0))[0] * wave[:, 0] + (s * (s < 0))[1] * wave[:, 1]
    u_l, u_r = q_l[1] / q_l[0], q_r[1] / q_r[0]
    h_m, h_m2 = q_l[0] + wave[0, 0], q_r[0] - wave[0, 1]
    u_m, u_m2 = (q_l[1] + wave[1, 0]) / h_m, (q_r[1] - wave[1, 1]) / h_m2
    # Roe middle depths can be negative for strong rarefactions; sqrt gives nan there and the
    # comparisons are False, as in Clawpack.
    with np.errstate(invalid='ignore'):
        transonic_1 = (u_l - np.sqrt(q_l[0]) < 0) & (u_m - np.sqrt(h_m) > 0)
        transonic_2 = (u_m2 + np.sqrt(h_m2) < 0) & (u_r + np.sqrt(q_r[0]) > 0)
    unchanged = ~(transonic_1 | transonic_2)
    assert transonic_1.any() and unchanged.any()
    np.testing.assert_allclose(amdq[:, unchanged], amdq_no_fix[:, unchanged], atol=1e-13)
    assert not np.allclose(amdq[:, transonic_1], amdq_no_fix[:, transonic_1])


def test_shallow_hlle_uses_einfeldt_speeds():
    """s1 = min(u_l - c_l, u_hat - c_hat) and s2 = max(u_r + c_r, u_hat + c_hat)."""
    q_l, q_r = random_swe_states(100, seed=4)
    _, s, _, _ = riemann.shallow_hlle_1D(q_l, q_r, None, None, G)
    _, s_roe, _, _ = riemann.shallow_roe_with_efix_1D(q_l, q_r, None, None, G)
    u_l, u_r = q_l[1] / q_l[0], q_r[1] / q_r[0]
    np.testing.assert_allclose(s[0], np.minimum(u_l - np.sqrt(q_l[0]), s_roe[0]), rtol=1e-14)
    np.testing.assert_allclose(s[1], np.maximum(u_r + np.sqrt(q_r[0]), s_roe[1]), rtol=1e-14)


def test_shallow_hlle_middle_depth_stays_positive_for_strong_rarefaction():
    q_l, q_r = np.array([[1.0], [-3.0]]), np.array([[1.0], [3.0]])
    wave, _, _, _ = riemann.shallow_hlle_1D(q_l, q_r, None, None, G)
    assert q_l[0, 0] + wave[0, 0, 0] > 0


def test_shallow_tracer_flow_part_matches_roe_and_tracer_moves_with_flow():
    q_l, q_r = random_swe_states(100, seed=5)
    rng = np.random.default_rng(6)
    t_l, t_r = rng.uniform(0, 1, (2, 100))
    wave, s, amdq, apdq = riemann.shallow_roe_tracer_1D(np.vstack([q_l, t_l]), np.vstack([q_r, t_r]),
                                                        None, None, G)
    wave_r, s_r, amdq_r, apdq_r = riemann.shallow_roe_with_efix_1D(q_l, q_r, None, None, G)
    np.testing.assert_array_equal(wave[:2, :2], wave_r)
    np.testing.assert_array_equal(amdq[:2], amdq_r)
    np.testing.assert_array_equal(apdq[:2], apdq_r)
    np.testing.assert_array_equal(wave[2, 2], t_r - t_l)
    u_hat = (s_r[0] + s_r[1]) / 2
    np.testing.assert_allclose(s[2], u_hat)
    np.testing.assert_allclose(amdq[2] + apdq[2], u_hat * (t_r - t_l))


# --- Euler ----------------------------------------------------------------------------
GAMMA = 1.4
EULER = {'gamma': GAMMA, 'gamma1': GAMMA - 1, 'efix': False}
EULER_SOLVERS = [riemann.euler_1D_py.euler_roe_1D, riemann.euler_1D_py.euler_hll_1D,
                 riemann.euler_with_efix_1D]


def euler_conserved(rho, u, p):
    return np.array([rho, rho * u, p / (GAMMA - 1) + 0.5 * rho * u**2])


def euler_flux(q):
    rho, mom, E = q
    u = mom / rho
    p = (GAMMA - 1) * (E - 0.5 * rho * u**2)
    return np.array([mom, mom * u + p, u * (E + p)])


def random_euler_states(n, seed):
    rng = np.random.default_rng(seed)
    return [euler_conserved(rng.uniform(0.2, 3, n), rng.uniform(-3, 3, n), rng.uniform(0.2, 3, n))
            for _ in range(2)]


@pytest.mark.parametrize("rs", EULER_SOLVERS)
def test_euler_fluctuations_sum_to_flux_difference(rs):
    q_l, q_r = random_euler_states(300, seed=7)
    wave, s, amdq, apdq = rs(q_l, q_r, None, None, EULER)
    np.testing.assert_allclose(wave.sum(axis=1), q_r - q_l, atol=1e-11)
    np.testing.assert_allclose(amdq + apdq, euler_flux(q_r) - euler_flux(q_l), atol=1e-10)


@pytest.mark.parametrize("rs", [riemann.euler_1D_py.euler_roe_1D, riemann.euler_with_efix_1D])
def test_euler_roe_resolves_isolated_contact_and_shock(rs):
    """Roe property: a single contact or shock gives one wave with the exact speed."""
    from exact_solvers import euler
    # Contact: same velocity and pressure, different density.
    q_l, q_r = euler_conserved(1.0, 0.5, 1.0), euler_conserved(0.25, 0.5, 1.0)
    wave, s, _, _ = rs(q_l[:, None], q_r[:, None], None, None, EULER)
    np.testing.assert_allclose(wave[:, [0, 2], 0], 0.0, atol=1e-13)
    assert s[1, 0] == pytest.approx(0.5)
    # 3-shock of the Sod problem: states either side of it.
    states, speeds, _, wave_types = euler.exact_riemann_solution(euler_conserved(1, 0, 1),
                                                                 euler_conserved(0.125, 0, 0.1))
    assert wave_types[2] == 'shock'
    wave, s, _, _ = rs(states[:, 2:3], states[:, 3:4], None, None, EULER)
    np.testing.assert_allclose(wave[:, :2, 0], 0.0, atol=1e-12)
    assert s[2, 0] == pytest.approx(speeds[2])


def test_euler_entropy_fix_only_acts_on_transonic_rarefactions():
    """Away from transonic rarefactions, the entropy-fixed Roe solver equals plain Roe."""
    q_l, q_r = random_euler_states(500, seed=8)
    _, _, amdq_fix, _ = riemann.euler_with_efix_1D(q_l, q_r, None, None, EULER)
    wave, s, amdq, _ = riemann.euler_1D_py.euler_roe_1D(q_l, q_r, None, None, EULER)

    def u_c(q, sign):
        rho, mom, E = q
        p = (GAMMA - 1) * (E - 0.5 * mom**2 / rho)
        with np.errstate(invalid='ignore'):   # Roe middle states may be unphysical
            return mom / rho + sign * np.sqrt(GAMMA * p / rho)

    transonic_1 = (u_c(q_l, -1) < 0) & (u_c(q_l + wave[:, 0], -1) > 0)
    transonic_3 = (u_c(q_r - wave[:, 2], 1) < 0) & (u_c(q_r, 1) > 0)
    unchanged = ~(transonic_1 | transonic_3)
    assert transonic_1.any() and unchanged.any()
    np.testing.assert_allclose(amdq_fix[:, unchanged], amdq[:, unchanged], atol=1e-12)
    assert not np.allclose(amdq_fix[:, transonic_1], amdq[:, transonic_1])


def test_euler_hll_middle_state_is_physical_for_strong_rarefaction():
    """HLL keeps positive density and pressure in the 123 problem (Toro's test 2)."""
    q_l, q_r = euler_conserved(1.0, -2.0, 0.4), euler_conserved(1.0, 2.0, 0.4)
    wave, _, _, _ = riemann.euler_1D_py.euler_hll_1D(q_l[:, None], q_r[:, None], None, None, EULER)
    rho, mom, E = q_l + wave[:, 0, 0]
    assert rho > 0 and (GAMMA - 1) * (E - 0.5 * mom**2 / rho) > 0
