"""New bounded Modal app, separate run volume, read-only existing weights."""
from __future__ import annotations

import json
from pathlib import Path
import modal

from .study import MODELS

APP_NAME = "repguard-arqa-v2-20261109"
VOLUME_NAME = "repguard-arqa-v2-runs-20261109"
app = modal.App(APP_NAME)
runs = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
qwen = modal.Volume.from_name("repguard-thesis-modern-models-20261019").read_only()
gemma = modal.Volume.from_name("repguard-thesis-gemma4-models-20261020").read_only()
image = (modal.Image.debian_slim(python_version="3.11").apt_install("curl", "ca-certificates", "zstd")
         .run_commands("curl -fsSL https://ollama.com/install.sh -o /tmp/install-ollama.sh",
                       "OLLAMA_VERSION=0.40.6 sh /tmp/install-ollama.sh")
         .add_local_dir(Path(__file__).resolve().parents[1], "/root/experiments", ignore=["__pycache__", "*.pyc"]))


def start(obj, role, manifest):
    import os
    import subprocess
    import time
    import urllib.request

    obj.role = role
    cfg = MODELS[role]
    actual = json.loads(Path("/models", manifest).read_text())
    if actual["models"][cfg["name"]]["digest"] != cfg["digest"]:
        raise RuntimeError("Pinned weights changed")
    obj.process = subprocess.Popen(["ollama", "serve"], env={**os.environ,
        "OLLAMA_HOST": "127.0.0.1:11434", "OLLAMA_MODELS": "/models", "OLLAMA_NUM_PARALLEL": "1",
        "OLLAMA_MAX_LOADED_MODELS": "1", "OLLAMA_FLASH_ATTENTION": "1", "OLLAMA_KV_CACHE_TYPE": "q8_0"},
        stdout=subprocess.DEVNULL, stderr=open("/tmp/arqa-v2-ollama.log", "w"))
    for _ in range(90):
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=2) as r:
                obj.version = json.load(r)["version"]
            if obj.version != "0.40.6": raise RuntimeError("Wrong server version")
            return
        except OSError:
            time.sleep(1)
    raise RuntimeError("Server failed to start")


def infer(obj, prompt):
    import urllib.request
    import subprocess

    cfg = MODELS[obj.role]
    body = {"model": cfg["name"], "messages": [{"role": "user", "content": prompt}],
            "stream": False, "think": False, "format": "json", "keep_alive": "20m",
            "options": {"temperature": 0, "seed": 20261109, "num_ctx": 16384, "num_predict": 2048}}
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r: response = json.load(r)
    with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=10) as r: loaded = json.load(r)
    model = next(m for m in loaded["models"] if m["name"] == cfg["name"])
    if model["digest"] != cfg["digest"] or model.get("size_vram", 0) < .8 * model["size"]:
        raise RuntimeError("Wrong digest or CPU fallback")
    if not response.get("done") or response.get("model") != cfg["name"]:
        raise RuntimeError("Incomplete or wrong-model response")
    return {"provider": "ollama_modal", "app": APP_NAME, "model": cfg["name"], "model_digest": cfg["digest"],
            "ollama_version": obj.version, "request_body": body, "response": response,
            "gpu": subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"], text=True).strip(),
            "weights_mounted_read_only": True, "evaluation_volume_mounted": False, "live_inference": True}


@app.cls(image=image, volumes={"/models": qwen}, gpu="L40S", cpu=2, memory=24576,
         timeout=600, max_containers=1, scaledown_window=120, retries=0)
class A:
    @modal.enter()
    def enter(self): start(self, "A", "repguard_modern_manifest.json")

    @modal.method()
    def run(self, prompt): return infer(self, prompt)

    @modal.exit()
    def exit(self): self.process.terminate()


@app.cls(image=image, volumes={"/models": gemma}, gpu="L40S", cpu=2, memory=24576,
         timeout=600, max_containers=1, scaledown_window=120, retries=0)
class B:
    @modal.enter()
    def enter(self): start(self, "B", "repguard_gemma_manifest.json")

    @modal.method()
    def run(self, prompt): return infer(self, prompt)

    @modal.exit()
    def exit(self): self.process.terminate()


@app.function(image=image, volumes={"/runs": runs}, cpu=1, memory=2048,
              timeout=14400, max_containers=1, retries=0)
def run_study(plan, public):
    from threading import Lock
    from experiments.arqa_v2.study import collect
    from experiments.arqa_v2.preflight import write, digest, ROOT

    for rel, expected in plan["source_hashes"].items():
        if digest((ROOT / rel).read_bytes()) != expected:
            raise RuntimeError("Remote source mismatch: " + rel)

    lock = Lock()
    a, b = A(), B()

    def commit():
        with lock: runs.commit()

    try:
        return collect(plan, public, Path("/runs") / plan["plan_id"],
                       lambda role, prompt: (a if role == "A" else b).run.remote(prompt), commit)
    except Exception as error:
        write(Path("/runs") / plan["plan_id"] / "status.json",
              {"state": "STOP_worker_exception", "error_type": type(error).__name__, "error": str(error)[:1000]})
        commit()
        raise


@app.function(image=image, volumes={"/runs": runs}, cpu=.25, memory=512, timeout=60, retries=0)
def inspect(plan_id):
    import re
    if not re.fullmatch("[a-f0-9]{24}", plan_id): raise ValueError("Bad plan ID")
    runs.reload()
    root = Path("/runs") / plan_id
    return {p.name: json.loads(p.read_text()) for p in root.glob("*.json") if p.name in ("status.json", "operational_gate.json")}


def launch():
    from datetime import datetime, timezone
    from .preflight import OUT, ROOT, digest, write

    plan = json.loads((OUT / "registered_plan.json").read_text())
    if (OUT / "launch_receipt.json").exists(): raise RuntimeError("Already launched; no duplicate")
    for rel, expected in plan["source_hashes"].items():
        if digest((ROOT / rel).read_bytes()) != expected: raise RuntimeError("Frozen source changed: " + rel)
    public = json.loads((OUT / "public_pilot.json").read_text())
    if digest(public) != plan["public_sha256"]: raise RuntimeError("Public packet changed")
    with app.run(detach=True):
        call = run_study.spawn(plan, public)
        receipt = {"plan_id": plan["plan_id"], "app_name": APP_NAME, "app_id": app.app_id,
                   "function_call_id": call.object_id, "created_utc": datetime.now(timezone.utc).isoformat(), "max_calls": plan["max_calls"]}
        write(OUT / "launch_receipt.json", receipt)
        print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    import sys
    if sys.argv[1] == "launch": launch()
    elif sys.argv[1] == "inspect":
        from .preflight import OUT
        plan = json.loads((OUT / "registered_plan.json").read_text())
        with app.run(): print(json.dumps(inspect.remote(plan["plan_id"]), indent=2))
