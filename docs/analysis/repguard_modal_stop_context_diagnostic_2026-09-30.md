# Modal stop, bảo toàn ledger và diagnostic context thinking

**Thời điểm kiểm tra:** 30/09/2026 khoảng 16:10 UTC (23:10 Việt Nam). **Trạng thái:** pipeline phát triển dừng tại 376/560 lượt Qwen3 8B thinking; 4 policy direct đủ 560 mỗi policy. Không mở sealed holdout.

## Sự cố vận hành đã xác minh

`results/real_dev_pool_v1/status.json` ghi `pipeline_failed` ở 376/560 thinking, tổng 2.616/2.800. `analyze_real_dev_pool.py` kiểm ledger ở trạng thái partial: các row hiện có khớp manifest, không có duplicate. Hai lỗi request được lưu: Modal 401 lúc 14:09 UTC đã phục hồi và ledger tiếp tục tăng; HTTP 503 cho task `mmlu_pro_9111` lúc 16:04 UTC khiến collector dừng. Lần preflight retry kế tiếp cũng nhận 503, watchdog dừng sau ba lần không có row mới. Hai watcher hậu xử lý đã ghi trạng thái dừng vì nguồn thất bại; **không có selector/router score mới**.

Modal app list cho thấy `ollama-server` ở trạng thái `stopped`, 0 container. Modal app log ghi rõ `Stopping app - user stopped from dashboard` lúc **16:04:15 UTC**, sau đó kết thúc request và server. Vì đây là thao tác từ dashboard sau lệnh tiếp tục trước đó, cần xác nhận ý định hiện tại trước khi redeploy. Đường chạy lại an toàn là deploy đúng source hiện hành `~/modal-ollama/ollama_modal.py`, xác minh `/api/version`, các model digest trùng manifest `c3c50fdb9a95bcc2de290c37283585036ec490a0dcb0b7731f17173c77b8ec67`, rồi chạy lại `run_real_dev_pipeline.py` trên ledger append-only. Chỉ báo phục hồi khi row thứ 377 được ghi và qua validator; sau đó khởi động lại hai watcher hậu xử lý.

## Diagnostic context đã khóa trước kết quả 560

Log server cho thấy `n_ctx_slot = 4096` ở lượt thinking hiện tại, trong khi `num_predict = 8192`. Trong 376 row đã có, **33 invalid**, và cả 33 đều có `done_reason=length`, `output_tokens=8192`; đây là quan sát giao thức, **không phải kết luận rằng context 4K gây sai**. Tài liệu [Ollama context length](https://github.com/ollama/ollama/blob/main/docs/context-length.mdx) giải thích giới hạn context và ảnh hưởng bộ nhớ; [FAQ chính thức](https://github.com/ollama/ollama/blob/main/docs/faq.mdx) mô tả cách đặt `num_ctx` qua API.

`configs/real_dev_context_pilot_v1.json` đã chọn bằng SHA-256 đúng **5 ID phát triển mỗi 14 môn = 70**, trước khi đủ 560 outcome và không chọn theo correctness/invalid. `run_real_dev_context_pilot.py` giữ nguyên model digest, prompt, temperature, schema, think và giới hạn output 8.192; chỉ yêu cầu `num_ctx=8192`. `analyze_real_dev_context_pilot.py` sẽ ghép từng ID với run 4K, xác minh prompt hash/model digest, rồi báo valid rate, accuracy, rescue/harm, CI bootstrap theo môn và token/latency. Đây là **diagnostic trên development**, không thay run chính hoặc phép xác nhận sealed holdout. Chỉ chạy khi app được phép hoạt động trở lại và sau khi nguồn 560 hoàn tất, tránh tranh cùng T4.
