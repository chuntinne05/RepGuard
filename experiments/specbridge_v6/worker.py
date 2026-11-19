"""Isolated public-only native SQL pilot; grader/reference never mounted."""
import json
from pathlib import Path
import modal

from .runtime import MODELS, digest, sha, write

NAME = 'repguard-specbridge-v6-native-pilot-20261109'
app = modal.App(NAME, include_source=False)
sources = modal.Volume.from_name('repguard-specbridge-v6-public-20261109').read_only()
runs = modal.Volume.from_name('repguard-specbridge-v6-runs-20261109', create_if_missing=True)
weights_a = modal.Volume.from_name('repguard-thesis-modern-models-20261019').read_only()
weights_b = modal.Volume.from_name('repguard-thesis-gemma4-models-20261020').read_only()
cpu_image = modal.Image.debian_slim(python_version='3.11').pip_install('sqlean.py==0.21.5.3')
gpu_image = (modal.Image.debian_slim(python_version='3.11').apt_install('curl','ca-certificates','zstd')
             .run_commands('curl -fsSL https://ollama.com/install.sh -o /tmp/install-ollama.sh', 'OLLAMA_VERSION=0.40.6 sh /tmp/install-ollama.sh'))
MEMBERS = ('__init__.py', 'runtime.py', 'worker.py')
for name in MEMBERS:
    cpu_image = cpu_image.add_local_file(Path(__file__).parent / name, '/root/experiments/specbridge_v6/' + name)
    gpu_image = gpu_image.add_local_file(Path(__file__).parent / name, '/root/experiments/specbridge_v6/' + name)


def start(obj, role, manifest):
    import os, subprocess, time, urllib.request
    obj.role = role
    data = json.loads(Path('/models', manifest).read_text())
    if data['models'][MODELS[role]['name']]['digest'] != MODELS[role]['digest']:
        raise RuntimeError('Wrong model weights')
    obj.process = subprocess.Popen(['ollama','serve'], env={**os.environ,'OLLAMA_HOST':'127.0.0.1:11434','OLLAMA_MODELS':'/models',
              'OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'1','OLLAMA_FLASH_ATTENTION':'1','OLLAMA_KV_CACHE_TYPE':'q8_0'},
              stdout=subprocess.DEVNULL, stderr=open('/tmp/specbridge-v6-ollama.log','w'))
    for _ in range(90):
        try:
            with urllib.request.urlopen('http://127.0.0.1:11434/api/version',timeout=2) as r:
                obj.version = json.load(r)['version']
            if obj.version != '0.40.6':
                raise RuntimeError('Wrong serving version')
            return
        except OSError:
            time.sleep(1)
    raise RuntimeError('Serving startup failed')


def infer(obj, messages):
    import urllib.request, subprocess
    cfg = MODELS[obj.role]
    body = {'model': cfg['name'], 'messages': messages, 'stream': False, 'think': False, 'format': 'json', 'keep_alive': '20m',
            'options': {'temperature': 0, 'seed': 20261109, 'num_ctx': 32768, 'num_predict': 8192}}
    request = urllib.request.Request('http://127.0.0.1:11434/api/chat', data=json.dumps(body).encode(), headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request, timeout=600) as r:
        response = json.load(r)
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps', timeout=10) as r:
        loaded = json.load(r)
    actual = next(m for m in loaded['models'] if m['name'] == cfg['name'])
    if actual['digest'] != cfg['digest'] or actual.get('size_vram',0) < .8 * actual['size']:
        raise RuntimeError('Wrong digest or CPU fallback')
    if not response.get('done') or response.get('model') != cfg['name']:
        raise RuntimeError('Incomplete response')
    return {'provider':'ollama_modal','app':NAME,'model':cfg['name'],'model_digest':cfg['digest'],'ollama_version':obj.version,
            'request_body':body,'response':response,'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version','--format=csv,noheader'],text=True).strip(),
            'evaluation_volume_mounted':False,'weights_read_only':True,'live_inference':True}


@app.cls(image=gpu_image, volumes={'/models':weights_a}, gpu='L40S', cpu=2, memory=24576, timeout=900, max_containers=1, scaledown_window=120, retries=0)
class A:
    @modal.enter()
    def enter(self): start(self, 'A', 'repguard_modern_manifest.json')
    @modal.method()
    def run(self, messages): return infer(self, messages)
    @modal.exit()
    def exit(self): self.process.terminate()


@app.cls(image=gpu_image, volumes={'/models':weights_b}, gpu='L40S', cpu=2, memory=24576, timeout=900, max_containers=1, scaledown_window=120, retries=0)
class B:
    @modal.enter()
    def enter(self): start(self, 'B', 'repguard_gemma_manifest.json')
    @modal.method()
    def run(self, messages): return infer(self, messages)
    @modal.exit()
    def exit(self): self.process.terminate()


@app.function(image=cpu_image, volumes={'/sources':sources,'/runs':runs}, cpu=2, memory=4096, timeout=14400, max_containers=1, retries=0)
def run_study(plan, packet):
    import sqlean
    from threading import Lock
    from .runtime import collect
    code = Path('/root/experiments/specbridge_v6')
    if set(p.name for p in code.glob('*.py')) != set(MEMBERS) or sqlean.sqlite_version != '3.42.0':
        raise RuntimeError('Runtime isolation or engine check failed')
    if Path('/evaluation').exists() or (Path('/sources') / 'evaluation').exists():
        raise RuntimeError('Evaluation material present')
    for name, expected in plan['runtime_hashes'].items():
        if sha(code / name) != expected:
            raise RuntimeError('Frozen runtime changed')
    files = sorted(str(p.relative_to('/sources')) for p in Path('/sources').rglob('*') if p.is_file())
    if files != sorted('databases/' + d['database'] + '.sqlite' for d in plan['source_databases']):
        raise RuntimeError('Unexpected source volume membership')
    root = Path('/runs') / plan['plan_id']
    write(root / 'isolation_receipt.json', {'plan_id':plan['plan_id'],'runtime_members':list(MEMBERS),
          'runtime_hashes':plan['runtime_hashes'],'source_files':files,'sqlite_version':sqlean.sqlite_version,
          'grader_or_reference_code_present':False,'evaluation_volume_present':False,'automatic_source_inclusion':False})
    runs.commit()
    a, b = A(), B(); lock = Lock()
    def commit():
        with lock: runs.commit()
    return collect(plan, packet, Path('/sources'), root, lambda role, messages: (a if role == 'A' else b).run.remote(messages), commit)


def launch():
    from datetime import datetime, timezone
    out = Path(__file__).resolve().parents[2] / 'results/specbridge_v6'
    receipt = out / 'launch_receipt.json'
    if receipt.exists():
        raise RuntimeError('Already launched; inspect existing call, never duplicate')
    plan = json.loads((out / 'registered_plan.json').read_text())
    packet = json.loads((out / 'public_packet.json').read_text())
    root = Path(__file__).resolve().parents[2]
    if digest(packet) != plan['public_packet_digest']:
        raise RuntimeError('Public packet changed')
    for path, expected in plan['source_hashes'].items():
        if sha(root / path) != expected:
            raise RuntimeError('Source changed before launch')
    with app.run(detach=True):
        call = run_study.spawn(plan, packet)
        record = {'plan_id':plan['plan_id'],'app_id':app.app_id,'function_call_id':call.object_id,
                  'created_utc':datetime.now(timezone.utc).isoformat(),'max_model_calls':plan['max_model_calls']}
        write(receipt, record); print(json.dumps(record, indent=2), flush=True)


if __name__ == '__main__': launch()
