"""Verify frozen FinQA consensus replay and regenerate its public report."""
import hashlib
import json

import numpy as np

import run_routerbench_finqa_consensus as cli
from routerbench_finqa_consensus_core import agreement_proxy, analyze, select_queries
from routerbench_finqa_consensus_pipeline import validate, verify
from report_routerbench_finqa_feedback import near_equal


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = cli.OUTPUT / 'cloud'
    packet = json.loads((root / 'input_private.json').read_text())
    verify(packet)
    if packet != json.loads((cli.OUTPUT / 'packet_private.json').read_text()):
        raise ValueError('Cloud packet differs from local frozen packet')
    for name, checksum in packet['source_sha256'].items():
        if sha(cli.ROOT / name) != checksum:
            raise ValueError('Frozen local source changed: ' + name)
    parent_root = cli.ROOT / 'results/routerbench_headroom_v1/cloud'
    if sha(parent_root / 'input_private.json') != packet['parent_input_sha256'] or sha(parent_root / 'analysis.json') != packet['parent_analysis_sha256']:
        raise ValueError('Parent headroom checksum differs')
    parent = json.loads((parent_root / 'input_private.json').read_text())
    old = json.loads((cli.ROOT / 'results/routerbench_finqa_feedback_v1/packet_private.json').read_text())
    spec = parent['datasets']['finqa/test']
    if packet['old_pilot_query_ids'] != old['query_ids'] or packet['query_ids'] != select_queries(spec['query_ids'], old['query_ids']):
        raise ValueError('Question selection differs from frozen parents')
    if packet['models'] != spec['models'] or packet['members'] != spec['members']:
        raise ValueError('Selected model/archive members differ from parent')
    if packet['positions'] != {m: {q: spec['positions'][m][q] for q in packet['query_ids']} for m in packet['models']}:
        raise ValueError('Selected positions differ from parent')
    if packet['new_solver_calls'] != 0 or packet['new_judge_calls'] != 0 or packet['selection_reads_outcomes']:
        raise ValueError('Experiment access/cost scope changed')
    status = json.loads((root / 'status.json').read_text())
    if status['run_id'] != packet['run_id'] or status['state'] != 'completed_development_review_required' or status['cells'] != 960:
        raise ValueError('Consensus replay incomplete')
    predictions = json.loads((root / 'predictions_private.json').read_text())
    proxy = json.loads((root / 'proxy_private.json').read_text())
    result = json.loads((root / 'analysis.json').read_text())
    for artifact in (predictions, proxy, result):
        validate(artifact)
        if artifact['run_id'] != packet['run_id']:
            raise ValueError('Mixed consensus artifact identities')
    if proxy['gold_fields_present'] is not False:
        raise ValueError('Proxy checkpoint is not gold blind')
    if len(predictions['matrix']) != 48 or any(len(r) != 20 for r in predictions['matrix']):
        raise ValueError('Wrong prediction matrix size')
    p, missing = agreement_proxy(predictions['matrix'])
    if p.tolist() != proxy['probability'] or missing.tolist() != proxy['missing']:
        raise ValueError('Proxy does not follow frozen exact-agreement rule')
    gold = json.loads((root / 'pilot_gold_private.json').read_text())
    if gold['query_ids'] != packet['query_ids'] or gold['models'] != packet['models']:
        raise ValueError('Gold matrix identity differs')
    y = np.asarray(gold['success'], float)
    recomputed = {'run_id': packet['run_id'], **analyze(y, p, missing)}
    near_equal(recomputed, {k: v for k, v in result.items() if k != 'artifact_sha256'})
    if result['operational_pass'] != status['operational_pass'] or result['expansion_signal_pass'] != status['expansion_signal_pass']:
        raise ValueError('Analysis/status gate differs')
    nright = y.sum(axis=0)
    raw_rank = int(np.argmax(p.mean(axis=0)))
    descriptive = {
        'fixed_model_gold_success_range': [int(nright.min()), int(nright.max())],
        'per_question_oracle_success': int(np.any(y == 1, axis=1).sum()),
        'raw_agreement_top_model': packet['models'][raw_rank],
        'raw_agreement_top_model_gold_success': int(nright[raw_rank]),
    }
    summary = {k: v for k, v in result.items() if k not in ('calibrated_predictions', 'gold_only_predictions', 'artifact_sha256')}
    summary.update({'source_sha256': packet['source_sha256'], 'verified_prediction_cells': 960,
                    'new_solver_calls': 0, 'new_judge_calls': 0, 'descriptive': descriptive})
    out = cli.ROOT / 'docs/analysis'
    (out / 'routerbench_finqa_consensus_v1_results_2026-10-06.json').write_text(json.dumps(summary, indent=2) + '\n')
    ci = summary['pair_residual_variance_ratio_ci95']
    lines = ['# FinQA: frozen exact-answer consensus development replay', '',
             f"Run `{packet['run_id']}`: 48 câu development mới ×20 model = 960 bản ghi lịch sử; "
             'đã xác minh checksum, danh tính, proxy và tính lại toàn bộ chỉ số tại local.', '',
             '| Chỉ số | Giá trị |', '|---|---:|',
             f"| Prediction không rỗng | {100*summary['prediction_coverage']:.2f}% |",
             f"| Brier agreement thô | {summary['brier']['raw_agreement']:.6f} |",
             f"| Brier agreement cross-fit | {summary['brier']['crossfit_agreement']:.6f} |",
             f"| Brier gold-only cross-fit | {summary['brier']['crossfit_gold_only']:.6f} |",
             f"| Pair residual variance ratio cross-fit | {summary['pair_residual_variance_ratio']:.6f} |",
             f"| CI95 ratio (question bootstrap) | {ci} |",
             f"| Pair ratio proxy thô | {summary['raw_agreement_pair_ratio']:.6f} |",
             f"| Gold success của best fixed model | {descriptive['fixed_model_gold_success_range'][1]}/48 |",
             f"| Gold success của model top theo proxy thô | {descriptive['raw_agreement_top_model_gold_success']}/48 |",
             f"| Per-question oracle | {descriptive['per_question_oracle_success']}/48 |", '',
             f"Operational gate: **{'PASS' if summary['operational_pass'] else 'FAIL'}**. "
             f"Expansion screen: **{'PASS' if summary['expansion_signal_pass'] else 'FAIL'}**.", '',
             'Đây là một phép thử development mới, có rule khóa trước khi mở 48×20 score của run này. '
             'Headroom 200 câu trước đó đã xem aggregate gold, nên không phải confirmation độc lập. '
             'Cross-fit vẫn cần toàn bộ gold của 36 câu huấn luyện trong mỗi fold; chưa chứng minh '
             'ít gold hơn, chọn model theo từng câu, tiết kiệm chi phí hay thắng baseline triển khai. '
             'Proxy đồng thuận dùng sẵn đầu ra lịch sử của cả 20 model; chi phí tạo ra chúng phải '
             'được tính trong một so sánh thực tế. CI không refit các fold.', '',
             '[Protocol](routerbench_finqa_consensus_v1_protocol_2026-10-06.md) · '
             '[JSON](routerbench_finqa_consensus_v1_results_2026-10-06.json) · '
             '[Judge pilot](routerbench_finqa_feedback_v1_assessment_2026-10-06.md)', '']
    (out / 'routerbench_finqa_consensus_v1_assessment_2026-10-06.md').write_text('\n'.join(lines))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
