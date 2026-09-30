# RepGuard tiếp theo — protocol và tiêu chuẩn dừng trước lượt xác nhận mới

**Ngày khóa bản kế hoạch:** 30/09/2026. Đây là protocol làm việc, không phải bằng chứng DART đã thắng. Kết quả Week 3 và pipeline bổ sung nằm trong [`repguard_final_pipeline_assessment_2026-09-30.md`](repguard_final_pipeline_assessment_2026-09-30.md).

## 1. Câu hỏi khoa học và điểm mới cần chứng minh

Trong một pool agent/model có năng lực khác nhau, khi feedback lịch sử từ judge có thể sai và chi phí suy luận hữu hạn, liệu **audit có ngân sách và quyết định có ngưỡng bất định** có tăng chất lượng đáp án ở cùng ngân sách so với router, reputation transfer và solver mạnh nhất hay không? Một thuật toán chỉ giảm Brier nhưng không đổi lựa chọn/accuracy không đủ cho claim phương pháp.

Không dùng tên “DART” như một kết quả đã được kiểm chứng. DART tạm là giả thuyết gồm: (a) năng lực agent theo câu/skill; (b) độ đáng tin của nguồn feedback theo agent/skill, ước lượng bằng gold audit hạn chế; (c) giá trị dự kiến và khoảng bất định của hành động direct, thinking, agent khác hoặc kiểm chứng; (d) fallback về baseline mạnh khi lợi ích không chắc. Làm ablation riêng từng phần.

Kiểm tra novelty đặc biệt chặt: [CP-Router (AAAI 2026)](https://ojs.aaai.org/index.php/AAAI/article/view/40589) đã route giữa LLM/LRM ở bài trắc nghiệm để tiết kiệm token; [Xia & Wang 2026](https://arxiv.org/abs/2606.14200) đã xét reputation theo skill và laundering; [Ebrahimi et al. 2025](https://aclanthology.org/2025.ijcnlp-long.90/) đã dùng credibility lịch sử; [WAFER-QA](https://arxiv.org/abs/2506.03332) đã xét judge đánh lừa agent; [Gozel 2026](https://arxiv.org/abs/2609.00088) chỉ ra blind/commit-first judge vẫn chịu lỗi của chính judge. Vì vậy claim cần là **giá trị quyết định đo được của audit dưới feedback không tin cậy**, không phải “lần đầu dùng trust/router/blind judge”.

Rà soát bổ sung trong ngày 30/09: [BEST-Route (ICML 2025)](https://arxiv.org/abs/2506.22716) đã kết hợp routing và số lần lấy mẫu theo ngân sách; [Budgeted Act-or-Defer (2026)](https://arxiv.org/abs/2606.29654) đã dùng reliability bound địa phương và ngân sách wrong-action trong hội nghị đa agent; [Share the Judge, Learn the Deferral (2026)](https://arxiv.org/abs/2607.27984) đã dùng audited deferral cascade cho judge; [TRUST-Bench/VISTA-Guard (2026)](https://arxiv.org/abs/2605.17453) đã nghiên cứu poisoning feedback công cụ theo lịch sử. Vì vậy riêng việc thêm lower confidence bound, act/defer, hoặc audit judge **không đủ mới**. Cần so trực tiếp với những nguyên tắc này, hoặc thu hẹp đóng góp vào bài benchmark/measurement nếu method không thắng ở endpoint mới.

## 2. Dữ liệu và ranh giới phát triển/xác nhận

- Tập cũ Week 3 test 2.416 câu và Week 5 dev 280 câu đã được xem; mọi phân tích tiếp trên đó là **thăm dò**.
- Script `freeze_real_next_study.py` đã khóa từ phần **train/calibration chưa dùng** của split MMLU-Pro cũ: 40 câu/môn × 14 = **560 development** và 30 câu/môn × 14 = **420 sealed holdout**. Cả hai không trùng task ID của các manifest và ledger thật trước đó. Protocol hash của `results/real_next_study_v1/frozen_splits.json`: `0bd154554e845ca472f73a5c113985a115b4f1a55322092909d798e45b326d1d`. Không xem gold hay outcome của sealed holdout trước khi khóa method, baseline, endpoint và attack policy.
- Kết quả routing trên 420 câu Week 4 train và 280 câu Week 5 dev từ `analyze_real_routing_gate.py` là **offline replay của hai output model thật đã chạy**, không tạo đáp án mô phỏng. Cả hai tập đã có kết quả được xem trong quá trình nghiên cứu nên không dùng làm final confirmation.
- Benchmark thứ hai cần chốt trước phép kiểm định cuối. Một lựa chọn MCQ nhanh là [ARC-Challenge](https://huggingface.co/datasets/allenai/ai2_arc); môi trường agent nhiều bước có ý nghĩa thực tiễn hơn là [AppWorld](https://aclanthology.org/2024.acl-long.850/), nhưng đòi hỏi triển khai/tool traces và đã được nghiên cứu skill-conditional trust sử dụng. Chọn dựa trên câu hỏi khoa học, license, dữ liệu công khai và tài nguyên, không chọn sau khi nhìn outcome có lợi.

## 3. Giai đoạn đang chạy: pool overlap trên câu đã có thinking

- `run_real_pool_overlap.py` đóng băng ba model `gemma2:latest`, `llama3:8b`, `qwen3:14b` ở `think=false`, JSON answer enum, 64 token, temperature 0; đúng **420 ID train** của Qwen3 8B direct/thinking screen. Protocol hash `f4d3b237728c0b0463c49e47673793e9e1290903c187f0741dc533f51e4c7308`.
- Chạy pilot 1 câu/môn/model để kiểm tra end-to-end rồi mở rộng 30 câu/môn/model nếu valid và ổn định. Mọi response được ghi append-only cùng model digest, task ID, prompt hash, raw answer, token và latency. `analyze_real_pool_overlap.py` kiểm tra các trường này và so ghép cặp trên cùng ID.
- Gate tiền đề: mô tả `model-only-correct` so Qwen3 thinking, độ bổ trợ giữa model, domain/skill specialist và chi phí. **Oracle any-of-pool là chẩn đoán dùng gold**, không phải thành tích hệ thống. Nếu thinking model đơn áp đảo và phần bổ trợ không thể dự báo, dừng phát triển DART trên pool này; vẫn có thể giữ nghiên cứu routing chi phí/HistRepEval.

## 4. Sàng lọc routing sớm bằng output thật đã có

Kết quả hiện tại chỉ để quyết định bước kế tiếp. Ridge score được học từ 420 câu train; các quota 25/50/75% thinking cố định, đánh giá trên 280 câu dev khác ID. Đây là replay, không phải yêu cầu model mới hay một online policy đã kiểm chứng.

| Policy tại quota 50% thinking | Đúng / 280 | Output token | Ghi chú |
|---|---:|---:|---|
| Luôn direct | 137 | 2.734 | Điểm rẻ |
| Chọn ngẫu nhiên, kỳ vọng | 170 | — | Kỳ vọng xác suất, không phải một lần chạy |
| Router feature câu hỏi trước trả lời | 181 | 290.763 | Thăm dò |
| Router chỉ dùng subject | 185 | 282.301 | Baseline đơn giản mạnh |
| Direct trước rồi router | 186 | 302.750 | Bao gồm chi phí direct mọi câu |
| Luôn thinking | 203 | 581.165 | Điểm accuracy mạnh |

Ở quota 75%, direct-first đạt 199/280 với 447.815 output token; giảm chi phí token quan sát được so luôn thinking nhưng mất 4 câu đúng. Chưa có kiểm định non-inferiority đã khóa và chưa cạnh tranh với CP-Router ở đúng giao thức. Bước này chỉ cho thấy **tín hiệu routeability đáng nghiên cứu**, không chứng minh DART hay claim mới.

Một chẩn đoán khác dùng `analyze_real_decision_guard_pilot.py`: từ 280 câu history có judge thật, mỗi fold lấy 10 câu/môn để audit judge, 10 câu/môn làm reputation history, chọn ngưỡng đổi đáp án trên 700 câu dev Week 3 và replay trên 2.416 câu test Week 3 đã xem. Sau nhiều biến thể ngưỡng và cách gộp đáp án đã được thử **trong cùng lượt khám phá**, FixedBorrow + weighted vote + guard đạt **1.148/2.416** ở fold 0 và **1.163/2.416** ở fold 1; ECRT + weighted vote + guard chọn ngưỡng rất cao và giữ nguyên model đơn **1.154/2.416** ở cả hai fold. FixedBorrow + answer-level Bayes giả định lỗi độc lập đạt **1.161/1.165**; ECRT dùng posterior mean với cùng aggregator đạt **1.158/1.163**. Dùng lower bound như xác suất Bayes làm kết quả xấu hơn rõ, cho thấy uncertainty bound không nên thế chỗ xác suất hiệu chuẩn. Các chênh rất nhỏ và test đã được xem; đây **không phải** bằng chứng phương pháp mới. Nó bác bỏ kỳ vọng rằng chỉ gắn threshold hoặc đổi công thức vote vào ECRT hiện tại sẽ đủ tạo bài mạnh.

`analyze_real_decision_sensitivity.py` đo nguyên nhân gần: trên mỗi fold 2.416 câu test cũ, ECRT và FixedBorrow có trung bình chênh khoảng **0,103–0,105** ở xác suất reputation agent nhưng chỉ chọn **37** hoặc **41** đáp án cuối khác nhau (1,53–1,70% câu). Trong các câu đổi đáp án, ECRT thắng riêng **8/9** câu và FixedBorrow thắng riêng **4/8** câu ở fold 0/1. Hai fold dùng chung test nên không phải hai lần xác nhận độc lập. Điểm nghẽn của phương pháp là **độ nhạy của quyết định**, không chỉ lỗi calibration; đây là một metric cần đưa vào HistRepEval.

## 5. Thiết kế kiểm định DART nếu pool qua gate

1. **Định nghĩa endpoint trước khi mở sealed holdout:** accuracy tại ngân sách output token/call/latency đã khóa và có tính chi phí history/judge/audit theo cách amortize công khai. Một operating point đề xuất là ngân sách bằng khoảng 50% output token của always-thinking; cũng báo toàn bộ đường accuracy–cost. Nếu mục tiêu là “accuracy gần bằng với ít token hơn”, đặt biên non-inferiority và CI phù hợp trước khi chạy.
2. **Baselines:** always thinking, always direct, random quota, subject router, question-only router, direct-first router, best single model, majority, FixedBorrow, ECRT, skill-conditional trust và self-consistency/thêm solver ở cùng compute. Muốn so với CP-Router thì tái hiện đúng tín hiệu uncertainty hoặc ghi rõ hạn chế API; một proxy khác không được gọi là tái lập CP-Router.
3. **Nguồn feedback:** oracle gold chỉ cho audit budget rõ ràng; candidate-conditioned judge và blind judge có ledger thực; thêm fresh judge batch với prompt khóa; corruption đối xứng/directional để phân tích nhân quả, targeted poisoning theo agent/skill để kiểm tra deployment risk. Không huấn luyện/evaluate trên cùng gold task. Giữ một phần audit chọn ngẫu nhiên bên cạnh audit theo giá trị đảo quyết định.
4. **Method và ablation:** ước lượng xác suất đúng theo agent/skill/câu, sai số của evaluator, xác suất mỗi **đáp án** đúng và uncertainty; chọn hành động khi lower bound của lợi ích utility vượt ngưỡng đã học ở development. So các ablation bỏ audit, bỏ transfer, bỏ uncertainty guard, bỏ answer-level aggregation. Nếu phần phức tạp không tăng endpoint chính, bỏ nó.
5. **Thống kê:** paired comparison trên cùng câu, CI bootstrap theo câu phân tầng subject, thêm phân tích theo benchmark/pool và sensitivity theo seed. Với nhiều baseline chính, khóa thứ tự kiểm định hoặc điều chỉnh; không chọn cell tốt nhất hậu nghiệm để tuyên bố thắng. Báo invalid/truncated là lỗi.
6. **External replication:** khóa code/prompt/threshold trên MMLU-Pro rồi chạy benchmark/pool thứ hai. Nếu claim multi-agent tương tác, phải có môi trường nhiều bước; các mô hình trả lời trắc nghiệm độc lập chỉ hỗ trợ claim về ensemble/routing.

## 6. Quyết định GO/STOP

**GO-method** chỉ khi (i) pool có bổ trợ thật và feature trước gold có thể khai thác; (ii) DART tăng endpoint quyết định so baseline mạnh ở ngân sách bằng nhau trên holdout chưa xem; (iii) ablation chứng minh phần audit/reputation riêng; (iv) under targeted poisoning không mất nhiều hơn baseline theo biên đã khóa; (v) external replication cùng chiều. **STOP-method** nếu một trong các tiền đề đầu trượt: chuyển thành HistRepEval/measurement paper với kết quả âm rõ ràng, không tiếp tục chỉnh tên hoặc công thức để tìm cell đẹp. Không có cổng nào bảo đảm bài được nhận.

### Kết quả sau khi khóa kế hoạch và chạy đủ pool

Đã hoàn tất **1.260/1.260** câu trả lời mới, không có lỗi/invalid. Phân tích độc lập ở [`repguard_pool_gate_assessment_2026-09-30.md`](repguard_pool_gate_assessment_2026-09-30.md), raw ledger SHA-256 `81319c132b75d7822027d943fe67c05c8c616c366e57ea46473d0b0289da0437`. Qwen3 8B thinking đúng **280/420**; Qwen3 14B direct **226/420**; Gemma2 **195/420**; Llama3 8B **158/420**. Oracle biết gold trước để chọn một trong năm đáp án đúng **344/420**, nhưng router chọn model theo subject bằng cross-fit chỉ đạt **274/420**, thấp hơn luôn thinking **6 câu**, 95% bootstrap CI của chênh accuracy **[−3,57; +0,71] điểm phần trăm**. Qwen3 14B direct dẫn thinking ở engineering 18/30 so 13/30, nhưng các môn khác không cho hai specialist thắng rõ độc lập.

**Gate 0 cho DART trên pool MMLU-Pro này: STOP.** Giữ sealed holdout nguyên trạng; không thử nhiều biến thể DART lên holdout để săn kết quả. Hướng tiếp theo là thiết kế pool/benchmark thực sự có khác biệt kỹ năng và feedback lịch sử, hoặc phát triển HistRepEval như measurement artifact. Routing tiết kiệm token vẫn là đường kỹ thuật phụ, nhưng cần so CP-Router/BEST-Route ở chi phí công bằng và không gọi đó là đóng góp DART đã xác nhận.
