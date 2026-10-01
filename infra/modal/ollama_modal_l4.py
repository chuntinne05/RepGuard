import os
import subprocess
import time
import urllib.request

import modal


# ============================================================
# CONFIG
# ============================================================

APP_NAME = "ollama-server-repguard-l4"

PORT = 11434

# Model mặc định mà chúng ta sẽ pull
DEFAULT_MODEL = "qwen3:32b"

# GPU dùng cho app phục hồi
GPU = "L4"

MODEL_DIR = "/models"


# ============================================================
# MODAL IMAGE
# ============================================================

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install(
        "curl",
        "ca-certificates",
        "zstd",       # <-- thêm dòng này
    )
    .run_commands(
        "curl -fsSL https://ollama.com/install.sh | sh"
    )
)


# ============================================================
# PERSISTENT STORAGE
# ============================================================

models_volume = modal.Volume.from_name(
    "ollama-models",
    create_if_missing=True,
)


app = modal.App(APP_NAME)


# ============================================================
# HEALTH CHECK
# ============================================================

def wait_for_ollama(timeout: int = 120):
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{PORT}/api/tags",
                timeout=2,
            ) as response:
                if response.status == 200:
                    print("Ollama is ready.")
                    return
        except Exception:
            time.sleep(1)

    raise RuntimeError("Ollama failed to start.")


# ============================================================
# DOWNLOAD MODEL
#
# This runs WITHOUT GPU.
# So we don't waste GPU credit downloading 10-20 GB models.
# ============================================================

@app.function(
    image=image,
    volumes={
        MODEL_DIR: models_volume,
    },
    env={
        "OLLAMA_MODELS": MODEL_DIR,
    },
    timeout=3600,
)
def pull_model(model: str = DEFAULT_MODEL):
    env = {
        **os.environ,
        "OLLAMA_HOST": f"127.0.0.1:{PORT}",
        "OLLAMA_MODELS": MODEL_DIR,
    }

    process = subprocess.Popen(
        ["ollama", "serve"],
        env=env,
    )

    try:
        wait_for_ollama()

        print(f"Pulling model: {model}")

        subprocess.run(
            ["ollama", "pull", model],
            env=env,
            check=True,
        )

        # Persist downloaded model
        models_volume.commit()

        print(f"Finished downloading {model}")

    finally:
        process.terminate()


# ============================================================
# GPU OLLAMA SERVER
# ============================================================

@app.server(
    image=image,

    # GPU
    gpu=GPU,

    # Ollama HTTP port
    port=PORT,

    # Persistent models
    volumes={
        MODEL_DIR: models_volume,
    },

    env={
        "OLLAMA_HOST": f"0.0.0.0:{PORT}",
        "OLLAMA_MODELS": MODEL_DIR,
    },

    # Shut GPU down after 5 minutes idle
    scaledown_window=300,

    # Prevent accidentally creating many GPU instances
    max_containers=1,

    startup_timeout=300,

    # IMPORTANT:
    # False = endpoint requires Modal authentication.
    unauthenticated=False,
)
class OllamaServer:

    @modal.enter()
    def start(self):
        print("Starting Ollama GPU server...")

        self.process = subprocess.Popen(
            ["ollama", "serve"]
        )

        wait_for_ollama()

    @modal.exit()
    def stop(self):
        print("Stopping Ollama...")

        if hasattr(self, "process"):
            self.process.terminate()
