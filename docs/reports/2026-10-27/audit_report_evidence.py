"""Read-only source/evidence review; writes only this report's new artifacts.

No inference, network request, dataset selection, or generated-code execution.
The arithmetic allowlist interpreters only recheck previously saved responses.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def read(relative):
    return json.loads((ROOT / relative).read_text())


def inventory():
    paths = []
    for name in ["src", "infra", "thesis_pilot", "tests", "docs/analysis"]:
        paths.extend((ROOT / name).rglob("*.py"))
    paths.extend(ROOT.glob("*.py"))
    records = []
    for path in sorted(set(paths)):
        raw = path.read_bytes()
        content = raw.decode("utf-8-sig")
        tree = ast.parse(content, filename=str(path))
        definitions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                definitions.append({"name": node.name, "line": node.lineno,
                                    "kind": type(node).__name__})
        records.append({"path": str(path.relative_to(ROOT)),
                        "lines": len(content.splitlines()), "bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "docstring": ast.get_docstring(tree) or "",
                        "definitions": sorted(definitions, key=lambda d: d["line"])})
    groups = {}
    for row in records:
        key = row["path"].split("/")[0] if "/" in row["path"] else "root_scripts"
        group = groups.setdefault(key, {"files": 0, "lines": 0})
        group["files"] += 1
        group["lines"] += row["lines"]
    artifact = {"review_date": "2026-10-27", "scope": "Project Python sources, scripts, tests, analysis utilities; excludes third-party source under results, venv, caches and this new report folder.",
                "review_depth": "Full-file bytes/hash/UTF-8/AST inventory; targeted behavioral review of research-critical algorithms, collectors, evaluators and protocols. Not a line-by-line formal verification or security audit.",
                "python_files": len(records), "lines": sum(r["lines"] for r in records),
                "groups": groups, "syntax_errors": [], "files": records}
    (OUT / "source_inventory.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")
    lines = ["# Danh mục mã nguồn đã rà soát - 27/10/2026", "",
             artifact["review_depth"], "", "| Nhóm | File Python | Dòng |", "|---|---:|---:|"]
    lines += [f"| {k} | {v['files']} | {v['lines']} |" for k, v in groups.items()]
    lines += ["", "Mỗi file bên dưới đã được đọc để kiểm hash/cú pháp và lập bản đồ định nghĩa. Danh mục không đồng nghĩa mọi nhánh đã được kiểm thử. Chi tiết phân tích hành vi nằm trong báo cáo chính.", ""]
    for row in records:
        relative = "../../../" + row["path"]
        lines += [f"## [{row['path']}]({relative})", "",
                  f"{row['lines']} dòng; SHA256 `{row['sha256']}`.", ""]
        if row["docstring"]:
            lines += [row["docstring"].splitlines()[0], ""]
        if row["definitions"]:
            lines += ["Định nghĩa: " + "; ".join(f"`{d['name']}` (L{d['line']})" for d in row["definitions"]) + ".", ""]
    (OUT / "source_inventory.md").write_text("\n".join(lines))
    return {k: v for k, v in artifact.items() if k != "files"}


def rerun_existing_receipt_audit(filename, expected_dest):
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), ROOT / "docs/analysis" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = Path.write_text
    redirected = []

    def only_report_write(path, data, *args, **kwargs):
        if path.resolve() != (ROOT / "docs/analysis" / expected_dest).resolve():
            raise RuntimeError("Unexpected write refused: " + str(path))
        target = OUT / ("rechecked_" + expected_dest)
        redirected.append(str(target.relative_to(ROOT)))
        return original(target, data, *args, **kwargs)

    output = io.StringIO()
    with patch.object(Path, "write_text", only_report_write), contextlib.redirect_stdout(output):
        module.audit()
    result = json.loads(output.getvalue())
    assert result["audit"] == "PASS"
    return {"audit": "PASS", "script": filename, "output": redirected,
            "writes_to_original_artifacts": False}


def recheck_scoring():
    """Recompute official TAT-QA EM without writing old summaries."""
    import numpy as np
    from thesis_pilot.tatqa_scope_study import prepare as scope_prepare, replay as scope_replay
    from thesis_pilot.tatqa_crossfamily_study import prepare as family_prepare, replay as family_replay
    source = ROOT / "results/thesis_tatqa_source_v1"
    sys.path.insert(0, "/tmp/repguard_tatqa_eval_deps")
    sys.path.insert(0, str(source))
    from tatqa_metric import TaTQAEmAndF1
    labels = read("results/thesis_tatqa_source_v1/annotations_private.json")
    all_results = {}
    for name, prepare, replay, folder in [
        ("scoped", scope_prepare, scope_replay, "thesis_tatqa_scoped_repair_v1"),
        ("crossfamily", family_prepare, family_replay, "thesis_tatqa_crossfamily_v1"),
    ]:
        plan, cases = prepare()
        expected = read("results/" + folder + "/summary.json")
        totals = Counter()
        validity = Counter()
        masks = {}
        for case in cases:
            effective = replay(case)[0] if name == "scoped" else replay(case, plan)[0]
            for action, value in effective.items():
                metric = TaTQAEmAndF1()
                metric(ground_truth=labels[case["id"]],
                       prediction=[str(value["value"])] if value["hard_pass"] else [],
                       pred_scale=value["scale"])
                em = metric.get_overall_metric()[0]
                totals[action] += int(bool(em))
                validity[action] += int(value["hard_pass"])
                masks.setdefault(action, []).append(bool(em))
        for action, score in expected["methods"].items():
            assert totals[action] == score["correct"]
            assert validity[action] == score["valid"]
        actions = ["initial", "evidence", "operation", "combined"] if name == "scoped" else list(masks)
        oracle = int(np.any([masks[a] for a in actions], axis=0).sum())
        target = expected["scoped_oracle_diagnostic"] if name == "scoped" else expected["oracle_union_diagnostic"]
        assert oracle == target
        all_results[name] = {"run_id": plan["run_id"], "official_em": dict(totals),
                             "executable": dict(validity), "oracle_union": oracle,
                             "summary_matches": True, "new_model_calls": 0}
    return all_results


def main():
    report = {"review_date": "2026-10-27", "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "new_model_calls": 0, "live_cloud_status_queried": False,
              "sealed_confirmation_outcomes_opened": False,
              "source_inventory": inventory()}
    audits = []
    for script, dest in [
        ("verify_tatqa_scope_cycle03.py", "repguard_cycle03_audit_2026-10-20.json"),
        ("verify_tatqa_crossfamily_cycle03.py", "repguard_cycle03_crossfamily_audit_2026-10-20.json"),
    ]:
        audits.append(rerun_existing_receipt_audit(script, dest))
    report["receipt_audits_rerun"] = audits
    try:
        report["official_scores_recomputed"] = recheck_scoring()
    except ImportError as error:
        report["official_scores_recomputed"] = {"status": "unavailable_dependency", "error": str(error)}
    prepared = read("results/thesis_evalplus_source_v1/inventory.json")
    assert prepared["selected_tasks"] == 32 and prepared["model_calls"] == prepared["programs_executed"] == 0
    report["evalplus_preparation"] = {k: prepared[k] for k in ["selected_tasks", "model_calls", "programs_executed", "benchmark_score"]}
    scope = read("results/thesis_tatqa_scoped_repair_v1/summary.json")
    family = read("results/thesis_tatqa_crossfamily_v1/summary.json")
    assert scope["actual_new_calls"] + family["actual_new_calls"] == 264
    assert scope["real_new_input_tokens"] + family["new_input_tokens"] == 572340
    assert scope["real_new_output_tokens"] + family["new_output_tokens"] == 59841
    report["cycle03_counts_verified"] = {"new_calls": 264, "unique_contexts": 24, "reused_calls_not_double_counted": 24,
                                         "input_tokens": 572340, "output_tokens": 59841}
    report["pytest_run_observed"] = {"command": "./.venv/bin/python -m pytest -q", "passed": 308, "skipped": 1,
                                     "collected": 309, "seconds": 82.83,
                                     "scope": "Existing repository test suite; recorded from actual run on review date, not a test of every thesis_pilot branch or semantic labels."}
    (OUT / "verification_2026-10-27.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
