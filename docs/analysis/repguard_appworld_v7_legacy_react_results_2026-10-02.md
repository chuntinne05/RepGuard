# AppWorld v7: đối chứng ReAct legacy đúng phiên bản — kết quả thật và quyết định gate

**Ngày:** 02/10/2026. **Trạng thái:** 3/3 trajectory train thật hoàn tất, runner thoát mã 0; 3/3 state-check chính thức chạy trong tiến trình Python riêng. Protocol đã được khóa và push lên nhánh `dev` ở commit `e047613` **trước** khi gọi model trên task. Dữ liệu raw được Git ignore tại `results/appworld_external_v1/train_pilot_v7_legacy_react/`. Đây là kiểm tra *năng lực agent nền*, không phải kết quả DART, ECRT hay HistRepEval.

## 1. Vì sao cần v7 và thời gian đã dùng vào đâu

V4 Qwen3 32B direct trên scaffold tự viết giải được 1/3 train task; v5 bật thinking và tăng budget trên chính ba ID đó giải 0/3, dùng 10,47 lần output token. V6 trên ba ID mới thêm lời nhắc xác minh hậu điều kiện, được 0/3 ở cả control lẫn treatment, treatment dùng 1,71 lần output token. Trước khi quy lỗi cho riêng model hay phương pháp, cần thử agent ReAct **do AppWorld phát hành ở đúng phiên bản benchmark**.

Việc dựng đối chứng mất thời gian vì các mã không tương thích: các pilot/data hiện có dùng `appworld==0.1.3.post1`/Pydantic 1, còn `simplified_react_code_agent` hiện tại của AppWorld thuộc dòng 0.2/Pydantic 2. V7 dùng mã **legacy Recoma ReAct** từ tag `v0.1.3.post1` commit `66ad8099e12188ece0d3fe45e661dbc01880813b`, với môi trường dependency riêng (`recoma==0.0.4`, `litellm==1.37.19`). Package 0.1.3 trong môi trường mới phải giải nén apps bundle; lần chạy đầu dừng ở import trước khi gọi model. Một lần chạy task thứ hai gặp 401 từ Modal trước model call, rồi được khôi phục bằng xác thực mới. Hai lỗi kỹ thuật đó không được tính thành thất bại task. AppWorld 0.1.3 trong môi trường runner không giải nén test bundle vào cache ngoài workspace; state-check được thực hiện bằng môi trường evaluator 0.1.3 riêng đã kiểm chứng trước đó.

## 2. Protocol và ranh giới kết luận

- **Train ID mới, chọn trước:** `afc0fce_2`, `27e1026_2`, `6ea6792_2` (vị trí 10–12 của danh sách SHA-256 một task mỗi generator đã khóa từ trước). Không mở dev/test; không chọn task theo nội dung hoặc kết quả.
- **Model và budget:** Qwen3 32B Q4_K_M digest cha `030ee887880fc378860c2dd35101da424377520441ae4bfe7be6deff8ade7840`, alias Ollama `qwen3:32b-ctx8192` đã xác minh `num_ctx=8192`, direct (`reasoning_effort=none`), temperature 0, top_p 1, tối đa 1.024 output token/gọi và 40 model/environment calls/task. Agent giữ prompt, controller và Recoma search của legacy ReAct; adapter chỉ xử lý Modal auth/OpenAI transport, chặn đọc gold trong agent, và chuyển state-check sang tiến trình riêng.
- **Không phải bản tái lập chính thức của bài AppWorld:** config gốc dùng GPT-4o, 100 model calls và 400 output tokens/call. V7 đổi model và budget, nên gọi là *version-matched adapted legacy-agent reference*. V4–v6 chạy trên ID khác nên không suy ra hiệu ứng ghép cặp giữa scaffold từ tỉ lệ thành công của chúng.
- **Gold isolation:** runner mở task với `load_ground_truth=False` và assert không có gold. Mã ReAct gốc có đọc `required_apis` để chuẩn bị một biến template, nhưng template `react.txt` không hiển thị biến đó; v7 bỏ hẳn truy cập. Official answerer gốc gọi evaluator ngay trong agent; v7 lưu hành động rồi chấm riêng. Kết quả thành công dựa trên AppWorld state-check, không dựa vào lời agent hoặc `complete_task()`.

## 3. Kết quả chấm thật

| Task train | State-check | Task success | Model calls / REPL steps | Input tokens | Output tokens |
|---|---:|---:|---:|---:|---:|
| `afc0fce_2` | 7/9 | 0 | 11 / 11 | 45.375 | 1.267 |
| `27e1026_2` | 1/2 | 0 | 11 / 11 | 38.566 | 1.044 |
| `6ea6792_2` | 5/6 | 0 | 8 / 8 | 30.706 | 642 |
| **Tổng** | **13/17 checks** | **0/3 tasks** | **30 / 30** | **114.647** | **2.953** |

`13/17` chỉ là phép cộng check để kiểm số, **không phải accuracy benchmark**: check khác nhau về độ khó và số lượng giữa task. AppWorld task success yêu cầu toàn bộ điều kiện. Mỗi cell có một trajectory hoàn chỉnh; các lượt dừng do import/401 không phát sinh model response và không được đưa vào bảng. Bộ chấm là `evaluate_appworld_legacy_react_v7.py`, kết quả máy đọc ở `evaluation.json` (ignored).

## 4. Phân tích nguyên nhân trực tiếp từ trajectory và state-check

1. **Task Venmo bình luận/like:** yêu cầu tác động lên các khoản nhận từ *bạn bè* trong bảy ngày. Agent lấy giao dịch nhận theo thời gian rồi bình luận/like **toàn bộ 42 giao dịch tìm thấy**, không lọc quan hệ bạn bè; state-check yêu cầu chính xác **12 giao dịch**, cả 12 nằm trong 42. Hai check sai là tập ID đã like và tập ID đã bình luận. Đây là lỗi *scope/precision* có hậu quả phụ: **30 giao dịch ngoài tập mục tiêu** cũng bị tác động, dù 7/9 check còn lại đạt. Agent từng thử API không tồn tại và sửa tên tham số bình luận sau lỗi, nhưng hai sửa kỹ thuật đó không sửa tập mục tiêu. Mốc `datetime.now() - 7 ngày` cũng cần được kiểm tra cẩn thận với cụm “bảy ngày gồm hôm nay”; dữ liệu hiện tại chứng minh lỗi lọc bạn bè, chưa tách riêng tác động của biên ngày.
2. **Task Spotify hỏi bài hát phát hành mới nhất:** agent đọc thư viện bài hát, album và playlist, rồi lấy `added_at` của bài hát, `release_date` của album và `created_at` của playlist để so sánh trực tiếp. Nó chọn một tiêu đề khác đáp án state-check. Vấn đề quan sát được ở mã là **lẫn loại thực thể và thời gian**: ngày thêm bài vào thư viện/ ngày tạo playlist không phải ngày phát hành của bài hát, và tiêu đề album/playlist không phải tiêu đề bài hát được hỏi. Agent còn đặt trần cứng 10 trang mà không chứng minh đã hết dữ liệu. Không có đủ bằng chứng để quy riêng sai số cho thiếu trang; phép so sánh sai ngữ nghĩa đã rõ.
3. **Task Venmo từ chối yêu cầu thanh toán:** yêu cầu chỉ với request đang chờ từ *bạn bè và bạn cùng phòng*. Agent gọi một API sai tên, rồi chỉ đọc danh sách request nhận được ở lượt truy vấn, không dựng tập contact đủ điều kiện và không duyệt trang đầy đủ. Nó từ chối **1 request không thuộc tập mục tiêu**, trong khi **14 request cần từ chối đều bị bỏ sót**. Đây là lỗi *recall lẫn precision*, nặng hơn vẻ ngoài `5/6 checks` gợi ra. Agent dùng điều kiện `denied_at is None` ở lần lặp đầu nên còn có nguy cơ đụng request đã approved; lần lặp sau kiểm thêm `approved_at`, nhưng không sửa tập contact hay tìm toàn bộ request.

Ba trường hợp cho thấy điểm nghẽn không đơn thuần là model thiếu bước hoặc không chịu kiểm tra cuối. Lỗi nằm ở **dịch ràng buộc ngôn ngữ thành tập đối tượng chính xác** (quan hệ, thời gian, loại thực thể, tất cả các trang), và ở câu hỏi là **truy xuất đúng thuộc tính ngữ nghĩa**. Check đạt nhiều vẫn có thể che hành động dư thừa hoặc bỏ sót nghiêm trọng; do đó dùng task success và tập ID đúng/sai, không dùng partial-check score làm claim.

## 5. Quyết định nghiên cứu

Theo gate đã khóa, **dừng xây pool HistRepEval/DART trên Qwen3 32B + AppWorld 0.1.3 trong cấu hình hiện tại**. V7 0/3 chỉ là mẫu train có chủ đích rất nhỏ; nó không chứng minh mọi ReAct agent hay Qwen3 32B đều thất bại trên AppWorld, và không so sánh công bằng với v4–v6 do khác ID/scaffold. Nhưng nó không cung cấp hai agent có task success bổ trợ để nghiên cứu chọn agent theo reputation. Không mở dev/test hoặc dùng ba ID v7 để tinh chỉnh rồi báo hiệu quả xác nhận.

**Bước tiếp theo có giá trị nhất:** (a) giữ v7 làm chẩn đoán phát triển; (b) trước khi chạy thêm AppWorld lớn, chọn một solver mạnh hơn hoặc cài AppWorld 0.2 cùng data bundle và simplified agent *đúng phiên bản*, rồi khóa một capability sample train mới; chỉ tiếp tục nếu task success đủ nhiều và có ca bổ trợ giữa các agent; (c) thiết kế một *scope verifier* có thể kiểm tra, trước hành động hàng loạt, rằng agent đã duyệt hết trang, xác định quan hệ/contact, lập tập target ID từ đúng thuộc tính, và đối chiếu hậu điều kiện. So với baseline ReAct và thêm solver ở cùng ngân sách; lỗi v7 là giả thuyết thiết kế, **không phải bằng chứng verifier sẽ thắng**. Nếu gate năng lực vẫn trượt, đặt AppWorld như kết quả feasibility âm và phát triển HistRepEval trên pool/môi trường tương tác khác có năng lực thực.

Để thành bài hội nghị mạnh, HistRepEval cần chứng minh giá trị *quyết định* của lịch sử/feedback ở pool bổ trợ thật, với attack/judge provenance, chi phí audit, cứu/hại task, baseline mạnh và xác nhận môi trường thứ hai. DART cần tăng outcome ở cùng ngân sách, không chỉ tăng Brier hoặc điểm partial check. Hiện chưa có bằng chứng đó và không thể bảo đảm venue A*.

**Nguồn:** [mã AppWorld chính thức](https://github.com/StonyBrookNLP/appworld) mô tả state-based evaluator, split train/dev/test và nhiều agent scaffold; protocol khóa trước tại `appworld_legacy_react_v7_protocol_2026-10-02.md`, mã chạy `run_appworld_legacy_react_v7.py`, mã chấm `evaluate_appworld_legacy_react_v7.py`.
