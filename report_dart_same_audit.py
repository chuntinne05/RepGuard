"""Publish aggregate tables only; private task outcomes remain in results/."""
import hashlib
import json
from pathlib import Path

import numpy as np


def main():
    root = Path('results/dart_same_audit_v2')
    status = json.loads((root/'status.json').read_text())
    if status['state'] != 'completed' or status['completed'] != 1200:
        raise ValueError('Require complete corrected replay')
    result = json.loads((root/'analysis.json').read_text())
    result['manifest'] = json.loads((root/'manifest.json').read_text())
    first = json.loads(Path('results/dart_same_audit_v1/predictions_private.json').read_text())['predictions']
    second = json.loads((root/'predictions_private.json').read_text())['predictions']
    revision = []
    for ch,designs in first.items():
        for design,budgets in designs.items():
            for budget,methods in budgets.items():
                for method,values in methods.items():
                    a,b = np.array(values),np.array(second[ch][design][budget][method])
                    changed = int((a != b).sum())
                    if changed:
                        revision.append({'channel':ch,'design':design,'budget':budget,'method':method,
                             'changed_task_seed_outcomes':changed,'mean_correct_v1':float(a.sum(axis=1).mean()),
                             'mean_correct_v2':float(b.sum(axis=1).mean())})
    result['numerical_revision'] = revision
    result['artifact_sha256'] = {f:hashlib.sha256((root/f).read_bytes()).hexdigest()
        for f in ('analysis.json','trace_private.jsonl','predictions_private.json')}
    out = Path('docs/analysis')
    (out/'dart_same_audit_aggregate_2026-10-05.json').write_text(json.dumps(result,indent=2)+'\n')
    lines = ['# DART — toàn bộ kết quả đối chứng cùng tập audit, 05/10/2026', '',
        'Nguồn: `results/dart_same_audit_v2`. 1.200 cấu hình × 12 biến thể = 14.400 lượt chọn policy; '
        '0 suy luận mới. Các nhãn đến từ trajectory thật đã lưu. 20 seed audit, 5 fold theo generator, '
        '168 task. Đây là dữ liệu phát triển đã xem, không phải xác nhận độc lập.', '',
        'Số trong bảng là số task thành công trung bình trên 168. Ngân sách là phần trăm số '
        'ô task–agent lịch sử được audit. Δ và CI tính bằng **điểm phần trăm** accuracy; '
        'bootstrap 5.000 lần theo generator sau khi trung bình seed. CI không chỉnh đa so sánh.', '']
    for ch,designs in result['results'].items():
        for design,budgets in designs.items():
            lines += [f'## {ch} / acquisition {design}', '',
                '| Biến thể | 5% | 10% | 20% | Δ so Original ở 10% [CI95%] |',
                '|---|---:|---:|---:|---|']
            for method in budgets['0.1']['methods']:
                vals = [budgets[b]['methods'][method]['mean_correct'] for b in ('0.05','0.1','0.2')]
                c = budgets['0.1']['methods'][method]['vs_original'];lo,hi = c['generator_ci95']
                lines.append(f'| {method} | {vals[0]:.2f} | {vals[1]:.2f} | {vals[2]:.2f} | {100*c["difference"]:+.3f} [{100*lo:+.3f}; {100*hi:+.3f}] |')
            lines += ['', '### Các cặp kiểm tra cơ chế tại 10%', '',
                      '| Cặp | Δ accuracy, điểm % [CI95%] |', '|---|---|']
            for name,c in budgets['0.1']['mechanism_contrasts'].items():
                lo,hi = c['generator_ci95']; lines.append(f'| {name} | {100*c["difference"]:+.3f} [{100*lo:+.3f}; {100*hi:+.3f}] |')
            lines += ['', 'Brier dự báo trên phần S, chỉ dùng để chẩn đoán sau chạy: '+
                      ', '.join(f'{k}={v:.6f}' for k,v in budgets['0.1']['proxy_brier_on_S_diagnostic'].items())+'.', '']
    lines += ['## Đối chứng bên ngoài cùng ngân sách', '',
              '| Control | 5% | 10% | 20% |','|---|---:|---:|---:|',
              '| UniformAuditGlobal | 64.40 | 69.70 | 75.15 |',
              '| PairedGlobal | 62.15 | 71.95 | 76.70 |','',
              'Các control này lấy **tập nhãn khác**; chúng là đối chứng hiệu quả cuối cùng, '
              'không phải can thiệp một thành phần cùng tập audit. Không biến thể nào ở ngân sách '
              'chính 10% trong từng channel/design có CI95% chênh lệch so UniformAuditGlobal hoàn toàn dương.', '',
              'v1 giữ nguyên để truy vết; v2 khôi phục đúng thứ tự phép toán HT của code cũ. '
              'Chỉ ZeroHT/RandomHistory thay kết quả ở 10% và 20%, giống nhau giữa hai channel. '
              'Tất cả Original tái tạo khớp và ZeroHT/uniform khớp AuditOnly hoàn toàn.', '']
    # Fail if the interpretation above stops matching the machine-readable output.
    assert all(v['vs_uniform_global']['generator_ci95'][0] <= 0
               for ds in result['results'].values() for bs in ds.values()
               for v in bs['0.1']['methods'].values())
    (out/'dart_same_audit_tables_2026-10-05.md').write_text('\n'.join(lines).rstrip()+'\n')
    print('Published complete aggregate tables and provenance')


if __name__ == '__main__':
    main()
