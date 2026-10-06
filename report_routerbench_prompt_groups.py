"""Independently recompute prompt-only grouping from verified cloud artifacts."""
import hashlib
import json
from pathlib import Path
import run_routerbench_prompt_groups as cli
from routerbench_prompt_groups_core import group, query_hash
from routerbench_prompt_groups_pipeline import validate, verify


def main():
    root = cli.OUTPUT / 'cloud'
    packet = json.loads((root / 'input_private.json').read_text())
    verify(packet)
    if packet != json.loads((cli.OUTPUT / 'packet_private.json').read_text()):
        raise ValueError('Cloud packet differs from frozen local packet')
    for name, checksum in packet['source_sha256'].items():
        if hashlib.sha256((cli.ROOT / name).read_bytes()).hexdigest() != checksum:
            raise ValueError('Local grouping source changed: ' + name)
    status = json.loads((root / 'status.json').read_text())
    if status['run_id'] != packet['run_id'] or status['state'] != 'completed_prompt_grouping_review_required':
        raise ValueError('Grouping is not complete')
    prompts_artifact = json.loads((root / 'prompts_private.json').read_text())
    validate(prompts_artifact)
    if prompts_artifact['run_id'] != packet['run_id']:
        raise ValueError('Mixed prompt artifact')
    prompts = prompts_artifact['prompts']
    if set(prompts) != set(packet['expected_query_ids']) or any(query_hash(t) != q for q, t in prompts.items()):
        raise ValueError('Incomplete or mismatched prompt coverage')
    cloud = json.loads((root / 'analysis.json').read_text())
    validate(cloud)
    computed = {'run_id': packet['run_id'], **group(prompts, packet['pilot_query_ids'])}
    if computed != {k: v for k, v in cloud.items() if k != 'artifact_sha256'}:
        raise ValueError('Local grouping does not reproduce cloud')
    if any(status[k] != computed[k] for k in ('total_groups', 'remaining_groups', 'remaining_questions')):
        raise ValueError('Status does not match grouping')
    public = {k: v for k, v in computed.items() if k not in ('components', 'linked_edges', 'review_edges')}
    public.update({'linked_edges_in_private_artifact': len(computed['linked_edges']),
                   'review_edges_in_private_artifact': len(computed['review_edges']),
                   'archive_sha256': packet['archive_sha256'],
                   'parent_pilot_run_id': packet['parent_pilot_run_id'],
                   'source_sha256': packet['source_sha256'],
                   'finished_at_utc': status['updated_at'],
                   'scope': 'Prompt-only heuristic grouping; no gold outside pilot read, no final split certified'})
    out = cli.ROOT / 'docs/analysis'
    (out / 'routerbench_prompt_groups_v1_results_2026-10-06.json').write_text(json.dumps(public, indent=2) + '\n')
    lines = ['# Nhóm prompt MATH500 trước study tiếp theo', '',
             f"Run `{packet['run_id']}` hoàn tất và được tính lại local trên **500/500 prompt**.", '',
             '| Chỉ số | Giá trị |', '|---|---:|',
             f"| Exact question hashes | {computed['total_questions']} |",
             f"| Near-template groups | {computed['total_groups']} |",
             f"| Nhóm có từ hai câu | {computed['multi_question_groups']} |",
             f"| Nhóm lớn nhất | {computed['largest_group']} |",
             f"| Linked near-template edges | {computed['linked_edge_count']} |",
             f"| Cặp cần review thêm | {computed['review_edge_count']} |",
             f"| Pilot đã xem | {computed['pilot_questions']} câu / {computed['pilot_touched_groups']} nhóm |",
             f"| Nằm trong nhóm liên quan pilot | {computed['pilot_touched_questions']} câu |",
             f"| Còn ngoài các nhóm pilot | {computed['remaining_questions']} câu / {computed['remaining_groups']} nhóm |", '',
             'Rule Jaccard được khóa trước khi đọc toàn bộ prompt; đọc đúng một member '
             'Qwen3-8B đã chọn bằng metadata, so khớp hash với 500 câu common. Worker '
             'không giữ score/output/reference; bản public chỉ có số tổng hợp. Cặp và '
             'prompt chi tiết nằm trong artifact private để review.', '',
             'Đây là grouping heuristic. Các review pairs chưa tự động gộp, nên số nhóm '
             'còn lại là ước lượng theo rule đã khóa, **chưa phải chứng nhận độc lập**. '
             'Cần xem những cặp này và làm sensitivity analysis bằng prompt trước khi '
             'khóa final split. Không dùng score của 452 câu ngoài pilot ở bước này.', '',
             '[Protocol](routerbench_prompt_groups_v1_protocol_2026-10-06.md) · '
             '[JSON tổng hợp](routerbench_prompt_groups_v1_results_2026-10-06.json) · '
             '[Phân tích gold thưa](routerbench_sparse_gold_v1_interpretation_2026-10-06.md)', '']
    (out / 'routerbench_prompt_groups_v1_assessment_2026-10-06.md').write_text('\n'.join(lines))
    print(json.dumps(public, indent=2))


if __name__ == '__main__':
    main()
