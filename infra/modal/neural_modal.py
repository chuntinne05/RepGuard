"""Deployed asynchronous CPU experiment; no local runner lifetime dependency."""
from pathlib import Path
import modal

APP_NAME = 'repguard-neural-p0p1-v1'
app = modal.App(APP_NAME)
volume = modal.Volume.from_name('repguard-neural-checkpoints-v1', create_if_missing=True)
HERE = Path(__file__).resolve().parent
image = (modal.Image.debian_slim(python_version='3.11')
    .pip_install('torch==2.5.1', index_url='https://download.pytorch.org/whl/cpu')
    .pip_install('numpy==1.26.4', 'transformers==4.48.3', 'safetensors==0.5.3')
    .env({'HF_HOME': '/checkpoints/hf', 'TOKENIZERS_PARALLELISM': 'false', 'OPENBLAS_NUM_THREADS': '1'})
    .add_local_file(HERE/'neural_core.py', '/root/neural_core.py')
    .add_local_file(HERE/'neural_pipeline.py', '/root/neural_pipeline.py')
    .add_local_file(HERE/'neural_smoke.py', '/root/neural_smoke.py'))


@app.function(image=image, volumes={'/checkpoints': volume}, cpu=2, memory=8192,
              timeout=86400, retries=2, max_containers=1)
def worker(packet: dict):
    from neural_pipeline import run
    return run(packet, '/checkpoints/runs/'+packet['run_id'], volume.commit)


@app.function(image=image, volumes={'/checkpoints': volume}, cpu=.25, memory=512, timeout=120)
def inspect_run(run_id: str, archive: bool = False):
    import io, json, re, zipfile
    if not re.fullmatch(r'[a-f0-9]{24}', run_id):
        raise ValueError('Invalid run ID')
    volume.reload()
    root = Path('/checkpoints/runs')/run_id
    if archive:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
            for path in sorted(root.glob('*.json')):
                z.write(path, path.name)
        return buffer.getvalue()
    path = root/'status.json'
    return json.loads(path.read_text()) if path.exists() else {'state': 'not_started'}
