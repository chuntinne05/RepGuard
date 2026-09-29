"""The paired thinking protocol must preserve arm separation and final answers."""

import json
from unittest.mock import patch

from repguard.config import ProviderConfig, ProviderParams
from repguard.providers.ollama_ import OllamaProvider
from run_real_week4_thinking import load_completed, select_unused


def test_ollama_thinking_is_explicit_and_final_content_is_separate():
    provider = OllamaProvider(ProviderConfig(name="ollama", model_id="qwen3:8b",
        parameters=ProviderParams(temperature=0.0, max_tokens=64, top_p=1.0)),
        base_url="http://localhost:11434")

    class Response:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"thinking": "private reasoning", "content": '{"answer":"B"}'},
                    "prompt_eval_count": 50, "eval_count": 110,
                    "done": True, "done_reason": "stop"}

    with patch.object(provider._client, "post", return_value=Response()) as post:
        result = provider.complete("question", think=True, max_tokens=1024,
                                   response_format={"type": "object"})
    payload = post.call_args.kwargs["json"]
    assert payload["think"] is True
    assert payload["options"]["num_predict"] == 1024
    assert payload["format"] == {"type": "object"}
    assert result.content == '{"answer":"B"}'
    assert result.raw_response == {"done": True, "done_reason": "stop",
                                   "thinking_present": True, "thinking_chars": 17}


def test_select_unused_does_not_reuse_week3_history():
    class Task:
        def __init__(self, task_id, subject):
            self.task_id = task_id
            self.metadata = type("Metadata", (), {"subject": subject})()

    class Split:
        records = [Task(f"x{i}", "biology") for i in range(4)]

    old = {"selected": {"train_calibration": {"biology": ["x0"]}}}
    selected = select_unused({"train_calibration": Split()}, old, 2, 123)
    assert "x0" not in selected["biology"]
    assert len(selected["biology"]) == 2


def test_resume_key_includes_variant_and_protocol(tmp_path):
    ledger = tmp_path / "predictions.jsonl"
    ledger.write_text(json.dumps({"protocol_hash": "abc", "variant": "direct64",
                                  "task_id": "q1"}) + "\n")
    assert load_completed(ledger, "abc") == {("direct64", "q1")}
