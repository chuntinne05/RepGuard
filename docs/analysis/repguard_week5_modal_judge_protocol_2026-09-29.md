# Week 5 — giao thức judge thật trên Modal

**Ngày khóa:** 29/09/2026. Mục tiêu là đo chất lượng feedback do một mô hình thật tạo ra, rồi mới đánh giá việc dùng feedback đó trong HistRepEval/ECRT. Lượt thử Google Gemini trước đó dừng vì API chập chờn và timeout; hai judgment Gemini đã lưu riêng để chẩn đoán, không trộn vào thí nghiệm Modal và không dùng để kết luận.

## Dữ liệu và tách nhãn

- Chọn trước từ history calibration Week 3 bằng seed 1618033: **20 câu/môn × 14 môn = 280 câu**. Mẫu này không chọn dựa trên đáp án đúng/sai.
- Dùng bốn đáp án agent thật ở `results/real_week3_json_v1/predictions.jsonl`. Các agent nộp cùng đáp án trên một câu chia sẻ một case `(task_id, candidate_answer)`. Manifest dự kiến **694 case** cho tối đa **1.120 quan sát agent–câu** sau khi mở rộng. Cần báo rõ hai mẫu số.
- Judge chỉ thấy câu hỏi, lựa chọn và một đáp án được nộp. `to_online_view()` loại gold và metadata nhãn. Prompt không có tên agent. Gold chỉ được đọc trong script phân tích sau khi phản hồi đã ghi vào ledger.

## Mô hình và cấu hình

- Server: Ollama trên endpoint Modal của dự án. Mô hình judge: `qwen3:14b`, tách với bốn model agent Week 3 về trọng số và kích thước. Manifest lưu digest mô hình từ `/api/tags` và phiên bản Ollama từ `/api/version`, không chỉ alias.
- `think=false`, temperature 0, top-p 1, tối đa 256 token, JSON schema gồm `verdict` boolean, `chosen_letter` thuộc lựa chọn hợp lệ, `confidence` trong [0,1]. Không thay mô hình hay prompt khi tiếp tục cùng manifest.
- Đây là **judge cùng họ Qwen** với agent `qwen3:8b` và `qwen3:0.6b`. Do đó phép đo không được diễn giải là hoàn toàn độc lập về kiến trúc. Báo độ nhạy theo agent, đặc biệt Qwen so với Gemma/Llama. Nếu cần claim mạnh về judge độc lập, chạy thêm một judge khác họ trên Modal theo manifest riêng.

## Thu thập và kiểm tra

`run_real_week5_modal_judge.py` tạo manifest trước; chỉ `--collect` mới gọi mô hình. Ledger JSONL append-only và resume theo protocol hash. Chạy pilot 1 câu/môn, sau đó 5 rồi 20 câu/môn nếu JSON và độ trễ chấp nhận được. **Không chạy judge đồng thời với lượt Qwen3 8B thinking lớn đang dùng cùng Tesla T4**, vì tranh GPU làm hỏng phép đo độ trễ và có thể gây lỗi bộ nhớ.

`analyze_real_week5_modal_judge.py` kiểm tra duplicate, protocol hash, prompt hash, digest, raw JSON, lỗi schema và mâu thuẫn giữa verdict và lựa chọn của judge. So verdict với correctness thật ở bước phân tích offline; báo TP/FP/TN/FN, accuracy, false positive, false negative, theo môn và theo agent. Khoảng tin cậy bootstrap gom theo **câu hỏi** vì nhiều đáp án agent của cùng câu không độc lập.

## Gate khoa học

Chỉ đưa feedback vào HistRepEval khi judge đủ chính xác và lỗi có thể định lượng. Sau đó đánh giá ECRT, FixedBorrow, SkillConditioned và ablation trên cùng câu trả lời agent thật, tách calibration khỏi kiểm tra xác nhận. Nếu judge sai có cấu trúc, nghiên cứu cách hiệu chỉnh feedback; nếu không cải thiện routing/utility so với baseline, báo kết quả âm trung thực. Kết quả Week 3 test đã dùng để khám phá nên không dùng lại làm xác nhận cuối.
