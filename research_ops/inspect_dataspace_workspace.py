"""Bounded, input-only ZIP inspection via HTTP Range, no benchmark execution.

Only metadata-selected input task/knowledge/small structured files are read.
Gold/output/config members are never opened. CRC is checked by zipfile; the
whole LFS archive SHA256 is NOT verified by this partial download.
"""
from __future__ import annotations

import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/general_verification_v1/source_intake/DataSpace"


class RemoteArchive(io.RawIOBase):
    def __init__(self, url, size, budget=25_000_000):
        self.url,self.size,self.budget=url,size,budget
        self.pos,self.downloaded=0,0
        self.cache={}

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos

    def seek(self, offset, whence=0):
        position=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
        if position<0 or position>self.size: raise ValueError('Seek outside archive')
        self.pos=position;return position

    def read(self, size=-1):
        size=self.size-self.pos if size<0 else min(size,self.size-self.pos)
        if size>2_000_000:raise ValueError('Read exceeds bound')
        if not size:return b''
        result=bytearray();chunk=262144
        while len(result)<size:
            start=(self.pos//chunk)*chunk;end=min(start+chunk,self.size)-1
            if start not in self.cache:
                expected=end-start+1
                if self.downloaded+expected>self.budget:raise ValueError('Download budget reached')
                req=urllib.request.Request(self.url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'})
                with urllib.request.urlopen(req,timeout=45) as response:
                    if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{self.size}':
                        raise ValueError('Server ignored/changed bounded byte range')
                    value=response.read(expected+1)
                if len(value)!=expected:raise ValueError('Truncated or oversized range')
                self.cache[start]=value;self.downloaded+=len(value)
            offset=self.pos-start;take=min(size-len(result),len(self.cache[start])-offset)
            result.extend(self.cache[start][offset:offset+take]);self.pos+=take
        return bytes(result)


def main():
    meta=json.loads((BASE/'hf_metadata.json').read_text())
    packet=json.loads((BASE/'source_inspection_public_tasks.json').read_text())
    archive=next(f for f in meta['files'] if f['rfilename']=='release/DataSpace-Benchmark.zip')
    url=f'https://huggingface.co/datasets/HKUSTDial/DataSpace/resolve/{meta["revision"]}/{archive["rfilename"]}?download=true'
    remote=RemoteArchive(url,archive['size'])
    records=[]
    with zipfile.ZipFile(remote) as z:
        members=z.infolist()
        if len(members)>20000:raise ValueError('Too many members')
        for task in packet['tasks']:
            tid=task['task_id'];marker=f'input/{tid}/'
            candidates=[m for m in members if marker in m.filename and not m.is_dir()]
            for m in candidates:
                rel=m.filename[m.filename.index(marker):]
                if '..' in Path(rel).parts:raise ValueError('Unsafe member')
            chosen=[]
            for suffix in ('/task.json','/knowledge.md'):
                match=[m for m in candidates if m.filename.endswith(suffix) and m.file_size<=500000]
                chosen.extend(match[:1])
            structured=sorted((m for m in candidates if '/context/' in m.filename and m.filename.endswith(('.csv','.json')) and m.file_size<=500000),key=lambda m:(m.file_size,m.filename))
            chosen.extend(structured[:1])
            inspected=[]
            for member in chosen:
                if not member.filename.endswith(('.json','.md','.csv')):raise ValueError('Nonwhitelisted input')
                with z.open(member) as source:data=source.read(500001)
                if len(data)>500000 or len(data)!=member.file_size:raise ValueError('Member exceeds bound')
                relative=member.filename[member.filename.index(marker):]
                dest=BASE/'partial_inputs'/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
                inspected.append({'member':member.filename,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'zip_crc32':f'{member.CRC:08x}'})
            records.append({'task_id':tid,'input_file_count_in_index':len(candidates),'inspected':inspected,
                            'complete_workspace_downloaded':False,'task_semantics_or_oracle_validated':False})
    result={'dataset_revision':meta['revision'],'scope':'Partial input-source inspection only; no gold/config/output opened, no scorer/program/model execution.',
            'archive_members':len(members),'downloaded_range_bytes':remote.downloaded,'byte_cap':remote.budget,
            'full_archive_sha256_verified':False,'published_archive_sha256':archive['lfs']['sha256'],
            'member_crc_checked':True,'tasks':records,'model_calls':0}
    (BASE/'partial_inspection.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
