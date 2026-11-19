"""Checks for the real-data protocol that affect scientific validity."""

from analyze_real_week3 import StudyTransferEstimator, choose_answer, wilson
from run_real_week3 import make_manifest


def test_manifest_selection_is_label_free_and_disjoint():
    class Task:
        def __init__(self, task_id, subject):
            self.task_id = task_id
            self.metadata = type("M", (), {"subject": subject})()

    class Split:
        def __init__(self, records):
            self.records = records

    splits = {
        "train_calibration": Split([Task(f"train_{s}_{i}", s) for s in ("math", "biology") for i in range(6)]),
        "dev": Split([Task(f"dev_{s}_{i}", s) for s in ("math", "biology") for i in range(6)]),
        "test": Split([Task(f"test_{s}_{i}", s) for s in ("math", "biology") for i in range(6)]),
    }
    tasks = [t for split in splits.values() for t in split.records]
    counts = {k: 4 for k in splits}
    a = make_manifest(tasks, splits, counts, 42)["selected"]
    b = make_manifest(list(reversed(tasks)), splits, counts, 42)["selected"]
    assert a == b
    ids = [tid for by_subject in a.values() for task_ids in by_subject.values() for tid in task_ids]
    assert len(ids) == len(set(ids))


def test_unrelated_label_matches_real_study_transfer_weight():
    transfer = StudyTransferEstimator()
    assert transfer.estimate("biology", "math").condition.value == "unrelated"
    assert transfer.estimate("biology", "math").tau == 0.0
    assert transfer.estimate("biology", "chemistry").condition.value == "related"


def test_wilson_interval_is_not_degenerate_for_five_of_five():
    lo, hi = wilson(5, 5)
    assert lo < 1.0
    assert hi == 1.0


def test_vote_tie_does_not_depend_on_agent_order():
    answers = {"qwen3-8b": "A", "gemma2": "B", "llama3-8b": "A", "qwen3-0.6b": "B"}
    x = choose_answer(answers, {}, "Uniform", "task_123")
    swapped = {agent: ("B" if answer == "A" else "A") for agent, answer in answers.items()}
    y = choose_answer(swapped, {}, "Uniform", "task_123")
    assert x == y
