"""Verify every cloud case, rerun decisions, and report aggregate development evidence."""
import hashlib
import json
from pathlib import Path
import numpy as np
import run_routerbench_sparse as cli
from report_routerbench_pilot import load_verified_pilot, near_equal
from routerbench_sparse_core import METHODS, PRIMARY, CONTROLS, BUDGETS
from routerbench_sparse_pipeline import verify, validate, case, summarize


def main():
    root = cli.OUTPUT / 'cloud'
    packet = json.loads((root / 'input_private.json').read_text())
    verify(packet)
    near_equal(packet, json.loads((cli.OUTPUT / 'packet_private.json').read_text()))
    for path, checksum in packet['source_sha256'].items():
        if hashlib.sha256((cli.ROOT / path).read_bytes()).hexdigest() != checksum:
            raise ValueError('Local source differs from frozen run: ' + path)
    parent = load_verified_pilot()
    assert parent['packet']['run_id'] == packet['parent_run_id']
    assert parent['packet']['query_ids'] == packet['query_ids']
    assert parent['packet']['models'] == packet['models']
    for field, value in (('success', parent['gold']), ('judge_scores', parent['probabilities']), ('judge_invalid', parent['invalid'])):
        assert np.array_equal(np.array(packet[field]), value)
    for name, checksum in packet['parent_artifact_sha256'].items():
        path = cli.ROOT / 'results/routerbench_pilot_v1/cloud' / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == checksum
    status = json.loads((root / 'status.json').read_text())
    assert status['run_id'] == packet['run_id']
    assert status['state'] == 'completed_development_review_required' and status['completed_cases'] == 240
    ledger = json.loads((root / 'ledger.json').read_text())
    assert set(ledger) == {str(i) for i in range(240)}
    rows = []
    for index, spec in enumerate(packet['cases']):
        row = json.loads((root / f'case_{index:04d}.json').read_text())
        validate(row)
        assert row['artifact_sha256'] == ledger[str(index)]
        assert row['run_id'] == packet['run_id'] and row['index'] == index and row['spec'] == spec
        expected = {'run_id': packet['run_id'], 'index': index, **case(packet, spec)}
        near_equal(expected, {k: v for k, v in row.items() if k != 'artifact_sha256'})
        rows.append(row)
    result = summarize(packet, rows)
    cloud = json.loads((root / 'analysis.json').read_text())
    validate(cloud)
    near_equal({'run_id': packet['run_id'], **result}, {k: v for k, v in cloud.items() if k != 'artifact_sha256'})
    assert result['development_expansion_gate_pass'] == status['development_expansion_gate_pass']
    summary = {**result, 'run_id': packet['run_id'], 'parent_run_id': packet['parent_run_id'],
               'models_order': packet['models'], 'source_sha256': packet['source_sha256'],
               'verified_cases': 240, 'recomputed_method_selections': 2400,
               'finished_at_utc': status['updated_at']}
    out = cli.ROOT / 'docs/analysis'
    (out / 'routerbench_sparse_gold_v1_results_2026-10-06.json').write_text(json.dumps(summary, indent=2) + '\n')
    lines = ['# Gold thưa trên MATH500: development replay v1', '',
             f"Run `{packet['run_id']}`: **240/240 case, 2.400 lựa chọn model** đã chạy trên Modal CPU; "
             'đã kiểm chứng checksum và chạy lại toàn bộ quyết định tại local.', '',
             '## Phạm vi và ngân sách', '',
             '48 câu development đã quan sát × 6 model; bốn outer folds, mỗi fold 36 câu lịch sử '
             'và 12 câu đánh giá; 20 seeds. Replay dùng 288 solver outcomes đã lưu và 288 judgment '
             'Qwen3-14B thật từ pilot. Không có lời gọi solver/judge mới. Learner chỉ đọc gold '
             'của cell được audit; feedback của câu đánh giá không tham gia chọn model.', '',
             '| Ngân sách danh nghĩa | Gold cells / 216 history cells | Tỷ lệ thực |', '|---|---:|---:|',
             '| 5% | 11 | 5,093% |', '| 10% primary | 22 | 10,185% |', '| 20% | 44 | 20,370% |', '',
             'RawJudge dùng 0 gold; các phương pháp khác dùng đúng 11/22/44 cell theo từng case. '
             'Đây là giới hạn truy cập nhãn trong replay, không phải các nhãn con người mới mua. '
             'Các ablation paired dùng cùng mask; SH có acquisition path riêng với tổng budget bằng nhau.', '',
             '## Thành công của model được chọn', '',
             'Số câu đúng trung bình /48, sau trung bình 20 seeds. Mỗi outer fold chọn một model '
             'cho toàn bộ 12 câu held-out; đây là global model selection, không phải task-contextual routing.', '',
             '| Phương pháp | 5% | 10% primary | 20% |', '|---|---:|---:|---:|']
    for method in METHODS:
        values = [summary['budgets'][str(b)]['methods'][method]['mean_correct'] for b in BUDGETS]
        lines.append(f'| {method} | ' + ' | '.join(f'{v:.2f}' for v in values) + ' |')
    gate = 'PASS' if summary['development_expansion_gate_pass'] else 'FAIL'
    lines += ['', f'**Development expansion gate: {gate}.**', '',
              'Gate đã khóa yêu cầu CFJudgeRectifier tại 10% có CI95 lower >0 và cải thiện '
              'ít nhất 1 điểm phần trăm trước từng đối chứng UniformGlobal, PairedGlobal, '
              'GoldRidge, CFGoldRectifier, IndependentSH, PairedSH. Không đổi candidate hoặc '
              'chọn ngân sách khác sau kết quả.', '',
              '## So sánh primary tại 10%', '',
              '| Đối chứng | Chênh lệch điểm % | CI95 điểm % | Rescue | Harm |', '|---|---:|---|---:|---:|']
    contrasts = summary['budgets']['0.1']['primary_contrasts']
    for control in CONTROLS:
        c = contrasts[control]
        lines.append(f"| {control} | {100*c['difference']:+.2f} | "
                     f"[{100*c['ci95'][0]:+.2f}, {100*c['ci95'][1]:+.2f}] | "
                     f"{c['mean_rescues']:.2f} | {c['mean_harms']:.2f} |")
    lines += ['', '## Calibration và phương sai dưới gold thưa', '',
              'Predictor diagnostic được fit riêng trên đúng B cell paired của TRAIN, sau khi '
              'quyết định đã khóa. Không dùng lại calibration full-gold của pilot. Brier thấp '
              'tốt hơn; variance ratio <1 nghĩa là residual differences ít biến động hơn outcome '
              'differences. Hai chỉ số này chưa tự chứng minh chọn model tốt hơn.', '',
              '| Ngân sách | Brier judge | Brier gold-only | Residual variance ratio | CI95 ratio | Empty inner fits /240 |',
              '|---|---:|---:|---:|---|---:|']
    for b in BUDGETS:
        d = summary['budgets'][str(b)]['diagnostic']
        ci = d['pair_residual_variance_ratio_ci95']
        ratio = d['pair_residual_variance_ratio']
        lines.append(f"| {100*b:.0f}% | {d['crossfit_outer_brier']['judge']:.6f} | "
                     f"{d['crossfit_outer_brier']['gold']:.6f} | "
                     + (f'{ratio:.6f}' if ratio is not None else 'Không xác định') + ' | '
                     + (f'[{ci[0]:.6f}, {ci[1]:.6f}]' if ci else 'Không xác định')
                     + f" | {d['empty_inner_training_partitions']}/{d['total_inner_partitions']} |")
    lines += ['', '## Pool và selection diagnostics sau quyết định', '',
              f"Best fixed model trên 48 câu: {100*summary['posthoc_best_fixed_accuracy']:.2f}%; "
              f"oracle chọn đúng theo từng câu: {100*summary['posthoc_oracle_per_question_accuracy']:.2f}%; "
              f"câu có model đúng và model sai: {100*summary['posthoc_model_disagreement_fraction']:.2f}%.", '',
              '| Model | Accuracy trên 48 câu |', '|---|---:|']
    for model, accuracy in zip(packet['models'], summary['posthoc_per_model_accuracy']):
        lines.append(f'| {model} | {100*accuracy:.2f}% |')
    lines += ['', '| Phương pháp | Chọn một TRAIN-best model tại 10% |', '|---|---:|']
    for method in METHODS:
        agreement = summary['budgets']['0.1']['methods'][method]['fraction_selecting_full_gold_train_best_reference']
        lines.append(f'| {method} | {100*agreement:.2f}% |')
    lines += ['', 'Các references này đọc gold sau quyết định; không phải controls cùng ngân sách. '
              'TRAIN-best agreement chỉ mô tả lựa chọn có khớp lịch sử toàn gold hay không, '
              'không chứng minh nguyên nhân hoặc bảo đảm thắng trên task tương lai.', '',
              '## Diễn giải và giới hạn', '',
              'Nếu Brier/phương sai còn tốt nhưng selection gate FAIL, feedback có giá trị dự báo '
              'mà chưa chuyển thành quyết định tốt hơn ở budget này. Nếu diagnostic suy giảm, '
              'bằng chứng pilot với calibration nhiều gold không chuyển nguyên trạng sang gold thưa. '
              'Không gọi một ablation có point score cao hơn là phương pháp mới đã thắng.', '',
              '- Bootstrap 5.000 lần theo câu, sau seed averaging; không coi seeds là dữ liệu độc lập. '
              'CI giữ nguyên fitted learners, chưa refit, chưa grouping near-duplicate hoặc điều chỉnh '
              'lịch sử nghiên cứu thích nghi.',
              '- Sáu model, 48 câu là pool development nhỏ đã được xem trong pilot; không phải '
              'final evaluation độc lập. Giữ nguyên mọi gate AppWorld/MMLU trước đây.',
              '- CF correction dùng shrinkage count+2, không được gọi unbiased. SH là bản '
              'thích ứng finite-archive với minimum budget 11 và stage-only scores, không tự '
              'thừa hưởng bảo đảm IID của bài gốc.',
              '- Judge được dùng trên lịch sử đã có; đối chứng gold-only không cần judge. '
              'Equal-gold-budget chưa là equal-total-cost; chưa đo annotation savings hoặc USD.', '',
              '## Quyết định tiếp', '',
              ('Gate PASS cho phép chuẩn bị prompt-only grouping và study độc lập có power/chi phí '
               'được khóa trước collection; chưa tự mở rộng hoặc mở holdout.' if gate == 'PASS' else
               'Gate FAIL: dừng mở rộng judgment theo v1. Giữ nguyên kết quả; phân tích calibration '
               'và selection bằng các ablation đã khóa. Không tune tiếp trên 48 câu để ép gate PASS.'), '',
              '[Protocol đã khóa](routerbench_sparse_gold_v1_protocol_2026-10-06.md) · '
              '[JSON đầy đủ](routerbench_sparse_gold_v1_results_2026-10-06.json) · '
              '[Pilot trước đó](routerbench_pilot_assessment_2026-10-06.md)', '']
    (out / 'routerbench_sparse_gold_v1_assessment_2026-10-06.md').write_text('\n'.join(lines))
    print(json.dumps({'run_id': summary['run_id'], 'verified_cases': 240, 'recomputed_method_selections': 2400,
                      'development_expansion_gate_pass': summary['development_expansion_gate_pass'],
                      'primary_results': summary['budgets']['0.1']}, indent=2))


if __name__ == '__main__':
    main()
