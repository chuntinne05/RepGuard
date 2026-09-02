# RepGuard: Evidence-Calibrated Reputation Transfer under Imperfect Feedback in Multi-Agent LLM Systems

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)

## Overview

**RepGuard** studies how multi-agent LLM systems should convert imperfect historical feedback into task-relevant teammate reputation. It proposes **Evidence-Calibrated Reputation Transfer (ECRT)**, which distinguishes *whether historical evidence is trustworthy* from *whether it is relevant to the current task* before allowing that evidence to influence team decisions.

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
1. Download MMLU-Pro from HuggingFace (or use cached data)
2. Create deterministic Train/Calibration, Dev, and Test splits
3. Evaluate sample tasks using the MockProvider
4. Output accuracy metrics and per-domain breakdown

## Architecture

```
src/repguard/
├── config.py           # Pydantic configuration schema
├── seed.py             # Deterministic seed management
├── logging_.py         # Structured experiment logger
├── data/
│   ├── models.py       # Core data models (GT isolation enforced)
│   ├── mmlu_pro.py     # MMLU-Pro download, parse, cache
│   └── splits.py       # Deterministic leak-proof splitting
├── providers/
│   ├── base.py         # LLMProvider protocol
│   ├── mock.py         # Deterministic mock (dry-run)
│   ├── openai_.py      # OpenAI provider
│   └── anthropic_.py   # Anthropic provider
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
