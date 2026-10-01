# RepGuard follow-up: context 8K và AppWorld train pilot v2

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

Artefact raw và task-derived AppWorld nằm trong `results/` bị Git ignore. JSON kết quả: `results/real_dev_context_pilot_v1/analysis.json`, `results/appworld_external_v1/train_pilot_v2/evaluation.json`, `results/appworld_external_v1/train_pilot_v3/evaluation.json`.
