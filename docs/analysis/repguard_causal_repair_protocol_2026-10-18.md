# Thí nghiệm nguyên nhân và khả năng sửa lỗi — v1

Đóng băng ngày 18/10/2026 trước inference mới. Run `31ea9478aa9d2696ef401e46`.
Protocol máy đọc được, danh sách câu, hashes và source snapshot nằm tại
`results/thesis_causal_repair_v1/{plan.json,private.json,frozen_source.zip}`.
Đây là nghiên cứu development, chưa phải xác nhận cuối hoặc chứng minh novelty.

## Giả thuyết và can thiệp

1. Giao diện một phép toán đang giới hạn solver: bổ sung DSL tối đa tám bước,
   giữ operands là reference từ nguồn, thực thi toán và percent bằng phần mềm.
   Thay đổi này gộp cả representation và prompt; so với probe cũ không nhận là
   tác động nhân quả riêng của số bước.
2. Truy xuất/chọn evidence là bottleneck: trên tám HISTORY đã xem, so sánh
   DSL đầy đủ với cùng DSL chỉ được cấp các span evidence do FinQA đánh dấu.
   Đây là **oracle diagnostic**, không phải retrieval triển khai được; không
   đưa gold program/target vào prompt và không tính arm này là method score.
3. Các repair action có lợi ích khác nhau theo trạng thái: trên 24 báo cáo mới,
   thu initial và tối đa ba repair thật, cùng model/tools/token cap.
   `self_repair` sửa toàn bộ; `evidence_repair` chỉ thay reference, giữ nguyên
   skeleton/constant/intermediate/unit; `plan_repair` chỉ dùng các reference
   ban đầu nhưng được sửa phép toán/thứ tự/constant. Output vi phạm constraint
   hoặc không execute được bị từ chối và giữ initial, không dùng gold để chọn.

## Chọn mẫu, đối chứng và chi phí

FinQA TRAIN commit/dataset hash giữ nguyên pilot. Chọn 24 report bằng hash
metadata, mỗi report một câu; loại toàn bộ 100 report pilot và hash 200 câu
archive cũ trước khi lấy target. Không chọn riêng câu baseline sai.
Đây là mẫu development mới, không mở final test.

Qwen3:14b cùng digest trước; L4, Ollama phiên bản đã pin; think=false,
temperature=0, seed=18102026, context=16384, output cap=1536 mỗi call.
16 calls diagnostic; 24 initial mới; chỉ thu thêm 72 repairs nếu initial đúng
và qua mechanical check ít nhất 4/24. Tổng tối đa 112 calls; wall cap collector
3600 giây. Không retry vì chất lượng. Initiated chưa rõ outcome phải dừng để
kiểm tra, không âm thầm gọi lại. Dùng app riêng `repguard-thesis-real-pilot-20261018`.

Score chính vẫn so chính xác `exe_ans` làm tròn cuối năm chữ số, không match
oracle nhân/chia 100. Giữ nguyên kết quả cũ. Bất nhất semantic/unit được audit
riêng, không loại câu sau khi xem output để làm đẹp điểm.
Source validity chỉ chứng minh lấy số từ nguồn và phép toán chạy được.

## Gate trước khi phát triển reputation

Repair union phải cứu ít nhất 3 câu và union phải hơn best fixed action ít nhất
2/24 để đáng tiếp tục học chọn action. Union dùng gold là upper bound chẩn đoán,
không phải policy có thể deploy. Gate nhỏ này chỉ sàng lọc cơ chế, không có
nghĩa statistical superiority hoặc đủ lực để kết luận thesis.

Nếu qua gate, thử learner đã định trước: ba fold report tách biệt; học gain
repair-trừ-harm từ paired outcomes của hai fold còn lại. Global shrinkage prior4;
local key `(question skill, initial source family, one/multi step)` kéo về global
với prior6; sửa khi predicted gain>0.05, còn lại STOP. Không tune sau kết quả.
Đối chứng initial, từng fixed repair, cùng agent tự sửa, global history không
context. Đây vẫn là exploratory OOF, không phải independent confirmation;
không thay contextual gain learner bằng tên gọi reputation rồi nhận novelty.

Ghi đủ rescue/harm, rejected edits, serving tokens và collection tokens/calls
riêng. Replay trên outputs thật không phải inference bổ sung. Request seconds
không phải tổng tiền billing. Không bảo đảm phương pháp thắng.
