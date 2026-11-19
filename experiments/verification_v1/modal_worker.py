"""Isolated bounded real-inference app; previous deployments are not invoked."""
from __future__ import annotations

import json
from pathlib import Path

import modal

APP_NAME = "repguard-verification-v1-20261109"
RUN_VOLUME = "repguard-verification-v1-runs-20261109"
app = modal.App(APP_NAME)
runs = modal.Volume.from_name(RUN_VOLUME, create_if_missing=True)
qwen_weights = modal.Volume.from_name("repguard-thesis-modern-models-20261019").read_only()
gemma_weights = modal.Volume.from_name("repguard-thesis-gemma4-models-20261020").read_only()
image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("curl", "ca-certificates", "zstd")
         .run_commands("curl -fsSL https://ollama.com/install.sh -o /tmp/install-ollama.sh",
                       "OLLAMA_VERSION=0.40.6 sh /tmp/install-ollama.sh")
         .add_local_dir(Path(__file__).resolve().parents[1], "/root/experiments",
                        ignore=["__pycache__", "*.pyc"]))


def start_server(obj, manifest_name, expected):
    import os
    import subprocess
    import time
    import urllib.request

    obj.manifest = json.loads(Path("/models", manifest_name).read_text())
    obj.expected = expected
    for name, value in expected.items():
        if obj.manifest["models"][name]["digest"] != value:
            raise RuntimeError("Pinned model weights changed")
    obj.process = subprocess.Popen(["ollama", "serve"], env={**os.environ,
        "OLLAMA_HOST": "127.0.0.1:11434", "OLLAMA_MODELS": "/models",
        "OLLAMA_NUM_PARALLEL": "1", "OLLAMA_MAX_LOADED_MODELS": "1",
        "OLLAMA_FLASH_ATTENTION": "1", "OLLAMA_KV_CACHE_TYPE": "q8_0"},
        stdout=subprocess.DEVNULL, stderr=open("/tmp/verification-ollama.log", "w"))
    for _ in range(90):
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=2) as response:
                obj.version = json.load(response)["version"]
            if obj.version != "0.40.6":
                raise RuntimeError("Wrong Ollama version")
            return
        except OSError:
            time.sleep(1)
    raise RuntimeError("Ollama startup failed")


def infer(obj, model, prompt):
    import subprocess
    import urllib.request

    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "stream": False, "think": False, "format": "json", "keep_alive": "20m",
            "options": {"temperature": 0, "seed": 20261109, "num_ctx": 16384,
                        "num_predict": 2048}}
    request = urllib.request.Request("http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as result:
        response = json.load(result)
    with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=10) as result:
        loaded = json.load(result)
    current = next(m for m in loaded["models"] if m["name"] == model)
    if current["digest"] != obj.expected[model] or current.get("size_vram", 0) < .8 * current["size"]:
        raise RuntimeError("Wrong digest or CPU fallback")
    if not response.get("done") or response.get("model") != model:
        raise RuntimeError("Incomplete or wrong-model response")
    return {"provider": "ollama_modal", "app": APP_NAME, "model": model,
            "model_digest": current["digest"], "ollama_version": obj.version,
            "request_body": body, "response": response,
            "gpu": subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version",
                                            "--format=csv,noheader"], text=True).strip(),
            "weights_mounted_read_only": True, "evaluation_volume_mounted": False,
            "live_inference": True}


@app.cls(image=image, volumes={"/models": qwen_weights}, gpu="L40S", cpu=2,
         memory=24576, timeout=600, max_containers=1, scaledown_window=120, retries=0)
class QwenVerifier:
    @modal.enter()
    def start(self):
        start_server(self, "repguard_modern_manifest.json", {"qwen3.5:27b":
            "64ae5b1d651fb2709d5928ccb8dcfb4bb2cc9c2c8001ac34497e36a6cf905b59"})

    @modal.method()
    def run(self, prompt):
        return infer(self, "qwen3.5:27b", prompt)

    @modal.exit()
    def stop(self):
        self.process.terminate()


@app.cls(image=image, volumes={"/models": gemma_weights}, gpu="L40S", cpu=2,
         memory=24576, timeout=600, max_containers=1, scaledown_window=120, retries=0)
class GemmaVerifier:
    @modal.enter()
    def start(self):
        start_server(self, "repguard_gemma_manifest.json", {"gemma4:26b-a4b-it-q4_K_M":
            "5571076f3d70050487b26b341705799e0ab29b808164f90d20d4cf84f699d251"})

    @modal.method()
    def run(self, prompt):
        return infer(self, "gemma4:26b-a4b-it-q4_K_M", prompt)

    @modal.exit()
    def stop(self):
        self.process.terminate()


@app.function(image=image, volumes={"/runs": runs}, cpu=1, memory=2048,
              timeout=14400, max_containers=1, retries=0)
def collect_remote(plan, public):
    from threading import Lock
    from experiments.verification_v1.collection import collect
    from experiments.verification_v1.prepare import digest

    if digest(public) != plan["public_sha256"]:
        raise ValueError("Input identity mismatch")
    lock = Lock()
    a, b = QwenVerifier(), GemmaVerifier()

    def commit():
        with lock:
            runs.commit()

    def invoke(role, prompt):
        return (a if role == "A" else b).run.remote(prompt)

    try:
        return collect(plan, public, Path("/runs") / plan["plan_id"], invoke, commit)
    except Exception as error:
        from experiments.verification_v1.prepare import write
        write(Path("/runs") / plan["plan_id"] / "status.json",
              {"state": "STOP_worker_exception", "error_type": type(error).__name__,
               "error": str(error)[:1000], "plan_id": plan["plan_id"]})
        commit()
        raise


@app.function(image=image, volumes={"/runs": runs}, cpu=.25, memory=1024,
              timeout=120, max_containers=1, retries=0)
def inspect_remote(plan_id, archive=False):
    import io
    import re
    import zipfile

    if not re.fullmatch("[a-f0-9]{24}", plan_id):
        raise ValueError("Invalid run identifier")
    runs.reload()
    directory = Path("/runs") / plan_id
    if archive:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as output:
            for p in directory.rglob("*.json"):
                output.write(p, str(p.relative_to(directory)))
        return buffer.getvalue()
    status = directory / "status.json"
    return json.loads(status.read_text()) if status.exists() else {"state": "not_started"}


@app.function(image=image, volumes={"/qwen": qwen_weights, "/gemma": gemma_weights},
              cpu=.25, memory=1024, timeout=60, retries=0)
def inspect_weights():
    return {"qwen": json.loads(Path("/qwen/repguard_modern_manifest.json").read_text()),
            "gemma": json.loads(Path("/gemma/repguard_gemma_manifest.json").read_text())}
