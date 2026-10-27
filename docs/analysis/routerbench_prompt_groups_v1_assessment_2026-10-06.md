# Nhóm prompt MATH500 trước study tiếp theo

Run `45bde622445084fb20c4d095` hoàn tất và được tính lại local trên **500/500 prompt**.

| Chỉ số | Giá trị |
|---|---:|
| Exact question hashes | 500 |
| Near-template groups | 500 |
| Nhóm có từ hai câu | 0 |
| Nhóm lớn nhất | 1 |
| Linked near-template edges | 0 |
| Cặp cần review thêm | 0 |
| Pilot đã xem | 48 câu / 48 nhóm |
| Nằm trong nhóm liên quan pilot | 48 câu |
| Còn ngoài các nhóm pilot | 452 câu / 452 nhóm |

Rule Jaccard được khóa trước khi đọc toàn bộ prompt; đọc đúng một member Qwen3-8B đã chọn bằng metadata, so khớp hash với 500 câu common. Worker không giữ score/output/reference; bản public chỉ có số tổng hợp. Cặp và prompt chi tiết nằm trong artifact private để review.

Đây là grouping heuristic. Các review pairs chưa tự động gộp, nên số nhóm còn lại là ước lượng theo rule đã khóa, **chưa phải chứng nhận độc lập**. Cần xem những cặp này và làm sensitivity analysis bằng prompt trước khi khóa final split. Không dùng score của 452 câu ngoài pilot ở bước này.

[Protocol](routerbench_prompt_groups_v1_protocol_2026-10-06.md) · [JSON tổng hợp](routerbench_prompt_groups_v1_results_2026-10-06.json) · [Phân tích gold thưa](routerbench_sparse_gold_v1_interpretation_2026-10-06.md)
