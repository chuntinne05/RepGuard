# Kiểm tra độ nhạy của nhóm prompt MATH500

Worker `45bde622445084fb20c4d095` đã hoàn tất trên 500 prompt; local reporter
tính lại và xác nhận 500 hash. Rule chính khóa trước khi đọc prompt cho **500
nhóm singleton**, không có linked edge hay review edge ở ngưỡng đã định;
**452 câu** nằm ngoài 48 câu pilot.

Để kiểm tra độ nhạy **sau kết quả**, tôi giữ nguyên điều kiện tỷ lệ độ dài
`>=0.70`, rồi dùng riêng char 5-gram Jaccard với các ngưỡng thấp hơn. Đây là
diagnostic, không thay đổi group IDs của run v1 và không dùng gold.

| Raw Jaccard tối thiểu | Cặp nối | Nhóm | Câu chạm nhóm pilot | Câu còn ngoài nhóm pilot |
|---:|---:|---:|---:|---:|
| 0.82 (rule chính) | 0 | 500 | 48 | 452 |
| 0.65 | 0 | 500 | 48 | 452 |
| 0.60 | 0 | 500 | 48 | 452 |
| 0.50 | 6 | 494 | 48 | 452 |
| 0.40 | 12 | 489 | 50 | 450 |

Sáu cặp gần nhất ở ngưỡng 0.50 có raw similarity **0.503–0.583**. Xem prompt
private cho thấy chúng chia sẻ cấu trúc hoặc dạng toán (ví dụ phép quay số
phức, phép chia đa thức, đổi phân số sang thập phân), nhưng biểu thức hoặc
điều kiện toán học khác nhau. Vì thế threshold thấp hơn có thể nhóm các skill
families, không đơn thuần loại bản sao gần nguyên văn. Prompt details tiếp tục
private vì điều kiện tái phân phối archive chưa được xác minh.

Kết luận hẹp: không tìm thấy câu gần trùng **theo rule đã khóa**. Điều này
không chứng minh 452 câu độc lập theo template/skill, không chứng minh có
oracle headroom, và chưa đủ để mở final evaluation. Study sau cần quyết định
trước khi xem gold liệu muốn tách theo exact prompt, template hay skill family;
quy tắc nhóm phải phù hợp claim transfer. Một split theo câu chỉ đo tổng quát
hóa sang câu mới trong cùng benchmark; không được gọi là transfer giữa domain.

[Kết quả grouping đã kiểm chứng](routerbench_prompt_groups_v1_assessment_2026-10-06.md) ·
[Protocol đã khóa](routerbench_prompt_groups_v1_protocol_2026-10-06.md) ·
[Kết quả gold thưa](routerbench_sparse_gold_v1_assessment_2026-10-06.md)
