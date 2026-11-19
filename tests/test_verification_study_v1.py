"""Research-critical checks: no label access, correct pairing, abstentions and receipts."""
import json

import pytest

from experiments.verification_v1.analysis import metrics
from experiments.verification_v1.collection import collect
from experiments.verification_v1.core import build_prompt, parse_answer, request_id
from experiments.verification_v1.prepare import digest


@pytest.fixture
def case():
    return {"claim": "Revenue was 10 in 2024.", "claim_date": "2025-01-01",
            "source_title": "Report", "domain": "example.org", "source_date": "2024-12-31",
            "passage": "Revenue was 10 in 2024."}


def answer(label=2):
    return json.dumps({"label": label, "confidence": .8,
                       "evidence_quote": "Revenue was 10 in 2024.", "explanation": "Period and metric match."})


def test_gold_rejected_before_prompt(case):
    with pytest.raises(ValueError):
        build_prompt({**case, "final_label": 2})


def test_initial_identity_and_gold_rejected(case):
    with pytest.raises(ValueError):
        build_prompt(case, {"raw_text": answer(), "model": "A"})


@pytest.mark.parametrize("value", [True, "2", 4, -1])
def test_invalid_labels(case, value):
    assert not parse_answer(answer(value), case)["valid"]


def test_fence_only_normalization(case):
    assert parse_answer("```json\n" + answer() + "\n```", case)["label"] == 2
    assert not parse_answer("Here is the answer: " + answer(), case)["valid"]


def test_hallucinated_quote_does_not_secretly_change_score(case):
    raw = json.loads(answer()); raw["evidence_quote"] = "not present"
    parsed = parse_answer(json.dumps(raw), case)
    assert parsed["valid"] and parsed["label"] == 2 and not parsed["grounded_sufficient"]


def test_no_approvals_risk_is_undefined():
    m = metrics([1, 1, None], [0, 1, 2])
    assert m["false_sufficient_risk"] is None and m["correct"] == 1


def test_direction_mismatch_counts_as_false_sufficient():
    m = metrics([2, 3, None], [3, 3, 2])
    assert m["false_sufficient_risk"] == .5 and m["accuracy"] == pytest.approx(1/3)


def test_request_ids_include_workflow_and_plan():
    assert len({request_id(p, "item", w) for p in ("p", "q") for w in ("A", "AA", "AB")}) == 6


def test_collection_actual_prior_lineage_and_no_duplicate_calls(case, tmp_path):
    public = {"items": [{"id": "x", "group": "g", "case": case}]}
    plan = {"plan_id": "p", "public_sha256": digest(public), "items": 1,
            "max_corpus_calls": 6, "concurrency": 2}
    seen = []
    def invoke(role, prompt):
        seen.append((role, prompt))
        return {"provider": "ollama_modal", "response": {"message": {"content": answer()}}}
    result = collect(plan, public, tmp_path, invoke)
    assert result["completed"] == 6 and len(seen) == 6
    records = [json.loads(p.read_text()) for p in (tmp_path / "responses").glob("*.json")]
    ab = next(r for r in records if r["workflow"] == "AB")
    a = next(r for r in records if r["workflow"] == "A")
    assert ab["parent_request_id"] == a["request_id"]
    assert answer() in json.loads(ab["prompt"].split("INITIAL_ASSESSMENT_JSON_STRING\n")[1])
    collect(plan, public, tmp_path, invoke)
    assert len(seen) == 6


def test_unknown_receipt_blocks_blind_regeneration(case, tmp_path):
    public = {"items": [{"id": "x", "group": "g", "case": case}]}
    plan = {"plan_id": "p", "public_sha256": digest(public), "items": 1,
            "max_corpus_calls": 6, "concurrency": 1}
    (tmp_path / "attempts").mkdir()
    (tmp_path / "attempts" / (request_id("p", "x", "A") + ".json")).write_text('{}')
    with pytest.raises(RuntimeError, match="Unresolved"):
        collect(plan, public, tmp_path, lambda *_: pytest.fail("Must not regenerate"))
