# Vận hành FinQA feedback pilot

- App: `repguard-routerbench-finqa-feedback-v1`.
- Run: `0fad63edd346eb0591fd99e1`.
- Detached FunctionCall: `fc-01M48K3QDX793BH81MBF02JM10`.
- Volume pilot: `repguard-routerbench-finqa-feedback-v1`.
- Archive Volume: `repguard-routerbench-intake-checkpoints-v1`.
- GPU model Volume: `ollama-models`.
- Scientific source/protocol commit: `a49d4d8`, push `dev` trước submit.
- 48 câu FinQA development ×20 model =960 genuine Qwen3-14B judgments;
  tối đa2initiated attempts/case, không có solver execution mới.

App deploy rồi submit bằng `.spawn()`. CPU worker trên Modal chuẩn bị input,
chờ GPU rồi tính analysis. Máy local ngủ hoặc Codex session kết thúc không hủy
FunctionCall. CPU worker timeout24giờ, GPU4giờ, mỗi function tối đa2infra
retries; mỗi case giữ trần2attempts qua resume. Không submit song song khi
receipt cũ còn pending.

**Trạng thái cuối:** `completed_pilot_review_required` lúc
`2026-10-06T13:43:29.177440+00:00`. Input **960/960**, boxed answer hoàn chỉnh
**889/960 (92,60%)**. GPU NVIDIA L4, digest Qwen3-14B khớp,
`archive_mounted=false`. Ledger/checksum local **960/960**, response hợp lệ
**960/960**, đúng **960 attempt**, không retry. Operational gate PASS;
expansion screening FAIL. Pair residual-variance ratio **1,045407**,
CI95 **[1,019379; 1,073530]**. Xem báo cáo cuối và phân tích lỗi bên dưới;
không diễn giải snapshot 9→30 lúc đầu như trạng thái hiện tại.

Các lệnh kiểm tra và tải tăng dần:

```bash
.venv/bin/python run_routerbench_finqa_feedback.py status
.venv/bin/python fetch_routerbench_finqa_feedback.py
.venv/bin/python report_routerbench_finqa_feedback.py
.venv/bin/python report_routerbench_finqa_failure.py
```

`status.json` chỉ cập nhật mỗi10case; ledger và các case artifacts cập nhật
từng case. Chỉ gọi inference đang tiến triển khi ledger tăng và có response
đúng model, `done`, token usage, prompt hash. Reporter chỉ chạy khi state
`completed_pilot_review_required` và đủ960cases; nó tính lại analysis/CI,
usage, response probabilities và so với cloud. Không đưa raw prompt, output,
gold hoặc checkpoints private vào Git.

Nếu call kết thúc `pipeline_failed`, đọc logs/error và receipt, sửa nguyên nhân
trước khi resume; không tự gọi submit mới chỉ vì không thấy container. `submit
--resume` trong CLI chỉ cho phép khi cloud xác nhận failure. Run tự dừng sau
pilot theo protocol, kể cả gate PASS. Không mở final test hay mua thêm judgment
trước protocol mới.

[Protocol](routerbench_finqa_feedback_v1_protocol_2026-10-06.md) ·
[Headroom development](routerbench_headroom_v1_assessment_2026-10-06.md) ·
[Verified pilot](routerbench_finqa_feedback_v1_assessment_2026-10-06.md) ·
[Failure analysis](routerbench_finqa_feedback_v1_interpretation_2026-10-06.md)
