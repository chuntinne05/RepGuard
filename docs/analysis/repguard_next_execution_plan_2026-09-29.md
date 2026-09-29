# RepGuard — kế hoạch thực thi sau Week 3 và quyết định về Modal thinking

**Ngày lập:** 29/09/2026. **Trạng thái:** đã triển khai provider và hoàn tất pilot 70 cặp câu; screen 420 cặp đang chạy, validation chưa chạy.
**Điểm xuất phát:** Week 3 chạy thật đã hoàn tất; ECRT chưa hơn FixedBorrow về team accuracy trong điều kiện chính. Xem `repguard_week3_real_report.md` và `repguard_comprehensive_progress_report_2026-09-29.md`.

## 1. Quyết định ngay

**Có, cần chỉnh client Modal/Ollama để *thử* thinking, nhưng không bật toàn cục và không chạy full ngay.** Modal là nơi host Ollama; nút điều khiển thực tế là trường `think` trong request Ollama `/api/chat`. Provider hiện ghi cứng `"think": false` trong `src/repguard/providers/ollama_.py`; runner Week 3 ghi cứng prompt direct, JSON enum, `max_tokens=64`, protocol ID `think_false`, và khóa resume chỉ theo `(agent, task_id)`. Chỉ thay `false` thành `true` sẽ làm giao thức cũ mất khả năng tái lập, dễ trộn hoặc bỏ qua kết quả; `64` token có thể cắt lời giải trước khi có đáp án.

Tài liệu chính thức: [Ollama Thinking](https://docs.ollama.com/capabilities/thinking) mô tả `think=true/false/null`, `/api/show` để biết model có hỗ trợ và `message.thinking` tách khỏi `message.content`; [Ollama Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs) mô tả `format` schema; [Qwen3](https://qwenlm.github.io/blog/qwen3/) có thinking và non-thinking; [MMLU-Pro](https://arxiv.org/abs/2406.01574) báo cáo CoT tốt hơn direct-answer trong đánh giá của họ. Những nguồn này **chỉ biện minh cho phép thử**; chưa chứng minh Qwen3 trên Modal của dự án sẽ tăng accuracy hoặc tạo specialist.

## 2. Mục tiêu khoa học của vòng tiếp theo

### Câu hỏi 1 — thinking có thay đổi năng lực *ở cùng câu* không?

So Qwen3 8B `think=false` với `think=true` bằng cùng model digest, cùng câu, cùng prompt direct, cùng JSON schema, nhiệt độ 0. Đo chênh accuracy ghép cặp, tỷ lệ không có đáp án/truncated, output tokens, latency và chi phí GPU thực. Không gộp tác động của thay prompt CoT vào so sánh này.

### Câu hỏi 2 — pool có thật sự dị biệt theo skill không?

Thinking có thể nâng Qwen3 8B ở mọi môn và làm pool **ít** dị biệt hơn; cũng có thể tạo thế mạnh mới ở toán/lý. Đánh giá người thắng trên train, xác nhận trên dev, đặc biệt chênh lệch với model đơn mạnh nhất và FixedBorrow. Không gọi một model là specialist chỉ vì đứng đầu một môn với vài câu.

### Câu hỏi 3 — có dự đoán được ai đúng cho *câu này* không?

Thử router theo thuộc tính câu và aggregator dựa trên mẫu bất đồng ở mức đơn giản. Oracle 68,34% Week 3 là trần dùng nhãn thật, không phải thành tích dự báo. Nếu baseline đơn giản không vượt model đơn trên dữ liệu mới, tinh chỉnh ECRT khó tạo paper phương pháp mạnh.

## 3. Việc kỹ thuật phải làm trước pilot

1. **Read-only preflight Modal/Ollama:** ghi phiên bản server qua `/api/version`; gọi `/api/show` cho đúng model digest/ID để biết `thinking.values` và mặc định. Kiểm tra endpoint hiện là Modal-hosted Ollama tự chạy, không nhầm với Ollama Cloud (tài liệu structured outputs nói Ollama Cloud chưa hỗ trợ schema). Nếu server không hỗ trợ `think` cho Qwen3, mới cần cập nhật server/image; thông thường chỉ cần sửa client.
2. **Provider:** đổi `think` từ hằng `False` thành tham số cấu hình rõ ràng `bool | str | None` tại `OllamaProvider.complete`/payload, mặc định `False` để giao thức Week 3 còn tái lập. Kiểm tra giá trị theo `/api/show` khi chọn mức named; không giả định mọi model hỗ trợ. Giữ `format` JSON schema tách biệt. Lấy `message.content` làm đáp án, log riêng có hay không `message.thinking`, token count và `done_reason`. Nếu cần lưu reasoning trace để audit, đặt nó ở artefact riêng có kiểm soát và không đưa nguyên văn câu hỏi benchmark lên Git.
3. **Runner mới, protocol mới:** tạo cấu hình/manifest và `results/real_week4_thinking_pilot_v1/`, không ghi tiếp vào `real_week3_json_v1`. Mỗi response định danh bằng `(task_id, agent_variant, prompt_version, think_value, num_predict, schema_version, model_digest)`; resume/cache phải phân biệt hai arm. Lưu config hash, server/model version, seed, prompt hash, output token limit và giá trị thinking được *yêu cầu*; pilot cần kiểm tra thinking được *trả về* thực sự.
4. **Parser/QA:** với `think=true`, đọc đáp án từ `message.content`, không nối `message.thinking` vào đáp án. Kiểm tra JSON enum, số câu bị `length`/`max_tokens`, raw output rỗng, retry. Chạy smoke có cả câu dễ và khó trước khi mở rộng.
5. **Đối chứng công bằng:** A = direct prompt + JSON schema + `think=false` + 64 token (giao thức Week 3); B = **cùng** direct prompt/schema + `think=true`. Pilot 1.024 và 4.096 token đều cắt một câu khó trước đáp án, nên protocol smoke mới khóa mức **8.192 token** trong ledger v3. Nếu B tiếp tục bị cắt đáng kể, tạo phiên bản protocol mới, không âm thầm thay giữa chừng. C = prompt CoT với chế độ phù hợp model chỉ là phép thử **riêng**; Gemma2/Llama3 không được tự động gán `think=true` nếu `/api/show` không hỗ trợ.

## 4. Thứ tự chạy và ngân sách câu hỏi

Mọi tập chọn theo ID/seed trước khi xem nhãn và ghi vào manifest. Dùng câu train/calibration **chưa nằm trong 1.400 history Week 3** để khám phá; dành các câu dev chưa dùng để kiểm tra sau lựa chọn. Số dev chưa dùng ít nhất ở `computer science` (20 câu), nên không thể tùy ý lấy 50 câu mới/môn tại đây.

| Pha | Quy mô gợi ý | Mục đích | Quyết định tiếp |
|---|---:|---|---|
| 0. Smoke kỹ thuật | 5 câu/môn × 14 = **70 câu**, Qwen3 8B thinking-on; thêm vài request direct đối chứng | Xác nhận Modal trả `thinking` riêng, JSON hợp lệ, không truncation/timeout hàng loạt; đo token và latency | Chỉ mở rộng khi contract API hoạt động |
| 1. Screen cân bằng | **30 câu/môn × 14 = 420 câu** từ train chưa dùng, cùng câu cho Qwen3 8B direct và thinking = **840 calls**; thêm model/scaffold ứng viên theo giới hạn cấu hình khóa trước | Đo gain accuracy ghép cặp, tính bổ sung, chi phí và top-2 theo môn/skill | Chỉ giữ các cấu hình có tín hiệu thật, không chọn theo test Week 3 |
| 2. Validation | Tối đa **20 câu/môn × 14 = 280 câu** từ dev chưa dùng cho các cấu hình đã chọn | Kiểm tra lại hướng chênh và router đơn giản; CI theo môn có thể rộng, nên đánh giá cả nhóm skill có cỡ mẫu đủ | Nếu promising nhưng CI rộng, tăng cỡ mẫu ở dữ liệu train chưa dùng hoặc dùng benchmark mới; không gọi kết quả này là xác nhận cuối |
| 3. Main evaluation | Chỉ sau khi khóa pool, prompt, metric, baseline và attack policy; dùng tập/benchmark mới, tối thiểu một môi trường khác MMLU-Pro nếu claim multi-agent rộng | Chứng minh hoặc bác bỏ gain outcome so model đơn, FixedBorrow, router/aggregator mạnh ở cùng compute | Ra quyết định paper phương pháp hay paper characterization |

Số call ở pha 1 chỉ là **đối chứng Qwen3 8B A/B**; mỗi cấu hình agent bổ sung trên cùng 420 câu tăng 420 calls. Giới hạn số cấu hình và tổng GPU budget trước khi chạy. Không quy ra USD từ token của Week 3; cần log thời gian GPU, hóa đơn Modal, token và tỷ lệ cold start của pilot. Dừng pilot khi chi phí mỗi câu thinking quá cao so với gain quan sát được hoặc khi nhiều đáp án bị cắt.

## 5. Phân tích và gate định trước

### Gate A — API/format

`think=true` thực sự được server chấp nhận; `message.thinking` xuất hiện ở các câu cần suy luận; final `message.content` có đáp án hợp lệ; 0 câu trộn sang ledger Week 3. Nếu server chỉ dùng default hoặc không có metadata thinking, ghi rõ mức bất định và kiểm tra raw response; không tuyên bố đã so hai chế độ khi thực ra cả hai giống nhau.

### Gate B — năng lực/chi phí

Báo cáo cho từng subject và nhóm skill: accuracy A/B, chênh ghép cặp + CI, số câu A-sai/B-đúng và ngược lại, tỷ lệ invalid/truncated, median/p95 tokens và latency, Modal GPU cost thực. Không dùng một ngưỡng p-value ở 20 câu/môn để phủ quyết mọi tín hiệu; đây là pilot khám phá. Giữ thinking làm agent variant khi có lợi ích năng lực hoặc bổ sung rõ so chi phí.

### Gate C — dị biệt có thể dùng được

Chọn ứng viên chỉ trên train; kiểm tra dev xem có **ít nhất hai agent/variant khác nhau** có lợi thế ổn định ở các skill khác nhau. Model thắng quan sát trực tiếp trên test không đủ. Nếu Qwen thinking thắng mọi skill, cách hợp lý có thể là dùng một model mạnh hoặc cascade theo chi phí, không ép bài reputation.

### Gate D — ra quyết định và phương pháp

Đánh giá router/aggregator đơn giản trước ECRT mới. Phép so chính trên tập khóa mới: accuracy hoặc risk-adjusted utility ở **cùng ngân sách compute** so best-single, majority/weighted vote, FixedBorrow, conditional trust và query router. Nếu calibration tốt hơn nhưng hành động cuối không đổi, ghi đây là kết quả calibration. Chỉ khi Gate C/D có đường cải thiện thực mới phát triển audit/decision-aware ECRT và targeted-poisoning study.

## 6. HistRepEval và bài báo trong vòng này

HistRepEval v0.1 hiện có manifest, ledger, Q×T, baseline và attack pilot MMLU-Pro. Sau thinking pilot, thêm **metadata agent variant và protocol** vào suite; tuyệt đối giữ Week 3 protocol `think=false` như một baseline riêng. Phiên bản tiếp theo cần judge feedback thật, audit gold có budget, benchmark thứ hai, attack nhiều seed và benchmark card. Không tái sử dụng 2.416 test câu Week 3 để tối ưu rồi gọi kết quả trên chính chúng là xác nhận độc lập.

**Paper mạnh theo nhánh phương pháp** đòi hỏi gain outcome so baseline mạnh trên dữ liệu mới, clean utility chấp nhận được và robustness đủ với targeted poisoning. **Nhánh characterization** vẫn hợp lý nếu hiện tượng Q/T và giới hạn của reputation lặp lại dù ECRT không thắng. Hai nhánh đều yêu cầu số liệu chạy thật, claim vừa mức và artefact tái lập.

## 7. Bàn giao theo week nghiên cứu (đề xuất)

- **Week 4, 30/09–04/10:** provider thinking có tham số + tests; read-only API preflight; manifest pilot; smoke 70 câu; screen 420 câu ghép cặp; báo cáo accuracy–cost và quyết định Gate A/B/C sơ bộ.
- **Week 5, 05–11/10:** validation tối đa 280 câu cho pool đã chọn; baseline router/answer aggregation; khóa phương pháp và metric; nếu đủ điều kiện, bắt đầu judge thật và audit budget. Ghi GO/NO-GO cho paper phương pháp.
- **Week 6, 12–18/10 (nếu Gate Week 5 qua):** main evaluation trên tập mới, nhiều attack/seed, external benchmark, HistRepEval card và bản thảo. Đây là lịch đề xuất sau GO-C; hạn 11/10 của kế hoạch cũ không nên được trình bày là đã bảo đảm.

## 8. Kết quả thực thi ban đầu, 29/09/2026

- Modal/Ollama `/api/version` trả `0.34.4`; `/api/show` của `qwen3:8b` công bố `thinking`; digest đã khóa `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`. Không cần sửa deployment Modal để bật thinking; cần tham số `think` ở client, đã bổ sung với mặc định `false`.
- Ledger v1 và v2 thử trên cùng một câu biology với giới hạn thinking 1.024 và 4.096 token: cả hai trả `done_reason=length`, không có đáp án cuối. Hai phép thử được giữ riêng, không gộp vào accuracy của v3.
- Ledger v3 (`results/real_week4_thinking_pilot_v3/`) đã chạy **14 câu khác nhau, một câu mỗi môn, hai biến thể trên mỗi câu = 28 request thật**. Direct đúng **7/14**, thinking đúng **10/14**; thinking sửa **4** câu direct sai và làm sai **1** câu direct đúng. Chênh quan sát **+21,43 điểm phần trăm**, nhưng cỡ mẫu quá nhỏ, không phải chứng cứ xác nhận.
- V3: 14/14 câu mỗi arm có JSON hợp lệ; 14/14 response thinking có `message.thinking`; 0/14 bị cắt ở 8.192 token. Median output tokens direct **10**, thinking **1.552,5**; median latency direct **0,98 giây**, thinking **42,11 giây**; p95 thinking **124,33 giây**. Đây là thời gian request, không phải chi phí USD; chưa có hóa đơn GPU tương ứng.
- Kiểm thử repo: `PYTHONPATH=src .venv/bin/python -m pytest -q` đạt **186 passed**.

**Pilot khóa ở 5 câu/môn đã hoàn tất:** 70 câu, 140 request thật trên cùng 14 môn và cùng protocol v3. Direct đúng **28/70 (40,00%)**; thinking đúng **41/70 (58,57%)**; chênh ghép cặp **+18,57 điểm phần trăm**, khoảng bootstrap theo câu trong môn 95% **[+7,14; +30,00]**, McNemar exact hai phía **p=0,0072** (thăm dò; chưa phải xác nhận độc lập). Thinking sửa **17** câu direct sai và làm sai **4** câu direct đúng. Có **5/70 (7,14%)** response thinking bị cắt ở 8.192 token, đã tính là sai; 70/70 có `message.thinking`. Median token output direct **10**, thinking **1.793,5**; p95 thinking **8.192**. Median latency direct **1,07 giây**, thinking **48,93 giây**; p95 thinking **226,51 giây**. Tổng latency request direct **78,84 giây**, thinking **4.908,31 giây** (gấp khoảng **62,3** lần). Đây không phải USD billable cost.

**Gate sau pilot:** đủ tín hiệu tăng năng lực để mở screen 420 cặp từ chính tập train chưa dùng đã chọn trước, nhưng tỷ lệ truncation và chi phí đòi hỏi báo cáo riêng. Full screen đã khởi chạy bằng runner resumable trên đúng manifest/digest/protocol, bắt đầu từ 140 response đã có; còn 350 cặp. Nếu tốc độ tương tự pilot, cần khoảng **6,9 giờ thời gian request** nữa, chưa tính cold start/gián đoạn. Không được xem 70 câu pilot và phần còn lại của cùng screen như hai tập xác nhận độc lập. Sau screen, chỉ chọn pool/policy trên train; dùng dev chưa dùng để xác nhận, rồi benchmark khác cho claim bài báo. Pilot này **chưa** chứng minh ECRT hay HistRepEval đạt giá trị phương pháp.
