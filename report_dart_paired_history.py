"""Recompute and verify every completed historical-feedback case before reporting."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'infra/modal'))
from paired_history_pipeline import verify,validate,summarize
from history_core import rectify,choose
from neural_core import observed_gold,means


def main():
    root=ROOT/'results/dart_paired_history_v1/cloud'
    packet=json.loads((root/'input_private.json').read_text()); verify(packet)
    status=json.loads((root/'status.json').read_text())
    if status['state']!='completed_review_required' or status['completed']!=300:
        raise SystemExit('Incomplete batch; no final report written.')
    ledger=json.loads((root/'ledger.json').read_text()); rows=[]
    audits={f"{a['budget_fraction']}_fold{a['fold']}_seed{a['seed']}":a for a in packet['audits']}
    folds=np.array(packet['folds']); y=np.array(packet['success']); groups=np.array(packet['groups'])
    for path in sorted(root.glob('case_*.json')):
        row=json.loads(path.read_text()); validate(row)
        assert row['run_id']==packet['run_id'] and path.stem[5:]==row['case']
        assert ledger[row['case']]==row['artifact_sha256']
        a=audits[row['case']]; tr,te=np.flatnonzero(folds!=a['fold']),np.flatnonzero(folds==a['fold'])
        assert row['test_indices']==te.tolist() and row['audit_count']==len(a['audit_indices'])
        obs=observed_gold(y[tr],a['audit_indices'])
        base=int(means(obs).argmax())
        assert row['agent_choices']['PairedGlobal']==base
        assert [base]*len(te)==a['test_agent_choices']
        prediction_groups=[]
        for part in row['crossfit_trace']:
            train,predict=set(part['train_groups']),set(part['prediction_groups'])
            assert not (train&predict or (train|predict)&set(groups[te]))
            assert train|predict==set(groups[tr])
            prediction_groups.extend(predict)
        assert len(prediction_groups)==len(set(prediction_groups))==len(set(groups[tr]))
        for name,field in [('CFGoldFactor','gold_proxy'),('CFJudgeFactor','judge_proxy')]:
            proxy=np.array(row[field]); score=rectify(obs,proxy)
            assert proxy.shape==obs.shape and np.isfinite(proxy).all() and ((proxy>=0)&(proxy<=1)).all()
            assert np.allclose(score,row['scores'][name],atol=1e-12,rtol=0)
            assert choose(score)==row['agent_choices'][name]
        rows.append(row)
    assert len(rows)==len(ledger)==300
    summaries={}
    for b in ('0.05','0.1','0.2'):
        rr=[r for r in rows if r['case'].startswith(b+'_')]; assert len(rr)==100
        summaries[b]=summarize(rr,packet,b)
        assert summaries[b]==json.loads((root/f'analysis_{b}.json').read_text())
    summary={'run_id':packet['run_id'],'status':status,'budgets':summaries,
        'verified_cases':300,'source_sha256':packet['source_sha256'],
        'judge_provenance':packet['judge_provenance'],'all_groups_isolated':True}
    out=ROOT/'docs/analysis'
    (out/'dart_paired_history_v1_results_2026-10-05.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Paired historical rectifier v1: thực nghiệm đầy đủ','',
        f"Run `{packet['run_id']}`. Đủ **300/300 trường hợp**, kết thúc `{status['state']}`.",'',
        '## Phạm vi','', 'Chỉ đổi acquisition sang đúng 300 paired masks cũ; estimator giữ nguyên. UniformCFJudgeFactor là phương pháp ở batch uniform trước, dùng để đo acquisition effect.','',
        '168 task / 56 generator / 14 agent; ba ngân sách ×20 audit seeds ×5 folds. '
        'Dùng các xác suất judge đã được sinh thật trên Modal, không gọi thêm judge/solver. '
        'Các learner chỉ nhận nhãn đã audit và feedback của outer TRAIN. '
        'Đây là phát triển thích nghi trên public normal đã xem, chưa xác nhận độc lập.','',
        '## Tất cả kết quả','',
        '| Phương pháp | 5% | 10% (primary) | 20% |','|---|---:|---:|---:|']
    for m in summaries['0.1']['methods']:
        values=[summaries[b]['methods'][m]['mean_correct'] for b in ('0.05','0.1','0.2')]
        lines.append('| '+m+' | '+' | '.join(f'{v:.2f}' for v in values)+' |')
    lines += ['', 'Đơn vị: số task thành công trung bình /168. Không phải số solver calls mới.','',
        '## Primary CFJudgeFactor ở ngân sách 10%','',
        '| Control | Chênh lệch điểm % | CI 95% điểm % | Rescue | Harm |','|---|---:|---|---:|---:|']
    for ref,c in summaries['0.1']['contrasts']['CFJudgeFactor'].items():
        lo,hi=c['ci95']
        lines.append(f"| {ref} | {100*c['difference']:+.2f} | [{100*lo:+.2f}, {100*hi:+.2f}] | {c['rescues']:.2f} | {c['harms']:.2f} |")
    passed=summaries['0.1']['primary_signal_pass']
    lines += ['', f"**Primary exploratory signal: {'PASS' if passed else 'FAIL'}.** "
              'Tiêu chí đã khóa: CI lower >0 với cả UniformAuditGlobal và PairedGlobal.','',
        'CI lấy từ 5.000 bootstrap theo generator, seed1404, sau khi trung bình audit seeds. '
        'Không điều chỉnh toàn bộ lịch sử adaptive experiments; không phải bảo đảm không thua khi deploy.','',
        '## Ý nghĩa cơ chế','',
        '- CFGoldFactor dùng cùng paired audit, cross-fit và rectifier nhưng không dùng judge. Chênh lệch với nó '
        'mới phản ánh phần bổ sung từ feedback trong họ estimator này.',
        '- TunedFactorRidge là uniform-audit structured control chọn regularization bằng inner CV, từ gain v1; '
        'FixedFactorRidge dùng penalty 4 cố định để tách phần tuning.',
        '- RawJudgeRectifier bỏ calibration; JudgeImpute bỏ residual correction. Giữ lại cả hai '
        'dù chúng thắng hay thua phương pháp primary.',
        '- Tất cả phương pháp ở đây chọn một agent toàn cục dựa trên lịch sử train. '
        'Chưa phải router học lợi thế theo từng task và chưa có adaptive pair acquisition.',
        '- Nếu thắng về số nhãn gold, vẫn phải tính chi phí thu 2.352 judgment lịch sử; '
        'không suy ra cùng USD/compute với baseline không cần judge.','',
        '## Kiểm chứng','',
        'Đã xác minh source/input identity, 300 checkpoint checksums, đúng audit counts/control '
        'choices, generator isolation, công thức rectification và tất cả bootstrap summaries '
        'tính lại từ action traces. Unit tests kiểm tra thay nhãn chưa audit không đổi kết quả, '
        'nhãn của một generator không lọt vào mô hình dự báo cho chính generator đó, '
        'constant proxy=.5 khôi phục Global chính xác, và resume không chạy lại case đã lưu.','',
        '## Giới hạn và hướng tiếp','',
        'Bảng này là bằng chứng phát triển, không đủ xác nhận novelty hoặc khả năng nhận bài A/A*. '
        'Chỉ giữ một ứng viên khi cải thiện còn tồn tại với control gold-only mạnh và validation '
        'độc lập. Nếu phần judge không đem lại lợi ích, không gọi lợi ích của cấu trúc agent là '
        'thành công của hiệu chỉnh feedback. Không dùng chính outer test để chọn lại primary.','',
        '- [Protocol khóa trước](dart_paired_history_v1_protocol_2026-10-05.md).',
        '- [JSON đầy đủ cho mọi phương pháp/ngân sách](dart_paired_history_v1_results_2026-10-05.json).',
        '- [PPI++](https://arxiv.org/html/2311.01453v2) và [Cross-PPI](https://arxiv.org/html/2309.16598v2) '
        'là nền tảng tham khảo; estimator regularized ở đây không được cấp tự động các bảo đảm của chúng.',
        '- Raw artifacts: `results/dart_paired_history_v1/cloud/`.','']
    (out/'dart_paired_history_v1_assessment_2026-10-05.md').write_text('\n'.join(lines))
    print(json.dumps({'verified_cases':300,'primary_signal_pass':passed,'primary_methods':summaries['0.1']['methods']},indent=2))


if __name__=='__main__':
    main()
