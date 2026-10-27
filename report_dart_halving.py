"""Verify cloud queries/decisions and recompute every result locally."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'infra/modal'))
from halving_core import METHODS, select
from halving_pipeline import verify, validate, summarize


def main():
    root = ROOT / 'results/dart_halving_v1/cloud'
    packet = json.loads((root / 'input_private.json').read_text()); verify(packet)
    status = json.loads((root / 'status.json').read_text())
    assert status['state'] == 'completed_review_required' and status['completed'] == 300
    ledger = json.loads((root / 'ledger.json').read_text())
    y = np.array(packet['success']); folds = np.array(packet['folds']); groups = np.array(packet['groups'])
    cases = {f"{a['budget_fraction']}_fold{a['fold']}_seed{a['seed']}": a for a in packet['cases']}
    rows = []
    for path in sorted(root.glob('case_*.json')):
        row = json.loads(path.read_text()); validate(row)
        assert row['run_id'] == packet['run_id'] and row['artifact_sha256'] == ledger[row['case']]
        assert path.stem[5:] == row['case']
        case = cases[row['case']]
        tr, te = np.flatnonzero(folds != case['fold']), np.flatnonzero(folds == case['fold'])
        assert not set(groups[tr]) & set(groups[te])
        assert row['test_indices'] == te.tolist() and row['budget'] == case['budget']
        for m in METHODS:
            result = row['methods'][m]; indices = result['audit_indices']
            assert len(indices) == len(set(indices)) == case['budget']
            assert np.array_equal(y[tr].ravel()[indices], result['audit_labels'])
            assert select(len(tr), y.shape[1], case['budget'], case['rng_seed'], m == 'PairedSH',
                          lambda i, a: y[tr[i], a]) == result
            # Independently reconstruct the round scores and elimination from the paid log.
            priority = {a: i for i, a in enumerate(result['tie_priority'])}
            active = list(range(y.shape[1]))
            for stage in result['rounds']:
                assert stage['active'] == active
                lo, hi = stage['audit_start'], stage['audit_stop']
                ids = np.array(indices[lo:hi]); labels = np.array(result['audit_labels'][lo:hi])
                scores = {a: float(labels[ids % y.shape[1] == a].mean()) for a in active}
                assert {str(a): v for a, v in scores.items()} == stage['scores']
                active = sorted(active, key=lambda a: (-scores[a], priority[a]))[:(len(active) + 1) // 2]
                assert active == stage['survivors']
            assert active == [result['agent']]
        rows.append(row)
    assert len(rows) == len(ledger) == len(cases) == 300
    summaries = {}
    for b in ('0.05', '0.1', '0.2'):
        summaries[b] = summarize([r for r in rows if r['case'].startswith(b + '_')], packet, b)
        assert summaries[b] == json.loads((root / ('analysis_' + b + '.json')).read_text())
    # Post-hoc descriptive diagnosis only; full TRAIN gold never entered selection.
    diagnostics = {}
    for b in ('0.05', '0.1', '0.2'):
        rr = [r for r in rows if r['case'].startswith(b + '_')]
        diagnostics[b] = {}
        for m in METHODS:
            retention, first_counts, last_regret = [], [], []
            for row in rr:
                train_scores = y[folds != row['fold']].mean(0)
                best = set(np.flatnonzero(train_scores == train_scores.max()))
                result = row['methods'][m]
                retention.append([bool(best & set(t['survivors'])) for t in result['rounds']])
                first_counts.append(result['rounds'][0]['audit_stop'] // y.shape[1])
                last_regret.append(float(train_scores.max() - train_scores[result['agent']]))
            diagnostics[b][m] = {'full_train_best_survival_by_round': np.mean(retention, axis=0).tolist(),
                                 'first_round_labels_per_agent_range': [min(first_counts), max(first_counts)],
                                 'mean_full_train_regret': float(np.mean(last_regret))}
    out = ROOT / 'docs/analysis'
    artifact = {'run_id': packet['run_id'], 'status': status, 'budgets': summaries,
                'verified_cases': 300, 'verified_method_runs': 600, 'source_sha256': packet['source_sha256'],
                'posthoc_train_diagnostics': diagnostics}
    (out / 'dart_halving_v1_results_2026-10-05.json').write_text(json.dumps(artifact, indent=2) + '\n')
    lines = ['# Kiểm tra đối chứng Sequential Halving', '',
             f"Run `{packet['run_id']}`: **300/300 case, 600 lần chạy phương pháp**, đã kiểm chứng.", '',
             'Ứng viên paired CFJudgeFactor giữ nguyên; các baseline chỉ nhận nhãn TRAIN trả phí. '
             'Đây là replay thật trên kết quả agent đã chạy, không gọi thêm solver/judge. '
             'Dữ liệu vẫn là development pool 168 task /56 generator /14 agent.', '',
             '## Kết quả', '', '| Phương pháp | 5% | 10% primary | 20% |', '|---|---:|---:|---:|']
    for m in summaries['0.1']['methods']:
        lines.append('| ' + m + ' | ' + ' | '.join(f"{summaries[b]['methods'][m]['mean_correct']:.2f}" for b in ('0.05', '0.1', '0.2')) + ' |')
    lines += ['', 'Số task thành công trung bình /168; trung bình 20 seeds trên toàn bộ outer folds.', '',
              '## Ứng viên trừ baseline ở ngân sách 10%', '',
              '| Baseline | Chênh lệch điểm % | CI95 điểm % | Rescue | Harm |', '|---|---:|---|---:|---:|']
    for m, c in summaries['0.1']['candidate_contrasts'].items():
        lo, hi = c['ci95']
        lines.append(f"| {m} | {100*c['difference']:+.2f} | [{100*lo:+.2f}, {100*hi:+.2f}] | {c['rescues']:.2f} | {c['harms']:.2f} |")
    lines += ['', f"**Gate đối chứng mới: {'PASS' if summaries['0.1']['new_baseline_signal_pass'] else 'FAIL'}.**", '',
              '**Gate gốc vẫn FAIL:** CI chưa dương trước cả UniformGlobal và PairedGlobal. '
              'Không thay primary endpoint, không gọi kết quả này là xác nhận DART hoặc SOTA.', '',
              'Ứng viên cao điểm hơn các controls trong bảng ở10%, nhưng PairedSH cao hơn '
              'ứng viên ở cả5% và20%. Vì thế không có phương pháp thắng đều trên toàn đường '
              'ngân sách. Không dùng điểm5% hoặc20% để chọn lại primary sau thực nghiệm.', '',
              '## Chẩn đoán mô tả sau thực nghiệm', '',
              'Dùng toàn bộ gold TRAIN sau khi quyết định đã khóa để xác định agent tốt nhất của '
              'train và xem nó bị loại ở vòng nào. Đây không phải feature, target được cấp miễn phí '
              'hay bằng chứng nhân quả; chỉ đo việc loại sớm trong dữ liệu đã quan sát.', '',
              '| Ngân sách | Baseline | Nhãn/agent vòng đầu | Còn ít nhất một agent tốt nhất TRAIN sau vòng 1/2/3/4 |',
              '|---|---|---|---|']
    for b, methods in diagnostics.items():
        for m, d in methods.items():
            lines.append(f"| {b} | {m} | {d['first_round_labels_per_agent_range']} | " +
                         ' / '.join(f'{100*x:.0f}%' for x in d['full_train_best_survival_by_round']) + ' |')
    lines += ['',
              '## Kiểm chứng và giới hạn', '',
              '- Kiểm tra source/input hash, mọi checksum, đúng số nhãn độc nhất; chạy lại 600 quyết định, '
              'đồng thời dựng lại điểm và tập agent sống sót từ log nhãn trả phí.',
              '- 5.000 generator bootstraps, seed1404, sau seed averaging. CI chưa điều chỉnh lịch sử '
              'nghiên cứu thích nghi và chưa đo toàn bộ bất định huấn luyện.',
              '- SH ở đây là bản thích ứng hữu hạn với ngân sách chính xác: lấy mẫu không hoàn lại, '
              'chuyển phần dư ngân sách sang vòng sau. Không tự động thừa hưởng định lý IID của bài gốc.',
              '- Baseline không cần judge; CFJudgeFactor dùng thêm 2.352 judgment lịch sử. '
              'Cùng ngân sách gold không đồng nghĩa cùng chi phí USD.',
              '- Kết quả với hai baseline này không đồng nghĩa thắng mọi phương pháp liên quan. '
              'Cần dữ liệu độc lập, baseline phù hợp và đóng góp thuật toán rõ trước kết luận cho bài báo.', '',
              '## Bước tiếp theo', '',
              'Giữ nguyên ứng viên và toàn bộ kết quả âm. Kiểm tra bộ dữ liệu độc lập và khả năng có '
              'feedback không lấy từ gold; khóa split, chi phí và tiêu chí trước khi đánh giá. '
              'Không tiếp tục chọn hyperparameter trên 168 task này để cố làm CI dương.', '',
              '- [Protocol đã khóa](dart_halving_v1_protocol_2026-10-05.md).',
              '- [Toàn bộ số liệu](dart_halving_v1_results_2026-10-05.json).',
              '- [Karnin et al., ICML 2013, Algorithm 2](https://proceedings.mlr.press/v28/karnin13.pdf).', '']
    (out / 'dart_halving_v1_assessment_2026-10-05.md').write_text('\n'.join(lines))
    print(json.dumps({'verified_cases': 300, 'primary': summaries['0.1']}, indent=2))


if __name__ == '__main__':
    main()
