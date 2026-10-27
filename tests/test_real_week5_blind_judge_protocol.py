"""Candidate-blind judge prompts cannot see candidate answers or gold labels."""

from run_real_week5_blind_judge import build_manifest, prompt_for, response_schema


def test_blind_judge_manifest_has_one_prompt_per_task_and_no_candidate():
    class Task:
        def __init__(self, task_id, subject):
            self.task_id = task_id
            self.metadata = type("Meta", (), {"subject": subject})()
            self.options = ("first option", "second option")
            self.ground_truth_answer = "SECRET_GOLD"

        def to_online_view(self):
            return type("View", (), {"question": "An example question?",
                                     "options": self.options})()

    subjects = [f"subject_{i}" for i in range(14)]
    selected = {subject: [f"task_{i}_{j}" for j in range(20)]
                for i, subject in enumerate(subjects)}
    tasks = {tid: Task(tid, subject)
             for subject, ids in selected.items() for tid in ids}
    source = {"selected_history_ids": selected, "dataset_id": "dataset",
              "dataset_task_id_sha256": "digest", "split_seed": 42,
              "protocol_hash": "source_hash", "judge_model_digest": "model_digest",
              "ollama_version": "version"}
    manifest = build_manifest(source, tasks)
    assert len(manifest["candidate_blind_cases"]) == 280
    assert all("candidate_answer" not in case for case in manifest["candidate_blind_cases"])
    prompt = prompt_for(tasks["task_0_0"])
    assert "SECRET_GOLD" not in prompt
    assert "Submitted answer" not in prompt
    assert response_schema(2)["properties"]["chosen_letter"]["enum"] == ["A", "B"]
