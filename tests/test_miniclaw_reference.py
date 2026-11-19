"""miniclaw reproduces the book's PyClaw runs.

The reference results in tests/reference/ were computed with Clawpack 5.14 by
generate_reference.py; the same setups (reference/book_setups.py) are run here with miniclaw.
"""

import os

import numpy as np
import pytest

from miniclaw import pyclaw, riemann
from reference import book_setups

book_setups.use(pyclaw, riemann)
REFERENCE = os.path.join(os.path.dirname(__file__), 'reference')


def load(name):
    return np.load(os.path.join(REFERENCE, name + '.npz'))


def assert_matches_reference(name, claw, every=1, rtol=1e-10, atol=1e-12):
    ref = load(name)
    frames = claw.frames[::every]
    np.testing.assert_allclose([f.t for f in frames], ref['t'], rtol=1e-12, atol=1e-14)
    np.testing.assert_allclose(claw.frames[0].grid.p_centers[0], ref['x'], rtol=1e-14)
    np.testing.assert_allclose(np.array([f.q for f in frames]), ref['q'], rtol=rtol, atol=atol)


@pytest.mark.parametrize("efix", [False, True])
@pytest.mark.parametrize("q_l, q_r, name", [(2., 1., 'shock'), (1., 2., 'raref'), (-1., 2., 'transonic')])
def test_burgers_approximate(q_l, q_r, name, efix):
    assert_matches_reference(f"burgers_approximate_{name}_efix{efix}",
                             book_setups.burgers_approximate(q_l, q_r, efix=efix))


def test_acoustics_bump():
    assert_matches_reference("acoustics_bump", book_setups.acoustics_bump(), every=5)


def test_burgers_bump():
    assert_matches_reference("burgers_bump", book_setups.burgers_bump(), every=5)


@pytest.mark.parametrize("riemann_solver", ['roe', 'hlle'])
def test_fv_compare_shallow_water_dam_break(riemann_solver):
    assert_matches_reference(f"fv_compare_shallow_{riemann_solver}",
                             book_setups.shallow_dam_break(riemann_solver))


@pytest.mark.parametrize("constant_initial_data", [False, True])
def test_kitchen_sink(constant_initial_data):
    name = "kitchen_sink" + ("_constant_initial_data" if constant_initial_data else "")
    assert_matches_reference(name, book_setups.kitchen_sink(constant_initial_data), every=5)


@pytest.mark.parametrize("riemann_solver", ['Roe', 'HLL'])
def test_fv_compare_shocktube_classic(riemann_solver):
    assert_matches_reference(f"fv_compare_shocktube_{riemann_solver}_classic",
                             book_setups.shocktube(riemann_solver, 'classic'))


@pytest.mark.parametrize("riemann_solver", ['Roe', 'HLL'])
def test_fv_compare_shocktube_sharpclaw(riemann_solver):
    assert_matches_reference(f"fv_compare_shocktube_{riemann_solver}_sharpclaw",
                             book_setups.shocktube(riemann_solver, 'sharpclaw'))


@pytest.mark.parametrize("riemann_solver", ['Roe', 'HLL'])
def test_fv_compare_blastwave(riemann_solver):
    assert_matches_reference(f"fv_compare_blastwave_{riemann_solver}",
                             book_setups.blastwave(riemann_solver))


@pytest.mark.parametrize("name, rs", [('euler_roe', riemann.euler_1D_py.euler_roe_1D),
                                      ('euler_hll', riemann.euler_1D_py.euler_hll_1D)])
def test_python_euler_solvers_match_clawpack_pointwise(name, rs):
    ref = load('riemann_py')
    key = name + '__'
    out = rs(ref[key + 'q_l'], ref[key + 'q_r'], None, None, {'gamma': 1.4, 'gamma1': 0.4, 'efix': False})
    for field, value in zip(('wave', 's', 'amdq', 'apdq'), out):
        np.testing.assert_allclose(value, ref[key + field], rtol=1e-13, atol=1e-13)


@pytest.mark.parametrize("rs", ['traffic_vc_1D', 'traffic_vc_fwave_1D'])
@pytest.mark.parametrize("rho_l, rho_r, v_l, v_r", [(0.7, 0.5, 1.0, 1.5), (0.7, 0.2, 1.0, 1.0)])
def test_traffic_variable_speed(rho_l, rho_r, v_l, v_r, rs):
    assert_matches_reference(f"traffic_variable_speed_{rho_l}_{rho_r}_{v_l}_{v_r}_{rs}",
                             book_setups.traffic_variable_speed(rho_l, rho_r, v_l, v_r,
                                                                getattr(riemann, rs)))


def test_nonlinear_elasticity_solver_matches_clawpack_pointwise():
    ref = load('riemann_py')
    key = 'nonlinear_elasticity__'
    out = riemann.nonlinear_elasticity_1D_py.nonlinear_elasticity_1D(
        ref[key + 'q_l'], ref[key + 'q_r'], ref[key + 'aux_l'], ref[key + 'aux_r'],
        {'stress_relation': 'quadratic'})
    for field, value in zip(('wave', 's', 'amdq', 'apdq'), out):
        np.testing.assert_allclose(value, ref[key + field], rtol=1e-14, atol=1e-14)


def test_python_burgers_solver_matches_clawpack_pointwise():
    ref = load('riemann_py')
    for efix in (False, True):
        key = f"burgers_efix{efix}__"
        out = riemann.burgers_1D_py.burgers_1D(ref[key + 'q_l'], ref[key + 'q_r'], None, None, {'efix': efix})
        for name, value in zip(('wave', 's', 'amdq', 'apdq'), out):
            np.testing.assert_allclose(value, ref[key + name], rtol=1e-14, atol=1e-14)
