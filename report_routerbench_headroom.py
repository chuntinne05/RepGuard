"""Verify 40 score-only checkpoints and independently recompute headroom."""
import hashlib
import json
from pathlib import Path
import numpy as np
import run_routerbench_headroom as cli
from routerbench_headroom_core import DATASETS, analyze
from routerbench_headroom_pipeline import validate, verify


def main():
    root = cli.OUTPUT / 'cloud'
    packet = json.loads((root / 'input_private.json').read_text()); verify(packet)
    if packet != json.loads((cli.OUTPUT / 'packet_private.json').read_text()):
        raise ValueError('Changed frozen packet')
    for name, sha in packet['source_sha256'].items():
        if hashlib.sha256((cli.ROOT / name).read_bytes()).hexdigest() != sha:
            raise ValueError('Local source changed: ' + name)
    status = json.loads((root / 'status.json').read_text())
    if status['run_id'] != packet['run_id'] or status['state'] != 'completed_development_headroom_review_required':
        raise ValueError('Run is not complete')
    ledger = json.loads((root / 'ledger.json').read_text())
    if len(ledger) != 40:
        raise ValueError('Incomplete score checkpoints')
    cloud = json.loads((root / 'analysis.json').read_text()); validate(cloud)
    recomputed = {}
    for dataset in DATASETS:
        spec = packet['datasets'][dataset]
        y = np.full((200, 20), np.nan)
        for mi, model in enumerate(spec['models']):
            entry = ledger[dataset + '/' + model]
            row = json.loads((root / entry['file']).read_text()); validate(row)
            if row['artifact_sha256'] != entry['sha256'] or row['run_id'] != packet['run_id'] or row['member'] != spec['members'][model]:
                raise ValueError('Mixed score artifact')
            if set(row['scores']) != set(spec['query_ids']):
                raise ValueError('Score artifact includes unselected question')
            y[:, mi] = [row['scores'][q] for q in spec['query_ids']]
        recomputed[dataset] = analyze(y, spec['models'])
    actual = {'run_id': packet['run_id'], 'datasets': recomputed}
    if actual != {k: v for k, v in cloud.items() if k != 'artifact_sha256'}:
        raise ValueError('Local headroom analysis does not match cloud')
    public = {'run_id': packet['run_id'], 'datasets': recomputed,
              'common_questions': {d: packet['datasets'][d]['common_questions'] for d in DATASETS},
              'eligible_unique_questions': {d: packet['datasets'][d]['eligible_unique_questions'] for d in DATASETS},
              'duplicate_query_hashes_excluded': {d: packet['datasets'][d]['duplicate_query_hashes_excluded'] for d in DATASETS},
              'selected_development_questions': 200, 'verified_member_files': 40,
              'unselected_questions_retained': {d: packet['datasets'][d]['common_questions'] - 200 for d in DATASETS},
              'archive_sha256': packet['archive_sha256'], 'source_sha256': packet['source_sha256'],
              'finished_at_utc': status['updated_at'],
              'scope': 'Gold-only development diagnostic; oracle uses per-question gold; no judge or fresh solver calls'}
    out = cli.ROOT / 'docs/analysis'
    (out / 'routerbench_headroom_v1_results_2026-10-06.json').write_text(json.dumps(public, indent=2) + '\n')
    lines = ['# Dư địa chọn model trên MBPP và FinQA', '',
             f"Run `{packet['run_id']}`: 40 files × 200 câu development đã được đọc score đúng vị trí, "
             'kiểm chứng checksum và tính lại tại local. Không có solver/judge calls mới.', '',
             '| Dataset | Common câu | Loại do trùng hash | Dev đã đọc score | Còn chưa đọc | Best fixed | Oracle | Headroom | CI95 mô tả | Câu cứu được |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---|---:|']
    for dataset in DATASETS:
        r = recomputed[dataset]
        ci = r['headroom_ci95_descriptive']
        lines.append(f"| {dataset} | {packet['datasets'][dataset]['common_questions']} | "
                     f"{packet['datasets'][dataset]['duplicate_query_hashes_excluded']} | 200 | "
                     f"{packet['datasets'][dataset]['common_questions'] - 200} | "
                     f"{100*r['best_fixed_mean_reward']:.2f}% | {100*r['oracle_mean_reward']:.2f}% | "
                     f"{100*r['headroom']:.2f} điểm % | [{100*ci[0]:.2f}, {100*ci[1]:.2f}] | "
                     f"{r['strict_rescue_questions']}/200 |")
    lines += ['', 'Oracle chọn model sau khi biết score từng câu. Headroom >0 chỉ cho thấy '
              'có chỗ về mặt lý thuyết; không chứng minh một router dự báo được câu nào '
              'cần model nào. Score là giá trị evaluator đã lưu trong archive, chưa được '
              'tái chấm ở study này.', '',
              'Model pool và 200 câu/domain được chọn theo metadata/hash trước khi worker đọc '
              'score. Các câu còn lại chưa được đọc score ở run này. Chỉ số và CI dựa trên '
              'câu development; không dùng chúng làm final confirmation.', '',
              '[Protocol](routerbench_headroom_v1_protocol_2026-10-06.md) · '
              '[JSON kết quả](routerbench_headroom_v1_results_2026-10-06.json) · '
              '[Phân tích MATH500](routerbench_sparse_gold_v1_interpretation_2026-10-06.md)', '']
    (out / 'routerbench_headroom_v1_assessment_2026-10-06.md').write_text('\n'.join(lines))
    print(json.dumps({d: {'best_fixed': r['best_fixed_mean_reward'], 'oracle': r['oracle_mean_reward'],
                          'headroom': r['headroom'], 'ci': r['headroom_ci95_descriptive'],
                          'rescues': r['strict_rescue_questions']} for d, r in recomputed.items()}, indent=2))


if __name__ == '__main__':
    main()
