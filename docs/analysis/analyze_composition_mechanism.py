"""Exploratory paired analysis after complete frozen collection. No inference."""
import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from thesis_pilot.core import digest,correct
from thesis_pilot.composition_tools import candidate,canonical
from thesis_pilot.causal_tools import verify as dsl_verify
from repguard_unit_failure_diagnostic import surgery

def read(p):return json.loads(p.read_text())

def main():
    dest=ROOT/'results/thesis_composition_cycle_02';summary=read(dest/'summary.json');traces=read(dest/'traces_private.json')['rows']
    cases=read(ROOT/'results/thesis_causal_repair_v1/plan.json')['fresh_cases'];cc={c['id']:c for c in cases}
    rng=np.random.default_rng(19102026);indices=rng.integers(0,len(traces),size=(20000,len(traces)))
    comparisons={}
    for base in ['direct_pot','self_review_1','self_review_2']:
        a=np.array([r['outcomes']['compose'] for r in traces],dtype=int);b=np.array([r['outcomes'][base] for r in traces],dtype=int)
        win=int(((a==1)&(b==0)).sum());loss=int(((a==0)&(b==1)).sum());n=win+loss
        p=min(1.,2*sum(math.comb(n,k) for k in range(min(win,loss)+1))/2**n) if n else 1.
        effect=(a-b)[indices].mean(axis=1)*100
        comparisons[base]={'compose_only_correct':win,'baseline_only_correct':loss,'net_gain_count':win-loss,
                           'difference_pp':float((a-b).mean()*100),'paired_bootstrap95_pp':np.quantile(effect,[.025,.975]).tolist(),
                           'exact_mcnemar_two_sided_p_exploratory':p,'confirmatory_claim':False}
    rows=[]
    for r in traces:
        i=r['id'];c=cc[i];h=digest(i)[:16]
        v=read(ROOT/f'results/thesis_causal_repair_v1/fresh/{h}_initial.json')['output']['verification']
        a,changed=surgery(v['answer']);v=dsl_verify(c,json.dumps(a)) if changed else v
        cheap_ok=bool(v['hard_pass'] and correct(v['value'],r['official_target']))
        rows.append({**r,'cheap_dsl_correct':cheap_ok,'cheap_dsl_value':v['value'],
                     'compose_correct_beyond_both_parents':bool(r['outcomes']['compose'] and not r['outcomes']['direct_pot'] and not cheap_ok),
                     'compose_correct_beyond_both_self_reviews':bool(r['outcomes']['compose'] and not r['outcomes']['self_review_1'] and not r['outcomes']['self_review_2'])})
    out={'scope':'Post-collection exploratory paired mechanism analysis, not independent confirmation',
         'n':24,'new_model_calls':0,'comparisons':comparisons,
         'compose_rescues_beyond_both_parents':sum(r['compose_correct_beyond_both_parents'] for r in rows),
         'compose_rescues_beyond_both_self_reviews':sum(r['compose_correct_beyond_both_self_reviews'] for r in rows),
         'gate_for_history_learning':summary['gate_for_history_learning'],
         'bootstrap_replicates':20000,'seed':19102026,'rows':rows}
    (HERE/'repguard_composition_mechanism_2026-10-19.json').write_text(json.dumps(out,indent=2))
    report=['# Vòng 2: đối chiếu bằng chứng và tự sửa đủ compute','',
            'Ngày 19/10/2026. **72 phản hồi model thật mới trên 24 báo cáo development đã xem.** Đây là phép sàng cơ chế, chưa là test độc lập và chưa triển khai learner reputation.','',
            '## Kết quả','',
            '| Phương án | Đúng/24 | Rescue / harm so PoT | Calls/câu | Mean Ollama eval giây |',
            '|---|---:|---:|---:|---:|']
    names={'direct_pot':'Một agent PoT','self_review_1':'PoT + tự sửa 1 lần','self_review_2':'PoT + tự sửa 2 lần','compose':'PoT + DSL + tổng hợp'}
    for a,m in summary['methods'].items():report.append(f'| {names[a]} | {m["correct"]} | {m["rescue_vs_direct"]} / {m["harm_vs_direct"]} | {m["model_calls_per_question"]} | {m["mean_ollama_eval_seconds"]:.2f} |')
    c=comparisons['self_review_2'];s=summary
    report+=['',f'Compose so self2: {c["compose_only_correct"]} rescue, {c["baseline_only_correct"]} harm, net {c["net_gain_count"]:+d} câu. Paired bootstrap 95% của chênh lệch là [{c["paired_bootstrap95_pp"][0]:.2f}, {c["paired_bootstrap95_pp"][1]:.2f}] pp trên development này. Không dùng interval/p-value exploratory làm xác nhận superiority hay equivalence.','',
             f'Oracle union các action={s["action_oracle_union"]}/24; best fixed={s["best_fixed"]}/24. Gate cố định={"PASS" if s["gate_for_history_learning"] else "FAIL"}. Compose tạo {out["compose_rescues_beyond_both_parents"]} câu đúng khi cả hai output cha sai; {out["compose_rescues_beyond_both_self_reviews"]} câu đúng mà cả hai vòng self-review sai. Oracle không là accuracy của thuật toán.','',
             '## Quyết định','']
    if not s['gate_for_history_learning']:
        report+=['Không fit thêm reputation controller trên pool này. Chưa đủ bằng chứng rằng phối hợp ở cấu hình hiện tại tạo đủ headroom để học chọn can thiệp. Giữ các output và kết quả âm; không thay threshold hoặc nhãn để cứu giả thuyết.']
    else:
        report+=['Pool qua gate sàng headroom; điều này chưa chứng minh lịch sử chọn được action đúng. Bước cần tiếp là khóa representation/learner và thu paired history trên báo cáo mới, so current-state-only learned routing và same-budget self-repair. Không dùng 24 development này làm final claim.']
    report+=['','## Thiết kế, chi phí và phạm vi kết luận','',
             'Mọi nhánh mới cùng tài liệu, checklist metric/kỳ/scope/unit/sign, native thinking, cap4096, seed19102026 và executor. Self1 xem PoT; self2 xem self1 đã acceptance; compose xem PoT cùng DSL với source contexts. Invalid giữ current proposal theo rule cơ học, không dùng gold. Baseline PoT và DSL cha là các call thật vòng trước; dùng cache chỉ để tránh thu lại, vẫn charge vào chi phí phục vụ từng phương án.','',
             'Compose và self2 cùng3calls nhưng cap tổng lần lượt9728 và12288; không mặc nhận cùng compute thực tế. Mean Ollama eval tính prompt_eval_duration+eval_duration, loại model load: là proxy runtime, không phải hóa đơn hoặc latency live. Self1/direct là đối chứng ít calls hơn vẫn phải báo.','',
             f'Đợt này có {s["actual_new_calls"]} calls mới, input {s["new_input_tokens"]:,}, output {s["new_output_tokens"]:,} tokens; {s["new_native_thinking_nonempty"]} phản hồi có native thinking, {s["new_length_stops"]} dừng do cap. Không quality retry, không model mock. Final score giữ exact FinQA round5; không oracle ×100 và không sửa các nhãn nghi vấn.','',
             'Tất cả24report đã dùng development trước đó, cùng một backbone Qwen3:14b. Không suy ra generalization, SOTA, hiệu quả history hoặc lợi ích mọi hệ multi-agent. Gold chỉ dùng khi analyze sau collection; solver không nhận gold/reference program. Source/arithmetic pass không là xác nhận semantic đúng.','',
             '## Những câu thay đổi kết quả so PoT','',
             '| Case | Target chính thức | PoT | Self1 | Self2 | Compose |',
             '|---|---:|---:|---:|---:|---:|']
    for r in rows:
        if any(r['outcomes'][a]!=r['outcomes']['direct_pot'] for a in ['self_review_1','self_review_2','compose']):
            def cell(a):return f'{r["values"][a]} ({"đúng" if r["outcomes"][a] else "sai"})'
            report.append(f'| {r["id"]} | {r["official_target"]} | {cell("direct_pot")} | {cell("self_review_1")} | {cell("self_review_2")} | {cell("compose")} |')
    report+=['','Các giá trị trên là đối chiếu với official target, không adjudication ngữ nghĩa. Phiếu audit độc lập đã chuẩn bị nhưng chưa có người nộp annotation.','',
             '## Artefacts','',
             '- Protocol và source snapshots: `results/thesis_composition_cycle_02/plan.json`, `registration.json`, `frozen_source.zip`.','- Raw receipts72, summary, traces_private trong cùng thư mục run.','- `verify_composition_cycle02.py` kiểm lại hash, prompts, canonical execution, acceptance/fallback, cost/outcomes và gate; không gọi model.','- `repguard_research_gap_2026-10-19.md` định vị với MoCA/CLAIR-Fin/MERIT/C3/GCJR và các routing/reputation controls.','- TAT-QA source inventory64 TRAIN contexts đã pin nguồn/metric, **chưa có inference hoặc điểm TAT-QA**. Không gọi context UID là report-disjoint.','']
    (HERE/'repguard_research_cycle_02_2026-10-19.md').write_text('\n'.join(report))
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
