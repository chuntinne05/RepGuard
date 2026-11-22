"""EvalPlus v3 disagreement audit (protocol 2026-11-22).

    python -m thesis_pilot.evalplus_disagreement confirm|gen|exec|score
Model code runs only inside ``docker run --network none`` (same image as v2).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

from thesis_pilot import evalplus_published as P
from thesis_pilot.evalplus_study import ROOT, load_jsonl, write_once

RUN = ROOT / "results" / "thesis_evalplus_disagreement_v3"
PROTOCOL = ROOT / "docs" / "analysis" / "repguard_evalplus_disagreement_audit_protocol_2026-11-22.md"
PROTOCOL_SHA = "dd760db842df795aadd139fc85ec317b36463aa487dd243dd797e3dad743daa0"
SEED = 20261122
BUDGETS = (0.05, 0.10, 0.20)


def check_protocol():
    if hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() != PROTOCOL_SHA:
        raise SystemExit("v3 protocol changed after lock")


def docker_run(mode: str, files: dict, timeout: int):
    """Run disagree_runner.py in the v2 image (network none, read-only, limited)."""
    with tempfile.TemporaryDirectory() as td:
        inp = Path(td)
        for n, b in files.items():
            (inp / n).write_bytes(b if isinstance(b, bytes) else b.encode("utf-8"))
        shutil.copy(P.DOCKER_DIR / "disagree_runner.py", inp)
        proc = subprocess.run(["docker", "run", "--rm", "--network", "none", "--memory", "4g", "--cpus", "4",
                               "--pids-limit", "1024", "--read-only", "--tmpfs", "/tmp:rw,exec,size=1g",
                               "--ulimit", "core=0", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "-e", "PYTHONHASHSEED=0",
                               "--mount", f"type=bind,source={inp},target=/in,readonly",
                               "--entrypoint", "python", P.IMAGE, "/in/disagree_runner.py", mode],
                              check=True, stdout=subprocess.PIPE, text=True, encoding="utf-8", timeout=timeout)
    line = [l for l in proc.stdout.splitlines() if l.startswith("RESULT_JSON:")][-1]
    return json.loads(line[len("RESULT_JSON:"):])


# ------------------------------------------------------------------ stages --
CRASHED: list = []  # keys whose evaluator run crashed/hung even alone -> recorded as base/plus fail
BAD_TASKS = {"Mbpp/255", "Mbpp/267"}  # observed to hang/crash the evaluator in chunk01 (harness isolation only)


def docker_eval_to(subset_text: str, samples: list) -> list:
    timeout = 60 + int(0.4 * len(samples))  # normal run ~0.15 s/sample; a hung evaluator never recovers
    """Same container/limits as P.docker_eval (image already built) plus a wall timeout and a kill."""
    with tempfile.TemporaryDirectory() as td:
        inp = Path(td)
        (inp / "subset.jsonl").write_text(subset_text, encoding="utf-8")
        (inp / "samples.json").write_text(json.dumps(samples), encoding="utf-8")
        name = "v3eval" + hashlib.sha256(td.encode()).hexdigest()[:8]
        try:
            proc = subprocess.run(["docker", "run", "--rm", "--name", name, "--network", "none", "--memory", "4g", "--cpus", "4",
                                   "--pids-limit", "1024", "--read-only", "--tmpfs", "/tmp:rw,exec,size=1g",
                                   "--ulimit", "core=0", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                                   "--mount", f"type=bind,source={inp},target=/in,readonly", P.IMAGE],
                                  check=True, stdout=subprocess.PIPE, text=True, encoding="utf-8", timeout=timeout)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", name], capture_output=True)
            raise subprocess.CalledProcessError(124, "timeout")
    res = json.loads([l for l in proc.stdout.splitlines() if l.startswith("RESULT_JSON:")][-1][len("RESULT_JSON:"):])
    if not res["network_blocked"]:
        raise SystemExit("Container had network access")
    return res["results"]


def robust_eval(batch: list) -> list:
    """Evaluator crash/hang/OOM -> bisect samples; a single failing sample is recorded as fail (logged)."""
    bad = [s for s in batch if s["task_id"] in BAD_TASKS]
    if bad:  # tasks that crashed the evaluator before: not re-run (each crash dumps WSL cores); recorded as B=0
        good = [s for s in batch if s["task_id"] not in BAD_TASKS]
        CRASHED.extend(s["key"] for s in bad)
        return (robust_eval(good) if good else []) + [
            {"key": s["key"], "task_id": s["task_id"], "sanitized_sha256": None, "base_status": "fail",
             "plus_status": "fail", "n_base": -1, "n_plus": -1, "base_fail_count": -1, "plus_fail_count": -1,
             "harness_crash": True, "ran": False} for s in bad]
    try:
        r = docker_eval_to(P.subset(sorted({s["task_id"] for s in batch})), batch)
        assert len(r) == len(batch)
        return r
    except subprocess.CalledProcessError:
        if subprocess.run(["docker", "image", "inspect", P.IMAGE], capture_output=True).returncode:
            raise SystemExit("Docker unavailable: not treating as sample crash")
        if len(batch) == 1:
            s = batch[0]
            CRASHED.append(s["key"])
            BAD_TASKS.add(s["task_id"])
            return [{"key": s["key"], "task_id": s["task_id"], "sanitized_sha256": None, "base_status": "fail",
                     "plus_status": "fail", "n_base": -1, "n_plus": -1, "base_fail_count": -1, "plus_fail_count": -1,
                     "harness_crash": True, "ran": True}]
        h = len(batch) // 2
        return robust_eval(batch[:h]) + robust_eval(batch[h:])


def cmd_confirm():
    """Score B/F on the 346 confirmation tasks with the v2 evaluator (v2 gate refusal bypassed by design)."""
    check_protocol()
    path = RUN / "eval_confirmation.jsonl"
    if path.exists():
        raise SystemExit("Refusing to overwrite " + str(path))
    ids = set(P.stage_ids("confirmation"))
    allm = P.load_all()
    cache = RUN / "confirm_cache"  # chunked batches: one 7.6k-sample or per-model 346-task batch was OOM-killed (exit 137)
    cache.mkdir(exist_ok=True)
    samples = []  # (cache dir loop below)
    tl = sorted(ids)
    for i in range(0, len(tl), 40):  # 40-task chunks (v2 dev scale); all 22 models per chunk
        chunk = set(tl[i:i + 40])
        f = cache / f"chunk{i // 40:02d}.json"
        if not f.exists():
            batch = [{"key": f"{m}|{t}", "task_id": t, "raw": raw} for m in sorted(allm)
                     for t, raw in sorted(allm[m].items()) if t in chunk]
            f.write_text(json.dumps(robust_eval(batch)), encoding="utf-8")
            print(i, flush=True)
        samples += json.loads(f.read_text(encoding="utf-8"))
    res = {"results": samples}
    rows = []
    for r in sorted(res["results"], key=lambda r: r["key"]):
        b = int(r["base_status"] == "pass")
        rows.append({"model": r["key"].split("|")[0], **r, "B": b, "F": int(b and r["plus_status"] == "pass")})
    assert len(rows) == len(samples)
    # pre-outcome rule: tasks where the evaluator crashed/hung are excluded entirely (no fabricated labels)
    excl = {}
    for r in rows:
        if r.get("harness_crash"):
            e = excl.setdefault(r["task_id"], {"crashed_samples": 0, "skipped_not_run": 0})
            e["crashed_samples" if r["ran"] else "skipped_not_run"] += 1
    (RUN / "excluded_harness_crash_tasks.json").write_text(json.dumps(excl, indent=1))
    rows = [r for r in rows if r["task_id"] not in excl]
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print("excluded tasks", len(excl), "cells", len(rows), "B", sum(r["B"] for r in rows), "F", sum(r["F"] for r in rows))


def all_subset() -> str:
    return P.subset(sorted(P.mbpp_rows()))


def cmd_gen():
    check_protocol()
    pk = RUN / "mutated_inputs.pkl"
    if pk.exists():
        raise SystemExit("exists")
    res = docker_run("gen", {"subset.jsonl": all_subset()}, 3 * 3600)
    pk.write_bytes(base64.b64decode(res["pickle_b64"]))
    write_once(RUN / "mutated_counts.json", res["counts"])
    c = list(res["counts"].values())
    print("tasks", len(c), "min", min(c), "mean", sum(c) / len(c), "short", sum(x < 30 for x in c))


def load_evals():
    return {"dev": load_jsonl(P.RUN / "eval_development.jsonl"), "conf": load_jsonl(RUN / "eval_confirmation.jsonl")}


def cmd_exec():
    check_protocol()
    ev = load_evals()
    allm = P.load_all()
    cache = RUN / "exec_cache"
    cache.mkdir(exist_ok=True)
    pk = (RUN / "mutated_inputs.pkl").read_bytes()
    for m in sorted(allm):
        f = cache / f"{m}.json"
        if f.exists():
            continue
        b1 = sorted(r["task_id"] for s in ev.values() for r in s if r["model"] == m and r["B"])
        samples = [{"key": f"{m}|{t}", "task_id": t, "raw": allm[m][t]} for t in b1]
        res = docker_run("exec", {"subset.jsonl": all_subset(), "inputs.pkl": pk, "samples.json": json.dumps(samples)},
                         4 * 3600)
        f.write_text(json.dumps(res["results"]), encoding="utf-8")
        print(m, len(b1), flush=True)


# ------------------------------------------------------------------ scoring --
def tie_key(m: str, t: str) -> str:
    return hashlib.sha256(f"{m}|{t}".encode()).hexdigest()


def disagreement(outs: dict) -> dict:
    """outs: model -> outputs for ONE task (B=1 solutions only). d = fraction of inputs differing from plurality."""
    if len(outs) < 2:
        return {m: 0.0 for m in outs}
    n = len(next(iter(outs.values())))
    if n == 0:
        return {m: 0.0 for m in outs}
    plur = []
    for i in range(n):
        c = Counter(o[i] for o in outs.values())
        top = max(c.values())
        plur.append(min(k for k, v in c.items() if v == top))  # deterministic tie break
    return {m: sum(o[i] != plur[i] for i in range(n)) / n for m, o in outs.items()}


def budget_k(n: int, frac: float) -> int:
    return int(round(n * frac))


def caught(order, fp, k: int) -> int:
    return int(fp[order[:k]].sum())


def avg_precision(order, fp) -> float:
    hits = fp[order]
    ranks = np.nonzero(hits)[0] + 1
    return float((np.cumsum(hits)[hits == 1] / ranks).mean()) if len(ranks) else 0.0


def rank(score, keys) -> list:
    return sorted(range(len(keys)), key=lambda i: (-score[i], keys[i]))


def build_pool(models, evals, outs, lens):
    """Candidate cells (B=1) for dev and conf in this pool, with d, frac, features."""
    cells = {}
    for stage, rows in evals.items():
        rr = [r for r in rows if r["model"] in models]
        nb = Counter(r["task_id"] for r in rr if r["B"])
        by_task = {}
        for r in rr:
            if r["B"]:
                by_task.setdefault(r["task_id"], {})[r["model"]] = outs[(r["model"], r["task_id"])]
        d = {}
        for t, o in by_task.items():
            for m, v in disagreement(o).items():
                d[(m, t)] = v
        cells[stage] = [{"model": r["model"], "task": r["task_id"], "fp": int(r["F"] == 0), "d": d[(r["model"], r["task_id"])],
                         "frac": nb[r["task_id"]] / len(models), "n_base": r["n_base"],
                         "loglen": math.log(lens[(r["model"], r["task_id"])])} for r in rr if r["B"]]
    return cells


def features(cells, models, with_d):
    return np.array([[c["model"] == m for m in models] + [c["frac"], c["n_base"], c["loglen"]] + ([c["d"]] if with_d else [])
                     for c in cells], dtype=float)


def scorers(models, cal, tst):
    from sklearn.linear_model import LogisticRegression
    out = {}
    cnt = Counter(c["model"] for c in cal)
    fpc = Counter(c["model"] for c in cal if c["fp"])
    out["AgentRep"] = np.array([(fpc[c["model"]] + 1) / (cnt[c["model"]] + 2) for c in tst])  # P(F=0|B=1) Beta(1,1)
    ytr = np.array([c["fp"] for c in cal])
    for name, wd in (("ActionValue", False), ("Disagreement+AV", True)):
        lr = LogisticRegression(C=1.0, max_iter=1000).fit(features(cal, models, wd), ytr)
        out[name] = lr.predict_proba(features(tst, models, wd))[:, 1]  # class 1 = F=0 (false pass)
    out["Disagreement"] = np.array([c["d"] for c in tst])
    return out


def clustered_bootstrap(tst, orders, fp, frac, n_boot=2000):
    tasks = sorted({c["task"] for c in tst})
    tix = {t: i for i, t in enumerate(tasks)}
    cell_t = np.array([tix[c["task"]] for c in tst])
    rng = np.random.default_rng(SEED)
    diffs = []
    for _ in range(n_boot):
        mult = np.bincount(rng.integers(0, len(tasks), len(tasks)), minlength=len(tasks))
        w = mult[cell_t].astype(float)
        N, FP = w.sum(), (w * fp).sum()
        k = round(N * frac)
        res = {"Random": k * FP / N}
        for name, o in orders.items():
            ww = w[o]
            before = np.cumsum(ww) - ww
            res[name] = float((fp[o] * np.clip(k - before, 0, ww)).sum())
        diffs.append(res["Disagreement"] - max(res["Random"], res["AgentRep"], res["ActionValue"]))
    return [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]


def fp_concentration(tst):
    cnt = Counter()
    for c in tst:
        cnt[c["task"]] += c["fp"]
    v = sorted(cnt.values(), reverse=True)
    top = math.ceil(0.1 * len(v))
    x = np.sort(np.array(v, dtype=float))
    n = len(x)
    gini = float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum())) if x.sum() else 0.0
    return {"n_tasks": n, "top10pct_tasks": top, "share_fp_in_top10pct": sum(v[:top]) / sum(v) if sum(v) else None, "gini": gini}


def evaluate_pool(models, evals, outs, lens):
    cells = build_pool(models, evals, outs, lens)
    cal, tst = cells["dev"], cells["conf"]
    sc = scorers(models, cal, tst)
    keys = [tie_key(c["model"], c["task"]) for c in tst]
    fp = np.array([c["fp"] for c in tst])
    orders = {n: rank(s, keys) for n, s in sc.items()}
    N, FP = len(tst), int(fp.sum())
    res = {"models": models, "n_candidates": N, "FP": FP, "n_cal_candidates": len(cal), "cal_FP": sum(c["fp"] for c in cal),
           "budgets": {}, "AP": {"Random": FP / N if N else None, **{n: avg_precision(o, fp) for n, o in orders.items()}},
           "fp_concentration": fp_concentration(tst)}
    for f in BUDGETS:
        k = budget_k(N, f)
        res["budgets"][str(f)] = {"k": k, "Random": k * FP / N, **{n: caught(o, fp, k) for n, o in orders.items()}}
    b = res["budgets"]["0.1"]
    res["primary"] = {"diff": b["Disagreement"] - max(b["Random"], b["AgentRep"], b["ActionValue"]),
                      "ci95": clustered_bootstrap(tst, orders, fp, 0.10)}
    res["primary"]["success"] = res["primary"]["ci95"][0] > 0
    return res


def cmd_score():
    check_protocol()
    evals = load_evals()
    outs, lens = {}, {}
    for f in sorted((RUN / "exec_cache").glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            m, t = r["key"].split("|")
            outs[(m, t)], lens[(m, t)] = r["outs"], r["len"]
    counts = list(json.loads((RUN / "mutated_counts.json").read_text()).values())
    out = {"protocol_sha256": PROTOCOL_SHA,
           "excluded_harness_crash_tasks": json.loads((RUN / "excluded_harness_crash_tasks.json").read_text()),
           "confirmation_totals": {"cells": len(evals["conf"]), "B1": sum(r["B"] for r in evals["conf"]),
                                   "FP": sum(r["B"] and not r["F"] for r in evals["conf"])},
           "mutated_counts": {"min": min(counts), "n_tasks_below_30": sum(x < 30 for x in counts), "n_tasks": len(counts)},
           "pools": {"pool22": evaluate_pool(sorted({r["model"] for r in evals["conf"]}), evals, outs, lens),
                     "P7": evaluate_pool(P.POOLS["P7"], evals, outs, lens)}}
    write_once(RUN / "results.json", out)
    print(json.dumps(out, indent=1)[:6000])


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["confirm", "gen", "exec", "score"])
    a = p.parse_args(argv)
    {"confirm": cmd_confirm, "gen": cmd_gen, "exec": cmd_exec, "score": cmd_score}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
