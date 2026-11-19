"""Independent receipt/lineage audit after bounded collection; no inference."""
from pathlib import Path
import hashlib
import json

from experiments.verification_v1.core import build_prompt, parse_answer, request_id
from experiments.verification_v1.prepare import OUT, ROOT, digest, write


def main():
    plan = json.loads((OUT / 'registered_plan.json').read_text())
    folder = OUT / 'runs' / plan['plan_id']
    public = json.loads((folder / 'public_pilot.json').read_text())
    assert digest(public) == plan['public_sha256']
    for name, expected in plan['source_hashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    cases = {r['id']: r for r in public['items']}
    records = {}
    for path in (folder / 'responses').glob('*.json'):
        r = json.loads(path.read_text())
        h = r.pop('record_sha256')
        assert digest(r) == h
        r['record_sha256'] = h
        key = r['item_id'], r['workflow']
        assert key not in records
        records[key] = r
    assert len(records) == plan['max_corpus_calls'] == 720
    for (item, workflow), r in records.items():
        assert r['transport_ok'] and r['live_inference']
        assert r['weights_mounted_read_only'] and r['evaluation_volume_mounted'] is False
        assert r['model_digest'] == plan['models'][workflow[-1]]['digest']
        assert r['model'] == plan['models'][workflow[-1]]['name']
        assert r['ollama_version'] == plan['ollama']
        assert 'L40S' in r['gpu']
        assert r['generation_attempts'] == 1
        assert r['request_id'] == request_id(plan['plan_id'], item, workflow)
        prior = {'raw_text': records[(item, workflow[0])]['raw_text']} if len(workflow) == 2 else None
        prompt = build_prompt(cases[item]['case'], prior)
        assert r['prompt'] == prompt and r['prompt_sha256'] == digest(prompt)
        assert r['request_body']['messages'] == [{'role': 'user', 'content': prompt}]
        assert r['request_body']['think'] is False
        assert r['request_body']['options']['num_predict'] == 2048
        assert r['parsed'] == parse_answer(r['raw_text'], cases[item]['case'])
        if prior is not None:
            assert r['parent_request_id'] == records[(item, workflow[0])]['request_id']
    result = {'audit': 'PASS', 'plan_id': plan['plan_id'], 'records_verified': len(records),
              'prompt_and_parent_lineage_verified': True, 'weights_digests_verified': True,
              'read_only_weights_and_no_eval_mount_verified': True,
              'local_sources_match_registration': True, 'new_model_calls': 0,
              'invalid': sum(not r['parsed']['valid'] for r in records.values()),
              'length_stops': sum(r['response'].get('done_reason') == 'length' for r in records.values()),
              'native_thinking_outputs': sum(bool(r['response'].get('message', {}).get('thinking')) for r in records.values()),
              'limitations': ['Receipts do not adjudicate semantic gold labels.',
                             'Local source hashes and prompt receipts are checked; this is not formal verification of the remote runtime.']}
    write(ROOT / 'docs/reports/2026-11-09/verification_v1_audit.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
