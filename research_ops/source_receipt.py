"""Local source/arithmetic receipt, always requiring semantic human review.

Independent diagnostic added after v2 registration. It never changes its primary
numeric/unit score or frozen parser. No network access or model calls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.arqa_v2.study import parse


def dependencies(program):
    """Trace final dataflow, not just the presence of source reads anywhere."""
    regs, read_ids, warnings = {}, set(), []
    for step in program:
        alias = step["as"]
        if step["op"] == "read":
            deps = {step["cell_id"]}
            read_ids |= deps
        else:
            deps = set()
            for arg in step["inputs"]:
                if isinstance(arg, str) and arg in regs:
                    deps |= regs[arg]
        regs[alias] = deps
    final = regs[program[-1]["as"]] if program else set()
    if not final:
        warnings.append("final_result_has_no_source_dependency")
    if read_ids - final:
        warnings.append("source_reads_unused_by_final_result")
    return {"final_cell_ids": sorted(final), "unused_read_ids": sorted(read_ids-final), "warnings": warnings}


def inspect(case, raw):
    parsed = parse(raw, case["table"])
    result = {"status": "needs_semantic_review", "question": case["question"],
              "source_table_id": case["table"]["table_id"], "parsed": parsed,
              "semantic_verified": False,
              "human_checks_required": ["entity", "metric", "period", "formula authority", "unit and scale", "source completeness"]}
    if parsed.get("source_bound"):
        dep = dependencies(parsed["answer"]["program"])
        result["dataflow"] = dep
        result["source_and_arithmetic_pass"] = bool(dep["final_cell_ids"] and parsed.get("internally_consistent"))
        used = set(dep["final_cell_ids"])
        result["final_source_cells"] = [c for c in case["table"]["cells"] if c["id"] in used]
    else:
        result["source_and_arithmetic_pass"] = False
    if not result["source_and_arithmetic_pass"]:
        result["status"] = "mechanical_check_failed_or_abstained"
    return result


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case", required=True, type=Path, help="JSON object with question and table")
    p.add_argument("--answer", required=True, type=Path, help="Raw JSON answer text")
    p.add_argument("--output", type=Path)
    args=p.parse_args()
    receipt=inspect(json.loads(args.case.read_text()),args.answer.read_text())
    text=json.dumps(receipt,ensure_ascii=False,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
    else:
        print(text,end="")
