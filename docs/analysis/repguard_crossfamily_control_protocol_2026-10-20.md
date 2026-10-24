# Đối chứng bổ sung: solver không hạn chế hằng số và khác họ model

Thiết kế lúc vòng scoped-repair vẫn đang chạy, **chưa xem model scores TAT-QA**.
Đây là đợt development bổ sung hậu nghiệm theo lỗi kỹ thuật quan sát được,
không thay thế protocol hay sửa điểm vòng scoped-repair.

Hai kiểm tra cần tách biệt:

1. Ràng buộc binding/count-literals có làm Qwen solver và tự kiểm tra yếu đi?
2. Với một họ model khác, có xuất hiện unique successes mà một router có thể
   khai thác, hay strongest fixed workflow vẫn giải hết phần oracle union?

Dùng **cùng toàn bộ24 contexts**, không chọn riêng các câu sai. Reuse đúng24
Qwen Plain outputs thật của vòng trước; mỗi câu gọi thêm Self1 và Self2 không
hạn chế hằng số (48 calls mới). Gemma chạy Plain/Self1/Self2 trên toàn24 câu
(72 calls mới). Tổng cap120 calls mới; không phải120 câu độc lập.

Model mới chỉ có một lựa chọn, không sweep:
[Gemma4:26b-a4b-it-q4_K_M](https://ollama.com/library/gemma4:26b-a4b-it-q4_K_M),
public digest prefix5571076f3d70, Q4_K_M. Tải bằng CPU vào volume mới
`repguard-thesis-gemma4-models-20261020`; lưu full digest/manifest rồi khóa
plan/source trước inference. Không thay weights Qwen. App mới
`repguard-thesis-crossfamily-20261020`, riêng với app Ollama gốc của người dùng.

Cả hai dùng cùng đầy đủ nguồn/cataloque, Python executor và JSON plain schema.
Review được đổi mọi trường, không phải giữ binding names/nguồn cũ. Invalid
review giữ incumbent; không dùng gold để quyết định. Cùng L40S,4096 output cap,
16384 context, seed20102026, temperature0, think=False. Ollama0.40.6.

**Giới hạn cấu hình:** trang model đề nghị temperature1.0; ở đây chuẩn hóa
temperature0 để kiểm cấu hình greedy cùng budget. Không nhận đây là cấu hình
tối đa hóa năng lực Gemma hoặc effect thuần của kiến trúc. Một sample/arm không
chứng minh độ ổn định giữa seeds.

Chỉ triển khai API review mới lên app Qwen sau khi collector scoped-repair đã
hoàn tất, giữ source cũ. Collector gọi tuần tự Qwen rồi Gemma, không chạy hai
batch suy luận đồng thời. GPU chỉ mount weights, không mount annotations.
Hóa đơn không bằng tổng decode duration; vẫn có startup và idle billing.

Chấm bằng evaluator TAT-QA gốc và model-predicted scale, y như vòng scoped.
Tính cả cost24 lượt Qwen đã reuse khi so workflow1/2/3 calls. So Qwen Plain
Self2 với Scoped Self2 trên **ALL24**, paired bootstrap20k và exact McNemar;
đây là capability/contract comparison, không phải reputation gain.

Gate cho việc thu history khác họ tiếp theo: union sáu workflows phải vượt
strongest fixed ít nhất2 câu và mỗi họ phải có ít nhất1 câu được nó giải đúng
trong khi toàn bộ workflows của họ kia sai. Oracle dùng gold chỉ để đo
headroom, không phải selector triển khai. Chưa fit learner trong đợt đối chứng.
Sau2 context Gemma, chỉ dừng kỹ thuật nếu không có direct output nào executable;
mọi prompt phải <=12288 tokens. Không retry theo chất lượng.

Giữ giới hạn:24 TRAIN contexts, không có human semantic adjudication,
context-disjoint không suy ra report-disjoint, chưa có independent test.
