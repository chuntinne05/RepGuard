"""RepGuard Reputation module — Week 2–3.

Implements the HistRepEval v0.1–v0.2 evaluation protocol:
- EpisodeRecord: unit of historical interaction data
- FeedbackCorruptor: controlled noise/sparsity injection
- Reputation baselines: Uniform, GlobalBeta, SkillConditioned, Oracle, ZeroEvidenceGate
- TransferEstimator: task transferability strata (τ weights)
- Aggregator: majority vote & reputation-weighted aggregation
- Reputation metrics: ECE, ExpertLeverage, RankCorr, BrierScore, NLL
- ECRT: Evidence-Calibrated Reputation Transfer (Week 3 core method)
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
from repguard.reputation.metrics import MetricsResult, ReputationMetrics
from repguard.reputation.ecrt import (
    ECRTReputation,
    FeedbackReliabilityEstimator,
    FeedbackReliabilityParams,
    build_ecrt_variants,
)

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
    "MetricsResult",
    "ReputationMetrics",
    # Week 3 — ECRT
    "ECRTReputation",
    "FeedbackReliabilityEstimator",
    "FeedbackReliabilityParams",
    "build_ecrt_variants",
]
