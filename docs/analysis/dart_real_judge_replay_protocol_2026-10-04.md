# Frozen full-judge replay and automation

Locked while the label-blind 168-call quality pilot is collecting, before its
quality analysis and before the remaining 2,184 model calls. This extends the
prospective judge protocol; it does not alter the pilot quality gate or prompt.

1. Finish 168 calls, analyze the predeclared quality gate in a separate process.
2. If failed, stop. If passed, resume the same manifest to all 2,352 calls.
3. Require every task-agent record and at least 95% valid outputs. A valid judge
   probability >=0.5 becomes category 1, below becomes 0. Invalid responses are
   category 2 (abstain), retained without replacement. The existing partial-pool
   calibration fits each category using construction audits only. Raw-feedback
   baselines encode abstention as neutral 0.5. No outcome-based imputation.
4. Replay exactly the v3 algorithms, five outer folds, 20 audit seeds and budgets
   5%, 10%, 20%; write a new `results/dart_audit_judge_v1` directory. Label budgets,
   policy class, priors, design iterations and baseline random seeds stay fixed.
5. At primary 10%, DARTContrast must have lower generator-bootstrap CI >0 versus
   AuditOnly, RandomHistory, UncertaintyHistory, UniformAuditGlobal and
   UniformAuditKNN for the exploratory method gate. No threshold optimization.
6. Report every method/budget and failed gates. Stop expansion into challenge or
   sealed MMLU holdout; independent confirmation needs its own locked protocol.

Equal-label baselines do not all require the judge; report judge collection cost
separately. Equal audit count is not total compute/USD parity. This is especially
important if the simple gold-only UniformAuditGlobal baseline wins.

`run_dart_judge_pipeline.py` is a bounded local controller: exclusive lock, ledger
resume, at most three collector attempts per stage, automatic quality/replay
analysis, and a final status file. It never silently changes models, prompts,
data, budgets or gates. All runner stdout/stderr stays under ignored results/.
Use caffeinate to inhibit idle sleep while the local controller runs; forced
sleep/shutdown still interrupts it. Rerunning the same command resumes the ledger.
