"""Unrestricted PoT review capability control shared across model families."""
import json
from .tatqa_scope_tools import SYSTEM,PLAIN,messages as base_messages

REVIEW='''Independently audit this fallible current calculation against the full original
table and paragraphs. Check metric, entity, periods, aggregation, numerator,
denominator, sign, and unit/scale conversion. Keep it if supported; otherwise
derive a corrected program. You may change ANY field and use document numeric
literals directly. You are NOT restricted to any previous bindings or variable
names. Execution is only a syntax/arithmetic check, not proof of correctness.
Return the same reasoning/status/code/scale JSON schema.'''
def messages(case,current=None):
    prompt=base_messages(case,'plain')
    if current is None:return prompt
    if set(current)!={'proposal','execution'}:raise ValueError('Unexpected current fields')
    data=json.loads(prompt[1]['content']);data['current_proposal']=current
    return [{'role':'system','content':SYSTEM+'\n'+REVIEW+'\n'+json.dumps(PLAIN)},
            {'role':'user','content':json.dumps(data,ensure_ascii=False)}]

def start_server(instance,volume,manifest_path):
    import os,subprocess,time,urllib.request
    from pathlib import Path
    volume.reload();instance.manifest=json.loads(Path(manifest_path).read_text())
    instance.process=subprocess.Popen(['ollama','serve'],env={**os.environ,'OLLAMA_HOST':'127.0.0.1:11434',
        'OLLAMA_MODELS':'/models','OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'1',
        'OLLAMA_FLASH_ATTENTION':'1','OLLAMA_KV_CACHE_TYPE':'q8_0'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(90):
        try:
            with urllib.request.urlopen('http://127.0.0.1:11434/api/version',timeout=2) as r:v=json.load(r)['version']
            if v!=instance.manifest['ollama']:raise RuntimeError('Ollama changed')
            return
        except OSError:time.sleep(1)
    raise RuntimeError('Startup timeout')

def solve_request(instance,case,current,model,app_name):
    import time,urllib.request,subprocess
    from .core import digest
    from .tatqa_scope_tools import verify
    prompt=messages(case,current)
    body={'model':model,'messages':prompt,'format':PLAIN,'stream':False,'think':False,'keep_alive':'10m',
          'options':{'temperature':0,'seed':20102026,'num_ctx':16384,'num_predict':4096}}
    start=time.monotonic();req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=540) as r:response=json.load(r)
    if not response.get('done') or response.get('model')!=model:raise RuntimeError('Incomplete response')
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps') as r:loaded=json.load(r)
    m=next(m for m in loaded['models'] if m['name']==model);expected=instance.manifest['models'][model]['digest']
    if m['digest']!=expected or m.get('size_vram',0)<.8*m.get('size',1):raise RuntimeError('Wrong weights/CPU fallback')
    return {'app':app_name,'model':model,'model_digest':expected,'response':response,'prompt_sha256':digest(prompt),
            'verification':verify(case,response['message']['content'],plain=True),'wall_seconds':time.monotonic()-start,
            'live_inference':True,'evaluation_volume_mounted':False,'actual_thinking_chars':len(response['message'].get('thinking','')),
            'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True).strip()}
