"""Postrun audit and human-readable report, preserving frozen cycle02 scoring."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from experiments.arqa_v2.preflight import OUT, REPORT, ROOT, digest, write
from experiments.arqa_v2.study import PROFILES, WORKFLOWS
from research_ops.source_receipt import inspect


def report(directory):
    directory=Path(directory)
    result=json.loads((directory/'analysis.json').read_text())
    plan=json.loads((directory/'plan.json').read_text())
    public=json.loads((directory/'public_pilot.json').read_text())
    attempts={p.stem:json.loads(p.read_text()) for p in (directory/'attempts').glob('*.json')}
    records=[json.loads(p.read_text()) for p in (directory/'responses').glob('*.json')]
    source_checks={rel:digest((ROOT/rel).read_bytes())==expected for rel,expected in plan['source_hashes'].items()}
    assert all(source_checks.values()),'Frozen source changed'
    assert set(attempts)=={r['request_id'] for r in records},'Attempt/response membership mismatch'
    assert len(records)==plan['max_calls'],'Incomplete run'
    registered=datetime.fromisoformat(plan['registered_utc'])
    for r in records:
        assert datetime.fromisoformat(r['created_utc'])>=registered,'Generation predates registration'
        assert attempts[r['request_id']]['prompt_sha256']==r['prompt_sha256'],'Attempt prompt mismatch'
    audit={'plan_id':plan['plan_id'],'source_checks':source_checks,'attempts':len(attempts),'responses':len(records),
           'attempt_response_ids_equal':True,'all_generations_after_registration':True,
           'native_thinking_outputs':sum(bool(r['response']['message'].get('thinking')) for r in records),
           'length_stops':sum(r['response'].get('done_reason')=='length' for r in records),
           'frozen_evaluator_receipt_audit':result['receipt_audit'],
           'post_registration_diagnostic':'Final-result source dependency; not a replacement primary score.'}
    cases={r['id']:r['case'] for r in public['items']}
    by_key={(r['item_id'],r['profile'],r['workflow']):r for r in records}
    scores={ (r['item_id'],r['profile'],r['workflow']):r for r in json.loads((directory/'scores_private.json').read_text())}
    diagnostics={}
    for p in PROFILES:
        for w in WORKFLOWS:
            rows=[r for r in records if r['profile']==p and r['workflow']==w]
            checks=[(r,inspect(cases[r['item_id']],r['raw_text'])) for r in rows]
            accepted=[r for r,c in checks if c['source_and_arithmetic_pass']]
            wrong=sum(not scores[(r['item_id'],p,w)]['correct'] for r in accepted)
            warnings=Counter(s for r,c in checks for s in c.get('dataflow',{}).get('warnings',[]))
            diagnostics[p+'/'+w]={'final_dependency_filter_accepted':len(accepted),'wrong_among_accepted_numeric_unit':wrong,
                                  'risk_relative_to_numeric_unit_gold':wrong/len(accepted) if accepted else None,
                                  'warnings':dict(warnings),'semantic_verified_count':0}
    contrast=result['contrasts']['checklist']
    lines=['# ARQA vòng02 — kết quả và quyết định','',
           f"Plan `{plan['plan_id']}`; registration {plan['registered_utc']}. {len(records)} real responses,24QA/24connected groups. Không phải official ARQA score.",'',
           f"**Primary checklist cross−self: {100*contrast['delta']:+.2f}pp; CI95% [{100*contrast['ci95'][0]:+.2f}; {100*contrast['ci95'][1]:+.2f}]pp. Gate: {result['scientific_gate']}.**",'',
           '**Measurement warning:** hậu kiểm phát hiện precision/unit và scope của câu hỏi cần adjudication; xem [phân tích oracle](ARQA_CYCLE02_ORACLE_VA_PATH_TIEP.md). Gate FAIL là quyết định không mở rộng theo protocol này, không chứng minh cross-agent vô ích hoặc mọi số bị chấm sai là lỗi nghiệp vụ thật.','',
           'Không thay primary bằng arm có điểm cao nhất. Source/program/parent/config/model/GPU receipt và attempt audit đã kiểm; xem JSON kèm theo.','',
           '|Profile / workflow|Đúng số+unit /24|Đúng số /24|Schema valid|Calls/item|Mean workflow tokens (in+out)|Mean serving s/workflow|',
           '|---|---:|---:|---:|---:|---:|---:|']
    for p in PROFILES:
        for w in WORKFLOWS:
            m=result['metrics'][p+'/'+w]
            tokens=(m['workflow_input_tokens']+m['workflow_output_tokens'])/m['n']
            lines.append(f"|{p}/{w}|{m['correct']}|{m['numeric_correct']}|{m['valid']}|{m['workflow_calls_per_item']}|{tokens:.1f}|{m['mean_workflow_serving_seconds']:.2f}|")
    lines.extend(['','Hai profiles dùng cùng output schema và checker; checklist được cấp cả direct/self/cross. Self/cross có cùng call/token ceilings, nhưng token thực khác nhau. Direct1call là baseline thấp chi phí, không dùng để nhận matched-cost gain. Serving seconds là số đo request tại Ollama, không là thời gian người dùng hay USD billing.',''])
    for key in ('standard','interaction'):
        c=result['contrasts'][key]
        lines.append(f"- Secondary {key}: {100*c['delta']:+.2f}pp, CI95% [{100*c['ci95'][0]:+.2f}; {100*c['ci95'][1]:+.2f}]pp.")
    lines.extend([f"- Checklist cross so self: {result['checklist_cross_rescues']}rescues, {result['checklist_cross_harms']}harms, rescue trên{result['checklist_rescue_groups']}groups.",
                  f"- Tổng counters corpus: {result['tokens_actual_terminal_total']['input']:,}input / {result['tokens_actual_terminal_total']['output']:,}output tokens, không phải hóa đơn. Schema validity {result['schema_validity']:.2%}; length stops {audit['length_stops']}.",'',
                  '## Kiểm cơ học không đủ làm semantic verification','',
                  'Diagnostic final-dependency được thêm sau registration, giữ riêng score frozen. Nó bỏ program có source reads không ảnh hưởng kết quả cuối. Kể cả PASS vẫn có thể sai metric/formula/unit; các risk dưới đây chỉ so numeric/unit gold, không phải risk nghiệp vụ đã adjudicate. Không so risk giữa coverage khác nhau để kết luận thắng.','',
                  '|Profile / workflow|Final-dependency filter nhận /24|Sai số+unit trong phần nhận|','|---|---:|---:|'])
    for k,d in diagnostics.items():lines.append(f"|{k}|{d['final_dependency_filter_accepted']}|{d['wrong_among_accepted_numeric_unit']}|")
    lines.extend(['','## Giới hạn và bước tiếp','',
                  '24groups nhỏ, một issuer, hai họ quantized model, nguồn bảng oracle sẵn; không có retrieval evaluation hoặc company transfer. Chưa có human semantic adjudication;0người dùng,0interviews. Oracle nguồn và decimal rounding được audit trước selection; vẫn có thể thiếu thẩm định diễn giải câu hỏi. Cùng schema không chứng minh cùng năng lực model.','',
                  'Giữ gate đã khóa. Nếu FAIL: dừng scale/history cho bank này; xem các lỗi và semantic oracle, không chọn lại metric/subset. Nếu GO: vẫn cần human adjudication, stronger single và confirmation độc lập trước claim hiệu quả. [Path kế tiếp](GAP_RECHECK_VA_CONFIRMATION_PATH.md) và [phiếu review](SOURCE_RECEIPT_VA_HUMAN_REVIEW.md).','',
                  '## Case review: tất cả24câu, hậu nghiệm','',
                  'Chỉ phục vụ phân tích lỗi; không làm lại selection hoặc đổi gold theo model. Raw outputs nằm trong thư mục results cùng plan, không tái phát hành nguồn theo mặc định.',''])
    for i,row in enumerate(public['items'],1):
        vals=[]
        for p in PROFILES:
            vals.append(p+': '+', '.join(w+'='+str(scores[(row['id'],p,w)]['correct']) for w in WORKFLOWS))
        lines.extend([f"### {i}. {row['id']}",'',row['case']['question'],'','; '.join(vals),''])
    write(REPORT/'arqa_v2_receipt_audit.json',audit)
    write(REPORT/'arqa_v2_dependency_diagnostic.json',diagnostics)
    (REPORT/'ARQA_CYCLE02_RESULTS_VA_QUYET_DINH.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'audit':'PASS','responses':len(records),'primary':contrast,'gate':result['scientific_gate'],'report':str(REPORT/'ARQA_CYCLE02_RESULTS_VA_QUYET_DINH.md')},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);report(p.parse_args().directory)
