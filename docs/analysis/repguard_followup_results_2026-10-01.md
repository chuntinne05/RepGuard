# RepGuard follow-up: context 8K và AppWorld train pilots

**Chốt:** 01/10/2026, sau khi MMLU-Pro development pool 2.800/2.800 đã hoàn tất. Hai thí nghiệm dưới đây là chẩn đoán **development/train**, không dùng 420 sealed holdout và không tạo claim phương pháp DART.

## 1. Context 4K → 8K trên 70 câu ghép cặp

`run_real_dev_context_pilot.py` chọn trước năm development ID trong mỗi môn bằng hash, cùng Qwen3 8B model digest, prompt, `think=true`, temperature 0 và output cap 8.192; chỉ `num_ctx` đổi từ mặc định 4.096 sang 8.192. `analyze_real_dev_context_pilot.py` kiểm đủ 70 ID, digest, prompt hash và protocol trước khi chấm.

| Chỉ số | 4K | 8K | Chênh |
|---|---:|---:|---:|
| Đúng | 42/70 (60,00%) | 46/70 (65,71%) | +4 câu / +5,71 điểm |
| Output hợp lệ | 64/70 | 64/70 | 0 |
| Chạm cap độ dài | 6/70 | 6/70 | 0 |
| Output token | 158.161 | 157.284 | −877 |
| Tổng thời gian request | 4.387,76 s | 4.784,72 s | +396,96 s (+9,05%) |

Ghép cặp accuracy: **4 ca 8K cứu, 0 ca 8K hại**; 9 câu đổi answer. CI bootstrap lấy mẫu theo 14 môn do script ghi là **[+1,43; +10,00] điểm**, nhưng chỉ có bốn cặp accuracy bất đồng; kiểm định dấu hai phía chính xác cho 4 so 0 có **p=0,125**. Vì mẫu nhỏ, không xem CI bootstrap này là xác nhận mạnh. Validity chuyển 62 valid→valid, 2 valid→invalid, 2 invalid→valid, 4 invalid→invalid. **Tăng context không loại bỏ lỗi output bị cắt**, nên không thay thế fallback invalid của run 560 câu; tín hiệu accuracy cần xác nhận riêng nếu có giá trị nghiên cứu.

Máy người dùng sleep làm client giữ request treo sau 29/70 dù process còn tồn tại và container Modal đã scale về 0. Sau khi ngắt request treo, runner retry; một lượt gặp 503 lúc container warmup, lượt sau tạo bản ghi 30. Cuối cùng ledger đủ **70 ID duy nhất**, analyzer hoàn tất, và status `followup_complete`. Đây là sự cố hạ tầng đã khôi phục, không phải 41 câu được mô phỏng hoặc bỏ qua.

## 2. AppWorld train pilot v2

`run_appworld_train_pilot_v2.py` dùng Qwen3 14B direct, chat history gọn, 40 bước, chống chạy lại code giống hệt trên ba train task khác v1. Sau trajectory, `evaluate_appworld_train_pilot.py` dùng official state-check. Kết quả **0/3 task success**, cả ba chạm 40 bước và không gọi `complete_task`: passed checks lần lượt **1/7**, **1/8**, **2/8**. Đây là điểm của custom scaffold trên ba task train, không phải AppWorld official baseline hoặc so sánh phương pháp.

Phân tích trace cho thấy lỗi scaffold/model có thể quan sát trực tiếp: ở hai task, model liên tục đoán các tên `apis.supervisor.*` không tồn tại thay vì dùng `apis.api_docs`; ở task file, model gọi `os`, `shutil`, `zipfile` bị AppWorld cấm. Mỗi task chỉ có **4 code block khác nhau trong 40 bước** và **36 lần exact-duplicate code bị chặn**. Prompt v2 chỉ nói “find API documentation” nhưng không đưa cú pháp discovery cụ thể; đó là một thiếu sót của scaffold. V2 do vậy chưa đo năng lực của một agent AppWorld được thiết lập đúng, càng chưa kiểm định reputation/audit.

## 3. Quyết định kế tiếp

Một v3 đã khóa trước khi gọi model trên **cùng ba task train** để cô lập sửa scaffold: ví dụ `apis.api_docs` chính xác, cấm đường OS, năm lượt history gần nhất, dừng khi lặp code tám lần. Protocol ở `histrepeval_appworld_v3_scaffold_diagnostic_2026-10-01.md`. Do đã xem lỗi v2 trên chính các task này, mọi cải thiện v3 chỉ là kiểm tra sửa lỗi, **không** phải gain độc lập. Nếu vẫn không có API action hợp lệ, dừng local Qwen14 custom scaffold và thử official ReAct scaffold tương thích hoặc solver mạnh hơn trên train. Chỉ mở paired method experiment khi agent có task success và lỗi bổ trợ thực.

**Kết quả v3 task đầu (train, cùng ID với v2):** `692c77d_2` dùng `apis.api_docs` đúng ở các bước đầu, nhưng sau đó lặp tra tài liệu/đoán tên API không tồn tại. Trajectory dừng ở **17 bước**, **9 code block duy nhất**, **8 lần duplicate bị chặn**, không gọi `complete_task`; official state-check **1/7 checks, task success = false**. Theo gate v3 đã khóa, hai task v3 còn lại **không chạy** để tránh tốn compute vào một scaffold vẫn lặp vô ích. Đây là quyết định về khả thi của local Qwen14 scaffold, không phải kết quả paired task-success hay bằng chứng phương pháp không thể hoạt động. Hướng kỹ thuật tiếp theo là kiểm tra scaffold ReAct official tương thích (prompt nhiều ví dụ, tới 100 LLM calls) hoặc dùng solver mạnh hơn trên train; cần giữ nhãn custom nếu thay đổi official config.

## 4. AppWorld train solver-capability pilot v4

Qwen3 32B Q4_K_M được tải thật vào Modal volume và chạy trên L4; endpoint Ollama 0.34.4, digest `030ee887880fc378860c2dd35101da424377520441ae4bfe7be6deff8ade7840`. V4 giữ scaffold v3, temperature 0, output cap 1.024, `num_ctx=4096`, 40 bước và cùng ba train ID để chẩn đoán đổi solver. Manifest protocol hash: `bffa22562140a9a932c282b09535610c6890b87fad1dd536b11d195eae60544d`. Đây vẫn là custom harness và train-visible task set.

| Train ID | State-check | Bước | `complete_task` | Code duy nhất | Repeat chặn | Output token |
|---|---:|---:|---|---:|---:|---:|
| `692c77d_2` | 2/7, fail | 29 | Có | 24 | 5 | 3.008 |
| `29caf6f_1` | 2/8, fail | 35 | Có | 34 | 1 | 2.545 |
| `7d7fbf6_1` | **8/8, success** | 25 | Có | 23 | 2 | 1.631 |

**Task success = 1/3.** Trên task `file_system` thành công, model dùng API ứng dụng thật thay vì import OS; đây là dấu hiệu base-agent capability có thể phục hồi bằng solver mạnh hơn. Hai task thất bại vẫn có nhiều lỗi thực thi: task Spotify dùng sai giá trị access token dẫn tới HTTP 401 khi gọi API, và task Simple Note chỉ qua 2/8 checks dù đã đánh dấu hoàn tất. Vì code nhiều bước có thể chứa lỗi dây chuyền, `complete_task=true` không được tính là thành công; official state-check mới là outcome.

V4 là **smoke test n=3**, không xác nhận tỷ lệ thành công tổng quát, không cho thấy hai policy có lỗi bổ trợ (Qwen14 v2 cùng ba task là 0/3), và không đo reputation/audit. Gate tiếp theo cần một tập train lớn hơn và ít nhất hai policy mạnh với các ca *mỗi policy cứu được task mà policy kia trượt*, rồi mới xây history/feedback. Không mở dev/test để chọn model hoặc prompt từ ba task này.

Artefact raw và task-derived AppWorld nằm trong `results/` bị Git ignore. JSON kết quả: `results/real_dev_context_pilot_v1/analysis.json`, `results/appworld_external_v1/train_pilot_v2/evaluation.json`, `results/appworld_external_v1/train_pilot_v3/evaluation.json`, `results/appworld_external_v1/train_pilot_v4/evaluation.json`.

## 5. AppWorld v5 Qwen3 32B thinking: kết quả cuối 02/10/2026

V5 dùng cùng Qwen3 32B model digest, scaffold và ba train ID của v4, nhưng bật `think=true`, nâng output cap 1.024→4.096 và context 4.096→8.192. Đây là so sánh **hai chính sách suy luận/ngân sách**, không phải ablation cô lập cờ thinking. Protocol được khóa trước các lệnh gọi ở `histrepeval_appworld_v5_thinking_protocol_2026-10-02.md`. Sau task đầu, do thinking đăng nhập được vào Spotify nhưng dừng sai khi chọn API, gate cho phép chạy tiếp hai task còn lại. Mỗi cell bên dưới đã được chấm lại bằng official AppWorld state-check **trong Python process riêng** để tránh cache state giữa các experiment.

| Train ID | V4 direct | V5 thinking | Bước direct→thinking | Output token direct→thinking |
|---|---:|---:|---:|---:|
| `692c77d_2` | 2/7 fail | 2/7 fail | 29→17 | 3.008→16.561 |
| `29caf6f_1` | 2/8 fail | 1/8 fail | 35→15 | 2.545→11.965 |
| `7d7fbf6_1` | **8/8 success** | **3/8 fail** | 25→30 | 1.631→46.724 |
| **Tổng** | **1/3 success** | **0/3 success** | **89→62 bước** | **7.184→75.250 (10,47×)** |

Paired task success: **2 task cùng fail; 1 task chỉ direct giải được; 0 task chỉ thinking giải được**. Ba train task nhỏ và đã nhìn thấy ở v4, nên không dùng chênh lệch 1/3→0/3 để suy ra hiệu quả tổng quát hay kiểm định thống kê. Thinking dùng ít bước hơn tổng cộng, nhưng output token tăng 68.066; vì token sinh chậm hơn token prompt, đây là tín hiệu chi phí nghiêm trọng, dù không có bảng giá GPU/đô la được đo trong experiment. Tổng input token 187.380→125.689, do ít bước hơn. Hai policy có budget khác nhau, nên không quy toàn bộ thất bại cho cờ thinking.

**Phân tích lỗi trực tiếp.** V5 task Spotify dùng được token login và truy xuất playlist, nhưng kết luận sai rằng không có API cần thiết rồi gọi `complete_task` khi nhiệm vụ chưa xong. Task Simple Note đăng nhập và đọc note, nhưng answer cuối không qua official checks. Task file (`7d7fbf6_1`) có 18/30 bước trả execution error, một lượt không có code vì chạm output cap 4.096 và sau nhiều lần dò `compress_directory` vẫn **không tạo/xóa bất kỳ record file hoặc thư mục nào**. Official state-check 3/8 của nó chủ yếu là các điều kiện về câu trả lời và không cập nhật record thừa; năm checks cần thay đổi trạng thái đều fail. V4 direct trên chính task file đã tạo đúng zip và xóa thư mục gốc (8/8). Vì vậy `complete_task=true` của v5 không chứng minh agent hoàn tất công việc.

**Hạ tầng và tính kiểm toán.** Attempt đầu của task file đạt 20 tương tác AppWorld rồi hai request dài bị HTTP 500 sau khoảng 5 phút 38 giây; Modal báo server draining và thay container. Attempt streaming đầu có hai tương tác rồi client kẹt ở SSL read sau khi server đóng tunnel; parser đã được sửa để dừng ở `done=true` và đặt read timeout 120 giây. Cả hai partial attempt được lưu riêng trong `results/appworld_external_v1/train_pilot_v5/aborted_*` và **không tính điểm**. Trajectory cuối là replay từ state đầu, 30 bước, dùng Ollama NDJSON stream; hai task đầu dùng non-streaming. Autoscaler L4 được tăng trực tiếp từ 300 lên 1.200 giây trong khi replay chạy để tránh container drain ở response dài. Những thay đổi transport/hạ tầng và thời điểm can thiệp được ghi ở `histrepeval_appworld_v5_transport_addendum_2026-10-02.md`; đây là lý do v5 chỉ là feasibility diagnostic, không phải điểm benchmark chuẩn. Không có ground truth trong model process.

**Gate:** Không có ca thinking rescue direct, và thinking fail task duy nhất direct giải được với 28,65× output token trên task đó. **Dừng nhánh Qwen32 direct/thinking làm pool bổ trợ cho DART trên ba ID này.** Bước tiếp theo là sửa vòng lặp agent dựa trên lỗi API/postcondition ở train, kiểm trên train ID **mới** với baseline cùng ngân sách; chỉ mở thí nghiệm reputation/audit khi thấy ít nhất hai policy mạnh có ca cứu lẫn nhau. Không mở sealed holdout cho một phương pháp chưa qua gate. Artefact kết quả local: `results/appworld_external_v1/train_pilot_v5/evaluation.json` và `paired_v4_v5.json` (Git ignore).
