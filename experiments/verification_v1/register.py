"""Freeze an exact plan before corpus generations, choosing service-health fallback."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .core import REVIEW, RUBRIC
from .prepare import OUT, ROOT, digest, write


def main():
    path = OUT / "registered_plan.json"
    if path.exists():
        raise RuntimeError("Plan already registered; never overwrite a registered run")
    inventory = json.loads((OUT / "inventory.json").read_text())
    probe = json.loads((OUT / "provider_probe/summary.json").read_text())
    if probe["api_pathway_valid"]:
        raise RuntimeError("API available; freeze its adapter before registering")
    hashes = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in Path(__file__).parent.glob("*.py")}
    plan = {"registered_utc": datetime.now(timezone.utc).isoformat(),
            "study": "standalone_passage_sufficiency_exchange_v1",
            "source_commit": inventory["source_commit"], "source_sha256": inventory["source_sha256"],
            "public_sha256": inventory["public_sha256"], "gold_sha256": inventory["gold_sha256"],
            "items": inventory["pilot_items"], "claim_groups": inventory["partition_group_counts"]["pilot"],
            "backend": "ollama_modal", "provider_fallback_reason": "Gemini3.8 synthetic request timed out without receipt; no corpus outcome used.",
            "models": {"A": {"name": "qwen3.5:27b", "digest": "64ae5b1d651fb2709d5928ccb8dcfb4bb2cc9c2c8001ac34497e36a6cf905b59"},
                       "B": {"name": "gemma4:26b-a4b-it-q4_K_M", "digest": "5571076f3d70050487b26b341705799e0ab29b808164f90d20d4cf84f699d251"}},
            "ollama": "0.40.6", "gpu_each": "L40S", "weights_mount": "read_only",
            "temperature": 0, "seed": 20261109, "thinking": False,
            "context_tokens": 16384, "output_tokens": 2048, "concurrency": 2,
            "max_corpus_calls": 6 * inventory["pilot_items"], "max_automatic_generation_retries": 0,
            "workflow_order": [["A", "B"], ["AA", "BB", "AB", "BA"]],
            "operational_screen_groups": 2, "operational_min_validity": .95,
            "primary": "mean_claim(0.5*((correctAB-correctAA)+(correctBA-correctBB)))",
            "bootstrap_seed": 20261109, "bootstrap_claim_replicates": 5000,
            "go_gate": {"primary_delta_at_least": .03, "rescue_cells_at_least": 6, "rescue_groups_at_least": 4,
                        "operational_pass_required": True, "confirmation_claim": False},
            "rubric": RUBRIC, "review_instruction": REVIEW, "source_hashes": hashes,
            "metadata_duplicate_amendment": "150 claims form147 exact claim/passage-connected groups; claim counts24/57/21/48 in pilot/dev/calibration/reserve. Pilot still24 groups/120pairs, cap720 unchanged. Reserve47 groups/48claims.",
            "human_oracle": "Published expert passage annotation only; no new human adjudication.",
            "no_gold_to_inference": True, "no_history_learner_in_this_study": True}
    plan["plan_id"] = digest(plan)[:24]
    write(path, plan)
    write(OUT / "runs" / plan["plan_id"] / "plan.json", plan)
    print(json.dumps({k: plan[k] for k in ("plan_id", "registered_utc", "items", "claim_groups", "max_corpus_calls", "backend")}, indent=2))


if __name__ == "__main__":
    main()
