import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from experiments.workspace_v4.tools import WorkspaceTools, materialize, sha


@pytest.fixture
def workspace(tmp_path):
    context=tmp_path/'input';context.mkdir()
    (context/'orders.csv').write_text('id,code,amount\n1,000423,12.5\n2,000424,20.0\n')
    (context/'regions.json').write_text(json.dumps({'table':'regions','records':[{'id':1,'region':'north'},{'id':2,'region':'south'}]}))
    (context/'notes.md').write_text('Current period: Q3.\nSource explains unit USD.')
    c=sqlite3.connect(context/'source.sqlite');c.execute('CREATE TABLE jobs(id INTEGER,state TEXT)');c.execute("INSERT INTO jobs VALUES(1,'submitted')");c.commit();c.close()
    derived=tmp_path/'derived/data.sqlite';materialize(context,derived)
    return context,derived,tmp_path/'artifacts'


def test_read_only_join_preserves_codes_and_exports_full_table(workspace):
    ctx,db,out=workspace;w=WorkspaceTools(ctx,db,out)
    r=w.query('SELECT orders.code, regions.region, orders.amount FROM orders JOIN regions ON orders.id=regions.id ORDER BY orders.id')
    assert r['preview'][0]==('000423','north',12.5)
    assert len(r['sources'])==2 and not r['task_semantics_verified']
    assert '000423' in (out/(r['result_id']+'.csv')).read_text()


@pytest.mark.parametrize('sql',["DELETE FROM orders","UPDATE orders SET amount=99","DROP TABLE orders", "ATTACH DATABASE '/tmp/evil' AS x", "PRAGMA writable_schema=ON", "SELECT load_extension('/tmp/x')", "SELECT readfile('/etc/passwd')", "SELECT * FROM sqlite_master"])
def test_sql_cannot_write_attach_or_escape(workspace,sql):
    ctx,db,out=workspace;before=sha(db);w=WorkspaceTools(ctx,db,out)
    with pytest.raises((sqlite3.DatabaseError,ValueError)):w.query(sql)
    assert sha(db)==before


def test_multiple_statements_and_constant_only_queries_rejected(workspace):
    w=WorkspaceTools(*workspace)
    for sql in ['SELECT * FROM orders; DROP TABLE jobs','SELECT 100 AS alleged_evidence']:
        with pytest.raises((sqlite3.DatabaseError,ValueError)):w.query(sql)


def test_recursive_resource_attack_is_bounded(workspace):
    w=WorkspaceTools(*workspace)
    with pytest.raises((sqlite3.DatabaseError,ValueError)):
        w.query('WITH RECURSIVE x(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM x) SELECT n FROM x JOIN orders')


def test_files_cannot_reach_gold_or_parent_paths(workspace,tmp_path):
    ctx,db,out=workspace;(tmp_path/'gold.csv').write_text('secret')
    (ctx/'symlink.md').symlink_to(tmp_path/'gold.csv')
    w=WorkspaceTools(ctx,db,out)
    for path in ['../gold.csv',str(tmp_path/'gold.csv'),'symlink.md']:
        with pytest.raises(ValueError):w.read(path)


def test_unicode_literal_search_and_truncation(workspace):
    ctx,db,out=workspace;(ctx/'extra.md').write_text('目标值 '+'x'*20000)
    w=WorkspaceTools(ctx,db,out)
    assert w.search('目标值')['hits'][0]['path']=='extra.md'
    assert w.read('extra.md',limit=30)['truncated']
    with pytest.raises(ValueError):w.read('extra.md',limit=100000)


def test_model_table_is_never_marked_executed_or_verified(workspace):
    w=WorkspaceTools(*workspace);r=w.save_table(['claimed'],[['100']])
    assert not r['execution_ok'] and not r['task_semantics_verified'] and r['origin']=='agent_asserted_table'


def test_source_snapshots_and_derived_snapshot_tamper_checks(workspace):
    ctx,db,out=workspace;w=WorkspaceTools(ctx,db,out)
    m=w.schema('orders');assert m['source_sha256']==sha(ctx/'orders.csv')
    with db.open('ab') as f:f.write(b'x')
    with pytest.raises(ValueError,match='changed'):WorkspaceTools(ctx,db,out)


def test_import_namespaces_name_collision_and_rejects_duplicate_header(tmp_path):
    ctx=tmp_path/'input';ctx.mkdir()
    (ctx/'data.csv').write_text('x,x\n1,2\n')
    with pytest.raises(ValueError,match='header'):materialize(ctx,tmp_path/'a.sqlite')
    (ctx/'data.csv').write_text('x\n1\n');(ctx/'data.json').write_text('[{"x":2}]')
    result=materialize(ctx,tmp_path/'b.sqlite')
    assert set(result['tables'])=={'data','json__data'}
    assert {v['source'] for v in result['tables'].values()}=={'data.csv','data.json'}


def test_unknown_tool_and_non_public_database_file_access(workspace):
    w=WorkspaceTools(*workspace)
    with pytest.raises(ValueError):w.dispatch({'tool':'bash','args':{'command':'whoami'}})
    with pytest.raises(ValueError):w.read('source.sqlite')


def test_sqlite_csv_collision_preserves_both_sources_without_reserved_alias(tmp_path):
    ctx=tmp_path/'input';ctx.mkdir();(ctx/'jobs.csv').write_text('id,state\n1,planned\n')
    c=sqlite3.connect(ctx/'source.sqlite');c.execute('CREATE TABLE jobs(id INTEGER,state TEXT)');c.execute("INSERT INTO jobs VALUES(1,'completed')");c.commit();c.close()
    db=tmp_path/'derived.sqlite';m=materialize(ctx,db)
    assert set(m['tables'])=={'jobs','database_source__jobs'}
    w=WorkspaceTools(ctx,db,tmp_path/'out')
    assert w.query('SELECT state FROM jobs')['preview']==[('planned',)]
    assert w.query('SELECT state FROM database_source__jobs')['preview']==[('completed',)]


def test_large_result_export_is_complete_while_preview_is_bounded(tmp_path):
    ctx=tmp_path/'input';ctx.mkdir()
    (ctx/'data.csv').write_text('id,value\n'+''.join(f'{i},{i*2}\n' for i in range(6001)))
    db=tmp_path/'derived.sqlite';materialize(ctx,db)
    w=WorkspaceTools(ctx,db,tmp_path/'artifacts');r=w.query('SELECT * FROM data ORDER BY id')
    assert r['rows']==6001 and len(r['preview'])==12 and r['preview_truncated']
    assert len((w.artifacts/(r['result_id']+'.csv')).read_text().splitlines())==6002


def test_numeric_text_is_bound_as_python_binary64_without_sqlite_reparsing(tmp_path):
    ctx=tmp_path/'input';ctx.mkdir()
    literals=['0.001368491','0.271213071','0.064226076']
    (ctx/'data.csv').write_text('code,value\n'+''.join('000423,'+v+'\n' for v in literals))
    db=tmp_path/'derived.sqlite';materialize(ctx,db)
    conn=sqlite3.connect(db)
    assert conn.execute('SELECT code,value FROM data ORDER BY rowid').fetchall()==[('000423',float(v)) for v in literals]
    conn.close()
