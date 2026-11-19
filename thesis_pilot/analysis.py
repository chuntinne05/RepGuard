"""Evaluator-only supervised reputation and controlled real-output policy replay."""
import json
import math
import re
from collections import Counter
import numpy as np
from .core import base_features, correct, digest, skill, verify


def reputation(case, agent, history, scored):
    values = [scored[(c["id"], agent)]["correct"] for c in history]
    same = [scored[(c["id"], agent)]["correct"] for c in history
            if skill(c["question"]) == skill(case["question"])]
    global_p = (sum(values) + 1) / (len(values) + 2)
    skill_p = (sum(same) + 8 * global_p) / (len(same) + 8)
    nearby = global_p
    if len(history) >= 2:
        def terms(text):
            words = re.findall(r"\b\w\w+\b", text.casefold())
            return Counter(words + [a+" "+b for a,b in zip(words,words[1:])])
        documents = [terms(c["question"]) for c in history]
        df = Counter(term for doc in documents for term in doc)
        idf = {term:math.log((len(documents)+1)/(n+1))+1 for term,n in df.items()}
        def vector(doc):
            v={term:count*idf[term] for term,count in doc.items() if term in idf}
            norm=math.sqrt(sum(t*t for t in v.values()))
            return {term:value/max(norm,1e-12) for term,value in v.items()}
        query=vector(terms(case["question"]))
        sim=np.array([sum(value*query.get(term,0) for term,value in vector(doc).items()) for doc in documents])
        order = np.argsort(-sim, kind="stable")[:10]
        weight = np.maximum(sim[order], 0)
        nearby = (sum(weight * np.asarray(values)[order]) + 4 * global_p) / (weight.sum() + 4)
    return [global_p, skill_p, nearby, min(len(same), 30) / 30]


def fit_model(x, y):
    x = np.asarray(x, float); y = np.asarray(y, int)
    if len(set(y.tolist())) < 2:
        return {"kind": "empirical_prior", "p": float((y.sum()+1)/(len(y)+2))}
    # Full-batch Newton optimization of binary logistic loss + L2/2.
    # This is actual supervised fitting on recorded solver outcomes, no mock labels.
    z=np.column_stack([np.ones(len(x)),x]);w=np.zeros(z.shape[1])
    w[0]=math.log((y.sum()+1)/(len(y)-y.sum()+1))
    penalty=np.ones(len(w));penalty[0]=0
    def loss(v):
        logits=z@v
        return float(np.sum(np.logaddexp(0,logits)-y*logits)+.5*np.dot(penalty*v,v))
    initial=loss(w);trace=[initial]
    for iteration in range(100):
        logits=np.clip(z@w,-40,40);p=1/(1+np.exp(-logits))
        gradient=z.T@(p-y)+penalty*w
        hessian=z.T@((p*(1-p))[:,None]*z)+np.diag(penalty+1e-8)
        direction=np.linalg.solve(hessian,gradient)
        rate=1.
        while rate>1e-8 and loss(w-rate*direction)>loss(w): rate*=.5
        updated=w-rate*direction;trace.append(loss(updated))
        if np.max(np.abs(updated-w))<1e-8:
            w=updated;break
        w=updated
    return {"kind":"logistic","coef":w[1:].tolist(),"intercept":float(w[0]),
            "training_objective":"sum binary log loss + 0.5*L2(coefficients)",
            "loss_trace":trace,"initial_loss":initial,"final_loss":loss(w),
            "iterations":len(trace)-1}


def predict(model, x):
    if model["kind"] == "empirical_prior": return model["p"]
    value = float(np.dot(model["coef"], x) + model["intercept"])
    return 1 / (1 + math.exp(-max(-40, min(40, value))))


def question_bootstrap(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    rng = np.random.default_rng(18102026)
    draws = rng.integers(0, len(d), (2000, len(d)))
    return {"difference": float(d.mean()),
            "ci95": np.quantile(d[draws].mean(1), [.025, .975]).tolist()}


def analyze(packet, responses):
    visible = packet["visible"]; cases = visible["cases"]
    gold = packet["evaluation"]["gold"]
    if set(gold) != {c["id"] for c in cases}:
        raise ValueError("Gold identity mismatch")
    scored = {}
    for case in cases:
        for agent in ["A", "B"]:
            key = (case["id"], agent)
            row = responses[key]
            check = verify(case, row["response"]["message"]["content"])
            # A completed length-limited response is a real model failure, not retried.
            if not row["response"].get("done"):
                raise ValueError("Unfinished model response in evaluator")
            scored[key] = {"verification": check, "correct": correct(check["value"], gold[case["id"]]),
                           "tokens": row["response"].get("prompt_eval_count", 0) + row["response"].get("eval_count", 0),
                           "seconds": row["wall_seconds"], "agent": agent}
    parts = {p: [c for c in cases if visible["partition"][c["id"]] == p]
             for p in ["history", "calibration", "validation", "screen"]}
    history = parts["history"]
    if len(history) != 60 or any(len(parts[p]) != n for p, n in
                                 [("calibration",10),("validation",10),("screen",20)]):
        raise ValueError("Changed frozen partition sizes")
    if len({c["report"] for c in cases}) != 100:
        raise ValueError("Reports cross partitions")

    def features(case, agent, reference, use_history):
        f = base_features(case, scored[(case["id"], agent)]["verification"], agent)
        return f + (reputation(case, agent, reference, scored) if use_history else [])

    learners = {}
    predictions = {}
    for name, use_history in [("EvidenceOnly", False), ("RepGuard", True)]:
        x, y = [], []
        for case in history:
            fold = int(digest(case["report"])[:8], 16) % 3
            reference = [c for c in history if int(digest(c["report"])[:8], 16) % 3 != fold]
            for agent in ["A", "B"]:
                x.append(features(case, agent, reference, use_history))
                y.append(scored[(case["id"], agent)]["correct"])
        model = fit_model(x, y)
        # Separate calibration labels; never use screen labels to fit or choose.
        cx, cy = [], []
        for case in parts["calibration"]:
            for agent in ["A", "B"]:
                p = predict(model, features(case, agent, history, use_history))
                cx.append([math.log(max(1e-6,p)/max(1e-6,1-p))])
                cy.append(scored[(case["id"],agent)]["correct"])
        calibrator = fit_model(cx, cy)
        for case in cases:
            if visible["partition"][case["id"]] == "history": continue
            for agent in ["A", "B"]:
                p = predict(model, features(case, agent, history, use_history))
                predictions[(name, case["id"], agent)] = predict(
                    calibrator, [math.log(max(1e-6,p)/max(1e-6,1-p))])
        learners[name] = {"model": model, "calibrator": calibrator,
                          "uses_history_features": use_history, "training_rows": len(y),
                          "calibration_rows": len(cy)}

    global_choice = max(["A", "B"], key=lambda a: sum(scored[(c["id"],a)]["correct"] for c in history))

    def choose(case, method, threshold=.5):
        cid = case["id"]; a = scored[(cid,"A")]; b = scored[(cid,"B")]
        first = "A"
        if method == "AlwaysB": first = "B"
        elif method == "GlobalGold": first = global_choice
        elif method in ["SkillGold", "RawFeedbackSkill"]:
            if method == "SkillGold":
                first = max(["A","B"], key=lambda ag: reputation(case,ag,history,scored)[1])
            else:
                similar = [c for c in history if skill(c["question"]) == skill(case["question"])]
                first = max(["A","B"], key=lambda ag: (
                    1+sum(scored[(c["id"],ag)]["verification"]["hard_pass"] for c in similar))/(len(similar)+2))
        selected = first; calls = [first]
        if method == "FixedCascade" and not a["verification"]["hard_pass"]:
            selected = "B"; calls = ["A","B"]
        elif method in learners and (not a["verification"]["hard_pass"] or
                                    predictions[(method,cid,"A")] < threshold):
            selected = "B"; calls = ["A","B"]
        row = scored[(cid,selected)]
        approved = row["verification"]["hard_pass"]
        if method in learners:
            approved = approved and predictions[(method,cid,selected)] >= threshold
        return {"id":cid, "agent": selected, "calls":calls, "correct":row["correct"],
                "approved":bool(approved), "value":row["verification"]["value"],
                "tokens":sum(scored[(cid,ag)]["tokens"] for ag in calls),
                "seconds":sum(scored[(cid,ag)]["seconds"] for ag in calls)}

    for name in learners:
        results = []
        for threshold in [.2,.35,.5,.65,.8]:
            rows = [choose(c,name,threshold) for c in parts["validation"]]
            reference_cost = sum(scored[(c["id"],"B")]["tokens"] for c in parts["validation"])
            # Explicit development utility: all-question accuracy minus token penalty.
            utility = np.mean([r["correct"] for r in rows]) - .05 * sum(r["tokens"] for r in rows)/max(1,reference_cost)
            results.append({"threshold":threshold,"utility":float(utility)})
        chosen = max(results, key=lambda r:r["utility"])
        learners[name].update(threshold=chosen["threshold"],validation_search=results)

    methods = ["AlwaysA","AlwaysB","GlobalGold","SkillGold","RawFeedbackSkill",
               "FixedCascade","EvidenceOnly","RepGuard"]
    action_traces = {m:[choose(c,m,learners.get(m,{}).get("threshold",.5)) for c in parts["screen"]]
                     for m in methods}
    summary = {}
    for method, rows in action_traces.items():
        approved = [r for r in rows if r["approved"]]
        summary[method] = {"correct":sum(r["correct"] for r in rows),"questions":len(rows),
            "accuracy":float(np.mean([r["correct"] for r in rows])),
            "coverage":len(approved)/len(rows),
            "approved_accuracy":float(np.mean([r["correct"] for r in approved])) if approved else None,
            "wrong_approved":sum(not r["correct"] for r in approved),
            "mean_tokens":float(np.mean([r["tokens"] for r in rows])),
            "mean_observed_request_seconds":float(np.mean([r["seconds"] for r in rows])),
            "model_calls":sum(len(r["calls"]) for r in rows)}
    primary = {}
    for baseline in ["AlwaysB","FixedCascade","EvidenceOnly","SkillGold"]:
        a,b=action_traces["RepGuard"],action_traces[baseline]
        primary[baseline] = question_bootstrap([r["correct"] for r in a],[r["correct"] for r in b])
        primary[baseline].update(rescues=sum(x["correct"] and not y["correct"] for x,y in zip(a,b)),
                                 harms=sum(not x["correct"] and y["correct"] for x,y in zip(a,b)))
    # A strict pilot screen, not a final statistical claim or a guarantee.
    rep=summary["RepGuard"]; ev=summary["EvidenceOnly"]; fixed=summary["FixedCascade"]
    signal=(rep["accuracy"] >= max(ev["accuracy"],fixed["accuracy"]) and
            (rep["accuracy"] > max(ev["accuracy"],fixed["accuracy"]) or
             rep["mean_tokens"] < .9*min(ev["mean_tokens"],fixed["mean_tokens"])))
    examples = [{"case":c,"gold":gold[c["id"]],"agents":{
        ag:{**scored[(c["id"],ag)],"probability":predictions[("RepGuard",c["id"],ag)]}
        for ag in ["A","B"]}} for c in parts["screen"]]
    return {"run_id":packet["run_id"],"scope":"100-question real development pilot; 20-question screen, NOT final confirmation",
            "collection_calls":len(responses),"mock_calls":0,"partitions":{p:len(v) for p,v in parts.items()},
            "methods":summary,"primary_contrasts":primary,"pilot_signal_pass":bool(signal),
            "learner_artifacts":learners,"action_traces":action_traces,"examples_private":examples,
            "limitations":["Only 20 screen questions; intervals are very imprecise and exploratory",
                "Full supervised history gold is available equally to all methods; NOT a 10% audit claim",
                "Code/source consistency is not proof of semantic correctness",
                "Same-family agents; model-block execution order affects cold-load latency",
                "Tokens and recorded request time are not total Modal billing or dollar parity",
                "Response collection includes counterfactual calls for evaluating all policies"]}
