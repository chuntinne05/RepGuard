"""The Modal pipeline must wait for all Week 4 calls before sharing its GPU."""

import run_real_week5_pipeline as pipeline


def test_pipeline_does_not_advance_on_partial_week4(monkeypatch, tmp_path):
    counts = iter([839, 840])
    seen = []
    monkeypatch.setattr(pipeline, "count_jsonl", lambda _: next(counts))
    monkeypatch.setattr(pipeline, "WEEK4", tmp_path)
    monkeypatch.setattr(pipeline, "week4_runner_alive", lambda: True)
    monkeypatch.setattr(pipeline, "modal_container_active", lambda: True)
    monkeypatch.setattr(pipeline, "status", lambda stage, **details:
                        seen.append((stage, details)))
    monkeypatch.setattr(pipeline.time, "sleep", lambda _: None)
    pipeline.wait_for_week4(max_wait_hours=1)
    assert seen[0] == ("waiting_for_week4",
                       {"completed_calls": 839, "expected_calls": 840})
    assert seen[-1] == ("week4_ledger_complete", {"completed_calls": 840})
