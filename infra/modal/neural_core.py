"""Gold-isolated frozen-feature routing; no network or outcome-store access."""
import hashlib
import numpy as np

HEADS = ('linear', 'lowrank', 'mlp')
REGS = (.01, .1)
SEEDS = (1404, 1405, 1406)


def observed_gold(gold, indices):
    out = np.full(np.shape(gold), np.nan)
    out.ravel()[indices] = np.asarray(gold).ravel()[indices]
    return out


def means(y):
    return (np.nansum(y, axis=0) + 1) / (np.isfinite(y).sum(axis=0) + 2)


def inner_folds(groups):
    unique = sorted(set(groups), key=lambda g: hashlib.sha256(('neural-inner-v1:' + g).encode()).hexdigest())
    if len(unique) < 3:
        raise ValueError('Need three groups')
    mapping = {g: i % 3 for i, g in enumerate(unique)}
    return np.array([mapping[g] for g in groups])


def features(train, test):
    center = train.mean(0)
    _, s, vt = np.linalg.svd(train - center, full_matrices=False)
    k = min(16, len(train)-1, int((s > 1e-8).sum()))
    if k == 0:
        return np.zeros((len(train), 1)), np.zeros((len(test), 1))
    scale = np.maximum(s[:k] / np.sqrt(len(train)), 1e-8)
    def transform(x):
        return np.clip(((x-center) @ vt[:k].T) / scale, -5, 5).astype('float32')
    return transform(train), transform(test)


def fit_predict(x, y, xt, head, reg, seed):
    import torch
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    if not np.isfinite(y).any():
        raise ValueError('No audited training labels')
    d, k = x.shape[1], y.shape[1]
    if head == 'linear':
        model = torch.nn.Linear(d, k)
        torch.nn.init.zeros_(model.weight)
        torch.nn.init.zeros_(model.bias)
    elif head == 'lowrank':
        model = torch.nn.Sequential(torch.nn.Linear(d, 2, bias=False), torch.nn.Linear(2, k))
        torch.nn.init.zeros_(model[1].weight)
        torch.nn.init.zeros_(model[1].bias)
    elif head == 'mlp':
        model = torch.nn.Sequential(torch.nn.Linear(d, 8), torch.nn.Tanh(), torch.nn.Linear(8, k))
        torch.nn.init.zeros_(model[2].weight)
        torch.nn.init.zeros_(model[2].bias)
    else:
        raise ValueError(head)
    base = means(y)
    offset = torch.tensor(np.log(base/(1-base)), dtype=torch.float32)
    xx = torch.tensor(x, dtype=torch.float32)
    yy = torch.tensor(np.nan_to_num(y), dtype=torch.float32)
    mask = torch.tensor(np.isfinite(y))
    optimizer = torch.optim.Adam(model.parameters(), lr=.02)
    for _ in range(300):
        optimizer.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits((model(xx)+offset)[mask], yy[mask])
        loss = loss + reg * sum(p.square().sum() for p in model.parameters())
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        return torch.sigmoid(model(torch.tensor(xt, dtype=torch.float32))+offset).numpy()


def ht_score(observed, actions):
    n, k = observed.shape
    count = np.isfinite(observed).sum()
    if not count:
        raise ValueError('No observed inner validation labels; fail closed')
    return float(np.nansum(observed[np.arange(n), actions]) / (count/(n*k)))


def route_case(x, observed, xt, groups, progress=lambda _: None):
    folds = inner_folds(groups)
    scores = {('Global', 0): 0.}
    scores.update({(h, r): 0. for h in HEADS for r in REGS})
    trace = []
    for f in range(3):
        train, val = folds != f, folds == f
        a, b = features(x[train], x[val])
        actions = np.full(val.sum(), means(observed[train]).argmax(), dtype=int)
        scores['Global', 0] += ht_score(observed[val], actions)
        trace.append({'fold': f, 'train_groups': sorted(set(np.array(groups)[train])),
                      'validation_groups': sorted(set(np.array(groups)[val])),
                      'training_labels': int(np.isfinite(observed[train]).sum()),
                      'validation_labels': int(np.isfinite(observed[val]).sum())})
        for h in HEADS:
            for r in REGS:
                progress(f'inner{f}:{h}:{r}')
                pred = fit_predict(a, observed[train], b, h, r, SEEDS[0])
                scores[h, r] += ht_score(observed[val], pred.argmax(1))
    best_regs = {h: max(REGS, key=lambda r: scores[h, r]) for h in HEADS}
    candidates = [('Global', 0)] + [(h, best_regs[h]) for h in HEADS]
    selected = max(candidates, key=lambda c: scores[c])[0]
    actions = {'Global': np.full(len(xt), means(observed).argmax(), dtype=int)}
    a, b = features(x, xt)
    for h in HEADS:
        progress('final:' + h)
        pred = np.mean([fit_predict(a, observed, b, h, best_regs[h], seed) for seed in SEEDS], axis=0)
        actions[h] = pred.argmax(1)
    actions['Selected'] = actions[selected].copy()
    return {h: v.tolist() for h, v in actions.items()}, {
        'selected': selected, 'regularization': best_regs,
        'inner_scores': {f'{h}:{r}': s/len(x) for (h, r), s in scores.items()}, 'inner_folds': trace}


def cluster_ci(delta, groups):
    unique = sorted(set(groups))
    totals = np.array([np.asarray(delta)[np.array(groups) == g].sum() for g in unique])
    counts = np.array([groups.count(g) for g in unique])
    draws = np.random.default_rng(1404).integers(0, len(unique), (5000, len(unique)))
    return np.quantile(totals[draws].sum(1)/counts[draws].sum(1), [.025, .975]).tolist()
