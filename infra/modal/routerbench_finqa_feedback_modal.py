"""Detached CPU orchestrator and isolated real Qwen3-14B GPU judge."""
from pathlib import Path
import modal

ollama_image = (modal.Image.debian_slim(python_version='3.12')
                .apt_install('curl', 'ca-certificates', 'zstd')
                .run_commands('curl -fsSL https://ollama.com/install.sh | sh'))

app = modal.App('repguard-routerbench-finqa-feedback-v1')
pilot = modal.Volume.from_name('repguard-routerbench-finqa-feedback-v1', create_if_missing=True)
archive_volume = modal.Volume.from_name('repguard-routerbench-intake-checkpoints-v1')
models_volume = modal.Volume.from_name('ollama-models')
HERE = Path(__file__).resolve().parent
NAMES = ('routerbench_finqa_feedback_core.py', 'routerbench_finqa_feedback_pipeline.py',
         'routerbench_intake_core.py')
cpu_image = modal.Image.debian_slim(python_version='3.11').pip_install('numpy==1.26.4', 'ijson==3.3.0')
gpu_image = ollama_image.pip_install('numpy==1.26.4', 'ijson==3.3.0')
for name in NAMES:
    cpu_image = cpu_image.add_local_file(HERE / name, '/root/' + name)
    gpu_image = gpu_image.add_local_file(HERE / name, '/root/' + name)


@app.function(image=gpu_image, volumes={'/pilot': pilot, '/models': models_volume},
              gpu=['L4', 'A10'], cpu=2, memory=16384, timeout=14400, retries=2, max_containers=1)
def judge(packet: dict):
    import json
    import os
    import subprocess
    import time
    import urllib.request
    from routerbench_finqa_feedback_core import MODEL, MODEL_DIGEST
    from routerbench_finqa_feedback_pipeline import collect, verify, atomic
    verify(packet); pilot.reload()
    root = Path('/pilot/runs') / packet['run_id']
    env = {**os.environ, 'OLLAMA_MODELS': '/models', 'OLLAMA_HOST': '127.0.0.1:11434',
           'OLLAMA_NUM_PARALLEL': '1', 'OLLAMA_MAX_LOADED_MODELS': '1'}
    process = subprocess.Popen(['ollama', 'serve'], env=env)
    try:
        deadline = time.monotonic() + 180
        while True:
            try:
                with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=3) as response:
                    tags = json.load(response)
                break
            except Exception:
                if time.monotonic() >= deadline:
                    raise RuntimeError('Ollama startup timeout')
                time.sleep(1)
        tag = next((m for m in tags['models'] if m['name'] == MODEL), None)
        if tag is None or tag['digest'] != MODEL_DIGEST:
            raise ValueError('Cached judge model missing or digest mismatch')
        with urllib.request.urlopen('http://127.0.0.1:11434/api/version', timeout=5) as response:
            version = json.load(response)
        atomic(root / 'judge_environment.json', {'model': MODEL, 'model_digest': tag['digest'], 'ollama': version,
               'gpu': subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], text=True).strip(),
               'think': False, 'num_ctx': 16384, 'num_predict': 128, 'temperature': 0, 'seed': 1404,
               'archive_mounted': False})
        pilot.commit()
        def request(body):
            req = urllib.request.Request('http://127.0.0.1:11434/api/chat',
                                         data=json.dumps(body).encode(),
                                         headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=180) as response:
                return json.load(response)
        return collect(packet, root, pilot.commit, request)
    finally:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait()


@app.function(image=cpu_image, volumes={'/pilot': pilot, '/archive': archive_volume},
              cpu=1, memory=4096, timeout=86400, retries=2, max_containers=1)
def worker(packet: dict):
    import json
    from routerbench_finqa_feedback_pipeline import prepare_inputs, finish, status, verify
    verify(packet); pilot.reload(); archive_volume.reload()
    root = Path('/pilot/runs') / packet['run_id']; root.mkdir(parents=True, exist_ok=True)
    sp = root / 'status.json'
    if sp.exists() and json.loads(sp.read_text())['state'] == 'completed_pilot_review_required':
        return json.loads(sp.read_text())
    archive = Path('/archive/runs/8844b39df2d3d6b37eface11/bench-release.tar.gz')
    try:
        prepare_inputs(packet, root, archive, pilot.commit)
        judge.remote(packet)
        pilot.reload()
        return finish(packet, root, archive, pilot.commit)
    except Exception as error:
        status(root, packet, pilot.commit, 'pipeline_failed', error=repr(error))
        raise


@app.function(image=cpu_image, volumes={'/pilot': pilot}, cpu=.25, memory=512, timeout=180)
def inspect_run(run_id: str, archive: bool = False):
    import io
    import json
    import re
    import zipfile
    if not re.fullmatch(r'[a-f0-9]{24}', run_id):
        raise ValueError('Invalid run ID')
    pilot.reload()
    root = Path('/pilot/runs') / run_id
    if archive:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
            for path in sorted(root.glob('*.json')):
                z.write(path, path.name)
        return buffer.getvalue()
    path = root / 'status.json'
    return json.loads(path.read_text()) if path.exists() else {'state': 'not_started'}
