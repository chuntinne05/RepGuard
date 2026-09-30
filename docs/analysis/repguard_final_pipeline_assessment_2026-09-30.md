# RepGuard / HistRepEval — kiểm toán kết quả và quyết định nghiên cứu sau pipeline 30/09/2026

**Thời điểm chốt:** 30/09/2026, múi giờ Việt Nam. **Nguồn sự thật:** manifest, ledger câu trả lời thực, script phân tích và `status.json` trong `results/`; không dùng các số liệu Week 2/3 cũ được mô phỏng. Đây là báo cáo nghiên cứu để lập kế hoạch và báo cáo tuần, **chưa phải bản thảo bài báo**.

## 1. Kết luận điều hành

**Pipeline mới đã chạy xong toàn bộ.** `results/real_week5_pipeline_v1/status.json` ghi `pipeline_complete` lúc 08:31:02 ngày 30/09/2026; 840/840 lượt Qwen3 8B ở screen train, 280/280 lượt blind judge, và 560/560 lượt Qwen3 8B ở validation dev đã có kết quả. Các script phân tích chạy lại trên raw ledger cho kết quả trùng khớp file tổng hợp. Điều này **không đồng nghĩa toàn bộ đề tài hoặc các exit gate nghiên cứu Week 4–6 đã hoàn thành**.

Ba phát hiện chính:

1. **Thinking hữu ích rõ rệt với Qwen3 8B trên MMLU-Pro 14 môn:** ở 280 câu dev tách ID, đúng 203/280 (72,50%) so với direct 137/280 (48,93%), hơn **23,57 điểm phần trăm**, khoảng tin cậy bootstrap ghép cặp 95% **[17,86; 29,29]**. Đây là kết quả xác nhận một lựa chọn cấu hình mạnh hơn, không phải đóng góp thuật toán mới: [bài MMLU-Pro gốc](https://arxiv.org/abs/2406.01574) đã báo cáo CoT tăng hiệu quả trên benchmark này.
2. **ECRT hiện chưa chứng minh được lợi ích chọn đáp án so với baseline đơn giản.** Trên Week 3, điều kiện chính `related + 25% noise`, ECRT hơn FixedBorrow **+0,02 điểm phần trăm** team accuracy, CI **[−0,04; +0,10]**. Với feedback của judge thật nhưng dùng lại test cũ, chênh `same` **+0,08** điểm [−0,04; +0,21], `related` **−0,16** điểm [−0,42; +0,11]. Brier có cải thiện trong một số điều kiện, tức ước lượng xác suất tốt hơn, nhưng chưa chuyển thành quyết định tốt hơn.
3. **Judge không thấy đáp án ứng viên tốt hơn trong phép thử thăm dò:** 79,11% so với 74,06% accuracy chấm đúng/sai trên 694 case, tăng **5,04 điểm phần trăm** [1,57; 8,56] theo bootstrap cụm câu hỏi. Prompt blind được đề xuất sau khi thấy lỗi của judge cũ trên **chính 280 câu đó**, vì vậy không được gọi đây là xác nhận độc lập. Judge vẫn chọn đúng đáp án chỉ 151/280 câu (53,93%).

**Quyết định:** Week 3 thực nghiệm thật đã hoàn thành, nhưng ý tưởng phương pháp ECRT ban đầu **không qua gate outcome**. Pipeline bổ sung đã sửa được một sai lệch lớn của giao thức năng lực (tắt thinking), đồng thời cho thấy cần đánh giá lợi ích theo **accuracy–cost–reliability** với pool và holdout mới. Hiện tại **chưa đủ chứng cứ cho bài phương pháp A\***. Có tiềm năng xây một bài mạnh hơn về giá trị ra quyết định của reputation/audit dưới feedback sai và ngân sách suy luận, song chỉ khi các gate định trước ở Mục 9 được vượt qua trên dữ liệu chưa xem và benchmark thứ hai. Không thể bảo đảm kết quả hay acceptance.

## 2. Đã chạy gì, theo đúng thứ tự chứng cứ

| Giai đoạn | Dữ liệu/cấu hình | Quy mô hoàn tất | Vai trò khoa học |
|---|---|---:|---|
| Week 3 rerun thật | MMLU-Pro 14 môn; Qwen3 8B, Gemma2, Llama3 8B, Qwen3 0.6B; zero-shot `think=false` | 18.064 lượt agent–câu = 4 × (1.400 history + 700 dev + 2.416 test) | Audit pool, Q×T, ECRT, attack pilot; test đã được xem và mở rộng sau pilot |
| Week 4 thinking screen v3 | Qwen3 8B, 30 câu train/calibration **chưa dùng** mỗi môn, direct và thinking ghép cùng câu | 420 câu, 840 lượt | Khám phá độ lớn lợi ích và chi phí thinking |
| Week 5 judge thấy ứng viên | Qwen3 14B; 280 câu history, đáp án ứng viên duy nhất | 694 lượt chấm cho 694 case | Nguồn feedback thật và phân tích lỗi; exploratory |
| Week 5 blind judge | Cùng Qwen3 14B/digest, 280 câu nói trên, một lần chọn đáp án/câu, không cho biết ứng viên | 280 lượt, 280 hợp lệ | So đối chứng prompt trên cùng câu; exploratory do chọn prompt sau khi xem lỗi |
| Week 5 thinking validation | Qwen3 8B; 20 câu dev chưa dùng/môn, direct và thinking ghép cùng câu | 280 câu, 560 lượt | Kiểm tra độc lập theo **task ID trong cùng MMLU-Pro** cho hiệu ứng thinking |
| Feedback impact offline | Dùng feedback judge thật, history thật và câu trả lời Week 3 thật | Hai fold, `same` và `related` | Kiểm tra tác động lên ECRT nhưng dùng lại test Week 3; exploratory |

Các tập ID của 420 câu screen, 280 câu blind judge và 280 câu validation có **0 ID giao nhau**. Screen train và validation dev không trùng các mẫu Week 3 ở split tương ứng; blind judge **cố ý dùng lại 280 câu Week 3 history** để so trực tiếp hai kiểu chấm. Qwen3 8B thinking dùng cùng digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`, Ollama `0.34.4`, temperature 0, cùng prompt và JSON enum. Hai policy so sánh là `think=false, max_tokens=64` và `think=true, max_tokens=8192`. Vì token cap cũng thay đổi, phép so đo **policy thinking với ngân sách dài so policy direct ngắn**, không cô lập tác dụng thuần của một biến nội bộ. Direct chỉ dùng khoảng 10 output token/câu, nên cap 64 không quan sát thấy gây cắt cụt.

`results/real_week4_thinking_pilot_v3/errors.jsonl` có **3 dòng lỗi request được khôi phục** trong quá trình chạy: một broken pipe và hai HTTP 503; ledger cuối vẫn đủ 840 lượt, không có dòng trả lời thiếu. Các phép tính accuracy cho câu invalid/truncated là **sai**, không loại các câu khó khỏi mẫu. Tất cả con số phần trăm trong báo cáo dùng mẫu số theo đúng hàng; không cộng các giai đoạn khác split thành một điểm accuracy chung.

## 3. Week 3 thật: tiền đề của phương pháp còn yếu

### 3.1 Năng lực bốn model trên toàn bộ test

| Model | Đúng / 2.416 | Accuracy |
|---|---:|---:|
| Qwen3 8B direct | 1.154 | 47,76% |
| Gemma2 direct | 1.090 | 45,12% |
| Llama3 8B direct | 877 | 36,30% |
| Qwen3 0.6B direct | 568 | 23,51% |

Router chọn model tốt nhất **theo môn dựa vào history** đạt 1.140/2.416 = **47,19%**, thấp hơn dùng Qwen3 8B mọi câu **0,58 điểm phần trăm**, CI ghép cặp [−1,90; +0,75]. Chỉ **Qwen3 8B ở physics** qua tiêu chuẩn specialist đã đặt: 116/254 so Gemma2 82/254, lợi thế **+13,39 điểm**, CI [+7,48; +19,29]. Pool này chưa cho thấy ít nhất hai specialist ở các nhóm kỹ năng khác nhau.

Oracle dùng **gold test để chọn model tốt nhất theo môn** là 48,97%; chỉ hơn model đơn 1,21 điểm. Oracle dùng **gold test để chọn ai đúng ở từng câu** là 68,34%; đây là độ bổ trợ quan sát được, không phải kết quả của router triển khai. Khoảng cách giữa hai oracle cho thấy môn quá thô và câu hỏi cụ thể quan trọng, nhưng **không chứng minh** có feature khả dụng để nhận ra model nào sẽ đúng.

### 3.2 ECRT, chất lượng feedback và tấn công

Trong lưới Q×T dùng câu trả lời model thật, 13 target có đủ ba mức transfer; 182 cặp nguồn–đích × 4 chế độ feedback × 3 seed × 9 phương pháp = **19.656 hàng phân tích**. Nhiễu của feedback và độ lệch nguồn có ảnh hưởng đo được lên **Brier**. Chẳng hạn GlobalBeta cùng môn dưới nhiễu lật 50% có Brier xấu thêm +0,0290 [0,0200; 0,0385]. Trong `same + directional false positive`, ECRT giảm Brier so FixedBorrow 0,0520 [0,0408; 0,0617]. Đây là điểm mạnh hẹp về calibration.

**Endpoint quyết định không theo kịp calibration.** Trong ô chính `related + 25% noise`, team accuracy ECRT−FixedBorrow chỉ +0,02 điểm [−0,04; +0,10]. So model đơn cũng không có lợi thế rõ. Pilot targeted poisoning A2 ở budget 100 cho ECRT mất 16,7 điểm accuracy, FixedBorrow mất 11,1 điểm; đây là can thiệp ép attacker trả lời sai bằng nhãn gold, **chưa phải attack ngoài đời** và chỉ một scenario. Không thể suy từ Brier tốt dưới nhiễu đồng đều ra an toàn trước poisoning có mục tiêu.

Các chi tiết và CI theo target: [`repguard_week3_real_report.md`](repguard_week3_real_report.md). Kết luận Week 3 giữ là **GO-C: sửa hướng, tạm dừng claim ECRT vượt baseline**. Week 3 cũ dùng correctness mô phỏng từ tỷ lệ tổng hợp đã bị vô hiệu hóa; tuyệt đối không dùng các bảng cũ như kết quả thực nghiệm.

## 4. Qwen3 8B thinking: xác nhận hiệu quả, chi phí và giới hạn

### 4.1 Kết quả ghép cặp

| Tập | Số câu | Direct đúng | Thinking đúng | Thinking−direct | CI 95% theo bootstrap ghép cặp trong môn | Thinking-only / direct-only |
|---|---:|---:|---:|---:|---:|---:|
| Screen train | 420 | 200 (47,62%) | 280 (66,67%) | **+19,05 điểm** | [14,29; 23,81] | 103 / 23 |
| Dev đã khóa | 280 | 137 (48,93%) | 203 (72,50%) | **+23,57 điểm** | [17,86; 29,29] | 79 / 13 |

Trên dev, 79 câu direct sai được thinking sửa và 13 câu direct đúng bị thinking làm sai. Kiểm định McNemar hai phía tính từ 92 cặp bất đồng cho p khoảng **1,07 × 10⁻¹²**; file phân tích lưu p = `0.0` vì làm tròn 5 chữ số, **không phải p thật bằng 0**. Screen cho p khoảng 2,79 × 10⁻¹³. Khoảng tin cậy ở đây lấy mẫu lại câu **bên trong từng môn**, cân bằng 14 môn; chưa tính bất định khi thay benchmark, model family hay phiên bản prompt. Kết quả dev cùng chiều với screen nhưng không nên khẳng định độ lớn hiệu ứng tăng giữa hai tập; chưa có phép kiểm định chênh hai hiệu ứng.

Mẫu dev 20 câu/môn, do đó từng tỷ lệ môn có sai số lớn. Dữ liệu chi tiết để phát hiện lỗi tập trung:

| Môn (n=20) | Direct đúng | Thinking đúng | Thinking bị cắt cụt |
|---|---:|---:|---:|
| biology | 13 | 16 | 0 |
| business | 8 | 17 | 1 |
| chemistry | 4 | 14 | 6 |
| computer science | 11 | 17 | 0 |
| economics | 15 | 18 | 0 |
| engineering | 7 | 9 | 5 |
| health | 15 | 17 | 0 |
| history | 10 | 11 | 0 |
| law | 4 | 7 | 0 |
| math | 6 | 18 | 1 |
| other | 10 | 13 | 0 |
| philosophy | 11 | 15 | 1 |
| physics | 11 | 18 | 1 |
| psychology | 12 | 13 | 0 |

Thinking quan sát tốt hơn ở cả 14 hàng dev, nhưng **mỗi hàng chỉ n=20**, chưa có CI cho từng môn. Engineering còn 9/20; law 7/20. Chemistry và engineering gộp **11/15** lần cắt cụt, một failure mode rõ để phân tích prompt/token budget riêng. Ở screen, engineering hòa 13/30 và physics cắt cụt 8/30; kết quả theo môn không hoàn toàn ổn định.

### 4.2 Chi phí đo được

| Tập | Direct output token | Thinking output token | Tỷ lệ token | Direct tổng request time | Thinking tổng request time | Tỷ lệ thời gian |
|---|---:|---:|---:|---:|---:|---:|
| Screen 420 câu | 4.104 | 953.873 | 232,4× | 482,57 s | 28.114,82 s | 58,3× |
| Dev 280 câu | 2.734 | 581.165 | 212,6× | 332,75 s | 17.525,70 s | 52,7× |

Trên dev, độ trễ **trung vị mỗi request** là 1,05 s direct và 41,27 s thinking; p95 là 1,88 s so 248,20 s. `total_request_seconds` là tổng thời gian của từng API call, **không phải** thời gian đồng hồ của cả pipeline hoặc chi phí USD; chưa có giá Modal/GPU được hạch toán. Thinking dev có **15/280 = 5,36%** câu bị cắt ở 8.192 token và không có đáp án hợp lệ; screen là **24/420 = 5,71%**. Thêm token có thể cứu một số câu nhưng cũng tăng chi phí; cần phép thử giới hạn token được khóa trước.

Oracle chọn direct **hoặc** thinking đúng bằng gold dev đạt 216/280 = **77,14%**, chỉ **+4,64 điểm** so luôn thinking; không thể triển khai vì cần biết đáp án đúng trước khi chọn. Đây là trần chẩn đoán cho việc tìm accuracy gain bằng cách chọn giữa đúng hai output đã đo. Tiềm năng thực dụng lớn hơn có thể nằm ở **giữ gần 72,5% accuracy với ít token hơn** qua routing chính xác; điều đó chưa được chứng minh.

### 4.3 Diễn giải đúng

Kết quả này có giá trị vì xác nhận cấu hình direct Week 3 bỏ lỡ năng lực reasoning đáng kể. Nó **không** tự động sửa thất bại của ECRT: thinking đã chỉ được so trên **một model**, còn Gemma2/Llama3/Qwen nhỏ và các policy đều chưa chạy trên cùng 280 câu dev này. Chưa biết pool mới có hai specialist hay không; cũng chưa có team accuracy, FixedBorrow, ECRT hoặc router trên pool thinking tại tập này. MMLU-Pro gốc đã chỉ ra lợi ích CoT, vì thế mức tăng direct→thinking là **baseline quan trọng**, không phải novelty riêng của RepGuard ([Wang et al. 2024](https://arxiv.org/abs/2406.01574)).

## 5. Judge thật và HistRepEval: tín hiệu có ích nhưng chưa đủ

### 5.1 Judge thấy ứng viên và judge blind

Qwen3 14B đã chấm 280 câu history từ bốn model Week 3. Có 694 case đáp án ứng viên duy nhất; cùng một case có thể đại diện nhiều agent nên phép so judge giữ **694 case**, không coi các bản sao agent độc lập. Judge thấy ứng viên đúng verdict 514/694 = **74,06%**; 112/234 câu có nhiều đáp án ứng viên cho thấy lựa chọn judge không nhất quán khi đổi ứng viên trong prompt. Điều này gợi ý candidate influence, chưa định danh riêng cơ chế nhân quả của mỗi lỗi.

| Chỉ số trên cùng 694 case | Thấy đáp án ứng viên | Blind, chọn một đáp án/câu |
|---|---:|---:|
| TP: đáp án đúng được chấp nhận | 140 | 140 |
| TN: đáp án sai bị từ chối | 374 | 409 |
| FN: đáp án đúng bị từ chối | 59 | 59 |
| FP: đáp án sai bị chấp nhận | 121 | 86 |
| Accuracy verdict | 74,06% | **79,11%** |
| Số request | 694 | **280** |
| Tổng request time | 1.484,73 s | **561,92 s** |

Mức tăng 35/694 = **5,04 điểm** [1,57; 8,56] đến **toàn bộ từ giảm 35 false positive**; TP và FN bằng nhau. Tập 694 case có **495 đáp án sai** nên baseline luôn từ chối đạt 495/694 = **71,33%**; accuracy verdict cao không thay thế precision/recall, confusion matrix và **team outcome**. Blind judge chọn đúng gold 151/280 = 53,93%, nên sẽ thường chấm sai khi tự giải sai. Một lần blind/câu giảm số request và tổng thời gian quan sát, nhưng phải kiểm tra chi phí/token và quality trên mẫu mới trước khi suy ra hiệu quả triển khai.

**Giới hạn lớn nhất:** blind prompt được chọn sau khi nhìn lỗi candidate judge **trên cùng 280 câu**. Dù CI theo câu không chứa 0, CI này chỉ lượng hóa biến thiên lấy mẫu **với phép so đã chọn**; nó không loại được thiên lệch do sửa prompt trên test. Cần khóa prompt và chạy một batch mới, tốt nhất thêm judge khác họ model, trước khi ghi claim độc lập.

### 5.2 Feedback thật vào ECRT

Phân tích offline chia 280 câu history làm hai fold, một nửa hiệu chuẩn judge, nửa kia làm history; test outcome vẫn là **test Week 3 đã xem**. Kết quả ECRT−FixedBorrow:

| Điều kiện | Team accuracy chênh | CI 95% | Brier chênh, thấp hơn tốt hơn | CI 95% |
|---|---:|---:|---:|---:|
| Cùng môn | +0,08 điểm | [−0,04; +0,21] | **−0,0189** | [−0,0281; −0,0092] |
| Môn liên quan | −0,16 điểm | [−0,42; +0,11] | **−0,0213** | [−0,0354; −0,0076] |

Vì ECRT chỉ biến xác suất năng lực thành trọng số vote **theo môn**, sửa xác suất có thể không đảo đáp án cuối. Đây là diễn giải phù hợp với Brier tốt hơn nhưng team accuracy gần như không đổi; muốn chứng minh nhân quả cần ablation decision rule trên holdout mới. Chi tiết: [`repguard_week5_real_feedback_impact_2026-09-29.md`](repguard_week5_real_feedback_impact_2026-09-29.md).

**HistRepEval hiện là giao thức đánh giá có dữ liệu thật và mã tái lập**, gồm manifest, per-question ledger, điều kiện Q×T, judge, calibration, attack pilot và phân tích ghép cặp. Nó **chưa** là một benchmark được xác nhận bên ngoài hoặc package công bố độc lập: mới một benchmark, pool generalist, nhiều điều kiện feedback là can thiệp nhãn, test đã được xem, attack chưa đa dạng, raw `results/` bị Git ignore và chưa có release/versioned artifact với independent rerun. Có thể tiếp tục phát triển HistRepEval thành đóng góp dữ liệu/đánh giá, nhưng không viết như đóng góp hoàn chỉnh hôm nay.

## 6. Mức độ chắc chắn và các điểm dễ báo cáo sai

| Mệnh đề | Mức chứng cứ tại 30/09 | Cách ghi phù hợp |
|---|---|---|
| Pipeline mới chạy xong | Kiểm chứng trực tiếp bằng `status.json`, ledger đủ, analyzer tái chạy trùng | **Hoàn tất pipeline** |
| Thinking tăng accuracy Qwen3 8B trên MMLU-Pro | 420 câu screen và 280 câu dev disjoint; cùng digest, paired effect lớn | **Được xác nhận nội bộ trên benchmark/model/policy này** |
| Blind judge hơn judge thấy ứng viên | Paired 694 case, nhưng prompt chọn sau khi xem lỗi cùng mẫu | **Thăm dò, cần fresh holdout** |
| ECRT tăng team accuracy so FixedBorrow | CI của các endpoint chính chứa 0; một số dấu âm | **Chưa có bằng chứng** |
| ECRT hiệu chuẩn xác suất tốt hơn | Brier cải thiện ở một số điều kiện can thiệp và feedback judge thật | **Có tín hiệu hẹp, cần external replication** |
| ECRT chống targeted poisoning | A2 pilot ECRT hại hơn baseline; forced-wrong oracle | **Không được khẳng định** |
| HistRepEval là benchmark paper hoàn chỉnh | Pipeline thật, nhưng thiếu external validation và release | **Prototype đánh giá có triển vọng** |

Ba tầng độc lập phải nói rõ: (a) **độc lập task ID trong cùng MMLU-Pro** cho validation thinking; (b) **độc lập prompt selection** còn thiếu với blind judge; (c) **độc lập benchmark/pool** còn thiếu cho mọi kết luận phương pháp. Dev 280 câu hiện đã bị xem kết quả; nếu dùng để chọn thuật toán tiếp theo thì nó chuyển thành tập phát triển, **không còn là test cuối** cho thuật toán đó. Reuse test Week 3 cũng vậy; rủi ro overfit do phân tích thích nghi là vấn đề phương pháp đã được nghiên cứu từ lâu ([Dwork et al. 2015](https://papers.neurips.cc/paper_files/paper/2015/hash/bad5f33780c42f2588878a9d07405083-Abstract.html)).

Các CI hiện có tập trung vào lấy mẫu câu trong môn hoặc bootstrap target/cụm câu; không bao phủ thay model seed, benchmark, công cụ, prompt, judge family. 14 môn MMLU-Pro không biến thành 14 benchmark độc lập. Các chỉ số nhỏ ở cấp môn không đủ để kết luận specialist mới. Báo cáo phải tách **kết quả quan sát** khỏi **ngưỡng mong muốn** và không gọi oracle là model hoặc policy.

## 7. Có đủ mạnh cho bài báo A* chưa?

**Đánh giá chuyên môn hiện tại: chưa.** Đây không phải dự đoán xác suất acceptance; chuẩn đánh giá tùy venue và thời điểm. Những phần đã mạnh là audit dữ liệu thật ở quy mô lớn, protocol có hash và raw ledger, một kết quả thinking có đối chứng ghép cặp, phân tích thất bại trung thực, và tín hiệu calibration dưới feedback sai. Những thiếu hụt có thể khiến bài phương pháp bị phản biện từ chối:

| Tiêu chí bài phương pháp mạnh | Hiện trạng | Cần có để thay đổi đánh giá |
|---|---|---|
| Đóng góp mới so prior art | Historical credibility, skill-conditional trust, router và selective verification đều đã có bài liên quan | Cơ chế cụ thể **decision-aware audit dưới feedback sai/transfer** có gain riêng so các thành phần |
| Outcome vượt baseline mạnh | ECRT≈FixedBorrow, router môn thua model đơn, thinking model đơn rất mạnh | Vượt always-thinking / router mạnh / FixedBorrow ở **cùng ngân sách**, CI trên primary endpoint |
| Specialist/pool thích hợp | Chỉ một specialist xác nhận ở Week 3; chưa có bốn model cùng prompt thinking | Ít nhất hai chuyên môn có lợi thế trên nhóm khác nhau, xác nhận trên tập khác |
| Robustness có khả năng diễn giải | Một A1/A2 forced-wrong pilot; A2 bất lợi | Nhiều attacker, budget, seed và đáp án độc hại sinh thật; không hy sinh clean outcome |
| External validity | Một benchmark trắc nghiệm, bốn model generalist | Benchmark/pool thứ hai; nếu claim multi-agent tương tác, một môi trường agent nhiều bước |
| Tái lập/công bố | Mã và manifest tốt; `results/` ignore | Artifact có phiên bản, checksum, license, instructions, independent rerun |

Khoảng trống novelty cần được diễn đạt hẹp: [Ebrahimi et al. 2025](https://aclanthology.org/2025.ijcnlp-long.90/) đã dùng credibility từ lịch sử; [Xia & Wang 2026](https://arxiv.org/abs/2606.14200) đã nghiên cứu trust theo skill, heterogeneity và laundering; [RouteLLM](https://arxiv.org/abs/2406.18665) đã làm query routing. Thêm một judge hoặc verifier cũng cần vượt đối chứng thêm lời giải/self-consistency cùng compute vì [Singhi et al. 2025](https://arxiv.org/abs/2504.01005) thấy verifier có thể kém hiệu quả hơn; [Smit et al. 2024](https://proceedings.mlr.press/v235/smit24a.html) cho thấy debate không luôn hơn các chiến lược đơn giản. Các bài này **không phủ định khả năng đề tài**, nhưng làm cho claim “có reputation/routing/judge” đơn thuần không đủ mới.

Ba đường ra bài hợp lý, phải chọn theo kết quả mới:

1. **Bài phương pháp (ưu tiên có điều kiện):** một policy DART ra quyết định dùng audit hạn chế để học độ tin cậy của feedback theo agent–skill, ước lượng giá trị đổi route/đáp án, fallback về solver mạnh khi không chắc; primary endpoint là risk/accuracy ở cùng cost. Chỉ theo nếu Gate 0–2 bên dưới qua.
2. **Bài benchmark/measurement:** phát triển HistRepEval thành benchmark đa dataset/pool về feedback reliability × task transfer × decision sensitivity; cần chất lượng artifact, chuẩn nguồn feedback/attack và các kết luận lặp lại ở môi trường ngoài. Một bảng MMLU-Pro duy nhất chưa đủ.
3. **Bài negative/failure analysis:** nếu phương pháp tiếp tục không thắng, nghiên cứu có hệ thống vì sao calibration không đổi decision và khi nào thinking model đơn áp đảo team. Có thể có giá trị khoa học nếu tìm ra phase diagram/tính chất tổng quát trên nhiều môi trường, nhưng không nên mặc định là A*.

## 8. Hướng chính đề xuất: từ reputation score sang giá trị của hành động

**Giả thuyết làm việc, chưa phải kết quả:** history và audit chỉ có giá trị nếu làm hệ thống chọn hành động tốt hơn khi phải trả tiền cho suy luận. Policy phải trả lời một trong ba câu: dùng direct rẻ, dùng thinking/agent khác, hay mua một bước kiểm chứng. Với mỗi câu, cần ước lượng (i) xác suất từng policy đúng, (ii) nguồn feedback cho agent/skill này đáng tin đến đâu, (iii) uncertainty và chi phí token/latency; chỉ thay baseline khi lợi ích dự kiến đủ lớn. Giữ một phần audit gold lấy ngẫu nhiên để nhận ra bias có mục tiêu; audit ưu tiên chỉ các ca gần ranh giới quyết định có thể bỏ sót attacker. Nếu toàn bộ feedback không đáng tin và không có gold audit/giả định độc lập nào, năng lực thật và bias của evaluator không nhận dạng được; phải ghi nguồn gold và chi phí của nó.

Một sơ đồ policy tối thiểu để kiểm định: `question → đặc trưng không dùng gold → direct/strong-think/agent khác → ước lượng giá trị đổi hành động bằng history đã hiệu chuẩn → nếu lợi ích không rõ, fallback về policy mạnh đã khóa; nếu đáng và còn budget, kiểm chứng hoặc gọi solver thêm`. Không dùng gold test để quyết định; không tự diễn giải score Brier là gain accuracy. Tên **DART** chỉ nên giữ nếu thí nghiệm ablation chứng minh cả phần audit, transfer và decision threshold đóng góp riêng.

## 9. Lộ trình thí nghiệm tiếp theo và cổng dừng

Các ngưỡng dưới đây là **đề xuất để khóa trước lượt chạy mới**, không phải tiêu chuẩn đã đăng ký cho dữ liệu hiện tại. Hạn 11/10 trong kế hoạch sáu tuần cũ không nên được hứa như hạn có bài mạnh; thời gian phụ thuộc Modal budget, external benchmark và số baseline.

### Gate 0 — chốt pool, holdout và bài toán chi phí (ưu tiên ngay)

1. Đóng băng mã, prompt, model digest, định nghĩa token/latency cost, các baseline và **ID holdout MMLU-Pro còn chưa dùng** trước khi xem nhãn/kết quả. Dev 280 câu đã xem chỉ dùng phát triển. Dành thêm một benchmark khác và ít nhất một pool/model family khác cho kiểm chứng ngoài. Ghi tất cả pool/prompt đã thử để tránh báo cáo chọn lọc.
2. Trên tập **train/calibration còn chưa dùng**, chạy 2–4 policy có cơ sở: Qwen3 8B direct, Qwen3 8B thinking, một model khác họ với reasoning phù hợp, và một policy chi phí thấp. Đo từng câu **trên cùng ID**; bao gồm invalid/truncation, token, latency, số lời gọi. Không cần quét full dataset trước khi thấy pool có lợi ích.
3. Kiểm tra có ít nhất **hai agent/policy khác nhau** thắng rõ trên các nhóm skill độc lập và có complementary errors có thể dự báo được. Skill phải được định nghĩa bằng feature có trước gold, không lựa từ test. Nếu không qua, **không** phát triển ECRT/DART trên pool đó; chuyển mục tiêu thành routing chi phí giữa direct và thinking hoặc thiết kế lại pool.

**Sản phẩm:** manifest holdout khóa, ma trận paired capability/cost trên pool mới, quyết định `POOL-GO`/`POOL-STOP`. Đây là việc gần nhất cần làm; không chạy tiếp full MMLU-Pro vô định.

### Gate 1 — kiểm tra khả năng quyết định tốt hơn baseline

1. Huấn luyện router nhẹ trên train: luôn direct, luôn thinking, chọn theo môn, router theo câu hỏi **trước khi có đáp án**, router sau direct dựa trên uncertainty/answer pattern, và một oracle gold **chỉ chẩn đoán**. So thêm self-consistency hoặc gọi solver khác ở ngân sách ngang nhau. Không chọn policy theo test.
2. Định primary metric trước: ví dụ accuracy ở cùng mức output token/request time, hoặc chi phí thấp hơn khi accuracy không giảm vượt biên chấp nhận được. Bắt buộc đưa đường **Pareto accuracy–token–latency**; một gain accuracy nhờ dùng hàng trăm lần token không được mô tả là cải tiến hiệu suất.
3. Trên holdout chưa xem, yêu cầu gain thực dụng đã khóa (gợi ý **≥2 điểm accuracy ở cùng cost**, hoặc **≥25% ít token hơn** tại accuracy suy giảm không quá biên đã khóa) và CI ghép cặp phù hợp tách khỏi 0 cho primary comparison. Nếu mục tiêu là non-inferiority về accuracy, phải đặt biên và CI non-inferiority đúng, không dùng “p > 0,05” để nói tương đương. Các mốc 2 điểm/25% là quyết định quản trị compute đề xuất, **không phải định lý hay hứa hẹn kết quả**.

**Sản phẩm:** bảng baseline công bằng, biểu đồ Pareto, paired CI, báo cáo lỗi/truncation. Nếu router không vượt always-thinking về utility, chuyển sang benchmark/characterization; không thêm reputation module chỉ vì Brier trông đẹp.

### Gate 2 — giá trị tăng thêm của audit/reputation, chỉ khi Gate 0–1 đạt

1. Chạy `FixedBorrow`, ECRT, skill-conditional trust, router không reputation và DART/audit policy trên **cùng pool và câu**, với budget history/audit/solver ngang nhau. Tách feedback oracle sạch, corruption seed có kiểm soát, judge thật đã khóa prompt, và poisoning **riêng agent/skill**. Có random audit và targeted audit, báo mỗi gold label tốn bao nhiêu.
2. Phải có ít nhất hai attack policy và nhiều lịch sử/seed; attacker dùng câu trả lời sai **do model tạo thật** trong ít nhất một điều kiện. Forced-wrong oracle được giữ như stress test tối đa, dán nhãn rõ. Đo clean utility, worst-case/regret, Brier và tỷ lệ audit. Làm ablation bỏ reliability, bỏ transfer, bỏ decision threshold, bỏ audit để chỉ ra nguồn gain.
3. Khóa một primary comparison với baseline mạnh nhất; CI theo câu ghép cặp và cụm phù hợp; điều chỉnh khi nhiều đối chứng chính. Không chọn riêng cell có lợi sau khi chạy. Nếu không có gain decision hoặc loss trước targeted poison cao hơn baseline, dừng claim phương pháp và công bố kết quả âm một cách trung thực.

**Sản phẩm:** protocol/main table/ablation/robustness đã khóa, script tái tạo từ raw log.

### Gate 3 — xác nhận ngoài và đóng gói HistRepEval

1. Khóa hoàn toàn method/hyperparameter rồi đánh giá benchmark thứ hai và pool khác. Nếu mục tiêu là **multi-agent tương tác**, bổ sung tác vụ nhiều bước/tool use; MMLU-Pro hiện chỉ là nhiều model trả lời độc lập rồi tổng hợp.
2. Chạy judge blind trên batch **mới** và model judge khác họ để kiểm tra candidate bias; đo effect lên team outcome, không dừng ở verdict accuracy. Báo uncertainty và cost.
3. Tạo benchmark card, data provenance/license, split IDs, prompt/config/model digest, raw ledger/checksum, script `one-command reproduction`, và independent rerun. `results/` hiện bị Git ignore nên push mã lên `dev` không đồng nghĩa đã chia sẻ dữ liệu thực nghiệm.

**Sản phẩm:** claim sheet cuối cho paper, external replication, HistRepEval release candidate. Chỉ sau gate này mới quyết định nộp venue cụ thể và viết abstract như kết luận đã xác nhận.

### Lịch làm việc để báo cáo tuần

| Mốc nghiên cứu đề xuất | Việc cần hoàn tất | Điều kiện chuyển bước |
|---|---|---|
| Week 4 bổ sung, bắt đầu 30/09 | Audit pipeline đã xong; khóa holdout/pool/cost; chạy screen đa policy trên train còn mới | Gate 0: heterogeneity hoặc cost trade-off đủ rõ |
| Week 5 | Xây và so router/aggregator với always-thinking, single-best, same-budget SC | Gate 1: utility gain trên holdout mới |
| Week 6 | Nếu qua gate, chạy DART/audit và factorial feedback + nhiều attack | Gate 2: gain riêng so baseline mạnh, clean và poison ổn |
| Sau Week 6 | Benchmark/pool thứ hai, judge fresh batch, HistRepEval artifact, bản thảo | Gate 3: external replication và reproducibility |

Những tên thư mục `real_week4_*`, `real_week5_*` là **tên pipeline thực nghiệm**, không chứng minh Week 4/5 của đề cương ban đầu đã đạt tiêu chí khoa học. Week 4/5 cũ yêu cầu phương pháp, robustness và external validity; các mục này vẫn còn. Nếu Gate 0 trượt, cần đổi đề cương/tham vọng paper sớm, tránh tiếp tục tiêu compute vào một pool thiếu specialist.

## 10. Tài liệu, mã và đối chiếu số

- Trạng thái cuối: `results/real_week5_pipeline_v1/status.json` (`pipeline_complete`, 30/09/2026 08:31:02 +07).
- Week 3: [`repguard_week3_real_report.md`](repguard_week3_real_report.md); raw `results/real_week3_json_v1/predictions.jsonl` (18.064 hàng; SHA-256 đã ghi trong báo cáo Week 3).
- Thinking screen: `results/real_week4_thinking_pilot_v3/manifest.json`, `predictions.jsonl` (840 hàng), `analysis_full.json`; protocol `74f421ec…`; SHA-256 ledger `eb6581a853350513813dfeae7f1778d4edae13fd73e5813f5779926d4c79ba0a`.
- Thinking dev: `results/real_week5_validation_v1/manifest.json`, `predictions.jsonl` (560 hàng), `analysis.json`; protocol `7e3ed4a2…`; SHA-256 ledger `fd36ee35bfb28d7a83d8fa81f368637ec3c229284c4581ec5643fab16a0be0da`.
- Blind judge: `results/real_week5_blind_judge_v1/manifest.json`, `judgments.jsonl` (280 hàng), `analysis.json`; protocol `2b9fe8eb…`; SHA-256 ledger `7972e84b0f6eb29fc96df19b8534674d628374e58bc1bca978f3644a655a4c42`.
- Judge candidate: `results/real_week5_modal_judge_v1/`; feedback impact: `results/real_week5_feedback_impact_v1/`.
- Script phân tích: `analyze_real_week4_thinking.py`, `analyze_real_week5_blind_judge.py`, `analyze_real_week5_feedback_impact.py`. Ngày 30/09 đã chạy lại hai lần đầu trên v3/dev/blind: **ba file JSON tái tạo trùng hoàn toàn** với bản lưu. Script thinking kiểm tra ID split, digest dataset, prompt hash, schema, model digest, duplicate và giới hạn token trước khi tính; script blind kiểm tra protocol/model/prompt và ghép đúng 694 case.

**Một câu để báo cáo ngắn:** “Đã hoàn tất rerun 18.064 đáp án thật Week 3 và pipeline bổ sung 840 + 280 + 560 lượt trên 14 môn MMLU-Pro. Qwen3 8B thinking được xác nhận tăng 23,57 điểm accuracy trên 280 câu dev mới nhưng dùng khoảng 213 lần output token. Judge blind cải thiện chấm feedback trong thử nghiệm thăm dò. ECRT cải thiện calibration ở một số điều kiện nhưng chưa hơn FixedBorrow về team accuracy; đang khóa holdout và pool mới trước khi quyết định hướng bài phương pháp/HistRepEval.”
