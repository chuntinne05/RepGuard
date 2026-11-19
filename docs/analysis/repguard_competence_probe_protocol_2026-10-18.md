# Đối chứng năng lực bộ giải — trước khi chạy

18/10/2026, bổ sung trong lúc batch causal v1 chạy; chưa chạy inference của
đối chứng này khi viết protocol. Không thay frozen source của causal v1.
Chờ batch đó hoàn tất trước khi cập nhật app. Chỉ tám HISTORY cũ, không chọn
câu theo lỗi mới, không dùng làm generalization hoặc xác nhận superiority.

Revision trước inference: thêm arm raw-matrix vì trace FRT cho thấy catalogue
không gắn rõ row group với năm, và HWM có nhầm alias step/constant.
Không chọn/chỉnh sửa arm dựa trên kết quả competence, vì chưa có call nào.

24 calls thật: tám câu × `{dsl_native,numeric_native,numeric_raw_native}`, Qwen3:14b/digest
giữ nguyên, temperature0/seed18102026/context16384/native thinking true,
output cap4096 mỗi call. Không retry vì chất lượng. App riêng giữ nguyên.
Tổng hai batch trong đợt này tối đa136calls (revision tăng8), không tính các đợt trước.

DSL native giữ đúng prompt/source input của initial causal v1; khác native
thinking và cap4096 so với cap1536, nên không suy diễn tác động riêng của
thinking ở cùng compute. Numeric native nhận đúng dữ liệu công khai, trả
reasoning/status/answer số hoặc percent string; không phải chép reference
hay sinh executable program. So hai native arm dùng cùng cap; instruction
và output contract khác nhau nên đây là diagnostic của cả interface, không
phải ablation tách mọi thành phần prompt. Numeric raw native giữ cùng system
và schema như numeric native, thay catalogue bằng table matrix nguyên thứ tự
và pre/post text. Đây là can thiệp serialization; input token cost khác nhau.

Score chính giữ FinQA exe_ans round5, không oracle nhân/chia100. Numeric
parse được không có nghĩa source-grounded hoặc đúng semantic. Lưu raw
thinking/content, digest, prompt hash, tokens, request seconds và validation;
không trộn với metric source-verified của DSL. Không dùng kết quả tám câu
để chốt phương pháp cuối; baseline mạnh hơn nếu có phải chạy tiếp trên các
report mới và cùng quyền tool/budget trước mọi claim superiority.
