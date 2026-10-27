"""Judge selection uses genuine agent answers and never sends benchmark gold."""

from run_real_week5_modal_judge import (
    AGENTS, build_manifest, fetch_metadata, prompt_for, response_schema,
)


def test_judge_cases_deduplicate_answers_without_gold():
    class Task:
        def __init__(self, task_id, subject):
            self.task_id = task_id
            self.options = ("option one", "option two")
            self.ground_truth_answer = "SECRET_GOLD"
            self.subject = subject

        def to_online_view(self):
            return type("View", (), {"question": "A sample question?",
                                     "options": self.options})()

    subjects = [f"subject_{i}" for i in range(14)]
    task_map = {f"task_{i}": Task(f"task_{i}", subject)
                for i, subject in enumerate(subjects)}
    old = {"selected": {"train_calibration": {
        subject: [f"task_{i}"] for i, subject in enumerate(subjects)}},
        "dataset_id": "dataset", "dataset_task_id_sha256": "digest", "split_seed": 42}
    rows = [{"task_id": task_id, "agent": agent, "answer": "A",
             "split": "train_calibration"}
            for task_id in task_map for agent in AGENTS]
    manifest = build_manifest(old, rows, task_map, per_subject=1, seed=7,
                              model_digest="fake_digest", server_version="test")
    assert len(manifest["candidate_cases"]) == 14
    assert all(len(case["agents"]) == 4 for case in manifest["candidate_cases"])
    assert "SECRET_GOLD" not in str(manifest)
    assert "SECRET_GOLD" not in prompt_for(task_map["task_0"], "A")
    assert response_schema(2)["properties"]["chosen_letter"]["enum"] == ["A", "B"]


def test_modal_metadata_retries_transient_503(monkeypatch):
    class Response:
        def __init__(self, status_code):
            self.status_code = status_code

    class Client:
        def __init__(self):
            self.calls = 0

        def request(self, method, url):
            self.calls += 1
            return Response(503 if self.calls == 1 else 200)

    monkeypatch.setattr("run_real_week5_modal_judge.time.sleep", lambda _: None)
    client = Client()
    response = fetch_metadata(client, "GET", "https://example.modal.direct/api/version")
    assert response.status_code == 200
    assert client.calls == 2
