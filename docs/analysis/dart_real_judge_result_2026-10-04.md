# Kết quả real judge và DART — 04/10/2026

Cập nhật UTC: 2026-10-04T15:26:22.165874+00:00

## Pilot đã khóa

- Số kết quả: 168; hợp lệ: 168.
- Generator: 53; nhãn thành công: 45; nhãn thất bại: 123.
- Balanced accuracy: 0.6962059620596206; CI 95% theo generator: [0.6405573094061962, 0.7521376811594203].
- Accuracy: 0.5654761904761905; Brier: 0.30851190476190476.
- Gate chất lượng phản hồi: **PASS**.

Gate này đánh giá kênh phản hồi, không chứng minh DART tốt hơn baseline.

## Suy luận thật đã hoàn tất

- Ledger: **2352/2352** kết quả chấm; 2352 hợp lệ.
- Input tokens: 7,042,225; output tokens: 20,762.
- Tổng latency các lời gọi có kết quả: 171.98 phút.
- Log cần cắt: 1364.
- Đây là lời gọi Qwen3-14B thực trên Modal, không phải chạy mới solver lịch sử.
- Số token/latency chỉ của response có ledger; timeout/retry có thể tiêu tốn thêm compute.
- Chưa có billing USD; không suy ra ngang tổng chi phí từ ngân sách gold.

## Replay: mean số task đúng / 168 qua 20 audit seed

| Method | 5% | 10% | 20% |
|---|---:|---:|---:|
| AuditOnly | 57.90 | 62.85 | 65.55 |
| RandomHistory | 61.60 | 64.60 | 67.65 |
| UncertaintyHistory | 60.05 | 65.95 | 67.25 |
| DART | 55.05 | 55.35 | 57.50 |
| DARTContrast | 61.25 | 63.90 | 68.35 |
| UniformAuditGlobal | 64.40 | 69.70 | 75.15 |
| UniformAuditKNN | 62.20 | 66.35 | 71.55 |
| AnchorOnly | 56.80 | 60.60 | 64.80 |
| ProxyGlobal | 53.00 | 53.00 | 53.00 |
| ProxyKNN | 53.00 | 53.00 | 53.00 |
| GoldTrainSingle | 82.00 | 82.00 | 82.00 |
| GoldTrainKNN | 71.00 | 71.00 | 71.00 |

### Primary 10%: DARTContrast trừ baseline

| Baseline | Chênh lệch điểm % | CI 95% điểm % |
|---|---:|---:|
| AuditOnly | +0.63 | [-2.29; +3.51] |
| RandomHistory | -0.42 | [-3.60; +2.77] |
| UncertaintyHistory | -1.22 | [-2.92; +0.42] |
| AnchorOnly | +1.96 | [-1.49; +5.36] |
| UniformAuditGlobal | -3.45 | [-6.90; +0.06] |
| UniformAuditKNN | -1.46 | [-4.76; +1.76] |

**Exploratory method gate: FAIL.**

CI chưa điều chỉnh đa so sánh. 20 seed không phải 20 bộ task độc lập.
Đây vẫn là public development replay; chưa xác nhận độc lập và chưa chứng nhận an toàn triển khai.
AnchorOnly dùng ít nhãn hơn; GoldTrainSingle/KNN dùng full gold, chỉ là diagnostic.

## Việc tiếp theo

Dừng claim DART superior. Phân tích gain của feedback và chi phí chia dữ liệu/candidate bank; không mở holdout để tìm cấu hình thắng.
Chưa có cơ sở bảo đảm bài được nhận ở hội nghị A/A*.
