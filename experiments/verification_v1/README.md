# Verification cycle 01

Prospectively registered pilot `1a97e7cca4367a1fe81c9417` completed720 real
responses. See `docs/reports/2026-11-09/VERIFICATION_CYCLE01_RESULTS_VA_QUYET_DINH.md`.
Operational audit passed; the registered scientific expansion gate failed.
No history learner is fitted, and no automatic follow-up inference is scheduled.

This task evaluates standalone passage sufficiency, not enterprise-report truth.
Public-field whitelisting and a separate local gold packet enforce the intended
inference boundary. Existing research weights are mounted read-only in a new
Modal app. The registered plan includes exact source hashes and model digests.

Offline score and audit from the repository root:

```sh
PYTHONPATH=. .venv/bin/python -m experiments.verification_v1.analysis results/verification_v1/runs/1a97e7cca4367a1fe81c9417
PYTHONPATH=. .venv/bin/python docs/reports/2026-11-09/audit_verification_v1.py
```

Raw source, prompts, responses, attempts, frozen source ZIP and private annotations
are under ignored `results/verification_v1/`. Do not silently regenerate a run or
overwrite a registered plan. `cloud launch` rejects an existing launch receipt.
Unresolved started requests block blind regeneration. No quality retries are used.

The remote ZIP inspector hit its120-second timeout for this archive. To download
the volume with the installed Modal CLI, create the local staging **directory
before** calling `modal volume get`; otherwise directory/file creation can race.
The completed artifacts were successfully downloaded by that route and audited.
