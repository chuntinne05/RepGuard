"""Modal CPU evaluator for the EvalPlus partial-feedback pilot.

Runs the OFFICIAL pinned EvalPlus evaluator on model-generated code inside a
container with ``block_network=True``. Generated code never executes on the
user's machine. No GPU, no model, no Ollama endpoint is involved here.

Deploy-free usage (ephemeral app) is driven by ``thesis_pilot.evalplus_study``.
"""

from __future__ import annotations

from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "thesis_evalplus_source_v1" / "source"

APP_NAME = "repguard-evalplus-eval-20261109"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "numpy==2.1.3",
        "tqdm==4.67.1",
        "termcolor==2.5.0",
        "fire==0.7.0",
        "appdirs==1.4.4",
        "wget==3.2",
        "tempdir==0.7.1",
        "multipledispatch==1.0.0",
        "psutil==6.1.1",
        "rich==13.9.4",
        "tree_sitter==0.23.2",
        "tree-sitter-python==0.23.6",
        "datasets==3.2.0",  # imported (unused on our path) by evalplus.data
    )
    .add_local_dir(str(SOURCE / "evalplus"), "/opt/evalplus_src/evalplus", copy=True)
    .env({"PYTHONPATH": "/opt/evalplus_src"})
)

app = modal.App(APP_NAME, image=image)


@app.function(cpu=4.0, memory=4096, timeout=1800, block_network=True, max_containers=1)
def evaluate_batch(subset_jsonl: str, samples: list[dict]) -> dict:
    """Sanitize + evaluate samples with the official EvalPlus pipeline.

    samples: [{"key": str, "task_id": str, "raw": str} | {"key", "task_id", "solution"}]
    A sample carrying ``raw`` is sanitized with the official sanitizer and entry point;
    one carrying ``solution`` (preflight controls) is evaluated verbatim.
    """
    import hashlib
    import json
    import os
    import socket
    import tempfile

    work = Path(tempfile.mkdtemp())
    subset_path = work / "mbpp_subset.jsonl"
    subset_path.write_text(subset_jsonl)
    os.environ["MBPP_OVERRIDE_PATH"] = str(subset_path)  # read at evalplus import time
    os.environ["XDG_CACHE_HOME"] = str(work / "cache")

    network_blocked = True
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=3).close()
        network_blocked = False
    except OSError:
        pass

    from evalplus.data import get_mbpp_plus
    from evalplus.evaluate import evaluate
    from evalplus.sanitize import sanitize

    problems = get_mbpp_plus()
    rows = []
    for s in samples:
        tid = s["task_id"]
        if "solution" in s:
            code = s["solution"]
        else:
            code = sanitize(s["raw"], problems[tid]["entry_point"])
        rows.append({"task_id": tid, "solution": code, "_key": s["key"]})

    samples_path = work / "samples.jsonl"
    samples_path.write_text("".join(json.dumps({"task_id": r["task_id"], "solution": r["solution"]}) + "\n" for r in rows))
    out_path = work / "eval_results.json"
    evaluate("mbpp", samples=str(samples_path), parallel=4, test_details=True, output_file=str(out_path))
    res = json.loads(out_path.read_text())

    # evaluate() sorts per task by completion_id == order of appearance per task
    by_task: dict[str, list[dict]] = {}
    for r in rows:
        by_task.setdefault(r["task_id"], []).append(r)
    out = []
    for tid, lst in by_task.items():
        evals = res["eval"][tid]
        assert len(evals) == len(lst)
        for r, e in zip(lst, evals):
            assert e["solution"] == r["solution"]
            out.append({
                "key": r["_key"],
                "task_id": tid,
                "sanitized_sha256": hashlib.sha256(r["solution"].encode()).hexdigest(),
                "sanitized": r["solution"],
                "base_status": e["base_status"],
                "plus_status": e["plus_status"],
                "n_base": len(problems[tid]["base_input"]),
                "n_plus": len(problems[tid]["plus_input"]),
                "base_fail_count": len(e["base_fail_tests"]),
                "plus_fail_count": len(e["plus_fail_tests"]),
                "plus_fail_example": repr(e["plus_fail_tests"][:1])[:400],
            })
    return {
        "dataset_hash": res["hash"],
        "network_blocked": network_blocked,
        "n_samples": len(out),
        "results": out,
    }
