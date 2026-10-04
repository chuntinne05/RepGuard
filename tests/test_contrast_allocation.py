import numpy as np

from repguard.audit.design import contrast_allocation
from repguard.audit.routing import select_policy


def test_contrast_design_keeps_uniform_as_objective_safeguard():
    proxy = np.array([[0.95, 0.5, 0.1], [0.1, 0.8, 0.4], [0.5, 0.7, 0.9]])
    routes = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2], [0, 1, 2]])
    q, diagnostics = contrast_allocation(routes, proxy, 4)
    assert np.isclose(q.sum(), 4)
    assert q.min() >= 0.2 * 4 / 9 - 1e-9
    assert diagnostics['selected_objective'] <= diagnostics['uniform_objective'] + 1e-12
    assert diagnostics['selectable_contrasts'] == 6


def test_all_selectable_policies_receive_contrast_coverage():
    proxy = np.tile([0.99, 0.5, 0.01], (8, 1))
    routes = np.tile(np.arange(3)[:, None], (1, 8))
    result = select_policy('DARTContrast', routes, proxy, 0, 6,
                           np.random.default_rng(41), lambda i: np.zeros(len(i)))
    assert result['active_candidates'] == [0, 1, 2]
    assert result['audits'] == 6
    assert result['design_diagnostics']['objective_is_exact_sampling_variance'] is False
