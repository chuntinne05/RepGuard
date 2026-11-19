# RepGuard: kịch bản slide và chuẩn bị trao đổi với Thầy

**Ngày 27/10/2026 • Thời lượng gợi ý 22–25 phút, chưa gồm hỏi đáp**

Tài liệu gốc: [Literature review và tiến độ chi tiết](REPGUARD_LITERATURE_REVIEW_VA_BAO_CAO_TIEN_DO.md). Mọi mã [Rxx] dùng cùng danh mục nguồn trong tài liệu gốc. Các số liệu dự án là development results, trừ khi ghi khác. Đây là nội dung để làm slide, chưa phải file PowerPoint.

## 1. Câu chuyện nên giữ xuyên suốt

**Câu hỏi:** khi lịch sử có thể được chấm sai hoặc thiếu, hệ thống nên dựa vào bằng chứng nào để quyết định tin/gọi/sửa bằng agent nào?

**Literature đã có:** history weighting; skill conditioning; current evidence; proxy+audit; claim verification; recovery/memory; counterfactual credit.

**Tiến độ của em:** đã xây hệ thống, thu kết quả thật, kiểm toán và loại được nhiều lời giải thích thay thế; chưa xác nhận lợi ích riêng của reputation trước đầy đủ strong controls.

**Phép thử tiếp:** cần một regime feedback có ích cho quyết định, rồi kiểm explicit reputation so với learner cùng thông tin, ở đúng budget/cost và trên task chưa dùng để sửa method.

Khoảng 60% thời gian nên dành literature và định vị; phần tiến độ chọn 2–3 bảng quan trọng, để toàn bộ lịch sử runner ở backup. Không đưa một slide kín tên 40–50 bài; mỗi slide literature cần một kết luận thiết kế.

## 2. Bố cục 22 slide chính

### Slide 1 — Tên đề tài và mục tiêu buổi báo cáo (20 giây)

**Đưa lên slide:**

- RepGuard: reputation dưới imperfect feedback.
- Literature review, bằng chứng tiến độ, kế hoạch xác nhận.
- Ngày 27/10/2026; họ tên/mã sinh viên/GVHD do bạn điền đúng thông tin chính thức.

**Lời nói:** “Lần này em bổ sung phần literature review còn thiếu, dùng nó để định vị lại contribution và giải thích các kết quả development mới nhất.”

Không thay tên đề tài được duyệt bằng tên candidate mới khi chưa thống nhất với Thầy.

### Slide 2 — Bài toán: lịch sử tốt chưa chắc dùng được cho câu mới (50 giây)

**Đưa lên slide:** một ví dụ A giỏi lookup, B giỏi multi-step; 2 câu hỏi độc lập: feedback cũ đúng không, task cũ liên quan không?

**Lời nói:** “Một agent có nhiều phản hồi tích cực có thể được chấm quá dễ, hoặc chỉ mạnh ở loại câu khác. Em tách reliability của phản hồi và relevance của lịch sử. Đầu ra cần đánh giá cuối cùng là quyết định, không chỉ reputation score.”

**Hình:** History → reliability/relevance → decision → outcome. Ví dụ là minh họa, không dùng số giả trông như kết quả thật.

### Slide 3 — Bản đồ literature: 7 nhánh nghiên cứu (50 giây)

**Đưa lên slide:**

1. Reputation/conditional trust.
2. Expert influence và security.
3. Imperfect feedback/PPI/audit.
4. Routing/cascade và cost.
5. Executable reasoning/claim verification.
6. Repair memory/counterfactual credit.
7. Benchmark và evaluator validity.

**Lời nói:** “Các nhánh gần nhau nhưng khác object, feedback và quyền quan sát. Em dùng ba tiêu chí đó để so sánh, thay vì chỉ so accuracy khác benchmark.”

### Slide 4 — Nền tảng Beta và ECRT đang cài đặt (70 giây)

**Đưa lên slide:** `α=α₀+Στmp`, `β=β₀+Στm(1−p)`; chú giải p=reliability-adjusted correctness, τ=task relevance, m=observed evidence mass.

**Lời nói:** “Beta reputation là nền tảng có từ trước. ECRT trong repo dùng calibration để suy p, taxonomy để suy τ và cộng bằng chứng mềm. Đây là representation đã triển khai, chưa tự tạo guarantee posterior khi feedback/correlation chưa được mô hình hóa đầy đủ.”

**Nguồn:** [R01]; code `ecrt.py`, `transfer.py`, `baselines.py`.

**Ghi chú backup:** lower-bound implementation là xấp xỉ normal-style, không exact Beta quantile.

### Slide 5 — Conditional Agent Trust: khi nào conditioning đáng làm? (70 giây)

**Đưa lên slide:** agent×skill; sparse evidence; correlated skills; borrowing vừa giảm variance vừa tạo laundering channel.

**Lời nói:** “Bài gần nhất của Xia và Wang đã nghiên cứu skill-conditioned reputation và mượn bằng chứng. Setup coi outcome kiểm được từ môi trường. Điểm em muốn kiểm thêm là feedback cũng có sai số, nhưng chỉ thêm calibration chưa đủ; nó phải giúp chọn tốt hơn controls.”

**Nguồn:** [R03], arXiv 2606.14200v1.

### Slide 6 — Historical credibility và MiniRep: lịch sử phải gặp bằng chứng hiện tại (65 giây)

**Đưa lên slide:** Credibility Scoring → weighted influence từ past contributions; MiniRep → history+current quality/risk+clone-group cap.

**Lời nói:** “Hai tiền lệ này khiến history weighting hay history kết hợp current warnings không còn là novelty có thể nhận chung. Em cần so phần representation/audit cụ thể với một comparator có cùng tín hiệu.”

**Nguồn:** [R02,R05]. Không nói MiniRep không xử lý imperfect signals; bài có cả estimated-quality feedback.

### Slide 7 — Vì sao biết expert vẫn có thể chọn sai? (55 giây)

**Đưa lên slide:** expert identification≠expert leveraging; reviewer có thể gây harmful correction; identity/provenance≠semantic truth.

**Lời nói:** “Multi-Agent Teams Hold Experts Back cho thấy vấn đề không chỉ tìm ai mạnh. Quyền ảnh hưởng và cách sửa output quyết định việc expert có được dùng đúng không. Bởi vậy em đo final answer, rescue và harm, so cả best single agent.”

**Nguồn:** [R04,R39,R40].

**Backup security:** WEREWOLF đã có Findings of EMNLP 2026 [R06]; controlled poisoning của repo chưa tương đương learned attack đó.

### Slide 8 — Feedback: JSON hợp lệ, calibration tốt, lựa chọn tốt là 3 điều khác (70 giây)

**Đưa lên slide:** validity → Brier/calibration → paired comparison → decision gain.

**Lời nói:** “LLM judge có bias và giới hạn reasoning. Một judge có thể dự báo câu nào dễ cho tất cả models, giảm Brier, nhưng không biết A hơn B trên cùng câu. Em cần kiểm pair signal trước khi mở rộng collection.”

**Nguồn:** [R08,R09]; bảng FinQA ở slide 18/backup.

### Slide 9 — PPI và limited audits: prediction cần residual correction (75 giây)

**Đưa lên slide:** `mean prediction + mean audited residual`; Ao: biased proxy+selective audits+propensity; PROBE: paired proxy+residual-variance certificate.

**Lời nói:** “Hiệu chỉnh predictions bằng ít gold là nền tảng có trước. Khi mua nhãn thích nghi phải giữ sampling probabilities và inference đúng. Guarantee của các bài không được nhập nguyên trạng vào archive binary shared-question của em.”

**Nguồn:** [R10–R14,R43]. Chỉ giữ một công thức trên slide; chi tiết assumptions để backup.

### Slide 10 — Routing phải tính cả acquisition cost và strong controls (75 giây)

**Đưa lên slide:** RouteLLM: prompt routing; R 2: model+length budget; SaveRouter: sparse acquisition và hoàn vốn; Causal Routing/CABS: regret/surrogate feedback.

**Lời nói:** “Em phân biệt chọn model toàn cục, prompt routing và cascade sau khi đã thấy output. Những phương pháp dùng history để học gain hay sparse feedback đã có tiền lệ; RepGuard phải chứng minh reliability/audit structure thêm giá trị ở cùng thông tin và cost.”

**Nguồn:** [R16,R17,R29,R42,R46,R48].

### Slide 11 — PAL/PoT và self-review: baseline phải đủ năng lực (60 giây)

**Đưa lên slide:** LLM hiểu và lập chương trình → interpreter tính; self 1/self 2 có cùng tools/calls thích hợp.

**Lời nói:** “Nếu baseline bị lỗi format hoặc phải tính nhẩm, method nhiều agent dễ có gain giả. Em đã bổ sung PoT và self-review, giữ strict score riêng với readout diagnostics. Lợi ích sửa compiler không được quy thành reputation.”

**Nguồn:** [R20–R23].

### Slide 12 — MoCA-Agent và CLAIR-Fin: verification ở mức claim đã có (70 giây)

**Đưa lên slide:** fact/formula/unit/sign; claim ledger; source authority; executable synthesis; adaptive review.

**Lời nói:** “Vì các hướng này đã kiểm claims tài chính, việc thêm extractor, accountant và reviewer không đủ mới. Câu hỏi của em phải nằm ở historical utility sau kiểm chứng một phần, và phải vượt adapted claim-verification control.”

**Nguồn:** [R24,R25]. Không xếp hạng điểm FinQA của paper với pilot 20 câu.

### Slide 13 — DARC, STAR và MERIT: lịch sử lỗi và repair đã có tiền lệ (65 giây)

**Đưa lên slide:** failure type → admissible repair; traces → recovery; finalized repair memory → task sau.

**Lời nói:** “Một method mới phải hơn diagnosis-guided recovery hoặc memory retrieval dùng cùng feedback. MERIT có oracle-assisted benchmark feedback, nên không thể coi source-check pass của em có cùng quyền quan sát.”

**Nguồn:** [R26–R28].

### Slide 14 — Counterfactual credit: cơ chế mới hay đổi cách biểu diễn? (65 giây)

**Đưa lên slide:** C3: message replacement+continuation; GCJR: joint repairs; `dEO=dE+dO+I`; same linear estimator có thể tương đương action-value.

**Lời nói:** “Tách credit là cách giải thích có ích nhưng chưa tự thành thuật toán mới. Nếu cùng features/loss/regularization, các regression components có thể cộng ra đúng cùng action-value predictor. Phải chỉ ra cấu trúc transfer hoặc uncertainty nào thật sự tạo lợi ích.”

**Nguồn:** [R30–R32] và ghi chú đại số nội bộ 20/10.

### Slide 15 — Research question được thu hẹp (75 giây)

**Đưa lên slide:**

- RQ 1: feedback có tín hiệu cho agent/action contrasts?
- RQ 2: history structure hơn learner cùng thông tin?
- RQ 3: gain còn sau rescue/harm và total cost?
- Candidate gap, chưa proven novelty/superiority.

**Lời nói:** “Em không tìm cách đặt lại tên cho một router. Em muốn kiểm điều kiện lịch sử phản hồi chưa hoàn hảo có giá trị quyết định và liệu reputation transfer cụ thể có vượt calibration/conditional action-value baselines. Các vòng hiện tại chưa chứng minh điều đó.”

**Nguồn:** tổng hợp literature; [R49] cho tiền lệ phân biệt complementarity và certified gain.

### Slide 16 — Hệ thống và phần đã hoàn thành (55 giây)

**Đưa lên slide:** data/splits → collectors → reputation/audit → replay/evaluation → prototype; 291 Python files; 308 pass/1 skip; receipt audits.

**Lời nói:** “Hệ thống đã có provenance và nhiều vòng real inference. File đang mở paired_history_modal là CPU replay worker. Em phân biệt completed execution với scientific gate; audit PASS không đồng nghĩa method thắng.”

**Hình:** sơ đồ khối của report chính. Số files chỉ minh họa phạm vi rà soát, không phải contribution metric.

### Slide 17 — Tóm tắt tiến trình: 3 nút thắt đã xác định (60 giây)

**Đưa lên slide:**

| Nhánh | Bằng chứng | Bài học |
|---|---|---|
| ECRT/MMLU-Pro | related+25%noise:+0,02 pp, CI gồm 0 | Calibration không chắc đổi decision |
| AppWorld/DART | Candidate có point gain, chưa qua đủ controls | Cần paired/gold-only/adaptive baselines |
| FinQA/TAT-QA repairs | Strong PoT/self-review làm mất headroom | Không học selector trước adequacy/headroom gate |

**Lời nói:** “Đây là ba phát hiện dẫn tới cách thiết kế tiếp, không phải ba benchmark đã thắng.”

### Slide 18 — DART và proxy: vì sao gate vẫn FAIL? (75 giây)

**Đưa lên slide:** AppWorld 10% gold: CFJudgeFactor 74,15/168; PairedGlobal 71,95; Uniform 69,70; PairedSH 71,90. CI so PairedSH [−0,86;+3,42] pp.

**Lời nói:** “Ứng viên có điểm trung bình cao hơn, nhưng chưa tách biệt trước tất cả controls. MATH 500 có feedback signal tốt nhưng RawJudge đã bằng oracle 46/48. FinQA có headroom nhưng judge pair variance ratio 1,0454. Cần cả signal lẫn decision headroom.”

**Nguồn:** paired-history/halving/pilot assessments. Giữ phần FinQA/MATH ở ghi chú nếu thiếu thời gian; không để slide quá nhiều bảng.

### Slide 19 — Vòng 3: scoped repair 144 calls trên 24 TAT-QA contexts (70 giây)

**Đưa lên slide:** Plain 19; KEEP 15; E 15; O 16; EO 15; Self 2(bound)15. Scoped oracle 16<Plain 19, gate FAIL.

**Lời nói:** “Các scope đã được thu thật và acceptance không dùng gold. Nhưng constant contract và receiver logic làm solver yếu, oracle scoped cũng thấp hơn baseline. Không có lý do fit một reputation selector lên bank này.”

**Hình:** bar chart đúng/24, cùng trục 0–24. Chú thích rõ TRAIN development, primary official evaluator; không trộn hậu kiểm.

### Slide 20 — Đối chứng bổ sung 120 calls: best fixed=oracle union (70 giây)

**Đưa lên slide:** Qwen direct/self 1/self 2=19/20/20; Gemma=16/16/16; oracle union 20; no history learner.264 new calls,24 contexts.

**Lời nói:** “Đợt unrestricted/cross-family là post-hoc adequacy control. Nó cho thấy baseline mạnh và thiếu complementary headroom trong bank này. Hậu kiểm metadata làm Gemma 18 nhưng union vẫn 20; không đổi primary scores. Chưa có human adjudication cho 4 semantic flags.”

**Nguồn:** cycle 03 và recheck 27/10. Không mô tả 264 calls là 264 independent tasks.

### Slide 21 — Phép thử tiếp theo và điều kiện dừng (80 giây)

**Đưa lên slide:** candidate: basic-test feedback vs extended-test audit; 32 MBPP+tasks đã chuẩn bị; 0 calls/0 executions; preflight → pilot → headroom gate → method → confirmation.

**Lời nói:** “Em đang xem một setting có feedback structure rõ hơn. Basic fail xác nhận full fail; basic pass chưa xác nhận full pass. Baseline phải audit trong nhóm pass để tránh lãng phí nhãn vào known failures. Đây chưa là method mới; SaveRouter, active inference và conditional learners là comparators quan trọng.”

**Nguồn:** decision 20/10; [R37,R42–R48]. Nếu Thầy yêu cầu giữ tài chính, trình bày như một domain kiểm phương pháp được đề xuất, không thông báo đã đổi đề tài.

### Slide 22 — Điều cần chốt với Thầy (50 giây)

**Đưa lên slide:** domain chính; contribution criterion; confirmation scope/budget.

**Lời nói:** “Em xin thống nhất phạm vi ứng dụng cuối, tiêu chí contribution có thể bảo vệ và mức xác nhận thực nghiệm phù hợp. Em sẽ giữ các kết quả âm và chỉ mở rộng khi pilot đạt điều kiện đã khóa.”

**Kết thúc:** nêu một deliverable kế tiếp cụ thể, ví dụ “protocol và preflight có thể kiểm tra”, không hứa chắc method sẽ thắng hoặc hứa thời hạn chưa thống nhất.

## 3. Nếu chỉ được 12–15 phút

Giữ slides 1–5; gộp 6–7; gộp 8–10; giữ 11–12; gộp 13–15; gộp 16–18; giữ 19–22. Tổng khoảng 14 slides. Đưa chi tiết lịch sử MMLU/thinking/AppWorld versions, formulas và đủ 49 references vào backup.

Tối thiểu phải giữ ba thông tin: literature làm thay đổi gap thế nào; latest results chính xác; điều kiện cần đạt để chốt method. Đừng cắt phần giới hạn rồi để người nghe tưởng pilot là final evaluation.

## 4. Các bảng/hình nên chuẩn bị

1. **Taxonomy map:**7 nhánh; chọn 1–3 paper/nhánh. Mỗi nhánh một câu hệ quả.
2. **Comparison matrix:**5–6 hàng gần nhất, không dùng dấu× để kết luận một bài hoàn toàn không có tính năng khi chỉ mới đọc abstract.
3. **Source → decision diagram:**gold/evaluator được vẽ riêng với solver-visible inputs.
4. **DART bar/CI plot:**primary 10% gold; phân biệt means qua seeds và task counts. Đơn vị pp cho differences.
5. **TAT-QA primary bars:**scoped và cross-family ở hai panels; trục 0–24; oracle đường nét đứt và chữ “diagnostic”.
6. **Next-study gate diagram:**preflight, pilot, STOP/GO, freeze, confirmation.

Không dùng đường nối kiểu “5% → 83%” cho FinQA pilot và TAT-QA: khácdataset/model/contract/sample/metric, không phải learning curve hoặc cùng một pipeline improvement.

## 5. Những câu Thầy có thể hỏi và câu trả lời nên chuẩn bị

### 1. “Em làm gì khác với việc gọi nhiều LLM rồi vote?”

“Đề tài đánh giá lịch sử như một nguồn bằng chứng có sai số và có giới hạn chuyển giao, rồi kiểm nó có giúp quyết định tốt hơn không. Vote là một baseline. Hiện em đã triển khai và thử nhiều candidate, nhưng chưa xác nhận explicit reputation structure tạo lợi ích riêng trước các controls mạnh.”

### 2. “Điểm mới của em là gì?”

“Em chưa chốt novelty claim vì conditional trust, proxy audit và repair memory đã có tiền lệ trực tiếp. Candidate của em là một cơ chế reliability/transfer/audit cụ thể trong setting partial feedback, chỉ nhận làm đóng góp nếu vượt learner cùng thông tin trên task mới. Bằng chứng hiện tại đang giúp thu hẹp cơ chế và loại các lợi ích do interface.”

Không trả lời “lần đầu kết hợp” nếu chưa có chứng minh và final related-work search.

### 3. “Vậy hiện tại đã có kết quả gì?”

“Em có hệ thống và artifacts thực nghiệm có kiểm chứng; ECRT chưa superiority; DART có development point gains chưa qua controls; cycle 3 có 264 responses và các adequacy/headroom gates đều FAIL. Kết quả mới xác định rõ tác động contract/acceptance và thiếu headroom trong bank hiện tại. Chưa có final confirmation cho method.”

### 4. “Sao không dùng một model mạnh tự sửa?”

“Đó chính là baseline bắt buộc. Ở cycle 3, Qwen self 1 đạt 20/24 và union cũng 20, nên em không tiếp tục fit selector lên bank này. Method đa agent phải hơn baseline đó theo accuracy/cost đã khóa, không chỉ hơn một solver bị ép schema.”

### 5. “Chỉ cần thêm dữ liệu history là được không?”

“Thêm history giúp giảm uncertainty nếu có signal phù hợp. Nó không tạo thêm correct output trong bank oracle bằng best fixed. Trước hết cần chứng minh complementarity có thể dự đoán được bằng thông tin deployment, rồi mới đầu tư history và power.”

### 6. “Tại sao Brier giảm mà accuracy không tăng?”

“Brier đo quality của xác suất. Nếu calibration đổi xác suất nhưng giữ ranking/threshold actions, final decisions không đổi. Hoặc nó dự báo độ khó chung thay vì chênh lệch A–B. Em đo paired residual differences và final rescue/harm để kiểm bước chuyển đó.”

### 7. “Oracle 20/24 là kết quả router của em à?”

“Không. Oracle xem correctness trước khi chọn nên là ceiling diagnostic. Router thật chỉ được dùng thông tin có trước quyết định. Kết quả 20/24 ở cycle 3 là strong fixed workflow; chưa có learner reputation mới được fit trong cycle 3.”

### 8. “264 calls có đủ để kết luận không?”

“264 responses nằm trên 24 contexts, không phải 264 independent tasks. Nó đủ làm pilot cơ chế theo gate đã đặt, chưa đủ xác nhận generalization/non-inferiority. Context cũng chưa chứng minh report-disjoint; final split cần group identity và power plan phù hợp.”

### 9. “AuditPASS có nghĩa method đúng không?”

“AuditPASS xác nhận run/source/prompt/response/execution nhất quán theo protocol. Scientific gate kiểm một giả thuyết về utility và có thểFAIL dù audit PASS. Semantic correctness của annotation lại cần một loại audit khác.”

### 10. “Mã có mock thì các kết quả có giả lập không?”

“Mock provider tồn tại để unit/smoke tests. Các real studies được trình bày có recorded model responses và provenance riêng. Một số bảng simulation cũ đã được loại khỏi bằng chứng method. Replay trên responses thật không phải mock inference, nhưng cũng không phải model calls mới.”

### 11. “Paired history đang là một phương pháp mới à?”

“Trong implementation hiện tại, paired wrapper giữ estimator và thay acquisition/control naming đúng paired masks. Lợi ích cần tách sampling design, structure, judge và residual correction. Kết quả chưa qua đầy đủ controls; nó chưa là validated new-method claim.”

### 12. “Sao không tăng model/GPU?”

“Model/capacity là một biến đã được kiểm qua backbone/modern controls. Lớn hơn có thể giúp solver nhưng chưa tự làm reputation có ích. Ở các pool mà mạnh nhất trùng oracle, thêm một learner không có thêm decision headroom. Cần thay cấu hình dựa trên một protocol có lý do và so actual cost, truncation.”

### 13. “Chạy được code và source token có thật thì sao còn sai?”

“Checker đó xác nhận cú pháp/phép tính và sự tồn tại của số. Nó chưa biết số đó đúng metric, kỳ, gross/net, dấu hay unit được hỏi. Case FRT đã có phép trừ đúng với cặp số sai kỳ. Do đó execution/source validity là features, chưa là gold.”

### 14. “Em nói nhãn dữ liệu sai phải không?”

“Em chỉ có các semantic/annotation flags ở một số case, chưa có independent human adjudication. Em giữ official scores và tách flag khỏi scoring. Không tự relabel để tăng điểm method.”

### 15. “Các sửa parser làm điểm tăng thì có phải tiến bộ không?”

“Có giá trị engineering, nhưng cần cấp đồng đều cho baselines và khóa lại cho study sau. Em giữ strict/format/readout scores riêng; không dùng chúng làm reputation gain. Không giả vờ output vòng sau được sinh từ context acceptance mới nếu thực tế chưa chạy lại.”

### 16. “Em có tiết kiệm chi phí không?”

“Chưa có claim tiết kiệm được xác nhận cho method cuối. Em phân biệt collection, serving replay và billing. Eval seconds/tokens là proxies; muốn claim kinh tế cần ledger đầy đủ và payback tương ứng. Một policy A → B phải charge cả hai calls.”

### 17. “Vì sao chuyển xem MBPP+?”

“Đó là candidate setting cho cùng câu hỏi imperfect-feedback reputation. Nested tests tạo quan hệ basic-fail⇒full-fail, nhưng basic-pass có thể false positive. Em chưa đổi đề tài chính thức và chưa có model result ở setting này; domain cuối cần thống nhất với Thầy.”

### 18. “Test đầy đủ rẻ, sao cần audit?”

“Nếu rẻ và có sẵn ở deployment, always-full-test là control phải xét. Giới hạn label revelation chỉ là một thiết kế nghiên cứu, không tự là tiền tiết kiệm thực. Em phải chứng minh chi phí/visibility phù hợp, không gán scarcity giả cho test CPU.”

### 19. “Gọi reputation khác gì action-value learning?”

“Có thể không khác nếu cùng features/labels và estimator tương đương. Repo đã có ghi chú ridge decomposition để tránh điều đó. Contribution chỉ có nếu cấu trúc transfer, uncertainty hoặc regularization thêm ích lợi trước contextual action-value learner được cấp cùng dữ liệu.”

### 20. “Còn gì để hoàn thành khóa luận?”

“Cần chốt một setting có signal/headroom, khóa một candidate/controls/budget, đánh giá trên task mới với power phù hợp, thực hiện ablations và hoàn thiện bản viết/reproducibility. Prototype hiện là integration evidence, chưa thay được phần scientific confirmation.”

### 21. “Nếu phương pháp tiếp theo vẫn không thắng?”

“Em sẽ giữ kết quả và xác định điều kiện thất bại, không tune trên final set. Em cần thống nhất với Thầy liệu điều chỉnh phạm vi/contribution có phù hợp chuẩn khóa luận hay cần một design mới. Em không xem nhiều kết quả âm tự động thay được một contribution đã được yêu cầu.”

### 22. “Em đã đọc/tái lập bao nhiêu?”

“Danh mục có 49 nguồn gốc được đối chiếu để tổng hợp; các bài gần nhất được đọc thêm method/limitations. Đây không phải 49 full reproductions. Phía source em lập inventory 291 Python files, kiểm cú pháp/hash, đọc sâu critical paths, chạy 308 tests và chạy lại cycle 3 receipt/execution/official scoring. Phạm vi kiểm chứng được ghi rõ.”

## 6. Checklist trước buổi báo cáo

- Điền đúng tên/mã đề tài, GVHD, thành viên và mốc báo cáo theo hồ sơ chính thức.
- Mỗi slide literature có tên paper, năm/status và 1 câu hệ quả cho thiết kế.
- Ghi “development/TRAIN sample” trên các biểu đồ pilot; không ghi “official test accuracy”.
- Giữ cùng mẫu số, đơn vị và evaluator trong một bảng so sánh.
- DART ghi mean successes/168 qua seeds; differences ghi điểm phần trăm.
- Cycle 3 ghi 264 new responses/24 contexts; không double-count 24 cached directs.
- Không trộn primary results với post-hoc parser/readout diagnostics.
- Có backup cho paired CI, oracle definition, cost ledger và current source flow.
- Chuẩn bị demo trace đã có để minh họa; live demo nếu tự chạy sẽ tạo inference mới và không là final evaluation.
- Kết thúc bằng deliverable/gate kế tiếp và nội dung cần Thầy định hướng.
