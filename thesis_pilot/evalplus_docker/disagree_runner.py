"""In-container helper for the v3 disagreement audit. Modes: gen | exec.

gen:  /in/subset.jsonl -> 30 TypedMut inputs per task (contract only, no canonical body/plus inputs).
exec: /in/samples.json + /in/inputs.pkl -> normalised outputs of each sanitized solution per input.
Prints a final RESULT_JSON: line.
"""
import base64
import json
import math
import sys
from copy import deepcopy


def norm(x):
    """Stable string form of an output; floats rounded to 6 decimals, sets/dicts order-free."""
    if isinstance(x, float):
        return repr(round(x, 6)) if math.isfinite(x) else repr(x)
    if isinstance(x, (list, tuple)):
        o, c = ("[", "]") if isinstance(x, list) else ("(", ")")
        return o + ",".join(norm(i) for i in x) + c
    if isinstance(x, (set, frozenset)):
        return "{" + ",".join(sorted(norm(i) for i in x)) + "}"
    if isinstance(x, dict):
        return "{" + ",".join(sorted(norm(k) + ":" + norm(v) for k, v in x.items())) + "}"
    return repr(x)[:5000]


class _TO(BaseException):
    pass


def _child(conn, code, entry, inputs):
    import os, resource, signal
    resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))
    sys.stdout = sys.stderr = open(os.devnull, "w")
    sys.stdin = open(os.devnull)

    def h(*_):
        raise _TO()
    signal.signal(signal.SIGALRM, h)
    outs = []
    try:
        g = {}
        exec(code, g)
        fn = g[entry]
    except BaseException as e:
        conn.send(["EXC:" + type(e).__name__] * len(inputs))
        return
    for inp in inputs:
        signal.setitimer(signal.ITIMER_REAL, 1.0)
        try:
            o = norm(fn(*deepcopy(inp)))
        except _TO:
            o = "TIMEOUT"
        except BaseException as e:
            o = "EXC:" + type(e).__name__
        signal.setitimer(signal.ITIMER_REAL, 0)
        outs.append(o)
    conn.send(outs)


def run_one(code, entry, inputs):
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    a, b = ctx.Pipe(False)
    p = ctx.Process(target=_child, args=(b, code, entry, inputs))
    p.start()
    b.close()
    try:
        outs = a.recv() if a.poll(len(inputs) * 1.0 + 15) else ["TIMEOUT"] * len(inputs)
    except EOFError:  # child died (e.g. memory)
        outs = ["EXC:ChildDied"] * len(inputs)
    p.kill()
    p.join()
    return outs


def main():
    import os
    ds = os.environ.get("EP_DATASET", "mbpp")
    os.environ["MBPP_OVERRIDE_PATH" if ds == "mbpp" else "HUMANEVAL_OVERRIDE_PATH"] = "/in/subset.jsonl"
    os.environ["XDG_CACHE_HOME"] = "/tmp/cache"
    from evalplus.data import get_human_eval_plus, get_mbpp_plus
    import evalplus.data.humaneval as _he
    _he.completeness_check = lambda *a, **k: None
    problems = get_mbpp_plus() if ds == "mbpp" else get_human_eval_plus()
    mode = sys.argv[1]
    if mode == "gen":
        import pickle, random
        from evalplus.gen.type_mut import TypedMutGen
        inputs, counts = {}, {}
        for tid, p in problems.items():
            sig = next(l for l in p["canonical_solution"].split("\n") if l.startswith(f"def {p['entry_point']}"))
            first = next(l for l in p["contract"].split("\n") if l.strip())
            ind = first[: len(first) - len(first.lstrip())]  # match the contract's own indentation
            code = sig + p["contract"] + "\n" + ind + "return None\n"  # signature line + contract only
            random.seed(f"20261122|{tid}")
            g = TypedMutGen(p["base_input"], p["entry_point"], code)
            g.timeout = 120
            inputs[tid] = g.generate(30)
            counts[tid] = len(inputs[tid])
            print(tid, counts[tid], file=sys.stderr, flush=True)
        print("\nRESULT_JSON:" + json.dumps({"counts": counts, "pickle_b64": base64.b64encode(pickle.dumps(inputs)).decode()}))
    else:
        import pickle
        from concurrent.futures import ThreadPoolExecutor
        from evalplus.sanitize import sanitize
        inputs = pickle.load(open("/in/inputs.pkl", "rb"))
        samples = json.load(open("/in/samples.json", encoding="utf-8"))

        def one(s):
            code = sanitize(s["raw"], problems[s["task_id"]]["entry_point"])
            return {"key": s["key"], "len": len(code),
                    "outs": run_one(code, problems[s["task_id"]]["entry_point"], inputs[s["task_id"]])}
        with ThreadPoolExecutor(4) as ex:
            res = list(ex.map(one, samples))
        print("\nRESULT_JSON:" + json.dumps({"results": res}))


if __name__ == "__main__":
    main()
