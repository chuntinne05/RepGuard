"""Incremental checksummed download of active FinQA pilot artifacts."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import modal
import run_routerbench_finqa_feedback as cli
from routerbench_finqa_feedback_pipeline import validate


def main():
    packet = json.loads((cli.OUTPUT / 'packet_private.json').read_text())
    volume = modal.Volume.from_name('repguard-routerbench-finqa-feedback-v1')
    remote = '/runs/' + packet['run_id'] + '/'
    root = cli.OUTPUT / 'cloud'; root.mkdir(parents=True, exist_ok=True)
    def read(name):
        raw = b''.join(volume.read_file(remote + name))
        temp = root / (name + '.download')
        temp.write_bytes(raw); temp.replace(root / name)
        return json.loads(raw)
    status = read('status.json')
    names = ['input_private.json', 'judge_inputs_private.json', 'judge_environment.json', 'ledger.json']
    if status['state'] == 'completed_pilot_review_required':
        names += ['analysis.json', 'pilot_gold_private.json']
    for name in names:
        try:
            read(name)
        except FileNotFoundError:
            if status['state'] == 'completed_pilot_review_required':
                raise
    ledger = json.loads((root / 'ledger.json').read_text()) if (root / 'ledger.json').exists() else {}
    if not set(ledger) <= {str(i) for i in range(960)}:
        raise ValueError('Unexpected ledger index')
    def fetch_case(item):
        index, checksum = item
        name = f'case_{int(index):04d}.json'; path = root / name
        if path.exists():
            row = json.loads(path.read_text()); validate(row)
            if row['artifact_sha256'] == checksum:
                return False
        row = read(name); validate(row)
        if not row['complete'] or row['artifact_sha256'] != checksum:
            raise ValueError('Case does not match committed ledger')
        return True
    with ThreadPoolExecutor(max_workers=8) as pool:
        downloaded = sum(pool.map(fetch_case, ledger.items()))
    print(json.dumps({'status_snapshot': status, 'verified_completed_cases': len(ledger),
                      'new_case_downloads': downloaded}, indent=2))


if __name__ == '__main__':
    main()
