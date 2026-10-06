# Vận hành pilot external judge

## Run và giới hạn

- App: `repguard-routerbench-pilot-v1`.
- Active run: `bad5a513bd5d227711eb1e0d`.
- Detached FunctionCall: `fc-01M478WXM5842B8CFNJEW6G4X5`.
- Pilot Volume: `repguard-routerbench-pilot-v1`.
- Archive Volume: `repguard-routerbench-intake-checkpoints-v1`.
- 48 development questions ×6 archived models =288 judgment cases; tối đa2attempts/case.
- Judge thật: Qwen3-14B, think=false, GPU L4 hoặc A10, context16.384.
- CPU orchestrator24h, GPU function4h; tối đa2 infrastructure retries, giữ giới hạn
 2attempts/case qua lần resume. Không có vòng tuning/chạy model vô hạn.

App được deploy trước, sau đó submit bằng `.spawn()`. Laptop/Codex không giữ vòng
đời của run. CPU tự chuẩn bị input, chờ GPU hoàn tất, đọc gold của đúng pilot và
tính analysis. Nếu laptop sleep, không khởi chạy lại chỉ vì terminal không còn.

## Pipeline state

1. `preparing_gold_blind_inputs`: kiểm tra archive hash và lấy query/output đã khóa;
   có thể chưa có GPU hay model response. Không gọi đây là đang suy luận.
2. `judging`: `completed_cases` tăng khi artifact hoàn tất đã lưu. Mỗi request có
   intent lưu trước dispatch; unknown usage sau crash vẫn tính vào giới hạn retry.
3. `judgments_completed`: đủ288cases; CPU đang chuyển sang phân tích.
4. `completed_pilot_review_required`: đã có `analysis.json` và gate. Dừng theo
   protocol, kể cả gate pass. Không tự mở test/holdout hoặc gọi thêm model.
5. `pipeline_failed`: đọc error, logs và receipt trước khi resume. Không submit
   song song khi FunctionCall cũ còn pending.

Một container tồn tại/Pending chưa chứng minh inference tiến triển. Kiểm tra
ledger tăng, response có token counts/done, timestamps và model digest khớp.

Snapshot ngày06/10/2026, khoảng07:18:35giờ Việt Nam: ledger đã tăng từ12 lên38
judgments hoàn tất; state `judging`. Case37 có5.255input tokens,11output tokens,
response hợp lệ từ `qwen3:14b`. GPU thực tế NVIDIA A10G, Ollama0.34.4, digest khớp.
Đây là ảnh chụp tiến độ, không phải kết quả cuối; dùng các lệnh bên dưới để xem mới nhất.

## Lệnh kiểm tra và kiểm chứng

```bash
.venv/bin/python run_routerbench_pilot.py status
.venv/bin/python fetch_routerbench_pilot.py
.venv/bin/python report_routerbench_pilot.py
```

`fetch_routerbench_pilot.py` tải tăng dần theo ledger với checksum; dùng được
trong khi đang chạy. Reporter chỉ sinh kết luận cuối khi đủ288cases và state
terminal; chạy lại calibration/CI và đối chiếu response probabilities, token logs,
development membership, prompt fields và source hashes. Không in raw answers/gold
ra chat hoặc đưa artifacts private vào Git.

Nếu reader function cold-start chậm, dùng SDK `Volume.read_file` cho
`/runs/<run_id>/status.json` và `ledger.json`; thao tác này không cần tạo GPU.
Nếu run đã hoàn tất, `FunctionCall.from_id(...).get(timeout=0)` xác nhận worker
đã trả thành công. Không gọi submit để tạo run mới khi chỉ cần xem tiến độ.

## Startup incident đã khắc phục

Run đầu `442db51a24b3f107551ac7b0`, call `fc-01M478GNSSNKRXC6RX6ZE515DT`, lỗi
`ModuleNotFoundError: ollama_modal_recovery` lúc import container: chưa có checkpoint
hoặc inference. Đã hủy call này, lưu packet/receipt/failure dưới
`results/routerbench_pilot_v1/failed_start_442db51a24b3f107551ac7b0/`.

Image declaration được đưa vào module deploy để tự đủ dependencies; thêm test
import chỉ với các file cloud. Manifest cũ/mới có mọi dữ liệu và scientific settings
giống nhau; chỉ source/run identity thay đổi. Bản sửa commit `1adc23a`.
13 targeted intake/pilot tests đạt, gồm chống gold leakage, bounded attempts,
resume/idempotence, archive integrity và container import.

## Giới hạn báo cáo

288 là số judgment dự kiến, không phải288solver executions mới. Candidate outputs
là execution từ archive. Gold là score evaluator đã lưu, chưa được pilot grade
lại. Phân tích dùng cross-fit với toàn gold của pilot, không phải thí nghiệm
routing gold-budget10%. Token/latency là usage ghi nhận; chưa phải hóa đơn USD.

[Protocol khoa học](routerbench_pilot_protocol_2026-10-06.md) ·
[Kết quả intake](routerbench_intake_assessment_2026-10-06.md).
