# FinQA judge pilot: kết quả và nguyên nhân gate thất bại

## Kết luận đúng phạm vi

Run `0fad63edd346eb0591fd99e1` kết thúc trên Modal lúc 13:43:29 UTC ngày
06/10/2026. Có **960/960** judgment Qwen3-14B thật trên **48 câu FinQA
development ×20 archived model executions**, đúng **960 attempt**, không retry
hoặc fallback do lỗi request. Local đã tải và xác minh checksum của cả 960
case, đối chiếu model/JSON/usage rồi tính lại đúng kết quả cloud. Không có
solver call mới. Gold của đúng 960 cell được evaluator đọc *sau* khi hoàn
thành judge; 938 câu FinQA eligible khác ngoài 200 câu headroom development
vẫn chưa được run này đọc score.

**Operational gate PASS, expansion screening FAIL.** Judgment hợp lệ
**100,00%** và đáp án boxed hoàn chỉnh **889/960 =92,60%**, vượt hai ngưỡng
95% và 90%. Tuy nhiên, tỷ số phương sai chênh lệch residual giữa model là
**1,045407**, CI95 **[1,019379; 1,073530]**: *tăng* khoảng 4,54% thay vì
giảm ít nhất 10% như protocol yêu cầu. Không được đổi gate hoặc chọn lại
candidate sau khi xem kết quả.

| Chỉ số trên 48 câu development | Giá trị |
|---|---:|
| Brier judge thô | 0,368354 |
| Brier judge sau cross-fit 4 folds | 0,208561 |
| Brier gold-only cross-fit | 0,237974 |
| Brier gain của judge so với gold-only | +0,029413; CI95 [+0,001827; +0,056282] |
| Pair residual variance ratio | 1,045407; CI95 [1,019379; 1,073530] |
| Recorded input/output tokens | 1.299.117 / 11.240 |

Tổng 632,51 giây `total_duration` trong response là thời gian suy luận cộng
của các request đã ghi, **không phải** GPU wall time hoặc hóa đơn Modal. CI là
bootstrap 48 câu với fitted predictions giữ nguyên, không tính lại fit và
không phải kiểm chứng độc lập. Brier tốt hơn chỉ chứng minh judge có thông tin
cho *dự báo đúng/sai chung* trên pool này; gate kiểm tra thông tin để *phân
biệt model trên cùng câu* và đã thất bại.

## Lý do định lượng: judge học độ khó của câu, rất yếu về khác biệt giữa model

Outcome đúng trung bình là **57,08%** nhưng xác suất judge thô chỉ trung bình
**36,91%**. Judge trả đúng 0 cho **591/960** và đúng 1 cho **290/960** case;
chỉ có 9 giá trị xác suất phân biệt trong toàn pilot. Trong đó có **274** case
đúng dù judge đặt xác suất ≤0,1, và **74** case sai dù judge đặt ≥0,9.
Ngưỡng 0,5 của judge thô phân loại đúng **61,77%** cell; đây không phải mức
chính xác chọn model. Brier thô 0,368 phản ánh độ tự tin sai lớn.

Tương quan mô tả giữa *trung bình judge của mỗi câu* và *tỷ lệ model đúng trên
câu đó* là **+0,476**. Nhưng sau khi trừ trung bình từng câu, tương quan giữa
judge và kết quả của các model trên chính câu đó chỉ **+0,043**. Trung bình
theo model thậm chí tương quan **−0,615** với accuracy của model trên 48 câu;
ngoại lệ MiMo đóng góp mạnh vào dấu âm này, và bỏ MiMo tương quan còn +0,101.
Các tương quan là hậu kiểm trên 48 câu, không là tham số population được
ước lượng chính xác.

Một ablation hậu kiểm, giữ nguyên folds/penalty và chỉ đổi features, làm rõ
điểm này:

| Features cross-fit | Brier | Tỷ số pair residual variance |
|---|---:|---:|
| Gold-only model identity | 0,237974 | 1,037100 |
| Model identity + trung bình judge của câu | **0,207415** | 1,036293 |
| Model identity + judge của cell | 0,212091 | 1,065866 |
| Full features đã khóa | 0,208561 | 1,045407 |

Chỉ dùng độ khó chung của câu đã tái tạo phần lớn cải thiện Brier nhưng gần
như không giúp pair contrast. Thêm score riêng của cell làm tỷ số pair xấu
hơn. Đây là chẩn đoán hậu kiểm, **không phải** một candidate mới đã qua gate.
Theo đẳng thức phương sai trên 190 cặp model, tổng phương sai difference của
gold là **41,8794**, của difference dự đoán là **0,7947**, nhưng tổng covariance
giữa hai difference là **−0,5535**. Do đó trừ dự đoán khỏi gold *tăng* phương
sai residual; vấn đề trực tiếp là dự đoán chênh lệch giữa model không đi cùng
chiều với chênh lệch thật trên các câu.

## Lỗi trích đáp án và giới hạn của cách sửa đơn giản

Trong 71 output phải dùng `tail_fallback`, MiMo chiếm **39**. Chỉ **1/39**
MiMo fallback được archive evaluator chấm đúng, nhưng judge cho xác suất
trung bình **0,614**; **15** case sai trong nhóm này còn bị chấm ≥0,9. Trên
toàn bộ 48 câu, MiMo chỉ đúng **7/48**, nhưng trung bình judge thô của MiMo cao
nhất 20 model. Nếu chọn model bằng mean judge thô trên chính 48 câu này, nó
chọn MiMo; best fixed *hậu kiểm* trên 48 câu là Intern-S1-mini **34/48** và
oracle per-question *hậu kiểm* là **42/48**. Đây chỉ là minh họa cấu trúc lỗi,
không phải evaluation của một router deployable. Không nhầm các số này với
best fixed 74% / oracle 88,5% trên **200 câu headroom development**.

Preflight gold-blind bổ sung đã đọc đúng 960 record từ cùng pinned archive:
`prediction` có nội dung ở **888/960**, `raw_output` chứa marker boxed ở
**896/960**, nhưng **0** record thiếu marker boxed trong raw output lại có
`prediction`. MiMo chỉ có **9/48** prediction. Vì vậy đổi sang trường
`prediction` không sửa được nhóm output không có final-answer marker. Bỏ
toàn bộ MiMo khỏi tỷ số pair hậu kiểm vẫn được **1,045214** trên 171 cặp;
fallback của MiMo là lỗi rõ ràng, **không phải** lời giải thích đầy đủ cho
gate FAIL. Có thể cần judge hiểu lời giải dài/không có boxed final, hoặc
phương pháp đánh giá khác, nhưng phải kiểm tra trên development mới.

## Quyết định tiếp theo

1. **Dừng mở rộng judge v1.** Không mua thêm judgment với prompt/extractor
   hiện tại chỉ để làm CI dương; không xem Brier PASS là chứng minh DART.
2. Thiết kế phiên bản mới để đánh giá *chênh lệch đúng/sai giữa các model trên
   cùng câu*, thay vì tối ưu Brier pooled. Hai can thiệp đáng kiểm tra, dưới
   protocol mới và dữ liệu development mới, là judge so sánh hai candidate
   answer có đảo thứ tự và judge có reasoning/kiểm tra số học. Phải đếm đủ
   token, latency và chi phí; không giả định thinking sẽ tự chữa lỗi.
3. Sau khi một judge mới chứng minh pair signal trên development, khóa replay
   gold thưa với RawJudge, gold-only, paired/SH, correction có propensity và
   baseline từ [Ao et al.](https://arxiv.org/abs/2601.21471). Chỉ kết luận
   phương pháp khi vượt đối chứng cùng budget và sau đó có evaluation độc lập.
   [PROBE](https://arxiv.org/abs/2607.06879) là comparator proxy/BAI liên
   quan, nhưng định lý Gaussian của họ không tự áp dụng cho binary FinQA.
4. Nếu pair signal vẫn yếu hoặc chi phí judge lớn hơn lợi ích gold, mục tiêu
   phương pháp phải đổi; HistRepEval là nhánh đo lường có thể tiếp tục nhưng
   phải khác biệt rõ với
   [LLMRouterBench 2026](https://aclanthology.org/2026.findings-acl.1881/).

Không có kết quả hiện nay nào bảo đảm DART vượt baseline hoặc đủ nhận bài A*.
Kết luận có giá trị thực tiễn đã được chứng minh ở đây là: **cải thiện dự báo
độ khó chung không đồng nghĩa cải thiện quyết định chọn model**. Báo cáo
chính, kết quả máy đọc và chẩn đoán tái lập được ở
[assessment](routerbench_finqa_feedback_v1_assessment_2026-10-06.md),
[results JSON](routerbench_finqa_feedback_v1_results_2026-10-06.json) và
[diagnostics JSON](routerbench_finqa_feedback_v1_diagnostics_2026-10-06.json).
