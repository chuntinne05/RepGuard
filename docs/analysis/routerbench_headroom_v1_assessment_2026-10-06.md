# Dư địa chọn model trên MBPP và FinQA

Run `58bcf5179974f10ebe94c405`: 40 files × 200 câu development đã được đọc score đúng vị trí, kiểm chứng checksum và tính lại tại local. Không có solver/judge calls mới.

| Dataset | Common câu | Loại do trùng hash | Dev đã đọc score | Còn chưa đọc | Best fixed | Oracle | Headroom | CI95 mô tả | Câu cứu được |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| mbpp/test | 970 | 4 | 200 | 770 | 78.00% | 94.50% | 16.50 điểm % | [11.50, 22.00] | 33/200 |
| finqa/test | 1138 | 9 | 200 | 938 | 74.00% | 88.50% | 14.50 điểm % | [9.50, 19.50] | 29/200 |

Oracle chọn model sau khi biết score từng câu. Headroom >0 chỉ cho thấy có chỗ về mặt lý thuyết; không chứng minh một router dự báo được câu nào cần model nào. Score là giá trị evaluator đã lưu trong archive, chưa được tái chấm ở study này.

Model pool và 200 câu/domain được chọn theo metadata/hash trước khi worker đọc score. Các câu còn lại chưa được đọc score ở run này. Chỉ số và CI dựa trên câu development; không dùng chúng làm final confirmation.

[Protocol](routerbench_headroom_v1_protocol_2026-10-06.md) · [JSON kết quả](routerbench_headroom_v1_results_2026-10-06.json) · [Phân tích MATH500](routerbench_sparse_gold_v1_interpretation_2026-10-06.md)
