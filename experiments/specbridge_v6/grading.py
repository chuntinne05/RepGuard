"""Offline only: pinned upstream grader functions and read-only SQLite.

Never put this module/reference packages in a model runtime. No model client.
"""
from __future__ import annotations

import ast
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'results/relational_v5/source_intake/SpecBridge'
RENDER_SHA = '941642673be85e434bef85415ffe0c9f87db0c978a4169da8cac0f8f8d3d7ce0'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_grader():
    render = SOURCE / 'native_scorer/specbridge/pd/spec/render.py'
    score = SOURCE / 'benchmark/score.py'
    if sha(render) != RENDER_SHA:
        raise ValueError('Upstream grade source changed')
    # Verify score.py against its pinned Git blob in the source tree, then load
    # only inspected pure functions; do not import the generator/LLM machinery.
    tree = json.loads((SOURCE / 'tree.json').read_text())
    expected = next(x['sha'] for x in tree['tree'] if x['path'] == 'benchmark/score.py')
    data = score.read_bytes()
    if hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() != expected:
        raise ValueError('Upstream matches source changed')
    namespace = {}
    extracted = []
    for path, names in ((render, {'grade'}), (score, {'_t', 'matches'})):
        source = path.read_text()
        module = ast.parse(source)
        functions = [n for n in module.body if isinstance(n, ast.FunctionDef) and n.name in names]
        if {f.name for f in functions} != names:
            raise ValueError('Missing native grader function')
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), namespace)
        extracted.extend({'name': f.name, 'source_sha256': hashlib.sha256(ast.get_source_segment(source, f).encode()).hexdigest()}
                         for f in functions)
    return namespace['matches'], {'module_sha256': {str(render.relative_to(ROOT)): sha(render), str(score.relative_to(ROOT)): sha(score)},
                                 'functions': extracted, 'loading': 'Unmodified AST of upstream grade/_t/matches only; generator/package code not imported'}


FUNCTIONS = {
    'abs', 'avg', 'count', 'sum', 'total', 'min', 'max', 'round', 'coalesce', 'ifnull', 'nullif', 'iif',
    'lower', 'upper', 'trim', 'ltrim', 'rtrim', 'length', 'substr', 'substring', 'replace', 'instr',
    'date', 'datetime', 'time', 'strftime', 'julianday', 'unixepoch', 'printf', 'format', 'typeof', 'cast',
    'like', 'glob', 'row_number', 'rank', 'dense_rank', 'ntile', 'lag', 'lead', 'first_value', 'last_value',
    'sqrt', 'pow', 'power', 'exp', 'log', 'ln', 'log10', 'floor', 'ceil', 'ceiling', 'trunc', 'sign',
    'group_concat', 'concat', 'concat_ws', 'char', 'unicode', 'hex', 'unhex', 'mod', 'json_extract',
}


def run_readonly(database, sql, *, engine=None, seconds=60, row_cap=10000):
    if engine is None:
        import sqlean as engine
    if not isinstance(sql, str) or not sql.strip() or len(sql) > 32000:
        return {'state': 'invalid_query', 'rows': None, 'error': 'SQL text bound'}
    start = time.monotonic()
    con = engine.connect(Path(database).resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        con.execute('PRAGMA query_only=ON'); con.execute('PRAGMA trusted_schema=OFF')
        allowed = {engine.SQLITE_SELECT, engine.SQLITE_READ}
        if hasattr(engine, 'SQLITE_RECURSIVE'):
            allowed.add(engine.SQLITE_RECURSIVE)
        def authorize(action, a, b, db, trigger):
            if action in allowed:
                return engine.SQLITE_OK
            if action == engine.SQLITE_FUNCTION and (b or '').lower() in FUNCTIONS:
                return engine.SQLITE_OK
            return engine.SQLITE_DENY
        con.set_authorizer(authorize)
        con.set_progress_handler(lambda: int(time.monotonic() - start > seconds), 10000)
        cur = con.execute(sql)
        if cur.description is None:
            raise ValueError('No table output')
        rows = cur.fetchmany(row_cap + 1)
        if len(rows) > row_cap:
            return {'state': 'resource_limit', 'rows': None, 'error': 'Output row cap'}
        return {'state': 'ok', 'rows': [list(row) for row in rows], 'columns': [c[0] for c in cur.description],
                'seconds': time.monotonic() - start, 'sqlite_version': engine.sqlite_version}
    except (engine.DatabaseError, ValueError) as error:
        return {'state': 'sql_error', 'rows': None, 'error': str(error)[:600], 'seconds': time.monotonic() - start}
    finally:
        con.close()
