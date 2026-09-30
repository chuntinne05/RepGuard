"""The context diagnostic selection is fixed from IDs, without outcomes."""

from run_real_dev_context_pilot import selected_ids


def test_context_pilot_selects_five_fixed_ids_per_subject():
    subjects = [f"subject_{i}" for i in range(14)]
    frozen = {"selected": {"development": {
        name: [f"{name}_{j}" for j in range(40)] for name in subjects}}}
    first = selected_ids(frozen)
    second = selected_ids(frozen)
    assert first == second
    assert len(first) == 14
    assert all(len(ids) == 5 for ids in first.values())
    assert len({task_id for ids in first.values() for task_id in ids}) == 70
