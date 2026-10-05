"""Verify downloaded checkpoints and write the complete aggregate result report."""
import json
from collections import Counter
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'infra/modal'))
from gain_pipeline import analysis,validate_case,verify
from neural_core import observed_gold,means


def main():
    root=ROOT/'results/dart_gain_v1/cloud'
    packet=json.loads((root/'input_private.json').read_text()); verify(packet)
    status=json.loads((root/'status.json').read_text())
    if status['state']!='completed_review_required' or status['completed']!=305:
        raise SystemExit('Batch incomplete: fetch again after all 305 cases. No final report written.')
    ledger=json.loads((root/'ledger.json').read_text())
    rows=[]
    for path in sorted(root.glob('case_*.json')):
        r=json.loads(path.read_text()); validate_case(r,packet['run_id'],path.stem[5:])
        assert ledger[r['case']]==r['artifact_sha256']
        assert r['test_indices']==np.flatnonzero(np.array(packet['folds'])==r['fold']).tolist()
        outer_test_groups={packet['groups'][i] for i in r['test_indices']}
        for inner in r['trace']['inner_folds']:
            tr,va=set(inner['train_groups']),set(inner['validation_groups'])
            assert not (tr&va or tr&outer_test_groups or va&outer_test_groups)
        rows.append(r)
    assert len(rows)==len(ledger)==305
    y=np.array(packet['success']); folds=np.array(packet['folds'])
    for audit in packet['audits']:
        train=np.flatnonzero(folds!=audit['fold'])
        obs=observed_gold(y[train],audit['audit_indices'])
        expected=[int(means(obs).argmax())]*int((folds==audit['fold']).sum())
        assert expected==audit['test_agent_choices']
        key=f"r1_{audit['budget_fraction']}_fold{audit['fold']}_seed{audit['seed']}"
        actual=next(r for r in rows if r['case']==key)
        assert actual['actions']['Global']==expected
        assert actual['audit_count']==len(audit['audit_indices'])
    r0=analysis([r for r in rows if r['case'].startswith('r0_')],packet)
    assert r0==json.loads((root/'r0_analysis.json').read_text())
    r1={}
    selected={}
    for budget in ('0.05','0.1','0.2'):
        rr=[r for r in rows if r['case'].startswith('r1_'+budget+'_')]
        assert len(rr)==100
        r1[budget]=analysis(rr,packet,packet['controls'][budget])
        assert r1[budget]==json.loads((root/f'r1_{budget}_analysis.json').read_text())
        selected[budget]=dict(Counter(r['trace']['selected'] for r in rr))
    output=ROOT/'docs/analysis'
    summary={'run_id':packet['run_id'],'status':status,'r0':r0,'r1':r1,'selection_counts':selected,
             'source_sha256':packet['source_sha256'],'parent_run_id':packet['parent_run_id'],
             'verification':{'case_checksums':305,'uniform_controls':300,'inner_outer_group_isolation':True,
                             'all_summaries_recomputed':True},'self_test':json.loads((root/'self_test.json').read_text())}
    (output/'dart_gain_v1_results_2026-10-05.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# DART gain/structure v1: báo cáo thực nghiệm đầy đủ','',
           f"Run `{packet['run_id']}`. Trạng thái cuối `{status['state']}`; đủ **305/305 cases**.",'',
           '## Phạm vi và kiểm chứng','',
           'Đây là huấn luyện/replay thật trên outcome AppWorld đã có, không phải chạy lại solver. '
           '168 task, 56 generator, 14 agent. Public normal đã dùng trong nhiều vòng phát triển; '
           'không phải xác nhận độc lập. Không đọc challenge hoặc MMLU sealed.','',
           'Đã kiểm tra 305 checksum, 300 control choices/audit counts, tách nhóm inner/outer, '
           'và tính lại toàn bộ summaries/CI từ action traces; đều khớp.','',
           '## Full-label diagnostic R0','',
           '| Method | Thành công /168 | Chênh lệch điểm % với Global | CI 95% điểm % |','|---|---:|---:|---|']
    for m,values in r0['methods'].items():
        c=r0['contrasts'][m]['Global']; lo,hi=c['ci95']
        lines.append(f"| {m} | {values['mean_correct']:.2f} | {100*c['difference']:+.2f} | [{100*lo:+.2f}, {100*hi:+.2f}] |")
    lines += ['', 'R0 dùng toàn bộ nhãn train, không so nó với control chỉ được audit 10%.','',
              '## R1: cùng ngân sách audit','',
              'Mỗi ngân sách: 20 audit seeds × 5 outer folds; cùng đúng tập nhãn với UniformAuditGlobal. '
              'PairedGlobal dùng cùng tổng số nhãn với thiết kế lấy mẫu khác. Giá trị là số task thành công '
              'trung bình trên 168 task, không phải 168 solver runs mới cho mỗi router.','',
              '| Method | 5% | 10% (primary) | 20% |','|---|---:|---:|---:|']
    for m in r1['0.1']['methods']:
        numbers=[r1[b]['methods'][m]['mean_correct'] for b in ('0.05','0.1','0.2')]
        lines.append(f'| {m} | '+ ' | '.join(f'{n:.2f}' for n in numbers)+' |')
    lines += ['', '### Primary 10%: tất cả family so với hai controls','',
              '| Method | Control | Chênh lệch điểm % | CI 95% điểm % | Rescue | Harm |',
              '|---|---|---:|---|---:|---:|']
    for m,contrasts in r1['0.1']['contrasts'].items():
        for control,c in contrasts.items():
            lo,hi=c['ci95']
            lines.append(f"| {m} | {control} | {100*c['difference']:+.2f} | [{100*lo:+.2f}, {100*hi:+.2f}] | {c['rescues']:.2f} | {c['harms']:.2f} |")
    primary=r1['0.1']['primary_signal_pass']
    lines += ['',f"**Primary signal gate: {'PASS' if primary else 'FAIL'}.** Selected phải có CI lower > 0 với cả hai controls. "
              'Không chọn một family khác sau khi xem T để thay primary endpoint.','',
              'Bootstrap 5.000 lần theo generator, seed 1404, sau khi lấy trung bình audit seeds. '
              'CI exploratory chưa điều chỉnh toàn bộ lịch sử thử nghiệm; không phải bảo đảm triển khai.','',
              '## Ý nghĩa từng thay đổi','',
              '- FactorRidge chỉ chia sẻ thống kê model/scaffold để chọn một agent toàn cục; không phải contextual DART mới.',
              '- SemanticRidge giữ đủ MiniLM 384 chiều; TextRidge kiểm tra lexical features với cùng squared loss.',
              '- DirectUtility tối ưu signed utility qua softmax, thay vì dự báo xác suất bằng BCE. '
              'Nó là adaptation của hướng policy learning có trước, chưa chứng minh novelty.',
              '- Selected chọn family/regularization trong inner CV bằng đúng nhãn đã mua; không nhìn outer gold.',
              '- Chỉ trừ anchor khỏi ridge targets không thay thứ hạng với cùng thiết kế; đã có test kiểm chứng đại số.','',
              '## Bước tiếp theo','',
              'Nếu một family tốt hơn controls, coi đó là ứng viên phát triển: kiểm tra tính ổn định theo '
              'generator/ngân sách, khóa thiết kế và xác nhận trên dữ liệu độc lập. Nếu Selected không thắng, '
              'không thay tên family thắng nhất thành phương pháp primary. Lợi ích chỉ từ FactorRidge sẽ '
              'ủng hộ giảm nhiễu ước lượng agent, chưa chứng minh khai thác feedback sai hay transfer theo task.','',
              'Hướng bài báo cần chứng minh phần feedback correction/acquisition mang lợi ích tăng thêm '
              'so với gold-only structured controls cùng budget, rồi đối chiếu các phương pháp gần. '
              'Một con số cao hơn trên public normal chưa bảo đảm bài A/A*.','',
              '## Tài liệu','',
              '- [Protocol khóa trước](dart_gain_v1_protocol_2026-10-05.md).',
              '- [JSON tổng hợp đầy đủ](dart_gain_v1_results_2026-10-05.json).',
              '- [Causal LLM Routing](https://arxiv.org/html/2505.16037v2): cơ sở cho direct regret/utility optimization.',
              '- [Offline Multi-Action Policy Learning](https://arxiv.org/abs/1810.04778): nền tảng policy learning.',
              '- Raw artifacts: `results/dart_gain_v1/cloud/`; không commit các task/trajectory derivatives vào Git.','']
    (output/'dart_gain_v1_assessment_2026-10-05.md').write_text('\n'.join(lines))
    print(json.dumps({'verified_cases':len(rows),'primary_signal_pass':primary,'primary_methods':r1['0.1']['methods']},indent=2))


if __name__=='__main__':
    main()
