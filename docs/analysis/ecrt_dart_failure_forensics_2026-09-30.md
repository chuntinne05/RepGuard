# Vì sao ECRT và hướng DART hiện tại chưa tạo được lợi ích: điều tra thuật toán và dữ liệu

**Ngày:** 30/09/2026. **Phạm vi:** các suy luận thật đã lưu trong Week 3–5 và pool 420 câu MMLU-Pro. Đây là phân tích nguyên nhân trên dữ liệu phát triển/Week 3 đã xem; không phải một thử nghiệm xác nhận mới. Trong trao đổi, “ERCT” được hiểu là **ECRT** trong mã nguồn.

## 1. Kết luận đúng về trạng thái

1. **ECRT đã được đánh giá ở Week 3 với cả bốn model `think=false`**; nó chưa được chạy lại với pool thinking. Trên `related + noisy_025`, chênh team accuracy so với FixedBorrow chỉ **+0,02 điểm phần trăm**, CI 95% **[−0,04; +0,10] điểm**. Brier chênh **+0,0088** (số dương là xấu hơn), CI **[−0,0003; +0,0181]**. Chưa có bằng chứng lợi ích cuối cùng ổn định. Dưới false positive attack, ECRT cải thiện Brier nhưng team accuracy hầu như giữ nguyên.
2. **DART chưa có implementation và đánh giá hoàn chỉnh trên sealed holdout.** Điều không qua là *Gate 0* của pool/router thử nghiệm: trên 420 câu đã xem, chưa có đủ hai specialist và tín hiệu dự báo trước đáp án để route thắng solver mạnh. Gọi đây là “DART đã thất bại khi bật thinking” là không chính xác.
3. Thinking thật sự giúp giải bài: Qwen3 8B direct **200/420**, cùng model thinking **280/420** trên screen train; ở dev độc lập direct **137/280**, thinking **203/280**. Vì thế không thể chuyển kết luận Week 3 direct sang pool thinking mà không chạy đánh giá mới.

## 2. Bằng chứng truy vết ECRT

Week 3 có 18.064 câu trả lời thật, bốn model trên 14 môn. Grid dùng một môn lịch sử làm nguồn, một môn test làm đích, ba seed corruption. Mỗi môn nguồn có 100 câu history × 4 agent và 50 câu calibration × 4 agent. `StudyTransferEstimator` gán cùng môn `τ=1`, cùng cụm `τ=0,5`, khác cụm `τ=0`. Toàn bộ các câu test trong một môn đích cùng nhận **bốn trọng số reputation cố định theo agent**; `choose_answer` cộng trọng số theo chữ cái đáp án. Không có độ tự tin theo câu, nội dung lập luận, hoặc xác minh câu đang giải.

ECRT dùng

\[
\hat p(F)=P(z=1\mid F),\qquad
\mu_i={1+\tau\sum_{j=1}^{n}\hat p(F_{ij})\over 2+\tau n}.
\]

`FixedBorrow` thay `\hat p(F)` bằng chính feedback nhị phân `F`. Vì calibration chung cho bốn agent trong một môn nguồn, đặt `p_+=P(z=1|F=1)` và `p_-=P(z=1|F=0)` thì

\[
\hat p(F)=p_-+(p_+-p_-)F.
\]

Ở đây mọi agent có cùng `n` và `τ`. Do đó, khi `p_+>p_-`, hiệu chuẩn **không thể đổi thứ hạng agent**; nó chỉ co giãn cách biệt điểm. Khi feedback oracle, `p_+=1`, `p_-=0`, posterior mean ECRT **bằng FixedBorrow về mặt đại số**. Đây là giới hạn thiết kế trực tiếp, không phải thiếu dữ liệu.

### Kiểm tra trên toàn bộ grid đã lưu

Các đếm dưới đây ghép từng ô `target × source × seed`; đơn vị này chỉ để kiểm tra cơ chế, **không dùng làm số mẫu độc lập cho CI**. Trong 546 ô mỗi chế độ nhiễu, 417 ô `unrelated` có `τ=0`, nên ECRT và FixedBorrow đều trả prior 0,5 và kết quả giống hệt. Chỉ 129 ô `same/related` thật sự dùng history.

| Chế độ feedback | Ô `same/related` | Thứ hạng bốn agent giống FixedBorrow | So cặp agent bị đảo thứ hạng | Ô team ECRT tốt hơn / Fixed tốt hơn / bằng |
|---|---:|---:|---:|---:|
| Oracle | 129 | 129 | 0/774 | 9 / 9 / 111 |
| Flip 25% | 129 | 129 | 0/774 | 1 / 4 / 124 |
| Flip 50% | 129 | 33 | 542/774 | 49 / 40 / 40 |
| False positive 40% | 129 | 129 | 0/774 | 0 / 3 / 126 |

Ở 50% noise, calibration ước lượng `sensitivity + specificity < 1` trong **30/42** tổ hợp môn nguồn × seed. Khi đó `p_+<p_-`: tín hiệu feedback dương được diễn giải là **ít khả năng đúng hơn feedback âm**, nên thứ hạng có thể đảo. Đây là hệ quả trực tiếp của plug-in Bayes ở giới hạn feedback ngẫu nhiên, không phải phát hiện một tín hiệu phản hướng đáng tin. Trong cùng điều kiện, ECRT cải thiện Brier ở `same` khoảng **0,0192** so FixedBorrow nhưng chênh accuracy của các ô same chỉ khoảng **−0,055 điểm** và related **+0,42 điểm** với CI 95% **[−0,38; +1,21] điểm**. Calibration tốt hơn không đủ để kết luận policy tốt hơn.

Ở false positive 40%, attack trong mã áp dụng **cho mọi agent có câu sai**, không chọn riêng agent/skill. ECRT hiệu chuẩn được sai lệch phổ biến này, làm Brier related thấp hơn FixedBorrow **0,0429** (CI 95% [−0,0722; −0,0115]), nhưng thứ hạng agent giữ nguyên ở 129/129 ô tích cực và team accuracy khác rất ít. Kết quả này **không chứng minh** chống poisoning có mục tiêu. `p_+` giảm nhưng có cùng tác dụng gần đơn điệu lên cả bốn agent; khi vote chỉ dùng thứ hạng và tổng trọng số, câu được chọn ít đổi.

Với real candidate-conditioned judge feedback trên test Week 3 dùng lại: mean absolute reputation shift khoảng **0,105/0,103** ở hai fold; đáp án cuối chỉ khác **37/2416** và **41/2416** câu. ECRT-only đúng lần lượt 8 và 9 câu; Fixed-only đúng 4 và 8 câu. Hai fold dùng **cùng test ID**, không phải hai xác nhận độc lập. Một pilot decision guard học threshold trên dev đã chọn threshold 0,8 cho ECRT weighted vote, dẫn đến **0 lần switch** trên 2416 test câu và đúng bằng baseline Qwen3 8B direct **1154/2416**. Đây là diagnostic, không phải thử nghiệm DART.

### Các điểm yếu ở mức code và mức thiết kế

- `FeedbackReliabilityEstimator.calibrate` tính một sensitivity, specificity và correctness prior **gộp toàn bộ agent** theo môn nguồn; không có mô hình `agent × skill × source`. Nếu một agent bị poisoning riêng, ước lượng chung có thể làm loãng tín hiệu. Nhiễu 50% còn cho thấy không có guard về độ chắc chắn của `sensitivity + specificity` trước khi đảo dấu evidence.
- `infer_p_correct` dùng **chỉ một bit feedback** và một prior gộp. Nó không thể phân biệt hai câu cùng feedback dương nhưng độ khó, chất lượng lý giải hoặc người chấm khác nhau. `StudyTransferEstimator` chỉ dựa vào cụm môn tĩnh; mọi history episode trong cặp môn dùng cùng `τ`. Đây không phải transfer theo câu hay skill thực đo.
- `evidence_mass=1` cho mọi feedback quan sát, kể cả feedback gần ngẫu nhiên. `BetaParams.update` cộng soft label như fractional successes với cùng tổng pseudo-count; `lower_credible_bound` không truyền sai số ước lượng reliability, độ phụ thuộc giữa episode, hay entropy latent correctness. Do đó bound có thể quá tự tin. Bound đang dùng xấp xỉ chuẩn `μ−1,645√(μ(1−μ)/(α+β))`, không phải phân vị Beta chính xác.
- `choose_answer` cộng **reputation toàn cục của agent cho từng chữ cái**. Điểm Brier là xác suất agent trả lời đúng nói chung; nó không phải `P(đáp án A đúng | chính câu này, tập câu trả lời)`. Việc dùng nó làm vote weight không tối ưu hóa trực tiếp expected decision value. Khi các model yếu đồng ý với cùng đáp án sai, vote có thể át model mạnh.
- Mã `ECRTReputation.score` lưu `uncertainty_mode` nhưng không đọc nó; trong Week 3, `ECRT-noUncertainty` chỉ được tạo khác **ở hàm `choose_answer`**, dùng mean thay lower bound. `oracle_ft` trong factory hiện dùng cùng `_compute_tau` như `oracle_f`, nên tên “oracle transfer” không tương ứng một oracle transfer riêng. Đây là vấn đề QA/ablation cần sửa trước khi claim đầy đủ, nhưng `oracle_ft` không có trong grid Week 3 và **không phải nguyên nhân của số liệu chính**.

## 3. Vì sao pool thinking không cứu được DART theo cấu hình hiện tại

Trên 420 câu cùng ID, Qwen3 8B thinking đúng **280**, Qwen3 14B direct **226**, Qwen3 8B direct **200**, Gemma2 direct **195**, Llama3 direct **158**. Trong 140 câu thinking sai, ít nhất một direct model đúng ở **64** câu; oracle chọn đúng model theo gold sẽ đạt **344/420**. Nhưng không có oracle đó ở inference. Subject router cross-fit 5 fold chọn **274/420**, trong khi luôn thinking **280/420**, dù giảm khoảng **26,05% output token**. Five-model vote chỉ **248/420**; three-model vote **267/420**. Một fallback đơn giản theo dấu hiệu quan sát được là thinking JSON invalid (24/420) + Qwen14 direct cứu **6** câu, replay thành **286/420**; đây là tín hiệu vận hành trên tập đã xem, chưa phải hiệu quả xác nhận.

Cơ chế mất điểm hiện ra ở **116 câu thinking trả lời hợp lệ nhưng khác phiếu đa số duy nhất của bốn direct model**: thinking đúng **66**, phiếu direct đúng **22**, còn 28 câu cả hai sai. Cụ thể khi direct đồng ý 2, 3, 4 phiếu, thinking đúng lần lượt 34/55, 25/47, 7/14, còn phe direct đúng 6/55, 12/47, 4/14. Cộng vote phổ thông trong nhóm này chủ yếu thay đáp án tốt bằng đáp án xấu. Đây là dữ liệu quan sát của pool hiện tại, không phải định luật của mọi ensemble.

Tại sao history theo **môn** chưa route được 64 ca cứu oracle? Sự bổ trợ đa phần là **theo câu**; nhãn môn không cho biết câu nào Qwen thinking sẽ sai và agent nào sẽ đúng. Chỉ Engineering có Qwen14 direct hơn thinking 18 so 13 trên 30 câu, discordant 8 so 3; Law/Psychology hơn chỉ một câu. Mẫu 30/môn quá nhỏ để khẳng định hai specialist ổn định. Pool còn bất cân xứng: một solver mạnh dùng `think=true`, max 8192 token; bốn solver khác direct, max 64 token. Kết luận là các **policy với budget cụ thể** khác nhau, không tách riêng tác dụng của `think` khỏi model/budget trong so sánh pool. Qwen8 direct/thinking là cặp cùng model nên có bằng chứng trực tiếp rằng policy thinking tăng accuracy.

## 4. Vì sao các đối chứng thắng ở những chỗ cụ thể

| Đối chứng | Lý do có thể thắng | Bằng chứng / giới hạn |
|---|---|---|
| FixedBorrow | Dùng cùng `τ` và history; không thêm sai số ước lượng từ calibration. Ở oracle posterior mean bằng ECRT. | Thắng ECRT nhẹ ở một số ô 25% noise, nhưng **không thắng mọi điều kiện**; ECRT tốt hơn về Brier ở false positive attack. |
| GlobalBeta | Dùng toàn bộ history không chiết khấu; khi chuyên môn agent chuyển được giữa các môn, evidence nhiều hơn. | Ở unrelated, ECRT luôn prior 0,5 còn GlobalBeta vẫn dùng history; GlobalBeta related/other không phải mặc nhiên tốt mọi cell. |
| Qwen3 8B thinking | Tăng năng lực giải từng câu bằng nhiều bước suy luận; reputation chỉ sắp xếp đáp án có sẵn. | 280/420 so Qwen8 direct 200/420, xác nhận độc lập trên dev 203/280 so 137/280; tốn rất nhiều token/time và có truncation. [Bài gốc MMLU-Pro](https://arxiv.org/abs/2406.01574) cũng nhận thấy chain-of-thought giúp trên benchmark này. |
| Fallback invalid | Dùng tín hiệu rõ ràng trước gold: không có đáp án hợp lệ. | 6 ca cứu trên 24 invalid, replay 286/420; chưa xác nhận trên holdout. |

Không phải “mọi phương pháp khác đều thắng”: uniform và đa số thường kém; ECRT có ích cho calibration trong một số corruption. Vấn đề là **endpoint chính của bài phương pháp là quyết định đúng hơn ở budget công bằng**, và bằng chứng đó hiện chưa xuất hiện.

## 5. Phân biệt nguyên nhân đã chứng minh và giả thuyết

**Chứng minh/quan sát trực tiếp từ code và ledger:** oracle ECRT mean bằng FixedBorrow; `τ=0` làm 417/546 ô mỗi regime bằng nhau; 30/42 calibration 50% noise phản hướng; chính sách dùng reputation cố định theo môn; rất ít final-answer switches trong judge pilot; thinking mạnh hơn direct cùng model; vote pool yếu hơn always-thinking.

**Giả thuyết hợp lý cần thí nghiệm riêng:** đầu tư audit `agent × skill`, confidence theo câu, mô hình tương quan giữa agent, transfer học từ dữ liệu hoặc decision-aware selection có thể biến oracle headroom thành gain thật. Chưa có bằng chứng hiện tại rằng phiên bản đó chắc chắn hoạt động. Muốn kiểm tra nhân quả, cần giữ nguyên pool/cost và thay từng thành phần trên train/dev mới, khóa policy, sau đó đánh giá **một lần** trên holdout chưa xem cùng benchmark thứ hai.

## 6. Việc tiếp theo có giá trị cao nhất

1. Sửa và kiểm thử ablation (`oracle_ft`, `uncertainty_mode`), rồi làm chẩn đoán **decision sensitivity**: score thay bao nhiêu, rank thay không, số quyết định thay, rescue/harm và cost mỗi lần thay. Thêm guard cho feedback gần random và uncertainty của reliability; kiểm tra trên train/dev, không tuning vào test cũ.
2. Nếu muốn DART là bài phương pháp, xây pool có **hai vai trò bổ trợ thật** và feedback có hậu quả thực tế (ví dụ agent/tool workflow), rồi chạy pilot nhỏ có targeted poison theo agent/skill, audit budget bằng nhau và đối chứng strongest-solver/FixedBorrow/router không reputation. Gate là gain quyết định ở cùng cost trên dev, không phải Brier đẹp hay oracle headroom.
3. Giữ 420 sealed holdout chưa xem. Chỉ mở sau khi có một policy DART và so sánh đã khóa. Nếu Gate 0/1 tiếp tục fail, HistRepEval + phát hiện giới hạn của reputation trong quyết định là hướng bài có chứng cứ hơn, nhưng vẫn cần benchmark thứ hai và baseline mạnh để thành bài A*.

**Nguồn tái lập:** chạy `.venv/bin/python analyze_failure_mechanisms.py` để kiểm lại đếm rank, calibration và disagreement từ ledger đã kiểm tra; script ghi `results/real_next_study_v1/failure_forensics.json`. Mã và dữ liệu nguồn: `analyze_real_week3.py`, `src/repguard/reputation/ecrt.py`, `src/repguard/reputation/baselines.py`, `src/repguard/reputation/feedback.py`, `results/real_week3_json_v1/analysis/qt_grid_results.csv`, `statistical_analysis.json`, `results/real_next_study_v1/decision_sensitivity.json`, `decision_guard_pilot.json`, `results/real_pool_overlap_v1/analysis_full.json`, `crossfit_gate.json`. Raw `results/` được Git ignore; khi báo cáo công khai cần xuất provenance, checksum và script tính lại, không chỉ bảng tổng hợp.
