"""Pydantic-based experiment configuration schema for RepGuard.

Provides hierarchical, validated configuration with YAML loading,
git-commit capture, and deterministic hashing for experiment tracking.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class ExperimentConfig(BaseModel):
    """Top-level experiment metadata."""

    name: str = Field(default="default", description="Human-readable experiment name")
    description: str = Field(default="", description="Experiment description")
    seed: int = Field(default=42, ge=0, description="Master random seed")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering")


class SplitConfig(BaseModel):
    """Data split ratios — must sum to 1.0."""

    train_calibration_ratio: float = Field(
        default=0.6, gt=0.0, lt=1.0, description="Fraction for train/calibration"
    )
    dev_ratio: float = Field(
        default=0.2, gt=0.0, lt=1.0, description="Fraction for development"
    )
    test_ratio: float = Field(
        default=0.2, gt=0.0, lt=1.0, description="Fraction for held-out test"
    )

    @field_validator("test_ratio")
    @classmethod
    def ratios_must_sum_to_one(cls, v: float, info: Any) -> float:
        """Validate that all split ratios sum to 1.0 (within tolerance)."""
        data = info.data
        total = data.get("train_calibration_ratio", 0.6) + data.get("dev_ratio", 0.2) + v
        if abs(total - 1.0) > 1e-6:
            msg = f"Split ratios must sum to 1.0, got {total:.6f}"
            raise ValueError(msg)
        return v


class DataConfig(BaseModel):
    """Dataset loading and splitting configuration."""

    dataset: str = Field(default="TIGER-Lab/MMLU-Pro", description="HuggingFace dataset ID")
    data_dir: str = Field(default="./data", description="Local data directory")
    splits: SplitConfig = Field(default_factory=SplitConfig)
    max_tasks: int | None = Field(
        default=None, ge=1, description="Max tasks to load (None = all)"
    )


class ProviderParams(BaseModel):
    """LLM generation parameters."""

    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=16384)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)


class ProviderConfig(BaseModel):
    """LLM provider configuration."""

    name: str = Field(default="mock", description="Provider name: mock, openai, anthropic")
    model_id: str = Field(default="mock-model-v1", description="Model identifier")
    parameters: ProviderParams = Field(default_factory=ProviderParams)

    @field_validator("name")
    @classmethod
    def validate_provider_name(cls, v: str) -> str:
        """Ensure provider name is one of the supported values."""
        allowed = {"mock", "openai", "anthropic"}
        if v not in allowed:
            msg = f"Provider must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return v


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    requests_per_minute: int = Field(default=60, ge=1)
    tokens_per_minute: int = Field(default=100_000, ge=1)


class RetryConfig(BaseModel):
    """Retry configuration for transient failures."""

    max_attempts: int = Field(default=3, ge=1)
    min_wait_seconds: float = Field(default=1.0, ge=0.1)
    max_wait_seconds: float = Field(default=60.0, ge=1.0)


class CacheConfig(BaseModel):
    """Disk cache configuration for LLM responses."""

    enabled: bool = Field(default=True)
    cache_dir: str = Field(default="./.llm_cache")


class HarnessConfig(BaseModel):
    """Single-agent evaluation harness configuration."""

    prompt_mode: str = Field(
        default="direct",
        description="Prompt mode: 'direct' or 'cot' (chain-of-thought)",
    )
    batch_size: int = Field(default=10, ge=1)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

    @field_validator("prompt_mode")
    @classmethod
    def validate_prompt_mode(cls, v: str) -> str:
        """Ensure prompt mode is valid."""
        allowed = {"direct", "cot"}
        if v not in allowed:
            msg = f"prompt_mode must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return v


class LoggingConfig(BaseModel):
    """Structured logging configuration."""

    log_dir: str = Field(default="./logs")
    level: str = Field(default="INFO")
    structured: bool = Field(default=True, description="Write JSON-lines experiment log")


class FeedbackConfig(BaseModel):
    """Feedback regime configuration (Week 2+)."""

    regime: str = Field(default="oracle")
    noise_eta: float = Field(default=0.0, ge=0.0, le=1.0)
    sparsity_rho: float = Field(default=1.0, ge=0.0, le=1.0)


class TransferConfig(BaseModel):
    """Transfer condition configuration (Week 2+)."""

    condition: str = Field(default="same")


class AgentPoolConfig(BaseModel):
    """Agent pool configuration (Week 2+)."""

    pool: list[dict[str, Any]] = Field(default_factory=list)


class RepGuardConfig(BaseModel):
    """Root configuration schema for RepGuard experiments.

    Provides hierarchical, validated configuration that can be loaded
    from YAML files and enriched with runtime metadata (git commit hash,
    config hash) for full experiment reproducibility.
    """

    experiment: ExperimentConfig = Field(default_factory=ExperimentConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    harness: HarnessConfig = Field(default_factory=HarnessConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    feedback: FeedbackConfig = Field(default_factory=FeedbackConfig)
    transfer: TransferConfig = Field(default_factory=TransferConfig)
    agents: AgentPoolConfig = Field(default_factory=AgentPoolConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> RepGuardConfig:
        """Load configuration from a YAML file.

        Args:
            path: Path to the YAML configuration file.

        Returns:
            Validated RepGuardConfig instance.

        Raises:
            FileNotFoundError: If the config file does not exist.
            yaml.YAMLError: If the YAML is malformed.
            pydantic.ValidationError: If the config fails validation.
        """
        path = Path(path)
        if not path.exists():
            msg = f"Configuration file not found: {path}"
            raise FileNotFoundError(msg)

        with open(path) as f:
            raw = yaml.safe_load(f)

        if raw is None:
            raw = {}

        return cls.model_validate(raw)

    def config_hash(self) -> str:
        """Compute a deterministic SHA-256 hash of this configuration.

        Useful for uniquely identifying experiment configurations in logs
        and cache keys.

        Returns:
            Hex-encoded SHA-256 hash string.
        """
        json_bytes = self.model_dump_json(indent=None).encode("utf-8")
        return hashlib.sha256(json_bytes).hexdigest()[:16]

    @staticmethod
    def get_git_commit() -> str:
        """Capture the current git commit hash, or 'unknown' if not in a git repo.

        Returns:
            Short git commit hash or 'unknown'.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return "unknown"
