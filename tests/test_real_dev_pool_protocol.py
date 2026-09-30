"""Protocol checks for fresh development collection without holdout inference."""

import pytest

from run_real_dev_pool import VARIANTS, make_manifest


def fake_frozen(overlap: bool = False):
    subjects = [f"subject_{i}" for i in range(14)]
    development = {subject: [f"dev_{i}_{j}" for j in range(40)]
                   for i, subject in enumerate(subjects)}
    holdout = {subject: [f"hold_{i}_{j}" for j in range(30)]
               for i, subject in enumerate(subjects)}
    if overlap:
        holdout[subjects[0]][0] = development[subjects[0]][0]
    return {"protocol_hash": "source-hash", "dataset_id": "test",
            "dataset_task_id_sha256": "dataset-hash",
            "selected": {"development": development, "holdout": holdout}}


def test_development_manifest_excludes_holdout_ids():
    digests = {settings["model_id"]: "digest" for settings in VARIANTS.values()}
    result = make_manifest(fake_frozen(), "0.34.4", digests)
    assert result["holdout_read_for_inference"] is False
    assert "holdout" not in result
    assert set(result["selected_development_ids"]) == set(fake_frozen()["selected"]["development"])


def test_development_manifest_rejects_holdout_overlap():
    with pytest.raises(RuntimeError, match="overlaps sealed holdout"):
        make_manifest(fake_frozen(overlap=True), "0.34.4", {})
