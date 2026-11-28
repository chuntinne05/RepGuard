"""HumanEval+ replication of the v3 disagreement audit (protocol 2026-11-28, frozen).

    python -m thesis_pilot.evalplus_audit_he
No new data: reuses confirm_humaneval eval.jsonl + exec_cache; reuses v3 evaluate_pool unchanged.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from thesis_pilot import evalplus_disagreement as D
from thesis_pilot.ecrt_v2_study import SEED, he_rows
from thesis_pilot.evalplus_study import ROOT, load_jsonl, write_once

PROTOCOL = ROOT / "docs" / "analysis" / "repguard_humaneval_audit_replication_protocol_2026-11-28.md"
PROTOCOL_SHA = "919311e9e38a0ae045bddec1a55e8aa75644d4c1de0f11a30e2e1ae9804b4485"
HE = ROOT / "results" / "thesis_ecrt_v2" / "confirm_humaneval"


def check_protocol():
    if hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() != PROTOCOL_SHA:
        raise SystemExit("audit protocol changed after lock")


def main():
    check_protocol()
    ev = load_jsonl(HE / "eval.jsonl")  # same source as cmd_he_score
    if any("n_base" not in r for r in ev):  # v3 meaning: number of base inputs of the task
        base_n = {t: len(json.loads(l)["base_input"]) for t, l in he_rows().items()}
        for r in ev:
            r.setdefault("n_base", base_n[r["task_id"]])
    outs, lens = {}, {}  # same exec_cache loading as v3 cmd_score (len = sanitized solution length)
    for f in sorted((HE / "exec_cache").glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            m, t = r["key"].split("|")
            outs[(m, t)], lens[(m, t)] = r["outs"], r["len"]
    models = sorted({r["model"] for r in ev})
    tasks = sorted({r["task_id"] for r in ev})
    assert len(models) == 12 and len(tasks) == 164, (len(models), len(tasks))
    assert all((m, t) in outs for (m, t) in
               [((r["model"], r["task_id"])) for r in ev if r["B"]]), "missing exec outputs"
    order = [tasks[i] for i in np.random.default_rng(SEED).permutation(len(tasks))]  # same as simulate()
    ncal = int(0.2 * len(order))  # same 20% calibration rule as simulate()
    cal_t, conf_t = order[:ncal], order[ncal:]
    assert len(cal_t) == 32 and len(conf_t) == 132, (len(cal_t), len(conf_t))
    cal_rows = [r for r in ev if r["task_id"] in set(cal_t)]
    conf_rows = [r for r in ev if r["task_id"] in set(conf_t)]
    res = D.evaluate_pool(models, {"dev": cal_rows, "conf": conf_rows}, outs, lens)  # v3 code unchanged
    write_once(HE / "audit_results.json", {"protocol_sha256": PROTOCOL_SHA, "n_cal_tasks": len(cal_t),
                                           "n_conf_tasks": len(conf_t), "cal_tasks": sorted(cal_t),
                                           "conf_tasks": sorted(conf_t), "result": res})
    print(json.dumps({"primary": res["primary"], "budget_0.1": res["budgets"]["0.1"]}, indent=1))


if __name__ == "__main__":
    main()
