"""Audit published gold against context before sampling or inference."""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
from collections import Counter
from decimal import Decimal
from pathlib import Path

from .oracle import bind, close, execute, number, source_table

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/verification_v1/enterprise_intake/arqa"
OUT = ROOT / "results/arqa_v2"
REPORT = ROOT / "docs/reports/2026-11-09"


def digest(obj):
    data = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def load():
    expected = {"ARQA_validated.json": "004075187f5e564a1ff7a35111c6d6828f67804f9b5d00c908fbe53d130a4063",
                "pack_context.db": "9b76189340c34c0b1cb57fc5b287d4a4e28d864b28702ab934f90fb77a25666a"}
    for name, sha in expected.items():
        if digest((SOURCE / name).read_bytes()) != sha:
            raise ValueError("Source changed: " + name)
    packs = json.loads((SOURCE / "ARQA_validated.json").read_text())["packs"]
    with tempfile.TemporaryDirectory(prefix="repguard-arqa-") as temp:
        db = Path(temp) / "ctx.db"
        shutil.copyfile(SOURCE / "pack_context.db", db)
        conn = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        rows = [dict(r) for r in conn.execute("SELECT * FROM context_packs")]
        conn.close()
    contexts = {}
    for r in rows:
        for field in ("headers", "merged_headers", "rows", "stub_col", "paragraphs"):
            r[field] = json.loads(r[field])
        if r["table_id"] in contexts:
            raise ValueError("Duplicate context ID")
        contexts[r["table_id"]] = r
    return packs, contexts


def audit():
    packs, contexts = load()
    details, eligible = [], []
    for pack in packs:
        table = source_table(contexts[pack["table_id"]])
        for q in pack["qas"]:
            if q["q_type"] != "arithmetic":
                continue
            row = {"qa_id": q["qa_id"], "table_id": pack["table_id"], "year": pack["year"],
                   "arith_type": q.get("arith_type"), "verified_published": q.get("verified")}
            try:
                result, ids = execute(q.get("program"), table, gold=True)
                declared = number(q.get("answer_value"))
                # Honor displayed decimal rounding (integer counts stay exact).
                exp = declared.as_tuple().exponent
                tolerance = max(Decimal("0.005000001"), Decimal("0.50000001").scaleb(exp)) if exp < 0 else Decimal("0.005000001")
                if not close(result, declared, tolerance):
                    raise ValueError("Recomputed answer outside published decimal rounding")
                evidence = q.get("evidence", [])
                if not isinstance(evidence, list) or not evidence:
                    raise ValueError("Missing evidence list")
                evidence_ids = []
                for c in evidence:
                    if set(c) == {"header_col"}:
                        if str(c["header_col"]) not in table["headers"] + table["expanded_headers"]:
                            raise ValueError("Unknown evidence header")
                        continue
                    evidence_ids.append(bind(c, table)["id"])
                if set(evidence_ids) != set(ids):
                    raise ValueError("Evidence/program source mismatch")
                row.update(passed=True, recomputed=str(result), source_ids=ids)
                eligible.append({"qa": q, "table": table, "oracle": str(result), "source_ids": ids})
            except (ValueError, ArithmeticError, TypeError, KeyError) as error:
                row.update(passed=False, reason=str(error))
            details.append(row)
    summary = {"scope": "Exact source-cell and arithmetic audit; NOT natural-language semantic adjudication, not an official ARQA score.",
               "zero_model_calls": True, "source_commit": "483e8c7b084afc6fbfb46d8609617b297b4322b8",
               "items": len(details), "passed": sum(d["passed"] for d in details),
               "failed_reasons": dict(Counter(d["reason"] for d in details if not d["passed"])),
               "passed_types": dict(Counter(e["qa"].get("arith_type") for e in eligible)),
               "passed_years": dict(Counter(e["table"]["year"] for e in eligible)),
               "unsupported_official_interpreter_ops": ["abs", "sum", "avg", "min", "max", "count", "rank", "sort", "topk"],
               "official_scorer_limitations": ["run_program reads self-declared values, not context DB",
                 "arithmetic evidence matching drops column", "ULP tolerance permits +/-1 for integer gold"],
               "semantic_claims": "No human review completed; provenance and arithmetic do not establish formula/metric/period appropriateness."}
    write(OUT / "preflight_details_private.json", details)
    write(OUT / "eligible_private.json", eligible)
    write(REPORT / "arqa_oracle_audit.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    audit()
