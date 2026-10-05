"""Tiny synthetic unit controls, never scientific experiment observations."""
import numpy as np
from neural_core import fit_predict


def smoke():
    x = np.linspace(-2, 2, 80, dtype=np.float32)[:, None]
    y = np.column_stack([x[:, 0] > 0, x[:, 0] <= 0]).astype(float)
    results = {}
    for head in ('linear', 'lowrank', 'mlp'):
        p = fit_predict(x, y, x, head, .01, 1404)
        q = fit_predict(x, y, x, head, .01, 1404)
        assert np.array_equal(p, q), 'Nondeterministic training'
        accuracy = float(y[np.arange(len(x)), p.argmax(1)].mean())
        assert accuracy > .95, (head, accuracy)
        negative = np.column_stack([np.ones(80), np.zeros(80)])
        q = fit_predict(x, negative, x, head, .01, 1404)
        assert (q.argmax(1) == 0).all(), 'Spurious switches in constant synthetic control'
        results[head] = {'synthetic_rescue_accuracy': accuracy, 'deterministic': True, 'constant_control_pass': True}
    return results
