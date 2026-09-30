# RepGuard: kiểm định pool mới và quyết định hướng bài sau 1.260 suy luận thật

**Ngày:** 30/09/2026. **Trạng thái:** đã hoàn tất và kiểm tra pool, đây là phân tích phát triển trên MMLU-Pro; không phải xác nhận DART hoặc kết quả ngoài benchmark. Kết quả Week 3–5 nằm ở [`repguard_final_pipeline_assessment_2026-09-30.md`](repguard_final_pipeline_assessment_2026-09-30.md). Gate đã định trước nằm ở [`repguard_next_study_registered_plan_2026-09-30.md`](repguard_next_study_registered_plan_2026-09-30.md).

## 1. Câu hỏi và thiết kế

Week 3 cho thấy ECRT cải thiện calibration trong vài điều kiện nhưng không cải thiện team accuracy đáng tin so FixedBorrow. Week 4/5 xác nhận Qwen3 8B `think=true` mạnh hơn đáng kể so `think=false`, nên một baseline solver mạnh có thể làm mất cơ hội cho reputation routing. Thí nghiệm này hỏi liệu thêm các model khác trên **cùng 420 câu, 14 môn** có tạo bổ trợ vừa đủ, và liệu một router chỉ học từ các câu khác có khai thác được bổ trợ đó không.

- Nguồn ID: 30 câu/môn từ Week 4 screen train, đã có Qwen3 8B direct/thinking trên từng ID. Ba model mới `gemma2:latest`, `llama3:8b`, `qwen3:14b` cùng trả lời từng ID; tổng 420 × 3 = **1.260 yêu cầu Ollama/Modal mới**. Không có đáp án mô phỏng.
- Cấu hình ba model mới: `think=false`, temperature 0, top-p 1, JSON answer enum, tối đa 64 output token. Qwen3 8B thinking dùng `think=true`, tối đa 8.192 output token, nên so sánh là **so hai chính sách suy luận và ngân sách**, không cô lập tham số `think`.
- Manifest giao thức SHA-256 `f4d3b237728c0b0463c49e47673793e9e1290903c187f0741dc533f51e4c7308`. Raw ledger `results/real_pool_overlap_v1/predictions.jsonl` có SHA-256 `81319c132b75d7822027d943fe67c05c8c616c366e57ea46473d0b0289da0437`. `analyze_real_pool_overlap.py` đọc lại raw JSON, đối chiếu digest model, prompt hash, task ID, split và duplicate. Đủ 420/model; ba model mới không có invalid. Ledger Qwen3 8B thinking cũ có **24/420 invalid/truncated** và được chấm sai, không xóa khỏi mẫu.
- Tất cả con số oracle dưới đây dùng gold để chẩn đoán **giới hạn cơ hội**. Chính sách khả thi chỉ dùng dữ liệu huấn luyện khác ID và thông tin có trước gold của câu đang giải.

## 2. Năng lực của mô hình trên đúng cùng 420 câu

| Chính sách | Đúng / 420 | Accuracy | Output token quan sát | Ghi chú |
|---|---:|---:|---:|---|
| Qwen3 8B thinking | **280** | **66,67%** | **953.873** | 24 invalid/truncated, đã tính sai |
| Qwen3 14B direct | 226 | 53,81% | 2.940 | 0 invalid |
| Qwen3 8B direct | 200 | 47,62% | 4.104 | 0 invalid |
| Gemma2 direct | 195 | 46,43% | 2.940 | 0 invalid |
| Llama3 8B direct | 158 | 37,62% | 3.610 | 0 invalid |

Output token là một chiều của chi phí, không phải GPU cost hay USD. Model khác kích thước, input token, thời gian nạp, latency và hạ tầng có thể khác; không suy ra tỷ lệ tiền trực tiếp từ bảng này. Tổng thời gian request của ba model direct mới lần lượt Gemma2 488,82 s, Llama3 357,91 s và Qwen3 14B 554,76 s; phép đo có thể bị ảnh hưởng bởi warm-up/server state.

### Khác biệt theo môn: Qwen3 14B direct so Qwen3 8B thinking

Mỗi môn n=30. Cột `14B-only` là câu chỉ 14B đúng, `think-only` là câu chỉ thinking đúng; đây là ghép cặp trên cùng câu.

| Môn | 14B đúng | Thinking đúng | 14B-only | Think-only |
|---|---:|---:|---:|---:|
| Biology | 23 | 25 | 2 | 4 |
| Business | 13 | 20 | 3 | 10 |
| Chemistry | 10 | 22 | 2 | 14 |
| Computer science | 19 | 25 | 3 | 9 |
| Economics | 22 | 25 | 1 | 4 |
| Engineering | **18** | 13 | 8 | 3 |
| Health | 19 | 19 | 3 | 3 |
| History | 17 | 17 | 3 | 3 |
| Law | 13 | 12 | 4 | 3 |
| Math | 12 | **24** | 0 | 12 |
| Other | 10 | 19 | 1 | 10 |
| Philosophy | 17 | 23 | 2 | 8 |
| Physics | 13 | 17 | 3 | 7 |
| Psychology | 20 | 19 | 2 | 1 |

Engineering là dấu hiệu chuyên môn duy nhất có cỡ chênh đáng quan tâm, nhưng **18/30 so 13/30 không đủ để xác nhận** một specialist ổn định; cặp discordant 8 so 3. Law và psychology chỉ hơn một câu. Môn toán trái với pilot direct ban đầu: thinking đạt 24/30, Gemma2 và 14B direct đều 12/30. Không chọn riêng engineering sau khi xem bảng để trình bày như discovery đã xác nhận.

## 3. Bổ trợ có thật nhưng chủ yếu là oracle, chưa thành method

- Trong **140 câu thinking sai**, Qwen3 14B direct cứu đúng 37, Gemma2 cứu 29, Llama3 cứu 25 và Qwen3 8B direct cứu 23; các tập cứu trùng nhau. Ít nhất một trong bốn direct model đúng ở **64/140** câu.
- Oracle biết đáp án đúng và chọn tùy ý trong năm đáp án đạt **344/420 = 81,90%**, cao hơn thinking 64 câu / 15,24 điểm. Đây là **upper reference không triển khai được**, vì trên câu mới policy không biết agent nào đúng. Với từng cặp, oracle thinking+14B là 317/420, thinking+Gemma2 309/420, thinking+Llama3 305/420.
- Majority vote năm model, khi hòa ưu tiên thinking, chỉ **248/420**, kém thinking 32 câu. Vote ba model (thinking, 14B, Gemma2), khi hòa ưu tiên thinking, được **267/420**. Do đó answer diversity tự nó không chuyển thành lợi ích.
- Một fallback cực đơn giản và khả thi là gọi Qwen3 14B direct **chỉ khi thinking không trả về JSON hợp lệ**. Trên 24 ca invalid quan sát, nó sửa đúng 6; replay đạt **286/420**, thêm 168 output token, 7.376 input token và 27,64 s thời gian request cộng dồn cho 24 call. Đây là baseline thực dụng mạnh hơn thinking trong tập phát triển, nhưng thuộc xử lý lỗi, không chứng minh reputation/audit hay một phương pháp mới. Cần xác nhận ở ID chưa xem và tính cost đầy đủ.

## 4. Router có thể học được gì?

`analyze_real_pool_gate.py` gán task ID vào 5 fold bằng SHA-256. Với mỗi câu, nó chọn global-best hoặc subject-best model từ **chỉ bốn fold khác**; kết quả câu đó không tham gia chọn. Bảng này là cross-fit trên pool đã được nghiên cứu nhiều lần, vì vậy chỉ là developmental diagnostic; bootstrap phân tầng môn lấy mẫu các chênh ghép cặp 10.000 lần. Không được coi fold là năm benchmark độc lập.

| Policy | Đúng / 420 | Chênh với thinking | 95% CI chênh accuracy | Output token |
|---|---:|---:|---:|---:|
| Luôn thinking | **280** | 0 | — | 953.873 |
| Global-best từ 4 fold | **280** | 0 | [0; 0] | 953.873 |
| Subject-best từ 4 fold | 274 | −6 | [−3,57; +0,71] điểm | 705.409 |

Subject router chọn thinking ở 322 câu, 14B direct 70, Gemma2 direct 23 và Qwen8 direct 5. Nó giảm **248.464 output token, khoảng 26,05%** với mất sáu câu đúng quan sát. Có thể có giá trị trong bài toán chi phí, nhưng chưa chứng minh non-inferiority hay novelty; [CP-Router](https://ojs.aaai.org/index.php/AAAI/article/view/40589) và [BEST-Route](https://arxiv.org/abs/2506.22716) là các đối chứng trực tiếp. Không được đánh đồng “ít token hơn” với “DART đánh bại baseline”.

## 5. Quyết định và cách tránh overclaim

**Gate 0 của DART trên pool MMLU-Pro này: STOP.** Yêu cầu trong kế hoạch là có ít nhất hai specialist khác nhau ở các skill độc lập và phần bổ trợ có thể dự báo bằng feature trước gold. Pool này chỉ có một tín hiệu yếu ở engineering, một solver thinking chiếm ưu thế chung, và subject routing không tăng accuracy. Oracle headroom 64 câu không phải lợi ích đã học được. Không dùng 420 sealed holdout để tiếp tục thử hàng loạt aggregator/router cho tới khi có cell đẹp; giữ nguyên holdout cho một phương pháp và so sánh đã khóa sau này.

Kết quả **không** nói ECRT/DART bất khả thi nói chung, cũng không chứng minh HistRepEval đã là bài A*. Nó bác bỏ cách triển khai DART cụ thể trên pool generalist MCQ này. Bài phương pháp mạnh cần môi trường có vai trò bổ sung thật, phản hồi lịch sử có thể sai nhưng có ảnh hưởng tới hành động, và lợi ích ở cùng cost so baselines. Nếu không có những điều kiện đó, nên báo cáo kết quả âm và đầu tư vào bài đánh giá HistRepEval: *khi nào cải thiện reputation calibration thực sự thay đổi quyết định, và khi nào không?*

## 6. Hướng thực hiện tiếp theo, có gate rõ

1. **Giữ HistRepEval là trục chắc nhất hiện nay.** Đóng gói ledgers/manifest/analyzer có checksum, benchmark card, error taxonomy, kết quả Week 3–5 và pool mới, nêu rõ provenance của feedback và các can thiệp có gold. Bổ sung metric decision sensitivity, rescueability và realized decision value. Không phát hành raw MMLU-Pro question text nếu license không cho phép; phân phối ID, script và hướng dẫn tái tạo.
2. **Đổi môi trường nếu muốn bài phương pháp.** Một benchmark agent tương tác như [AppWorld](https://aclanthology.org/2024.acl-long.850/) có task nhiều bước, tool feedback và vai trò agent khác nhau, hợp với trust/audit hơn MMLU-Pro độc lập. Tuy nhiên [Xia & Wang](https://arxiv.org/abs/2606.14200) và [TRUST-Bench](https://arxiv.org/abs/2605.17453) đã gần câu hỏi này; cần xác lập đúng khoảng trống, protocol phòng dữ liệu rò rỉ và baseline tương ứng trước khi chạy lớn. [AppWorld repo](https://github.com/StonyBrookNLP/appworld) có ràng buộc phân phối phần dữ liệu bảo vệ ở dạng mã hóa; phải tuân thủ khi làm artifact.
3. **Method hypothesis mới:** decision-aware audit chọn câu/lịch sử có thể *đảo hành động*, giữ một phần random audit để phát hiện bias có mục tiêu; mô hình hóa feedback source và answer-level uncertainty; chỉ dùng evidence khi expected utility sau audit đủ vượt chi phí và rủi ro. Đây là giả thuyết nghiên cứu, không phải claim mới vì local bounds, act/defer và audit đã có trong [Budgeted Act-or-Defer](https://arxiv.org/abs/2606.29654) và [Share the Judge, Learn the Deferral](https://arxiv.org/abs/2607.27984). Phải chứng minh phần feedback/audit điều kiện theo skill đem thêm gain so các phương pháp đó.
4. **Thử nghiệm go/no-go kế tiếp:** trước hết chạy pilot nhỏ trên môi trường agent thật với hai policy có lỗi bổ sung và một feedback source quan sát được; dùng train/dev để kiểm tra đường accuracy–cost và under targeted poison; nếu không hơn baseline, dừng nhánh method sớm. Chỉ khi pilot qua, khóa endpoint, ablation, đối chứng và attack rồi mở holdout/benchmark thứ hai. Báo paired CI, số trường hợp đổi quyết định và chi phí gold audit. Không hứa trước một mô hình chắc chắn thắng hay một bài chắc chắn được hội nghị nhận.

## 7. Tái lập

Các script: `run_real_pool_overlap.py`, `analyze_real_pool_overlap.py`, `analyze_real_pool_gate.py`. Artifact bị Git ignore: `results/real_pool_overlap_v1/manifest.json`, `predictions.jsonl`, `analysis_full.json`, `crossfit_gate.json`, `full.log`. Lệnh phân tích sau khi có dữ liệu: `.venv/bin/python analyze_real_pool_overlap.py` và `.venv/bin/python analyze_real_pool_gate.py`. Analyzer đầu kiểm tra protocol, digest, ID, duplicate, prompt hash và raw answer; analyzer cross-fit yêu cầu đủ **1.260** bản ghi mới trước khi tính routing. Sealed holdout: `results/real_next_study_v1/frozen_splits.json`, chưa mở để chấm outcome.
