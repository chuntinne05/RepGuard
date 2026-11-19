"""Summarize completed verified experiments; never starts a model call."""
import json
import re
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def read(p):return json.loads(p.read_text())

def main():
    a=read(ROOT/'results/thesis_composition_cycle_02/summary.json')
    b=read(ROOT/'results/thesis_backbone_diversity_probe_v1/summary.json')
    c=read(ROOT/'results/thesis_modern_backbone_control_v1/summary.json')
    d=read(ROOT/'results/thesis_modern_direct_control_v1/summary.json')
    for name in ['repguard_composition_cycle02_verification_2026-10-19.json','repguard_backbone_diversity_verification_2026-10-19.json','repguard_modern_control_verification_2026-10-19.json','repguard_modern_direct_verification_2026-10-19.json']:
        assert read(HERE/name)['status']=='PASS'
    h=read(HERE/'repguard_modern_routing_headroom_2026-10-19.json');native=c['methods']['qwen3.5:27b'];modern=d['method']
    calls=a['actual_new_calls']+b['actual_new_calls']+c['actual_new_calls']+d['actual_new_calls'];assert calls==136
    lines=['# Quyết định nghiên cứu RepGuard — 19/10/2026','',
      '**Đã hoàn tất và kiểm lại 136 phản hồi model thật mới; chưa có phương pháp reputation vượt baseline được xác nhận.** Đây là một vòng sàng phương pháp, không phải đóng góp cuối của khóa luận. Giữ topic uy tín/chuyển bằng chứng trong hệ đa tác tử, chuyển trọng tâm khỏi weighted voting sang hiệu quả can thiệp có điều kiện.','',
      '136 responses gồm 72 trên 24 development reports đã xem và 64 trên 16 report mới so với các LIVE cohorts trước; không coi 136 là 136 task độc lập. 16 report mới vẫn là development. Chưa xác lập report overlap với archive cũ chỉ có query hashes; không nhận là final test hay contamination-free evaluation.','',
      '## Hai quyết định đã có bằng chứng','',
      '| Cấu hình trên cùng24report | Khớp target | Calls/câu | Mean Ollama eval giây |',
      '|---|---:|---:|---:|']
    names={'direct_pot':'Một agent PoT','self_review_1':'Một vòng tự kiểm','self_review_2':'Hai vòng tự kiểm','compose':'Hai lời giải + tổng hợp'}
    for name,m in a['methods'].items():lines.append(f'| {names[name]} | {m["correct"]}/24 | {m["model_calls_per_question"]} | {m["mean_ollama_eval_seconds"]:.2f} |')
    lines+=['','Compose0rescues/1harm; union17=bạn tốt nhất17. GateFAIL. **Không fit thêm reputation controller để chọn giữa các output này.** Self-review dùng checklist/prompt cố định, không nhận là best possible single-agent workflow. Một lượt PoT đã đủ thắng cấu hình compose này.','',
      '| Backbone, cùng16report/prompt/cap4096 | Khớp target | Valid | Output tokens | Mean Ollama eval giây | GPU |',
      '|---|---:|---:|---:|---:|---|']
    for name,m in c['methods'].items():lines.append(f'| {name} | {m["correct"]}/16 | {m["valid"]}/16 | {m["output_tokens"]:,} | {m["mean_ollama_eval_seconds"]:.2f} | {"L40S" if name=="qwen3.5:27b" else "L4"} |')
    lines.append(f'| qwen3.5:27b, think=False | {modern["correct"]}/16 | {modern["valid"]}/16 | {modern["output_tokens"]:,} | {modern["mean_ollama_eval_seconds"]:.2f} | L40S |')
    lines+=['','8B/14Bcùng11/16và cùng correctness mask: zero unique success, union11. GateFAIL. Trên mẫu này8Bkhông tiết kiệm eval runtime dù ít tham số; đây không phải kết luận thống kê cho mọi workload.','',
      f'Đối chứng 27B native đạt {native["correct"]}/16, nhưng {native["length_stops"]} responses dùng hết 4096 tokens và không xuất answer. Không dùng đây để kết luận giới hạn năng lực model. Giữ nguyên điểm/outputs; bổ sung một control hậu nghiệm trên **toàn bộ 16 câu**, chỉ tắt native thinking, cùng prompt/weights/cap, không chọn riêng câu lỗi. Control đạt {modern["correct"]}/16, {modern["length_stops"]} length stops, native-thinking nonempty={modern["native_thinking_nonempty"]}.','',
      f'So 14B: control think=False có {d["paired"]["qwen3:14b"]["direct_only_correct"]} câu đúng riêng và {d["paired"]["qwen3:14b"]["other_only_correct"]} câu sai riêng. Model 27B đã tải và pin digest thật trên app/volume riêng. Khác GPU và model package nên không gọi cùng compute; cùng source/prompt/output cap không đủ làm matched-cost experiment. Đây là model-configuration control trên development, không phải phương pháp reputation hay independent confirmation.','']
    if modern['correct']>b['methods']['qwen3:14b']['correct']:
        lines+=['Nâng backbone có cải thiện point score ở probe này. Đó là lợi ích của solver/configuration, không phải reputation. Phương pháp tiếp theo phải so với chính baseline mạnh hơn này, không chỉ so14B.']
    else:
        lines+=['Control think=False chưa cho thấy tăng official accuracy trên probe này. Native4K có truncation nên không kết luận model lớn không có năng lực tốt hơn. Không dùng tên/kích thước model để mặc nhận chất lượng hoặc chi phí.']
    modern_gpu=modern['mean_ollama_eval_seconds']*16*.000542
    small_gpu=b['methods']['qwen3:14b']['mean_ollama_eval_seconds']*16*.000222
    lines+=['',f'GPU-eval cost proxy cho cả16câu: 14B={small_gpu:.6f} USD; 27B think=False={modern_gpu:.6f} USD. Đây là runtime×GPUrate, không phải billing và không gồm cold load/idle/CPU/RAM. Mọi policy về sau phải so cả cấu hình solver này; không nhận lợi ích do tắt thinking thành gain reputation.']
    stats=read(HERE/'repguard_modern_direct_paired_analysis_2026-10-19.json')
    lines+=['',f'Đây chỉ là candidate baseline trên development: accuracy point gain {stats["accuracy_difference_pp"]:.1f} pp, paired bootstrap95% [{stats["paired_bootstrap95_accuracy_pp"][0]:.2f}, {stats["paired_bootstrap95_accuracy_pp"][1]:.2f}] pp; exact paired p={stats["exact_mcnemar_two_sided_p"]:.2f}. Cost-proxy ratio={stats["gpu_eval_cost_ratio_direct27b_over14b"]:.3f}, bootstrap95% [{stats["paired_bootstrap95_cost_ratio"][0]:.3f}, {stats["paired_bootstrap95_cost_ratio"][1]:.3f}]. Chưa xác nhận superiority/cost saving ở population. Zero harm/16 vẫn có cận trên một phía95% khoảng17.1%; không chứng minh non-inferiority2pp.']
    lines+=['','## Đối chứng rẻ và giới hạn headroom','',
      'Bảng dưới chỉ dùng cấu hình27B **native4096** đã lưu, không chọn nó làm baseline duy nhất để quảng bá tiết kiệm. Fixed14B đã có cùng11/16 và rẻ hơn ở proxy; không cần reputation để nhận khác biệt này. Control think=False bên trên cũng phải được xét trước khi chốt comparator.','',
      '| Replay trên16responses thật,27Bnative | Khớp target | Mean calls | GPU-eval cost proxy / direct27Bnative |',
      '|---|---:|---:|---:|']
    for name,m in h['methods'].items():lines.append(f'| {name} | {m["correct"]}/16 | {m["mean_calls"]:.3f} | {m["gpu_eval_cost_proxy_relative_to_direct27b"]:.3f} |')
    lines+=['','**Đây là replay từ outputs thật, không phải policy học đã chạy live.** Rule chỉ gọi27B khi14Bkhông executable; không biết gold. Dòng ORACLE dùng gold hiện tại để biết khi nào nên gọi: chỉ là trần chẩn đoán, tuyệt đối không là kết quả thuật toán. Các outputs27Blà solve độc lập, không được đổi tên thành expert repair có nhận incumbent.','',
      'Cost proxy nhân thời gian prompt/eval thực với GPUrate công bố, L4=$0.000222/s, L40S=$0.000542/s theo[Modal pricing](https://modal.com/pricing) tại19/10/2026. Không gồm load/startup/idle, CPU/RAM, audit hay cold-reload effects, không phải hóa đơn. Chưa chứng minh non-inferiority hoặc cost saving của một policy triển khai.','',
      '## Root causes được khoanh bằng trace và can thiệp','',
      '1. **Bank hiện tại thiếu output bổ sung:** trên24report, mọi self-review giữ nguyên correctness; compose không tạo rescue. Trên16report khác,8B/14Bđúng/sai cùng câu. Thay một learner chọn output không thể vượt oracle của đúng bank đó. Không suy từ sample sang mọi hệ multi-agent.','2. **Source có tồn tại chưa xác nhận binding:** FRTcompose đổi cặp số đúng năm thành cặp source có thật nhưng gán sai năm, làm5,908thành6,890. EWcompose chỉ chọn một trong hai khoản0.6/4.1, chưa tạo tổng4.7mà reference dùng. Không quy lỗi này cho formatter.','3. **Official score và semantic validity cần tách:** trong5shared errors mới có4flag về entity subset, stock/flow hoặc sign convention; WRKcũ còn nhầm metric valuation allowance và deferred-tax asset. Đây là flags cần hai người kiểm, không phải4label errors đã xác nhận. Không relabel primary và không dùng flags để tuyên bố đã thắng.','',
      'Vì vậy, research contribution không nên là “nhiều agent tốt hơn” hay “thêm uy tín”. Cần tạo can thiệp đúng phần, có khả năng bổ sung trước, rồi mới kiểm liệu lịch sử dự báo được tác dụng của can thiệp ấy ngoài development hay không.','',
      '## Research gap và hướng phương pháp','',
      'Candidate question: **uy tín theo trạng thái bằng chứng và phạm vi sửa có giúp chọn can thiệp hữu ích trên task mới, khi verifier chỉ kiểm được một phần và audit có chi phí, hơn same-budget self-review và learned action-value với cùng dữ liệu không?**','',
      'Cơ chế cần thử: giữ PoT đủ năng lực; biểu diễn source–quantity–period–unit; actions KEEP/evidence/operation-unit/bundle; học rescue/harm và interaction từ branches đã thực thi và audit; chọn action trước khi biết correctness. Không coi source-pass là gold. History phải index configuration/model/prompt/executor, tránh dùng profile cũ sau đổi contract.','',
      'Đây là giả thuyết, chưa là novelty/superiority đã chứng minh. [MoCA-Agent](https://arxiv.org/abs/2606.11537) đã có claim-based verification; [C3](https://arxiv.org/abs/2603.06859) và[GCJR](https://arxiv.org/abs/2608.29228) đã có counterfactual/joint-repair credit hoặc localization. Khác biệt cần kiểm là transfer và lựa chọn scope repair trên task mới không có oracle chỉ lỗi; phải vượt contextual learner công bằng. Learned selector train trên history vẫn dùng lịch sử dù không có biến mang tên reputation.','',
      '## Những việc đã chuẩn bị cho bước tiếp','',
      '-40câu có phiếu source-only cho hai reviewer độc lập; hiện0annotation hoàn tất. Khóa đánh giá metric/kỳ/unit/scope trước xem method identity. Giữ FinQA official score và semantic audit riêng.','-TAT-QA: pin TRAIN/evaluator và chọn64arithmetic contexts theo metadata. Chạy evaluator gốc64gold roundtrip và zero-interface software checks; **chưa có inference/model score** trên corpus này. Không lấy software selfcheck làm kết quả model.','-Giữ200development/50calibration/150confirmation report IDs, tách124LIVEreport đã dùng. Confirmation chưa có inference hay extracted outcome;150không mặc nhận đủ power. Archive report-disjointness còn phải làm rõ/disclose.','-Ứng viên scope/interaction repair cần preflight bảo toàn năng lực solver, rồi thử trên report development mới sau audit; nếu corpus có quá nhiều target ambiguity, dùng corpus có contract rõ hơn trước mở rộng history. Không tiếp tục tune trên24câu cũ.','-Sau khi bank có headroom mới train/calibrate và đánh giá policy thật trên confirmation. So strong single-agent, fixed expert, rule, contextual action-value, global/conditional history và các ablations. Prototype chỉ là phần trình diễn nhỏ.','',
      'Một khóa luận nghiên cứu vững cần phương pháp có cơ chế và bằng chứng end-to-end rõ; không cần nhận thắng mọi ChatGPT/Claude. Đợt này chưa so trực tiếp hai sản phẩm đó và không nhận đã đánh bại chúng.','',
      '## Hồ sơ để đọc','',
      '-`repguard_research_cycle_02_2026-10-19.md`:72calls, chi tiết FRT/EW/WRK và gate.','-`repguard_research_gap_2026-10-19.md`:ma trận related work và những novelty claims cần tránh.','-`repguard_method_candidate_2026-10-19.md`:thiết kế phương pháp cụ thể, ghi rõ chưa triển khai.','-Bốn verifier/manifest JSON và các run directories giữ raw responses/source snapshots.7primary files của pilot cũ không đổi.','-Tất cả scores là kết quả thật đã lưu/tái tính; không model mock. Không tự lên automation hay gửi thông điệp cho thành viên nhóm.','']
    doc='\n'.join(lines).replace('union17=bạn tốt nhất17','union 17 = phương án cố định tốt nhất 17')
    doc=doc.replace('Compose0rescues/1harm','Compose: 0 rescue / 1 harm').replace('GateFAIL','Gate FAIL')
    doc=doc.replace('8B/14B','8B / 14B').replace('Model27B','Model 27B').replace('So14B','So với 14B').replace('KhácGPUvà','Khác GPU và')
    fixes={'cùng24':'cùng 24','cùng16':'cùng 16','cap4096':'cap 4096','cùng11':'cùng 11',
      'union11':'union 11','này8B':'này, 8B','so14B':'so với 14B','cả16':'cả 16',
      'cấu hình27B':'cấu hình 27B','Fixed14B':'Fixed 14B','native4096':'native 4096',
      'trên16':'trên 16','thật,27B':'thật, 27B','gọi27B':'gọi 27B','khi14B':'khi 14B',
      'outputs27B':'outputs 27B','theo[':'theo [','tại19':'tại 19','trên24':'trên 24',
      'khác,8B':'khác, 8B','FRTcompose':'FRT: compose','làm5,908':'làm 5,908',
      'thành6,890':'thành 6,890','EWcompose':'EW: compose','khoản0.6':'khoản 0.6',
      'tổng4.7':'tổng 4.7','trong5':'trong 5','có4':'có 4','WRKcũ':'WRK cũ','phải4':'phải 4',
      'và[':'và [','hiện0':'hiện 0','chọn64':'chọn 64','gốc64':'gốc: 64','Giữ200':'Giữ 200',
      'tách124LIVEreport':'tách 124 report LIVE','snapshots.7':'snapshots. 7'}
    for old,new in fixes.items():doc=doc.replace(old,new)
    doc=re.sub(r'(?m)^-(?=\S)','- ',doc)
    parts=re.split(r'(`[^`]*`|https?://[^\s)]+)',doc)
    for i in range(0,len(parts),2):
        parts[i]=re.sub(r'(?<=\d)(?=[a-zà-ỹ]{2})',' ',parts[i])
        parts[i]=re.sub(r'(\d+B)(?=[A-Za-zÀ-ỹ])',r'\1 ',parts[i])
        parts[i]=re.sub(r'(?m)^-(?=\S)','- ',parts[i])
    (HERE/'repguard_research_decision_2026-10-19.md').write_text(''.join(parts))
    print(json.dumps({'report':'repguard_research_decision_2026-10-19.md','new_real_responses':calls,'modern_correct':modern['correct'],'reputation_superiority_claim':False}))

if __name__=='__main__':main()
