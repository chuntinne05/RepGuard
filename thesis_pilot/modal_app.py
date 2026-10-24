"""An isolated Modal application; never imports or calls the existing Ollama apps."""
from pathlib import Path
import modal

APP_NAME = "repguard-thesis-real-pilot-20261018"
MODEL_VOLUME = "repguard-thesis-models-20261018"
RUN_VOLUME = "repguard-thesis-runs-20261018"
OLLAMA_VERSION = "0.40.6"
MODELS = ("qwen3:8b", "qwen3:14b")
app = modal.App(APP_NAME)
models = modal.Volume.from_name(MODEL_VOLUME, create_if_missing=True)
runs = modal.Volume.from_name(RUN_VOLUME, create_if_missing=True)
image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("curl", "ca-certificates", "zstd")
         .run_commands("curl -fsSL https://ollama.com/install.sh -o /tmp/install-ollama.sh",
                       "OLLAMA_VERSION=0.40.6 sh /tmp/install-ollama.sh"))


@app.function(image=image, volumes={"/models": models}, cpu=2, memory=4096,
              timeout=3600, max_containers=1, retries=0)
def download_models():
    import json, os, subprocess, time, urllib.request
    env = {**os.environ, "OLLAMA_HOST": "127.0.0.1:11434", "OLLAMA_MODELS": "/models"}
    process = subprocess.Popen(["ollama", "serve"], env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 60
        while True:
            try:
                urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2).close()
                break
            except Exception:
                if time.monotonic() > deadline:
                    raise RuntimeError("Ollama did not start")
                time.sleep(1)
        for name in MODELS:
            print("Downloading in NEW volume:", name, flush=True)
            with open("/tmp/model-pull.log", "ab") as log:
                subprocess.run(["ollama", "pull", name], env=env, check=True,
                               timeout=1500, stdout=log, stderr=log)
            models.commit()
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags") as response:
            tags = json.load(response)
        with urllib.request.urlopen("http://127.0.0.1:11434/api/version") as response:
            version = json.load(response)
        assert version["version"] == OLLAMA_VERSION, version
        manifest = {"ollama": version["version"], "models": {
            name: next(row for row in tags["models"] if row["name"] == name)
            for name in MODELS}, "volume": MODEL_VOLUME, "app": APP_NAME}
        Path("/models/repguard_manifest.json").write_text(json.dumps(manifest, indent=2))
        models.commit()
        print(json.dumps(manifest), flush=True)
        return manifest
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


@app.function(image=image, volumes={"/models": models}, cpu=.25, memory=512,
              timeout=60, max_containers=1)
def inspect_models():
    import json
    models.reload()
    path = Path("/models/repguard_manifest.json")
    return json.loads(path.read_text()) if path.exists() else {"state": "models_not_ready"}


EVAL_VOLUME = "repguard-thesis-evals-20261018"
evaluations = modal.Volume.from_name(EVAL_VOLUME, create_if_missing=True)
HERE = Path(__file__).resolve().parent
runtime = image.pip_install("numpy==2.4.6").add_local_dir(HERE, "/root/thesis_pilot",
                                                       ignore=["__pycache__", "*.pyc"])


@app.function(image=runtime, volumes={"/models": models, "/responses": runs},
              gpu="L4", cpu=2, memory=16384, timeout=7200,
              retries=0, max_containers=1, scaledown_window=2)
def collect_inference(public):
    import json, os, subprocess, time, urllib.request
    from thesis_pilot.pipeline import collect, verify_visible
    verify_visible(public);models.reload();runs.reload()
    manifest=json.loads(Path('/models/repguard_manifest.json').read_text())
    if {k:v['digest'] for k,v in manifest['models'].items()}!=public['model_digests']:
        raise ValueError('Downloaded model digest changed')
    env={**os.environ,'OLLAMA_HOST':'127.0.0.1:11434','OLLAMA_MODELS':'/models',
         'OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'1',
         'OLLAMA_FLASH_ATTENTION':'1','OLLAMA_KV_CACHE_TYPE':'q8_0'}
    process=subprocess.Popen(['ollama','serve'],env=env,
                             stdout=subprocess.DEVNULL,stderr=open('/tmp/ollama-pilot.log','w'))
    try:
        deadline=time.monotonic()+90
        while True:
            try:
                with urllib.request.urlopen('http://127.0.0.1:11434/api/version',timeout=2) as r:
                    version=json.load(r)['version']
                break
            except Exception:
                if time.monotonic()>deadline:raise RuntimeError('New GPU Ollama failed to start')
                time.sleep(1)
        if version!=public['ollama_version']:raise ValueError('Ollama version differs')
        gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version',
                                     '--format=csv,noheader'],text=True).strip()
        environment={'app':APP_NAME,'gpu':gpu,'ollama_version':version,
                     'model_digests':public['model_digests'],'evaluation_volume_mounted':False,
                     'flash_attention':True,'kv_cache_type':'q8_0','think':False}
        checked=set()
        def request(body):
            req=urllib.request.Request('http://127.0.0.1:11434/api/chat',
                data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=240) as r:response=json.load(r)
            if body['model'] not in checked:
                with urllib.request.urlopen('http://127.0.0.1:11434/api/ps',timeout=5) as r:loaded=json.load(r)
                model=next(m for m in loaded['models'] if m['name']==body['model'])
                if model.get('size_vram',0)<.8*model.get('size',1):
                    raise RuntimeError('Inference not substantially GPU-offloaded')
                environment.setdefault('loaded_models',{})[body['model']]=model
                checked.add(body['model'])
            return response
        result=collect(public,Path('/responses')/public['run_id'],runs.commit,request,environment)
        from thesis_pilot.pipeline import atomic
        atomic(Path('/responses')/public['run_id']/'environment.json',environment);runs.commit()
        return result
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill()


@app.function(image=runtime,volumes={'/responses':runs,'/evaluations':evaluations},
              cpu=1,memory=4096,timeout=10800,retries=0,max_containers=1)
def worker(packet):
    import json
    from thesis_pilot.pipeline import atomic,save,verify_visible,load_responses
    from thesis_pilot.core import digest
    from thesis_pilot.analysis import analyze
    public=packet['visible'];verify_visible(public)
    if packet['run_id']!=public['run_id'] or digest(packet['evaluation'])!=public['evaluation_sha256']:
        raise ValueError('Evaluation/public packet mismatch')
    runs.reload();evaluations.reload()
    root=Path('/evaluations')/packet['run_id'];root.mkdir(parents=True,exist_ok=True)
    status=root/'status.json'
    if status.exists() and json.loads(status.read_text())['state']=='completed_development_review_required':
        return json.loads(status.read_text())
    atomic(root/'packet_private.json',packet)
    atomic(status,{'state':'collecting_real_models','run_id':packet['run_id'],'total':200});evaluations.commit()
    try:
        result=collect_inference.remote(public)
        runs.reload()
        if result['state']!='collection_complete':
            atomic(status,{**result,'run_id':packet['run_id']});evaluations.commit();return result
        responses=load_responses(public,Path('/responses')/packet['run_id'])
        atomic(status,{'state':'fitting_and_evaluating','completed':200,'total':200});evaluations.commit()
        analysis=analyze(packet,responses)
        saved=save(root/'analysis_private.json',analysis)
        final={'state':'completed_development_review_required','run_id':packet['run_id'],
               'completed':200,'total':200,'pilot_signal_pass':analysis['pilot_signal_pass'],
               'analysis_sha256':saved['artifact_sha256']}
        atomic(status,final);evaluations.commit();return final
    except Exception as error:
        atomic(status,{'state':'pipeline_failed','run_id':packet['run_id'],'error':repr(error)})
        evaluations.commit();raise


@app.function(image=runtime,volumes={'/responses':runs,'/evaluations':evaluations},
              cpu=.25,memory=1024,timeout=120,max_containers=1)
def inspect_run(run_id,archive=False):
    import io,json,re,zipfile
    if not re.fullmatch('[a-f0-9]{24}',run_id):raise ValueError('Invalid run ID')
    runs.reload();evaluations.reload()
    roots={'responses':Path('/responses')/run_id,'evaluation':Path('/evaluations')/run_id}
    if archive:
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
            for prefix,root in roots.items():
                for p in sorted(root.glob('*.json')):z.write(p,prefix+'/'+p.name)
        return output.getvalue()
    result={}
    for key,root in roots.items():
        p=root/'status.json'
        result[key]=json.loads(p.read_text()) if p.exists() else {'state':'not_started'}
    return result
