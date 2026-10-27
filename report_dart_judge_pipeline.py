"""Export aggregate-only research results after the fixed automated stages."""
from __future__ import annotations

import json
from pathlib import Path

from run_dart_modal_judge import now

ROOT = Path(__file__).resolve().parent
JUDGE = ROOT / 'results/dart_modal_judge_v1'
REPLAY = ROOT / 'results/dart_audit_judge_v1'
REPORT = ROOT / 'docs/analysis/dart_real_judge_result_2026-10-04.md'


def report() -> None:
    quality = json.loads((JUDGE / 'pilot_quality.json').read_text())
    ledger = [json.loads(line) for line in (JUDGE / 'judgments_private.jsonl').read_text().splitlines()]
    aggregate = {'updated_at': now(), 'pilot_quality': quality,
                 'completed_judge_records': len(ledger),
                 'valid_judge_records': sum(r['valid'] for r in ledger),
                 'prompt_tokens': sum(r['usage']['prompt_eval_count'] or 0 for r in ledger),
                 'output_tokens': sum(r['usage']['eval_count'] or 0 for r in ledger),
                 'sum_call_latency_s': sum(r['latency_s'] for r in ledger),
                 'clipped_records': sum(r['case']['clipped'] for r in ledger)}
    lines = ['# Kết quả real judge và DART — 04/10/2026', '',
             f"Cập nhật UTC: {aggregate['updated_at']}", '',
             '## Pilot đã khóa', '',
             f"- Số kết quả: {quality['rows']}; hợp lệ: {quality['valid']}.",
             f"- Generator: {quality['generators']}; nhãn thành công: {quality['positive_labels']}; nhãn thất bại: {quality['negative_labels']}.",
             f"- Balanced accuracy: {quality['balanced_accuracy']}; CI 95% theo generator: {quality['balanced_accuracy_generator_ci95']}.",
             f"- Accuracy: {quality['accuracy']}; Brier: {quality['brier_score']}.",
             f"- Gate chất lượng phản hồi: **{'PASS' if quality['gate_pass'] else 'FAIL'}**.", '',
             'Gate này đánh giá kênh phản hồi, không chứng minh DART tốt hơn baseline.', '',
             '## Suy luận thật đã hoàn tất', '',
             f"- Ledger: **{len(ledger)}/2352** kết quả chấm; {aggregate['valid_judge_records']} hợp lệ.",
             f"- Input tokens: {aggregate['prompt_tokens']:,}; output tokens: {aggregate['output_tokens']:,}.",
             f"- Tổng latency các lời gọi có kết quả: {aggregate['sum_call_latency_s'] / 60:.2f} phút.",
             f"- Log cần cắt: {aggregate['clipped_records']}.",
             '- Đây là lời gọi Qwen3-14B thực trên Modal, không phải chạy mới solver lịch sử.',
             '- Số token/latency chỉ của response có ledger; timeout/retry có thể tiêu tốn thêm compute.',
             '- Chưa có billing USD; không suy ra ngang tổng chi phí từ ngân sách gold.', '']
    if (REPLAY / 'analysis.json').exists():
        result = json.loads((REPLAY / 'analysis.json').read_text())
        aggregate['routing_analysis'] = result
        lines += ['## Replay: mean số task đúng / 168 qua 20 audit seed', '',
                  '| Method | 5% | 10% | 20% |', '|---|---:|---:|---:|']
        for method in result['budgets']['0.1']['methods']:
            values = [result['budgets'][b]['methods'][method]['mean_correct'] for b in ('0.05', '0.1', '0.2')]
            lines.append(f"| {method} | " + ' | '.join(f'{v:.2f}' for v in values) + ' |')
        lines += ['', '### Primary 10%: DARTContrast trừ baseline', '',
                  '| Baseline | Chênh lệch điểm % | CI 95% điểm % |', '|---|---:|---:|']
        for method, values in result['budgets']['0.1']['DART_contrasts'].items():
            lo, hi = values['generator_cluster_ci95']
            lines.append(f"| {method} | {100*values['difference']:+.2f} | [{100*lo:+.2f}; {100*hi:+.2f}] |")
        lines += ['', f"**Exploratory method gate: {'PASS' if result['exploratory_method_gate_pass'] else 'FAIL'}.**", '',
                  'CI chưa điều chỉnh đa so sánh. 20 seed không phải 20 bộ task độc lập.',
                  'Đây vẫn là public development replay; chưa xác nhận độc lập và chưa chứng nhận an toàn triển khai.',
                  'AnchorOnly dùng ít nhãn hơn; GoldTrainSingle/KNN dùng full gold, chỉ là diagnostic.', '',
                  '## Việc tiếp theo', '',
                  ('Đóng băng ứng viên và thiết kế phép xác nhận độc lập, faithful baselines, cost và robustness trước claim superior.'
                   if result['exploratory_method_gate_pass'] else
                   'Dừng claim DART superior. Phân tích gain của feedback và chi phí chia dữ liệu/candidate bank; không mở holdout để tìm cấu hình thắng.'),
                  'Chưa có cơ sở bảo đảm bài được nhận ở hội nghị A/A*.']
    elif not quality['gate_pass']:
        lines += ['## Dừng theo gate', '',
                  'Không mở rộng sang 2.352 lượt vì kênh judge chưa qua tiêu chí đã khóa.',
                  'Tiếp theo: phân tích false positive/negative, độ thiếu log và thông tin trạng thái cuối; giữ nguyên kết quả thất bại.',
                  'Không có kết quả DART với full real judge ở giai đoạn này.']
    else:
        lines += ['Full collection hoặc routing analysis chưa hoàn tất. Không suy diễn kết quả còn thiếu.']
    REPORT.write_text('\n'.join(lines) + '\n')
    REPORT.with_suffix('.json').write_text(json.dumps(aggregate, indent=2) + '\n')
    print(str(REPORT))


if __name__ == '__main__':
    report()
