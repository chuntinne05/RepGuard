import json

import numpy as np
import pytest

from repguard.audit.feedback import judge_feedback
from repguard.audit.routing import calibrated_proxy


def test_abstention_calibration_is_finite_and_anchor_only():
    f = np.array([[0, 2], [1, 2]])
    a = np.array([[0., np.nan], [1., 1.]])
    result = calibrated_proxy(f, a, np.array([[2, 2], [1, 0]]))
    assert np.isfinite(result).all()
    assert ((result > 0) & (result < 1)).all()
    with pytest.raises(ValueError):
        calibrated_proxy(f, a, np.array([[3, 0]]))


def test_completed_judge_matrix_rejects_missing_and_duplicate_rows(tmp_path):
    cases = [{'task_id': 'a_1', 'agent': 'x'}, {'task_id': 'b_1', 'agent': 'x'}]
    manifest = {'hash': 'frozen', 'cases': cases}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    (tmp_path / 'pilot_quality.json').write_text(json.dumps({'protocol_hash': 'frozen', 'gate_pass': True}))
    rows = [{'index': i, 'case': c, 'protocol_hash': 'frozen', 'valid': True,
             'success_probability': p} for i, (c, p) in enumerate(zip(cases, [.8, .1]))]
    ledger = tmp_path / 'judgments_private.jsonl'
    def write(values):
        ledger.write_text(''.join(json.dumps(r) + '\n' for r in values))
    write(rows)
    feedback, _ = judge_feedback(tmp_path, ['b_1', 'a_1'], ['x'])
    np.testing.assert_array_equal(feedback, [[0], [1]])
    write(rows[:1])
    with pytest.raises(ValueError, match='Incomplete'):
        judge_feedback(tmp_path, ['a_1', 'b_1'], ['x'])
    write([rows[0], rows[0]])
    with pytest.raises(ValueError, match='identity'):
        judge_feedback(tmp_path, ['a_1', 'b_1'], ['x'])
