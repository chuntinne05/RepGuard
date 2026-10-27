"""Finite-archive, exact-budget Sequential Halving; gold access by callback only."""
import math
import numpy as np

METHODS = ('IndependentSH', 'PairedSH')


def select(n_tasks, n_agents, budget, seed, paired, query):
    """Round-only means. Carry floor remainders forward; never query a cell twice."""
    rounds = math.ceil(math.log2(n_agents)) if n_agents > 1 else 0
    if rounds == 0 or not n_agents * rounds <= budget <= n_tasks * n_agents:
        raise ValueError('Unsupported agent count or budget')
    rng = np.random.default_rng(seed)
    priority = rng.permutation(n_agents).tolist()
    rank = {a: i for i, a in enumerate(priority)}
    if paired:
        order = np.tile(rng.permutation(n_tasks), (n_agents, 1))
    else:
        order = np.array([rng.permutation(n_tasks) for _ in range(n_agents)])
    offsets = np.zeros(n_agents, dtype=int)
    active = list(range(n_agents))
    trace, indices, labels = [], [], []
    remaining = budget
    for stage in range(rounds):
        k = len(active)
        stage_budget = remaining // (rounds - stage)
        count = stage_budget // k
        # Earlier rounds use complete blocks. Last round uses every remaining cell.
        extra = remaining % k if stage == rounds - 1 else 0
        extra_arms = set(sorted(active, key=rank.get)[:extra])
        counts = {a: count + int(a in extra_arms) for a in active}
        if count < 1 or any(offsets[a] + counts[a] > n_tasks for a in active):
            raise ValueError('Insufficient distinct archive rows for allocation')
        start = len(indices)
        scores = {}
        for a in active:
            rewards = []
            for i in order[a, offsets[a]:offsets[a] + counts[a]]:
                value = float(query(int(i), a))
                if not np.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError('Reward outside [0,1]')
                indices.append(int(i) * n_agents + a)
                labels.append(value)
                rewards.append(value)
            offsets[a] += counts[a]
            scores[a] = float(np.mean(rewards))
        survivors = sorted(active, key=lambda a: (-scores[a], rank[a]))[:math.ceil(k / 2)]
        trace.append({'stage': stage, 'active': active, 'survivors': survivors,
                      'scores': {str(a): s for a, s in scores.items()},
                      'audit_start': start, 'audit_stop': len(indices)})
        remaining -= len(indices) - start
        active = survivors
    assert remaining == 0 and len(indices) == len(set(indices)) == budget
    return {'agent': active[0], 'audit_indices': indices, 'audit_labels': labels,
            'rounds': trace, 'tie_priority': priority}
