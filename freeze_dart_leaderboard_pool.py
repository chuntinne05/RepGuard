"""Freeze the historical AppWorld baseline pool without inspecting outcomes.

This script reads only git tree paths and the public dataset ID lists. It never
opens leaderboard JSON or encrypted bundles.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


BASELINES = (
    "full_code_refl_deepseekcoder",
    "full_code_refl_gpt4o",
    "full_code_refl_gpt4turbo",
    "full_code_refl_llama3",
    "ipfuncall_gpt4o",
    "ipfuncall_gpt4turbo",
    "plan_exec_deepseekcoder",
    "plan_exec_gpt4o",
    "plan_exec_gpt4turbo",
    "plan_exec_llama3",
    "react_deepseekcoder",
    "react_gpt4o",
    "react_gpt4turbo",
    "react_llama3",
)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leaderboard-repo", type=Path, required=True)
    parser.add_argument(
        "--dataset-root", type=Path, default=Path("results/appworld_external_v1/data/datasets")
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("docs/analysis/dart_leaderboard_pool_manifest_2026-10-04.json"),
    )
    args = parser.parse_args()
    commit = git(args.leaderboard_repo, "rev-parse", "HEAD")
    paths = set(git(args.leaderboard_repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines())
    agents = []
    for name in BASELINES:
        bundles = {
            split: f"experiments/outputs/{name}_{split}/leaderboard.bundle"
            for split in ("test_normal", "test_challenge")
        }
        agents.append({"name": name, "bundle_paths": bundles,
                       "both_bundles_present": all(p in paths for p in bundles.values())})
    datasets = {}
    for split in ("test_normal", "test_challenge"):
        source = args.dataset_root / f"{split}.txt"
        raw = source.read_bytes()
        ids = raw.decode().splitlines()
        assert len(ids) == len(set(ids)), f"Duplicate task IDs in {source}"
        datasets[split] = {
            "source": str(source), "sha256": hashlib.sha256(raw).hexdigest(),
            "count": len(ids), "task_ids": ids,
        }
    normal_ids = datasets["test_normal"]["task_ids"]
    generators = sorted({task_id.rsplit("_", 1)[0] for task_id in normal_ids})
    folds = {g: int(hashlib.sha256(("dart-appworld-v1:" + g).encode()).hexdigest(), 16) % 5
             for g in generators}
    manifest = {
        "schema": "dart-leaderboard-pool-v1",
        "leaderboard_repo": "https://github.com/StonyBrookNLP/appworld-leaderboard",
        "leaderboard_commit": commit,
        "selection_rule": "14 historical official baseline agents by scaffold/model, fixed before task outcomes; later exclusions only for predeclared schema/version/completeness failures",
        "agents": agents,
        "dataset_id_lists": datasets,
        "normal_outer_fold_by_generator": folds,
        "normal_outer_fold_rule": "SHA256('dart-appworld-v1:' + generator_id) as integer mod 5; generator_id is task_id before final underscore",
        "challenge_role": "secondary distribution shift; use only if identical task IDs and evaluation schema across eligible agents",
        "per_task_outcomes_opened_at_freeze": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"Frozen {len(agents)} agents, {len(normal_ids)} normal tasks, {len(generators)} generators, commit {commit}")
    print("fold task counts:", {fold: sum(folds[t.rsplit('_', 1)[0]] == fold for t in normal_ids)
                                for fold in range(5)})


if __name__ == "__main__":
    main()
