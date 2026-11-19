# Week 5 — tác động của feedback Modal thật lên HistRepEval/ECRT

**Ngày phân tích:** 29/09/2026. **Trạng thái:** phân tích offline thăm dò hoàn tất. Chưa phải xác nhận độc lập vì team outcome dùng lại test Week 3 đã được xem. Không có câu trả lời mô hình nào được mô phỏng trong phép này; bốn agent, judge và output đều lấy từ ledger chạy thật.

## Thiết kế

- Đầu vào: 280 câu history Week 3 đã được judge `qwen3:14b` trên Modal, 694 judgment duy nhất mở rộng thành 1.120 quan sát agent–câu. Protocol judge `aea88c2c99be006561040acf1a243c4f08cbf0bd9146c27020df1557408a4f48`.
- Chia mỗi môn thành hai nửa 10/10 câu theo thứ tự chọn đã khóa. Fold 0 dùng nửa đầu để hiệu chuẩn độ tin cậy của judge, nửa sau làm history; fold 1 đổi vai trò. **Không dùng cùng câu để vừa hiệu chuẩn vừa cập nhật reputation trong một fold.** Mỗi fold có 560 quan sát agent–câu để hiệu chuẩn và 560 quan sát khác làm history.
- Ma trận lỗi judge ước lượng gộp qua 14 môn trên nửa hiệu chuẩn: sensitivity 0,7982 / 0,7936; specificity 0,6717 / 0,6988; prior correctness 0,4071 / 0,3893 cho fold 0 / 1. Không ước lượng riêng từng agent hoặc môn ở cỡ 10 câu vì không đủ ổn định.
- So `Uniform`, `FixedBorrow` (feedback judge thô), `ECRT` (Bayes hiệu chỉnh bằng nửa hiệu chuẩn) và `OracleFixedBorrow` (thay feedback history bằng gold **chỉ để chẩn đoán**). Cùng bốn đáp án agent thật và cùng test Week 3 cho mỗi điều kiện. OracleFixedBorrow không bảo đảm là trần team accuracy của mọi router.
- `same`: source trùng target, 14 target. `related`: source khác nhưng cùng cụm metadata đã định trước, 13 target có nguồn liên quan. Các source và hai fold được bình quân **trong từng target** trước bootstrap 5.000 lần theo target, tránh coi những phép chấm cùng câu là độc lập.

## Kết quả team accuracy

| Điều kiện | Uniform | FixedBorrow | ECRT | OracleFixedBorrow | ECRT − FixedBorrow, CI 95% |
|---|---:|---:|---:|---:|---:|
| Cùng môn | 47,65% | 48,54% | **48,62%** | 49,09% | **+0,08 điểm %** [−0,04; +0,21] |
| Môn liên quan | 47,82% | **49,36%** | 49,21% | 49,37% | **−0,16 điểm %** [−0,42; +0,11] |

ECRT hơn Uniform khoảng +0,97 điểm % ở `same` và +1,39 điểm % ở `related`, nhưng FixedBorrow đạt gần tương tự. Đó là lợi ích của dùng history/transfer trong thiết lập này, **chưa phải đóng góp riêng đã xác nhận của ECRT**. Khoảng tin cậy ECRT–FixedBorrow đều chứa 0, phù hợp với kết quả Week 3.

## Hiệu chuẩn xác suất

| Điều kiện | Brier FixedBorrow | Brier ECRT | ECRT − FixedBorrow, CI 95% |
|---|---:|---:|---:|
| Cùng môn | 0,2495 | **0,2306** | **−0,0189** [−0,0281; −0,0092] |
| Môn liên quan | 0,2598 | **0,2385** | **−0,0213** [−0,0354; −0,0076] |

Competence MAE cũng thấp hơn FixedBorrow khoảng 0,0504 (`same`) và 0,0509 (`related`). Điều này cho thấy bước hiệu chỉnh feedback có tác dụng rõ ở **ước lượng xác suất năng lực**, nhưng tác dụng đó chưa chuyển thành quyết định đội tốt hơn. Brier thấp hơn OracleFixedBorrow ở một số ô không có nghĩa vượt oracle: beta posterior, prior và trọng số khác nhau; OracleFixedBorrow là đối chứng phản hồi sạch trong cùng một thuật toán, không phải giới hạn tối ưu của metric.

## Diễn giải và giới hạn

1. Judge thực tế có false positive 24,44% và false negative 29,65% theo case, cùng 112/234 câu nhiều đáp án ứng viên cho lựa chọn judge không nhất quán. ECRT dùng ma trận lỗi gộp nên chỉ sửa được thành phần nhiễu bình quân. Nó chưa xử lý sai số phụ thuộc agent, môn hoặc đáp án ứng viên.
2. Mỗi source chỉ có 10 câu history trong một fold. Ranking agent có thể không ổn định; hai fold và bootstrap theo target giúp thấy biến động nhưng không thay thế validation mới.
3. Outcome dùng test Week 3 đã ảnh hưởng định hướng nghiên cứu. Dù code và phép tách calibration/history là đúng, **mọi hiệu ứng ở đây là thăm dò**, không dùng làm bằng chứng cuối cho paper.
4. Phép so sánh dùng voting dựa trên reputation ở cấp môn, chưa có router nhận diện đặc điểm từng câu; vì vậy không kiểm định được lợi ích của task-level routing.

## Quyết định tiếp theo

- Giữ kết luận **ECRT có tín hiệu hiệu chuẩn xác suất, chưa có gain team accuracy riêng so với FixedBorrow**.
- Ưu tiên kiểm tra một judge không được thấy đáp án ứng viên trước khi chấm, hoặc một judge khác họ Qwen, trên dữ liệu và manifest riêng. Đánh giá lại lỗi, độ ổn định và chi phí; không trộn với ledger hiện tại.
- Sau khi lượt thinking lớn hoàn tất, khóa pool/variant và chạy xác nhận trên 280 câu dev Week 5 chưa dùng. Cần bốn agent/variant trên đúng cùng câu; test ghép cặp, compute và độ trễ là endpoint chính.

Mã tái lập: `analyze_real_week5_feedback_impact.py`; raw output: `results/real_week5_feedback_impact_v1/cells.csv` và `analysis.json`.
