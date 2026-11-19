# Kiểm tra bản sửa contract — history, 18/10/2026

Trong chẩn đoán đầu tiên, phản hồi `reasoning_first` trên câu history đầu nêu
được 8816 từ nguồn nhưng vẫn xuất `insufficient_evidence`. Đọc lại system prompt
cho thấy chỉ mô tả cụ thể nhánh thất bại mà chưa nói rõ status của nhánh thành
công. Đây là thiếu sót trong thiết kế prompt của lần triển khai này; chưa đủ cơ
sở quy tỷ lệ từ chối cho năng lực nội tại của Qwen hoặc reputation.

Không sửa pilot v2 hoặc chẩn đoán 16 calls đang chạy. Giữ snapshot source/outputs.
Sau khi chẩn đoán đó hoàn tất, thực hiện **tối đa 16 calls mới**, cùng B, cùng
8 câu history đầu, cùng options/token cap, hai biến thể:

1. `explicit_status`: giữ `reasoning_first`, thêm hướng dẫn rõ `status="answer"`
   khi có bằng chứng cho chương trình thực thi được; chỉ từ chối khi thiếu bằng
   chứng thực sự. Status và reasoning phải thống nhất.
2. `schema_prompt`: giữ thay đổi trên, đồng thời đưa toàn bộ schema vào system
   prompt để model đọc được contract đầy đủ, ngoài grammar gửi qua `format`.

Không chọn lại câu, không lấy screen để đánh giá hay tune hai biến thể này,
không sửa output sai hoặc retry chất lượng. Lưu intent trước mỗi call, raw output
và strict source/arithmetic checks; gold history chỉ dùng đánh giá local sau
thu thập. Báo cả hai biến thể, kể cả kết quả xấu. So với dữ liệu thật của các
contract trước trên cùng 8 câu nhưng không tính chúng thành calls mới.

Đây là sửa và kiểm tra tích hợp, chưa là đánh giá độc lập về độ đúng hoặc đóng
góp reputation. Không dùng lại calibrator v2 để bảo đảm độ tin cậy cho contract
mới. Mã `thesis_pilot/contract_repair.py`; artifacts riêng
`results/thesis_contract_repair_v1/`, có plan/hash/source snapshot và receipts.
