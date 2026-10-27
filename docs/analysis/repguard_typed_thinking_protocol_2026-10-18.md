# Kiểm tra native thinking trên typed tools — 18/10/2026

Typed-tools think=false đã xong 8/8 calls: 6 câu thực thi có nguồn, 2 câu đúng
target và qua check. Demo DISH/2008 tính đúng 256917/371999 →69.064%, nhưng
chưa đủ bằng chứng về chất lượng tổng thể hoặc lợi ích reputation.

Trước khi quy kết năng lực model, kiểm tra **đúng 8 calls B Qwen3:14b trên cùng
8 câu history**, giữ nguyên catalogue/prompt/schema/typed executor, bật native
`think=true` và nâng giới hạn output từ1536 lên4096 để chứa reasoning. Đây là
so sánh **hai cấu hình có ngân sách output khác nhau**, không phải so ngang cost
hoặc tách riêng tác động thinking. Không gọi là reputation gain.

Ghi actual `message.thinking` và `eval_count`, prompt/digest, thời gian, source
references, program và status. Response stop/length/abstain đều giữ; hết output
mà chưa có JSON cuối là thất bại, không retry chất lượng. HTTP cap540s, Modal
function cap600s/call, tối đa8calls. Không đổi case, prompt, units hoặc gold.
Không dùng screen, không chuẩn hóa theo gold factor100. Không tự động chạy
study lớn/model search sau đợt này. Không cần thêm lần demo cho nhánh thinking.

Theo [Ollama thinking documentation](https://docs.ollama.com/capabilities/thinking),
chat trả reasoning và câu trả lời cuối ở các trường riêng. Thực tế có thinking
hay không phải kiểm bằng response của đúng model/server đang deploy.

Plan/source snapshot/intent/raw output riêng ở
`results/thesis_typed_thinking_probe_v1/`. Đây là development diagnostic, chưa
đánh giá độc lập, chưa fit lại reputation/calibration.
