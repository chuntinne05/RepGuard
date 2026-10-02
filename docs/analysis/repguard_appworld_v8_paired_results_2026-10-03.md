# AppWorld v8: capability screen và đối chứng ghép cặp trên sáu train task

**Báo cáo:** 03/10/2026. **Thực nghiệm:** 02–03/10/2026. **Trạng thái:** hai nhánh đều có 6/6 trajectory thật, runner thoát mã 0, và 12/12 cell được chấm bằng AppWorld state-check. Đây là phép thử năng lực agent nền; **chưa phải thí nghiệm ECRT, DART hay HistRepEval**.

## Câu hỏi và protocol đã khóa

V7 cho thấy Qwen3 32B trên legacy Recoma ReAct đúng phiên bản AppWorld 0.1.3 giải 0/3 train task mới. V8 hỏi liệu đổi model sang Qwen3-Coder 30B, trong khi giữ agent và ngân sách, có tạo một solver tương tác đủ năng lực và có lỗi bổ trợ với Qwen3 32B hay không. Sáu train ID là vị trí 13–18 của quy tắc chọn SHA-256 một task mỗi generator: `cf6abd2_2`, `771d8fc_2`, `6104387_3`, `e7a10f8_3`, `82e2fac_2`, `aa8502b_2`. Chúng được cố định trước khi xem instruction/gold. Không mở dev/test hay sealed holdout.

Protocol Coder đã được push trước task call ở `493a2fc`; nhánh Qwen3 32B được kích hoạt bởi gate Coder `≥2/6` và cố định trước control task call ở `0f7fcbb`. Xem [`appworld_v8_coder_capability_protocol_2026-10-02.md`](appworld_v8_coder_capability_protocol_2026-10-02.md). Cả hai dùng AppWorld `0.1.3.post1`, source official legacy Recoma ReAct tag `v0.1.3.post1` với adapter gold-blind/transport như V7, context 8.192, temperature 0, top_p 1, trần 1.024 output tokens/lượt, tối đa 40 lượt model và môi trường/task, giới hạn lịch sử prompt 20.000 ký tự. Model chạy thật qua Ollama trên Modal; alias Qwen3-Coder 30B có digest `b51abbfa75725b89e9bedf9f38a28b57c44a8f1a37c6429def3cc648e6c0d918`, Qwen3 32B có digest `09629261f4ec92b3ffd142c8a45c0b9104423ad62bb9d9d43ce095197524cf27`. Parent digest và chi tiết xác minh nằm trong protocol. Cùng một deployment Modal dùng A10G theo log server.

Mỗi nhánh chạy một trajectory hoàn chỉnh trên mỗi ID, ở namespace AppWorld riêng. Agent không được nạp ground truth. Evaluator được gọi sau trajectory trong Python process riêng cho từng task; `success` yêu cầu **tất cả** check đúng. Một lỗi xác thực/khởi động trước task call trong phần chuẩn bị control được sửa rồi chạy lại, không tính là task failure. Lượt chấm tạm khi control vẫn chạy có token chưa hoàn chỉnh; toàn bộ bảng dưới đây lấy từ lần chấm lại **sau khi 6/6 task kết thúc**. Raw instruction, API log, database và output protected nằm dưới `results/` đã Git-ignore.

## Kết quả state-check cuối cùng

| Train task | Coder: success, checks | Qwen3 32B: success, checks | Coder calls | Qwen3 32B calls | Coder input/output tokens | Qwen3 32B input/output tokens |
|---|---:|---:|---:|---:|---:|---:|
| `cf6abd2_2` | 1, 8/8 | 1, 8/8 | 8 | 13 | 27.522 / 494 | 53.711 / 983 |
| `771d8fc_2` | 1, 6/6 | 1, 6/6 | 14 | 39 | 63.740 / 893 | 186.599 / 4.275 |
| `6104387_3` | 0, 7/10 | 0, 7/10 | 31 | 29 | 130.939 / 3.473 | 128.161 / 2.591 |
| `e7a10f8_3` | 1, 2/2 | 1, 2/2 | 9 | 8 | 32.165 / 1.159 | 25.307 / 890 |
| `82e2fac_2` | 0, 1/2 | 0, 1/2 | 18 | 7 | 70.694 / 1.652 | 21.853 / 548 |
| `aa8502b_2` | 0, 1/4 | 0, 3/4 | 40 | 9 | 158.392 / 2.943 | 31.589 / 885 |
| **Tổng** | **3/6; 25/32** | **3/6; 27/32** | **120** | **105** | **483.452 / 10.614** | **447.220 / 10.172** |

Các số token là usage trả về từ các model call đã ghi; đây là thước đo tài nguyên, **không phải tiền GPU**, vì runner chưa ghi thời gian GPU đủ để tính chi phí hóa đơn. Ở ba task **cùng thành công**, Coder cần 31 calls, 123.427 input và 2.546 output tokens; Qwen3 32B cần 60 calls, 265.617 input và 6.148 output tokens. Trên toàn sáu task, Qwen3 32B lại dùng ít calls/tokens hơn vì dừng sớm hơn ở hai task thất bại. Vì vậy không được kết luận một model rẻ hơn ở mọi tình huống từ tổng sáu task. Task `aa8502b_2` của Coder chạm trần 40 model calls (39 environment steps); đây là thất bại task đã chạy, không phải thiếu bản ghi. Các con số `25/32` và `27/32` chỉ kiểm tổng state-check, không phải metric task accuracy.

Ma trận ghép cặp trên cùng ID: **cả hai đúng 3, chỉ Coder đúng 0, chỉ Qwen3 32B đúng 0, cả hai sai 3**. Oracle chọn model tốt hơn cho mỗi task vẫn chỉ đạt **3/6** trên mẫu này. Coder và Qwen3 32B có cùng outcome nhị phân ở cả sáu task, dù đường đi và chi phí khác. Đây là bằng chứng trực tiếp rằng **cặp này chưa cung cấp opportunity về task success cho DART/HistRepEval** trong pilot. Sáu train task không đủ để khẳng định không tồn tại complementarity ngoài mẫu hoặc model nào có accuracy tổng thể cao hơn. Thứ tự chạy Coder rồi Qwen3 32B và trạng thái server cũng là yếu tố gây nhiễu tiềm năng; không có repeat seed hay cost-matched test. Mục đích v8 là gate khả thi, không ước lượng hiệu ứng bài báo.

## Vì sao ba task thất bại

Đọc trajectory và requirement của official state-check, chỉ rút ra các nguyên nhân có bằng chứng trực tiếp:

1. **`6104387_3`, xuất danh sách bài hát sang CSV:** hai agent hoàn thành một số bước tạo file và thao tác tài khoản nhưng đều sai ba check liên quan đến tập `song title → artist names` trong CSV: cả key và value không khớp yêu cầu. Trajectory Coder nhiều lần dựng tập bài hát từ library/album/playlist, đổi schema artist và thử sửa API file; Qwen3 32B cũng lặp qua nguồn bài hát và sửa cách ghi file. Lỗi còn lại nằm ở **nội dung/tập dữ liệu được xuất**, nên việc `complete_task()` hoặc tạo được file không đủ. Chưa thể quy chính xác phần sai cho pagination, nguồn bài hát hay format CSV nếu chưa đối chiếu từng dòng với target; tránh phát biểu nguyên nhân cụ thể hơn state-check cho phép.
2. **`82e2fac_2`, trả lời bài hát ít lượt nghe:** cả hai sai check câu trả lời. Qwen3 32B dùng `song.get('play_count', 0)` trên song-library record rồi lấy `min`, nên nếu trường đó không chứa lượt nghe đúng ngữ nghĩa, giá trị mặc định 0 có thể làm sai thứ tự; đây là **rủi ro thấy trực tiếp trong code**, không phải chứng minh riêng trường đó đã thiếu ở tất cả record. Coder thử tra API private/playlist rồi trả một tên khác; trajectory không chứng minh nó đã thu thập đúng toàn bộ play count. Lỗi quan sát được là câu trả lời cuối sai.
3. **`aa8502b_2`, xử lý artist followings theo liked songs:** Coder lặp nhiều lần đọc documentation, liked songs và followed artists, chạm trần trước khi ghi nhận một hành động cuối hợp lệ; check đáp án và state change đều sai. Qwen3 32B tính hiệu tập ID và thử `unfollow_artist`, nhưng check cuối chỉ đạt 3/4, trong đó check về tập artist followings thay đổi vẫn sai. Việc agent đã gọi API không chứng minh tập tác động đúng. Dạng lỗi là **xác định/tác động đúng tập đối tượng**, phù hợp với chẩn đoán scope ở V7, nhưng v8 chưa chứng minh một verifier sẽ sửa được.

Ba task đúng chung cho thấy cả hai model có năng lực trên một phần AppWorld; ba task sai chung cho thấy thay model trong cùng scaffold chưa tạo được bộ năng lực bổ trợ. Chênh lệch partial check ở task cuối không tạo task rescue. Không dùng lỗi đã nhìn thấy này để sửa prompt rồi gọi lại cùng sáu ID như kết quả xác nhận.

## Quyết định gate và công việc tiếp

Gate `≥2/6` của Coder **đã qua**, nên control ghép cặp đã được chạy đầy đủ. Gate tiếp theo cần *meaningful rescues in both directions* trước khi xây thí nghiệm history cho pool này; kết quả **0/0 rescues** nên **không qua**. Do đó dừng việc dùng cặp Qwen3-Coder 30B/Qwen3 32B legacy ReAct này làm pool DART/HistRepEval AppWorld, không mở dev/test để tìm hiệu ứng và không trình bày router/oracle ảo là phương pháp thắng. Kết luận chỉ áp dụng cho cấu hình và sample train đã nêu.

Hướng nghiên cứu hợp lý tiếp theo là chuẩn bị **pool thật có chuyên môn bổ trợ**, khóa capability screen trên train ID mới và chỉ xây history khi thấy nhiều rescue hai chiều ở task success. Ứng viên AppWorld phải được test đúng version/data/agent (ví dụ phiên bản 0.2 riêng, không gộp điểm với 0.1.3) hoặc scaffold/solver khác với đối chứng cùng chi phí; scope verifier từ lỗi CSV/tập artist là giả thuyết có thể kiểm nghiệm, chưa là kết quả. Song song, HistRepEval nên tiếp tục trên pool MMLU-Pro đã có output thật nhưng phải giải bài toán giá trị quyết định so fallback/audit-only, thêm môi trường tương tác thứ hai và sealed holdout sau khi khóa method. Nếu không tìm được pool có complementarity lẫn hiệu ứng decision value, bài phương pháp DART chưa sẵn sàng để claim mạnh; một benchmark/negative-result paper cũng cần novelty, dữ liệu và replication đủ rộng. Không thể bảo đảm mức A* hoặc acceptance từ pilot này.

**Artifact tái lập:** `run_appworld_coder_v8.py`, `run_appworld_qwen32_v8_control.py`, `run_appworld_legacy_react_v7.py`, `evaluate_appworld_legacy_react_v7.py`; summary chấm ở `results/appworld_external_v1/train_pilot_v8_{coder,qwen32_control}/evaluation.json` (ignored). Protocol hashes lần lượt `b3cbb60b11e561c3fb12274ebf3794fd1a8504897b7a49e841c5c5201e121913` và `85223acd9031062df8cbd6c3b6d09994db3a7c6e1a4df9abbd0893f3554d2c1c`.
