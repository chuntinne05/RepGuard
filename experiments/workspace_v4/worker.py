"""Isolated GPU inference and source-only CPU tool runtime; no evaluation mount."""
from __future__ import annotations

import json
from pathlib import Path
import modal

from .agent import MODELS

APP_NAME='repguard-workspace-v4-pilot-20261109'
RUN_VOLUME='repguard-workspace-v4-runs-20261109'
app=modal.App(APP_NAME,include_source=False)
runs=modal.Volume.from_name(RUN_VOLUME,create_if_missing=True)
inputs=modal.Volume.from_name('repguard-workspace-v4-inputs-20261109').read_only()
qwen=modal.Volume.from_name('repguard-thesis-modern-models-20261019').read_only()
gemma=modal.Volume.from_name('repguard-thesis-gemma4-models-20261020').read_only()
allowed={'__init__.py','tools.py','agent.py','worker.py'}
base=modal.Image.debian_slim(python_version='3.11')
gpu_image=(modal.Image.debian_slim(python_version='3.11').apt_install('curl','ca-certificates','zstd')
           .run_commands('curl -fsSL https://ollama.com/install.sh -o /tmp/install-ollama.sh','OLLAMA_VERSION=0.40.6 sh /tmp/install-ollama.sh'))
for name in sorted(allowed):
    target='/root/experiments/workspace_v4/'+name
    base=base.add_local_file(Path(__file__).parent/name,target)
    gpu_image=gpu_image.add_local_file(Path(__file__).parent/name,target)


def start(obj,role,manifest):
    import os,subprocess,time,urllib.request
    obj.role=role
    m=json.loads(Path('/models',manifest).read_text());cfg=MODELS[role]
    if m['models'][cfg['name']]['digest']!=cfg['digest']:raise RuntimeError('Wrong model weights')
    obj.process=subprocess.Popen(['ollama','serve'],env={**os.environ,'OLLAMA_HOST':'127.0.0.1:11434','OLLAMA_MODELS':'/models','OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'1','OLLAMA_FLASH_ATTENTION':'1','OLLAMA_KV_CACHE_TYPE':'q8_0'},stdout=subprocess.DEVNULL,stderr=open('/tmp/workspace-v4-ollama.log','w'))
    for _ in range(90):
        try:
            with urllib.request.urlopen('http://127.0.0.1:11434/api/version',timeout=2) as r:obj.version=json.load(r)['version']
            if obj.version!='0.40.6':raise RuntimeError('Wrong Ollama version')
            return
        except OSError:time.sleep(1)
    raise RuntimeError('Server failed to start')


def infer(obj,messages):
    import urllib.request,subprocess
    cfg=MODELS[obj.role]
    body={'model':cfg['name'],'messages':messages,'stream':False,'think':False,'format':'json','keep_alive':'20m',
          'options':{'temperature':0,'seed':20261109,'num_ctx':32768,'num_predict':2048}}
    req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=300) as r:response=json.load(r)
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps',timeout=10) as r:loaded=json.load(r)
    model=next(m for m in loaded['models'] if m['name']==cfg['name'])
    if model['digest']!=cfg['digest'] or model.get('size_vram',0)<.8*model['size']:raise RuntimeError('Wrong digest or CPU fallback')
    if not response.get('done') or response.get('model')!=cfg['name']:raise RuntimeError('Incomplete response')
    return {'provider':'ollama_modal','app':APP_NAME,'model':cfg['name'],'model_digest':cfg['digest'],'ollama_version':obj.version,
            'request_body':body,'response':response,'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version','--format=csv,noheader'],text=True).strip(),
            'evaluation_volume_mounted':False,'reference_reconstruction_code_in_image':False,'weights_read_only':True,'live_inference':True}


@app.cls(image=gpu_image,volumes={'/models':qwen},gpu='L40S',cpu=2,memory=24576,timeout=600,max_containers=1,scaledown_window=120,retries=0)
class A:
    @modal.enter()
    def enter(self):start(self,'A','repguard_modern_manifest.json')
    @modal.method()
    def run(self,messages):return infer(self,messages)
    @modal.exit()
    def exit(self):self.process.terminate()


@app.cls(image=gpu_image,volumes={'/models':gemma},gpu='L40S',cpu=2,memory=24576,timeout=600,max_containers=1,scaledown_window=120,retries=0)
class B:
    @modal.enter()
    def enter(self):start(self,'B','repguard_gemma_manifest.json')
    @modal.method()
    def run(self,messages):return infer(self,messages)
    @modal.exit()
    def exit(self):self.process.terminate()


@app.function(image=base,volumes={'/sources':inputs,'/runs':runs},cpu=2,memory=4096,timeout=14400,max_containers=1,retries=0)
def run_study(plan,packet):
    from threading import Lock
    from experiments.workspace_v4.agent import collect,digest,write
    from experiments.workspace_v4.tools import sha
    for forbidden in ('preflight.py','readiness.py'):
        if Path('/root/experiments/workspace_v4',forbidden).exists():raise RuntimeError('Reference reconstruction code present')
    if Path('/evaluation').exists() or Path('/sources/output').exists():raise RuntimeError('Evaluation material present in source runtime')
    for name,expected in plan['runtime_hashes'].items():
        if sha(Path('/root/experiments/workspace_v4')/name)!=expected:raise RuntimeError('Runtime source mismatch')
    if digest(packet)!=plan['public_packet_digest']:raise RuntimeError('Input packet mismatch')
    code_files=sorted(p.name for p in Path('/root/experiments/workspace_v4').glob('*.py'))
    if set(code_files)!=allowed:raise RuntimeError('Unexpected runtime source membership')
    write(Path('/runs')/plan['plan_id']/'isolation_receipt.json',{'plan_id':plan['plan_id'],'runtime_python_files':code_files,
          'runtime_hashes':plan['runtime_hashes'],'evaluation_path_present':False,'source_output_path_present':False,
          'automatic_source_inclusion':False,'check_stage':'before any model invocation'})
    runs.commit()
    # Validate EVERY selected adapter before the first model call, not task by task.
    from experiments.workspace_v4.tools import materialize,relation_fingerprint
    for task in packet['tasks']:
        derived=Path('/runs')/plan['plan_id']/'derived'/task['id']/'workspace.sqlite'
        if not derived.exists():materialize(Path('/sources/input')/task['id']/'context',derived)
        if relation_fingerprint(derived)!=plan['derived_relation_sha256'][task['id']]:raise RuntimeError('All-task pre-inference adapter check failed:'+task['id'])
    write(Path('/runs')/plan['plan_id']/'adapter_preflight_receipt.json',{'plan_id':plan['plan_id'],'all_tasks_checked_before_inference':True,
          'relation_fingerprints':plan['derived_relation_sha256']})
    runs.commit()
    lock=Lock();a,b=A(),B()
    def commit():
        with lock:runs.commit()
    return collect(plan,packet,Path('/sources'),Path('/runs')/plan['plan_id'],lambda role,messages:(a if role=='A' else b).run.remote(messages),commit)


def launch(plan_name='registered_plan.json',receipt_name='launch_receipt.json'):
    from datetime import datetime,timezone
    from .agent import write
    from .tools import sha
    root=Path(__file__).resolve().parents[2];out=root/'results/workspace_v4'
    plan=json.loads((out/plan_name).read_text());packet=json.loads((out/plan.get('public_packet_file','public_packet.json')).read_text())
    if (out/receipt_name).exists():raise RuntimeError('Already launched; no duplicate')
    for rel,expected in plan['source_hashes'].items():
        if sha(root/rel)!=expected:raise RuntimeError('Frozen source changed:'+rel)
    with app.run(detach=True):
        call=run_study.spawn(plan,packet)
        receipt={'plan_id':plan['plan_id'],'app_id':app.app_id,'function_call_id':call.object_id,'app_name':APP_NAME,'max_model_calls':plan['max_model_calls'],'created_utc':datetime.now(timezone.utc).isoformat()}
        write(out/receipt_name,receipt);print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--plan',default='registered_plan.json');parser.add_argument('--receipt',default='launch_receipt.json')
    args=parser.parse_args();launch(args.plan,args.receipt)
