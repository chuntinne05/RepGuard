"""In-container evaluator (port of evalplus_eval_app.evaluate_batch).

Reads /in/subset.jsonl + /in/samples.json (read-only mount), prints a final RESULT_JSON: line.
samples: [{"key","task_id","raw"} | {"key","task_id","solution"}].
"""
import hashlib
import json
import os
import socket
import tempfile
from pathlib import Path

work = Path(tempfile.mkdtemp())
DS = os.environ.get("EP_DATASET", "mbpp")  # humaneval: ECRT-v2 confirmation
os.environ["MBPP_OVERRIDE_PATH" if DS == "mbpp" else "HUMANEVAL_OVERRIDE_PATH"] = "/in/subset.jsonl"  # read at import time
os.environ["XDG_CACHE_HOME"] = str(work / "cache")

network_blocked = True
try:
    socket.create_connection(("1.1.1.1", 53), timeout=3).close()
    network_blocked = False
except OSError:
    pass

from evalplus.data import get_human_eval_plus, get_mbpp_plus  # noqa: E402
import evalplus.data.humaneval as _he  # noqa: E402

_he.completeness_check = lambda *a, **k: None  # chunked subsets are incomplete by design
from evalplus.evaluate import evaluate  # noqa: E402
from evalplus.sanitize import sanitize  # noqa: E402

samples = json.loads(Path("/in/samples.json").read_text(encoding="utf-8"))
problems = get_mbpp_plus() if DS == "mbpp" else get_human_eval_plus()
rows = []
for s in samples:
    tid = s["task_id"]
    code = s["solution"] if "solution" in s else sanitize(s["raw"], problems[tid]["entry_point"])
    rows.append({"task_id": tid, "solution": code, "_key": s["key"]})

samples_path = work / "samples.jsonl"
samples_path.write_text("".join(json.dumps({"task_id": r["task_id"], "solution": r["solution"]}) + "\n" for r in rows))
out_path = work / "eval_results.json"
evaluate(DS, samples=str(samples_path), parallel=4, test_details=True, output_file=str(out_path))
res = json.loads(out_path.read_text())

by_task = {}
for r in rows:
    by_task.setdefault(r["task_id"], []).append(r)
out = []
for tid, lst in by_task.items():
    evals = res["eval"][tid]
    assert len(evals) == len(lst)
    for r, e in zip(lst, evals):
        assert e["solution"] == r["solution"]
        out.append({
            "key": r["_key"], "task_id": tid,
            "sanitized_sha256": hashlib.sha256(r["solution"].encode()).hexdigest(),
            "base_status": e["base_status"], "plus_status": e["plus_status"],
            "n_base": len(problems[tid]["base_input"]), "n_plus": len(problems[tid]["plus_input"]),
            "base_fail_count": len(e["base_fail_tests"]), "plus_fail_count": len(e["plus_fail_tests"]),
        })
# stdout, not a mount: a sample once removed /out; no writable host mount is safer anyway
print("\nRESULT_JSON:" + json.dumps({"dataset_hash": res["hash"], "network_blocked": network_blocked, "results": out}))
