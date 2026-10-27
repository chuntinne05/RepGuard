"""Prepare/submit/status/fetch the pinned external-data inventory on Modal."""
import hashlib
from pathlib import Path
import run_dart_gain as transport
from routerbench_intake_core import digest
from routerbench_intake_v2_pipeline import atomic

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'results/routerbench_intake_v2'


def prepare():
    import json
    packet = {'dataset': 'NPULH/LLMRouterBench', 'revision': '0e5af1b84bf73437a01a1849c0f1d2468baa93fc'}
    packet.update({'archive_bytes': 1283503080,
                   'archive_sha256': 'b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1',
                   'url': 'https://huggingface.co/datasets/NPULH/LLMRouterBench/resolve/' + packet['revision'] + '/bench-release.tar.gz',
                   'github_revision': 'c77cb0506949d8f959e97967d2fefca0e8ff1b05'})
    paths = [ROOT / 'infra/modal' / name for name in ('routerbench_intake_core.py', 'routerbench_intake_v2_core.py', 'routerbench_intake_v2_pipeline.py', 'routerbench_intake_v2_modal.py')]
    paths += [Path(__file__), ROOT / 'docs/analysis/routerbench_intake_v2_protocol_2026-10-05.md', ROOT / 'run_dart_gain.py']
    packet['source_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    packet['run_id'] = digest(packet)[:24]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / 'packet_private.json'
    if target.exists() and json.loads(target.read_text()) != packet:
        raise ValueError('Prepared input differs')
    atomic(target, packet); print(json.dumps({'run_id': packet['run_id'], 'archive_bytes': packet['archive_bytes']}))


if __name__ == '__main__':
    transport.OUTPUT = OUTPUT; transport.APP = 'repguard-routerbench-intake-v2'; transport.prepare = prepare
    transport.main()
