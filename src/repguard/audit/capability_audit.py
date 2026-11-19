"""Capability Audit module for RepGuard — Step 1.1 (Week 1 exit gate).

Runs each agent in the configured pool against a stratified sample of
MMLU-Pro tasks across domains, then produces a Domain × Agent capability
matrix and runs the Heterogeneity Gate check required before Week 2.

Usage (CLI):
    python -m repguard.audit.capability_audit \\
        --config configs/capability_audit.yaml \\
        --output results/capability_audit/

Usage (Python):
    from repguard.audit.capability_audit import CapabilityAudit
    from repguard.audit.capability_audit import CapabilityAuditConfig

    cfg = CapabilityAuditConfig.from_yaml("configs/capability_audit.yaml")
    audit = CapabilityAudit(cfg)
    matrix = audit.run()
    matrix.print_report()
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from repguard.config import ProviderConfig, ProviderParams
from repguard.data.mmlu_pro import create_synthetic_tasks, load_mmlu_pro
from repguard.data.models import TaskRecord
from repguard.data.splits import create_splits
from repguard.evaluation.metrics import bootstrap_confidence_interval, compute_accuracy
from repguard.harness.cache import DiskCache
from repguard.harness.parser import parse_response
from repguard.harness.prompts import format_prompt
from repguard.harness.rate_limiter import RateLimiter
from repguard.providers.base import LLMProvider, create_provider
from repguard.seed import SeedManager

logger = logging.getLogger("repguard")
console = Console()

# Heterogeneity gate thresholds
_MIN_DOMAINS_BEST_CHANGES = 2   # best agent must flip across at least this many domain pairs
_MIN_PERFORMANCE_SPREAD = 0.10  # max - min average accuracy across agents


# ─────────────────────────────────────────────────────────────────────────────
# Configuration models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentConfig:
    """Configuration for one agent in the capability audit pool.

    Attributes:
        name: Human-readable agent label (used in reports and CSV output).
        provider: Provider name (``mock``, ``gemini``, ``openai``, ``anthropic``, ``ollama``).
        model_id: Model identifier string sent to the provider API.
        base_url: Optional endpoint override for local or hosted Ollama.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.
        top_p: Top-p sampling parameter.
        api_key_env: Name of the environment variable holding the API key.
            Leave empty for ``mock`` provider (no key needed).
        requests_per_minute: Rate limit for this agent.
        tokens_per_minute: Token rate limit for this agent.
        cache_dir: Directory for on-disk LLM response cache.
    """

    name: str
    provider: str
    model_id: str
    base_url: str | None = None
    temperature: float = 0.0
    max_tokens: int = 512
    top_p: float = 1.0
    api_key_env: str = ""
    requests_per_minute: int = 60
    tokens_per_minute: int = 100_000
    cache_dir: str = "./.llm_cache"

    def to_provider_config(self) -> ProviderConfig:
        """Convert to a ProviderConfig understood by create_provider()."""
        return ProviderConfig(
            name=self.provider,
            model_id=self.model_id,
            parameters=ProviderParams(
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
            ),
        )


@dataclass
class CapabilityAuditConfig:
    """Full configuration for a capability audit run.

    Attributes:
        seed: Master random seed for reproducibility.
        n_samples_per_domain: Number of tasks sampled per subject/domain.
        domains: Subjects to include (empty = all subjects found in data).
        prompt_mode: ``direct`` or ``cot``.
        use_synthetic: If True, use synthetic tasks instead of MMLU-Pro.
        synthetic_n: Total synthetic tasks to generate (when use_synthetic=True).
        data_dir: Local directory for MMLU-Pro cache (real data mode).
        dataset_id: HuggingFace dataset identifier for MMLU-Pro.
        output_dir: Directory where audit results are written.
        agents: List of AgentConfig objects defining the agent pool.
    """

    seed: int = 42
    n_samples_per_domain: int = 10
    domains: list[str] = field(default_factory=list)
    prompt_mode: str = "direct"
    use_synthetic: bool = False
    synthetic_n: int = 200
    data_dir: str = "./data"
    dataset_id: str = "TIGER-Lab/MMLU-Pro"
    output_dir: str = "./results/capability_audit"
    agents: list[AgentConfig] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: str | Path) -> CapabilityAuditConfig:
        """Load capability audit configuration from a YAML file.

        Args:
            path: Path to the audit YAML config file.

        Returns:
            CapabilityAuditConfig instance.

        Raises:
            FileNotFoundError: If the config file does not exist.
            KeyError / ValueError: On malformed config.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Audit config not found: {path}")

        with open(path) as fh:
            raw = yaml.safe_load(fh) or {}

        audit_raw = raw.get("audit", {})
        agents_raw = raw.get("agents", [])

        agents = []
        for a in agents_raw:
            agents.append(AgentConfig(
                name=a["name"],
                provider=a["provider"],
                model_id=a["model_id"],
                base_url=a.get("base_url"),
                temperature=float(a.get("temperature", 0.0)),
                max_tokens=int(a.get("max_tokens", 512)),
                top_p=float(a.get("top_p", 1.0)),
                api_key_env=a.get("api_key_env", ""),
                requests_per_minute=int(a.get("requests_per_minute", 60)),
                tokens_per_minute=int(a.get("tokens_per_minute", 100_000)),
                cache_dir=a.get("cache_dir", "./.llm_cache"),
            ))

        return cls(
            seed=int(audit_raw.get("seed", 42)),
            n_samples_per_domain=int(audit_raw.get("n_samples_per_domain", 10)),
            domains=list(audit_raw.get("domains", [])),
            prompt_mode=str(audit_raw.get("prompt_mode", "direct")),
            use_synthetic=bool(audit_raw.get("use_synthetic", False)),
            synthetic_n=int(audit_raw.get("synthetic_n", 200)),
            data_dir=str(audit_raw.get("data_dir", "./data")),
            dataset_id=str(audit_raw.get("dataset_id", "TIGER-Lab/MMLU-Pro")),
            output_dir=str(audit_raw.get("output_dir", "./results/capability_audit")),
            agents=agents,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentDomainResult:
    """Per-agent, per-domain evaluation outcome.

    Attributes:
        agent_name: Agent identifier.
        domain: MMLU-Pro subject/domain name.
        n_tasks: Number of tasks evaluated.
        n_correct: Number of correct predictions.
        accuracy: Fraction correct.
        ci_lower: Bootstrap 95% CI lower bound.
        ci_upper: Bootstrap 95% CI upper bound.
        total_cost_usd: Estimated API cost for this domain.
        total_latency_ms: Cumulative latency.
    """

    agent_name: str
    domain: str
    n_tasks: int
    n_correct: int
    accuracy: float
    ci_lower: float
    ci_upper: float
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0


@dataclass
class CapabilityMatrix:
    """Full capability audit output: the Domain × Agent accuracy matrix.

    Attributes:
        agents: Ordered list of agent names.
        domains: Ordered list of domain/subject names.
        results: Nested dict ``results[agent_name][domain]`` → AgentDomainResult.
        seed: Master seed used.
        n_samples_per_domain: Samples per domain (target).
        timestamp: ISO-8601 audit timestamp.
        heterogeneity: HeterogeneityGateResult with Go/No-Go decision.
    """

    agents: list[str]
    domains: list[str]
    results: dict[str, dict[str, AgentDomainResult]]
    seed: int
    n_samples_per_domain: int
    timestamp: str
    heterogeneity: HeterogeneityGateResult

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    def accuracy_for(self, agent: str, domain: str) -> float | None:
        """Return accuracy or None if not available."""
        r = self.results.get(agent, {}).get(domain)
        return r.accuracy if r is not None else None

    def best_agent_per_domain(self) -> dict[str, str]:
        """Return the name of the best-performing agent for each domain."""
        best: dict[str, str] = {}
        for domain in self.domains:
            best_acc = -1.0
            best_name = ""
            for agent in self.agents:
                acc = self.accuracy_for(agent, domain) or 0.0
                if acc > best_acc:
                    best_acc = acc
                    best_name = agent
            best[domain] = best_name
        return best

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def print_report(self) -> None:
        """Print a rich formatted capability matrix report to the console."""
        console.print()
        console.print(Panel.fit(
            "[bold cyan]RepGuard — Capability Audit Report[/bold cyan]\n"
            "[dim]Heterogeneity Gate · Week 1 Exit Criterion · OQ-1[/dim]",
            border_style="cyan",
        ))

        # --- Domain × Agent accuracy table ---
        table = Table(
            title=f"Domain × Agent Accuracy  (seed={self.seed}, "
                  f"n_per_domain≈{self.n_samples_per_domain})",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Domain", style="cyan", min_width=20)
        for agent in self.agents:
            table.add_column(agent, justify="right")

        best_per_domain = self.best_agent_per_domain()

        for domain in self.domains:
            row: list[str] = [domain]
            for agent in self.agents:
                acc = self.accuracy_for(agent, domain)
                if acc is None:
                    row.append("[dim]—[/dim]")
                else:
                    is_best = best_per_domain.get(domain) == agent
                    star = " ★" if is_best else ""
                    row.append(f"[bold]{acc:.1%}[/bold]{star}" if is_best else f"{acc:.1%}")
            table.add_row(*row)

        console.print(table)

        # --- Summary row (mean across domains) ---
        console.print()
        summary_table = Table(show_header=True, header_style="bold")
        summary_table.add_column("Agent")
        summary_table.add_column("Mean Accuracy", justify="right")
        summary_table.add_column("Total Cost (USD)", justify="right")
        summary_table.add_column("Best-in Domain", justify="right")

        for agent in self.agents:
            accs = [
                self.accuracy_for(agent, d)
                for d in self.domains
                if self.accuracy_for(agent, d) is not None
            ]
            mean_acc = sum(accs) / len(accs) if accs else 0.0
            total_cost = sum(
                self.results.get(agent, {}).get(d, AgentDomainResult(
                    agent, d, 0, 0, 0.0, 0.0, 0.0
                )).total_cost_usd
                for d in self.domains
            )
            n_best = sum(
                1 for d in self.domains if best_per_domain.get(d) == agent
            )
            summary_table.add_row(
                agent, f"{mean_acc:.1%}", f"${total_cost:.4f}", str(n_best)
            )
        console.print(summary_table)

        # --- Heterogeneity gate ---
        gate = self.heterogeneity
        console.print()
        gate_color = "green" if gate.passed else "red"
        gate_status = "PASS ✓" if gate.passed else "FAIL ✗"
        console.print(Panel(
            f"[bold]Heterogeneity Gate: [{gate_color}]{gate_status}[/{gate_color}][/bold]\n\n"
            + "\n".join(f"  • {line}" for line in gate.reason_lines),
            title="OQ-1: Model Pool Composition",
            border_style=gate_color,
        ))

    def to_dict(self) -> dict[str, Any]:
        """Serialise the capability matrix to a JSON-friendly dictionary."""
        results_ser: dict[str, dict[str, Any]] = {}
        for agent, dom_map in self.results.items():
            results_ser[agent] = {}
            for domain, r in dom_map.items():
                results_ser[agent][domain] = {
                    "n_tasks": r.n_tasks,
                    "n_correct": r.n_correct,
                    "accuracy": round(r.accuracy, 4),
                    "ci_lower": round(r.ci_lower, 4),
                    "ci_upper": round(r.ci_upper, 4),
                    "total_cost_usd": round(r.total_cost_usd, 6),
                }
        return {
            "timestamp": self.timestamp,
            "seed": self.seed,
            "n_samples_per_domain": self.n_samples_per_domain,
            "agents": self.agents,
            "domains": self.domains,
            "results": results_ser,
            "heterogeneity": {
                "passed": self.heterogeneity.passed,
                "n_domains_best_changes": self.heterogeneity.n_domains_best_changes,
                "performance_spread": round(self.heterogeneity.performance_spread, 4),
                "reason_lines": self.heterogeneity.reason_lines,
            },
        }


@dataclass
class HeterogeneityGateResult:
    """Outcome of the heterogeneity gate check.

    The gate passes when:
    1. The best agent changes across at least ``_MIN_DOMAINS_BEST_CHANGES``
       distinct domain pairs (i.e., no single model dominates every domain).
    2. The performance spread (max mean − min mean across agents) exceeds
       ``_MIN_PERFORMANCE_SPREAD``.

    Attributes:
        passed: True if the pool is sufficiently heterogeneous.
        n_domains_best_changes: How many domain pairs have different winners.
        performance_spread: Difference between best and worst mean accuracy.
        reason_lines: Human-readable explanation lines.
    """

    passed: bool
    n_domains_best_changes: bool  # whether best agent changes across domains
    performance_spread: float
    reason_lines: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# Core audit engine
# ─────────────────────────────────────────────────────────────────────────────

class CapabilityAudit:
    """Orchestrate the capability audit for all configured agents.

    Loads tasks (real or synthetic), samples a stratified subset per domain,
    runs each agent, and produces a CapabilityMatrix with heterogeneity analysis.

    Example:
        >>> cfg = CapabilityAuditConfig.from_yaml("configs/capability_audit.yaml")
        >>> audit = CapabilityAudit(cfg)
        >>> matrix = audit.run()
        >>> matrix.print_report()
        >>> audit.save(matrix)
    """

    def __init__(self, config: CapabilityAuditConfig) -> None:
        load_dotenv()
        self._cfg = config
        self._seed_manager = SeedManager(config.seed)

    def run(self) -> CapabilityMatrix:
        """Execute the full capability audit.

        Returns:
            CapabilityMatrix with per-agent, per-domain accuracy results
            and heterogeneity gate decision.
        """
        console.print(Panel.fit(
            "[bold cyan]RepGuard — Capability Audit (Step 1.1)[/bold cyan]\n"
            "[dim]Building Domain × Agent capability matrix ...[/dim]",
            border_style="blue",
        ))

        # 1. Load and split tasks
        tasks = self._load_tasks()
        sample_map = self._stratified_sample(tasks)

        domains = sorted(sample_map.keys())
        if self._cfg.domains:
            # Filter to configured domains (intersection with what we have data for)
            domains = [d for d in domains if d in self._cfg.domains]

        agent_names = [a.name for a in self._cfg.agents]
        all_results: dict[str, dict[str, AgentDomainResult]] = {
            name: {} for name in agent_names
        }

        # 2. Evaluate each agent on the sampled tasks
        for agent_cfg in self._cfg.agents:
            console.print(f"\n[bold magenta]▶ Evaluating agent: {agent_cfg.name}[/bold magenta]")
            provider = self._build_provider(agent_cfg)
            cache = DiskCache(
                cache_dir=f"{agent_cfg.cache_dir}/audit_{agent_cfg.name}",
                enabled=True,
            )
            rate_limiter = RateLimiter(
                requests_per_minute=agent_cfg.requests_per_minute,
                tokens_per_minute=agent_cfg.tokens_per_minute,
            )

            for domain in domains:
                domain_tasks = sample_map.get(domain, [])
                if not domain_tasks:
                    logger.warning(f"No tasks found for domain '{domain}' — skipping.")
                    continue

                result = self._evaluate_agent_on_domain(
                    agent_name=agent_cfg.name,
                    domain=domain,
                    tasks=domain_tasks,
                    provider=provider,
                    cache=cache,
                    rate_limiter=rate_limiter,
                )
                all_results[agent_cfg.name][domain] = result

                console.print(
                    f"  {domain:<22} → acc={result.accuracy:.1%} "
                    f"({result.n_correct}/{result.n_tasks})  "
                    f"cost=${result.total_cost_usd:.4f}"
                )

        # 3. Run heterogeneity gate
        gate = _check_heterogeneity(agent_names, domains, all_results)

        matrix = CapabilityMatrix(
            agents=agent_names,
            domains=domains,
            results=all_results,
            seed=self._cfg.seed,
            n_samples_per_domain=self._cfg.n_samples_per_domain,
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            heterogeneity=gate,
        )
        return matrix

    def save(self, matrix: CapabilityMatrix) -> Path:
        """Save audit results to ``output_dir``.

        Writes:
        - ``capability_matrix.json`` — full machine-readable results.
        - ``capability_matrix.csv`` — flat CSV for easy spreadsheet import.
        - ``heterogeneity_gate.txt`` — plain-text gate decision.

        Args:
            matrix: The CapabilityMatrix returned by run().

        Returns:
            Path to the output directory.
        """
        out_dir = Path(self._cfg.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # JSON
        json_path = out_dir / "capability_matrix.json"
        with open(json_path, "w") as fh:
            json.dump(matrix.to_dict(), fh, indent=2)
        console.print(f"\n[green]Saved JSON:[/green] {json_path}")

        # CSV — flat format: agent, domain, accuracy, n_tasks, n_correct, ci_lower, ci_upper, cost
        csv_path = out_dir / "capability_matrix.csv"
        fieldnames = [
            "agent", "domain", "accuracy", "n_tasks", "n_correct",
            "ci_lower", "ci_upper", "total_cost_usd",
        ]
        with open(csv_path, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for agent in matrix.agents:
                for domain in matrix.domains:
                    r = matrix.results.get(agent, {}).get(domain)
                    if r is None:
                        continue
                    writer.writerow({
                        "agent": agent,
                        "domain": domain,
                        "accuracy": round(r.accuracy, 4),
                        "n_tasks": r.n_tasks,
                        "n_correct": r.n_correct,
                        "ci_lower": round(r.ci_lower, 4),
                        "ci_upper": round(r.ci_upper, 4),
                        "total_cost_usd": round(r.total_cost_usd, 6),
                    })
        console.print(f"[green]Saved CSV:[/green]  {csv_path}")

        # Gate decision
        gate_path = out_dir / "heterogeneity_gate.txt"
        gate = matrix.heterogeneity
        lines = [
            f"Heterogeneity Gate: {'PASS' if gate.passed else 'FAIL'}",
            f"Timestamp: {matrix.timestamp}",
            f"Seed: {matrix.seed}",
            f"Agents: {', '.join(matrix.agents)}",
            f"Domains evaluated: {len(matrix.domains)}",
            f"Performance spread: {gate.performance_spread:.4f}",
            "",
        ] + gate.reason_lines
        gate_path.write_text("\n".join(lines))
        console.print(f"[green]Saved gate:[/green] {gate_path}")

        return out_dir

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_tasks(self) -> list[TaskRecord]:
        """Load MMLU-Pro tasks (real or synthetic) and return train_cal split."""
        if self._cfg.use_synthetic:
            console.print(
                f"[yellow]Using synthetic tasks (n={self._cfg.synthetic_n})[/yellow]"
            )
            tasks = create_synthetic_tasks(
                n=self._cfg.synthetic_n,
                seed=self._cfg.seed,
            )
        else:
            console.print(
                f"[cyan]Loading MMLU-Pro from: {self._cfg.data_dir}[/cyan]"
            )
            tasks = load_mmlu_pro(
                data_dir=self._cfg.data_dir,
                dataset_id=self._cfg.dataset_id,
            )

        # Only use train_calibration for the capability audit (no data leakage)
        train_cal, _dev, _test = create_splits(
            tasks, self._seed_manager,
            train_cal_ratio=0.6, dev_ratio=0.2, test_ratio=0.2,
        )
        console.print(
            f"[dim]Using train_calibration split: {train_cal.size} tasks[/dim]"
        )
        return list(train_cal.records)

    def _stratified_sample(
        self, tasks: list[TaskRecord]
    ) -> dict[str, list[TaskRecord]]:
        """Sample up to n_samples_per_domain tasks for each subject.

        Uses a deterministic shuffle (from seed) so that the same config
        always evaluates the same tasks.

        Args:
            tasks: Full list of tasks from the train_calibration split.

        Returns:
            Mapping from domain/subject name → list of sampled TaskRecords.
        """
        rng = self._seed_manager.get_rng("capability_audit_sample")
        n = self._cfg.n_samples_per_domain

        # Group by subject
        by_subject: dict[str, list[TaskRecord]] = defaultdict(list)
        for t in tasks:
            by_subject[t.metadata.subject].append(t)

        sampled: dict[str, list[TaskRecord]] = {}
        for subject, subject_tasks in by_subject.items():
            shuffled = list(subject_tasks)
            rng.shuffle(shuffled)
            sampled[subject] = shuffled[:n]

        console.print(
            f"[dim]Stratified sample: "
            f"{sum(len(v) for v in sampled.values())} tasks across "
            f"{len(sampled)} domains[/dim]"
        )
        return sampled

    def _build_provider(self, agent_cfg: AgentConfig) -> LLMProvider:
        """Instantiate the LLM provider for an agent.

        Reads the API key from the environment variable named in
        ``agent_cfg.api_key_env`` and injects it into the provider factory.

        Args:
            agent_cfg: Agent configuration.

        Returns:
            Initialised LLMProvider.
        """
        import os

        if agent_cfg.api_key_env:
            api_key = os.environ.get(agent_cfg.api_key_env, "")
            if not api_key:
                raise RuntimeError(
                    f"API key env var '{agent_cfg.api_key_env}' is not set "
                    f"for agent '{agent_cfg.name}'. "
                    f"Set it in your .env file or export it."
                )
            # Inject into environment so that create_provider() can find it
            os.environ[_PROVIDER_ENV_MAP.get(agent_cfg.provider, agent_cfg.api_key_env)] = api_key

        provider_config = agent_cfg.to_provider_config()
        if agent_cfg.provider == "ollama":
            from repguard.providers.ollama_ import OllamaProvider

            return OllamaProvider(provider_config, base_url=agent_cfg.base_url)
        return create_provider(provider_config)

    def _evaluate_agent_on_domain(
        self,
        agent_name: str,
        domain: str,
        tasks: list[TaskRecord],
        provider: LLMProvider,
        cache: DiskCache,
        rate_limiter: RateLimiter,
    ) -> AgentDomainResult:
        """Run one agent on all tasks for one domain.

        For each task:
        1. Format the multiple-choice prompt.
        2. Check disk cache; if miss, call the provider API.
        3. Parse the answer from the raw response.
        4. Score against ground truth.

        Args:
            agent_name: Agent label for logging.
            domain: MMLU-Pro subject name.
            tasks: Ordered list of tasks to evaluate.
            provider: Initialised LLMProvider.
            cache: Per-agent disk cache.
            rate_limiter: Per-agent rate limiter.

        Returns:
            AgentDomainResult with accuracy and cost statistics.
        """
        scores: list[bool] = []
        total_cost = 0.0
        total_latency = 0.0

        for task in tasks:
            # Format prompt (never exposes GT)
            formatted = format_prompt(task, mode=self._cfg.prompt_mode)

            # Cache key
            cache_key = DiskCache.make_key(
                model_id=provider.model_id,
                prompt_hash=formatted.prompt_hash,
                temperature=0.0,
                max_tokens=512,
                top_p=1.0,
            )
            cached_resp = cache.get(cache_key)

            if cached_resp is not None:
                raw_text = cached_resp.content
                cost = 0.0
                latency = 0.0
            else:
                rate_limiter.wait_if_needed(estimated_tokens=600)
                try:
                    api_resp = provider.complete(
                        formatted.text,
                        temperature=0.0,
                        max_tokens=512,
                    )
                    cache.put(cache_key, api_resp)
                    rate_limiter.record_request(api_resp.total_tokens)
                    raw_text = api_resp.content
                    cost = api_resp.cost_usd
                    latency = api_resp.latency_ms
                except RuntimeError as exc:
                    logger.error(
                        f"[{agent_name}/{domain}] API call failed for "
                        f"task {task.task_id}: {exc}"
                    )
                    raw_text = ""
                    cost = 0.0
                    latency = 0.0

            # Parse answer
            parsed = parse_response(raw_text, num_options=len(task.options))
            is_correct = task.check_answer(parsed.answer)

            scores.append(is_correct)
            total_cost += cost
            total_latency += latency

        # Compute stats
        accuracy = compute_accuracy(scores)
        _mean, ci_lower, ci_upper = bootstrap_confidence_interval(
            scores, n_bootstrap=500, confidence=0.95, seed=self._cfg.seed
        )

        return AgentDomainResult(
            agent_name=agent_name,
            domain=domain,
            n_tasks=len(tasks),
            n_correct=sum(scores),
            accuracy=accuracy,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            total_cost_usd=total_cost,
            total_latency_ms=total_latency,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Heterogeneity gate
# ─────────────────────────────────────────────────────────────────────────────

# Maps provider name → the environment variable key expected by create_provider()
_PROVIDER_ENV_MAP: dict[str, str] = {
    "gemini":    "GEMINI_API_KEY",
    "openai":    "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def _check_heterogeneity(
    agents: list[str],
    domains: list[str],
    results: dict[str, dict[str, AgentDomainResult]],
) -> HeterogeneityGateResult:
    """Evaluate the heterogeneity gate.

    Checks:
    1. Whether the best agent changes across domains (required for reputation
       transfer experiments — if one model always wins, there is nothing to study).
    2. Whether the performance spread between agents is meaningful.

    Args:
        agents: Agent name list.
        domains: Domain name list.
        results: Nested results dict.

    Returns:
        HeterogeneityGateResult with pass/fail and explanations.
    """
    if len(agents) < 2:
        return HeterogeneityGateResult(
            passed=False,
            n_domains_best_changes=False,
            performance_spread=0.0,
            reason_lines=[
                "❌ Need at least 2 agents to check heterogeneity.",
                "   → Add more agents to the audit config.",
            ],
        )

    # Best agent per domain
    best_per_domain: dict[str, str] = {}
    for domain in domains:
        best_acc = -1.0
        best_name = ""
        for agent in agents:
            r = results.get(agent, {}).get(domain)
            if r is not None and r.accuracy > best_acc:
                best_acc = r.accuracy
                best_name = agent
        best_per_domain[domain] = best_name

    # Count unique best agents (do different agents win different domains?)
    unique_winners = set(best_per_domain.values())
    n_domains_best_changes = len(unique_winners) > 1

    # Performance spread: max mean accuracy − min mean accuracy across agents
    agent_means: dict[str, float] = {}
    for agent in agents:
        accs = [
            results[agent][d].accuracy
            for d in domains
            if d in results.get(agent, {})
        ]
        agent_means[agent] = sum(accs) / len(accs) if accs else 0.0

    spread = max(agent_means.values()) - min(agent_means.values())
    spread_ok = spread >= _MIN_PERFORMANCE_SPREAD

    passed = n_domains_best_changes and spread_ok

    # Build human-readable reasons
    reason_lines: list[str] = []

    if n_domains_best_changes:
        winners_str = ", ".join(f"'{w}'" for w in sorted(unique_winners))
        reason_lines.append(
            f"✓ Best agent changes across domains: YES "
            f"(winners: {winners_str})"
        )
    else:
        dominant = list(unique_winners)[0] if unique_winners else "?"
        reason_lines.append(
            f"✗ Best agent does NOT change — '{dominant}' wins every domain. "
            f"Add more heterogeneous agents."
        )

    if spread_ok:
        reason_lines.append(
            f"✓ Performance spread: {spread:.1%} "
            f"(threshold ≥ {_MIN_PERFORMANCE_SPREAD:.0%}) — meaningful."
        )
    else:
        reason_lines.append(
            f"✗ Performance spread: {spread:.1%} "
            f"(threshold ≥ {_MIN_PERFORMANCE_SPREAD:.0%}) — too small."
        )

    for agent, mean in sorted(agent_means.items(), key=lambda x: -x[1]):
        reason_lines.append(
            f"   {agent:<25} mean accuracy = {mean:.1%}"
        )

    if passed:
        reason_lines.append(
            "\n→ OQ-1 CLOSED: Proceed with Week 2 baselines and HistRepEval v0.1."
        )
    else:
        reason_lines.append(
            "\n→ OQ-1 OPEN: Adjust agent pool before running experiments."
        )

    return HeterogeneityGateResult(
        passed=passed,
        n_domains_best_changes=n_domains_best_changes,
        performance_spread=spread,
        reason_lines=reason_lines,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Research-ops update helpers
# ─────────────────────────────────────────────────────────────────────────────

def update_research_ops(
    matrix: CapabilityMatrix,
    research_ops_dir: str | Path = "./research_ops",
) -> None:
    """Append capability audit results to research_ops tracking files.

    Updates:
    - ``research_log.md`` — adds a dated entry with gate decision.
    - ``open_questions.md`` — closes OQ-1 if gate passed.
    - ``experiment_registry.csv`` — appends one row per agent.

    Args:
        matrix: Completed CapabilityMatrix.
        research_ops_dir: Path to the research_ops directory.
    """
    research_ops_dir = Path(research_ops_dir)
    gate = matrix.heterogeneity

    # --- research_log.md ---
    log_path = research_ops_dir / "research_log.md"
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    log_entry = (
        f"\n---\n\n"
        f"## {today} — Capability Audit (Step 1.1)\n\n"
        f"### Agents evaluated\n"
        + "".join(f"- {a}\n" for a in matrix.agents) +
        f"\n### Domains covered\n"
        + "".join(f"- {d}\n" for d in matrix.domains) +
        f"\n### Heterogeneity Gate: {'PASS ✓' if gate.passed else 'FAIL ✗'}\n"
        + "".join(f"- {line}\n" for line in gate.reason_lines) +
        f"\n### Accuracy summary\n"
    )
    for agent in matrix.agents:
        accs = [
            matrix.accuracy_for(agent, d) or 0.0
            for d in matrix.domains
        ]
        mean = sum(accs) / len(accs) if accs else 0.0
        log_entry += f"- {agent}: mean={mean:.1%}\n"

    if log_path.exists():
        with open(log_path, "a") as fh:
            fh.write(log_entry)
    else:
        log_path.write_text(f"# RepGuard Research Log\n{log_entry}")
    console.print(f"[dim]Updated: {log_path}[/dim]")

    # --- open_questions.md: close OQ-1 if gate passed ---
    oq_path = research_ops_dir / "open_questions.md"
    if oq_path.exists() and gate.passed:
        content = oq_path.read_text()
        old_oq1_status = "**Status:** OPEN — pending API key availability"
        winners = ", ".join(sorted(set(matrix.best_agent_per_domain().values())))
        new_oq1_status = (
            f"**Status:** CLOSED — gate passed on {today}. "
            f"Winners per domain: {winners}. "
            f"Spread: {gate.performance_spread:.1%}."
        )
        if old_oq1_status in content:
            oq_path.write_text(content.replace(old_oq1_status, new_oq1_status))
            console.print(f"[dim]Closed OQ-1 in: {oq_path}[/dim]")

    # --- experiment_registry.csv: append one row per agent ---
    registry_path = research_ops_dir / "experiment_registry.csv"
    fieldnames = [
        "timestamp", "experiment_name", "config_hash", "git_commit",
        "seed", "model_id", "provider", "dataset_split",
        "num_tasks", "metric_accuracy", "metric_notes",
    ]
    file_exists = registry_path.exists() and registry_path.stat().st_size > 0
    with open(registry_path, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        for agent_name in matrix.agents:
            accs = [
                matrix.accuracy_for(agent_name, d) or 0.0
                for d in matrix.domains
            ]
            mean_acc = sum(accs) / len(accs) if accs else 0.0
            writer.writerow({
                "timestamp": matrix.timestamp,
                "experiment_name": f"capability_audit_{agent_name}",
                "config_hash": "",
                "git_commit": "",
                "seed": matrix.seed,
                "model_id": agent_name,
                "provider": "",
                "dataset_split": "train_calibration",
                "num_tasks": matrix.n_samples_per_domain * len(matrix.domains),
                "metric_accuracy": round(mean_acc, 4),
                "metric_notes": (
                    f"audit; gate={'PASS' if gate.passed else 'FAIL'}; "
                    f"spread={gate.performance_spread:.3f}"
                ),
            })
    console.print(f"[dim]Updated registry: {registry_path}[/dim]")


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """CLI entry point: python -m repguard.audit.capability_audit --config ..."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="RepGuard Capability Audit — Week 1, Step 1.1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--config", "-c",
        default="configs/capability_audit.yaml",
        help="Path to capability audit YAML config file.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Override output directory (default: from config).",
    )
    parser.add_argument(
        "--research-ops",
        default="./research_ops",
        help="Path to research_ops directory for log updates.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        default=False,
        help="Print report only; do not write files.",
    )

    args = parser.parse_args()

    try:
        cfg = CapabilityAuditConfig.from_yaml(args.config)
    except FileNotFoundError as exc:
        console.print(f"[red]Config not found: {exc}[/red]")
        sys.exit(1)

    if args.output:
        cfg.output_dir = args.output

    audit = CapabilityAudit(cfg)

    try:
        matrix = audit.run()
    except RuntimeError as exc:
        console.print(f"[red]Audit failed: {exc}[/red]")
        sys.exit(1)

    matrix.print_report()

    if not args.no_save:
        audit.save(matrix)
        update_research_ops(matrix, research_ops_dir=args.research_ops)

    sys.exit(0 if matrix.heterogeneity.passed else 1)


if __name__ == "__main__":
    main()
