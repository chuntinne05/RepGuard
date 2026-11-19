"""Metadata-only external preflight; no gold file or benchmark code is executed."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/general_verification_v1/source_intake"


def fingerprint(value):
    return hashlib.sha256(value.encode()).hexdigest()


def public_task(row):
    keys = ("task_id", "question", "workspace_path", "modalities", "workspace_files")
    return {k: row[k] for k in keys}


def main():
    meta = json.loads((BASE / "DataSpace/hf_metadata.json").read_text())
    path = BASE / "DataSpace/hf/data/tasks.jsonl"
    if hashlib.sha256(path.read_bytes()).hexdigest() != "2afa196004c19e4b0e04f1689762f6a224beecfe6f3b02f99c7e3e1d09fa1474":
        raise ValueError("Pinned task metadata changed")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    references = [r for r in rows if r["reference_available"]]
    if len({r["task_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate task IDs")
    # Candidate source inspection only, not membership for a model study.
    eligible = [r for r in references if not r["video_files"] and r["context_bytes"] <= 100_000_000]
    selected = sorted(eligible, key=lambda r: fingerprint("source-inspection-only:" + r["task_id"]))[:6]
    packet = {"scope": "Source-inspection candidates only, not a registered study or inference launch.",
              "dataset_revision": meta["revision"], "tasks": [public_task(r) for r in selected]}
    destination = BASE / "DataSpace/source_inspection_public_tasks.json"
    destination.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
    partial_path = BASE / 'DataSpace/partial_inspection.json'
    partial = json.loads(partial_path.read_text()) if partial_path.exists() else None
    summary = {"scope": "Source/schema availability and optionally bounded partial input inspection only; no model generation, gold answer, benchmark config or model output inspected.",
               "dataspace": {"code_revision": "6491caa4c70cc06cacb6103ba73cefb00746abfe", "dataset_revision": meta["revision"],
                 "task_metadata_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "tasks": len(rows),
                 "public_reference_tasks": len(references), "withheld_reference_tasks": len(rows)-len(references),
                 "unique_question_strings": len({r["question"] for r in rows}),
                 "modality_task_counts": dict(Counter(m for r in rows for m in r["modalities"])),
                 "median_workspace_bytes": median(r["context_bytes"] for r in rows),
                 "public_reference_no_video_tasks": sum(not r["video_files"] for r in references),
                 "inspection_candidate_ids": [r["task_id"] for r in selected],
                 "archive_bytes_from_metadata": next(x["size"] for x in meta["files"] if x["rfilename"].endswith('.zip')),
                 "full_archive_downloaded_or_verified": False,
                 "partial_workspace_inspection": {"candidate_workspaces": len(partial['tasks']),
                    "input_files_read": sum(len(t['inspected']) for t in partial['tasks']),
                    "range_bytes_downloaded": partial['downloaded_range_bytes'],
                    "member_crc_checked": True,"full_archive_sha256_verified": False,
                    "complete_workspace_or_oracle_validated": False} if partial else None,
                 "scorer_source_inspected": True, "scorer_executed": False,
                 "scorer_notes": ["Task-specific types/precision/percent convention frozen", "Complete-table equality with column alignment and row multiplicities", "Does not itself establish that agent reasoning or attribution is sound"],
                 "grouping_limit": "Task metadata lacks source content hashes/lineage; task-level random split cannot certify source-disjoint transfer.",
                 "next": "Inspect selected workspaces, grouping and question/config semantics before freezing any new inference protocol."},
               "dab": {"code_revision": "3ce514f0a601569ab2ac3569542152423794a461", "readme_reported_queries":54,
                       "readme_reported_datasets":12, "readme_reported_domains":9,
                       "downloaded": "README and Git tree only", "database_assets_validated":False,
                       "license_confirmed":False, "next":"Resolve dataset-specific terms, manifests, database dependencies and per-query validators before use."},
               "mm_enterprise": {"source":"https://mlv.kaist.ac.kr/MMEnterprise-Bench/", "availability":"Official project page currently says dataset/evaluation toolkit coming soon; not ready for local experiments."}}
    output = ROOT / "docs/reports/2026-11-09/cross_workload_source_preflight.json"
    output.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == "__main__": main()
