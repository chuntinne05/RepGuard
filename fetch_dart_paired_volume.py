"""Fetch a terminal paired run incrementally using the official Volume read API."""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import modal

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'infra/modal'))
from neural_pipeline import atomic
from paired_history_pipeline import validate


def main():
    out=ROOT/'results/dart_paired_history_v1'
    receipt=json.loads((out/'receipt.json').read_text()); run_id=receipt['run_id']
    if not re.fullmatch('[a-f0-9]{24}',run_id):
        raise ValueError('Invalid run ID')
    volume=modal.Volume.from_name('repguard-paired-history-checkpoints-v1')
    def read(name):
        return name,json.loads(b''.join(volume.read_file('/runs/'+run_id+'/'+name)))
    _,status=read('status.json')
    if status['state']!='completed_review_required':
        raise ValueError('Use the status command while the run is still active')
    _,ledger=read('ledger.json'); target=out/'cloud'; target.mkdir(exist_ok=True)
    names=[]; skipped=0
    for key,sha in ledger.items():
        if not re.fullmatch(r'0\.(05|1|2)_fold[0-4]_seed(1[0-9]|[0-9])',key):
            raise ValueError('Unexpected case ID')
        name='case_'+key+'.json'; path=target/name
        if path.exists():
            try:
                row=json.loads(path.read_text()); validate(row)
                if row['run_id']==run_id and row['case']==key and row['artifact_sha256']==sha:
                    skipped+=1; continue
            except (ValueError,KeyError):
                pass
        names.append(name)
    names += ['input_private.json','environment.json','analysis_0.05.json','analysis_0.1.json','analysis_0.2.json','analysis.json']
    with ThreadPoolExecutor(max_workers=8) as pool:
        for name,value in pool.map(read,names):
            if name.startswith('case_'):
                validate(value)
                if value['run_id']!=run_id or value['artifact_sha256']!=ledger[value['case']]:
                    raise ValueError('Downloaded case identity mismatch')
            atomic(target/name,value)
    atomic(target/'ledger.json',ledger); atomic(target/'status.json',status)
    print(json.dumps({'verified_cached_cases':skipped,'files_downloaded':len(names),'case_total':len(ledger),'state':status['state']}))


if __name__=='__main__':
    main()
