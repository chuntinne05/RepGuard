# Vì sao feedback tốt nhưng ứng viên vẫn chưa thắng?

## Trạng thái và kết luận đúng phạm vi

Run `a4c73220bc917a52700300d0` hoàn tất 240/240 case, 2.400 lựa chọn trên Modal
CPU lúc 08:42:46 ngày 06/10/2026. Đã kiểm chứng 240 checksums và chạy lại toàn bộ
quyết định, acquisition paths, predictions và bootstrap tại local. Không có
solver/judge calls mới; mọi kết quả dựa trên executions và judgments thật đã có.

Gate development FAIL. Tuy nhiên, tại 10% gold CFJudgeRectifier hơn
UniformGlobal **3,44 điểm %**, CI95 **[1,35; 5,83]**, và hơn CFGoldRectifier
**2,92 điểm %**, CI95 **[1,25; 5,42]**. Đây là tín hiệu exploratory cho giá trị
của feedback, chưa đủ trước tất cả controls. Trước PairedGlobal/GoldRidge,
IndependentSH và PairedSH, CI vẫn chứa zero. Point gain trước PairedSH chỉ
0,42 điểm %, dưới practical threshold 1 điểm % đã khóa.

Điều kiện quan trọng hơn cho hướng phương pháp: baseline **RawJudge đạt 46/48
với 0 gold** trên cả ba budgets. Nó vẫn cần chi phí historical judge; 0 gold
không có nghĩa tổng chi phí bằng 0. Ứng viên đạt 40,90 / 44,30 / 45,40 tại
5% / 10% / 20%, đều thấp hơn baseline này. Không chuyển sang ablation điểm cao
hơn rồi gọi đó là DART đã được xác nhận.

## 1. Pool này không có accuracy headroom trên execution đã lưu

Qwen3-8B đúng **46/48**, DeepSeek-R1-0528-Qwen3-8B đúng **45/48**. Oracle chọn
model đúng cho từng câu từ sáu executions cũng chỉ đúng **46/48**. Vì mọi reward
là binary và oracle là rowwise maximum, tổng oracle bằng tổng Qwen3-8B chứng
minh rằng không model khác cứu được câu nào Qwen3-8B sai trong pool 48 câu này.

Do đó không router nào chỉ chọn giữa sáu outputs đã lưu có thể vượt 46/48 trên
pool này. Oracle gap bằng zero là một kết luận xác định về ma trận đã quan sát,
không phải phỏng đoán về khả năng transformer. RawJudge đã chạm bound đó; có
thêm calibration, attention hoặc thuật toán selection phức tạp cũng không tạo
ra một execution đúng vốn không tồn tại.

**Giới hạn:** chưa đọc gold ngoài 48 câu để kết luận tương tự cho toàn bộ 500
MATH500, các dataset khác hoặc solver runs mới. 60,42% câu có model đúng và sai
không đồng nghĩa có complementary capability: các model yếu có thể chỉ đúng
trên tập con các câu model mạnh đã đúng. Cần đo *oracle gap*, không chỉ disagreement.

## 2. Thêm correction làm lựa chọn xấu đi trong ablation đã khóa

Tại 10%, CalibratedJudge và CFJudgeRectifier có cùng audit mask, features,
penalties, inner cross-fit và predictor. Chúng khác ở việc CFJudgeRectifier
thêm residual correction. Bỏ correction tăng kết quả từ **44,30 lên 44,95/48**.
Contrast của candidate trừ CalibratedJudge là **−1,35 điểm %**, CI95
**[−2,40; −0,42]** trong question bootstrap của development replay.

So với RawJudgeRectifier cùng paired audits và cùng correction formula,
candidate thay raw proxy bằng cross-fitted calibrated proxy: **44,30 so với
45,15/48**, chênh lệch **−1,77 điểm %**, CI95 **[−2,71; −0,94]**.
Đây là hai component ablations có kiểm soát trên pool đã chọn, không phải chứng
minh correction hoặc calibration luôn có hại trên dữ liệu khác.

Tại 10%, RawJudge chỉ chọn hai model mạnh nhất; candidate chọn bốn model còn
lại trong **12,5%** các outer-fold/seed decisions. CalibratedJudge chọn nhóm
yếu hơn trong **7,5%**; thêm correction tăng tỷ lệ này 5 điểm %. Full-gold
TRAIN-best agreement của candidate là 66,25%, RawJudge 86,25%, nhưng reference
TRAIN-best không bảo đảm luôn thắng trên held-out và không được learner dùng.

## 3. Vì sao điều này phù hợp với công thức?

Estimator đóng băng là:

```text
score[a] = mean_history(proxy[:, a])
           + sum_audited(y[i,a] - proxy[i,a]) / (n_audited[a] + 2)
```

Mean proxy có nền thông tin dense từ 216 historical judgments mỗi outer fold.
Correction chỉ dựa vào khoảng **3,6–3,8 nhãn/model** tại 10%. Đây là regularized
correction, không phải confidence-certified switch. Một residual từ ít nhãn có
thể đổi thứ hạng dù proxy ban đầu đã chọn model tốt. Cross-fitting ngăn nhãn
của chính câu được dự báo đi vào fit, nhưng không loại bỏ sampling noise hoặc
bảo đảm model sau correction tốt hơn incumbent.

Predictor có 11 coefficients gồm intercept, sáu model indicators, bốn judge
features; regularization giữ phép fit xác định. Inner cross-fit tại 10% chỉ thấy
trung bình 2B/3 = **14,67 paid labels** mỗi fit. Tại 5%, **21/240 inner fits**
không có nhãn và phải trả .5 theo rule đã khóa. Không được sửa bằng cách đưa
gold ngoài budget vào calibration. Những con số này giải thích nguồn rủi ro
ước lượng; ablation ở mục 2 mới đo trực tiếp hậu quả component trong replay.

## 4. Feedback vẫn có giá trị; lỗi dự báo và lỗi quyết định khác nhau

Tại 10%, diagnostic Brier của judge predictor là **0,130096**, so với gold-only
**0,213957**; Brier gain **0,083861**, CI95 **[0,057534; 0,109340]**. Pairwise
residual variance ratio **0,769981**, CI95 **[0,622643; 0,932881]**, tương ứng
giảm khoảng **23,00%** phương sai so với raw outcome differences.

Như vậy tín hiệu feedback không biến mất khi gold thưa. Nhưng Brier tối ưu xác
suất trên mọi task–model cell; quyết định global cần giữ đúng thứ hạng giữa
những model cạnh tranh. Giảm lỗi dự báo trung bình chưa đủ để giữ thứ hạng
và tránh chuyển từ một incumbent đã tốt sang model yếu hơn.

Diagnostic predictor được fit trên B labels và đánh giá sau quyết định; nó
không phải chính history out-of-fold predictor dùng để lựa chọn. Không lấy
Brier diagnostic làm bằng chứng nhân quả rằng selection predictor đã tối ưu.
Các CI condition on fitted learners, chưa refit training/nhóm template hoặc
điều chỉnh lịch sử nghiên cứu thích nghi. Dataset chỉ có 48 câu đã quan sát.

## 5. Thay đổi hướng tiếp theo hợp lý

### Giữ nguyên kết quả và dừng mở rộng v1

Không mua thêm judgment cho cùng phiên bản để cố làm CI dương; không thay
primary budget/candidate/gate. Positive feedback feasibility của pilot trước
vẫn đúng, nhưng chưa trở thành superiority của candidate. Thinking của judge
không phải lời giải cho bound 46/48 của outputs đã cố định. Fresh solver runs
có thể đổi bound, nhưng đó là protocol/cost khác và chưa được chạy ở đây.

### Chuẩn bị dữ liệu bằng prompt-only grouping

Bước dữ liệu tiếp theo là exact/near-template grouping trên prompt của pool
common 500 câu, không đọc gold ngoài pilot. Cố định grouping và đánh dấu nhóm
liên quan 48 câu đã xem là development trước chia dữ liệu mới. Chọn thêm nguồn
objective-scored từ inventory bằng metadata/loại task và coverage, không lọc
từng câu/model để tăng score. MATH500 vẫn phải được báo như một regime có thể
thiếu headroom, không xóa kết quả âm để chọn benchmark thuận lợi.

Trên development mới chọn trước bằng metadata, cần đo riêng hai cơ hội:
(a) oracle gap cho task routing; (b) proxy incumbent regret cho hiệu chỉnh
feedback. Chỉ có disagreement không đủ. Nếu cả hai gần zero, contribution
phù hợp là chi phí/certification/robustness, không hứa tăng accuracy.

### Nghiên cứu sửa phương pháp theo rủi ro của quyết định

Hướng đáng kiểm tra là một **incumbent-preserving audit rule**: bắt đầu từ lựa
chọn raw feedback, chỉ đổi model nếu nhãn gold cung cấp bằng chứng đủ mạnh về
gain của challenger. Calibration/correction phục vụ decision gaps và mức độ
bất định, thay vì luôn thay thế thứ hạng tốt ban đầu. Đây là đề xuất mới cần
protocol riêng; **chưa implement, chưa có guarantee và chưa có kết quả thắng**.

Cần thiết kế estimator và confidence rule đúng sampling design; nếu acquisition
thích nghi phải có support và xử lý stopping/multiple comparisons. Không dùng
bootstrap của development để tự cấp bảo đảm safety trên deployment. Baselines
phải gồm RawJudge, RawJudgeRectifier, CalibratedJudge, gold-only adaptive/paired
controls và một conservative incumbent rule cùng quyền truy cập. Chỉ thêm
neural router khi development độc lập cho thấy complementary outcomes có thể
dự báo từ thông tin sẵn có trước khi chạy solver.

Mục tiêu phương pháp nên là **dùng audit để sửa thứ hạng khi proxy sai, đồng
thời hạn chế gây hại khi proxy đã tốt**, với quality/cost/uncertainty được đo
trên nhiều regime được chọn trước. Đây có ý nghĩa thực tiễn hơn mục tiêu
ép một correction luôn thắng trên pool không còn accuracy headroom. Novelty
và khả năng nhận bài A/A* vẫn cần nghiên cứu và bằng chứng độc lập; kết quả
hiện tại chưa xác nhận cả hai.

[Báo cáo đã kiểm chứng](routerbench_sparse_gold_v1_assessment_2026-10-06.md) ·
[JSON mọi contrasts](routerbench_sparse_gold_v1_results_2026-10-06.json) ·
[Protocol đã khóa](routerbench_sparse_gold_v1_protocol_2026-10-06.md)
