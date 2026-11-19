from pathlib import Path
import modal

APP_NAME='repguard-routerbench-intake-v2'
app=modal.App(APP_NAME)
volume=modal.Volume.from_name('repguard-routerbench-intake-checkpoints-v1',create_if_missing=True)
HERE=Path(__file__).resolve().parent
image=(modal.Image.debian_slim(python_version='3.11').pip_install('ijson==3.3.0')
       .env({'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}))
for name in ('routerbench_intake_core.py','routerbench_intake_v2_core.py','routerbench_intake_v2_pipeline.py'):
    image=image.add_local_file(HERE/name,'/root/'+name)


@app.function(image=image,volumes={'/checkpoints':volume},cpu=1,memory=4096,timeout=86400,retries=2,max_containers=1)
def worker(packet:dict):
    from routerbench_intake_v2_pipeline import run
    return run(packet,'/checkpoints/runs/'+packet['run_id'],volume.commit)


@app.function(image=image,volumes={'/checkpoints':volume},cpu=.25,memory=512,timeout=180)
def inspect_run(run_id:str,archive:bool=False):
    import io,json,re,zipfile
    if not re.fullmatch(r'[a-f0-9]{24}',run_id):
        raise ValueError('Invalid run ID')
    volume.reload(); root=Path('/checkpoints/runs')/run_id
    if archive:
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
            for path in sorted(root.glob('*.json')):
                z.write(path,path.name)
        return buffer.getvalue()
    path=root/'status.json'
    return json.loads(path.read_text()) if path.exists() else {'state':'not_started'}
