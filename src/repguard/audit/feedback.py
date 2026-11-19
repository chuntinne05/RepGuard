"""Validated categorical feedback matrix from a completed real-judge ledger."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


def judge_feedback(directory: Path, ids: list[str], agents: list[str]) -> tuple[np.ndarray, dict]:
    manifest_bytes = (directory / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    quality = json.loads((directory / 'pilot_quality.json').read_text())
    if not quality['gate_pass'] or quality['protocol_hash'] != manifest['hash']:
        raise ValueError('Judge pilot quality gate is closed')
    ledger_bytes = (directory / 'judgments_private.jsonl').read_bytes()
    rows = [json.loads(line) for line in ledger_bytes.splitlines() if line.strip()]
    positions = {(t, a): (i, j) for i, t in enumerate(ids) for j, a in enumerate(agents)}
    feedback = np.full((len(ids), len(agents)), -1, dtype=int)
    seen_indices = set()
    valid_count = 0
    for row in rows:
        index = row['index']
        if (row['protocol_hash'] != manifest['hash'] or index in seen_indices
                or not 0 <= index < len(manifest['cases'])
                or row['case'] != manifest['cases'][index]):
            raise ValueError('Judge ledger identity/protocol mismatch')
        seen_indices.add(index)
        key = (row['case']['task_id'], row['case']['agent'])
        if key not in positions or feedback[positions[key]] != -1:
            raise ValueError('Unexpected or duplicate task-agent feedback')
        if row['valid']:
            p = row['success_probability']
            if type(p) not in (float, int) or not np.isfinite(p) or not 0 <= p <= 1:
                raise ValueError('Invalid probability marked as valid')
            feedback[positions[key]] = int(p >= .5)
            valid_count += 1
        else:
            feedback[positions[key]] = 2  # separate abstention category
    if (feedback < 0).any() or len(rows) != len(positions) or len(rows) != len(manifest['cases']):
        raise ValueError('Incomplete judge matrix; no subset routing analysis')
    if valid_count < .95 * len(rows):
        raise ValueError('Full judge validity gate below 95%')
    return feedback, {'source': 'real Modal qwen3:14b trajectory judge',
                      'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
                      'ledger_sha256': hashlib.sha256(ledger_bytes).hexdigest(),
                      'records': len(rows), 'valid': valid_count,
                      'encoding': '0 negative; 1 positive at p>=0.5; 2 invalid/abstain'}
