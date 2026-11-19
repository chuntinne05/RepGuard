"""Fixed sparse-gold model selection. Learners receive audit callbacks, never full gold."""
import math
import numpy as np

METHODS = ('UniformGlobal', 'PairedGlobal', 'GoldRidge', 'CFGoldRectifier',
           'RawJudgeRectifier', 'CalibratedJudge', 'CFJudgeRectifier',
           'IndependentSH', 'PairedSH', 'RawJudge')
PRIMARY = 'CFJudgeRectifier'
CONTROLS = ('UniformGlobal', 'PairedGlobal', 'GoldRidge', 'CFGoldRectifier',
            'IndependentSH', 'PairedSH')
BUDGETS = (.05, .1, .2)
SEEDS = tuple(range(20))
MODELS = ('Qwen3-8B', 'DeepSeek-R1-0528-Qwen3-8B', 'Llama-3.1-8B-Instruct',
          'Qwen2.5-Coder-7B-Instruct', 'Fin-R1', 'gemma-2-9b-it')


class Audit:
    """Evaluator-owned finite-budget gold server. Only query is passed to a learner."""
    def __init__(self, gold, budget):
        self._gold = np.asarray(gold, float).copy()
        if self._gold.ndim != 2 or not np.isin(self._gold, [0, 1]).all():
            raise ValueError('Audit requires a binary history matrix')
        if not 0 <= budget <= self._gold.size:
            raise ValueError('Invalid audit budget')
        self.budget = budget
        self.indices = []
        self.labels = []

    def query(self, i, a):
        n, k = self._gold.shape
        if type(i) is not int or type(a) is not int or not (0 <= i < n and 0 <= a < k):
            raise ValueError('Gold query outside history')
        index = i * k + a
        if index in self.indices or len(self.indices) >= self.budget:
            raise ValueError('Duplicate query or gold budget exceeded')
        value = float(self._gold[i, a])
        self.indices.append(index)
        self.labels.append(value)
        return value


def choose(scores, priority):
    scores = np.asarray(scores, float)
    if not np.isfinite(scores).all():
        raise ValueError('Invalid model scores')
    ties = set(np.flatnonzero(np.isclose(scores, scores.max(), atol=1e-12, rtol=0)))
    return next(int(a) for a in priority if a in ties)


def audit_order(n, k, seed, paired):
    rng = np.random.default_rng(seed)
    if not paired:
        return rng.permutation(n * k).tolist()
    arms, rows = rng.permutation(k), rng.permutation(n)
    return [int(i * k + a) for i in rows for a in arms]


def observed_from_query(n, k, indices, query):
    observed = np.full((n, k), np.nan)
    for index in indices:
        i, a = divmod(int(index), k)
        value = query(i, a)
        if not np.isfinite(value) or value not in (0, 1):
            raise ValueError('Nonbinary audit response')
        observed[i, a] = value
    return observed


def means(observed):
    return (np.nansum(observed, axis=0) + 1) / (np.isfinite(observed).sum(axis=0) + 2)


def design(p, invalid, use_judge):
    p, invalid = np.asarray(p, float), np.asarray(invalid, bool)
    if p.ndim != 2 or p.shape != invalid.shape or not np.isfinite(p).all() or not ((p >= 0) & (p <= 1)).all():
        raise ValueError('Invalid feedback matrix')
    n, k = p.shape
    base = np.tile(np.column_stack([np.ones(k), np.eye(k)])[None, :, :], (n, 1, 1))
    penalty = np.array([0.] + [4.] * k)
    if not use_judge:
        return base, penalty
    extras = np.stack([p - .5, (p >= .9).astype(float) - .5,
                       np.broadcast_to(p.mean(1, keepdims=True) - .5, p.shape), invalid.astype(float)], axis=2)
    return np.concatenate([base, extras], axis=2), np.r_[penalty, np.ones(4)]


def predict(observed, p, invalid, out_p, out_invalid, use_judge):
    """Only finite (paid) training labels enter the fit; no-label fallback is explicit."""
    observed = np.asarray(observed, float)
    x, penalty = design(p, invalid, use_judge)
    z, _ = design(out_p, out_invalid, use_judge)
    if observed.shape != x.shape[:2] or z.shape[1:] != x.shape[1:] or np.isinf(observed).any():
        raise ValueError('Invalid observation shape')
    mask = np.isfinite(observed)
    if not np.isin(observed[mask], [0, 1]).all():
        raise ValueError('Invalid paid labels')
    if not mask.any():
        return np.full(z.shape[:2], .5)
    a = x[mask]
    beta = np.linalg.solve(a.T @ a + np.diag(penalty), a.T @ (observed[mask] - .5))
    return np.clip(.5 + z @ beta, 0, 1)


def cross_proxy(observed, p, invalid, use_judge):
    n = len(observed)
    if n < 3:
        raise ValueError('Need three inner question folds')
    folds = np.arange(n) % 3
    result = np.full(observed.shape, np.nan)
    trace = []
    for f in range(3):
        train, test = folds != f, folds == f
        count = int(np.isfinite(observed[train]).sum())
        result[test] = predict(observed[train], p[train], invalid[train], p[test], invalid[test], use_judge)
        trace.append({'fold': f, 'training_rows': np.flatnonzero(train).tolist(),
                      'prediction_rows': np.flatnonzero(test).tolist(), 'paid_training_labels': count,
                      'empty_training_fallback': count == 0})
    return result, trace


def rectify(observed, proxy):
    if observed.shape != proxy.shape or not np.isfinite(proxy).all():
        raise ValueError('Invalid residual proxy')
    if np.equal(proxy, .5).all():
        return means(observed)
    mask = np.isfinite(observed)
    return proxy.mean(0) + np.where(mask, np.nan_to_num(observed) - proxy, 0).sum(0) / (mask.sum(0) + 2)


def halving(n, k, budget, seed, paired, priority, query):
    """Exact-budget low-budget adaptation; old AppWorld implementation is unchanged."""
    counts = [k]
    while counts[-1] > 1:
        counts.append(math.ceil(counts[-1] / 2))
    stages = len(counts) - 1
    if stages == 0 or not sum(counts[:-1]) <= budget <= n * k:
        raise ValueError('Unsupported SH budget')
    rng = np.random.default_rng(seed)
    orders = np.tile(rng.permutation(n), (k, 1)) if paired else np.array([rng.permutation(n) for _ in range(k)])
    offsets = np.zeros(k, int)
    rank = {a: i for i, a in enumerate(priority)}
    active, indices, labels, trace = list(range(k)), [], [], []
    remaining = budget
    for stage in range(stages):
        size = len(active)
        future_min = sum(counts[stage + 1:-1])
        block = max(1, remaining // ((stages - stage) * size))
        block = min(block, (remaining - future_min) // size)
        extra = remaining % size if stage == stages - 1 else 0
        extra_arms = set(sorted(active, key=rank.get)[:extra])
        allocation = {a: block + int(a in extra_arms) for a in active}
        if block < 1 or any(offsets[a] + allocation[a] > n for a in active):
            raise ValueError('SH allocation exceeds distinct history capacity')
        start = len(indices)
        scores = {}
        for a in active:
            rewards = []
            for i in orders[a, offsets[a]:offsets[a] + allocation[a]]:
                value = float(query(int(i), int(a)))
                if not np.isfinite(value) or value not in (0, 1):
                    raise ValueError('Nonbinary SH response')
                indices.append(int(i) * k + int(a))
                labels.append(value)
                rewards.append(value)
            offsets[a] += allocation[a]
            scores[a] = float(np.mean(rewards))
        ranked = sorted(active, key=lambda a: (-scores[a], rank[a]))
        survivors = ranked[:math.ceil(size / 2)]
        trace.append({'stage': stage, 'active': active, 'survivors': survivors,
                      'scores': {str(a): scores[a] for a in active},
                      'allocation': {str(a): allocation[a] for a in active},
                      'audit_start': start, 'audit_stop': len(indices)})
        remaining -= len(indices) - start
        active = survivors
    if remaining != 0 or len(indices) != len(set(indices)) or len(indices) != budget:
        raise ValueError('SH exact-budget invariant failed')
    return {'agent': int(active[0]), 'audit_indices': indices, 'audit_labels': labels, 'rounds': trace}


def select_case(p, invalid, budget, seed, audit_factory):
    """Feedback must contain only historical tasks. Factory returns a bounded query callback."""
    p, invalid = np.asarray(p, float), np.asarray(invalid, bool)
    design(p, invalid, True)
    n, k = p.shape
    if not 0 < budget <= n * k:
        raise ValueError('Invalid gold budget')
    priority = np.random.default_rng(seed + 991).permutation(k).tolist()
    uniform_ids = audit_order(n, k, seed + 11, False)[:budget]
    paired_ids = audit_order(n, k, seed + 23, True)[:budget]
    uniform = observed_from_query(n, k, uniform_ids, audit_factory('uniform'))
    paired = observed_from_query(n, k, paired_ids, audit_factory('paired'))
    gold_proxy, gold_trace = cross_proxy(paired, p, invalid, False)
    judge_proxy, judge_trace = cross_proxy(paired, p, invalid, True)
    gold_fit = predict(paired, p, invalid, p, invalid, False)
    scores = {'UniformGlobal': means(uniform), 'PairedGlobal': means(paired),
              'GoldRidge': gold_fit.mean(0), 'CFGoldRectifier': rectify(paired, gold_proxy),
              'RawJudgeRectifier': rectify(paired, p), 'CalibratedJudge': judge_proxy.mean(0),
              'CFJudgeRectifier': rectify(paired, judge_proxy), 'RawJudge': p.mean(0)}
    choices = {m: choose(s, priority) for m, s in scores.items()}
    sh = {}
    for method, is_paired in (('IndependentSH', False), ('PairedSH', True)):
        sh[method] = halving(n, k, budget, seed + (23 if is_paired else 11), is_paired,
                             priority, audit_factory(method))
        choices[method] = sh[method]['agent']
    return {'agent_choices': choices, 'scores': {m: s.tolist() for m, s in scores.items()},
            'tie_priority': priority, 'uniform_indices': uniform_ids, 'paired_indices': paired_ids,
            'gold_crossfit_trace': gold_trace, 'judge_crossfit_trace': judge_trace,
            'gold_proxy': gold_proxy.tolist(), 'judge_proxy': judge_proxy.tolist(), 'halving': sh}


def observed_from_log(n, k, indices, labels):
    if len(indices) != len(labels) or len(indices) != len(set(indices)):
        raise ValueError('Invalid audit log')
    observed = np.full((n, k), np.nan)
    for index, label in zip(indices, labels):
        if type(index) is not int or not 0 <= index < n * k or label not in (0, 1):
            raise ValueError('Invalid audit log entry')
        observed.flat[index] = label
    return observed
