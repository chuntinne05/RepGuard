"""ECRT-v2 item-reliability study (protocol 2026-11-22, frozen).

    python -m thesis_pilot.ecrt_v2_study dev                       # MBPP+ (development, descriptive)
    python -m thesis_pilot.ecrt_v2_study he-prepare|he-gen|he-eval|he-exec|he-score   # HumanEval+ (confirmation)
Model code runs only inside ``docker run --network none`` (see ``drun``).
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np

from repguard.reputation.audited import AuditedECRTReputation
from repguard.reputation.ecrt import ECRTReputation, FeedbackReliabilityEstimator
from repguard.reputation.ecrt_item import ECRTItemReputation, calibrate_q
from repguard.reputation.episode import EpisodeRecord
from thesis_pilot import evalplus_disagreement as D
from thesis_pilot import evalplus_published as P
from thesis_pilot.evalplus_study import ROOT, load_jsonl, sha, write_once

PROTOCOL = ROOT / "docs" / "analysis" / "repguard_ecrt_v2_item_reliability_protocol_2026-11-22.md"
PROTOCOL_SHA = "361dd67e6cce5bc372a437c66f56e6f89cbfb71284248c904146990ed5249ded"
OUT = ROOT / "results" / "thesis_ecrt_v2"
HE = OUT / "confirm_humaneval"
HE_VERSION = "v0.1.10"
HE_SEED = 20261122  # mutation seed (v3)
SEED = 20261123  # task order, audit, bootstrap
METHODS = ["Random", "SingleBest", "RawRep", "ECRT", "AuditedECRT", "MBR-exec", "ECRT-v2", "ECRT-v2-noaudit", "Oracle"]
BASELINES = ["SingleBest", "RawRep", "ECRT", "AuditedECRT", "MBR-exec"]
CHEATERS = ["hardcode-1", "hardcode-2"]


def check_protocol():
    if hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() != PROTOCOL_SHA:
        raise SystemExit("ECRT-v2 protocol changed after lock")


# ------------------------------------------------------------------ simulation --
def simulate(models, BF, outs, plus_in_base, domain, tasks, scenario_s2=False):
    """BF[(m,t)] = (B,F); outs[(m,t)] = outputs of B=1 cells; returns result dict for one scenario."""
    models = list(models)
    if scenario_s2:  # synthetic test-gaming agents: pass base tests, wrong on plus inputs, None elsewhere
        for c in CHEATERS:
            for t in tasks:
                BF[(c, t)] = (1, int(plus_in_base[t]))
                n = len(next((outs[(m, t)] for m in models if (m, t) in outs), []))
                outs[(c, t)] = ["None"] * n
        models += CHEATERS
    d = {}
    for t in tasks:
        for m, v in D.disagreement({m: outs[(m, t)] for m in models if BF[(m, t)][0] and (m, t) in outs}).items():
            d[(m, t)] = v
    order = [tasks[i] for i in np.random.default_rng(SEED).permutation(len(tasks))]
    ncal = int(0.2 * len(order))
    cal_t, ev_t = order[:ncal], order[ncal:]

    def ep(m, t, gold, with_d=True, audited=False):
        B, F = BF[(m, t)]
        md = {"d": d[(m, t)]} if with_d and (m, t) in d else {}
        if audited:
            md["audited"] = True
        return EpisodeRecord(f"{m}|{t}", m, t, domain, "1", ("1" if F else "0") if gold else "", float(B), metadata=md)

    cal_eps = [ep(m, t, True) for t in cal_t for m in models]
    params = FeedbackReliabilityEstimator().calibrate(cal_eps)
    cal_b1 = [(m, t) for t in cal_t for m in models if BF[(m, t)][0]]
    q = calibrate_q([(d[c], bool(BF[c][1])) for c in cal_b1])
    thr = float(np.percentile([d[c] for c in cal_b1], 90))
    fcal = {m: sum(BF[(m, t)][1] for t in cal_t) for m in models}
    best_rank = sorted(models, key=lambda m: (-fcal[m], D.tie_key(m, "")))

    reps = {"RawRep": ECRTReputation(mode="no_reliability"),
            "ECRT": ECRTReputation(reliability_params=params, mode="no_transfer"),
            "ECRT-v2": ECRTItemReputation(q, params), "ECRT-v2-noaudit": ECRTItemReputation(q, params)}
    hist = {k: list(cal_eps) for k in reps}
    a_hist, a_audit = [], list(cal_eps)  # cal cells are gold audits for AuditedECRT
    audited_rep = AuditedECRTReputation()
    rng = np.random.default_rng(SEED)
    acc = {k: [] for k in METHODS}
    n_b1 = n_v2_aud = n_rand_aud = 0

    def pick(cands, t, score):
        return min(cands, key=lambda m: (-score(m), D.tie_key(m, t)))

    for t in ev_t:
        b1 = [m for m in models if BF[(m, t)][0]]
        cands = b1 or models
        F = lambda m: BF[(m, t)][1]
        acc["Random"].append(sum(F(m) for m in cands) / len(cands))
        acc["SingleBest"].append(F(next(m for m in best_rank if m in cands)))
        acc["MBR-exec"].append(F(pick(cands, t, lambda m: -d.get((m, t), 0.0))))
        acc["Oracle"].append(int(any(F(m) for m in models)))
        for k in ("RawRep", "ECRT"):
            reps[k].fit(hist[k])
            acc[k].append(F(pick(cands, t, lambda m, k=k: reps[k].score(m, domain).lower_bound)))
        audited_rep.fit(a_hist, a_audit)
        acc["AuditedECRT"].append(F(pick(cands, t, lambda m: audited_rep.score(m, domain).lower_bound)))
        for k in ("ECRT-v2", "ECRT-v2-noaudit"):
            reps[k].fit(hist[k])
            acc[k].append(F(pick(cands, t, lambda m, k=k: reps[k].score(m, domain).lower_bound
                                 * (reps[k].q(d[(m, t)]) if (m, t) in d else 1.0))))
        for m in models:  # decision done: cells of t enter history
            b = BF[(m, t)][0]
            hist["RawRep"].append(ep(m, t, False, with_d=False))
            hist["ECRT"].append(ep(m, t, False, with_d=False))
            hist["ECRT-v2-noaudit"].append(ep(m, t, False))
            v2_aud = bool(b) and d[(m, t)] >= thr
            rand_aud = bool(b) and rng.random() < 0.10
            n_b1 += b
            n_v2_aud += v2_aud
            n_rand_aud += rand_aud
            hist["ECRT-v2"].append(ep(m, t, v2_aud, audited=v2_aud))
            (a_audit if rand_aud else a_hist).append(ep(m, t, rand_aud, with_d=False))
    X = np.array([acc[k] for k in METHODS], dtype=float).T  # tasks x methods
    ix = {k: i for i, k in enumerate(METHODS)}
    idx = np.random.default_rng(SEED).integers(0, len(ev_t), (2000, len(ev_t)))
    boot = np.stack([X[i].mean(0) for i in idx])

    def cmp(a, bs):
        f = lambda m: m[:, ix[a]] - (np.max(m[:, [ix[x] for x in bs]], axis=1))
        diff, bd = float(f(X.mean(0, keepdims=True))[0]), f(boot)
        ci = [float(np.percentile(bd, 2.5)), float(np.percentile(bd, 97.5))]
        return {"diff": diff, "ci95": ci, "success": ci[0] > 0}
    means = X.mean(0)
    return {"n_tasks": len(tasks), "n_cal": len(cal_t), "n_eval": len(ev_t), "models": models,
            "accuracy": {k: float(means[ix[k]]) for k in METHODS},
            "primary_vs_max_baselines": cmp("ECRT-v2", BASELINES),
            "secondary": {"v2_vs_ECRT": cmp("ECRT-v2", ["ECRT"]), "v2_vs_noaudit": cmp("ECRT-v2", ["ECRT-v2-noaudit"]),
                          "v2_vs_MBR": cmp("ECRT-v2", ["MBR-exec"])},
            "audits": {"eval_B1_cells": int(n_b1), "ECRT-v2_by_d": int(n_v2_aud), "AuditedECRT_random": int(n_rand_aud),
                       "d_threshold_p90_cal": thr},
            "calibration": {"sens": params.sensitivity, "spec": params.specificity, "prior": params.p_correct_prior,
                            "q_by_bin": q, "single_best": best_rank[0], "n_cal_B1_cells": len(cal_b1)},
            "curve_S3": {str(n): {k: float(X[:n, ix[k]].mean()) for k in METHODS} for n in (20, 50, 100) if n <= len(ev_t)}}


def run_scenarios(models, BF, outs, plus_in_base, domain, tasks):
    return {"S1": simulate(models, dict(BF), dict(outs), plus_in_base, domain, tasks),
            "S2": simulate(models, dict(BF), dict(outs), plus_in_base, domain, tasks, scenario_s2=True)}


def plus_subset_flags(rows):
    """task -> True iff plus inputs are all among base inputs (then hardcoding is genuinely correct)."""
    return {t: all(x in r["base_input"] for x in r["plus_input"]) for t, r in rows.items()}


# ------------------------------------------------------------------------- dev --
def cmd_dev():
    check_protocol()
    ev = load_jsonl(D.RUN / "eval_confirmation.jsonl")
    outs = {}
    for f in sorted((D.RUN / "exec_cache").glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            m, t = r["key"].split("|")
            outs[(m, t)] = r["outs"]
    BF = {(r["model"], r["task_id"]): (r["B"], r["F"]) for r in ev}
    tasks = sorted({t for _, t in BF})
    models = sorted({m for m, _ in BF})
    assert len(tasks) == 339 and len(models) == 22
    rows = {t: json.loads(l) for t, l in P.mbpp_rows().items() if t in set(tasks)}
    res = {"protocol_sha256": PROTOCOL_SHA, "dataset": "MBPP+ v0.2.0 (development, descriptive only)",
           **run_scenarios(models, BF, outs, plus_subset_flags(rows), "mbpp", tasks)}
    (OUT / "dev_mbpp").mkdir(parents=True, exist_ok=True)
    write_once(OUT / "dev_mbpp" / "results.json", res)
    print(json.dumps({s: {"acc": res[s]["accuracy"], "primary": res[s]["primary_vs_max_baselines"]} for s in ("S1", "S2")}, indent=1))


# ------------------------------------------------------------- HumanEval+ side --
def he_rows():
    raw = gzip.decompress((HE / "downloads" / "HumanEvalPlus.jsonl.gz").read_bytes()).decode()
    return {json.loads(l)["task_id"]: l for l in raw.splitlines() if l.strip()}


def he_subset(ids):
    r = he_rows()
    return "\n".join(r[t] for t in ids) + "\n"


def he_zip(path):
    out = {}
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            m = re.fullmatch(r"(?:.*/)?HumanEval_(\d+)/0\.py", n)
            if m:
                out[f"HumanEval/{m.group(1)}"] = z.read(n).decode("utf-8")
    return out


def he_manifest():
    return json.loads((HE / "download_manifest.json").read_text(encoding="utf-8"))


def he_load_all():
    out = {}
    for a in he_manifest()["assets"]:
        p = HE / "downloads" / a["asset"]
        if sha(p.read_bytes()) != a["sha256"]:
            raise SystemExit("corrupt " + a["asset"])
        out[a["model"]] = he_zip(p)
    return out


def cmd_he_prepare():
    check_protocol()
    dl = HE / "downloads"
    zs = sorted(dl.glob("*_temp_0.0.zip"))
    man = {"protocol_sha256": PROTOCOL_SHA, "samples_release": "evalplus/evalplus v0.1.0 (greedy temp 0.0 zips)",
           "dataset": f"evalplus/humanevalplus_release {HE_VERSION} HumanEvalPlus.jsonl.gz",
           "dataset_sha256": sha((dl / "HumanEvalPlus.jsonl.gz").read_bytes()),
           "not_used": {"wizardcoder-34b.jsonl": "different (jsonl) format, not a zip sample tree; excluded for uniform pipeline",
                        "gpt-3.5-turbo/deepseek-coder*/wizardcoder-7b,15b/zephyr-7b": "no published HumanEval greedy samples in v0.1.0",
                        "chatgpt_temp_0.0.zip": "different model name than v3's gpt-3.5-turbo; not substituted"},
           "assets": [{"asset": z.name, "model": P.model_name(z.name), "bytes": z.stat().st_size, "sha256": sha(z.read_bytes())} for z in zs]}
    write_once(HE / "download_manifest.json", man)
    allm = he_load_all()
    print(len(allm), "models", {m: len(v) for m, v in allm.items()}, len(he_rows()), "tasks")


def free_gb():
    return shutil.disk_usage("C:\\").free / 2**30


def drun(files, args, timeout, name, env=()):
    """Mandatory-flag sandbox for every model-code execution."""
    if free_gb() < 3:
        raise SystemExit(f"C: free space {free_gb():.1f} GB < 3 GB: stopping")
    with tempfile.TemporaryDirectory() as td:
        inp = Path(td)
        for n, b in files.items():
            (inp / n).write_bytes(b if isinstance(b, bytes) else b.encode("utf-8"))
        for r in ("runner.py", "disagree_runner.py"):
            shutil.copy(P.DOCKER_DIR / r, inp)
        cmd = ["docker", "run", "--rm", "--name", name, "--network", "none", "--memory", "4g", "--cpus", "4",
               "--pids-limit", "1024", "--read-only", "--tmpfs", "/tmp:rw,exec,size=1g", "--ulimit", "core=0",
               "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "-e", "PYTHONHASHSEED=0",
               "-e", "EP_DATASET=humaneval", *env, "--mount", f"type=bind,source={inp},target=/in,readonly",
               "--entrypoint", "python", P.IMAGE, *args]
        try:
            proc = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, text=True, encoding="utf-8", timeout=timeout)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", name], capture_output=True)
            raise subprocess.CalledProcessError(124, "timeout")
    return json.loads([l for l in proc.stdout.splitlines() if l.startswith("RESULT_JSON:")][-1][len("RESULT_JSON:"):])


def cmd_he_gen():
    check_protocol()
    pk = HE / "mutated_inputs.pkl"
    if pk.exists():
        raise SystemExit("exists")
    res = drun({"subset.jsonl": he_subset(sorted(he_rows()))}, ["/in/disagree_runner.py", "gen"], 3 * 3600, "ecrtv2gen")
    pk.write_bytes(base64.b64decode(res["pickle_b64"]))
    write_once(HE / "mutated_counts.json", res["counts"])
    c = list(res["counts"].values())
    print("tasks", len(c), "min", min(c), "short", sum(x < 30 for x in c))


BAD: set = set()


def he_robust(batch, sub_ids=None):
    """Chunk eval; crash/hang -> bisect samples; a lone failing sample marks its task bad (excluded entirely)."""
    batch = [s for s in batch if s["task_id"] not in BAD]
    if not batch:
        return []
    try:
        ids = sorted({s["task_id"] for s in batch})
        res = drun({"subset.jsonl": he_subset(ids), "samples.json": json.dumps(batch)}, ["/in/runner.py"],
                   120 + int(0.5 * len(batch)), "ecrtv2eval" + hashlib.sha256(str(ids).encode()).hexdigest()[:6])
        if not res["network_blocked"]:
            raise SystemExit("network access in container")
        assert len(res["results"]) == len(batch)
        return res["results"]
    except subprocess.CalledProcessError:
        if subprocess.run(["docker", "image", "inspect", P.IMAGE], capture_output=True).returncode:
            raise SystemExit("Docker unavailable")
        if len(batch) == 1:
            BAD.add(batch[0]["task_id"])
            print("CRASH", batch[0]["key"], flush=True)
            return []
        h = len(batch) // 2
        return he_robust(batch[:h]) + he_robust(batch[h:])


def cmd_he_eval():
    check_protocol()
    path = HE / "eval.jsonl"
    if path.exists():
        raise SystemExit("exists")
    allm = he_load_all()
    cache = HE / "eval_cache"
    cache.mkdir(exist_ok=True)
    tl = sorted(he_rows(), key=lambda t: int(t.split("/")[1]))
    rows = []
    for i in range(0, len(tl), 20):
        chunk = set(tl[i:i + 20])
        f = cache / f"chunk{i // 20:02d}.json"
        if not f.exists():
            batch = [{"key": f"{m}|{t}", "task_id": t, "raw": raw} for m in sorted(allm) for t, raw in sorted(allm[m].items()) if t in chunk]
            f.write_text(json.dumps({"res": he_robust(batch), "bad": sorted(BAD & chunk)}), encoding="utf-8")
            print(i, f"free {free_gb():.1f} GB", flush=True)
        c = json.loads(f.read_text(encoding="utf-8"))
        BAD.update(c["bad"])
        rows += c["res"]
    out = []
    for r in sorted(rows, key=lambda r: r["key"]):
        b = int(r["base_status"] == "pass")
        out.append({"model": r["key"].split("|")[0], **r, "B": b, "F": int(b and r["plus_status"] == "pass")})
    out = [r for r in out if r["task_id"] not in BAD]  # crashed tasks excluded entirely (v3 rule)
    write_once(HE / "excluded_harness_crash_tasks.json", sorted(BAD))
    path.write_text("".join(json.dumps(r) + "\n" for r in out), encoding="utf-8")
    print("excluded", sorted(BAD), "cells", len(out), "B", sum(r["B"] for r in out), "F", sum(r["F"] for r in out))


def cmd_he_exec():
    check_protocol()
    ev = load_jsonl(HE / "eval.jsonl")
    allm = he_load_all()
    cache = HE / "exec_cache"
    cache.mkdir(exist_ok=True)
    pk = (HE / "mutated_inputs.pkl").read_bytes()
    allt = sorted(he_rows())
    for m in sorted(allm):
        f = cache / f"{m}.json"
        if f.exists():
            continue
        b1 = sorted(r["task_id"] for r in ev if r["model"] == m and r["B"])
        samples = [{"key": f"{m}|{t}", "task_id": t, "raw": allm[m][t]} for t in b1]
        res = drun({"subset.jsonl": he_subset(allt), "inputs.pkl": pk, "samples.json": json.dumps(samples)},
                   ["/in/disagree_runner.py", "exec"], 4 * 3600, "ecrtv2exec")
        f.write_text(json.dumps(res["results"]), encoding="utf-8")
        print(m, len(b1), f"free {free_gb():.1f} GB", flush=True)


def cmd_he_score():
    check_protocol()
    ev = load_jsonl(HE / "eval.jsonl")
    outs = {}
    for f in sorted((HE / "exec_cache").glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            m, t = r["key"].split("|")
            outs[(m, t)] = r["outs"]
    BF = {(r["model"], r["task_id"]): (r["B"], r["F"]) for r in ev}
    tasks = sorted({t for _, t in BF})
    models = sorted({m for m, _ in BF})
    assert all((m, t) in outs for (m, t), (b, _) in BF.items() if b), "missing exec outputs"
    rows = {t: json.loads(l) for t, l in he_rows().items() if t in set(tasks)}
    res = {"protocol_sha256": PROTOCOL_SHA, "dataset": f"HumanEval+ {HE_VERSION}", "models": models, "n_models": len(models),
           "excluded_harness_crash_tasks": json.loads((HE / "excluded_harness_crash_tasks.json").read_text()),
           "totals": {"cells": len(ev), "B1": sum(r["B"] for r in ev), "FP": sum(r["B"] and not r["F"] for r in ev)},
           **run_scenarios(models, BF, outs, plus_subset_flags(rows), "humaneval", tasks)}
    write_once(HE / "results.json", res)
    print(json.dumps({s: {"acc": res[s]["accuracy"], "primary": res[s]["primary_vs_max_baselines"]} for s in ("S1", "S2")}, indent=1))


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["dev", "he-prepare", "he-gen", "he-eval", "he-exec", "he-score"])
    a = p.parse_args(argv)
    {"dev": cmd_dev, "he-prepare": cmd_he_prepare, "he-gen": cmd_he_gen, "he-eval": cmd_he_eval,
     "he-exec": cmd_he_exec, "he-score": cmd_he_score}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
