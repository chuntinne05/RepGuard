"""Fourth isolated research app and weights volume; never user's original app."""
import modal
from .modal_app import runtime,OLLAMA_VERSION
APP_NAME='repguard-thesis-crossfamily-20261020'
MODEL='gemma4:26b-a4b-it-q4_K_M'
models=modal.Volume.from_name('repguard-thesis-gemma4-models-20261020',create_if_missing=True)
app=modal.App(APP_NAME)

@app.cls(image=runtime,volumes={'/models':models},gpu='L40S',cpu=2,memory=24576,
         timeout=600,max_containers=1,scaledown_window=60,retries=0)
class TatqaGemmaOllama:
    @modal.enter()
    def start(self):
        from .tatqa_plain_tools import start_server
        start_server(self,models,'/models/repguard_gemma_manifest.json')
    @modal.exit()
    def stop(self):self.process.terminate()
    @modal.method()
    def solve(self,case,current=None):
        from .tatqa_plain_tools import solve_request
        return solve_request(self,case,current,MODEL,APP_NAME)

@app.function(image=runtime,volumes={'/models':models},cpu=2,memory=4096,timeout=2400,max_containers=1,retries=0)
def download_gemma():
    import os,json,subprocess,time,urllib.request
    from pathlib import Path
    file=Path('/models/repguard_gemma_manifest.json')
    if file.exists():return json.loads(file.read_text())
    proc=subprocess.Popen(['ollama','serve'],env={**os.environ,'OLLAMA_HOST':'127.0.0.1:11434','OLLAMA_MODELS':'/models'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(90):
            try:
                with urllib.request.urlopen('http://127.0.0.1:11434/api/version',timeout=2) as r:v=json.load(r)['version']
                if v!=OLLAMA_VERSION:raise RuntimeError('Unexpected Ollama')
                break
            except OSError:time.sleep(1)
        else:raise RuntimeError('Startup timeout')
        with open('/tmp/gemma-pull.log','wb') as log:
            subprocess.run(['ollama','pull',MODEL],env={**os.environ,'OLLAMA_HOST':'127.0.0.1:11434','OLLAMA_MODELS':'/models'},stdout=log,stderr=log,timeout=2100,check=True)
        with urllib.request.urlopen('http://127.0.0.1:11434/api/tags') as r:tags=json.load(r)
        m=next(m for m in tags['models'] if m['name']==MODEL)
        if not m['digest'].startswith('5571076f3d70') or m['details']['quantization_level']!='Q4_K_M':raise RuntimeError('Public tag metadata changed')
        manifest={'app':APP_NAME,'volume':'repguard-thesis-gemma4-models-20261020','ollama':v,'models':{MODEL:m}}
        file.write_text(json.dumps(manifest,indent=2));models.commit();return manifest
    finally:proc.terminate()
