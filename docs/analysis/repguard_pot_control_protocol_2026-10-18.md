# PoT arithmetic control — trước inference

18/10/2026. Thêm một control có căn cứ từ [PoT](https://arxiv.org/abs/2211.12588)
và [PAL](https://arxiv.org/abs/2211.10435), sau khi quan sát v1zero-rescue và
numeric-native có lỗi rounding/truncation. Chưa có output PoT mới khi viết.
Đây là adaptation dùng chương trình Python arithmetic với variable names,
không nhận là tái lập toàn bộ published protocol hay một method mới.

24calls, tất cả24development case của causal v1, không chọn riêng câu sai.
Qwen3:14b/digest cũ, L4, native thinking true, context16384, cap4096, seed18102026,
temperature0. Một lượt/câu; không quality retry; collector wall cap3600giây.
Tổng ba batch đợt này tối đa160calls:112causal+24native diagnostics+24PoT.
Chỉ deploy sau khi24native diagnostics hoàn tất; giữ các frozen snapshots.

Input là question, full table matrix, pre/post text, không có qa/program/target.
Output JSON reasoning/status/code; code straight-line gán`answer`. Bộ diễn
giải AST allowlist thực thi arithmetic, comparisons, lists/indexing có giới hạn, abs/sum/min/max/len/round;
không gọi Python exec/eval, không import/network/files/loops/attributes.
Boolean chuyển yes/no; số chỉ round cuối5decimals, giữ exact FinQA exe_ans.
Không chọn thang đo theo gold, không oracle tolerance hoặc factor100matching.

Đây là executable-answer baseline, **không tự kiểm chứng source binding**.
Không cap-matched với DSL1536nonthinking; native cap lớn hơn cần báo rõ.
Ghi input/output tokens, request seconds, capped/invalid outputs và scale.
Không gọi kết quả trên24development đã thấy là independent confirmation,
hay lấy thắng DSL yếu làm đóng góp reputation. Mục tiêu là xác lập baseline
generation/execution quen thuộc trước khi học chọn repair từ lịch sử.
