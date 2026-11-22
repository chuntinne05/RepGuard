"""EvalPlus published-samples study v2 (protocol 2026-11-21).

    python -m thesis_pilot.evalplus_published download|preflight|gate
    python -m thesis_pilot.evalplus_published evaluate|replay --stage development|confirmation

Sample code is only read as text on the host; it executes solely inside
``docker run --network none`` (read-only mounts, memory/cpu limits).
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from thesis_pilot.evalplus_study import SRC, ROOT, load_jsonl, sha, wilson, write_once

RUN = ROOT / "results" / "thesis_evalplus_published_v2"
PROTOCOL = ROOT / "docs" / "analysis" / "repguard_evalplus_published_samples_protocol_2026-11-21.md"
PROTOCOL_SHA = "a4e38f55fe25b27b7dc7b4981c6c963e583fce454e155d3d8d3b7b194e2e3aa0"
DOCKER_DIR = ROOT / "thesis_pilot" / "evalplus_docker"
IMAGE = "repguard-evalplus:v2"
POOLS = {
    "P7": ["code-llama-7b", "deepseek-coder-6.7b-base", "mistral-7b", "codegen-6b"],
    "P15": ["code-llama-13b", "starcoder", "codegen-16b"],
}
STAGES = ("development", "confirmation")


def model_name(asset: str) -> str:
    return re.sub(r"_temp_0(\.0)?\.zip$", "", asset)


def zip_samples(path: Path) -> dict[str, str]:
    """task_id -> raw code, read from zip text only (never extracted)."""
    out = {}
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            m = re.fullmatch(r"[^/]+/Mbpp_(\d+)/0\.py", n)
            if m:
                out[f"Mbpp/{m.group(1)}"] = z.read(n).decode("utf-8")
    return out


def fractional_ks(n_tasks: int, n_models: int) -> list[int]:
    from thesis_pilot.evalplus_replay import fractional_ks as f
    return f(n_tasks, n_models)


def check_protocol() -> None:
    if sha(PROTOCOL.read_bytes()) != PROTOCOL_SHA:
        raise SystemExit("Protocol changed after lock")


def mbpp_rows() -> dict[str, str]:
    raw = gzip.decompress((SRC / "MbppPlus-v0.2.0.jsonl.gz").read_bytes()).decode()
    return {json.loads(l)["task_id"]: l for l in raw.splitlines() if l.strip()}


def dev_ids() -> list[str]:
    return json.loads((SRC / "inventory.json").read_text(encoding="utf-8"))["case_ids"]


def stage_ids(stage: str) -> list[str]:
    dev = set(dev_ids())
    return sorted(dev if stage == "development" else set(mbpp_rows()) - dev)


def subset(ids) -> str:
    rows = mbpp_rows()
    return "\n".join(rows[t] for t in ids) + "\n"


# ----------------------------------------------------------------- download --
def cmd_download(_):
    check_protocol()
    dl = RUN / "downloads"
    dl.mkdir(parents=True, exist_ok=True)
    names = subprocess.run(["gh", "api", "repos/evalplus/evalplus/releases/tags/v0.2.0", "--jq",
                            ".assets[].name"], capture_output=True, text=True, check=True).stdout.split()
    names = sorted(n for n in names if re.search(r"_temp_0(\.0)?\.zip$", n))
    if len(names) != 22:
        raise SystemExit(f"Expected 22 assets, got {len(names)}")
    for n in names:
        if not (dl / n).exists():
            subprocess.run(["gh", "release", "download", "v0.2.0", "-R", "evalplus/evalplus", "-p", n,
                            "-D", str(dl)], check=True)
    man = {"protocol_sha256": PROTOCOL_SHA, "release": "evalplus/evalplus v0.2.0",
           "assets": [{"asset": n, "model": model_name(n), "bytes": (dl / n).stat().st_size,
                       "sha256": sha((dl / n).read_bytes())} for n in names]}
    write_once(RUN / "download_manifest.json", man)
    print(len(names), "assets", sum(a["bytes"] for a in man["assets"]), "bytes")


def load_all() -> dict[str, dict[str, str]]:
    """model -> {task_id: raw}, verified against manifest; STOP on missing/corrupt pool zip."""
    man = json.loads((RUN / "download_manifest.json").read_text(encoding="utf-8"))
    pinned = set(mbpp_rows())
    out = {}
    for a in man["assets"]:
        p = RUN / "downloads" / a["asset"]
        if not p.exists() or sha(p.read_bytes()) != a["sha256"]:
            raise SystemExit(f"Missing/corrupt zip: {a['asset']}")
        out[a["model"]] = {t: c for t, c in zip_samples(p).items() if t in pinned}
    for pool in POOLS.values():
        for m in pool:
            if m not in out or not out[m]:
                raise SystemExit(f"Pool model missing: {m}")
    return out


# ------------------------------------------------------------------- docker --
def docker_eval(subset_text: str, samples: list[dict]) -> dict:
    """Run sample code only inside a network-less, read-only, resource-limited container."""
    with tempfile.TemporaryDirectory() as ctx:
        ctx = Path(ctx)
        shutil.copytree(SRC / "source" / "evalplus", ctx / "evalplus", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(DOCKER_DIR / "Dockerfile", ctx)
        shutil.copy(DOCKER_DIR / "runner.py", ctx)
        subprocess.run(["docker", "build", "-q", "-t", IMAGE, str(ctx)], check=True)
    with tempfile.TemporaryDirectory() as td:
        inp = Path(td)
        (inp / "subset.jsonl").write_text(subset_text, encoding="utf-8")
        (inp / "samples.json").write_text(json.dumps(samples), encoding="utf-8")
        proc = subprocess.run(["docker", "run", "--rm", "--network", "none", "--memory", "4g", "--cpus", "4",
                               "--pids-limit", "1024", "--read-only", "--tmpfs", "/tmp:rw,exec,size=1g",
                               "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                               "--mount", f"type=bind,source={inp},target=/in,readonly", IMAGE],
                              check=True, stdout=subprocess.PIPE, text=True, encoding="utf-8")
        line = [l for l in proc.stdout.splitlines() if l.startswith("RESULT_JSON:")][-1]
        res = json.loads(line[len("RESULT_JSON:"):])
    if not res["network_blocked"]:
        raise SystemExit("Container had network access")
    return res


# ---------------------------------------------------------------- preflight --
def cmd_preflight(_):
    check_protocol()
    ids = dev_ids()
    rows = {t: json.loads(l) for t, l in mbpp_rows().items() if t in set(ids)}
    sub = subset(ids)
    canon = [{"key": f"canon|{t}", "task_id": t, "solution": r["prompt"] + r["canonical_solution"]} for t, r in rows.items()]
    null = [{"key": f"null|{t}", "task_id": t,
             "solution": f"def {r['entry_point']}(*args, **kwargs):\n    return None\n"} for t, r in rows.items()]
    runs = []
    for name, batch in [("canonical_run1", canon), ("canonical_run2", canon), ("null_control", null)]:
        res = docker_eval(sub, batch)
        runs.append({"name": name, "network_blocked": res["network_blocked"], "dataset_hash": res["dataset_hash"],
                     "status": {r["task_id"]: [r["base_status"], r["plus_status"]] for r in res["results"]}})
        print(name, "done", flush=True)
    c1, c2, nc = (r["status"] for r in runs)
    checks = {
        "canonical_all_pass": sum(v == ["pass", "pass"] for v in c1.values()),
        "canonical_rerun_identical": sum(c1[t] == c2[t] for t in c1),
        "null_fails_base": sum(v[0] != "pass" for v in nc.values()),
        "network_blocked_all_runs": all(r["network_blocked"] for r in runs),
    }
    g0 = (checks["canonical_all_pass"] == 32 and checks["canonical_rerun_identical"] == 32
          and checks["null_fails_base"] == 32 and checks["network_blocked_all_runs"])
    write_once(RUN / "preflight.json", {"gate": "G0", "pass": g0, "checks": checks, "runs": runs,
                                        "protocol_sha256": PROTOCOL_SHA})
    print(json.dumps({"G0": g0, **checks}, indent=2))


# ----------------------------------------------------------------- evaluate --
def require_gate_passed() -> None:
    g = RUN / "gate_development.json"
    if not g.exists() or not json.loads(g.read_text(encoding="utf-8"))["pools"]["P7"]["PASS"]:
        raise SystemExit("Development gate missing or P7 not PASS: refused")


def cmd_evaluate(a):
    check_protocol()
    if not json.loads((RUN / "preflight.json").read_text(encoding="utf-8"))["pass"]:
        raise SystemExit("G0 failed")
    if a.stage == "confirmation":
        require_gate_passed()
    path = RUN / f"eval_{a.stage}.jsonl"
    if path.exists():
        raise SystemExit(f"Refusing to overwrite {path}")
    ids = set(stage_ids(a.stage))
    allm = load_all()
    samples = [{"key": f"{m}|{t}", "task_id": t, "raw": raw} for m in sorted(allm)
               for t, raw in sorted(allm[m].items()) if t in ids]
    res = docker_eval(subset(sorted(ids)), samples)
    rows = []
    for r in sorted(res["results"], key=lambda r: r["key"]):
        b = int(r["base_status"] == "pass")
        rows.append({"model": r["key"].split("|")[0], **r, "B": b, "F": int(b and r["plus_status"] == "pass")})
    assert len(rows) == len(samples)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(a.stage, "cells", len(rows), "B", sum(r["B"] for r in rows), "F", sum(r["F"] for r in rows))


def bank(stage: str) -> dict[tuple[str, str], tuple[int, int]]:
    return {(r["model"], r["task_id"]): (r["B"], r["F"]) for r in load_jsonl(RUN / f"eval_{stage}.jsonl")}


def pool_tids(bk, models) -> list[str]:
    return sorted(set.intersection(*[{t for (m, t) in bk if m == x} for x in models]))


# --------------------------------------------------------------------- gate --
def gate_pool(bk, models) -> dict:
    tids = pool_tids(bk, models)
    cells = [bk[(m, t)] for m in models for t in tids]
    nB = sum(b for b, _ in cells)
    FP = sum(b and not f for b, f in cells)
    fsum = {m: sum(bk[(m, t)][1] for t in tids) for m in models}
    best_model = max(models, key=fsum.get)
    oracle = sum(any(bk[(m, t)][1] for m in models) for t in tids)
    D = [t for t in tids if sum(bk[(m, t)][0] for m in models) >= 2
         and len({bk[(m, t)][1] for m in models if bk[(m, t)][0]}) == 2]
    g1 = {"FP": FP, "nB": nB, "FPR": round(FP / nB, 4) if nB else None, "FPR_wilson95": wilson(FP, nB),
          "pass": FP >= 8 and nB > 0 and FP / nB >= 0.10}
    g2 = {"oracle": oracle, "best_fixed": fsum[best_model], "best_model": best_model,
          "gap": oracle - fsum[best_model], "pass": oracle - fsum[best_model] >= 3}
    g3 = {"D": len(D), "tasks": D, "pass": len(D) >= 3}
    return {"models": models, "n_tasks": len(tids), "G1": g1, "G2": g2, "G3": g3,
            "PASS": all(g["pass"] for g in (g1, g2, g3))}


def cmd_gate(_):
    check_protocol()
    g0 = json.loads((RUN / "preflight.json").read_text(encoding="utf-8"))["pass"]
    bk = bank("development")
    pools = {}
    for name, ms in POOLS.items():
        pools[name] = gate_pool(bk, ms)
        pools[name]["PASS"] = bool(g0 and pools[name]["PASS"])
    per_model = {}
    for m in sorted({m for m, _ in bk}):
        cells = [v for (mm, _), v in bk.items() if mm == m]
        b, f = sum(x[0] for x in cells), sum(x[1] for x in cells)
        per_model[m] = {"n": len(cells), "B_rate": round(b / len(cells), 4), "F_rate": round(f / len(cells), 4),
                        "nB": b, "FP": b - f, "FPR": round((b - f) / b, 4) if b else None,
                        "FPR_wilson95": wilson(b - f, b)}
    out = {"stage": "development", "G0": g0, "pools": pools, "per_model": per_model}
    write_once(RUN / "gate_development.json", out)
    print(json.dumps({k: {x: v[x] for x in ("n_tasks", "G1", "G2", "G3", "PASS")} for k, v in pools.items()}, indent=2))


# ------------------------------------------------------------------- replay --
def cmd_replay(a):
    from thesis_pilot.evalplus_replay import run_replay

    check_protocol()
    require_gate_passed()
    bk = bank(a.stage)
    out = {}
    for name, ms in POOLS.items():
        tids = pool_tids(bk, ms)
        out[name] = run_replay({(m, t, 0): v for (m, t), v in bk.items() if m in ms}, ms, tids,
                               ks=fractional_ks(len(tids), len(ms)))
    write_once(RUN / f"replay_{a.stage}.json", out)
    print(json.dumps({k: v["summary"] for k, v in out.items()}, indent=2))


def main(argv=None):
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    for name in ["download", "preflight", "gate"]:
        sp.add_parser(name)
    for name in ["evaluate", "replay"]:
        sp.add_parser(name).add_argument("--stage", choices=STAGES, required=True)
    a = p.parse_args(argv)
    {"download": cmd_download, "preflight": cmd_preflight, "evaluate": cmd_evaluate, "gate": cmd_gate,
     "replay": cmd_replay}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
