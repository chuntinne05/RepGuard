"""RepGuard Reputation module — Week 2.

Implements the HistRepEval v0.1 evaluation protocol:
- EpisodeRecord: unit of historical interaction data
- FeedbackCorruptor: controlled noise/sparsity injection
- Reputation baselines: Uniform, GlobalBeta, SkillConditioned, Oracle, ZeroEvidenceGate
- TransferEstimator: task transferability strata
- Aggregator: majority vote & reputation-weighted aggregation
- Reputation metrics: ECE, ExpertLeverage, RankCorr
"""

from repguard.reputation.episode import DomainTransferCondition, EpisodeRecord
from repguard.reputation.feedback import FeedbackCorruptor, FeedbackRegime
from repguard.reputation.baselines import (
    GlobalBetaReputation,
    OracleReputation,
    SkillConditionedReputation,
    UniformReputation,
    ZeroEvidenceGate,
)
from repguard.reputation.transfer import TransferEstimator
from repguard.reputation.aggregator import AggregationResult, ReputationAggregator
from repguard.reputation.metrics import ReputationMetrics

__all__ = [
    "EpisodeRecord",
    "DomainTransferCondition",
    "FeedbackCorruptor",
    "FeedbackRegime",
    "GlobalBetaReputation",
    "OracleReputation",
    "SkillConditionedReputation",
    "UniformReputation",
    "ZeroEvidenceGate",
    "TransferEstimator",
    "AggregationResult",
    "ReputationAggregator",
    "ReputationMetrics",
]
