# BÁO CÁO TIẾN ĐỘ TỔNG HỢP — RepGuard / ECRT / HistRepEval

**Ngày chốt số liệu:** 29/09/2026 (giờ Việt Nam)
**Mục đích:** tài liệu gốc để viết báo cáo tuần, trao đổi với giảng viên và lập kế hoạch nghiên cứu tiếp theo.
**Tình trạng:** Week 3 **hoàn tất về thực nghiệm và phân tích**, quyết định khoa học **GO-C**. Các week tiếp theo trong tài liệu này là **kế hoạch đề xuất**, chưa phải kết quả đã thực hiện.
**Nguồn kiểm chứng chính:** `docs/analysis/repguard_week3_real_report.md`, `research_ops/real_week3_protocol.md`, `results/real_week3_json_v1/` và các file nghiên cứu trong `research_ops/`.

## 1. Tóm tắt điều hành

RepGuard nghiên cứu cách biến phản hồi lịch sử về năng lực của các LLM agent thành độ tin cậy phù hợp với nhiệm vụ mới. Ý tưởng ECRT (Evidence-Calibrated Reputation Transfer) tách hai câu hỏi: **phản hồi lịch sử có đáng tin không** và **lịch sử đó có liên quan đến câu hỏi hiện tại không**. HistRepEval là tên làm việc của bộ quy trình đánh giá, không phải tên một dataset mới đã công bố.

Từ 28–29/09, dự án đã chạy lại Week 3 với **18.064 câu trả lời model thật**: bốn model × (1.400 câu history + 700 câu dev + 2.416 câu test) trên **đủ 14 môn MMLU-Pro**. Ledger có **0 hàng thiếu, 0 hàng trùng, 0 đáp án không hợp lệ**. Bài toán Q×T tạo **19.656 hàng kết quả** cho 182 cặp môn nguồn–đích, bốn chế độ chất lượng feedback, ba seed và chín phương pháp; attack pilot A1/A2 cũng đã chạy. Bộ mã hiện có **183/183 tests qua** khi chạy `PYTHONPATH=src pytest -q` ngày 29/09.

Kết luận quan trọng: model đơn Qwen3 8B đạt **47,76%** trên test; routing theo môn chọn từ history chỉ đạt **47,19%**. Ở ô so sánh chính được đăng ký trước, ECRT hơn FixedBorrow **+0,02 điểm phần trăm team accuracy**, CI 95% **[−0,04; +0,10]**, không cho thấy lợi ích thực dụng. ECRT cải thiện Brier score dưới một số kiểu nhiễu mạnh, song chưa chuyển thành tăng tỷ lệ trả lời đúng và còn yếu ở pilot poisoning chọn lọc. Vì vậy **không được báo cáo rằng ECRT đã thắng baseline hay chống được tấn công**. Quyết định hiện tại là **GO-C: giữ phát hiện thực nghiệm, sửa tiền đề specialist/tín hiệu câu hỏi, tạm dừng claim vượt trội của ECRT**.

## 2. Tiến độ theo week: kế hoạch gốc và thực tế

Kế hoạch ban đầu ghi sáu tuần từ **31/08 đến 11/10/2026**. Nhật ký hiện cho thấy phần triển khai và thực nghiệm trọng tâm dồn vào 28–29/09. Vì vậy cần phân biệt **tuần theo lịch** với **mốc nghiên cứu**: tại ngày 29/09 đã thuộc khoảng Week 5 theo lịch gốc, nhưng bản đánh giá khoa học đáng tin mới hoàn tất mốc Week 3. Không nên ghi Week 4/5 đã xong chỉ vì ngày trên lịch đã qua.

| Mốc | Mục tiêu kế hoạch gốc | Việc có chứng cứ đã làm | Trạng thái ngày 29/09 |
|---|---|---|---|
| Week 1 | Chốt câu hỏi, tổng quan, khung mã, chia dữ liệu, audit nhỏ | Có proposal, kế hoạch 6 tuần, mã tải/parse MMLU-Pro, split xác định, provider/harness, ghi log và ranh giới ground truth | Hạ tầng cơ bản có; audit nhỏ cũ không đủ xác nhận specialist; chưa thấy bản manuscript hoàn chỉnh |
| Week 2 | HistRepEval v0.1, các baseline, demo feedback/task mismatch | Đã có Uniform, GlobalBeta, SkillConditioned, ZeroEvidenceGate, FixedBorrow, công cụ corruption, aggregation, metric; các bảng Week 2 cũ là dry-run/mô phỏng/thăm dò | **Hạ tầng đạt**, nhưng kết quả cũ **không phải bằng chứng thực nghiệm model thật** để đưa vào bài |
| Week 3 | Hiện tượng Q×T, pilot tấn công, CI, quyết định GO | Rerun bốn model thật trên 14 môn; phân tích Q×T, ECRT và ablation, A1/A2, báo cáo đầy đủ | **Hoàn tất thực nghiệm, GO-C**; giả thuyết ECRT cải thiện team outcome chưa đạt |
| Week 4 | Hoàn thiện và kiểm chứng phương pháp ECRT | Mã ECRT và ablation đã có, được dùng trong rerun Week 3 | **Chưa qua exit gate phương pháp**: ECRT chưa hơn FixedBorrow ở outcome chính; không nên tiếp tục thêm module theo quán tính |
| Week 5 | Robustness nhiều điều kiện, judge thật, external validity, kết quả đóng băng | Mới có Q×T can thiệp có kiểm soát và A1/A2 pilot | **Chưa hoàn tất** judge thật, nhiều attacker/seed attack, benchmark thứ hai, result freeze |
| Week 6 | Bản thảo hoàn chỉnh và gói tái lập | Proposal, kế hoạch, báo cáo, mã, ledger và hình đã tồn tại | **Chưa hoàn tất** bài báo, benchmark card, external validation và gói release ổn định |

**Sửa lịch đề xuất:** dùng Week 4–6 dưới đây như **mốc công việc còn lại**, thay vì mặc định rằng hạn 11/10 vẫn đủ cho một bài mạnh. Để báo cáo tuần có ngày cụ thể, có thể tạm xếp Week 4 nghiên cứu **30/09–04/10**, Week 5 **05–11/10**, Week 6 **12–18/10**. Đây là lịch **đề xuất sau GO-C**, chưa phải tiến độ đã cam kết; hạn bản thảo 11/10 trong kế hoạch gốc cần đánh giá lại sau pilot và ước lượng compute.

**Kết quả lịch sử chỉ có giá trị kiểm tra pipeline:** `results/week2_reputation/week2_results.json` từng ghi trung bình tám môn Uniform 48,5%, GlobalBeta 54,5%, SkillConditioned 48,0%, ZeroEvidenceGate 57,5% và OracleReputation 54,0%; `results/week3/` cũ từng dẫn tới GO-B. Chúng dựa trên mô phỏng hoặc audit năng lực quá nhỏ, nên **không được cộng gộp, so trực tiếp hay trích như kết quả khoa học với bảng Week 3 chạy thật**. Chúng chứng minh mã/harness đã vận hành, không chứng minh giả thuyết phương pháp.

## 3. Câu hỏi nghiên cứu và ranh giới novelty

**Câu hỏi trung tâm:** hệ thống nhiều LLM agent nên dùng phản hồi lịch sử không hoàn hảo như thế nào để ước lượng năng lực phù hợp với tác vụ hiện tại và phân bổ ảnh hưởng cho agent?

**Các đối tượng cần tách:** (i) đáp án/action và đúng sai thật `z`; (ii) feedback quan sát được `F`, có thể sai; (iii) skill/đặc điểm câu lịch sử so với câu mới; (iv) độ bất định của bằng chứng; (v) quyết định cuối và chi phí. Một điểm Brier tốt không tự động chứng minh team accuracy tốt.

Không tuyên bố là mới: reputation từ lịch sử ([Ebrahimi et al. 2025](https://aclanthology.org/2025.ijcnlp-long.90/)); conditional trust, evidence borrowing và laundering ([Xia & Wang 2026](https://arxiv.org/abs/2606.14200)); routing theo câu ([RouteLLM](https://arxiv.org/abs/2406.18665)); hay selective verification nói chung. Khoảng trống cần kiểm chứng tiếp là **khi nào feedback lịch sử đủ đáng tin và đủ liên quan để thay đổi một quyết định, và ngân sách audit nên đặt vào đâu**. Đây hiện chỉ là hướng nghiên cứu, không phải một claim mới đã được chứng minh.

## 4. Dữ liệu, model và giao thức chạy thật

### 4.1 Dữ liệu và split

- Nguồn: bản local `TIGER-Lab/MMLU-Pro`, **12.032 câu, 14 môn**; dataset task-ID SHA-256 và file hash nằm trong `results/real_week3_json_v1/manifest.json`. MMLU-Pro tăng số lựa chọn lên khoảng 10 và nhấn mạnh câu suy luận ([bài gốc](https://arxiv.org/abs/2406.01574)).
- Split hash với seed 42: **7.241 train/calibration, 2.375 dev, 2.416 test**. Lấy đúng **100 history/môn = 1.400 câu** và **50 dev/môn = 700 câu** cho bốn model. Toàn bộ **2.416 câu test** được trả lời bởi mỗi model; số câu test từng môn không bằng nhau.
- Protocol đầu tiên chọn 70 câu test/môn. Sau pilot này, vì các khoảng cách top-2 nhỏ, thực nghiệm được mở rộng **đồng đều ở cả 14 môn** tới hết test. `test_extension.json` lưu lý do và ID thêm. Vì quyết định mở rộng xảy ra sau khi xem pilot, kết quả và CI trên chính test này phải diễn giải **thăm dò**, không trình bày như một xác nhận hoàn toàn độc lập.

### 4.2 Model và điều kiện suy luận

| Agent thực sự có prediction | Ollama model ID | Kích thước/quantization trong inventory |
|---|---|---|
| qwen3-8b | `qwen3:8b` | 8,2B, Q4_K_M |
| gemma2 | `gemma2:latest` | 9,2B, Q4_0 |
| llama3-8b | `llama3:8b` | 8,0B, Q4_0 |
| qwen3-0.6b | `qwen3:0.6b` | 751,63M, Q4_K_M |

`model_inventory.json` còn có `qwen3:14b` được kiểm kê, **nhưng model này không có prediction trong ledger chạy thật**. Không lẫn nó với `gemma2` như một dòng audit nhỏ cũ từng làm. Digest chính xác từng model nằm trong inventory.

Mọi model dùng cùng giao thức zero-shot direct-answer, nhiệt độ 0, `think=false`, `num_predict=64`, Ollama JSON-schema enum trên các đáp án hợp lệ. Đây **không phải** giao thức few-shot/CoT của bảng xếp hạng MMLU-Pro; không so các accuracy tuyệt đối với leaderboard. MMLU-Pro gốc báo cáo CoT có lợi hơn trả lời trực tiếp, còn [Qwen3](https://arxiv.org/abs/2505.09388) có thinking mode. Do đó cần pilot prompt/reasoning mới; hiện **chưa có bằng chứng** kết quả Week 3 kém là do `think=false`.

### 4.3 Kiểm toán thực thi và chi phí quan sát được

| Khoản | Số đo từ ledger |
|---|---:|
| Tổng model–task responses | **18.064** |
| Mỗi model | **4.516 = 1.400 history + 700 dev + 2.416 test** |
| Thiếu / trùng / đáp án không hợp lệ | **0 / 0 / 0** |
| Input tokens ghi trong ledger | **4.414.855** |
| Output tokens ghi trong ledger | **158.721** |
| Tổng tokens ghi nhận | **4.573.576** |
| SHA-256 `predictions.jsonl` | `1c69cd9d49f3b2c97bf20868e246c5b524492a0f28f9b0095170fa1dded9fd4e` |

Latency trung bình theo **mỗi response** được log: Gemma2 1.220 ms, Llama3 994 ms, Qwen3 0.6B 705 ms, Qwen3 8B 988 ms. Các con số này không phải tổng wall-clock hay GPU-hours vì các lời gọi có thể chạy song song. **Chưa có hóa đơn Modal/GPU được kiểm chứng** trong artefact để ghi chi phí tiền; không tự quy đổi tokens thành USD.

Ground truth không xuất hiện trong prompt hoặc prediction ledger; scorer đọc bản benchmark riêng. Mã phân tích xác nhận task/split/model/prompt hash, đáp án raw và trùng lặp. Đây là kiểm soát quan trọng đối với rò nhãn trong đánh giá.

## 5. Kết quả năng lực model trên toàn bộ 2.416 câu test

### 5.1 Toàn cục

| Model | Số câu đúng | Micro accuracy | Wilson 95% CI | Macro trung bình 14 môn |
|---|---:|---:|---:|---:|
| Qwen3 8B | 1.154/2.416 | **47,76%** | 45,78–49,76% | 49,19% |
| Gemma2 | 1.090/2.416 | **45,12%** | 43,14–47,11% | 47,53% |
| Llama3 8B | 877/2.416 | **36,30%** | 34,41–38,24% | 38,52% |
| Qwen3 0.6B | 568/2.416 | **23,51%** | 21,86–25,24% | 23,90% |

Micro gộp tất cả câu; macro lấy trung bình tỷ lệ của 14 môn nên khác micro khi số câu/môn khác nhau. Wilson CI ở đây mô tả sai số lấy mẫu của từng accuracy, **không** phải kiểm định ghép cặp giữa các model. Trên cùng 2.416 câu, Qwen3 8B hơn Gemma2 **2,65 điểm phần trăm**; paired-bootstrap thăm dò cho chênh lệch này là **[+0,66; +4,64] điểm**.

### 5.2 Bảng đầy đủ theo 14 môn

Mỗi ô ghi `số đúng / n (accuracy)`. Các tỷ lệ trong cùng hàng mới so trực tiếp được; không suy ra specialist có ý nghĩa thống kê chỉ từ model đứng đầu một hàng.

| Môn | n | Qwen3 8B | Gemma2 | Llama3 8B | Qwen3 0.6B |
|---|---:|---:|---:|---:|---:|
| biology | 146 | 110/146 (75,34%) | 105/146 (71,92%) | 94/146 (64,38%) | 60/146 (41,10%) |
| business | 167 | 74/167 (44,31%) | 64/167 (38,32%) | 43/167 (25,75%) | 37/167 (22,16%) |
| chemistry | 234 | 97/234 (41,45%) | 83/234 (35,47%) | 57/234 (24,36%) | 52/234 (22,22%) |
| computer science | 97 | 49/97 (50,52%) | 56/97 (57,73%) | 41/97 (42,27%) | 28/97 (28,87%) |
| economics | 171 | 106/171 (61,99%) | 95/171 (55,56%) | 84/171 (49,12%) | 62/171 (36,26%) |
| engineering | 203 | 92/203 (45,32%) | 88/203 (43,35%) | 76/203 (37,44%) | 44/203 (21,67%) |
| health | 156 | 85/156 (54,49%) | 79/156 (50,64%) | 65/156 (41,67%) | 26/156 (16,67%) |
| history | 72 | 35/72 (48,61%) | 36/72 (50,00%) | 28/72 (38,89%) | 11/72 (15,28%) |
| law | 226 | 72/226 (31,86%) | 83/226 (36,73%) | 70/226 (30,97%) | 45/226 (19,91%) |
| math | 249 | 92/249 (36,95%) | 83/249 (33,33%) | 53/249 (21,29%) | 42/249 (16,87%) |
| other | 187 | 89/187 (47,59%) | 90/187 (48,13%) | 69/187 (36,90%) | 42/187 (22,46%) |
| philosophy | 110 | 44/110 (40,00%) | 49/110 (44,55%) | 43/110 (39,09%) | 18/110 (16,36%) |
| physics | 254 | 116/254 (45,67%) | 82/254 (32,28%) | 66/254 (25,98%) | 51/254 (20,08%) |
| psychology | 144 | 93/144 (64,58%) | 97/144 (67,36%) | 88/144 (61,11%) | 50/144 (34,72%) |

### 5.3 Specialist, routing và trần oracle

Ứng viên specialist được **chọn từ 100 câu history/môn**, rồi so trên test bằng paired bootstrap với ba model còn lại. Chỉ xác nhận khi cả ba CI lợi thế đều trên 0. **Chỉ Qwen3 8B ở physics qua gate**: 116/254 đúng so Gemma2 82/254, chênh **+13,39 điểm**, CI **[+7,48; +19,29]**. Gemma2 đứng đầu test ở vài môn nhưng CI với Qwen3 8B còn chứa 0; không xem đó là specialist được xác nhận. Gate này là thăm dò trên 14 phép so theo môn, chưa điều chỉnh đầy đủ đa kiểm định.

| Cách chọn | Số đúng / 2.416 | Accuracy | Ý nghĩa |
|---|---:|---:|---|
| Một Qwen3 8B chọn toàn cục từ history | 1.154 | **47,76%** | Baseline có thể triển khai |
| Chọn model theo môn từ history | 1.140 | **47,19%** | Thấp hơn baseline −0,58 điểm, CI [−1,90; +0,75] |
| Oracle model tốt nhất *theo môn* bằng nhãn test | 1.183 | **48,97%** | Trần lạc quan, không thể triển khai khi chưa biết nhãn |
| Oracle *có ít nhất một model đúng trên từng câu* | 1.651 | **68,34%** | Trần chỉ để đo tính bổ sung cấp câu, không phải accuracy khả thi |

Phân bố số model đúng trên mỗi câu test: **0 model: 765 câu; 1 model: 549; 2 model: 430; 3 model: 408; cả 4 model: 264**. Tỷ lệ đúng chỉ một model là **549/2.416 = 22,72%**. Điều này gợi ý tín hiệu ở cấp câu có thể đáng nghiên cứu, nhưng chưa cho thấy một router thực tế sẽ tìm được câu/model đó. Khoảng cách từ 47,76% đến oracle 68,34% là **20,58 điểm**, không được báo cáo như một gain đã đạt.

## 6. Thực nghiệm Q × T: phản hồi và độ liên quan nhiệm vụ

### 6.1 Thiết kế

- **Q — chất lượng feedback:** oracle đúng; lật nhãn đối xứng 25%; lật đối xứng 50%; false positive có hướng trên 40% câu trả lời sai. Feedback được can thiệp lên correctness của **câu trả lời model thật**. Đây là can thiệp có kiểm soát, **chưa phải** feedback của một judge chạy thật.
- **T — nguồn history so mục tiêu:** same, related và unrelated theo taxonomy metadata cố định (life sciences; physical/technical; social/behavioral; humanities; `other`). `other` vẫn được tính ở audit năng lực nhưng không có related source nên không vào factorial đủ ba mức.
- **Quy mô:** 182 cặp source–target × 4 mức Q × 3 seed (42, 123, 456) × 9 phương pháp = **19.656 hàng**; **13 target subject** có đủ ba mức T.
- **Phương pháp:** Uniform, GlobalBeta, SkillConditioned, ZeroEvidenceGate, FixedBorrow, ECRT, cùng ba ablation ECRT bỏ reliability/transfer/uncertainty.
- **Metric:** team accuracy và unique-expert success (cao hơn tốt); Brier binary và MAE năng lực (thấp hơn tốt). Các source pair và seed được bình quân *trong từng target*, rồi bootstrap **5.000 lần trên 13 target subject** để ra CI 95%; đây là suy luận thăm dò, chưa hiệu chỉnh nhiều so sánh.

### 6.2 Bảng kết quả các ô quyết định

Team accuracy dưới đây là **trung bình các target môn bằng trọng số ngang nhau**, nên có thể khác micro accuracy gộp 2.416 câu ở mục 5.

| Điều kiện | Phương pháp | Team accuracy | Brier | Unique-expert success |
|---|---|---:|---:|---:|
| same + oracle | Uniform | 47,82% | 0,2500 | 9,45% |
| same + oracle | GlobalBeta / FixedBorrow | 49,64% | 0,2206 | 13,76% |
| same + oracle | ECRT | 49,60% | 0,2206 | 14,19% |
| related + 25% noise | SkillConditioned | 47,82% | 0,2500 | 9,45% |
| related + 25% noise | FixedBorrow | 49,28% | 0,2422 | 12,74% |
| related + 25% noise | ECRT | 49,29% | 0,2510 | 12,74% |
| same + 50% noise | FixedBorrow | 47,89% | 0,2495 | 10,00% |
| same + 50% noise | ECRT | 47,83% | 0,2304 | 9,14% |
| same + 40% false positive | FixedBorrow | 49,69% | 0,2763 | 13,26% |
| same + 40% false positive | ECRT | 49,68% | 0,2243 | 13,26% |

### 6.3 Các phép so có CI và cách đọc

1. **Q thật sự ảnh hưởng đến calibration.** Với GlobalBeta cùng môn, 50% flip làm Brier tăng **+0,0290** (CI **[+0,0200; +0,0385]**) và team accuracy giảm **−1,75 điểm** (CI **[−3,09; −0,53]**). False positive có hướng làm Brier tăng **+0,0557** (CI **[+0,0440; +0,0661]**).
2. **T ảnh hưởng đến calibration trong thiết kế này.** GlobalBeta với feedback oracle: Brier của same thấp hơn related **0,0265** (CI **[0,0133; 0,0421]** theo chiều lợi cho same), nhưng chênh team accuracy same–related là **−0,02 điểm**, CI **[−0,38; +0,39]**. Có Q×T contrast trên Brier, ví dụ interaction 50% noise, unrelated so same **−0,0246** (CI **[−0,0347; −0,0154]**), song không chứng minh được interaction tương ứng trên team accuracy.
3. **So sánh phương pháp được đăng ký trước không đạt.** Related + 25% noise: ECRT − FixedBorrow team accuracy **+0,02 điểm**, CI **[−0,04; +0,10]**; Brier **+0,0088**, CI **[−0,0003; +0,0181]** (dương là xấu hơn); unique-expert success bằng nhau. ECRT hơn SkillConditioned **+1,47 điểm** team accuracy (CI **[+0,46; +2,43]**), nhưng FixedBorrow cũng đạt gần tương tự. Phần gain này thuộc việc *mượn history related*, chưa xác nhận đóng góp riêng của ECRT.
4. **Ablation:** bỏ reliability chỉ thay team accuracy ở ô chính khoảng **+0,02 điểm** cho ECRT (CI **[−0,02; +0,08]**). Trong same + oracle, ECRT còn thấp hơn FixedBorrow **−0,03 điểm** (CI **[−0,10; 0]**). So với model đơn trên 13 target, ECRT same + oracle **+0,29 điểm** (CI **[−1,54; +2,15]**), related + 25% noise **−0,02 điểm** (CI **[−1,88; +1,84]**).
5. **Lợi ích hẹp có thật về xác suất:** same + 50% noise, ECRT giảm Brier so FixedBorrow **0,0192** (CI mức giảm **[0,0104; 0,0281]**); same + false positive có hướng giảm **0,0520** (CI **[0,0408; 0,0617]**); related + false positive giảm **0,0429** (CI **[0,0115; 0,0722]**). Team accuracy ở các ô này gần như không tăng.

Một caveat cơ chế: ở `unrelated`, ECRT/FixedBorrow có thể đặt `tau=0` và trở về prior 0,5. Vì vậy vài kết quả Brier/interaction ở đây có yếu tố **cơ học của thiết kế**, không chứng minh transfer năng lực thực sự bằng 0.

## 7. Pilot tấn công A1/A2

Scenario chọn **chỉ bằng dev**, rồi áp dụng lên test. Dữ liệu đầu vào là câu trả lời thật của model, nhưng phần tấn công thay câu trả lời test của attacker bằng một đáp án biết chắc sai **nhờ gold test**, và/hoặc đổi feedback sai của attacker thành tích cực. Đây là **stress test can thiệp có oracle**, chưa phải attacker LLM tự phát nói sai trong môi trường thật. Mỗi scenario chỉ có một attacker và một thứ tự history; chưa đủ suy luận tần suất tấn công tổng quát.

| Pilot | Thiết lập | Kết quả nổi bật |
|---|---|---|
| **A1 — delayed betrayal** | Qwen3 8B, economics → economics; dev source accuracy 68%; budget 5 history, feedback honest | ECRT cho attacker **89,3%** trọng số; clean 61,99% → attacked 0%, mất **62,0 điểm**. FixedBorrow/SkillConditioned cho 33,3% trọng số và mất **17,5 điểm**. Kết quả cực đoan, rất nhạy với 5 câu đầu. |
| **A2 — cross-skill laundering/poisoning** | Gemma2, biology → chemistry; dev source 64%, target 24%, gap 40 điểm; budget 100, feedback false positive chọn riêng attacker | ECRT cho attacker **36,9%** trọng số, team accuracy clean 37,18% → attacked 20,51%, mất **16,7 điểm**. FixedBorrow 33,7% trọng số, mất **11,1 điểm**; SkillConditioned mất **8,1 điểm**. |

Diễn giải: ECRT hiệu chỉnh được một số nhiễu **đồng đều** nếu dev phản ánh đúng cơ chế, nhưng dev honest không phát hiện được poisoning nhắm riêng vào attacker. Đặc biệt ở A2, biology và chemistry được taxonomy xem là related, nên chính phần transfer vẫn là đường laundering. Không thể dùng pilot này để khẳng định “ECRT luôn kém” hoặc “tấn công chắc chắn thành công”; nhưng **không có bằng chứng robustness** cho ECRT hiện tại.

## 8. Đối chiếu giả thuyết và quyết định khoa học

| Giả thuyết kế hoạch | Bằng chứng hiện có | Kết luận báo cáo |
|---|---|---|
| H1: feedback kém làm reputation suy giảm | Q can thiệp làm GlobalBeta Brier tăng rõ, team accuracy giảm ở 50% flip | **Được hỗ trợ trong thiết kế can thiệp này** |
| H2: history lệch nhiệm vụ làm reputation sai | T contrast trên Brier rõ; taxonomy related/unrelated chưa được xác thực bằng skill thật | **Được hỗ trợ một phần cho calibration** |
| H3: Q và T gây tác động khác nhau/tương tác | Có vài Q×T contrast Brier; team outcome không rõ; `tau=0` gây hiệu ứng cơ học ở unrelated | **Hỗn hợp; không được claim interaction mạnh về outcome** |
| H4: ECRT tốt hơn baseline công bằng | Brier tốt hơn dưới nhiễu mạnh; ô chính team accuracy +0,02 điểm CI chứa 0; A2 bất lợi | **Không được hỗ trợ cho team accuracy/robustness** |
| H5: tấn công khai thác lịch sử/transfer | A1/A2 pilot cho thấy lỗ hổng có thể xảy ra trong stress test | **Chỉ là bằng chứng pilot, chưa tổng quát hóa** |

**Quyết định GO-C** thay cho dòng GO-B cũ ngày 28/09. Cần tạm ngừng claim ECRT superiority, giữ ECRT như phương pháp nghiên cứu/baseline, sửa pool agent và tín hiệu task, sau đó đăng ký thí nghiệm xác nhận mới. Đây không phải GO-D vì Q/T vẫn tạo hiệu ứng calibration rõ trong một số ô. Nó cũng chưa phải GO-A vì chưa có specialist dị biệt đủ và chưa thắng FixedBorrow trên outcome chính.

## 9. HistRepEval hiện ở đâu?

**Đã có:** phiên bản quy trình đánh giá chạy được trên dữ liệu thật MMLU-Pro: split/manifest, ID task, model digest, ledger nguyên gốc có prompt hash và token/latency, mô hình tạo feedback có seed, strata transfer, chín phương pháp, Q×T/attack analysis, mã hình và CI. Có thể tái tính kết quả Week 3 từ artefact local. HistRepEval ở đây là **evaluation protocol/suite working version**, không được gọi là benchmark đã công bố hay bộ dữ liệu mới độc lập.

**Chưa có để gọi là gói benchmark mạnh:** benchmark card hoàn chỉnh; judge thật đã chạy và đo lỗi; benchmark/môi trường thứ hai; nhiều pool dị biệt; nhiều attacker/seed cho tấn công; xác nhận độc lập; bộ artefact release có phiên bản và hướng dẫn tải lại dữ liệu. `results/` đang bị Git ignore; vì vậy chỉ đẩy mã lên Git **không đủ** để người khác tái lập các con số. Cần kiểm tra giấy phép benchmark trước khi phát tán câu hỏi/raw dataset; có thể phát hành ID, manifest, script và những bản ghi được phép.

## 10. Khó khăn, sai lệch cũ và giới hạn hiện tại

1. **Bằng chứng cũ bị thay thế.** Audit 8 môn × 5 câu và Week 2/3 pipeline cũ dùng mẫu rất nhỏ hoặc Bernoulli correctness mô phỏng; có lỗi gán cấu hình `qwen3:14b` thành `gemma2`. Những bảng “specialist Math/Physics”, “GO-B”, hoặc ECRT chặn laundering từ 28/09 **không phải kết quả cuối**. Kết quả thật hiện cho thấy physics thuộc Qwen3 8B và A2 vẫn lọt transfer related.
2. **Pool chưa có ít nhất hai specialist được xác nhận.** Các model hiện đều là generalist; chênh top-2 theo nhiều môn nhỏ. Điều kiện cần cho claim conditional reputation theo môn chưa đạt.
3. **Nhãn môn có thể quá thô.** Oracle theo môn chỉ hơn model đơn **1,21 điểm**, trong khi oracle từng câu hơn **20,58 điểm**. Tín hiệu ở cấp câu có thể hữu ích nhưng hoàn toàn chưa được chứng minh là dự đoán được.
4. **Phương pháp chưa tạo lợi ích quyết định.** Brier tốt hơn không đủ nếu trọng số thay đổi mà phiếu cuối không đổi; FixedBorrow là baseline khó vượt trong pool này.
5. **Nhiễu feedback chính vẫn được tạo bằng can thiệp.** Câu trả lời model là thật, nhưng flip/false positive là tình huống giả định; cần LLM judge/công cụ thật và audit chất lượng feedback của từng nguồn.
6. **Attack pilot chưa phải tấn công tự phát.** Forced-wrong dùng nhãn test để kiểm tra sức chịu đựng của thuật toán; chưa đo khả năng attacker model tự tạo câu sai, đa dạng chiến lược và nhiều seed.
7. **External validity còn yếu.** MMLU-Pro ở đây là bốn model trả lời độc lập rồi tổng hợp, chưa phải agent tương tác nhiều bước. Claim rộng về MAS cần môi trường thứ hai như [AppWorld](https://aclanthology.org/2024.acl-long.850/) hoặc benchmark tác vụ có tool/action khách quan.
8. **Thống kê có giới hạn.** Nhiều câu test nhưng chỉ khoảng 13–14 cụm môn; CI bootstrap theo target có thể rộng, so sánh nhiều ô chưa hiệu chỉnh multiplicity. Mở rộng test sau pilot làm xác nhận nội bộ yếu hơn một protocol khóa trước từ đầu.
9. **Giao thức reasoning chưa được đối chứng.** Trả lời trực tiếp `think=false` có thể thay đổi năng lực quan sát được. Cần pilot trước khi khẳng định nguyên nhân.
10. **Tình trạng vận hành/release:** registry và `open_questions.md` vẫn còn vài trạng thái cũ, đặc biệt OQ-1 ghi heterogeneity gate PASS từ pilot nhỏ; phải cập nhật theo GO-C khi chốt vòng sau. Chưa thấy bản thảo bài báo hoàn chỉnh hay benchmark card trong workspace.

## 11. Hướng nghiên cứu và kế hoạch các week tới

Tài liệu thiết kế chi tiết: `docs/analysis/repguard_post_week3_research_direction_2026-09-29.md`. **Không có cách đảm bảo trước phương pháp sẽ thắng hoặc bài báo sẽ được nhận.** Kế hoạch dưới đây ưu tiên kiểm tra sớm tiền đề, chi phí và đối chứng công bằng.

### Week 4 nghiên cứu (đề xuất 30/09–04/10) — sửa tiền đề trước khi mở rộng ECRT

**Mục tiêu:** biết chắc liệu pool/giao thức mới có ít nhất hai nhóm skill với agent thắng rõ hay không, và liệu tín hiệu cấp câu có thể giúp chọn đúng agent.

1. Đăng ký trước số cấu hình model/scaffold và số câu pilot; lấy từ phần train/dev MMLU-Pro **chưa dùng**, không chọn prompt bằng 2.416 câu test Week 3.
2. Chạy paired pilot direct-answer so reasoning/CoT phù hợp model, cùng câu và digest, đo accuracy, token, latency, overlap correctness, specialist theo skill chi tiết. Cân bằng đủ 14 môn; không vội chạy toàn bộ tập.
3. Kiểm tra pool có ít nhất hai agent khác nhau thắng ở các skill khác nhau theo lựa chọn từ train và xác nhận trên dev. Báo cáo cả trường hợp gate không đạt.
4. Xây baseline query-aware routing và answer-aware aggregation **đơn giản** từ train/dev, so model đơn, majority, FixedBorrow ở cùng ngân sách. Oracle 68,34% chỉ làm trần chẩn đoán, không dùng để chọn chính sách.
5. Viết bản cập nhật HistRepEval protocol và paper claim tracker, sửa OQ-1/registry vốn còn dấu tích pilot cũ.

**Gate ra Week 5:** (i) dị biệt năng lực thật ở ít nhất hai skill/agent; (ii) router/aggregator tạo gain có ý nghĩa thực dụng trên dev so baseline mạnh và không chỉ là chọn bằng test; (iii) chi phí suy luận chấp nhận được. Nếu trượt, dừng phát triển bài phương pháp ECRT/DART trên pool này; chuyển sang thiết kế benchmark/pool mới hoặc bài characterization.

**Bàn giao tuần:** protocol amendment trước khi chạy, bảng capability v2 kèm CI và chi phí, bảng router/aggregator đối chứng, quyết định gate có lý do, cập nhật `paper_claims.md` và HistRepEval manifest.

### Week 5 nghiên cứu (đề xuất 05–11/10) — phương pháp decision-aware và robustness thật

**Chỉ làm nếu Gate Week 4 qua.** Ước lượng riêng năng lực agent theo câu/skill, độ tin cậy feedback theo evaluator–agent–skill và xác suất từng đáp án đúng. Dùng **một ngân sách audit gold được khai báo** để học/kiểm tra kênh feedback; phân tầng tối thiểu theo agent–skill để không bỏ sót poisoning chọn lọc. Quy tắc quyết định phải có fallback sang model đơn khi bằng chứng yếu; nếu thêm verifier, so với **gọi thêm solver/self-consistency ở cùng token và latency**.

Chạy feedback từ judge/công cụ **thật** với nhãn đánh giá ẩn, thêm controlled corruption để phân tích nhân quả. Attack study phải có nhiều attacker, nhiều history sample/seed/budget và câu trả lời sai do attacker model sinh ra. Endpoint chính đăng ký trước là team accuracy hoặc utility rủi ro–chi phí **so FixedBorrow, model đơn và router mạnh nhất**; Brier/MAE là endpoint phụ nếu outcome chính là accuracy.

**Gate ra Week 6:** method hơn baseline ở metric chính trên dev/validation mới và không gây hại lớn trong clean condition; targeted poisoning không tệ hơn baseline theo tiêu chí đã khóa. Nếu không đạt, không tiếp tục thêm module; chuyển sang bài thực nghiệm về giới hạn của reputation, có đối chứng mạnh và mô tả lỗ hổng.

**Bàn giao tuần:** bảng phương pháp/ablation ở cùng ngân sách, báo cáo judge thật và mẫu audit, nhiều attack curves có CI, thống kê chi phí, danh sách claim được phép đưa vào bản thảo.

### Week 6 nghiên cứu (đề xuất 12–18/10) — xác nhận độc lập, bài báo và HistRepEval

Khóa prompt, model digest, hyperparameter, tập baseline, attack policy, metric và seed rồi chạy trên benchmark/pool **thứ hai**. AppWorld là lựa chọn hợp lý để có agent tương tác và kiểm thử trạng thái, nhưng [Xia & Wang](https://arxiv.org/abs/2606.14200) đã dùng AppWorld; dùng nó để xác nhận tính khái quát, không nhận là novelty. Báo cáo kết quả kể cả khi âm, ablation, bảng chi phí thực, failure cases, CI ghép cặp, giới hạn và phần không lặp lại.

Hoàn thiện HistRepEval card, script tái lập, manifest/hash, bảng kết quả machine-readable, hướng dẫn giấy phép và các hình. Bản thảo chỉ claim phương pháp vượt trội nếu kết quả mới thực sự qua gate. Nếu chỉ calibration lặp lại nhưng team outcome không đổi, đổi câu chuyện bài báo sang **khi nào feedback/transfer làm sai reputation và vì sao calibration không đủ để tăng accuracy**.

**Bàn giao tuần:** kết quả tập xác nhận độc lập, bản thảo với mọi claim nối tới bảng/hình, HistRepEval card, mã chạy lại và gói artefact có checksum. Nếu không kịp external validation trong tuần này, ghi rõ việc còn thiếu và không ghi “bài báo đã hoàn tất”.

### Đầu ra cuối cùng theo hai nhánh

| Nhánh | Điều kiện | Đầu ra trung thực |
|---|---|---|
| **Paper phương pháp mạnh** | Pool dị biệt, gain outcome trên tập mới so baseline mạnh, không giảm clean utility, chịu được attack kiểm chứng | Bài báo + mã phương pháp + HistRepEval + external validation + gói tái lập |
| **Paper characterization/benchmark** | ECRT không thắng, nhưng hiệu ứng Q/T và giới hạn quyết định lặp lại trên môi trường thứ hai | Bài thực nghiệm âm/dương có giá trị + HistRepEval được chuẩn hóa + attack/failure analysis |
| **Chưa đủ để nộp bài mạnh** | Không lặp lại hiệu ứng hoặc không có pool/task phù hợp | Báo cáo nghiên cứu trung thực; đổi pool/benchmark/câu hỏi trước khi viết claim lớn |

## 12. Gợi ý cấu trúc báo cáo tuần gửi giảng viên

Có thể trích nguyên các mục 1, 2, 5.3, 6.3, 8 và 11 để tạo bản 2–4 trang. Đoạn kết luận ngắn có thể dùng như sau:

> Đến 29/09/2026, nhóm đã hoàn tất vòng thực nghiệm Week 3 chạy thật trên đủ 14 môn MMLU-Pro, gồm 18.064 câu trả lời của bốn model và 19.656 kết quả phân tích feedback-quality × task-transfer. Kết quả cho thấy phản hồi sai và mismatch ảnh hưởng rõ đến calibration của reputation. Tuy nhiên pool hiện chỉ xác nhận một specialist, routing theo môn không hơn model đơn, và ECRT không hơn FixedBorrow về team accuracy ở điều kiện chính (+0,02 điểm phần trăm; CI 95% [−0,04; +0,10]). ECRT cải thiện Brier trong vài chế độ nhiễu mạnh nhưng pilot poisoning chọn lọc còn bộc lộ điểm yếu. Do đó quyết định khoa học là GO-C: giữ kết quả thực nghiệm, tạm dừng claim ECRT vượt trội và ưu tiên pilot giao thức suy luận/pool agent, tín hiệu chọn agent ở cấp câu, rồi mới thử phương pháp ra quyết định có audit và xác nhận trên benchmark thứ hai.

## 13. Danh mục artefact và hình đã có

| Artefact | Vai trò |
|---|---|
| `research_ops/real_week3_protocol.md` | Giao thức đăng ký, amendment sau pilot |
| `results/real_week3_json_v1/manifest.json`, `test_extension.json` | ID/split/hash/câu test mở rộng |
| `results/real_week3_json_v1/model_inventory.json` | Model ID, digest, quantization |
| `results/real_week3_json_v1/predictions.jsonl` | 18.064 phản hồi thật, prompt hash, token, latency |
| `results/real_week3_json_v1/analysis/capability_matrix.csv` và `.json` | Năng lực 14 môn, specialist và routing |
| `results/real_week3_json_v1/analysis/qt_grid_results.csv` | 19.656 hàng factorial Q×T |
| `results/real_week3_json_v1/analysis/statistical_analysis.json` | CI, paired contrasts, method differences |
| `results/real_week3_json_v1/analysis/attack_capital_curves.csv`, `attack_scenarios.json` | A1/A2 pilot và budget curves |
| `results/real_week3_json_v1/analysis/figures/` | Heatmap năng lực, Q×T accuracy/Brier/unique-expert, ECRT vs FixedBorrow, attack curves; PNG/PDF |
| `analyze_real_week3.py`, `attack_real_week3.py`, `figures_real_week3.R` | Mã phân tích/tấn công/hình |
| `docs/analysis/repguard_week3_real_report.md` | Báo cáo kết quả Week 3 nguồn |
| `docs/analysis/repguard_post_week3_research_direction_2026-09-29.md` | Đề xuất hướng sau Week 3 |

**Quy tắc trích dẫn số liệu:** ưu tiên báo cáo Week 3 thật và các artefact `real_week3_json_v1`; các bảng `results/week2_reputation/` và `results/week3/` cũ chỉ là engineering/exploratory và không được pha vào kết quả thực nghiệm cuối.
