# RepGuard — Week 3, thực nghiệm trên câu trả lời model thật

Ngày chạy: 2026-09-29. **Trạng thái thực nghiệm: hoàn tất. Quyết định khoa học: GO-C / sửa hướng phương pháp.**

## 1. Quyết định về kết quả cũ

Kết luận `WEEK 3 COMPLETE / GO-B` ghi ngày 2026-09-28 **không còn hiệu lực**. Lưới Q×T và attack pilot cũ dùng correctness được rút ngẫu nhiên từ tỷ lệ đúng ước lượng trên một audit quá nhỏ, thay vì dùng câu trả lời thật trên từng câu hỏi. Mẫu audit cũ chỉ có 8/14 môn và lịch sử còn có chỗ ghi nhầm model `gemma2` thành cấu hình `qwen3:14b`. Kết quả cũ chỉ là kiểm thử kỹ thuật của pipeline, không phải bằng chứng khoa học cho bài báo.

## 2. Nguồn dữ liệu và giao thức mới

- Dữ liệu: bản local `TIGER-Lab/MMLU-Pro`, 12.032 câu, 14 môn. Split hash seed 42: 7.241 train/calibration, 2.375 dev, 2.416 test. Manifest định danh từng câu và hash tập dữ liệu trong `results/real_week3_json_v1/manifest.json`.
- Model thật trên Modal/Ollama: `qwen3:8b`, `gemma2:latest`, `llama3:8b`, `qwen3:0.6b`; digest cụ thể có trong `results/real_week3_json_v1/model_inventory.json`. Tất cả dùng cùng zero-shot direct-answer prompt, nhiệt độ 0, `think=false`, JSON-schema enum theo các đáp án hợp lệ. Đây không phải thiết lập CoT/few-shot của leaderboard MMLU-Pro; độ chính xác tuyệt đối không được so trực tiếp với leaderboard.
- Tập history lấy đúng 100 câu/môn từ train/calibration (1.400 câu); dev hiệu chuẩn phản hồi lấy đúng 50 câu/môn (700 câu); toàn bộ test được dùng để đánh giá cuối cùng. Ban đầu protocol ghi 70 câu test/môn. Sau pilot 70 câu/môn, do nhiều khoảng cách top-2 chỉ vài câu, đã mở rộng **đồng đều cho cả 14 môn** đến toàn bộ test (2.416 câu/model). Tổng thiết kế là 18.064 lượt trả lời thật. `test_extension.json` lưu hash manifest gốc, danh sách ID thêm và lý do. Việc mở rộng sau khi xem pilot là một amendment công khai, nên các khoảng tin cậy vẫn cần đọc ở mức thăm dò.
- Ledger `results/real_week3_json_v1/predictions.jsonl` lưu model ID, task ID, split, subject, prompt hash, raw JSON response, token/latency. Ground truth không nằm trong prompt hay ledger; scorer đọc benchmark riêng. `analyze_real_week3.py` kiểm tra mapping task/split, model ID, số đáp án, prompt hash, đáp án raw và trùng lặp trước khi phân tích.
- Audit cuối: **18.064/18.064** model–task rows, mỗi model có đúng `[1.400 history, 700 dev, 2.416 test]`, **0 missing, 0 duplicate, 0 invalid answer**, không có file lỗi. SHA-256 ledger: `1c69cd9d49f3b2c97bf20868e246c5b524492a0f28f9b0095170fa1dded9fd4e`.
- Kiểm tra mã: toàn bộ **183/183 unit tests** qua; script analysis chạy hết 182 cặp và script R xuất đầy đủ capability, team accuracy, Brier, unique-expert và attack figures ở cả PNG/PDF. Các hình đã được mở kiểm tra hiển thị.

## 3. Audit năng lực trên toàn bộ test

Mỗi model đã trả lời đủ 2.416 câu test. Không có đáp án `UNKNOWN` hoặc lỗi JSON trong tập test. Wilson 95% interval dưới đây mô tả sai số lấy mẫu ở cấp câu; các câu cùng môn và các model ghép cặp nên không dùng chúng làm kiểm định hiệu quả định tuyến.

| Model | Đúng / 2.416 | Micro accuracy | Wilson 95% CI | Trung bình 14 môn |
|---|---:|---:|---:|---:|
| Qwen3 8B | 1.154 | 47,76% | 45,78–49,76% | 49,19% |
| Gemma2 | 1.090 | 45,12% | 43,14–47,11% | 47,53% |
| Llama3 8B | 877 | 36,30% | 34,41–38,24% | 38,52% |
| Qwen3 0.6B | 568 | 23,51% | 21,86–25,24% | 23,90% |

Số câu đúng theo môn (mẫu test có kích thước khác nhau; chỉ đọc theo tỷ lệ trong cùng hàng):

| Môn | n | Qwen3 8B | Gemma2 | Llama3 8B | Qwen3 0.6B |
|---|---:|---:|---:|---:|---:|
| biology | 146 | 110 | 105 | 94 | 60 |
| business | 167 | 74 | 64 | 43 | 37 |
| chemistry | 234 | 97 | 83 | 57 | 52 |
| computer science | 97 | 49 | 56 | 41 | 28 |
| economics | 171 | 106 | 95 | 84 | 62 |
| engineering | 203 | 92 | 88 | 76 | 44 |
| health | 156 | 85 | 79 | 65 | 26 |
| history | 72 | 35 | 36 | 28 | 11 |
| law | 226 | 72 | 83 | 70 | 45 |
| math | 249 | 92 | 83 | 53 | 42 |
| other | 187 | 89 | 90 | 69 | 42 |
| philosophy | 110 | 44 | 49 | 43 | 18 |
| physics | 254 | 116 | 82 | 66 | 51 |
| psychology | 144 | 93 | 97 | 88 | 50 |

Qwen3 8B hơn Gemma2 2,65 điểm phần trăm trên cùng 2.416 câu (paired task bootstrap thăm dò: khoảng 0,66–4,64 điểm). Chỉ riêng physics có khoảng cách Qwen3 8B so Gemma2 lớn, 116/254 so với 82/254; nhiều môn còn lại có top-2 cách nhau rất ít. Vì vậy cần tách “model tốt nhất quan sát trên test” khỏi “model chuyên gia được chọn độc lập từ history”.

Trần lạc quan chọn **model tốt nhất cho từng môn bằng nhãn test** là 48,97%, chỉ hơn 1,21 điểm so với một Qwen3 8B dùng mọi câu. Ngược lại, có ít nhất một model đúng ở 68,34% câu, và 22,72% câu chỉ có đúng một model đúng. Pool có bổ trợ mạnh ở cấp câu hỏi, nhưng nhãn môn có thể quá thô để định tuyến hiệu quả. Cả hai con số oracle đều dùng nhãn test và **không** phải phương pháp triển khai.

### Gate chuyên gia và routing không rò test

Với từng môn, chọn ứng viên có accuracy cao nhất trên **100 câu history**, rồi so ghép cặp trên toàn bộ câu test môn đó với ba model còn lại. Một chuyên gia chỉ được xác nhận khi cả ba 95% paired-bootstrap CI của lợi thế đều nằm trên 0. **Chỉ Qwen3 8B ở physics** đạt gate: 116/254 đúng so với Gemma2 82/254; chênh +13,39 điểm phần trăm, CI [+7,48; +19,29]. Không có model thứ hai đạt gate, nên điều kiện dị biệt năng lực mạnh của đề tài **không đạt**. Các môn Gemma2 quan sát thắng như law, history, philosophy, psychology đều có CI với Qwen3 8B chứa 0; vài ứng viên được history chọn còn thua model khác trên test.

Routing theo môn chọn từ history đạt **1.140/2.416 = 47,19%**, trong khi model đơn Qwen3 8B chọn từ history toàn cục đạt **1.154/2.416 = 47,76%**. Chênh lệch routing −0,58 điểm phần trăm, paired task bootstrap 95% CI [−1,90; +0,75]; không có bằng chứng cải thiện. Trần oracle theo môn dùng nhãn test là 1.183/2.416 = 48,97%.

## 4. Phân tích Q×T và attack pilot

### Thiết kế và đơn vị suy luận

Q có bốn mức: oracle, lật phản hồi đối xứng 25% và 50%, cùng 40% false-positive **trên các câu sai**. T có ba mức nguồn history so với target: same, related và unrelated theo taxonomy cố định. Chạy mọi cặp nguồn–đích hợp lệ, 3 seed và 9 phương pháp: **182 cặp × 4 Q × 3 seed × 9 phương pháp = 19.656 hàng**. Có 13 target đủ cả ba mức T; `other` vẫn ở audit capability nhưng không nằm trong factorial ba mức. History lấy câu trả lời model thật; chỉ observed feedback bị can thiệp. Dev rời history và test dùng để hiệu chuẩn độ tin cậy phản hồi. Các phương pháp được so trên cùng câu hỏi và cùng câu trả lời test.

Mỗi target được trọng số bằng nhau; nguồn và seed được trung bình **bên trong target**, rồi bootstrap 13 target subject để lấy CI 95%. Các CI là thăm dò, không điều chỉnh đa so sánh. Brier dưới đây là binary-outcome Brier cho xác suất năng lực từng model; **thấp hơn tốt hơn**. Team accuracy và unique-expert success **cao hơn tốt hơn**.

| Điều kiện / phương pháp | Team accuracy | Brier | Unique-expert success |
|---|---:|---:|---:|
| same + oracle: Uniform | 47,82% | 0,2500 | 9,45% |
| same + oracle: GlobalBeta / FixedBorrow | 49,64% | 0,2206 | 13,76% |
| same + oracle: ECRT | 49,60% | 0,2206 | 14,19% |
| related + 25% noise: SkillConditioned | 47,82% | 0,2500 | 9,45% |
| related + 25% noise: FixedBorrow | 49,28% | 0,2422 | 12,74% |
| related + 25% noise: ECRT | 49,29% | 0,2510 | 12,74% |
| same + 50% noise: FixedBorrow | 47,89% | 0,2495 | — |
| same + 50% noise: ECRT | 47,83% | 0,2304 | — |
| same + directional false-positive: FixedBorrow | 49,69% | 0,2763 | — |
| same + directional false-positive: ECRT | 49,68% | 0,2243 | — |

**Q có hiệu ứng rõ với calibration.** Ở GlobalBeta cùng môn, lật 50% làm Brier xấu thêm **+0,0290** (CI [+0,0200; +0,0385]) và team accuracy giảm **−1,75 điểm phần trăm** (CI [−3,09; −0,53]). Directional false-positive làm Brier GlobalBeta cùng môn xấu thêm **+0,0557** (CI [+0,0440; +0,0661]).

**T có hiệu ứng rõ với calibration nhưng không chứng minh được lợi ích team accuracy mạnh.** Với GlobalBeta và phản hồi oracle, Brier same thấp hơn related **0,0265** (CI [0,0133; 0,0421]); chênh team accuracy same–related là −0,02 điểm phần trăm (CI [−0,38; +0,39]). Tương tác Q×T ở GlobalBeta khi lật 50% có Brier difference-in-differences (unrelated so same) **−0,0246** (CI [−0,0347; −0,0154]), nhưng chênh team accuracy tương ứng có CI chứa 0. Hiệu ứng Brier tương tác của ECRT/FixedBorrow trong unrelated còn chịu tác động **cơ học** của `tau=0`, khiến score luôn trở về prior 0,5; không được diễn giải như bằng chứng rằng skill transfer thật bằng 0.

**ECRT chưa vượt baseline công bằng về outcome.** Ở ô chính đã ghi trong protocol (related + 25% noise), ECRT so FixedBorrow: team accuracy **+0,02 điểm phần trăm** (CI [−0,04; +0,10]), Brier **+0,0088** (CI [−0,0003; +0,0181], dấu dương là xấu hơn), unique-expert success bằng nhau. So SkillConditioned, ECRT tăng team accuracy +1,47 điểm (CI [+0,46; +2,43]), nhưng FixedBorrow cũng đạt mức đó; phần lợi ích đến từ cho phép mượn bằng chứng related, chưa xác nhận novelty của hiệu chuẩn ECRT. So ablation bỏ reliability, ECRT chỉ +0,02 điểm team accuracy (CI [−0,02; +0,08]). Ở same + oracle, ECRT so FixedBorrow −0,03 điểm (CI [−0,10; 0]); không thấy cải thiện sạch. So model đơn Qwen3 8B trên 13 target, ECRT same + oracle +0,29 điểm (CI [−1,54; +2,15]) và related + 25% noise −0,02 điểm (CI [−1,88; +1,84]).

**Có một lợi ích hẹp về calibration dưới nhiễu mạnh.** Same + 50% symmetric noise, ECRT giảm Brier so FixedBorrow **0,0192** (CI [0,0104; 0,0281]); same + directional false-positive giảm **0,0520** (CI [0,0408; 0,0617]). Related + directional false-positive giảm **0,0429** (CI [0,0115; 0,0722]). Tuy vậy các mức team accuracy ở cùng điều kiện gần bằng nhau; lợi ích xác suất chưa chuyển thành cải thiện chọn đáp án.

### A1/A2 strategic pilot

Chọn scenario **chỉ bằng dev**: A1 là Qwen3 8B trên economics (dev accuracy 68%); A2 là Gemma2 history biology → target chemistry (dev source 64%, dev target 24%, gap 40 điểm). Dùng các câu trả lời gốc thật; trong phép thử can thiệp, câu trả lời test của attacker bị thay bằng một đáp án biết chắc sai nhờ ground truth, và biến thể poisoning đổi feedback sai của riêng attacker thành positive. Đây là **stress test can thiệp có oracle**, chưa phải lời nói dối tự phát do model tạo ra. Một scenario/loại và một thứ tự 100 câu history không đủ để ước lượng tần suất tấn công ngoài đời.

- A1, budget 5, history honest: ECRT đặt 89,3% tổng trọng số vào attacker và mất 62,0 điểm team accuracy khi attacker bị ép sai; FixedBorrow/SkillConditioned mất 17,5 điểm. Kết quả cực đoan này nhạy với 5 câu đầu và cần lặp lại nhiều mẫu lịch sử trước khi khẳng định tổng quát.
- A2, budget 100, feedback attacker false-positive: ECRT cho attacker 36,9% trọng số và mất 16,7 điểm team accuracy; FixedBorrow 33,7% và mất 11,1 điểm; SkillConditioned 25,0% và mất 8,1 điểm. Vì biology và chemistry được taxonomy gắn `related`, ECRT hiện **không chặn** laundering trong scenario này.
- Calibration ECRT xử lý được nhiễu false-positive **đồng đều** khi dev phản ánh cơ chế nhiễu, nhưng dev honest không phát hiện poisoning **có chủ đích riêng cho attacker**. Hai can thiệp có giả thiết khác nhau; không được dùng kết quả Q×T để suy ra robustness trước tấn công.

## 5. Quyết định Week 3 và hướng bài báo

**Week 3 đã hoàn tất ở mức thực nghiệm và báo cáo**, nhưng gate khoa học cho câu chuyện phương pháp ban đầu **không qua**. Có hiện tượng thực: chất lượng phản hồi và mismatch làm sai lệch calibration, với CI theo target có dấu rõ ở một số điều kiện. Tuy nhiên pool chưa có từ hai specialist ổn định trở lên; routing theo môn không hơn model đơn; ECRT không hơn FixedBorrow về team accuracy ở ô định trước và có lỗ hổng trong pilot poisoning có mục tiêu. Theo lựa chọn trong kế hoạch 6 tuần, quyết định phù hợp nhất là **GO-C: baseline đơn giản giải quyết phần outcome hiện thấy; tạm dừng claim ECRT superiority, sửa pool/task signal và đóng khung đóng góp thực nghiệm**. Đây không phải GO-D vì trong thí nghiệm này đã quan sát được hiệu ứng calibration có CI tách 0; cũng chưa phải GO-A/B cho paper phương pháp mạnh.

Hướng tiếp theo theo thứ tự ưu tiên:

1. **Sửa tiền đề specialist trước khi mở rộng phương pháp.** Chọn pool có khác biệt được xác nhận trên split độc lập, hoặc chuyển từ nhãn môn sang thuộc tính câu hỏi/skill chi tiết. Đánh giá routing từ history trên benchmark thứ hai, giữ split test khóa; không chọn specialist bằng test.
2. **Tách hai mục tiêu kết quả.** Nếu paper là reputation calibration, xem Brier/MAE/decision cost là primary và xây decision rule dùng xác suất đã hiệu chuẩn. Nếu paper là team accuracy, phải chứng minh cải thiện so FixedBorrow và model đơn, với CI và ít nhất hai pool/benchmark.
3. **Sửa mô hình đe dọa.** Hiệu chuẩn phản hồi theo evaluator/agent và phát hiện poisoning cục bộ hoặc thay đổi đột ngột; kiểm tra nhiều attacker, nhiều seed lịch sử, nhiều mức budget, và phản hồi tấn công do model thực sự tạo ra. Pilot hiện chỉ là upper-bound can thiệp.
4. **Đăng ký thí nghiệm xác nhận mới** trước khi xem kết quả: tập dữ liệu độc lập, taxonomy transfer đo trên dev, kiểm định route/aggregation ở test mới, ablation của reliability và uncertainty. Không dùng cùng 2.416 test câu để tối ưu rồi gọi lại là xác nhận độc lập.

**Gate đề xuất cho vòng xác nhận tiếp theo:** (i) ít nhất hai model khác nhau được chọn bằng history/dev và thắng mọi đối thủ trên các nhóm task khác nhau, với CI ghép cặp tách 0; (ii) routing học từ dữ liệu không phải test vượt model đơn mạnh nhất với CI tách 0 và mức tăng thực dụng được đăng ký trước; (iii) ECRT vượt FixedBorrow trên endpoint chính, đồng thời không giảm đáng kể clean performance; (iv) trong nhiều kịch bản poisoning có model attacker tạo câu trả lời thật, loss của ECRT không lớn hơn baseline công bằng. Nếu (i) không đạt, dừng phát triển ECRT để sửa pool/skill representation; nếu (i) đạt mà (iii) không đạt, chuyển đóng góp chính sang benchmark/characterization. Dùng một tập xác nhận mới cho các gate này, và báo cáo số lần thử pool để tránh chọn lọc hậu nghiệm.

Artefact: `results/real_week3_json_v1/analysis/capability_matrix.json`, `statistical_analysis.json`, `qt_grid_results.csv`, `attack_capital_curves.csv`, `domain_pairs.json`, và các heatmap/curve PNG+PDF trong `analysis/figures/`. Chúng có thể tái tạo từ manifest, ledger, script và model digest trong cùng thư mục kết quả.

## 6. Giới hạn cần giữ trong bản thảo

1. Chỉ có một benchmark và một lần chạy trực tiếp mỗi model/câu. Mẫu test rất lớn nhưng chỉ 14 cụm subject; CI theo subject sẽ rộng hơn CI ở cấp câu.
2. Mô hình đều là generalist; không có bằng chứng mặc định rằng pool có chuyên gia thật theo domain. Việc chọn model thắng trực tiếp trên test là phép đo oracle lạc quan, tuyệt đối không dùng làm chính sách routing được đánh giá công bằng.
3. Giao thức zero-shot JSON trực tiếp thay đổi mức accuracy tuyệt đối so với thiết lập benchmark công bố. `think=false` áp dụng cho mọi model để giảm khác biệt do output parsing, nhưng có thể bất lợi với model vốn dùng reasoning dài.
4. Q là nhiễu/thiên lệch phản hồi được can thiệp có seed trên correctness của câu trả lời thật; đây là thí nghiệm nhân quả về thuật toán reputation dưới tín hiệu giả lập, chưa phải quan sát evaluator ngoài đời. T là taxonomy metadata cố định, chưa được xác thực là độ gần kỹ năng thật.
5. Mở rộng test sau khi xem pilot được áp dụng đồng đều cho tất cả môn nhưng vẫn là quyết định hậu pilot. Mọi tuyên bố khẳng định mạnh cần kiểm tra lại trên benchmark, pool và seed độc lập.
6. Thư mục `results/` đang bị Git bỏ qua. Trước khi chia sẻ bài báo, cần đóng gói ledger, manifest, model inventory, checksum và bản sao dữ liệu đầu vào vào một kho artefact có phiên bản; chỉ commit mã và báo cáo sẽ không đủ để người khác kiểm tra lại số liệu.
