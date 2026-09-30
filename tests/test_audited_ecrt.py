"""Tests for the experimental audited feedback channel."""

import pytest

from repguard.reputation.audited import AuditedECRTReputation
from repguard.reputation.episode import EpisodeRecord


def episode(agent: str, index: int, correct: bool, feedback: float,
            domain: str = "biology") -> EpisodeRecord:
    return EpisodeRecord(
        episode_id=f"{agent}:{index}", agent_id=agent, task_id=str(index),
        domain=domain, agent_answer="A" if correct else "B",
        _ground_truth="A", observed_feedback=feedback,
    )


def test_uninformative_feedback_falls_back_to_disjoint_audit():
    audited = [episode("a", i, i < 20, float(i % 2)) for i in range(40)]
    history = [episode("a", i + 100, False, 1.0) for i in range(20)]
    model = AuditedECRTReputation().fit(history, audited)
    channel = model.channel("a", "biology")
    assert channel is not None
    assert channel.conservative_signal == 0.0
    assert model.score("a", "biology").mean == pytest.approx(0.5)
    assert model.score("a", "biology").evidence_count == pytest.approx(40)


def test_channels_are_agent_specific_under_targeted_false_positives():
    clean = [episode("clean", i, i < 20, float(i < 20)) for i in range(40)]
    attacked = [episode("attacked", i, i < 20,
                        float(i < 20 or (i >= 20 and i % 2 == 0)))
                for i in range(40)]
    model = AuditedECRTReputation().fit([], clean + attacked)
    clean_channel = model.channel("clean", "biology")
    attacked_channel = model.channel("attacked", "biology")
    assert clean_channel is not None and attacked_channel is not None
    assert attacked_channel.specificity < clean_channel.specificity
    assert attacked_channel.correctness_given(True) < clean_channel.correctness_given(True)


def test_unrelated_history_and_audits_have_zero_transfer():
    model = AuditedECRTReputation().fit(
        [episode("a", 100, True, 1.0)],
        [episode("a", i, True, 1.0) for i in range(10)],
    )
    assert model.score("a", "law").mean == pytest.approx(0.5)
    assert model.score("a", "law").evidence_count == pytest.approx(0)


def test_history_and_audit_cannot_share_agent_task_id():
    row = episode("a", 1, True, 1.0)
    with pytest.raises(ValueError, match="disjoint"):
        AuditedECRTReputation().fit([row], [row])
