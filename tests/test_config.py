"""Tests for configuration schema."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from repguard.config import RepGuardConfig


class TestRepGuardConfig:
    """Tests for the RepGuardConfig Pydantic model."""

    def test_default_config_is_valid(self) -> None:
        """Default config should pass validation."""
        config = RepGuardConfig()
        assert config.experiment.seed == 42
        assert config.provider.name == "mock"
        assert config.data.dataset == "TIGER-Lab/MMLU-Pro"

    def test_from_yaml(self, tmp_path: Path) -> None:
        """Config should load correctly from a YAML file."""
        yaml_content = {
            "experiment": {"name": "test_exp", "seed": 123},
            "provider": {"name": "mock", "model_id": "mock-v2"},
        }
        yaml_path = tmp_path / "test_config.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(yaml_content, f)

        config = RepGuardConfig.from_yaml(yaml_path)
        assert config.experiment.name == "test_exp"
        assert config.experiment.seed == 123
        assert config.provider.model_id == "mock-v2"

    def test_from_yaml_file_not_found(self) -> None:
        """Loading from nonexistent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            RepGuardConfig.from_yaml("/nonexistent/path/config.yaml")

    def test_invalid_provider_name(self) -> None:
        """Invalid provider name should raise ValidationError."""
        with pytest.raises(Exception):
            RepGuardConfig(
                provider={"name": "invalid_provider"}  # type: ignore[arg-type]
            )

    def test_split_ratios_must_sum_to_one(self) -> None:
        """Split ratios not summing to 1.0 should raise ValidationError."""
        with pytest.raises(Exception):
            RepGuardConfig(
                data={"splits": {  # type: ignore[arg-type]
                    "train_calibration_ratio": 0.5,
                    "dev_ratio": 0.3,
                    "test_ratio": 0.3,
                }}
            )

    def test_config_hash_is_deterministic(self) -> None:
        """Same config should always produce the same hash."""
        config1 = RepGuardConfig()
        config2 = RepGuardConfig()
        assert config1.config_hash() == config2.config_hash()

    def test_config_hash_changes_with_seed(self) -> None:
        """Different seeds should produce different hashes."""
        from repguard.config import ExperimentConfig
        config1 = RepGuardConfig(experiment=ExperimentConfig(name="a", seed=1))
        config2 = RepGuardConfig(experiment=ExperimentConfig(name="a", seed=2))
        assert config1.config_hash() != config2.config_hash()

    def test_get_git_commit_returns_string(self) -> None:
        """git commit capture should return a string (even if not in a repo)."""
        commit = RepGuardConfig.get_git_commit()
        assert isinstance(commit, str)
        assert len(commit) > 0
