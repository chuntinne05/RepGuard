# AppWorld v6: kết quả scaffold verification trên train ID mới

**Ngày:** 02/10/2026. **Trạng thái:** 6/6 trajectory thật hoàn tất; 6/6 official AppWorld state-check đã chạy, mỗi cell trong một Python process mới. Runner thoát mã 0. Dữ liệu raw và task-derived nằm tại `results/appworld_external_v1/train_pilot_v6/` (Git ignore). Protocol, task ID, ngân sách và điều kiện dừng đã được khóa trong `histrepeval_appworld_v6_scaffold_protocol_2026-10-02.md` và commit `db8bfbf` **trước** model call đầu.

## Câu hỏi và thiết kế

V4 direct Qwen3 32B đạt 1/3, v5 thinking/ngân sách lớn đạt 0/3 trên cùng ba train ID cũ. V6 hỏi liệu thêm chỉ dẫn **kiểm tra hậu điều kiện bằng read APIs trước khi hoàn tất** có cải thiện agent direct trên ba train ID **mới** hay không. Control dùng prompt v4; treatment thêm một đoạn verification chung. Cả hai cùng model digest `030ee887880fc378860c2dd35101da424377520441ae4bfe7be6deff8ade7840`, `think=false`, `num_ctx=8192`, output cap 1.024, temperature 0, tối đa 40 bước, lịch sử năm lượt gần nhất, cùng Ollama streaming và Modal L4. V6 control **không phải** v4 cell cũ, vì context và transport đổi đồng thời so với v4. Model process mở task với `load_ground_truth=False`.

AppWorld có [state-based evaluator và ReAct agent tham chiếu riêng](https://github.com/StonyBrookNLP/appworld); v6 là **custom-harness train pilot**, không phải leaderboard/official-agent baseline score. Prompt thêm các nguyên tắc chung có trong [prompt ReAct chính thức](https://github.com/StonyBrookNLP/appworld/blob/main/experiments/prompts/react_code_agent/instructions.txt), nhưng không sao chép toàn bộ agent hay cấu hình chính thức.

## Kết quả state-check chính thức

| Train ID | Control | Verified | Bước control→verified | Output token control→verified | Kết quả ghép cặp |
|---|---:|---:|---:|---:|---|
| `34d9492_2` | 4/5, fail | 4/5, fail | 24→34 | 1.615→3.033 | Cùng fail |
| `b0a8eae_2` | 0/5, fail | 0/5, fail | 28→40 | 1.045→2.541 | Cùng fail |
| `76f2c72_1` | 1/2, fail | 1/2, fail | 11→6 | 748→251 | Cùng fail |
| **Tổng** | **0/3 task success** | **0/3 task success** | **63→80** | **3.408→5.825 (1,71×)** | **0 rescue, 0 control-only** |

Input token cộng dồn 122.118→198.137 (1,62×). Tổng checks 5/12 ở mỗi policy, nhưng **không** dùng tổng checks như success rate vì task có mẫu số và điều kiện khác nhau. `complete_task` được gọi ở task thứ nhất và thứ ba của cả hai; task thứ hai không gọi. Ở task thứ ba, verified gọi `complete_task(status='fail')`, vì vậy cờ `completed_task_api=true` **không** là bằng chứng thành công. `evaluation.json` và `paired.json` là bảng đối chiếu local, được tạo từ các trajectory thật.

## Cơ chế lỗi quan sát được

- **ID thứ nhất, file-system:** Cả hai tới 4/5 checks rồi fail. Control có 10/24 và verified 17/34 tool output chứa `Traceback` hoặc `Error:`; verified nhiều lần gặp lỗi access token/API, rồi gọi hoàn tất sau các lượt di chuyển file và đọc lại trạng thái. Chỉ dẫn verification tạo thêm read attempts nhưng không sửa điều kiện còn thiếu. Đếm lỗi này là phép lọc chuỗi trên tool output, có thể bỏ sót các failure response không chứa hai chuỗi đó.
- **ID thứ hai, multi-app:** Control lặp các thao tác đăng nhập/search Simple Note và dừng ở 28 bước sau tám exact-code repeats; verified đọc thêm API docs, truy cập Simple Note rồi Spotify, nhưng hết 40 bước trước khi hoàn tất. Hai bản đều 0/5 checks. Đây là ví dụ rõ rằng tăng độ dài tương tác và khám phá thêm app chưa đủ để chuyển thành task success.
- **ID thứ ba, file answer:** Control đọc nhiều file rồi gửi một answer nhưng chỉ 1/2 checks. Verified gặp ba tool output lỗi trong sáu bước, không đọc được nội dung cần thiết và gọi `complete_task(status='fail')`; cũng 1/2. Chỉ dẫn “không đoán” có thể khuyến khích thoát sớm trong một failure mode, nhưng một task không đủ để xác nhận quan hệ nhân quả.

Tổng số tool output chứa `Traceback` hoặc `Error:` là 21 control và 31 verified; exact-code repeats tương ứng 10 và 9. Không tính các lượt bị chặn lặp như tương tác AppWorld mới. Những số này mô tả trajectory, không phải metric chất lượng chuẩn của benchmark.

## Diễn giải và gate

V6 có 3 cặp train-visible, không đủ để ước lượng hiệu quả tổng quát hoặc kiểm định ý nghĩa thống kê. Dù inference budget bằng nhau, prompt thêm verification có thể đổi hành vi model theo nhiều cách; số token thực tế không được giữ bằng nhau, nên so sánh là **equal-cap, không phải cost-matched**. Thứ tự control→verified không random và chỉ có một run mỗi cell. Không có bằng chứng treatment cứu task, và chi phí quan sát tăng. **Dừng nhánh “chỉ thêm lời nhắc verification” như một sửa chữa độc lập**, không tiếp tục tinh chỉnh trên ba ID này và không mở sealed holdout.

Nút thắt hiện tại là **năng lực agent nền**: sử dụng API đúng, duy trì trạng thái/credentials, tránh loop, xử lý tác vụ nhiều app và xác minh điều kiện hoàn tất. Bước hợp lý tiếp theo là dựng hoặc cấu hình [simplified ReAct agent chính thức của AppWorld](https://github.com/StonyBrookNLP/appworld) với một model tương thích, rồi kiểm trên train ID mới theo một protocol khóa trước, so với custom direct ở cùng ngân sách. Nếu vẫn không có đủ task success và ca bổ trợ lẫn nhau, không chạy DART/reputation trên pool tương tác yếu. HistRepEval có thể tiếp tục như protocol đo giá trị của history/feedback với kết quả âm và baseline mạnh; để thành bài A*, vẫn cần môi trường thứ hai, pool có năng lực, can thiệp lịch sử có kiểm soát, external replication và metric decision value, chứ v6 không cung cấp chứng cứ đó.
