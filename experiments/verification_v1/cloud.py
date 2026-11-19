"""Launch, inspect and fetch this study only. No old deployment is called."""
from __future__ import annotations

import argparse
import io
import json
import zipfile
from datetime import datetime, timezone

from .prepare import OUT, digest, write


def main(action):
    from .modal_worker import app, collect_remote, inspect_remote, inspect_weights

    plan = json.loads((OUT / "registered_plan.json").read_text())
    for relative, expected in plan["source_hashes"].items():
        from .prepare import ROOT
        if digest((ROOT / relative).read_bytes()) != expected:
            raise RuntimeError("Registered source changed: " + relative)
    receipt = OUT / "launch_receipt.json"
    if action == "launch":
        if receipt.exists():
            raise RuntimeError("Launch receipt exists; inspect/resume carefully instead of duplicate launch")
        public = json.loads((OUT / "public_pilot.json").read_text())
        with app.run(detach=True):
            weights = inspect_weights.remote()
            write(OUT / "weights_preflight.json", weights)
            for role, name in (("A", "qwen"), ("B", "gemma")):
                cfg = plan["models"][role]
                if weights[name]["models"][cfg["name"]]["digest"] != cfg["digest"]:
                    raise RuntimeError("Wrong remote weights")
            call = collect_remote.spawn(plan, public)
            result = {"plan_id": plan["plan_id"], "function_call_id": call.object_id,
                      "app_id": app.app_id, "app_name": app.name,
                      "created_utc": datetime.now(timezone.utc).isoformat(),
                      "detached_bounded_worker": True, "max_calls": plan["max_corpus_calls"]}
            write(receipt, result)
            print(json.dumps(result, indent=2), flush=True)
    else:
        # A separate short-lived inspector reads only this study's runs volume.
        # It never calls an old deployment or starts an inference class.
        with app.run():
            value = inspect_remote.remote(plan["plan_id"], archive=(action == "fetch"))
        if action == "fetch":
            destination = OUT / "runs" / plan["plan_id"]
            destination.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(value)) as z:
                for member in z.infolist():
                    target = destination / member.filename
                    if not target.resolve().is_relative_to(destination.resolve()):
                        raise ValueError("Unsafe archive member")
                z.extractall(destination)
            print(json.dumps({"downloaded_bytes": len(value), "destination": str(destination)}))
        else:
            print(json.dumps(value, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("launch", "inspect", "fetch"))
    main(p.parse_args().action)
