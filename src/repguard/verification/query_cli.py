"""Audit one or multiple caller-supplied interpretations; no SQL execution."""
import argparse
import json
from pathlib import Path

from .relational import Catalog, QueryContract, audit_query


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contracts', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--sql-file', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.sql_file.stat().st_size > 64000:
        parser.error('SQL file exceeds64KB input bound')
    raw = json.loads(args.contracts.read_text())
    items = raw if isinstance(raw, list) else [raw]
    if not 1 <= len(items) <= 8:
        parser.error('Supply1to8explicit interpretations')
    contracts = [QueryContract.model_validate(item) for item in items]
    catalog = Catalog.from_manifest(json.loads(args.manifest.read_text()))
    sql = args.sql_file.read_text()
    result = {'interpretation_selection_required': len(contracts) > 1,
              'semantic_truth_certified': False, 'sql_executed': False,
              'receipts': [audit_query(c, sql, catalog).model_dump(mode='json') for c in contracts]}
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        with args.output.open('x') as target:
            target.write(text)
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
