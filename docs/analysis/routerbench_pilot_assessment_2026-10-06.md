# Pilot judge thật trên MATH500: kết quả

Run `bad5a513bd5d227711eb1e0d`: **288/288 judgment** cho 48 câu × 6 model; đã kiểm chứng artifacts và tính lại kết quả.

## Phạm vi

Qwen3-14B chạy thật trên Modal, think=false, context 16.384. Candidate answers là execution có sẵn trong LLMRouterBench; không gọi mới sáu solver. Đây là pilot development đánh giá feedback, chưa phải DART routing hay xác nhận thắng baseline.

## Các con số

| Chỉ số | Kết quả |
|---|---:|
| Judgment hợp lệ | 100.00% |
| Answer bị cắt bớt | 17.71% |
| Brier judge thô — thấp tốt hơn | 0.115773 |
| Brier hiệu chỉnh cross-fit | 0.094493 |
| Brier control không judge | 0.173013 |
| Cải thiện Brier so với control không judge | 0.078519 |
| CI95 cải thiện Brier | [0.042103, 0.113073] |
| Tỷ số phương sai residual / outcome differences | 0.694670 |
| CI95 tỷ số trên | [0.519834, 0.880492] |
| Attempts đã khởi tạo | 288 |
| Input tokens ghi nhận | 511,561 |
| Output tokens ghi nhận | 3,500 |
| Attempts chưa biết đủ usage | 0 |
| Tổng thời gian inference ghi nhận | 7.40 phút |

**Operational gate: PASS.**
**Expansion signal: PASS.**

Expansion yêu cầu ít nhất 95% valid, tối đa 50% answers bị cắt, tỷ số phương sai ≤0,90 và CI upper<1. Tiêu chí được khóa trước judgment; không sửa sau kết quả.

## Diễn giải

Tỷ số 0.6947 tương ứng giảm khoảng 30.53% phương sai trong các chênh lệch giữa model. Feedback đã hiệu chỉnh có thông tin ngoài khả năng trung bình của từng model, theo chẩn đoán held-out của pilot này. Brier thấp hơn nghĩa là xác suất dự báo gần gold hơn, không phải accuracy hay số task thành công.

Đây là bằng chứng để thử bước tiếp với gold thưa. Chưa đo được số nhãn có thể tiết kiệm, lợi ích chọn agent, hay lợi ích ròng sau chi phí judge. Calibration ở pilot được học từ toàn gold của 36 câu khác trong mỗi fold; cần kiểm tra lại khi chỉ cấp 5%, 10%, 20% nhãn và so với đối chứng cùng quyền truy cập.

## Giới hạn và quyết định tiếp

- Tất cả gold của pilot được dùng cho chẩn đoán cross-fit: 36 câu train, 12 câu held-out mỗi fold. Không gọi đây là routing với ngân sách 10%.
- Bootstrap 2.000 lần theo question trên prediction cố định; chưa refit toàn bộ learner, chưa chứng nhận template/near-duplicate independence.
- Gold là binary score của evaluator MATH500 đã lưu, không phải đáp án được người kiểm chứng lại trong pilot. Không đọc gold của các câu ngoài pilot vào analysis.
- Model-only ridge là bản thích ứng mới; không dùng parser tên model để giả lập scaffold.
- Usage chỉ là inference đã ghi nhận; tổng Modal billing, thời gian startup và unknown attempts phải tính riêng, không đổi token count thành USD khi chưa có hóa đơn.
- Pipeline đã dừng theo giới hạn pilot. Nếu gate fail, phân tích feedback/clipping/calibration trước mở rộng. Nếu pass, khóa study lớn hơn và các đối chứng cùng ngân sách trước khi chạy.

[Protocol](routerbench_pilot_protocol_2026-10-06.md) · [JSON đầy đủ](routerbench_pilot_results_2026-10-06.json)
