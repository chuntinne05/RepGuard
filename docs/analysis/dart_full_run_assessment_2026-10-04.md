# Kết luận full run DART và bước nghiên cứu tiếp theo — 04/10/2026

## 1. Đã xong những gì?

**Full collection, replay và follow-up đều hoàn tất lúc khoảng 22:26 giờ Việt Nam.**

- 2.352/2.352 kết quả chấm thật trên Modal, không trùng index; 2.352 response
  hợp lệ về schema. Đây không phải tỷ lệ chấm đúng.
- 14 agent lịch sử × 168 task AppWorld `test_normal`, thuộc 56 generator.
- Model judge Qwen3-14B, no-thinking theo protocol, digest và collector source
  hash giữ nguyên qua lần phục hồi; Ollama 0.34.4.
- Full judge replay: 300 tổ hợp fold/budget/seed, 2.100 audit-policy runs.
- Paired-audit ablation: thêm 1.200 audit-policy runs cho self-report và 1.200
  cho judge. Replay không phát sinh solver/judge inference mới.
- Post-run diagnostics đã tái dựng đúng action từ candidate bank và xác nhận
  toàn bộ control không dùng feedback giữ nguyên prediction giữa hai kênh.
- Toàn bộ suite: **233 tests passed**. Các test nhỏ/synthetic chỉ kiểm tra code
  và toán lấy mẫu; không được tính vào kết quả thực nghiệm phía trên.
- MMLU sealed holdout và outcome AppWorld challenge chưa được mở.

**Kết luận thực thi:** thành công. **Kết luận gate phương pháp:** không đạt.
Không nhầm hai trạng thái này.

## 2. Kết quả chính, cùng ngân sách nhãn audit 10%

Đơn vị: số task thành công trung bình trên 168 task qua 20 seed chọn audit.

| Phương pháp | Self-report | Real judge |
|---|---:|---:|
| DART đầu tiên | 55,50 | 55,35 |
| DARTContrast — bản sửa | 67,40 | 63,90 |
| AuditOnly | 62,85 | 62,85 |
| RandomHistory | 64,40 | 64,60 |
| UncertaintyHistory | 65,50 | 65,95 |
| UniformAuditGlobal | 69,70 | 69,70 |
| UniformAuditKNN | 66,35 | 66,35 |
| PairedHistory | 65,85 | 65,45 |
| PairedGlobal | 71,95 | 71,95 |
| PairedKNN | 70,45 | 70,45 |

Không có phương pháp dùng history đang xét nào chứng minh vượt các control mạnh.
PairedGlobal chỉ là control chọn agent bằng nhãn audit, không phải DART đổi tên.

Một số chênh lệch quan trọng, CI bootstrap theo generator, đơn vị điểm phần trăm:

- DARTContrast judge − UniformAuditGlobal: **−3,45**, CI **[−6,90; +0,06]**.
  Chưa đủ để kết luận thua ở mức 95% theo contrast này, càng không thể claim thắng.
- DARTContrast judge − DARTContrast self-report: **−2,08**, CI **[−3,75; −0,42]**.
  Đổi sang judge làm giảm 3,50 task trung bình trong cấu hình đã khóa.
- PairedHistory judge − PairedGlobal: **−3,87**, CI **[−6,93; −0,86]**.
- Phép so sánh bổ sung hậu nghiệm DARTContrast judge − PairedGlobal:
  **−4,79**, CI **[−8,75; −0,92]**. Đây không phải contrast chính được khóa cho
  full replay ban đầu; phải ghi rõ tính exploratory của nó.

Các CI chưa điều chỉnh cho toàn bộ quá trình phát triển nhiều phiên bản. Dataset
đã được xem nhiều lần; gate chất lượng judge còn sử dụng mẫu trải qua các outer
folds. Việc learner không đọc test gold khi ra action không biến toàn bộ nghiên
cứu này thành một đánh giá test độc lập. Không claim khả năng tổng quát cuối cùng.

## 3. Judge có vấn đề gì?

Trong 2.352 trajectory, evaluator chính thức xác nhận 590 thành công, 1.762 thất
bại. Judge tại ngưỡng 0,5 có TP=581, FN=9, TN=690, FP=1.072.

- Accuracy: **54,04%**, self-report **55,10%**.
- Balanced accuracy: **68,82%**, self-report **70,03%**.
- Judge sửa được **172** lỗi self-report nhưng tạo thêm **197** lỗi.
- Brier score của xác suất judge thô: **0,33000**. Không phải xác suất đã được
  hiệu chuẩn tốt chỉ vì output là một số từ 0 đến 1.
- 1.364/2.352 log bị cắt theo quy tắc đầu/cuối đã khóa. Các nhóm clipped và
  unclipped khác cả task/agent; không suy ra tác động nhân quả của cắt log.

Mẫu lỗi rõ nhất là **báo thành công quá nhiều**: judge nhận gần hết success nhưng
bỏ qua nhiều failure. Thiếu bằng chứng trạng thái cuối, tác dụng phụ không hiện
trong log hoặc tin lời hoàn thành của agent là các giả thuyết cần kiểm tra trực
tiếp; các confusion counts tự chúng chưa chứng minh được nguyên nhân nào.

Gate pilot PASS chỉ có nghĩa kênh feedback có tín hiệu trên chance theo tiêu chí
đã khóa. Nó không có nghĩa judge hơn self-report, được hiệu chuẩn tốt hoặc giúp
router chọn agent đúng hơn. Full run hiện cho thấy cần tách ba câu hỏi đó.

## 4. Điểm có thể khai thác tiếp, nhưng chưa được chứng minh

**AUC của xác suất judge liên tục là 0,79471**, trong khi AUC của chính verdict
nhị phân tại 0,5 bằng balanced accuracy **0,68817**. Replay v1 đã khóa sử dụng
verdict nhị phân. Việc nhị phân hóa đã bỏ thứ tự giữa nhiều giá trị confidence.

Đây là bằng chứng mô tả rằng raw score còn thông tin xếp hạng ở mức trajectory;
không phải bằng chứng một router giữ raw score sẽ thắng. AUC trong từng agent
dao động khoảng 0,659–0,954, nhưng số success của một số agent rất nhỏ. Không
suy thẳng từ AUC classification sang lợi ích routing hoặc chọn agent theo task.

Nút thắt thứ hai là cách dùng nhãn audit. Nếu được cấp toàn bộ gold selection
history để chọn trong cùng candidate bank, diagnostic test score là 74,35/168;
DARTContrast thực đạt 63,90. Mức 74,35 dùng thêm gold nên không được báo như kết
quả phương pháp. Đồng thời learner global dùng toàn bộ ngân sách đang mạnh hơn
selector chia ngân sách construction/selection. Điều này gợi ý kiểm tra việc tái
sử dụng nhãn hiệu quả hơn, chưa chứng minh riêng split là nguyên nhân.

## 5. Thứ tự hợp lý cho vòng tiếp theo

### Bước 1 — ablation biểu diễn feedback, không gọi thêm model

Tận dụng 2.352 score hiện có. Khóa một protocol mới trước khi chạy:

1. Giữ nguyên task folds, 20 seed, audit budget, nhãn audit đã lấy, candidate
   bank và baseline. Không thay nhiều thành phần đồng thời.
2. So sánh proxy nhị phân hiện tại, xác suất thô và xác suất liên tục được hiệu
   chuẩn chỉ bằng construction audit. Không chọn threshold/calibrator bằng gold
   selection hoặc test. Phương pháp hiệu chuẩn/hyperparameter phải được khóa.
3. Đầu tiên giữ acquisition uniform giống nhau để cô lập tác động của proxy;
   sau đó mới xét thiết kế contrast. Báo cả task success, RMSE và variance.
4. Đối chứng vẫn phải gồm UniformAuditGlobal và PairedGlobal. Cải thiện so với
   DART cũ nhưng vẫn thua control không đủ cho claim phương pháp.

Đây là bước có lý do cụ thể từ dữ liệu và không cần thêm chi phí inference. Chưa
chạy ablation continuous-score này trong báo cáo hiện tại; không gán score dự kiến.

### Bước 2 — kiểm tra sử dụng toàn bộ nhãn, cùng chính xác audit set

Nếu bước 1 chưa đủ, đối chiếu selector hiện tại với learner học từ cả nhãn
construction và selection đã trả phí. Cross-fitting chỉ hợp lệ khi mô hình proxy
không dùng chính các nhãn đang sửa sai và sampling dependencies được tính đúng.
Không áp dụng chéo ngây thơ cho adaptive acquisition rồi tự gọi unbiased/safe.

### Bước 3 — candidate và khả năng tổng quát

Sau hai kiểm tra có kiểm soát mới cân nhắc representation ngữ nghĩa instruction
và contextual learner mạnh hơn TF-IDF/kNN. Khóa feature chỉ có trước khi agent
hành động; không dùng required API/skill từ gold. Chỉ mở đánh giá độc lập khi
ứng viên vượt control mạnh trên development; không dùng holdout để tìm cấu hình.

Đây là thứ tự nghiên cứu, không phải cam kết thành công. Tránh thay solver,
judge, feature, split, audit và threshold cùng lúc rồi không biết gain đến từ đâu.

## 6. Vị trí với các phương pháp liên quan và mục tiêu bài báo

[CABS](https://arxiv.org/html/2607.09015v1) quan sát true reward của arm được chọn
trong setting online và surrogate của các arm khác; cần đối chiếu cost/information
setting trước một so sánh faithful. [SELECT-LLM](https://arxiv.org/html/2510.09418v2)
chọn reference query để giảm annotation cost; một reference có thể chấm nhiều
model, khác đơn vị task–agent audit đang dùng. [Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html)
là nền tảng đã có cho selective annotation hỗ trợ bởi prediction. Không claim
những ý tưởng chung đó là novelty riêng của DART.

Hiện đầu ra chắc chắn là artifact đo lường và chẩn đoán có thể bổ sung HistRepEval.
**Đầu ra DART superior chưa có.** Muốn bài phương pháp đủ mạnh cần gain hữu ích,
so sánh faithful, chi phí đầy đủ, cơ chế được kiểm tra và xác nhận độc lập; không
thể bảo đảm A/A* bằng số lần chạy hay bằng việc thêm độ phức tạp vào thuật toán.

## 7. Vận hành, chi phí và artifact

- 7.042.225 input tokens, 20.762 output tokens được ghi trong response ledger.
- Tổng latency của các lời gọi có kết quả: 10.318,57 giây ≈ 2,87 giờ. Đây bao
  gồm thời gian request/load, không phải số GPU-hours được đo hay billing USD.
- 2.353 logical request starts cho 2.352 kết quả; một index bắt đầu lại sau lỗi.
  Retry cấp transport có thể tốn thêm compute và chưa được đếm đủ trong ledger.
- Khoảng trống lớn nhất 14.862,52 giây; controller tự resume, không đếm trùng.
- Raw benchmark derivatives giữ trong `results/`, không đưa plaintext per-task
  lên Git. Báo cáo và aggregate JSON được công bố cùng code.

Tài liệu chính:

- [Bảng đầy đủ và follow-up](dart_followup_report_2026-10-04.md).
- [Kết quả full replay gốc](dart_real_judge_result_2026-10-04.md).
- [Diagnostic JSON](dart_postrun_diagnostics_2026-10-04.json).
- [Protocol ablation và giới hạn](dart_paired_audit_ablation_protocol_2026-10-04.md).
- [Lịch sử sự cố và provenance commit](dart_continuation_notes_2026-10-04.md).
