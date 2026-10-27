# Vận hành sparse-gold development replay

- App và Volume: `repguard-routerbench-sparse-v1`.
- Run đã khóa: `a4c73220bc917a52700300d0`.
- Detached FunctionCall: `fc-01M47DSWD7RNTBQ9QXY7D1KZNN`.
- Source/protocol freeze commit: `282816f`, đã push `dev` trước submit.
- 240 case: 3 budgets × 4 outer folds × 20 seeds; 10 methods/case.
- Modal CPU 1 core, RAM 2 GiB, timeout 1 giờ, 2 infrastructure retries,
  tối đa 1 worker container; **không khởi động GPU/solver/judge**.

Worker được deploy rồi submit bằng `.spawn()`. Laptop hoặc Codex session không
giữ vòng đời công việc. Mỗi case và ledger lưu atomically trên Modal Volume;
worker retry/resume kiểm tra identity/checksum và bỏ qua case đã hoàn tất.
Đây là replay trên artifacts thật đã có, không phải execution solver mới hay
nhãn con người mới mua. Các pipeline và holdout cũ không bị thay đổi.

## Kiểm tra và lấy kết quả

```bash
.venv/bin/python run_routerbench_sparse.py status
.venv/bin/python run_routerbench_sparse.py fetch
.venv/bin/python report_routerbench_sparse.py
```

Chỉ dùng `prepare` để tạo packet chưa có, và `submit` cho packet đã khóa.
Lệnh submit có receipt guard: nếu call còn pending thì không tạo call thứ hai.
Chỉ `--resume` sau khi call cũ đã thất bại và checkpoint xác nhận
`pipeline_failed`; không submit lại vì laptop sleep hoặc chưa thấy stdout.

Status: `replaying` → `analyzing` → `completed_development_review_required`.
`pipeline_failed` phải đọc error trước khi tiếp tục. Một process/container còn
tồn tại không đủ chứng minh tiến triển: đọc ledger, xác nhận số case artifact
tăng và checksum đúng. Có thể dùng SDK `Volume.read_file` cho
`/runs/a4c73220bc917a52700300d0/status.json` và `ledger.json` để kiểm tra mà
không cold-start reader function.

Reporter chỉ chốt khi đủ 240 case và worker terminal. Kiểm tra parent 288
judgments, source/input hashes, mọi case/ledger checksum; chạy lại toàn bộ
2.400 lựa chọn, audit paths, diagnostic predictions, bootstrap và gate. Raw
labels/probabilities/checkpoints chỉ lưu private dưới `results/`.

Gate PASS hay FAIL đều dừng sau batch; không tự mua thêm judgment. Study này
vẫn là development đã quan sát, không phải independent final evaluation.
28 targeted tests đạt trước submit, gồm budget/leakage/cross-fit/resume và
cloud module import; summary diagnostics bổ sung cũng được kiểm tra lại.

## Trạng thái cuối

Hoàn tất **240/240 case, 2.400 lựa chọn model** lúc **08:42:46 ngày 06/10/2026**
giờ Việt Nam (`2026-10-06T01:42:46.838554+00:00`). FunctionCall đã trả thành công;
state `completed_development_review_required`. Development expansion gate
**FAIL**; đây là kết quả khoa học âm, không phải pipeline execution thất bại.

Các snapshot thực: ledger 36 → 134 → 203 → 240. Case 133 dùng đúng 22 cell cho
mỗi đường uniform/paired/IndependentSH/PairedSH, đủ 10 lựa chọn. Không gọi lại
solver/judge trong batch này. Đã dừng theo protocol; không mở rộng collection
hoặc thay candidate/budget để đổi kết quả gate.

[Protocol](routerbench_sparse_gold_v1_protocol_2026-10-06.md) ·
[Kế hoạch bằng chứng](routerbench_next_evidence_plan_2026-10-06.md) ·
[Báo cáo kết quả](routerbench_sparse_gold_v1_assessment_2026-10-06.md)
