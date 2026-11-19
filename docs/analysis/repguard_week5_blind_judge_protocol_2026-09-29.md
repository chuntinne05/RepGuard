# Phép kiểm tra judge không thấy đáp án ứng viên

**Trạng thái 29/09/2026:** manifest đã khóa, **chưa chạy request** vì lượt Qwen3 8B thinking lớn đang sử dụng cùng Modal GPU. Mục đích là kiểm tra giả thuyết từ kết quả Week 5: trong 112/234 câu có nhiều đáp án ứng viên, `qwen3:14b` đã chọn các phương án khác nhau khi prompt chỉ đổi đáp án được nộp. Điều đó gợi ý khả năng bị đáp án ứng viên ảnh hưởng, nhưng chưa chứng minh nguyên nhân.

## Đối chứng đã khóa

- Dùng lại đúng 280 câu history, 20 câu/môn × 14 môn, và đúng digest Qwen3 14B của lượt judge trước. Protocol mới `2b9fe8eb449d78c8cdb79334f6f6112f921efa1b4ef09fd6a2adea18aad0a6eb`.
- Mỗi câu chỉ gửi **một request**, gồm câu hỏi và các lựa chọn. Prompt không chứa đáp án agent, verdict, gold hay tên agent. Judge trả `chosen_letter` và confidence theo JSON schema. Sau khi đã lưu phản hồi, analyzer mới suy ra verdict cho từng đáp án agent bằng phép so chữ cái.
- Giữ `think=false`, temperature 0, top-p 1 và giới hạn 256 token để so cùng mô hình/cấu hình. Đây là phép thử prompt hậu nghiệm được nghĩ ra sau khi xem lỗi lượt đầu, do đó toàn bộ kết quả trên 280 câu này là **thăm dò**, cần tập xác nhận mới trước claim paper.
- Báo choice accuracy theo 280 câu; verdict accuracy, TP/FP/TN/FN trên 694 case đáp án; chênh accuracy với judge thấy ứng viên bằng bootstrap **theo câu**, không coi 694 case độc lập; thời gian/token tổng để so chi phí.

## Thứ tự chạy

1. Đợi lượt thinking 840/840 kết thúc, kiểm tra ledger, GPU và model digest.
2. `run_real_week5_blind_judge.py --collect --limit-per-subject 1` làm pilot 14 câu; kiểm tra 14 JSON và prompt hash.
3. Nếu protocol hợp lệ, chạy `--collect --limit-per-subject 20` để đủ 280 câu và chạy `analyze_real_week5_blind_judge.py`.
4. Dù prompt blind tốt hơn, không tự động thay feedback của ECRT trong cùng tập đã dùng để chọn ý tưởng. Đánh giá tác động thực dụng trên tập xác nhận mới, so với FixedBorrow và model đơn ở cùng compute.

Không có bảo đảm blind judge tốt hơn: nếu mô hình tự giải sai, phép suy verdict cũng sai. Phép này đo nguyên nhân và chi phí tốt hơn rồi mới quyết định có đáng theo hướng judge hay không.
