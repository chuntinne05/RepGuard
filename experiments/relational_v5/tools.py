"""Source-only tool integration, separate from the frozen workspace_v4 code."""
from pathlib import Path

from experiments.workspace_v4.tools import WorkspaceTools, sha
from repguard.verification.relational import Catalog, QueryContract, audit_query, search_schema


class AuditedWorkspaceTools(WorkspaceTools):
    def __init__(self, context, derived_database, artifacts, *, contract: QueryContract, pdf_views=None):
        super().__init__(context, derived_database, artifacts, pdf_views)
        self.contract = QueryContract.model_validate(contract.model_dump())
        self.source_catalog = Catalog.from_manifest(self.manifest)

    def _check_snapshot(self):
        if sha(self.db) != self.manifest['derived_sha256']:
            raise ValueError('Derived database changed since contract/catalog binding')
        sources = {(t['source'], t['source_sha256']) for t in self.manifest['tables'].values()}
        for relative, expected in sources:
            if sha(self._path(relative)) != expected:
                raise ValueError('Source bytes changed: ' + relative)

    def schema_search(self, literal, limit=12):
        self._check_snapshot()
        return search_schema(self.source_catalog, literal, limit=limit)

    def query(self, sql):
        self._check_snapshot()
        record = super().query(sql)
        # Execution succeeds independently of semantic diagnostics. No automatic
        # rewrite, gold lookup, output projection or host approval here.
        record['query_obligations'] = audit_query(self.contract, sql, self.source_catalog).model_dump(mode='json')
        record['execution_scope'] = 'Host executed this SQL on the recorded derived snapshot; task truth not certified'
        return record

    def query_audit(self, result_id):
        self._check_snapshot()
        if result_id not in self.results:
            raise ValueError('Unknown actual result ID')
        record = self.results[result_id]
        path = Path(self.artifacts) / (result_id + '.csv')
        if sha(path) != record['output_sha256']:
            raise ValueError('Result bytes changed')
        if 'sql' not in record:
            return {'result_id': result_id, 'output_sha256': record['output_sha256'], 'state': 'unresolved',
                    'reason': 'Agent-asserted table has no SQL execution evidence; another adapter is required',
                    'semantic_truth_certified': False}
        return {'result_id': result_id, 'output_sha256': record['output_sha256'], 'host_execution_recorded': True,
                'query_obligations': audit_query(self.contract, record['sql'], self.source_catalog).model_dump(mode='json'),
                'semantic_truth_certified': False}

    def dispatch(self, action):
        if set(action) == {'tool', 'args'} and isinstance(action['args'], dict):
            if action['tool'] == 'schema_search':
                return self.schema_search(**action['args'])
            if action['tool'] == 'query_audit':
                return self.query_audit(**action['args'])
        return super().dispatch(action)
