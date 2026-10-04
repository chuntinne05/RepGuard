import json

import numpy as np
import pytest

from analyze_dart_postrun import metrics, paired_feedback, routing_comparison


def test_feedback_metrics_and_paired_identity():
    y = np.array([0, 1, 0, 1])
    p = np.array([0., 1., 0., 1.])
    m = metrics(y, p)
    assert m['auc'] == m['balanced_accuracy'] == m['accuracy'] == 1
    assert m['brier'] == 0
    result = paired_feedback(y, p, p, ['a', 'a', 'b', 'b'])
    assert result['accuracy_delta_ci95'] == [0, 0]
    assert result['balanced_accuracy_delta_ci95'] == [0, 0]
    assert metrics(y, np.full(4, .5))['auc'] == .5


def test_single_class_auc_and_balanced_accuracy_undefined():
    m = metrics(np.ones(3), np.array([.2, .5, .9]))
    assert m['auc'] is None and m['balanced_accuracy'] is None


def test_gold_only_control_feedback_invariance_guard(tmp_path):
    a, b = tmp_path / 'judge', tmp_path / 'self'
    a.mkdir(); b.mkdir()
    ids = [f'g{i//3}_{i%3}' for i in range(168)]
    predictions = {'task_ids': ids, 'predictions': {'0.1': {'UniformAuditGlobal': np.zeros((20,168)).tolist()}}}
    for root in (a, b):
        (root / 'predictions_private.json').write_text(json.dumps(predictions))
    assert routing_comparison(a, b)['gold_only_controls_invariant']
    predictions['predictions']['0.1']['UniformAuditGlobal'][0][0] = 1
    (a / 'predictions_private.json').write_text(json.dumps(predictions))
    with pytest.raises(ValueError, match='Gold-only control changed'):
        routing_comparison(a, b)
