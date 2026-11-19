# Erratum: số câu common chưa chọn và câu unique đủ điều kiện

Đối chiếu `results/routerbench_headroom_v1/cloud/input_private.json` với
[kết quả public](routerbench_headroom_v1_results_2026-10-06.json) ngày
07/10/2026 (giờ Việt Nam): cột "Còn chưa đọc" trong assessment và trường
`unselected_questions_retained` của JSON cũ lấy **common questions − 200**.
Hai số **770 MBPP** và **938 FinQA** gồm cả query hash bị loại do trùng trong
intake. Đây không phải số **unique eligible** cho một tập đánh giá mới.

| Dataset | Common | Trùng bị loại | Unique eligible | Đã chọn development | Unique eligible còn lại | Common chưa chọn, gồm trùng |
|---|---:|---:|---:|---:|---:|---:|
| MBPP | 970 | 4 | 966 | 200 | **766** | 770 |
| FinQA | 1.138 | 9 | 1.129 | 200 | **929** | 938 |

Các outcome, best-fixed/oracle, CI và gate trước đây **không đổi**. Đây là sửa
cách gọi mẫu số cho kế hoạch split trong tương lai, không phải chạy lại
experiment hoặc thay protocol đã khóa. Những protocol đã được băm SHA256 có
thể vẫn chứa cách gọi cũ; giữ nguyên chúng để không làm mất provenance. Khi
chọn câu mới, phải bắt đầu từ tập 766/929 unique eligible còn lại, kiểm tra
không trùng với 200 câu development cũ.
