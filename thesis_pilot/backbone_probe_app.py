"""A second isolated research app; reuse pinned weights read-only, no old app."""
import modal
from .modal_app import runtime,models
APP_NAME='repguard-thesis-backbone-probe-20261019'
app=modal.App(APP_NAME)

@app.cls(image=runtime,volumes={'/models':models},gpu='L4',cpu=2,memory=16384,
         timeout=600,max_containers=1,scaledown_window=60)
class BackboneProbeOllama:
    @modal.enter()
    def start(self):
        import os,json,subprocess,time,urllib.request
        from pathlib import Path
        models.reload();self.manifest=json.loads(Path('/models/repguard_manifest.json').read_text())
        self.process=subprocess.Popen(['ollama','serve'],env={**os.environ,'OLLAMA_HOST':'127.0.0.1:11434',
            'OLLAMA_MODELS':'/models','OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'1',
            'OLLAMA_FLASH_ATTENTION':'1','OLLAMA_KV_CACHE_TYPE':'q8_0'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(90):
            try:
                with urllib.request.urlopen('http://127.0.0.1:11434/api/version',timeout=2) as r:v=json.load(r)['version']
                if v!=self.manifest['ollama']:raise RuntimeError('Ollama changed')
                return
            except OSError:time.sleep(1)
        raise RuntimeError('Ollama startup timeout')

    @modal.exit()
    def stop(self):self.process.terminate()

    @modal.method()
    def solve(self,case,model):
        import json,time,urllib.request,subprocess
        from .pot_tools import messages,SCHEMA
        from .composition_tools import canonical
        from .core import digest
        if model not in ['qwen3:8b','qwen3:14b']:raise ValueError('Unknown model')
        prompt=messages(case)
        body={'model':model,'messages':prompt,'format':SCHEMA,'stream':False,'think':True,'keep_alive':'10m',
              'options':{'temperature':0,'seed':19102026,'num_ctx':16384,'num_predict':4096}}
        start=time.monotonic()
        req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=540) as r:response=json.load(r)
        if not response.get('done') or response.get('model')!=model:raise RuntimeError('Incomplete model response')
        with urllib.request.urlopen('http://127.0.0.1:11434/api/ps') as r:loaded=json.load(r)
        m=next(m for m in loaded['models'] if m['name']==model);expected=self.manifest['models'][model]['digest']
        if m['digest']!=expected or m.get('size_vram',0)<.8*m.get('size',1):raise RuntimeError('Wrong weights/CPU fallback')
        return {'app':APP_NAME,'model':model,'model_digest':expected,'response':response,'prompt_sha256':digest(prompt),
                'verification':canonical(response['message']['content']),'wall_seconds':time.monotonic()-start,
                'live_inference':True,'evaluation_volume_mounted':False,
                'actual_thinking_chars':len(response['message'].get('thinking','')),
                'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True).strip()}
