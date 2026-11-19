import sqlite3

import pytest

from experiments.specbridge_v6.grading import run_readonly


def test_query_cannot_write_attach_or_load_external_files(tmp_path):
    database = tmp_path / 'data.sqlite'
    con = sqlite3.connect(database); con.execute('CREATE TABLE numbers(value INTEGER)'); con.execute('INSERT INTO numbers VALUES(7)'); con.commit(); con.close()
    for sql in ('DELETE FROM numbers', "ATTACH DATABASE '/private/tmp/unauthorized.sqlite' AS other", "SELECT load_extension('x')", "SELECT readfile('/etc/passwd')"):
        assert run_readonly(database, sql, engine=sqlite3)['state'] == 'sql_error'
    assert run_readonly(database, 'SELECT value FROM numbers', engine=sqlite3)['rows'] == [[7]]


def test_full_result_required_no_silent_prefix(tmp_path):
    database = tmp_path / 'data.sqlite'
    con = sqlite3.connect(database); con.execute('CREATE TABLE numbers(value)'); con.executemany('INSERT INTO numbers VALUES(?)', [(i,) for i in range(11)]); con.commit(); con.close()
    result = run_readonly(database, 'SELECT * FROM numbers', engine=sqlite3, row_cap=10)
    assert result['state'] == 'resource_limit' and result['rows'] is None
