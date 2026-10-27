"""Independent dev validation must never reuse Week 3 calibration questions."""

from run_real_week5_validation import select_unused_dev


def test_dev_selection_is_deterministic_and_excludes_prior_calibration():
    class Task:
        def __init__(self, task_id, subject):
            self.task_id = task_id
            self.metadata = type("Metadata", (), {"subject": subject})()

    class Split:
        records = [Task(f"bio{i}", "biology") for i in range(8)] + [
            Task(f"law{i}", "law") for i in range(8)]

    old = {"selected": {"dev": {"biology": ["bio0", "bio1"],
                                "law": ["law0", "law1"]}}}
    a = select_unused_dev({"dev": Split()}, old, per_subject=4, seed=42)
    b = select_unused_dev({"dev": Split()}, old, per_subject=4, seed=42)
    assert a == b
    assert set(a["biology"]).isdisjoint(old["selected"]["dev"]["biology"])
    assert set(a["law"]).isdisjoint(old["selected"]["dev"]["law"])
    assert all(len(ids) == 4 for ids in a.values())
