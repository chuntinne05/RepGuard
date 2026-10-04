# RepGuard: Evidence-Calibrated Reputation Transfer under Imperfect Feedback in Multi-Agent LLM Systems

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)

## Overview

**RepGuard** studies how multi-agent LLM systems should convert imperfect historical feedback into task-relevant teammate reputation. It proposes **Evidence-Calibrated Reputation Transfer (ECRT)**, which distinguishes *whether historical evidence is trustworthy* from *whether it is relevant to the current task* before allowing that evidence to influence team decisions.

### Current research status (2026-10-04)

The AppWorld study now includes 14 historical agents on 168 tasks (56 generators),
**2,352 completed real Qwen3-14B trajectory judgments on Modal**, and completed
equal-audit-budget routing replays. At the primary 10% audit budget, DARTContrast
with judge feedback achieves **63.90/168** mean task successes, versus **69.70**
for UniformAuditGlobal and **71.95** for the additional PairedGlobal control.
The DART superiority gate **fails**. These are exploratory public-data replays,
not fresh solver runs or independent confirmation. The sealed holdout is unused.

See the [full-run assessment and next experiment](docs/analysis/dart_full_run_assessment_2026-10-04.md),
[full results and diagnostics](docs/analysis/dart_followup_report_2026-10-04.md),
and [implementation history](docs/analysis/dart_implementation_progress_2026-10-04.md).
The original pipeline and its follow-up both completed; a failed scientific gate
does not mean the execution failed. The test suite has **233 passing tests**.

### Earlier evidence (2026-09-30)

The full real-answer rerun covers **all 14 MMLU-Pro subjects** and 18,064 answers from four Ollama models. In the prespecified `related + 25% noise` condition, ECRT's team-accuracy difference against FixedBorrow is only +0.02 percentage points (95% CI [−0.04, +0.10]); ECRT superiority is **not established**. A separate paired Qwen3 8B study found a +23.57-point thinking-policy accuracy gain on 280 unused dev questions, with about 213 times the output tokens. A new 1,260-response real-model pool study found an oracle upper reference of 344/420 but a cross-fitted subject router of 274/420 versus 280/420 for always thinking. The prespecified pool gate for DART **failed**; the new sealed holdout remains unused.

See the [full evidence audit](docs/analysis/repguard_final_pipeline_assessment_2026-09-30.md), the [pool gate assessment](docs/analysis/repguard_pool_gate_assessment_2026-09-30.md), the [next study protocol](docs/analysis/repguard_next_study_registered_plan_2026-09-30.md), and the [HistRepEval benchmark card draft](docs/analysis/histrepeval_benchmark_card_draft_2026-09-30.md). DART remains a conditional method hypothesis, not a validated result.

### Key Research Questions

1. How do feedback sparsity, noise, and evaluator error affect learned reputation calibration?
2. How does task mismatch degrade the usefulness of historical reputation?
3. Do feedback reliability and task transferability correspond to distinguishable failure modes?
4. Does ECRT improve reputation quality over global and skill-conditioned baselines?
5. How much historical evidence must a strategic agent accumulate to gain harmful influence?

## Quick Start

### Prerequisites

- Python 3.11 or later
- `pip` or a virtual environment manager

### Installation

```bash
# Clone the repository
git clone https://github.com/chuntinne05/RepGuard.git
cd RepGuard

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install with development dependencies
pip install -e ".[dev]"

# Copy environment template (API keys are NOT required for dry-run)
cp .env.example .env
```

### Run Tests

```bash
# Full test suite (no API keys needed — uses MockProvider)
pytest

# Smoke test only
pytest tests/test_smoke.py -v
```

### Dry-Run Smoke Test

Run the full pipeline with the mock provider (no API keys required):

```bash
python -m repguard.harness.runner --config configs/default.yaml --dry-run
```

This will:
1. Generate deterministic synthetic tasks (the mock provider does not measure real model capability)
2. Create deterministic Train/Calibration, Dev, and Test splits
3. Evaluate sample tasks using the MockProvider
4. Output accuracy metrics and per-domain breakdown

### Local Model Capability Audit

RepGuard can compare Ollama models installed on the same machine using the real MMLU-Pro benchmark. The **example config** evaluates 80 shared train/calibration questions per model across eight subjects; the completed study described above uses a separate 14-subject protocol. The example writes a capability matrix and a heterogeneity-gate decision.

```bash
python -m repguard.audit.capability_audit --config configs/capability_audit.ollama.yaml
```

The Ollama server must be running at `http://127.0.0.1:11434`; update `base_url` in the config if it uses another address. MMLU-Pro is downloaded and cached under `./data` on the first run. Results are saved under `./results/capability_audit_ollama`; reruns reuse each model's cached responses.

## Architecture

```
src/repguard/
├── config.py           # Pydantic configuration schema
├── seed.py             # Deterministic seed management
├── logging_.py         # Structured experiment logger
├── audit/
│   └── capability_audit.py # Multi-model benchmark and heterogeneity gate
├── data/
│   ├── models.py       # Core data models (GT isolation enforced)
│   ├── mmlu_pro.py     # MMLU-Pro download, parse, cache
│   └── splits.py       # Deterministic leak-proof splitting
├── providers/
│   ├── base.py         # LLMProvider protocol
│   ├── mock.py         # Deterministic mock (dry-run)
│   ├── openai_.py      # OpenAI provider
│   ├── anthropic_.py   # Anthropic provider
│   └── ollama_.py      # Local Ollama provider
├── harness/
│   ├── prompts.py      # MC prompt formatting
│   ├── parser.py       # Answer extraction
│   ├── cache.py        # Disk cache for LLM calls
│   ├── rate_limiter.py # Rate limiting + retry
│   └── runner.py       # Single-agent evaluation harness
└── evaluation/
    └── metrics.py      # Accuracy, bootstrap CI, per-domain
```

### Ground-Truth Isolation

RepGuard enforces GT/online-feedback separation at the architecture level:

- `TaskRecord` contains GT and is used only by the offline evaluator
- `OnlineTaskView` is a GT-stripped projection — the online reputation system physically cannot access GT
- Feedback generators receive GT only during simulation setup; their output (`FeedbackSignal`) contains only the noisy observation

### Reproducibility

- All stochastic operations use explicit seeds derived from a master seed via SHA-256
- Every LLM call is cached to disk with a content-addressable key
- Experiment configs, git commits, and prompt hashes are logged automatically
- Split manifests store task IDs for exact reproduction

## Configuration

See [`configs/default.yaml`](configs/default.yaml) for the full configuration schema. Key sections:

| Section | Purpose |
|---------|---------|
| `experiment` | Name, seed, description |
| `data` | Dataset, splits, data directory |
| `provider` | LLM provider, model, parameters |
| `harness` | Batch size, rate limits, cache |
| `logging` | Log directory, verbosity |

## Project Structure

```
repguard/
├── docs/               # Research proposal and 6-week plan
├── research_ops/       # Research log, experiment registry, claims
├── configs/            # Experiment configurations (YAML)
├── src/repguard/       # Source code
├── tests/              # pytest test suite
├── .env.example        # Environment template
├── pyproject.toml      # Package configuration
└── README.md           # This file
```

## Research Operations

Daily tracking files in `research_ops/`:

- `research_log.md` — Daily research notes and decisions
- `experiment_registry.csv` — Structured log of every experiment run
- `paper_claims.md` — Tracks which claims are supported by evidence
- `open_questions.md` — Research questions requiring resolution

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Citation

```bibtex
@misc{repguard2026,
  title={RepGuard: Evidence-Calibrated Reputation Transfer under Imperfect Feedback in Multi-Agent LLM Systems},
  author={RepGuard Research Team},
  year={2026},
  note={Working paper}
}
```
