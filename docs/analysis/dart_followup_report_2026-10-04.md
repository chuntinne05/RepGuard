# DART — phân tích full judge và bước tiếp theo

## Trạng thái thực nghiệm

- Hoàn tất 2.352 kết quả chấm thật trên Modal và replay đã khóa.
- Hoàn tất thêm 1.200 audit-policy runs lấy mẫu theo task cho mỗi kênh feedback.
- Các replay dùng outcome agent lịch sử chính thức; không phải chạy solver mới.
- Đủ 168 task, 56 generator, 14 agent. Seed audit không làm tăng số task độc lập.
- Kiểm tra tính bất biến của mọi control không dùng feedback: PASS.

## Judge có tốt hơn lời tự báo hoàn thành không?

| Metric | Judge | Self-report |
|---|---:|---:|
| Accuracy | 54.04% | 55.10% |
| Balanced accuracy | 68.82% | 70.03% |
| TP / FN | 581 / 9 | 590 / 0 |
| TN / FP | 690 / 1072 | 706 / 1056 |
| Brier raw score | 0.33000 | 0.44898 |
| AUC raw score | 0.79471 | 0.70034 |

Hai kênh đồng ý 84.31% trên các bản ghi hợp lệ. Judge sửa 172 lỗi của self-report và gây thêm 197 lỗi.
CI 95% chênh lệch balanced accuracy (judge − self-report): [-2.81, 0.46] điểm phần trăm.
Brier của self-report ở đây coi bit tự báo là xác suất 0/1; cả hai đều chưa qua calibration. AUC của judge dùng xác suất liên tục; replay v1 đã khóa dùng nhãn ngưỡng 0,5.

## Kết quả task success — mean đúng / 168

### Feedback: selfreport

| Method | 5% | 10% | 20% |
|---|---:|---:|---:|
| DART | 51.55 | 55.50 | 57.65 |
| DARTContrast | 62.00 | 67.40 | 69.55 |
| AuditOnly | 57.90 | 62.85 | 65.55 |
| RandomHistory | 58.70 | 64.40 | 67.55 |
| UncertaintyHistory | 61.70 | 65.50 | 65.85 |
| UniformAuditGlobal | 64.40 | 69.70 | 75.15 |
| UniformAuditKNN | 62.20 | 66.35 | 71.55 |
| PairedAuditOnly | 64.60 | 63.35 | 66.80 |
| PairedHistory | 63.85 | 65.85 | 64.85 |
| PairedGlobal | 62.15 | 71.95 | 76.70 |
| PairedKNN | 62.25 | 70.45 | 73.95 |

PairedHistory exploratory all-comparisons gate: **FAIL**.

| Thay đổi sampling tại 10% | Delta điểm % | CI 95% điểm % |
|---|---:|---:|
| PairedAuditOnly − AuditOnly | +0.30 | [-2.05; +2.77] |
| PairedHistory − RandomHistory | +0.86 | [-1.49; +3.27] |
| PairedGlobal − UniformAuditGlobal | +1.34 | [-1.52; +4.23] |
| PairedKNN − UniformAuditKNN | +2.44 | [-0.21; +5.30] |

### Feedback: judge

| Method | 5% | 10% | 20% |
|---|---:|---:|---:|
| DART | 55.05 | 55.35 | 57.50 |
| DARTContrast | 61.25 | 63.90 | 68.35 |
| AuditOnly | 57.90 | 62.85 | 65.55 |
| RandomHistory | 61.60 | 64.60 | 67.65 |
| UncertaintyHistory | 60.05 | 65.95 | 67.25 |
| UniformAuditGlobal | 64.40 | 69.70 | 75.15 |
| UniformAuditKNN | 62.20 | 66.35 | 71.55 |
| PairedAuditOnly | 64.60 | 63.35 | 66.80 |
| PairedHistory | 63.85 | 65.45 | 67.25 |
| PairedGlobal | 62.15 | 71.95 | 76.70 |
| PairedKNN | 62.25 | 70.45 | 73.95 |

PairedHistory exploratory all-comparisons gate: **FAIL**.

| Thay đổi sampling tại 10% | Delta điểm % | CI 95% điểm % |
|---|---:|---:|
| PairedAuditOnly − AuditOnly | +0.30 | [-2.05; +2.77] |
| PairedHistory − RandomHistory | +0.51 | [-2.35; +3.36] |
| PairedGlobal − UniformAuditGlobal | +1.34 | [-1.52; +4.23] |
| PairedKNN − UniformAuditKNN | +2.44 | [-0.21; +5.30] |

Gate DARTContrast của full replay ban đầu: **FAIL**.

Các gate và CI là exploratory trên cùng public development data; không phải xác nhận độc lập. Không chọn cell 5% hoặc 20% thuận lợi để thay primary 10%.

## Feedback làm thay đổi routing như thế nào?

| Method, budget 10% | Judge − self-report, số task trung bình | CI delta accuracy điểm % |
|---|---:|---:|
| DARTContrast | -3.50 | [-3.75; -0.42] |
| RandomHistory | +0.20 | [-0.89; +1.13] |
| UncertaintyHistory | +0.45 | [-1.73; +2.38] |
| AuditOnly | +0.00 | [+0.00; +0.00] |
| UniformAuditGlobal | +0.00 | [+0.00; +0.00] |

## Chẩn đoán chọn policy với full judge, budget 10%

| Method | Task đúng thực | Diagnostic chọn bằng gold selection-history | RMSE value | Optimism của policy được chọn |
|---|---:|---:|---:|---:|
| AuditOnly | 62.85 | 74.35 | 0.1587 | +0.2852 |
| RandomHistory | 64.60 | 74.35 | 0.1308 | +0.2041 |
| UncertaintyHistory | 65.95 | 74.35 | 0.1191 | +0.1843 |
| DART | 55.35 | 74.35 | 0.1936 | +0.3937 |
| DARTContrast | 63.90 | 74.35 | 0.1151 | +0.1680 |

Diagnostic dùng nhãn gold không được cấp cho learner, chỉ để phân biệt lỗi ước lượng với giới hạn candidate/generalization. Không thay thế score đạt được của DART.

## Diễn giải và việc tiếp theo

1. Đối chiếu cả gain của feedback và gain do cách lấy mẫu. PairedAuditOnly/Global/KNN là control thông thường; không đổi tên một control thắng thành DART mới.
2. Nếu DART hoặc PairedHistory thua learner global dùng toàn bộ ngân sách, ưu tiên kiểm tra chi phí chia dữ liệu, cách học từ toàn bộ nhãn đã trả phí, và chất lượng candidate theo instruction. Chỉ thêm acquisition phức tạp sau khi xác nhận đó là nút thắt.
3. Trước vòng thuật toán tiếp theo, khóa một giả thuyết và control dùng cùng nhãn audit thực tế; báo mọi biến thể. Cần kiểm tra feature/ngữ nghĩa instruction mạnh hơn TF-IDF để tách thiếu thông tin với learner quá yếu.
4. Tái lập baseline liên quan theo đúng feedback/cost setting. [CABS](https://arxiv.org/html/2607.09015v1) có true reward của arm được chọn; [SELECT-LLM](https://arxiv.org/html/2510.09418v2) tính annotation theo reference query. Không âm thầm cấp thông tin khác nhau rồi so trực tiếp.
5. Giữ sealed MMLU và challenge chưa mở. Chỉ xác nhận độc lập sau khi phương pháp vượt control mạnh trên dev với claim và operating point đã khóa.
6. Chưa có kết quả nào ở đây bảo đảm bài A/A*. HistRepEval có thể đóng góp về đo lường; claim DART superior cần vượt các gate phương pháp riêng.

## Sự cố và provenance

Khoảng trống giữa hai bản ghi lớn nhất: 4.13 giờ. Collector đã resume, không nhân đôi ledger. Log xác nhận retry exhaustion; không đủ bằng chứng quy nguyên nhân cho sleep máy.
Logical request starts: 2353; duplicate starts: 1. Transport retry cấp thấp có thể tốn thêm compute chưa phản ánh đầy đủ ở số này.
Protocol và code paired-ablation được viết trước khi chạy, source hashes được ghi vào manifest trước vòng tính kết quả. Lệnh commit trước lần chạy self-report bị iCloud Git index timeout; commit 8e85898 được tạo sau lần chạy đó bằng temporary index. Vì vậy không gọi lần chạy self-report này là thí nghiệm đã commit trước outcome.
Không thay kết quả sau timeout Git. Dữ liệu benchmark per-task không được đưa vào báo cáo công khai.
