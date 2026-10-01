# RepGuard: hướng bài báo và các gate còn phải vượt (01/10/2026)

> **Cập nhật sau hai pilot:** Context 8K và AppWorld v2 đã hoàn tất; AppWorld v3 đã dừng sau một task train theo gate scaffold. Số và chẩn đoán cuối ở [`repguard_followup_results_2026-10-01.md`](repguard_followup_results_2026-10-01.md). Các bước dưới đây là tiêu chí nghiên cứu đã đặt ra, không còn là trạng thái đang chạy.

## Chẩn đoán dựa trên dữ liệu hiện có

Pool MMLU-Pro 560 câu mới đã đủ 2.800 đáp án thật. Qwen3 8B thinking đạt 372/560; quy tắc gọi Qwen3 14B khi output thinking invalid đạt 388/560 với 40 lời gọi bổ sung. Selector sau khi gọi cả hai model đạt 396/560 nhưng phải gọi Qwen14 ở cả 560 câu; router trước lời gọi đạt 388/560 với 172 lời gọi. Cả hai không qua gate đã khóa so fallback. Trên study audit 520 câu, AuditedECRT chống được can thiệp false-positive nhắm agent yếu so ECRT cũ, nhưng chưa thắng AuditOnly với CI trên 0 và vẫn kém Qwen14 đơn lẻ. Xem `repguard_dev_pool_complete_2026-10-01.md` để biết toàn bộ mẫu số, CI và giới hạn.

Đây là một kết quả nghiên cứu hữu ích: **ước lượng reputation tốt hơn chưa chắc tạo quyết định cuối tốt hơn**. Oracle thấy agent khác cứu được nhiều câu không có nghĩa một policy có thể nhận ra đúng câu cần cứu trước gold. Khi agent chính quá mạnh và các lỗi còn lại khó dự báo, history có thể trở thành tín hiệu yếu, chi phí và rủi ro poisoning lại tăng. Kết luận này chỉ áp dụng cho pool và protocol đã đo.

## Ranh giới novelty phải tôn trọng

- Routing theo chất lượng/chi phí đã có [RouteLLM](https://arxiv.org/abs/2406.18665), [CP-Router](https://ojs.aaai.org/index.php/AAAI/article/view/40589), và benchmark [LLMRouterBench](https://aclanthology.org/2026.findings-acl.1881/). Vì vậy gọi DART là “router mới” hoặc chỉ hơn always-thinking trên một tập MCQ là chưa đủ. LLMRouterBench cũng ghi nhận nhiều router không thắng baseline đơn giản một cách đáng tin; đây là lý do cần so trực tiếp với fallback invalid và đường accuracy–cost.
- [Budgeted Act-or-Defer](https://arxiv.org/abs/2606.29654) và [Share the Judge, Learn the Deferral](https://arxiv.org/abs/2607.27984) đã nghiên cứu risk budget, local reliability và deferral. Nếu đề xuất audit có ngân sách, cần chỉ rõ đóng góp riêng của **feedback lịch sử theo agent/skill/provenance** và chứng minh gain ngoài audit/deferral cùng ngân sách.
- [TRUST-Bench](https://arxiv.org/abs/2605.17453) và [Potemkin](https://aclanthology.org/2026.findings-acl.499/) đã nghiên cứu feedback/tool output không đáng tin trong agent tương tác. HistRepEval cần đo *lịch sử hiệu năng của các agent ảnh hưởng quyết định chọn agent ra sao*; không thể chỉ đổi tên tool poisoning thành reputation poisoning.
- [AppWorld](https://aclanthology.org/2024.acl-long.850/) cung cấp tác vụ API nhiều bước và state-check, nhưng pilot Qwen14 custom scaffold đầu tiên là 0/3 train task. Đây là kiểm tra khả thi, chưa là kết quả benchmark hay bằng chứng ủng hộ một phương pháp.

## Trục bài có bằng chứng mạnh nhất hiện giờ

**HistRepEval** có thể thành một protocol/benchmark về *giá trị quyết định của lịch sử reputation*, nếu hoàn thành ba phần: (1) ledger output thật, feedback provenance và can thiệp có kiểm soát; (2) nhiều môi trường/pool có bổ trợ agent rõ, gồm ít nhất một môi trường tương tác; (3) metric nối calibration với decision: số lần đổi chọn agent, rescue, harm, task success, cost, audit budget, attack degradation và CI ghép cặp. Benchmark card phải phân biệt gold audit, noisy judge feedback, feedback bị attack, và không phân phối dữ liệu AppWorld được bảo vệ.

Một bài **phương pháp** vẫn khả thi về mặt giả thuyết, nhưng chưa được xác nhận. Ứng viên hợp lý là chọn audit chủ động tại nơi feedback lịch sử có khả năng đổi hành động, giữ một phần audit ngẫu nhiên để phát hiện sai lệch có mục tiêu, và chỉ dùng history khi tín hiệu còn giá trị so audit-only. Đây là phác thảo để kiểm nghiệm; không được mô tả là DART đã thắng. Phải đo trên môi trường có agent thật sự chuyên môn bổ sung và so với strong single, invalid fallback, AuditOnly, fixed+audit, router chuẩn và cost-matched solver.

## Thứ tự công việc và tiêu chí dừng

1. **Đóng diagnostic 8K trên 70 development ID đã chọn trước.** So ghép cặp validity/accuracy với 4K và báo output token, request time. Nếu tăng context không cứu invalid hoặc gain CI còn mơ hồ, giữ fallback invalid như baseline thực dụng; không thay ngầm protocol 560 câu.
2. **Kết thúc AppWorld v2 train pilot đã khóa.** Chạy Qwen14 direct với chat history ngắn, chống lặp và 40 bước trên ba task train khác v1; chấm bằng official state-check sau trajectory. Nếu 0/3, phân loại lỗi (doc loop, auth, API, planning, completion, cap), rồi thử scaffold official tương thích hoặc solver mạnh hơn trên *train*; chưa mở dev/test.
3. **Gate pool tương tác.** Chỉ khi solver đạt task success trên train và có ít nhất hai policy tạo các ca cứu nhau, chạy paired pilot với cùng task ID/scaffold/budget. Đo khả năng dự báo lỗi trước hành động và ít nhất hai kiểu feedback (đáng tin, sai lệch) tách history/test. Không dùng oracle complementarity làm performance claim.
4. **Gate phương pháp.** Khóa method, hyperparameter, audit budget và baseline trước khi chấm dev mới. Yêu cầu lợi ích task success hoặc decision value có CI ghép cặp trên 0 so cả audit-only và baseline mạnh nhất ở chi phí so sánh được, cùng với robustness dưới attack. Nếu không qua, báo kết quả âm và dồn lực vào HistRepEval.
5. **Xác nhận và bài viết.** Chỉ một lần dùng sealed holdout cho policy đã khóa; bổ sung môi trường thứ hai, nhiều seed/task generator, ablation, sensitivity theo ngân sách/attack và code/data card tái lập. Một submission A* cần novelty rõ và replication ngoài MMLU-Pro; hiện chưa có cơ sở hứa chắc acceptance.

Hai pilot ở bước 1–2 được nối bằng `run_context_to_appworld.py`; `results/real_dev_context_pilot_v1/followup_status.json` là trạng thái điều phối, còn số bản ghi thực phải đọc `predictions.jsonl`. Không suy ra tiến độ chỉ từ sự tồn tại của process/container.
