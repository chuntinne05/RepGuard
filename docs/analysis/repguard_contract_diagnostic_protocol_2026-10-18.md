# Chẩn đoán hợp đồng đầu ra — development history, 18/10/2026

Kế hoạch này được viết khi pilot v2 vẫn đang thu thập, chưa phân tích kết quả
20 câu screen. Quan sát history hiện có: tác tử A thường trả
`insufficient_evidence`, kể cả khi câu hỏi có số liệu trong tài liệu. Đây là
triệu chứng, chưa chứng minh nguyên nhân. Không thay đổi batch hoặc gate v2.

Sau khi lưu và kiểm toán đầy đủ pilot v2, cho **cùng tác tử B Qwen3:14b** chạy
thật trên **8 câu history đầu tiên**, với hai biến thể cố định:

1. `unconstrained_json`: giữ nguyên messages, model, token cap và tùy chọn;
   bỏ constrained JSON grammar trong request. Đầu ra vẫn phải là JSON đúng
   contract gốc. Không sửa Markdown fence hoặc đáp án lỗi cho đẹp điểm.
2. `reasoning_first`: thêm trường `reasoning` trước các trường cũ trong schema
   và yêu cầu phân tích nguồn/phép tính trước khi quyết định trả lời. Loại riêng
   trường này khi đưa vào executor; lưu toàn bộ phản hồi gốc.

Tổng tối đa **16 lượt gọi mới**, không thêm model, không dùng screen làm dữ liệu
chọn prompt, không retry câu sai/từ chối. Mỗi lần gọi có intent lưu trước và raw
response sau; lỗi vận chuyển không rõ trạng thái phải dừng để kiểm tra.
Đối chiếu với phản hồi B đã chạy thật trong v2 trên cùng 8 câu, không gọi lại
baseline hoặc gọi đó là lượt suy luận mới. Gold chỉ dùng trong đánh giá local
sau khi đã có các phản hồi; GPU chỉ nhận tài liệu/câu hỏi và contract.

Báo cáo số câu thực thi có nguồn, số câu ra kết quả đúng, số câu đồng thời đúng
và qua check; ghi input/output token. Nếu cải thiện trên history thì đây chỉ là
bằng chứng development để thiết kế vòng sau. Không coi là cải thiện đã xác nhận,
không thay kết quả âm của v2, không tái sử dụng probability/calibrator cũ cho
prompt mới rồi tuyên bố còn được hiệu chỉnh tốt.

Đường backend dùng chung app **mới** `repguard-thesis-real-pilot-20261018`,
chỉ deploy sau khi collector v2 kết thúc. Prototype live mặc định vẫn dùng
contract v2 và có nhãn giới hạn nghiên cứu. Mã: `thesis_pilot/diagnostic.py`;
artifacts: `results/thesis_contract_diagnostic_v1/`.
