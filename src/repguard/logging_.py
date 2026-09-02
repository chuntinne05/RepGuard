"""Structured experiment logging for RepGuard.

Provides JSON-lines logging of every experiment action and LLM call,
plus CSV experiment registry updates. All entries include audit metadata:
timestamp, git commit, config hash, seed, model ID, prompt hash, task ID,
split, cost, latency, and result.
"""

from __future__ import annotations

import csv
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.logging import RichHandler

from repguard.config import RepGuardConfig


def setup_console_logging(level: str = "INFO") -> logging.Logger:
    """Configure rich console logging for the repguard package.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("repguard")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        console = Console(stderr=True)
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
        )
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        logger.addHandler(handler)

    return logger


class ExperimentLogger:
    """Structured JSON-lines logger for experiment tracking.

    Every call to log_event() writes a single JSON line to the experiment
    log file, capturing all audit metadata required for reproducibility.

    Attributes:
        log_dir: Directory where log files are written.
        experiment_name: Name of the current experiment.
        config_hash: Hash of the experiment configuration.
        git_commit: Current git commit hash.
    """

    def __init__(
        self,
        config: RepGuardConfig,
        log_dir: str | Path | None = None,
    ) -> None:
        """Initialize the experiment logger.

        Args:
            config: The experiment configuration.
            log_dir: Override for log directory (defaults to config value).
        """
        self._config = config
        self._config_hash = config.config_hash()
        self._git_commit = RepGuardConfig.get_git_commit()
        self._experiment_name = config.experiment.name
        self._seed = config.experiment.seed

        self.log_dir = Path(log_dir or config.logging.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._log_file = self.log_dir / f"experiment_{self._experiment_name}_{timestamp}.jsonl"
        self._start_time = time.monotonic()

        self._console_logger = setup_console_logging(config.logging.level)

        # Write initial config entry
        self.log_event(
            event_type="experiment_start",
            data={
                "config": config.model_dump(),
                "config_hash": self._config_hash,
                "git_commit": self._git_commit,
                "python_version": sys.version,
            },
        )

    @property
    def log_file(self) -> Path:
        """Path to the current log file."""
        return self._log_file

    def log_event(
        self,
        event_type: str,
        data: dict[str, Any] | None = None,
        *,
        task_id: str | None = None,
        split: str | None = None,
        model_id: str | None = None,
        prompt_hash: str | None = None,
        cost_usd: float | None = None,
        latency_ms: float | None = None,
    ) -> None:
        """Write a structured log entry as a JSON line.

        Args:
            event_type: Category of event (e.g., "llm_call", "evaluation", "error").
            data: Arbitrary event payload.
            task_id: Task identifier, if applicable.
            split: Data split (train_calibration, dev, test).
            model_id: LLM model identifier.
            prompt_hash: SHA-256 hash of the prompt.
            cost_usd: Estimated API cost in USD.
            latency_ms: Call latency in milliseconds.
        """
        entry: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "elapsed_seconds": round(time.monotonic() - self._start_time, 3),
            "experiment": self._experiment_name,
            "config_hash": self._config_hash,
            "git_commit": self._git_commit,
            "seed": self._seed,
            "event_type": event_type,
        }

        if task_id is not None:
            entry["task_id"] = task_id
        if split is not None:
            entry["split"] = split
        if model_id is not None:
            entry["model_id"] = model_id
        if prompt_hash is not None:
            entry["prompt_hash"] = prompt_hash
        if cost_usd is not None:
            entry["cost_usd"] = cost_usd
        if latency_ms is not None:
            entry["latency_ms"] = latency_ms
        if data is not None:
            entry["data"] = data

        with open(self._log_file, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def log_llm_call(
        self,
        task_id: str,
        split: str,
        model_id: str,
        prompt_hash: str,
        response_text: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: float,
        cached: bool = False,
    ) -> None:
        """Log a single LLM API call with full audit metadata.

        Args:
            task_id: Identifier for the task being evaluated.
            split: Data split name.
            model_id: Model identifier string.
            prompt_hash: SHA-256 hash of the formatted prompt.
            response_text: The model's response text (truncated for logging).
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            cost_usd: Estimated cost of this call.
            latency_ms: Round-trip latency in milliseconds.
            cached: Whether the response was served from cache.
        """
        self.log_event(
            event_type="llm_call",
            task_id=task_id,
            split=split,
            model_id=model_id,
            prompt_hash=prompt_hash,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            data={
                "response_preview": response_text[:200],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cached": cached,
            },
        )

    def log_evaluation(
        self,
        task_id: str,
        split: str,
        model_id: str,
        predicted: str,
        correct: str,
        is_correct: bool,
        domain: str,
    ) -> None:
        """Log an evaluation result for a single task.

        Args:
            task_id: Task identifier.
            split: Data split name.
            model_id: Model that produced the prediction.
            predicted: The predicted answer.
            correct: The ground-truth answer.
            is_correct: Whether the prediction matches GT.
            domain: Task domain/subject.
        """
        self.log_event(
            event_type="evaluation",
            task_id=task_id,
            split=split,
            model_id=model_id,
            data={
                "predicted": predicted,
                "correct": correct,
                "is_correct": is_correct,
                "domain": domain,
            },
        )

    def update_experiment_registry(
        self,
        registry_path: str | Path,
        metrics: dict[str, Any],
    ) -> None:
        """Append an entry to the CSV experiment registry.

        Args:
            registry_path: Path to the experiment_registry.csv file.
            metrics: Dictionary of result metrics to record.
        """
        registry_path = Path(registry_path)
        file_exists = registry_path.exists()

        row = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "experiment_name": self._experiment_name,
            "config_hash": self._config_hash,
            "git_commit": self._git_commit,
            "seed": self._seed,
            "model_id": self._config.provider.model_id,
            "provider": self._config.provider.name,
            **{f"metric_{k}": v for k, v in metrics.items()},
        }

        fieldnames = list(row.keys())

        with open(registry_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        self._console_logger.info(
            f"Registry updated: {registry_path} "
            f"(experiment={self._experiment_name}, hash={self._config_hash})"
        )

    def finalize(self) -> None:
        """Write the experiment completion entry."""
        elapsed = time.monotonic() - self._start_time
        self.log_event(
            event_type="experiment_end",
            data={"total_elapsed_seconds": round(elapsed, 3)},
        )
        self._console_logger.info(
            f"Experiment '{self._experiment_name}' completed in {elapsed:.1f}s. "
            f"Log: {self._log_file}"
        )
