"""EvalPlus partial-feedback pilot v1 — driver (protocol 2026-11-09).

Subcommands (run from repo root with the Python that has ``modal`` installed):

    python -m thesis_pilot.evalplus_study manifest   # freeze protocol/inputs/models
    python -m thesis_pilot.evalplus_study preflight  # G0, Modal CPU, no model call
    python -m thesis_pilot.evalplus_study generate --stage greedy|sampled   # local Ollama
    python -m thesis_pilot.evalplus_study evaluate --stage greedy|sampled   # Modal CPU
    python -m thesis_pilot.evalplus_study gate       # G1-G3 on greedy bank, no inference
    python -m thesis_pilot.evalplus_study replay     # step 3, only if gate PASS

Generation never executes code. Evaluation executes code only in Modal with
``block_network=True``. Response files are append-only; a completed response is
never regenerated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "thesis_evalplus_source_v1"
RUN = ROOT / "results" / "thesis_evalplus_pilot_v1"
PROTOCOL = ROOT / "docs" / "analysis" / "repguard_evalplus_partial_feedback_protocol_2026-11-09.md"
OLLAMA = "http://127.0.0.1:11434"

MODELS = [
    "qwen3:8b",
    "gemma2:latest",
    "llama3:8b",
    "qwen3:0.6b",
    "qwen3:4b-instruct-2507-q4_K_M",
]
INSTRUCTION = ("Please provide a self-contained Python script that solves the following "
               "problem in a markdown code block:")
STAGES = {
    "greedy": [(0, 0.0, 0)],
    "sampled": [(i, 0.8, i) for i in range(1, 5)],
}
NUM_PREDICT = 1024


def sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode() if isinstance(b, str) else b).hexdigest()


def write_once(path: Path, value) -> None:
    data = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != data:
            raise SystemExit(f"Refusing to change frozen artifact {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def tasks() -> list[dict]:
    return json.loads((SRC / "public_development_inventory.json").read_text(encoding="utf-8"))


def subset_jsonl() -> str:
    """Official MBPP+ rows for the 32 selected tasks, in original serialized form."""
    import gzip

    ids = {t["task_id"] for t in tasks()}
    raw = gzip.decompress((SRC / "MbppPlus-v0.2.0.jsonl.gz").read_bytes()).decode()
    keep = [l for l in raw.splitlines() if l.strip() and json.loads(l)["task_id"] in ids]
    assert len(keep) == 32
    return "\n".join(keep) + "\n"


def prompt_for(task: dict) -> str:
    return f"{INSTRUCTION}\n```\n{task['prompt'].strip()}\n```\n"


def ollama(path: str, payload: dict | None = None, timeout: int = 600) -> dict:
    req = urllib.request.Request(OLLAMA + path, data=None if payload is None else json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def model_info() -> dict:
    tags = {m["name"]: m for m in ollama("/api/tags")["models"]}
    info = {}
    for m in MODELS:
        show = ollama("/api/show", {"model": m})
        info[m] = {"digest": tags[m]["digest"], "parameter_size": tags[m]["details"]["parameter_size"],
                   "quantization": tags[m]["details"]["quantization_level"],
                   "thinking_capable": "thinking" in show.get("capabilities", [])}
    return info


# ----------------------------------------------------------------- manifest --
def cmd_manifest(_):
    inv = json.loads((SRC / "inventory.json").read_text(encoding="utf-8"))
    sub = subset_jsonl()
    manifest = {
        "run": "thesis_evalplus_pilot_v1",
        "protocol_path": str(PROTOCOL.relative_to(ROOT)).replace("\\", "/"),
        "protocol_sha256": sha(PROTOCOL.read_bytes()),
        "evalplus_revision": inv["revision"],
        "mbppplus_sha256": inv["source_files"]["MbppPlus-v0.2.0.jsonl.gz"]["sha256"],
        "public_inventory_sha256": sha((SRC / "public_development_inventory.json").read_bytes()),
        "subset_sha256": sha(sub),
        "task_ids": [t["task_id"] for t in tasks()],
        "models": model_info(),
        "instruction_prefix": INSTRUCTION,
        "prompt_sha256": {t["task_id"]: sha(prompt_for(t)) for t in tasks()},
        "stages": {k: [{"sample_idx": i, "temperature": T, "seed": s} for i, T, s in v] for k, v in STAGES.items()},
        "num_predict": NUM_PREDICT,
        "generation_host": "local Ollama (RTX 4050 Laptop 6GB); generation only, no code execution",
        "evaluation_host": "Modal CPU, block_network=True, official EvalPlus evaluate()",
    }
    write_once(RUN / "manifest.json", manifest)
    print(json.dumps({k: manifest[k] for k in ["protocol_sha256", "subset_sha256", "models"]}, indent=2))


def check_manifest() -> dict:
    m = json.loads((RUN / "manifest.json").read_text(encoding="utf-8"))
    if sha(PROTOCOL.read_bytes()) != m["protocol_sha256"]:
        raise SystemExit("Protocol changed after freeze")
    if sha(subset_jsonl()) != m["subset_sha256"]:
        raise SystemExit("Subset changed after freeze")
    return m


# ---------------------------------------------------------------- preflight --
def run_modal(samples: list[dict]) -> dict:
    from thesis_pilot.evalplus_eval_app import app, evaluate_batch

    with app.run():
        return evaluate_batch.remote(subset_jsonl(), samples)


def cmd_preflight(_):
    check_manifest()
    rows = {json.loads(l)["task_id"]: json.loads(l) for l in subset_jsonl().splitlines() if l.strip()}
    canon = [{"key": f"canon|{t}", "task_id": t, "solution": r["prompt"] + r["canonical_solution"]} for t, r in rows.items()]
    null = [{"key": f"null|{t}", "task_id": t,
             "solution": f"def {r['entry_point']}(*args, **kwargs):\n    return None\n"} for t, r in rows.items()]
    runs = []
    for name, batch in [("canonical_run1", canon), ("canonical_run2", canon), ("null_control", null)]:
        t0 = time.time()
        res = run_modal(batch)
        runs.append({"name": name, "seconds": round(time.time() - t0, 1), "network_blocked": res["network_blocked"],
                     "dataset_hash": res["dataset_hash"],
                     "status": {r["task_id"]: [r["base_status"], r["plus_status"]] for r in res["results"]}})
        print(name, "done", runs[-1]["seconds"], "s")
    c1, c2, nc = (r["status"] for r in runs)
    checks = {
        "canonical_all_pass": sum(v == ["pass", "pass"] for v in c1.values()),
        "canonical_rerun_identical": sum(c1[t] == c2[t] for t in c1),
        "null_fails_base": sum(v[0] != "pass" for v in nc.values()),
        "network_blocked_all_runs": all(r["network_blocked"] for r in runs),
    }
    g0 = (checks["canonical_all_pass"] == 32 and checks["canonical_rerun_identical"] == 32
          and checks["null_fails_base"] == 32 and checks["network_blocked_all_runs"])
    out = {"gate": "G0", "pass": g0, "checks": checks, "runs": runs,
           "failures": {t: v for t, v in c1.items() if v != ["pass", "pass"]},
           "null_passing_base": [t for t, v in nc.items() if v[0] == "pass"],
           "model_calls": 0}
    write_once(RUN / "preflight.json", out)
    print(json.dumps({"G0": g0, **checks}, indent=2))


# ----------------------------------------------------------------- generate --
def cmd_generate(a):
    m = check_manifest()
    if not json.loads((RUN / "preflight.json").read_text())["pass"]:
        raise SystemExit("G0 failed: no generation")
    if a.stage == "sampled":
        gate = RUN / "gate.json"
        if not gate.exists():
            raise SystemExit("Run greedy gate first")
    path = RUN / f"responses_{a.stage}.jsonl"
    done = {r["key"] for r in load_jsonl(path)}
    info = model_info()
    for mod in MODELS:
        if info[mod]["digest"] != m["models"][mod]["digest"]:
            raise SystemExit(f"Model digest changed: {mod}")
    todo = [(mod, t, i, T, s) for mod in MODELS for t in tasks() for i, T, s in STAGES[a.stage]
            if f"{a.stage}|{mod}|{t['task_id']}|{i}" not in done]
    print(f"{len(done)} done, {len(todo)} to do", flush=True)
    with path.open("a", encoding="utf-8") as f:
        for n, (mod, t, i, T, s) in enumerate(todo, 1):
            key = f"{a.stage}|{mod}|{t['task_id']}|{i}"
            payload = {"model": mod, "stream": False,
                       "messages": [{"role": "user", "content": prompt_for(t)}],
                       "options": {"temperature": T, "seed": s, "num_predict": NUM_PREDICT}}
            if info[mod]["thinking_capable"]:
                payload["think"] = False
            r, err, attempts = None, None, 0
            for attempts in (1, 2):
                try:
                    r = ollama("/api/chat", payload, timeout=900)
                    break
                except Exception as e:  # transport failure only
                    err = repr(e)
                    time.sleep(5)
            if r is None:
                print("TRANSPORT FAIL", key, err, flush=True)
                continue
            rec = {"key": key, "stage": a.stage, "model": mod, "model_digest": info[mod]["digest"],
                   "task_id": t["task_id"], "sample_idx": i, "temperature": T, "seed": s,
                   "think": payload.get("think"), "prompt_sha256": sha(prompt_for(t)),
                   "content": r["message"]["content"], "content_sha256": sha(r["message"]["content"]),
                   "thinking_present": bool(r["message"].get("thinking")),
                   "done_reason": r.get("done_reason"), "eval_count": r.get("eval_count"),
                   "prompt_eval_count": r.get("prompt_eval_count"),
                   "total_duration_s": round(r.get("total_duration", 0) / 1e9, 3), "attempts": attempts,
                   "created": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if n % 10 == 0 or n == len(todo):
                print(f"[{n}/{len(todo)}] {key} {rec['eval_count']} tok {rec['total_duration_s']}s {rec['done_reason']}",
                      flush=True)


# ----------------------------------------------------------------- evaluate --
def cmd_evaluate(a):
    check_manifest()
    resp = load_jsonl(RUN / f"responses_{a.stage}.jsonl")
    expected = len(MODELS) * 32 * len(STAGES[a.stage])
    if len(resp) != expected or len({r["key"] for r in resp}) != expected:
        raise SystemExit(f"Incomplete stage: {len(resp)}/{expected}")
    for r in resp:
        assert sha(r["content"]) == r["content_sha256"]
    t0 = time.time()
    res = run_modal([{"key": r["key"], "task_id": r["task_id"], "raw": r["content"]} for r in resp])
    out = {"stage": a.stage, "seconds": round(time.time() - t0, 1), "network_blocked": res["network_blocked"],
           "dataset_hash": res["dataset_hash"], "responses_sha256": sha((RUN / f"responses_{a.stage}.jsonl").read_bytes()),
           "results": sorted(res["results"], key=lambda r: r["key"])}
    assert out["network_blocked"] and len(out["results"]) == expected
    write_once(RUN / f"eval_{a.stage}.json", out)
    B = sum(r["base_status"] == "pass" for r in out["results"])
    F = sum(r["plus_status"] == "pass" and r["base_status"] == "pass" for r in out["results"])
    print(json.dumps({"stage": a.stage, "n": expected, "B": B, "F": F, "seconds": out["seconds"]}))


# --------------------------------------------------------------------- bank --
def bank(stage: str) -> dict[tuple[str, str, int], tuple[int, int]]:
    ev = json.loads((RUN / f"eval_{stage}.json").read_text(encoding="utf-8"))
    out = {}
    for r in ev["results"]:
        _, mod, tid, i = r["key"].split("|")
        b = int(r["base_status"] == "pass")
        f = int(b and r["plus_status"] == "pass")
        out[(mod, tid, int(i))] = (b, f)
    return out


def wilson(k: int, n: int, z: float = 1.959964) -> list[float]:
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return [round(c - h, 4), round(c + h, 4)]


def cmd_gate(_):
    check_manifest()
    bk = bank("greedy")
    tids = [t["task_id"] for t in tasks()]
    nB = sum(b for b, _ in bk.values())
    FP = sum(b and not f for b, f in bk.values())
    per_model = {}
    for m in MODELS:
        cells = [bk[(m, t, 0)] for t in tids]
        b = sum(x[0] for x in cells)
        f = sum(x[1] for x in cells)
        per_model[m] = {"B": b, "F": f, "FP": b - f, "FPR": round((b - f) / b, 4) if b else None,
                        "FPR_wilson95": wilson(b - f, b)}
    oracle = sum(any(bk[(m, t, 0)][1] for m in MODELS) for t in tids)
    best_model = max(MODELS, key=lambda m: per_model[m]["F"])
    best = per_model[best_model]["F"]
    D_tasks = []
    for t in tids:
        passB = [m for m in MODELS if bk[(m, t, 0)][0]]
        if len(passB) >= 2 and len({bk[(m, t, 0)][1] for m in passB}) == 2:
            D_tasks.append(t)
    fp_tasks = sorted({t for (m, t, _), (b, f) in bk.items() if b and not f})
    g = {
        "G1": {"FP": FP, "nB": nB, "FPR": round(FP / nB, 4) if nB else None, "FPR_wilson95": wilson(FP, nB),
               "fp_tasks": fp_tasks, "pass": FP >= 8 and nB > 0 and FP / nB >= 0.10},
        "G2": {"oracle": oracle, "best_fixed": best, "best_model": best_model, "gap": oracle - best,
               "pass": oracle - best >= 3},
        "G3": {"D": len(D_tasks), "tasks": D_tasks, "pass": len(D_tasks) >= 3},
    }
    G0 = json.loads((RUN / "preflight.json").read_text())["pass"]
    out = {"stage": "greedy", "n_cells": len(bk), "G0": G0, **g, "per_model": per_model,
           "PASS": G0 and all(v["pass"] for v in g.values()),
           "matrix": {t: {m: "".join(map(str, bk[(m, t, 0)])) for m in MODELS} for t in tids}}
    write_once(RUN / "gate.json", out)
    print(json.dumps({k: out[k] for k in ["PASS", "G0", "G1", "G2", "G3"]}, indent=2))
    print(json.dumps(per_model, indent=2))


# ------------------------------------------------------------------- replay --
def cmd_replay(_):
    from thesis_pilot.evalplus_replay import run_replay

    check_manifest()
    gate = json.loads((RUN / "gate.json").read_text())
    if not gate["PASS"]:
        raise SystemExit("Gate FAILED: STOP (protocol §4). No method is fit.")
    out = run_replay(bank("greedy"), MODELS, [t["task_id"] for t in tasks()])
    write_once(RUN / "replay.json", out)
    print(json.dumps(out["summary"], indent=2))


def main(argv=None):
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    for name in ["manifest", "preflight", "gate", "replay"]:
        sp.add_parser(name)
    for name in ["generate", "evaluate"]:
        q = sp.add_parser(name)
        q.add_argument("--stage", choices=list(STAGES), required=True)
    a = p.parse_args(argv)
    {"manifest": cmd_manifest, "preflight": cmd_preflight, "generate": cmd_generate, "evaluate": cmd_evaluate,
     "gate": cmd_gate, "replay": cmd_replay}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
