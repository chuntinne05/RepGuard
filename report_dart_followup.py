"""Aggregate-only synthesis of the completed feedback and paired-design studies."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(relative):
    return json.loads((ROOT / relative).read_text())


def main():
    d=read('docs/analysis/dart_postrun_diagnostics_2026-10-04.json')
    main_result=read('results/dart_audit_judge_v1/analysis.json')
    channels={name:read(f'results/dart_paired_{name}_v1/analysis.json') for name in ('selfreport','judge')}
    # The new non-feedback-dependent controls must also remain identical.
    pp={name:read(f'results/dart_paired_{name}_v1/predictions_private.json')['predictions']
        for name in channels}
    for budget in pp['judge']:
        for method in ('PairedAuditOnly','PairedGlobal','PairedKNN'):
            if pp['judge'][budget][method]!=pp['selfreport'][budget][method]:
                raise ValueError(f'Paired gold-only invariant failed: {budget}/{method}')
    f=d['feedback']; j=f['judge']; s=f['self_report_binary']
    lines=['# DART — phân tích full judge và bước tiếp theo', '',
           '## Trạng thái thực nghiệm', '',
           '- Hoàn tất 2.352 kết quả chấm thật trên Modal và replay đã khóa.',
           '- Hoàn tất thêm 1.200 audit-policy runs lấy mẫu theo task cho mỗi kênh feedback.',
           '- Các replay dùng outcome agent lịch sử chính thức; không phải chạy solver mới.',
           '- Đủ 168 task, 56 generator, 14 agent. Seed audit không làm tăng số task độc lập.',
           '- Kiểm tra tính bất biến của mọi control không dùng feedback: PASS.', '',
           '## Judge có tốt hơn lời tự báo hoàn thành không?', '',
           '| Metric | Judge | Self-report |','|---|---:|---:|',
           f"| Accuracy | {100*j['accuracy']:.2f}% | {100*s['accuracy']:.2f}% |",
           f"| Balanced accuracy | {100*j['balanced_accuracy']:.2f}% | {100*s['balanced_accuracy']:.2f}% |",
           f"| TP / FN | {j['tp']} / {j['fn']} | {s['tp']} / {s['fn']} |",
           f"| TN / FP | {j['tn']} / {j['fp']} | {s['tn']} / {s['fp']} |",
           f"| Brier raw score | {j['brier']:.5f} | {s['brier']:.5f} |",
           f"| AUC raw score | {j['auc']:.5f} | {s['auc']:.5f} |", '',
           f"Hai kênh đồng ý {100*f['agreement']:.2f}% trên các bản ghi hợp lệ. Judge sửa {f['judge_corrects_self_report']} lỗi của self-report và gây thêm {f['judge_introduces_error']} lỗi.",
           f"CI 95% chênh lệch balanced accuracy (judge − self-report): {[round(100*v,2) for v in f['balanced_accuracy_delta_ci95']]} điểm phần trăm.",
           'Brier của self-report ở đây coi bit tự báo là xác suất 0/1; cả hai đều chưa qua calibration. AUC của judge dùng xác suất liên tục; replay v1 đã khóa dùng nhãn ngưỡng 0,5.', '',
           '## Kết quả task success — mean đúng / 168', '']
    for channel,result in channels.items():
        lines += [f'### Feedback: {channel}', '', '| Method | 5% | 10% | 20% |','|---|---:|---:|---:|']
        for method in ('DART','DARTContrast','AuditOnly','RandomHistory','UncertaintyHistory',
                       'UniformAuditGlobal','UniformAuditKNN','PairedAuditOnly','PairedHistory',
                       'PairedGlobal','PairedKNN'):
            values=[result['budgets'][b]['methods'][method]['mean_correct'] for b in ('0.05','0.1','0.2')]
            lines.append(f'| {method} | '+' | '.join(f'{x:.2f}' for x in values)+' |')
        lines += ['', f"PairedHistory exploratory all-comparisons gate: **{'PASS' if result['exploratory_method_gate_pass'] else 'FAIL'}**.", '',
                  '| Thay đổi sampling tại 10% | Delta điểm % | CI 95% điểm % |','|---|---:|---:|']
        for method,contrast in result['budgets']['0.1']['matched_design_contrasts'].items():
            ci=contrast['generator_cluster_ci95']
            lines.append(f"| {method} − {contrast['comparator']} | {100*contrast['difference']:+.2f} | [{100*ci[0]:+.2f}; {100*ci[1]:+.2f}] |")
        lines.append('')
    lines += [f"Gate DARTContrast của full replay ban đầu: **{'PASS' if main_result['exploratory_method_gate_pass'] else 'FAIL'}**.", '',
              'Các gate và CI là exploratory trên cùng public development data; không phải xác nhận độc lập. Không chọn cell 5% hoặc 20% thuận lợi để thay primary 10%.', '',
              '## Feedback làm thay đổi routing như thế nào?', '',
              '| Method, budget 10% | Judge − self-report, số task trung bình | CI delta accuracy điểm % |',
              '|---|---:|---:|']
    for method in ('DARTContrast','RandomHistory','UncertaintyHistory','AuditOnly','UniformAuditGlobal'):
        v=d['routing_feedback_comparison']['budgets']['0.1'][method]; ci=v['generator_ci95']
        lines.append(f"| {method} | {v['judge_mean_correct']-v['self_report_mean_correct']:+.2f} | [{100*ci[0]:+.2f}; {100*ci[1]:+.2f}] |")
    lines += ['', '## Chẩn đoán chọn policy với full judge, budget 10%', '',
              '| Method | Task đúng thực | Diagnostic chọn bằng gold selection-history | RMSE value | Optimism của policy được chọn |',
              '|---|---:|---:|---:|---:|']
    for method,v in d['selection_diagnostics']['0.1'].items():
        lines.append(f"| {method} | {v['chosen_test_correct_per_168']:.2f} | {v['full_selection_gold_chosen_test_correct_diagnostic_per_168']:.2f} | {v['candidate_value_rmse']:.4f} | {v['chosen_value_optimism']:+.4f} |")
    lines += ['', 'Diagnostic dùng nhãn gold không được cấp cho learner, chỉ để phân biệt lỗi ước lượng với giới hạn candidate/generalization. Không thay thế score đạt được của DART.', '',
              '## Diễn giải và việc tiếp theo', '',
              '1. Đối chiếu cả gain của feedback và gain do cách lấy mẫu. PairedAuditOnly/Global/KNN là control thông thường; không đổi tên một control thắng thành DART mới.',
              '2. Nếu DART hoặc PairedHistory thua learner global dùng toàn bộ ngân sách, ưu tiên kiểm tra chi phí chia dữ liệu, cách học từ toàn bộ nhãn đã trả phí, và chất lượng candidate theo instruction. Chỉ thêm acquisition phức tạp sau khi xác nhận đó là nút thắt.',
              '3. Trước vòng thuật toán tiếp theo, khóa một giả thuyết và control dùng cùng nhãn audit thực tế; báo mọi biến thể. Cần kiểm tra feature/ngữ nghĩa instruction mạnh hơn TF-IDF để tách thiếu thông tin với learner quá yếu.',
              '4. Tái lập baseline liên quan theo đúng feedback/cost setting. [CABS](https://arxiv.org/html/2607.09015v1) có true reward của arm được chọn; [SELECT-LLM](https://arxiv.org/html/2510.09418v2) tính annotation theo reference query. Không âm thầm cấp thông tin khác nhau rồi so trực tiếp.',
              '5. Giữ sealed MMLU và challenge chưa mở. Chỉ xác nhận độc lập sau khi phương pháp vượt control mạnh trên dev với claim và operating point đã khóa.',
              '6. Chưa có kết quả nào ở đây bảo đảm bài A/A*. HistRepEval có thể đóng góp về đo lường; claim DART superior cần vượt các gate phương pháp riêng.', '',
              '## Sự cố và provenance', '',
              f"Khoảng trống giữa hai bản ghi lớn nhất: {d['operations']['largest_record_gap_s']/3600:.2f} giờ. Collector đã resume, không nhân đôi ledger. Log xác nhận retry exhaustion; không đủ bằng chứng quy nguyên nhân cho sleep máy.",
              f"Logical request starts: {d['operations']['logical_request_starts']}; duplicate starts: {d['operations']['repeated_request_starts']}. Transport retry cấp thấp có thể tốn thêm compute chưa phản ánh đầy đủ ở số này.",
              'Protocol và code paired-ablation được viết trước khi chạy, source hashes được ghi vào manifest trước vòng tính kết quả. Lệnh commit trước lần chạy self-report bị iCloud Git index timeout; commit 8e85898 được tạo sau lần chạy đó bằng temporary index. Vì vậy không gọi lần chạy self-report này là thí nghiệm đã commit trước outcome.',
              'Không thay kết quả sau timeout Git. Dữ liệu benchmark per-task không được đưa vào báo cáo công khai.']
    (ROOT/'docs/analysis/dart_followup_report_2026-10-04.md').write_text('\n'.join(lines)+'\n')
    aggregate={'diagnostics':d,'paired_ablations':channels,'gold_only_controls_invariant':True}
    (ROOT/'docs/analysis/dart_followup_aggregate_2026-10-04.json').write_text(json.dumps(aggregate,indent=2)+'\n')


if __name__=='__main__':
    main()
