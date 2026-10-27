"""Private live-inference backend on the NEW app, deployed after the pilot finishes."""
import modal
from thesis_pilot.modal_app import app,runtime,models,APP_NAME


@app.cls(image=runtime,volumes={'/models':models},gpu='L4',cpu=2,memory=16384,
         timeout=600,max_containers=1,scaledown_window=60)
class LiveOllama:
    @modal.method()
    def pot_solve(self,case):
        import json,time,urllib.request,subprocess
        from thesis_pilot.pot_tools import messages,verify,SCHEMA
        from thesis_pilot.core import digest
        prompt=messages(case);name='qwen3:14b'
        body={'model':name,'messages':prompt,'format':SCHEMA,'stream':False,'think':True,
            'keep_alive':'10m','options':{'temperature':0,'seed':18102026,'num_ctx':16384,'num_predict':4096}}
        start=time.monotonic()
        req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=540) as r:response=json.load(r)
        if not response.get('done') or response.get('model')!=name:raise RuntimeError('Incomplete PoT response')
        with urllib.request.urlopen('http://127.0.0.1:11434/api/ps') as r:loaded=json.load(r)
        m=next(m for m in loaded['models'] if m['name']==name);expected=self.manifest['models'][name]['digest']
        if m['digest']!=expected or m.get('size_vram',0)<.8*m.get('size',1):raise RuntimeError('Wrong weights/CPU fallback')
        return {'app':APP_NAME,'model':name,'model_digest':expected,'response':response,
            'prompt_sha256':digest(prompt),'verification':verify(response['message']['content']),
            'wall_seconds':time.monotonic()-start,'live_inference':True,'evaluation_volume_mounted':False,
            'actual_thinking_chars':len(response['message'].get('thinking','')),
            'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True).strip()}

    @modal.method()
    def competence_solve(self,case,contract):
        import json,time,urllib.request,subprocess
        from thesis_pilot.competence_tools import messages,verify,DSL_SCHEMA,SIMPLE_SCHEMA
        from thesis_pilot.core import digest
        prompt=messages(case,contract);name='qwen3:14b'
        body={'model':name,'messages':prompt,'format':DSL_SCHEMA if contract=='dsl_native' else SIMPLE_SCHEMA,
            'stream':False,'think':True,'keep_alive':'10m','options':{'temperature':0,'seed':18102026,'num_ctx':16384,'num_predict':4096}}
        start=time.monotonic()
        req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=540) as r:response=json.load(r)
        if not response.get('done') or response.get('model')!=name:raise RuntimeError('Incomplete competence response')
        with urllib.request.urlopen('http://127.0.0.1:11434/api/ps') as r:loaded=json.load(r)
        m=next(m for m in loaded['models'] if m['name']==name);expected=self.manifest['models'][name]['digest']
        if m['digest']!=expected or m.get('size_vram',0)<.8*m.get('size',1):raise RuntimeError('Wrong weights/CPU fallback')
        return {'app':APP_NAME,'model':name,'model_digest':expected,'contract':contract,'response':response,
            'prompt_sha256':digest(prompt),'verification':verify(case,response['message']['content'],contract),
            'wall_seconds':time.monotonic()-start,'live_inference':True,'evaluation_volume_mounted':False,
            'actual_thinking_chars':len(response['message'].get('thinking','')),
            'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True).strip()}

    @modal.method()
    def causal_solve(self,case,action='initial',initial=None,oracle_sources=None):
        import json,time,urllib.request,subprocess
        from thesis_pilot.causal_tools import SCHEMA,messages,verify
        from thesis_pilot.core import digest
        prompt=messages(case,action,initial,oracle_sources);model_name='qwen3:14b'
        body={'model':model_name,'messages':prompt,'format':SCHEMA,'stream':False,
              'think':False,'keep_alive':'10m','options':{'temperature':0,'seed':18102026,
                  'num_ctx':16384,'num_predict':1536}}
        start=time.monotonic()
        req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=300) as r:response=json.load(r)
        if not response.get('done') or response.get('model')!=model_name:raise RuntimeError('Incomplete causal response')
        with urllib.request.urlopen('http://127.0.0.1:11434/api/ps') as r:loaded=json.load(r)
        model=next(m for m in loaded['models'] if m['name']==model_name)
        expected=self.manifest['models'][model_name]['digest']
        if model['digest']!=expected or model.get('size_vram',0)<.8*model.get('size',1):raise RuntimeError('Wrong weights or CPU fallback')
        return {'app':APP_NAME,'model':model_name,'model_digest':expected,'action':action,
            'prompt_sha256':digest(prompt),'response':response,
            'verification':verify(case,response['message']['content'],action,initial),
            'wall_seconds':time.monotonic()-start,'live_inference':True,
            'oracle_diagnostic':oracle_sources is not None,'evaluation_volume_mounted':False,
            'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True).strip()}

    @modal.enter()
    def start(self):
        import os,json,subprocess,time,urllib.request
        from pathlib import Path
        models.reload()
        self.manifest=json.loads(Path('/models/repguard_manifest.json').read_text())
        self.process=subprocess.Popen(['ollama','serve'],env={**os.environ,
            'OLLAMA_HOST':'127.0.0.1:11434','OLLAMA_MODELS':'/models',
            'OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'2',
            'OLLAMA_FLASH_ATTENTION':'1','OLLAMA_KV_CACHE_TYPE':'q8_0'},
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(90):
            try:
                with urllib.request.urlopen('http://127.0.0.1:11434/api/version',timeout=2) as r:
                    version=json.load(r)['version']
                if version!=self.manifest['ollama']:raise RuntimeError('Wrong live Ollama version')
                return
            except OSError:time.sleep(1)
        raise RuntimeError('Live Ollama startup timeout')

    @modal.exit()
    def stop(self):
        self.process.terminate()

    @modal.method()
    def solve(self,case,agent_id,variant='frozen'):
        import json,time,urllib.request,subprocess
        from thesis_pilot.core import AGENTS,SCHEMA,prompt,digest
        from thesis_pilot.source_checks import strict_verify
        agent=next(a for a in AGENTS if a['id']==agent_id)
        messages=prompt(case,agent)
        if variant not in ['frozen','unconstrained_json','reasoning_first','explicit_status','schema_prompt']:
            raise ValueError('Unknown diagnostic contract')
        schema=SCHEMA
        if variant in ['reasoning_first','explicit_status','schema_prompt']:
            schema={**SCHEMA,'required':['reasoning',*SCHEMA['required']],
                    'properties':{'reasoning':{'type':'string'},**SCHEMA['properties']}}
            messages[0]['content']+='\nFirst write a reasoning field identifying the relevant source values and arithmetic. Then fill all original fields. Do not abstain before examining the document.'
        if variant in ['explicit_status','schema_prompt']:
            messages[0]['content']+='\nSet status="answer" when the source evidence supports an executable answer. Use status="insufficient_evidence" ONLY when required evidence is actually missing. Your status must agree with your reasoning.'
        if variant=='schema_prompt':
            messages[0]['content']+='\nThe complete output JSON schema is:\n'+json.dumps(schema,ensure_ascii=False)
        body={'model':agent['model'],'messages':messages,
              'stream':False,'think':False,'keep_alive':'10m','options':{
                  'temperature':0,'seed':18102026,'num_ctx':16384,'num_predict':agent['num_predict']}}
        if variant!='unconstrained_json':body['format']=schema
        start=time.monotonic()
        req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(body).encode(),
                                   headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=300) as r:response=json.load(r)
        if not response.get('done') or response.get('model')!=agent['model']:
            raise RuntimeError('Incomplete/unexpected real response')
        with urllib.request.urlopen('http://127.0.0.1:11434/api/ps') as r:loaded=json.load(r)
        model=next(m for m in loaded['models'] if m['name']==agent['model'])
        expected=self.manifest['models'][agent['model']]['digest']
        if model['digest']!=expected or model.get('size_vram',0)<.8*model.get('size',1):
            raise RuntimeError('Wrong weights or CPU fallback')
        raw=response['message']['content']
        if variant in ['reasoning_first','explicit_status','schema_prompt']:
            try:
                answer=json.loads(raw);answer.pop('reasoning',None);raw=json.dumps(answer)
            except (ValueError,TypeError,AttributeError):pass
        return {'app':APP_NAME,'agent':agent_id,'model':agent['model'],'model_digest':expected,
                'prompt_sha256':digest(messages),'response':response,
                'verification':strict_verify(case,raw),'contract_variant':variant,
                'wall_seconds':time.monotonic()-start,'live_inference':True,
                'evaluation_volume_mounted':False,
                'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True).strip()}

    @modal.method()
    def typed_solve(self,case,thinking=False):
        import json,time,urllib.request,subprocess
        from thesis_pilot.typed_tools import SCHEMA,messages,verify
        from thesis_pilot.core import digest
        prompt=messages(case);model_name='qwen3:14b'
        body={'model':model_name,'messages':prompt,'format':SCHEMA,'stream':False,
              'think':bool(thinking),'keep_alive':'10m','options':{'temperature':0,'seed':18102026,
                  'num_ctx':16384,'num_predict':4096 if thinking else 1536}}
        start=time.monotonic()
        req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=540 if thinking else 300) as r:response=json.load(r)
        if not response.get('done') or response.get('model')!=model_name:raise RuntimeError('Incomplete typed real response')
        with urllib.request.urlopen('http://127.0.0.1:11434/api/ps') as r:loaded=json.load(r)
        model=next(m for m in loaded['models'] if m['name']==model_name)
        expected=self.manifest['models'][model_name]['digest']
        if model['digest']!=expected or model.get('size_vram',0)<.8*model.get('size',1):raise RuntimeError('Wrong typed model or CPU fallback')
        return {'app':APP_NAME,'agent':'B','model':model_name,'model_digest':expected,
            'prompt_sha256':digest(prompt),'response':response,'verification':verify(case,response['message']['content']),
            'contract_variant':'typed_reasoning' if thinking else 'typed_tools',
            'requested_thinking':bool(thinking),'actual_thinking_chars':len(response['message'].get('thinking','')),
            'wall_seconds':time.monotonic()-start,'live_inference':True,
            'evaluation_volume_mounted':False,'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True).strip()}
