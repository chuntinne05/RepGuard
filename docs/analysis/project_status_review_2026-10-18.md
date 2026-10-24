# RepGuard — rà soát tiến độ và nút thắt ngày 18/10/2026

**Kết luận:** dự án đã hoàn tất nhiều vòng thu thập, replay và phân tích development; chưa xác nhận được ECRT/DART cải thiện quyết định so với đầy đủ đối chứng mạnh. Điểm dừng hiện tại là trước một protocol mới cho verifier FinQA độc lập và trước triển khai ứng viên paired incumbent audit. Hướng bài hiện tại là giá trị quyết định của feedback lịch sử dưới ngân sách audit hữu hạn, với HistRepEval là giao thức đánh giá và DART là phương pháp có điều kiện.

**Phạm vi kiểm tra:** rà soát bộ 97 tài liệu Markdown và 23 JSON gốc trong `docs/analysis`, README, năm tệp `research_ops`, lịch sử Git, sổ tay nguồn LaTeX ngày 08/10, các trạng thái run local và mã liên quan tới cơ chế ECRT/history rectifier/FinQA. Các tài liệu dài được đối chiếu theo giả thuyết, thiết kế, kết quả, quyết định và tài liệu kế tiếp; đây không phải kiểm toán toàn bộ từng dòng mã. Kết quả thí nghiệm cuối mới nhất tìm thấy là consensus FinQA hoàn tất lúc **00:00:46 ngày 07/10** giờ Việt Nam; quyết định chiến lược gần nhất ngày **07/10**, sổ tay tổng hợp ngày **08/10**. Không thấy kết quả mới hơn trong workspace tới ngày rà soát. Không truy vấn trạng thái Modal trực tiếp trong lượt này.

## 1. Tiến độ thực chất

| Phần việc | Đã có bằng chứng | Còn thiếu |
|---|---|---|
| Hạ tầng nghiên cứu | Harness, providers, split/hash, GT isolation, ledger, checkpoint/resume, collectors, baselines, analyzers, tests | Chuẩn hóa artifact công bố và quy trình tái lập bên ngoài |
| ECRT/MMLU-Pro | 18.064 đáp án thật, đủ 14 môn; Q×T và attack pilots; phân tích calibration và decision sensitivity | Lợi ích outcome riêng so FixedBorrow; xác nhận độc lập; robustness rộng |
| Thinking/fallback | Thinking mạnh hơn direct; fallback invalid hữu ích trên development | Selector/router đủ gain để bù chi phí gọi thêm model |
| Agent AppWorld chạy mới | Pilot v1–v10, chấm state-check; lỗi scaffold/version/transport có ghi nhận | Pool agent mới có năng lực và rescue hai chiều ổn định |
| DART trên AppWorld archive | 14 agent ×168 task/56 generator; 2.352 judgment thật; replay và nhiều ablation | Superiority trước toàn bộ controls; tổng cost tương đương; confirmation mới |
| Neural DART | P0 đủ 5 folds/135 fits; dừng đúng gate | P0 không hơn global nên P1 chưa chạy |
| RouterBench | Intake 649 file/467.023 metadata records; pilots MATH500, FinQA; headroom FinQA/MBPP | Proxy có pair signal đủ mạnh và có giá trị chọn model ở ít gold |
| HistRepEval/paper | Proposal, card nháp, báo cáo, code, provenance, error analyses | Benchmark release, external replication, confirmatory study, manuscript hoàn chỉnh có claim được hỗ trợ |

Không có cơ sở gán phần trăm hoàn thành chính xác cho dự án nghiên cứu này. Theo kế hoạch sáu tuần ban đầu, Week 3 thực nghiệm đã xong; các gate khoa học phương pháp, external confirmation và paper/release của Week 4–6 chưa hoàn tất. Hạn manuscript/release cũ **11/10/2026** đã qua, nhưng workspace không có bằng chứng một bản paper/release cuối đã đạt các gate đó.

## 2. Những quyết định dẫn tới hướng hiện tại

| Thời điểm | Kết quả dẫn tới quyết định | Quyết định còn hiệu lực |
|---|---|---|
| 31/08–đầu 09 | Proposal tách reliability feedback và relevance/transfer; ECRT biến hai thành phần thành reputation/influence | Đánh giá cả calibration và quyết định thực tế; không coi reputation score tự nó là đóng góp đủ |
| 28–29/09 | Các bảng cũ dùng correctness mô phỏng từ audit nhỏ, có nhầm cấu hình model | Loại các kết luận GO-B cũ khỏi bằng chứng khoa học; chạy lại output thật |
| 29/09 | ECRT−FixedBorrow ở related+25% noise chỉ +0,02 điểm %, CI95 [−0,04;+0,10] | Week 3 GO-C: thực thi xong, giả thuyết method superiority chưa được hỗ trợ |
| 29/09–01/10 | Thinking mạnh; pool/router/selector/audit vẫn không qua đối chứng phù hợp | Giữ fallback và gold-only controls; không mở sealed holdout để sửa method |
| 01–03/10 | Agent AppWorld mới yếu hoặc cùng thành công/thất bại trên cùng task | Dừng xây pool từ các cặp đó; không suy ra DART thắng từ partial checks |
| 04/10 | Archive có complementarity nhưng DARTContrast 63,90/168, thấp hơn Uniform 69,70 và PairedGlobal 71,95 ở 10% gold | Điều tra feedback, estimator, candidate bank, cách dùng nhãn |
| 05/10 | Continuous scores, C/S reuse, neural, factor/history, paired audit, SH đều đã kiểm tra | Giữ ứng viên paired CFJudgeFactor như development candidate; cần dữ liệu mới |
| 06/10 | MATH500 có pair signal nhưng sample không còn headroom; FinQA/MBPP có headroom | Chuyển kiểm tra proxy sang FinQA; không mở rộng MATH500 chỉ vì Brier tốt |
| 06–07/10 | Judge FinQA và consensus đều fail expansion gate | Dừng hai proxy v1; thử verifier độc lập theo protocol mới |
| 07–08/10 | Strategy và handbook tổng hợp các thất bại, giới hạn và thiếu hụt | Một bài về decision value; method chỉ claim khi qua confirmation, nếu không phát triển measurement có replication |

## 3. Kết quả cốt lõi và nguyên nhân stuck

**ECRT thường đổi xác suất mà không đổi thứ hạng/hành động.** Mã áp dụng cùng phép hiệu chuẩn lên feedback nhị phân. Khi history count và transfer weight như nhau, phép biến đổi cùng chiều giữ thứ hạng agent: trong 129 ô same/related ở noise25%, ECRT và FixedBorrow có cùng ranking 129/129. Với judge thật, đáp án cuối chỉ khác 37 hoặc 41 trên cùng 2.416 test IDs ở hai fold. Vì thế Brier tốt hơn không tự tạo gain accuracy. Transfer taxonomy còn thô, pool không cho nhiều specialist được xác nhận, và targeted poisoning không được kênh calibration gộp bảo vệ đầy đủ.

**Thinking cải thiện solver nhưng chưa cứu được cơ chế lựa chọn.** Trên 560 development IDs, thinking 372/560, direct 277/560; fallback Qwen14 trên 40 invalid đạt 388/560. Selector phải gọi thêm Qwen14 cho cả 560 câu để đạt 396/560, chỉ hơn fallback 8 câu thay vì gate 12. Router gọi Qwen14 172 lần vẫn chỉ 388/560. Đây là vấn đề gain/cost, không phải thiếu output để chờ chạy.

**AppWorld cần phân biệt hai nguồn dữ liệu.** Pilot agent mới v8: Coder và Qwen32 đều 3/6, không có rescue riêng; v9 GLM 0/6; v10 official simplified ReAct/AppWorld0.2 đạt 1/6, dưới gate2/6. Ngược lại, DART archive dùng 14 agent lịch sử trên AppWorld0.1.0, best fixed82/168 và oracle134/168. Archive có bổ trợ nhưng chưa học được quyết định tốt ổn định. Hai nguồn và các version không được gộp như cùng protocol.

**DART có tiến bộ development nhưng chưa thắng đầy đủ controls.** Ở 10% gold, paired CFJudgeFactor74,15/168 so PairedGlobal71,95: +1,31 điểm %, CI[+0,03;+2,59]. So Uniform69,70: +2,65 điểm %, CI[−0,60;+5,86]; so PairedSH71,90: +1,34 điểm %, CI[−0,86;+3,42]. Gate vẫn fail. Neural P0 Selected=Global82/168, nên P1 không chạy. Những cơ chế đã kiểm tra gồm proxy binary/continuous, HT/normalization, candidate restriction, paid-label reuse, structure/text/semantic learning và paired/adaptive acquisition. Không có bằng chứng chỉ cần tăng mạng hoặc GPU sẽ giải được nút thắt.

**MATH500 không còn headroom trong đúng sample đã thử.** Judge pilot48×6 có pair variance ratio0,69467, qua gate tín hiệu. Nhưng RawJudge0-gold, best fixed và oracle cùng46/48; ứng viên10%gold44,30/48. Đây là một sample không cho accuracy gain vượt baseline đó, không phải chứng minh mọi MATH500 pool đều không có headroom.

**FinQA có headroom nhưng các proxy hiện tại không phân biệt model đủ tốt.** Trên200 câu×20model, best fixed74%, oracle88,5%; MBPP78% và94,5%. Tuy nhiên:

| Proxy FinQA | Brier cross-fit / gold-only | Pair residual variance ratio, CI95 | Kết luận |
|---|---|---|---|
| Judge48×20 | 0,208561 /0,237974 | 1,045407 [1,019379;1,073530] | Dự báo pooled tốt hơn nhưng làm tăng nhiễu contrast khoảng4,54%; FAIL |
| Consensus48×20 khác | 0,204689 /0,219816 | 0,923388 [0,848729;1,000613] | Giảm khoảng7,66%, chưa đạt10% và CIupper<1; FAIL |

Judge có thông tin về độ khó chung nhưng within-question correlation chỉ khoảng0,043. Consensus có tín hiệu hơn trong phép đo riêng của nó, nhưng nhóm đồng thuận cao vẫn có22cell sai trên hai câu. Hai pilot dùng hai tập câu khác nhau: không trừ hai ratio thành hiệu ứng paired. Đổi parser hoặc bỏ MiMo hậu kiểm cũng không giải thích hết thất bại.

**Nút thắt xuyên suốt:** thông tin giúp dự báo đúng/sai nói chung chưa chắc giúp so sánh A với B trên cùng nhiệm vụ; lợi ích dự báo chưa chuyển thành lợi ích quyết định dưới ngân sách và chi phí thực. Dữ liệu development đã xem nhiều lần cũng không thể trở thành confirmation chỉ bằng thêm folds/seeds/bootstrap.

## 4. Hướng đã chốt gần nhất và phần chưa thực hiện

Bài toán ưu tiên là **chọn một model mặc định từ lịch sử để dùng cho workload tương lai**. Router theo prompt là study khác, chỉ mở khi có tín hiệu prompt-only; không dùng output của20model trên câu test rồi tính cost như một solver.

Ứng viên kế tiếp là **paired, incumbent-preserving audit**: giữ model hiện tại; đề cử ít challenger; audit hai model trên cùng task; giữ random coverage; hiệu chỉnh proxy bằng gold với sampling probabilities phù hợp; chỉ switch khi gain sau cost/harm có bằng chứng đủ mạnh. Đây là đề xuất chưa triển khai/kiểm chứng, khác các replay paired history đã hoàn tất.

Thứ tự tiếp theo theo strategy07/10:

1. Chốt provenance, quyền sử dụng/phát hành, duplicate groups, split hashes, budget và cost ledger.
2. Viết protocol FinQA verifier độc lập trên development mới: một lần/câu, chỉ thấy prompt, không thấy candidate/modelID/gold; khóa model/digest, reasoning, parsing, abstention, cost và STOP gate.
3. Chỉ scale nếu proxy cải thiện pair signal đủ mạnh và đáng chi phí. Nếu fail, giữ gold-only track.
4. Implement ứng viên audit cùng full controls; tách nomination/calibration khỏi certification hoặc dùng sequential inference phù hợp. Chọn tối đa một finalist trên development.
5. Freeze rồi xác nhận một lần trên FinQA+MBPP hoặc nguồn độc lập đã chốt; so cả gold-only và proxy-aware controls ở cùng tổng cost.
6. Hoàn thiện HistRepEval release/card và external rerun. Nếu method fail, measurement paper vẫn cần finding lặp lại rộng, không chỉ gom failure cases.

Ngưỡng gain≥3điểm% ở10%gold trong strategy là **đề xuất phải power-check và khóa**, chưa là gate confirmatory đã đăng ký. Chưa thấy protocol/run mới cho verifier FinQA độc lập hoặc implementation ứng viên incumbent audit trong workspace.

Theo erratum07/10, ngoài200development có **929 FinQA** và **766 MBPP unique eligible**; số938/770 cũ gồm duplicate đã loại. Chúng chưa phải final split được chứng nhận. Quota FinQA100pilot/100method-dev/khoảng700final và MBPP80/80/khoảng600 là gợi ý trước grouping/license review. MMLU sealed420 vẫn được tài liệu ghi là chưa dùng cho method outcome mới; lượt review này không mở tập đó hoặc AppWorld challenge.

## 5. Kiểm chứng mới thực hiện trong lượt rà soát

- Tính lại headroom từ40 score checkpoints của đúng200development questions/dataset: khớp cloud; MBPP0,78/0,945, FinQA0,74/0,885.
- Kiểm960case FinQA judge bằng checksum/ledger, prompt hash, index, run identity và response probability; tính lại Brier, pair ratio, bootstrap và gate: khớp cloud/public.
- Kiểm960cell consensus, checksum các artifact, rule exact agreement, missing mask và gold-blind proxy flag; tính lại Brier, pair ratio, bootstrap và gate: khớp cloud/public trong tolerance1e−10.
- Kiểm trạng thái local10run chính: hoàn tất hoặc dừng vì scientific gate; không coi receipt/deployed app là bằng chứng job đang chạy.
- Đọc/parse23JSON tổng hợp gốc. Lượt này không gọi solver/judge, không mở outcome chưa xem, không thay protocol/kết quả cũ và không chạy lại toàn bộ test suite. Các con số tests trong tài liệu cũ là kết quả lịch sử của thời điểm đó.

Chi tiết máy đọc: [project_status_verification_2026-10-18.json](project_status_verification_2026-10-18.json).

## 6. Nguồn ưu tiên khi tiếp tục

- [Strategy07/10](repguard_a_conference_strategy_2026-10-07.md): hướng hiện tại và evidence gates.
- [Handbook08/10](../book/repguard_research_handbook_2026-10-08.tex): diễn giải lý thuyết, mã và toàn bộ tiến trình; đây là sổ tay, không phải manuscript xác nhận method.
- [DART research progress05/10](dart_research_progress_2026-10-05.md): ứng viên tốt nhất và controls đã chạy.
- [Root causes05/10](dart_root_causes_and_next_steps_2026-10-05.md): phân biệt cơ chế đã can thiệp với giả thuyết.
- [FinQA judge interpretation](routerbench_finqa_feedback_v1_interpretation_2026-10-06.md) và [consensus interpretation](routerbench_finqa_consensus_v1_interpretation_2026-10-06.md): kết quả âm mới nhất.
- [Count erratum07/10](routerbench_headroom_count_erratum_2026-10-07.md): mẫu số dùng cho study mới.

README đã cập nhật nhiều kết quả đến06–07/10; `research_ops/research_log.md`, `paper_claims.md`, `open_questions.md` và registry còn chủ yếu ghi giai đoạn09/2026. Không dùng trạng thái chờ/STOP vận hành cũ để ghi đè báo cáo hoàn tất mới hơn. `results/` bị Gitignore; `docs/book/` hiện chưa được Gittrack. Số liệu local và việc push code không đồng nghĩa đã có release artifact độc lập.
