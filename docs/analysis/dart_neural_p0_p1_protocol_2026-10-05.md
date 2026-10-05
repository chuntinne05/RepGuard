# Neural DART P0/P1: locked execution protocol

Fixed before new neural outcomes. Exploratory public AppWorld normal development;
no independent confirmation. No challenge or sealed MMLU outcome access.

## Inputs and encoder

Use the existing SHA-verified 14-agent × 168-task, 56-generator outcome matrix,
matching 0.1.0 public instructions and original five generator outer folds.
Only this small normal-data packet is uploaded to the user's Modal workspace;
no credentials, account data, raw trajectories or other project files.

Frozen sentence-transformers/all-MiniLM-L6-v2 at revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Tokenize the whole instruction,
split into nonoverlapping chunks of 240 content tokens, encode each with the
model's special tokens/attention mask, mean-pool tokens then normalize, take a
content-token-weighted chunk mean and normalize again. Record token/chunk counts;
never silently truncate long tasks. No training of the encoder.

Fold-local PCA to at most 16 dimensions, fitted only on each training partition
(including inside inner CV), standardized by training component SD, clipped ±5.
Test instructions may be encoded independently, never used to fit PCA or tune.

## Models and fitting

Global: Beta(1,1) agent mean, same definition as UniformAuditGlobal.
Three residual-logit heads initialized around the gold-only global logits:
linear, rank-2 factorization, MLP with one 8-unit tanh hidden layer.
All use masked BCE on revealed binary gold, Adam lr .02 for exactly 300 epochs,
L2 penalty .01 or .1 on learned residual parameters; no early stopping on T.
Fixed one initialization for inner comparisons; final probabilities ensemble
three fixed initialization seeds. L2 coefficients chosen via grouped 3-fold
inner CV. Candidate order for exact ties: Global, linear, lowrank, MLP.
No hundreds-configuration search. Full software versions and seeds recorded.

## P0: full-label learnability diagnostic

Five outer folds. Inside each outer train, grouped 3-fold CV chooses each head's
regularization and the overall Selected candidate, including Global. Inner
validation scores routing success, not BCE; no outer gold is used for selection.
Refit heads on full outer-train labels, then freeze choices before reading T gold.
Report all three heads, Selected and Global. This is explicitly a 100%-label
diagnostic; never compare it as a fair 10%-audit method.

Gate for automatic P1: Selected-minus-Global lower endpoint of an exploratory
5,000 generator bootstrap CI is > 0 (seed 1404). No alternate head or threshold
chosen after seeing results. On failure, save analysis and stop at
`stopped_p0_gate`; do not scale training/judging automatically.

## P1: full-budget gold-only neural learner, if P0 gate passes

All original 5 folds × 20 audit seeds × budgets 5%,10%,20% = 300 cases.
Use exactly the original UniformAuditGlobal indices and audited binary labels.
Same heads, fitting and inner CV; all tuning labels count within B. For each inner
validation fold, score using only audited outcomes with HT weight given the
realized uniform within-fold sampling fraction, conditional on sample counts.
An inner fold without any revealed labels fails closed rather than using full gold.
Refit on all B labels after configuration selection. T outcomes are read only
after actions are fixed. Require Global predictions identical to saved original
UniformAuditGlobal; report heads and Selected, and paired seed-averaged generator
CIs versus UniformAuditGlobal and the existing PairedGlobal control.

P1 primary budget 10%. Gate: Selected has positive CI lower bounds against both
controls there. Always report every budget/head and retain losses. If pass, stop
at `completed_p1_review_required`; further feedback/acquisition algorithms require
scientific review and a separate locked protocol, not unbounded search.

This milestone isolates representation/learner. It does not yet implement DART
feedback correction, ranking loss or adaptive pair acquisition. Those are later
ablation stages, contingent on this evidence.

## Detached execution and recovery

Deploy a versioned Modal app. Submit using deployed Function.spawn, not a local
blocking entrypoint. The function runs up to 24 hours with at most 2 retries,
one worker container/input at a time, persistent Volume checkpoints after every
outer case and each embedding artifact. Atomic JSON checkpoint/status writes.
Stable input+source hashes identify a run; duplicate submissions resume/return
the same run rather than mixing inputs. Resume skips verified completed cases.
The full cloud pipeline makes the gate decision and starts P1 without Codex.

Save FunctionCall ID locally immediately after submission. A separate cloud
reader can inspect progress and return an artifact archive. No always-on polling
or GPU. Codex/session termination or local sleep does not terminate a successfully
submitted deployed job; Modal outage, timeout, exhausted retries or manual stop
can still interrupt it. The durable checkpoint enables an explicit safe resume.

Tests: finite gold-mask isolation, group isolation, feature-fit isolation,
checkpoint identity, remote deterministic training and positive/negative synthetic
unit controls. Synthetic examples are tests only, excluded from scientific results.
Success requires observed checkpoint advancement, not just a live container.
