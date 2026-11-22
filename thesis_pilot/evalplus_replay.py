"""Step-3 equal-information replay for the EvalPlus partial-feedback pilot.

Implements protocol 2026-11-09 §5 exactly. Written before the greedy bank was
scored; called only when the greedy gate passes. Pure CPU, no inference.
"""

from __future__ import annotations

import hashlib
import random
import warnings

import numpy as np

KS = [16, 39]
POLICIES = ["Uniform", "CensoredUniform", "Disagreement"]
SELECTORS = ["BestFixedB", "RawB", "GlobalRepF", "CensoredRep", "ActionValue"]
SEEDS = 200
BOOT = 2000


def _rng(*parts) -> random.Random:
    return random.Random(int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:16], 16))


def _argmax(cands, score, tie):
    return max(cands, key=lambda m: (score[m], tie[m]))


def _audit(policy, hist, bank, models, k, rng):
    if policy == "Uniform":
        pool = list(hist)
        rng.shuffle(pool)
        return set(pool[:k])
    b1 = [c for c in hist if bank[(c[0], c[1], 0)][0]]
    if policy == "CensoredUniform":
        rng.shuffle(b1)
        return set(b1[:k])
    # Disagreement: B=1 cells on tasks where >=2 models pass B (visible without F)
    nB = {}
    for m, t in hist:
        nB[t] = nB.get(t, 0) + bank[(m, t, 0)][0]
    hi = [c for c in b1 if nB[c[1]] >= 2]
    lo = [c for c in b1 if nB[c[1]] < 2]
    rng.shuffle(hi)
    rng.shuffle(lo)
    return set((hi + lo)[:k])


def _action_value(known, hist_b, models, cur, fallback):
    from sklearn.linear_model import LogisticRegression

    X, y = [], []
    idx = {m: i for i, m in enumerate(models)}
    for (m, _t), (b, f) in known.items():
        row = [0.0] * len(models)
        row[idx[m]] = 1.0
        X.append(row + [float(b), hist_b[m]])
        y.append(f)
    if len(set(y)) < 2:
        return fallback
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clf = LogisticRegression(C=1.0, max_iter=1000).fit(np.array(X), np.array(y))
    rows = []
    for m in models:
        row = [0.0] * len(models)
        row[idx[m]] = 1.0
        rows.append(row + [float(cur[m]), hist_b[m]])
    p = clf.predict_proba(np.array(rows))[:, 1]
    best = max(range(len(models)), key=lambda i: (p[i], hist_b[models[i]]))
    return models[best]


def fractional_ks(n_tasks, n_models, fracs=(0.10, 0.25)):
    """k = round(frac*|H|), |H| = (n_tasks-1)*n_models (protocol v2 §6)."""
    return [round(f * (n_tasks - 1) * n_models) for f in fracs]


def run_replay(bank, models, tids, ks=None):
    ks = list(ks) if ks is not None else KS  # v1 default KS=[16,39]; primary is ks[0]
    tie = {m: -i for i, m in enumerate(models)}  # deterministic final tie-break
    oracle = {t: max(bank[(m, t, 0)][1] for m in models) for t in tids}
    best_fixed_f_model = max(models, key=lambda m: sum(bank[(m, t, 0)][1] for t in tids))
    # per (k, policy, selector) -> per-task mean reward over seeds
    reward = {(k, p, s): {t: 0.0 for t in tids} for k in ks for p in POLICIES for s in SELECTORS}
    for t in tids:
        hist = [(m, u) for u in tids if u != t for m in models]
        hist_b = {m: float(np.mean([bank[(m, u, 0)][0] for u in tids if u != t])) for m in models}
        cur = {m: bank[(m, t, 0)][0] for m in models}
        cands = [m for m in models if cur[m]] or list(models)
        fixed_b = _argmax(models, hist_b, tie)
        raw_b = _argmax(cands, hist_b, tie)
        for k in ks:
            for p in POLICIES:
                for seed in range(SEEDS):
                    A = _audit(p, hist, bank, models, k, _rng("audit", t, k, p, seed))
                    known = {c: bank[(c[0], c[1], 0)] for c in hist
                             if c in A or bank[(c[0], c[1], 0)][0] == 0}
                    g = {}
                    for m in models:
                        fs = [f for (mm, _u), (_b, f) in known.items() if mm == m]
                        g[m] = (1 + sum(fs)) / (2 + len(fs))
                    c = {}
                    for m in models:
                        fs = [bank[(mm, u, 0)][1] for (mm, u) in A if mm == m and bank[(mm, u, 0)][0]]
                        c[m] = (1 + sum(fs)) / (2 + len(fs))
                    tb = {m: (hist_b[m], tie[m]) for m in models}
                    choice = {
                        "BestFixedB": fixed_b,
                        "RawB": raw_b,
                        "GlobalRepF": max(cands, key=lambda m: (g[m], tb[m])),
                        "CensoredRep": max(cands, key=lambda m: (c[m], tb[m])),
                        "ActionValue": _action_value(known, hist_b, models, cur, raw_b),
                    }
                    for s, m in choice.items():
                        reward[(k, p, s)][t] += bank[(m, t, 0)][1] / SEEDS

    def boot_ci(diff):
        rng = np.random.default_rng(20261109)
        d = np.array(diff)
        sims = [d[rng.integers(0, len(d), len(d))].sum() for _ in range(BOOT)]
        return [round(float(np.percentile(sims, 2.5)), 3), round(float(np.percentile(sims, 97.5)), 3)]

    table = []
    for k in ks:
        for p in POLICIES:
            row = {"k": k, "policy": p}
            for s in SELECTORS:
                row[s] = round(sum(reward[(k, p, s)].values()), 3)
            table.append(row)
    primary = {}
    for comp in ["RawB", "ActionValue", "GlobalRepF"]:
        diff = [reward[(ks[0], "CensoredUniform", "CensoredRep")][t] - reward[(ks[0], "CensoredUniform", comp)][t] for t in tids]
        primary[f"CensoredRep_minus_{comp}"] = {"total": round(sum(diff), 3), "ci95": boot_ci(diff)}
    success = all(primary[f"CensoredRep_minus_{c}"]["total"] >= 1 and primary[f"CensoredRep_minus_{c}"]["ci95"][0] > 0
                  for c in ["RawB", "ActionValue"])
    return {
        "summary": {"oracle": sum(oracle.values()), "best_fixed_F": sum(bank[(best_fixed_f_model, t, 0)][1] for t in tids),
                    "best_fixed_F_model": best_fixed_f_model, "primary_k16_CensoredUniform": primary, "primary_k": ks[0],
                    "primary_success": success},
        "table": table,
        "per_task": {f"{k}|{p}|{s}": reward[(k, p, s)] for k in ks for p in POLICIES for s in SELECTORS},
        "config": {"ks": ks, "policies": POLICIES, "selectors": SELECTORS, "seeds": SEEDS, "bootstrap": BOOT},
    }
