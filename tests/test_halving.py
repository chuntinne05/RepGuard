import json
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'infra/modal'))
from halving_core import select


@pytest.mark.parametrize('paired', [False, True])
def test_exact_budget_distinct_queries_round_scores_and_pairing(paired):
    y = np.random.default_rng(8).integers(0, 2, (132, 14))
    for budget in (92, 93, 184, 185, 369, 370):
        calls = []
        def query(i, a):
            calls.append((i, a)); return y[i, a]
        r = select(132, 14, budget, 14, paired, query)
        assert len(calls) == len(set(calls)) == budget
        assert r['audit_indices'] == [i * 14 + a for i, a in calls]
        assert [len(t['active']) for t in r['rounds']] == [14, 7, 4, 2]
        for t in r['rounds']:
            rows = calls[t['audit_start']:t['audit_stop']]
            per_agent = {a: [i for i, aa in rows if aa == a] for a in t['active']}
            for a, ids in per_agent.items():
                assert t['scores'][str(a)] == float(y[ids, a].mean())
            if paired and t['stage'] < 3:
                assert all(ids == next(iter(per_agent.values())) for ids in per_agent.values())


@pytest.mark.parametrize('paired', [False, True])
def test_unqueried_labels_cannot_change_path(paired):
    y = np.random.default_rng(5).integers(0, 2, (132, 14))
    first = select(132, 14, 185, 65, paired, lambda i, a: y[i, a])
    z = 1 - y
    z.ravel()[first['audit_indices']] = y.ravel()[first['audit_indices']]
    assert select(132, 14, 185, 65, paired, lambda i, a: z[i, a]) == first


def test_known_best_and_tied_agents():
    for paired in (True, False):
        r = select(132, 14, 185, 77, paired, lambda i, a: float(a == 12))
        assert r['agent'] == 12
        tie = select(132, 14, 185, 77, paired, lambda i, a: 0.0)
        assert tie['agent'] == tie['tie_priority'][0]
    with pytest.raises(ValueError):
        select(2, 14, 56, 0, True, lambda i, a: 0.)


def test_pipeline_resume_and_terminal_idempotence(tmp_path, monkeypatch):
    import halving_pipeline as p
    monkeypatch.setattr(p, 'verify', lambda packet: None)
    monkeypatch.setattr(p, 'summarize', lambda *args: {'new_baseline_signal_pass': False, 'methods': {}})
    calls = []
    def stub(n, k, budget, seed, paired, query):
        assert n == 4 and k == 2
        assert query(0, 0) == 1
        calls.append(1)
        if len(calls) == 3:
            raise RuntimeError('injected interruption')
        return {'agent': 0}
    monkeypatch.setattr(p, 'select', stub)
    packet = {'run_id': 'test', 'success': [[1., 0.]] * 5, 'folds': list(range(5)), 'groups': list(range(5)),
              'cases': [{'budget_fraction': b, 'fold': f, 'seed': s, 'rng_seed': s, 'budget': 1}
                        for b in (.05, .1, .2) for f in range(5) for s in range(20)]}
    with pytest.raises(RuntimeError, match='injected'):
        p.run(packet, tmp_path, lambda: None)
    assert len(list(tmp_path.glob('case_*.json'))) == 1
    assert json.loads((tmp_path / 'status.json').read_text())['state'] == 'pipeline_failed'
    status = p.run(packet, tmp_path, lambda: None)
    assert status['completed'] == 300 and len(calls) == 601
    assert p.run(packet, tmp_path, lambda: None) == status and len(calls) == 601


def test_checkpoint_corruption_rejected():
    from halving_pipeline import validate
    from neural_pipeline import digest
    row = {'case': 'test', 'agent': 1}
    row['artifact_sha256'] = digest(row)
    validate(row)
    row['agent'] = 2
    with pytest.raises(ValueError, match='checksum'):
        validate(row)
