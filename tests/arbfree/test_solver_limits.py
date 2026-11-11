from __future__ import annotations

import cvxpy as cp
import numpy as np
import pytest

from oqdata.arbfree.sanos_tools import SanosLPSolver


@pytest.mark.parametrize('algorithm,is_fallback', [('simplex', False), ('clarabel', False), ('simplex', True)])
def test_limit_accepts_feasible_nonoptimal_density(monkeypatch, algorithm, is_fallback):
    density = cp.Variable(3, bounds=[0., 1.])
    strikes = np.array([0.5, 1., 1.5])
    candidate = np.array([0.25, 0.5, 0.25])
    constraints = [cp.sum(density) == 1., strikes @ density == 1.]
    calls = []

    def solve(problem, **kwargs):
        calls.append(kwargs['solver'])
        density.save_value(candidate)
        problem._status = cp.USER_LIMIT
        problem._value = float(density[0].value)

    monkeypatch.setattr(cp.Problem, 'solve', solve)
    with pytest.warns(UserWarning, match='accepting feasible iterate'):
        result = SanosLPSolver(algorithm=algorithm)(
            objective=density[0], constraints=constraints, variables=[(density, None)], is_fallback=is_fallback,
        )

    assert result == (True, 'user_limit', is_fallback)
    assert len(calls) == 1  # No fallback when a feasible primary iterate is available.
    np.testing.assert_array_equal(density.value, candidate)
    assert density[0].value > 0.  # A point mass at strike 1 would minimize the objective.


@pytest.mark.parametrize('candidate', [
    None,
    [np.nan, 0.5, 0.25],
    [np.inf, 0.5, 0.25],
    [-0.1, 1.2, -0.1],  # Mass and martingale hold; implicit bounds fail.
    [0.25, 0.4, 0.25],  # Mass fails.
    [0.2, 0.5, 0.3],  # Martingale fails.
    [0., 1., 0.],  # Mass, martingale and bounds hold; calendar no-arbitrage fails.
])
def test_limit_rejects_missing_or_arbitrage_violating_density(monkeypatch, candidate):
    density = cp.Variable(3, bounds=[0., 1.])
    strikes = np.array([0.5, 1., 1.5])
    constraints = [cp.sum(density) == 1., strikes @ density == 1., np.maximum(strikes - 1., 0.) @ density >= 0.1]

    def solve(problem, **kwargs):
        density.save_value(None if candidate is None else np.asarray(candidate))
        problem._status = cp.USER_LIMIT
        problem._value = 0.  # Finite objective alone is insufficient.

    monkeypatch.setattr(cp.Problem, 'solve', solve)
    result = SanosLPSolver(algorithm='clarabel')(
        objective=density[0], constraints=constraints, variables=[(density, None)],
    )
    assert result == (False, 'user_limit', False)
