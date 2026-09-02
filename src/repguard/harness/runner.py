"""Single-agent evaluation harness for RepGuard.

Orchestrates the complete evaluation pipeline:
1. Load tasks (from MMLU-Pro or synthetic data)
2. Create deterministic splits
3. Format prompts
4. Query LLM provider (with cache and rate limiting)
5. Parse responses
6. Score against ground truth (offline evaluator only)
7. Log results and compute metrics

Supports both dry-run (MockProvider) and live API modes, with seamless
switching via configuration.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from repguard.config import RepGuardConfig
from repguard.data.mmlu_pro import create_synthetic_tasks, load_mmlu_pro
from repguard.data.models import AgentResponse, TaskRecord
from repguard.data.splits import create_splits, verify_no_leakage
from repguard.evaluation.metrics import compute_accuracy, compute_per_domain_accuracy
from repguard.harness.cache import DiskCache
from repguard.harness.parser import parse_response
from repguard.harness.prompts import format_prompt
from repguard.harness.rate_limiter import RateLimiter
from repguard.logging_ import ExperimentLogger
from repguard.providers.base import LLMProvider, create_provider
from repguard.seed import SeedManager

logger = logging.getLogger("repguard")
console = Console()


class SingleAgentRunner:
    """Single-agent evaluation harness.

    Runs a single LLM agent against a set of multiple-choice tasks,
    collecting responses, parsing answers, and scoring against ground
    truth. Integrates with caching, rate limiting, and structured logging.

    The runner operates in two phases:
    1. **Generation**: Format prompts, query the provider, parse responses.
    2. **Evaluation**: Score parsed answers against ground truth (offline only).

    Example:
        >>> config = RepGuardConfig.from_yaml("configs/default.yaml")
        >>> runner = SingleAgentRunner(config)
        >>> results = runner.run()
    """

    def __init__(self, config: RepGuardConfig) -> None:
        """Initialize the runner with experiment configuration.

        Args:
            config: Validated experiment configuration.
        """
        self._config = config
        self._seed_manager = SeedManager(config.experiment.seed)

        # Initialize provider
        self._provider: LLMProvider = create_provider(config.provider)

        # Initialize cache
        self._cache = DiskCache(
            cache_dir=config.harness.cache.cache_dir,
            enabled=config.harness.cache.enabled,
        )

        # Initialize rate limiter
        self._rate_limiter = RateLimiter(
            requests_per_minute=config.harness.rate_limit.requests_per_minute,
            tokens_per_minute=config.harness.rate_limit.tokens_per_minute,
        )

        # Initialize logger
        self._exp_logger = ExperimentLogger(config)

    def run(
        self,
        tasks: list[TaskRecord] | None = None,
        split_name: str = "dev",
        max_tasks: int | None = None,
    ) -> RunResult:
        """Execute the full evaluation pipeline.

        If tasks are not provided, loads data from the configured source
        and creates splits. Evaluates tasks from the specified split.

        Args:
            tasks: Optional pre-loaded tasks. If None, loads from config.
            split_name: Which split to evaluate ("train_calibration", "dev", "test").
            max_tasks: Maximum tasks to evaluate (None = all in split).

        Returns:
            RunResult with responses, scores, and aggregate metrics.
        """
        console.print("\n[bold cyan]═══ RepGuard Single-Agent Evaluation ═══[/bold cyan]\n")

        # Step 1: Load data
        if tasks is None:
            tasks = self._load_data()

        # Step 2: Create splits
        train_cal, dev, test = create_splits(
            tasks,
            self._seed_manager,
            self._config.data.splits.train_calibration_ratio,
            self._config.data.splits.dev_ratio,
            self._config.data.splits.test_ratio,
        )
        verify_no_leakage(train_cal, dev, test)

        # Select the target split
        split_map = {"train_calibration": train_cal, "dev": dev, "test": test}
        target_split = split_map.get(split_name)
        if target_split is None:
            msg = f"Unknown split: '{split_name}'. Use 'train_calibration', 'dev', or 'test'."
            raise ValueError(msg)

        eval_tasks = list(target_split.records)
        if max_tasks is not None:
            eval_tasks = eval_tasks[:max_tasks]

        console.print(f"[green]Split sizes:[/green] "
                      f"train_cal={train_cal.size}, dev={dev.size}, test={test.size}")
        console.print(f"[green]Evaluating:[/green] {len(eval_tasks)} tasks from '{split_name}'\n")

        self._exp_logger.log_event(
            event_type="evaluation_start",
            data={
                "split": split_name,
                "num_tasks": len(eval_tasks),
                "provider": self._config.provider.name,
                "model_id": self._config.provider.model_id,
            },
        )

        # Step 3: Evaluate each task
        responses: list[AgentResponse] = []
        scores: list[bool] = []

        for i, task in enumerate(eval_tasks):
            response = self._evaluate_task(task, split_name)
            responses.append(response)

            is_correct = task.check_answer(response.parsed_answer)
            scores.append(is_correct)

            self._exp_logger.log_evaluation(
                task_id=task.task_id,
                split=split_name,
                model_id=self._config.provider.model_id,
                predicted=response.parsed_answer,
                correct=task.ground_truth_answer,
                is_correct=is_correct,
                domain=task.metadata.subject,
            )

            if (i + 1) % 10 == 0 or (i + 1) == len(eval_tasks):
                running_acc = sum(scores) / len(scores)
                console.print(
                    f"  [{i+1}/{len(eval_tasks)}] "
                    f"Running accuracy: {running_acc:.1%}"
                )

        # Step 4: Compute metrics
        accuracy = compute_accuracy(scores)
        per_domain = compute_per_domain_accuracy(eval_tasks, scores)

        result = RunResult(
            responses=responses,
            scores=scores,
            accuracy=accuracy,
            per_domain_accuracy=per_domain,
            split_name=split_name,
            num_tasks=len(eval_tasks),
            provider_stats=self._provider.get_stats(),
            cache_stats=self._cache.get_stats(),
        )

        # Print results table
        self._print_results(result)

        # Log completion
        self._exp_logger.log_event(
            event_type="evaluation_complete",
            data={
                "accuracy": accuracy,
                "num_tasks": len(eval_tasks),
                "provider_stats": self._provider.get_stats(),
                "cache_stats": self._cache.get_stats(),
            },
        )

        self._exp_logger.finalize()
        return result

    def _load_data(self) -> list[TaskRecord]:
        """Load tasks from the configured data source.

        Uses synthetic data for dry-run mode, real MMLU-Pro otherwise.

        Returns:
            List of TaskRecord objects.
        """
        if self._config.provider.name == "mock":
            console.print("[yellow]Mock provider: using synthetic tasks[/yellow]")
            return create_synthetic_tasks(
                n=self._config.data.max_tasks or 50,
                seed=self._config.experiment.seed,
            )
        else:
            return load_mmlu_pro(
                data_dir=self._config.data.data_dir,
                dataset_id=self._config.data.dataset,
                max_tasks=self._config.data.max_tasks,
            )

    def _evaluate_task(self, task: TaskRecord, split_name: str) -> AgentResponse:
        """Evaluate a single task: format → query → parse.

        Args:
            task: The task to evaluate.
            split_name: Current split name for logging.

        Returns:
            AgentResponse with the parsed answer and metadata.
        """
        # Format prompt (uses only question + options, never GT)
        formatted = format_prompt(task, mode=self._config.harness.prompt_mode)

        # Check cache
        cache_key = DiskCache.make_key(
            model_id=self._config.provider.model_id,
            prompt_hash=formatted.prompt_hash,
            temperature=self._config.provider.parameters.temperature,
            max_tokens=self._config.provider.parameters.max_tokens,
            top_p=self._config.provider.parameters.top_p,
        )

        cached_response = self._cache.get(cache_key)

        if cached_response is not None:
            response = cached_response
        else:
            # Rate limit and query provider
            self._rate_limiter.wait_if_needed(
                estimated_tokens=self._config.provider.parameters.max_tokens
            )

            response = self._provider.complete(
                formatted.text,
                temperature=self._config.provider.parameters.temperature,
                max_tokens=self._config.provider.parameters.max_tokens,
                top_p=self._config.provider.parameters.top_p,
            )

            # Cache the response
            self._cache.put(cache_key, response)
            self._rate_limiter.record_request(response.total_tokens)

        # Log the LLM call
        self._exp_logger.log_llm_call(
            task_id=task.task_id,
            split=split_name,
            model_id=response.model_id,
            prompt_hash=formatted.prompt_hash,
            response_text=response.content,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=response.cost_usd,
            latency_ms=response.latency_ms,
            cached=response.cached,
        )

        # Parse the answer
        parse_result = parse_response(response.content, num_options=formatted.num_options)

        return AgentResponse(
            agent_id=f"agent_{self._config.provider.model_id}",
            task_id=task.task_id,
            raw_response=response.content,
            parsed_answer=parse_result.answer,
            model_id=response.model_id,
            prompt_hash=formatted.prompt_hash,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            latency_ms=response.latency_ms,
            cost_usd=response.cost_usd,
            cached=response.cached,
        )

    def _print_results(self, result: RunResult) -> None:
        """Print a formatted results table to the console.

        Args:
            result: The evaluation results to display.
        """
        console.print("\n[bold cyan]═══ Results ═══[/bold cyan]\n")

        # Overall accuracy
        console.print(f"[bold]Overall Accuracy:[/bold] {result.accuracy:.1%} "
                      f"({sum(result.scores)}/{result.num_tasks})")

        # Per-domain table
        if result.per_domain_accuracy:
            table = Table(title="Per-Domain Accuracy")
            table.add_column("Domain", style="cyan")
            table.add_column("Accuracy", justify="right", style="green")
            table.add_column("Correct / Total", justify="right")

            for domain, stats in sorted(result.per_domain_accuracy.items()):
                table.add_row(
                    domain,
                    f"{stats['accuracy']:.1%}",
                    f"{stats['correct']}/{stats['total']}",
                )

            console.print(table)

        # Provider stats
        stats = result.provider_stats
        console.print(f"\n[dim]Provider: {stats.get('provider', '?')} "
                      f"| Model: {stats.get('model_id', '?')} "
                      f"| Calls: {stats.get('total_calls', 0)} "
                      f"| Cost: ${stats.get('total_cost_usd', 0):.4f}[/dim]")

        # Cache stats
        cache = result.cache_stats
        console.print(f"[dim]Cache: hits={cache.get('hits', 0)} "
                      f"misses={cache.get('misses', 0)} "
                      f"hit_rate={cache.get('hit_rate', 0):.0%}[/dim]\n")


class RunResult:
    """Container for evaluation results.

    Attributes:
        responses: List of AgentResponse objects.
        scores: List of boolean scores (correct/incorrect).
        accuracy: Overall accuracy fraction.
        per_domain_accuracy: Per-domain accuracy breakdown.
        split_name: Name of the evaluated split.
        num_tasks: Number of tasks evaluated.
        provider_stats: Provider usage statistics.
        cache_stats: Cache usage statistics.
    """

    def __init__(
        self,
        responses: list[AgentResponse],
        scores: list[bool],
        accuracy: float,
        per_domain_accuracy: dict[str, dict[str, int | float]],
        split_name: str,
        num_tasks: int,
        provider_stats: dict,
        cache_stats: dict,
    ) -> None:
        self.responses = responses
        self.scores = scores
        self.accuracy = accuracy
        self.per_domain_accuracy = per_domain_accuracy
        self.split_name = split_name
        self.num_tasks = num_tasks
        self.provider_stats = provider_stats
        self.cache_stats = cache_stats


def main() -> None:
    """CLI entry point for the single-agent evaluation harness."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="RepGuard Single-Agent Evaluation Harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="configs/default.yaml",
        help="Path to experiment configuration YAML file",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="dev",
        choices=["train_calibration", "dev", "test"],
        help="Which data split to evaluate",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=None,
        help="Maximum number of tasks to evaluate",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Force mock provider for dry-run testing",
    )

    args = parser.parse_args()

    try:
        config = RepGuardConfig.from_yaml(args.config)
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {args.config}[/red]")
        sys.exit(1)

    # Override provider for dry-run
    if args.dry_run:
        config.provider.name = "mock"  # type: ignore[misc]
        config.provider.model_id = "mock-model-v1"  # type: ignore[misc]

    runner = SingleAgentRunner(config)
    result = runner.run(
        split_name=args.split,
        max_tasks=args.max_tasks,
    )

    sys.exit(0 if result.accuracy >= 0.0 else 1)


if __name__ == "__main__":
    main()
