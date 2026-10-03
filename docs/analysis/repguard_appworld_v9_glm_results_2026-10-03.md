# AppWorld v9: GLM-4.7-Flash capability screen trên sáu train task mới

**Ngày:** 03/10/2026. **Trạng thái:** 6/6 trajectory thật hoàn tất, runner thoát mã 0; 6/6 cell chấm bằng official AppWorld state-check trong evaluator riêng. Protocol và runner đã được push lên `dev` ở commit `99b1904` **trước** task call đầu tiên. V9 là kiểm tra năng lực solver nền, chưa chạy ECRT, DART hay HistRepEval.

## Vì sao chạy và giữ ranh giới nào

V8 cho Qwen3-Coder 30B và Qwen3 32B cùng thành công đúng ba trong sáu task; không có ca model này cứu model kia. V9 thử một model khác họ Qwen trên sáu **train ID mới** theo quy tắc chọn SHA-256 một task mỗi generator, vị trí 19–24. Không chọn task bằng instruction, lời giải, outcome hoặc gold; không truy cập dev/test/holdout. [Model card GLM-4.7-Flash của Ollama](https://registry.ollama.com/library/glm-4.7-flash) là lý do thử nghiệm, không phải bằng chứng model sẽ giải AppWorld. Chi tiết ID, budget và gate đã khóa tại [`appworld_v9_glm_capability_protocol_2026-10-03.md`](appworld_v9_glm_capability_protocol_2026-10-03.md).

Thiết lập dùng cùng AppWorld `0.1.3.post1` và legacy Recoma ReAct/adapters gold-blind như v7–v8. GLM alias `glm-4.7-flash-ctx8192:latest` digest `724a495ee5055ed5ed9d396c12d1c0bc0eedaf03a4746829bfba59f0946500a5`, parent digest `4475827791a269b02c8ec49b1c3bc1abb5846bacf3fae015b75d33986322d8f6`; context 8.192, temperature 0, top_p 1, `reasoning_effort=none`, 1.024 output tokens và 40 model/environment calls tối đa mỗi task. Server Modal chạy Ollama `0.34.4`. Model 19 GB được tải bằng Modal CPU function, xác minh và commit Volume trước task call; `/api/show` và một completion `print('READY')` kiểm kỹ thuật alias. Một yêu cầu tạo alias bằng schema API cũ trả 400, được sửa **trước** khi gọi task. Không tính đó là lỗi task.

## Số liệu cuối cùng

| Train task | Exact success | State-check | Model calls | Environment steps | Input tokens | Output tokens |
|---|---:|---:|---:|---:|---:|---:|
| `60d0b5b_2` | 0 | 0/7 | 40 | 39 | 185.205 | 2.232 |
| `3c13f5a_1` | 0 | 1/6 | 40 | 39 | 184.091 | 1.701 |
| `ccb4494_2` | 0 | 4/5 | 12 | 12 | 40.805 | 500 |
| `e3d6c94_3` | 0 | 6/9 | 26 | 26 | 114.464 | 1.280 |
| `e85d92a_2` | 0 | 1/2 | 40 | 39 | 179.270 | 1.902 |
| `229360a_1` | 0 | 2/6 | 40 | 39 | 177.872 | 1.761 |
| **Tổng** | **0/6** | **14/35** | **198** | **194** | **881.707** | **9.376** |

Bốn task chạm trần 40 model calls; 39 environment steps là do lượt model cuối không tạo thêm môi trường action. Các task ở trần vẫn là **trajectory task hoàn chỉnh theo ngân sách**, không phải job bị ngắt. `14/35` chỉ là tổng check để đối soát, không phải AppWorld accuracy: một task cần toàn bộ check đúng. Usage tokens là số model trả trong JSONL; không có đo thời gian GPU đủ tin cậy để quy đổi thành chi phí hóa đơn. Số cuối đã được đối chiếu với 198 dòng `model_calls.jsonl`, sáu run JSON và protocol hash `abe401ebd2a8df2291c9157ede5a6e5cb41486b034b4ebe6b093e6bf9dfce779`.

## Chẩn đoán từ trajectory và check

- **Lặp tài liệu/API:** task `3c13f5a_1`, `e85d92a_2`, `229360a_1` có lần lượt **28, 21, 38** lời gọi `api_docs.show_api_doc` trong code trajectory; task cuối chỉ có năm đoạn code khác nhau trong 39 bước. Cả ba chạm trần và không có `complete_task()`. Đây là bằng chứng trực tiếp của vòng lặp khám phá API trong cấu hình agent/model này. Task `60d0b5b_2` cũng chạm trần, thử các API đọc/tìm nhiều lần và không hoàn tất. Không thể khẳng định vòng lặp do riêng model, riêng prompt hay cắt history nếu chưa có can thiệp đối chứng.
- **Sai tập kết quả dù gần hoàn tất:** `ccb4494_2` có lời gọi `complete_task()` nhưng state-check còn sai tập đối tượng được tác động (4/5 check). `e3d6c94_3` cũng có `complete_task()` nhưng ba check liên quan đến thành viên/tập chính xác của kết quả bị sai (6/9). Trạng thái cuối, chứ không phải lời agent, quyết định task success. Hai lỗi này củng cố giả thuyết cần kiểm tra scope/set semantics, nhưng không chứng minh một verifier sẽ tăng điểm.
- **Định dạng và hạ tầng:** completion không thuộc task trả code hợp lệ; các task thật có model call, environment steps và state-check. Không có bằng chứng các thất bại trên là do server 503 hoặc lỗi load model. Một preflight 503 thoáng qua trước download đã hồi phục; không tính vào bảng. Bốn lần chạm cap và các vòng lặp là lỗi outcome trong protocol đã khóa.

## Quyết định gate và ý nghĩa bài báo

Gate khóa trước yêu cầu GLM `≥2/6` exact success để chạy Qwen3-Coder paired control trên cùng sáu ID. Kết quả **0/6**, nên **dừng nhánh này và không chạy control**. Đây là quyết định tiết kiệm compute đã quy định trước, không chọn baseline sau khi xem kết quả. Không dùng v9 để claim GLM kém Coder trên phân phối AppWorld: Coder v8 là **sáu ID khác**, chưa có so sánh ghép cặp. Tương tự, 0/6 không chứng minh GLM bất lực với mọi scaffold; nó chỉ bác bỏ ứng viên GLM + legacy ReAct + budget hiện tại làm pool reputation trong sample này.

Đối với mục tiêu bài phương pháp, v8 có task success nhưng không có bổ trợ; v9 thử model khác nhưng trượt gate năng lực. Vì vậy chưa có pool AppWorld đủ để đánh giá DART/HistRepEval trên quyết định chọn agent, càng chưa có bằng chứng method vượt baseline. Bước tiếp có giá trị là **đổi cơ chế agent/scaffold hoặc môi trường**, thay vì tiếp tục thay model trong cùng legacy ReAct. Một AppWorld 0.2 simplified agent cần data/agent/evaluator đúng phiên bản và protocol riêng; phiên bản 0.2 trên GitHub hiện chưa là bản PyPI đang cài, nên không gộp số v1–v9. Trên MMLU-Pro đã có pool output thật, cần kiểm tra decision value vượt fallback/audit-only ở chi phí tương đương, cộng thêm môi trường tương tác thứ hai trước claim hội nghị mạnh. Không mở sealed holdout để chữa pilot âm.

**Artifact nội bộ:** `results/appworld_external_v1/train_pilot_v9_glm/{manifest.json,evaluation.json,model_calls.jsonl,runs/}` và runner logs (Git-ignored). Báo cáo public chỉ chứa số tổng và chẩn đoán mức phương pháp; không phân phối raw AppWorld protected data.
