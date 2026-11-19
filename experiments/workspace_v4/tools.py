"""Bounded workspace tools. Original inputs read-only; derived tables separate.

No arbitrary code, shell, network, hidden reference or model-generated paths
outside the task workspace. Execution receipts do not certify task semantics.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sqlite3
from pathlib import Path


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def quote(value): return '"'+value.replace('"','""')+'"'


def table_alias(name,kind,tables):
    if name not in tables:return name
    alias=kind+'__'+name
    if alias in tables:raise ValueError('Ambiguous derived table alias:'+alias)
    return alias


def relation_fingerprint(database):
    """Logical snapshot ID; SQLite binary headers vary by platform/version."""
    conn=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
    tables={}
    try:
        names=sorted(r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        for name in names:
            columns=[r[1] for r in conn.execute('PRAGMA table_info('+quote(name)+')')]
            h=hashlib.sha256(json.dumps(columns,ensure_ascii=False,separators=(',',':')).encode()+b'\n')
            for row in conn.execute('SELECT * FROM '+quote(name)+' ORDER BY rowid'):
                cells=[{'blob_hex':x.hex()} if isinstance(x,bytes) else x for x in row]
                h.update(json.dumps(cells,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()+b'\n')
            tables[name]=h.hexdigest()
    finally:conn.close()
    return hashlib.sha256(json.dumps(tables,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def infer_type(values):
    present=[v for v in values if v is not None and v!='']
    if not present:return 'TEXT'
    if all(isinstance(v,int) and not isinstance(v,bool) or isinstance(v,str) and re.fullmatch(r'-?(?:0|[1-9]\d*)',v) for v in present):return 'INTEGER'
    if all(isinstance(v,(int,float)) and not isinstance(v,bool) or isinstance(v,str) and re.fullmatch(r'[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][+-]?\d+)?',v) for v in present):
        # Text identifiers like000423 must retain their representation.
        if any(isinstance(v,str) and re.fullmatch(r'0\d+',v) for v in present):return 'TEXT'
        return 'REAL'
    return 'TEXT'


def bind_value(value, affinity):
    """Parse numeric text in Python before binding, across SQLite versions.

    SQLite's text-to-REAL parser differs by one binary64 ULP between versions.
    Never normalize fingerprints to hide such differences in the query inputs.
    """
    if value is None:return None
    if isinstance(value,str) and affinity=='REAL':return float(value)
    if isinstance(value,str) and affinity=='INTEGER':return int(value)
    return value


def materialize(context: Path, destination: Path):
    """Deterministic convenience view of original SQL/CSV/record-oriented JSON.

    This adapter records every source mapping. It does not infer domain meaning,
    validate joins, or reproduce arbitrary Python/dataframe semantics.
    """
    context=context.resolve();destination=destination.resolve()
    if destination.is_relative_to(context):raise ValueError('Derived DB must be outside input')
    if destination.exists():raise ValueError('Do not overwrite a derived snapshot')
    destination.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(destination);tables={};unsupported=[]
    try:
        for path in sorted(context.rglob('*')):
            if not path.is_file():continue
            rel=str(path.relative_to(context));ext=path.suffix.lower()
            if ext not in ('.sqlite','.csv','.json'):continue
            if path.stat().st_size>500_000_000:raise ValueError('Source file cap')
            if ext=='.sqlite':
                source=sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True)
                source.execute('PRAGMA query_only=ON');source.execute('PRAGMA trusted_schema=OFF')
                try:
                    names=[r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
                    for name in names:
                        alias=table_alias(name,'database_'+path.stem,tables)
                        columns=list(source.execute('PRAGMA table_info('+quote(name)+')'))
                        defs=','.join(quote(c[1])+' '+(c[2] if c[2].upper() in {'TEXT','REAL','INTEGER','BLOB','NUMERIC',''} else 'TEXT') for c in columns)
                        conn.execute('CREATE TABLE '+quote(alias)+' ('+defs+')')
                        source_rows=source.execute('SELECT * FROM '+quote(name))
                        count=0;sql='INSERT INTO '+quote(alias)+' VALUES ('+','.join('?' for _ in columns)+')'
                        while True:
                            rows=source_rows.fetchmany(1000)
                            if not rows:break
                            count+=len(rows)
                            if count>2_000_000:raise ValueError('Source row cap')
                            conn.executemany(sql,rows)
                        tables[alias]={'source':rel,'source_sha256':sha(path),'source_table':name,'rows':count,'columns':[c[1] for c in columns],'kind':'sqlite_copy'}
                finally:source.close()
                continue
            if ext=='.csv':
                with path.open(encoding='utf-8-sig',newline='') as f:
                    reader=csv.reader(f);headers=next(reader,[]);rows=list(reader)
                if not headers or len(set(headers))!=len(headers) or any(not h for h in headers):raise ValueError('Ambiguous CSV header:'+rel)
                if any(len(r)!=len(headers) for r in rows):raise ValueError('Ragged CSV:'+rel)
                rows=[[None if v=='' else v for v in row] for row in rows]
            else:
                obj=json.loads(path.read_text())
                records=obj.get('records') if isinstance(obj,dict) else obj
                if not isinstance(records,list) or not records or not all(isinstance(r,dict) for r in records):
                    unsupported.append(rel);continue
                headers=list(dict.fromkeys(k for r in records for k in r))
                rows=[[json.dumps(r.get(k),ensure_ascii=False) if isinstance(r.get(k),(list,dict)) else r.get(k) for k in headers] for r in records]
            name=table_alias(path.stem,ext[1:],tables)
            if len(rows)>2_000_000:raise ValueError('Source row cap')
            types=[infer_type([r[i] for r in rows]) for i in range(len(headers))]
            conn.execute('CREATE TABLE '+quote(name)+' ('+','.join(quote(h)+' '+t for h,t in zip(headers,types))+')')
            bound_rows=([bind_value(v,t) for v,t in zip(row,types)] for row in rows)
            conn.executemany('INSERT INTO '+quote(name)+' VALUES ('+','.join('?' for _ in headers)+')',bound_rows)
            tables[name]={'source':rel,'source_sha256':sha(path),'rows':len(rows),'columns':headers,'inferred_affinities':types,'kind':ext[1:]+'_import'}
        conn.commit()
    except BaseException:
        conn.close();destination.unlink(missing_ok=True);raise
    conn.close()
    manifest={'derived_sha256':sha(destination),'logical_relation_sha256':relation_fingerprint(destination),'tables':tables,'unsupported_structured_files':unsupported,
              'semantics_certified':False,'numeric_limit':'SQLite numeric arithmetic uses binary64; task-specific precision must be checked independently.'}
    destination.with_suffix('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return manifest


class WorkspaceTools:
    def __init__(self,context,derived_database,artifacts,pdf_views=None):
        self.context=Path(context).resolve();self.db=Path(derived_database).resolve();self.artifacts=Path(artifacts).resolve()
        if self.artifacts.is_relative_to(self.context):raise ValueError('Artifact directory must be outside inputs')
        self.artifacts.mkdir(parents=True,exist_ok=True)
        self.files={str(p.relative_to(self.context)):p for p in self.context.rglob('*') if p.is_file() and p.resolve().is_relative_to(self.context)}
        self.manifest=json.loads(self.db.with_suffix('.manifest.json').read_text())
        if sha(self.db)!=self.manifest['derived_sha256']:raise ValueError('Derived snapshot changed')
        self.pdf_views=pdf_views or {};self.results={};self.trace=[]

    def _path(self,path):
        if path not in self.files:raise ValueError('Path not in public workspace')
        return self.files[path]

    def catalog(self):
        return {'files':[{'path':k,'bytes':p.stat().st_size} for k,p in sorted(self.files.items())],
                'tables':[{'name':k,'source':v['source']} for k,v in self.manifest['tables'].items()]}

    def schema(self,table):
        if table not in self.manifest['tables']:raise ValueError('Unknown table')
        return self.manifest['tables'][table]

    def read(self,path,offset=0,limit=8000,page=1):
        p=self._path(path)
        if not isinstance(offset,int) or offset<0 or not isinstance(limit,int) or not 1<=limit<=12000:raise ValueError('Read bound')
        if p.suffix.lower()=='.pdf':
            pages=self.pdf_views.get(path)
            if pages is None:raise ValueError('PDF text view unavailable; cannot infer missing content')
            if not isinstance(page,int) or not 1<=page<=len(pages):raise ValueError('Page out of range')
            text=pages[page-1]['text'];locator={'page':page,'pages':len(pages)}
        elif p.suffix.lower() in {'.csv','.json','.md','.txt'}:
            text=p.read_text(encoding='utf-8-sig');locator={}
        else:raise ValueError('Use schema/query for database files')
        return {'path':path,'source_sha256':sha(p),'offset':offset,'text':text[offset:offset+limit],
                'truncated':offset+limit<len(text),**locator}

    def search(self,literal,path=None):
        if not isinstance(literal,str) or not 1<=len(literal)<=128:raise ValueError('Search bound')
        paths=[path] if path is not None else sorted(self.files)
        hits=[]
        for name in paths:
            p=self._path(name)
            if p.suffix.lower()=='.pdf':
                texts=[(i+1,x['text']) for i,x in enumerate(self.pdf_views.get(name,[]))]
            elif p.suffix.lower() in {'.csv','.json','.md','.txt'}:
                texts=[(None,p.read_text(encoding='utf-8-sig'))]
            else:continue
            for page,text in texts:
                at=text.casefold().find(literal.casefold())
                if at>=0:hits.append({'path':name,'page':page,'offset':max(at-250,0),'excerpt':text[max(at-250,0):at+650]})
                if len(hits)==12:return {'hits':hits,'truncated':True}
        return {'hits':hits,'truncated':False}

    def query(self,sql):
        if not isinstance(sql,str) or not 1<=len(sql)<=16000:raise ValueError('SQL bound')
        conn=sqlite3.connect(self.db.as_uri()+'?mode=ro&immutable=1',uri=True)
        # Some macOS Python builds omit extension loading entirely.
        if hasattr(conn,'enable_load_extension'):conn.enable_load_extension(False)
        conn.execute('PRAGMA query_only=ON');conn.execute('PRAGMA trusted_schema=OFF')
        allowed_functions={'abs','avg','count','sum','total','min','max','round','coalesce','ifnull','nullif','lower','upper','trim','ltrim','rtrim','length','substr','substring','replace','date','datetime','strftime','julianday','unixepoch','printf','typeof','cast','like','glob','row_number','rank','dense_rank'}
        used=set();steps=0
        def authorize(action,a,b,database,trigger):
            if action==sqlite3.SQLITE_READ:
                if a not in self.manifest['tables']:return sqlite3.SQLITE_DENY
                used.add(a);return sqlite3.SQLITE_OK
            if action==sqlite3.SQLITE_SELECT:return sqlite3.SQLITE_OK
            if action==sqlite3.SQLITE_FUNCTION and (b or '').lower() in allowed_functions:return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY
        def progress():
            nonlocal steps
            steps+=1000;return int(steps>2_000_000)
        conn.set_authorizer(authorize);conn.set_progress_handler(progress,1000)
        try:
            cursor=conn.execute(sql)
            if cursor.description is None:raise ValueError('Only tabular SELECT allowed')
            columns=[c[0] for c in cursor.description];rows=cursor.fetchmany(100001)
            if len(rows)>100000:raise ValueError('Result exceeds100000rows; no partial export')
            if not used:raise ValueError('Query must read at least one public table')
        finally:conn.close()
        identity=hashlib.sha256((self.manifest['derived_sha256']+'\n'+sql).encode()).hexdigest()[:20]
        result_id='query_'+identity
        path=self.artifacts/(result_id+'.csv')
        with path.open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f);w.writerow(columns);w.writerows(rows)
        if path.stat().st_size>20*1024*1024:
            path.unlink();raise ValueError('Result exceeds20MiB; no partial export')
        record={'result_id':result_id,'rows':len(rows),'columns':columns,'preview':rows[:12],
                'preview_truncated':len(rows)>12,'sql':sql,'output_sha256':sha(path),
                'sources':[self.manifest['tables'][t] for t in sorted(used)],
                'execution_ok':True,'task_semantics_verified':False}
        self.results[result_id]=record;self.trace.append(record)
        return record

    def save_table(self,columns,rows):
        if not isinstance(columns,list) or not columns or not all(isinstance(c,str) for c in columns) or len(set(columns))!=len(columns):raise ValueError('Table columns')
        if not isinstance(rows,list) or len(rows)>5000 or any(not isinstance(r,list) or len(r)!=len(columns) for r in rows):raise ValueError('Table rows')
        if any(isinstance(x,(dict,list)) for r in rows for x in r):raise ValueError('Scalar cells required')
        data=io.StringIO(newline='');w=csv.writer(data);w.writerow(columns);w.writerows(rows)
        value=data.getvalue()
        if len(value.encode())>1_000_000:raise ValueError('Table byte cap')
        rid='asserted_'+hashlib.sha256(value.encode()).hexdigest()[:20]
        p=self.artifacts/(rid+'.csv');p.write_text(value)
        r={'result_id':rid,'rows':len(rows),'columns':columns,'output_sha256':sha(p),'execution_ok':False,'task_semantics_verified':False,'origin':'agent_asserted_table'}
        self.results[rid]=r;self.trace.append(r);return r

    def dispatch(self,action):
        if set(action)!={'tool','args'} or not isinstance(action['args'],dict):raise ValueError('Tool schema')
        methods={'catalog':self.catalog,'schema':self.schema,'read':self.read,'search':self.search,'query':self.query,'save_table':self.save_table}
        if action['tool'] not in methods:raise ValueError('Unknown tool')
        return methods[action['tool']](**action['args'])
