# RepGuard — rà soát toàn bộ tiến trình và chiến lược khóa luận

Ngày 09/11/2026, giờ Việt Nam. Định vị nghiên cứu sau rà soát repo và nguồn học thuật đến ngày này.

**Kết luận:** nên tiếp tục dự án, nhưng chuyển mục tiêu từ “chứng minh ECRT là phương pháp tốt” sang **“chứng minh khi nào một nhóm agent kiểm chứng được đầu ra tốt hơn một agent mạnh có cùng tài nguyên, và xây một công cụ giải quyết đúng nhu cầu đó”**. Giữ RepGuard làm tên hệ thống; ECRT/DART là các phương án có thể bị loại bằng thực nghiệm.

**Hướng ưu tiên:** hệ đa tác tử rà soát **khẳng định và số liệu trong báo cáo tài chính/doanh nghiệp**, trả về chấp thuận, bác bỏ có bằng chứng, hoặc yêu cầu con người kiểm tra. Câu hỏi chính là giá trị của phân công kiểm chứng theo **bằng chứng đang có và hiệu quả reviewer trong lịch sử**, trước lỗi ngữ nghĩa và sai sót chung giữa agent.

**Tên khóa luận làm việc:** “Điều phối kiểm chứng trong hệ đa tác tử LLM dưới phản hồi chưa đầy đủ: ứng dụng rà soát khẳng định và số liệu doanh nghiệp”. Đây là cách mô tả phạm vi để thảo luận với GVHD, chưa là thay đổi tên chính thức.

Đây là đề xuất phạm vi mới dựa trên yêu cầu hiện tại: giữ multi-agent, scope mở, thời gian và ngân sách không là giới hạn cứng. Tài chính là vertical được đề xuất vì đã có prototype và lỗi thực tế trong dự án, **không phải ràng buộc từ người dùng**. Chưa thay tên đề tài được duyệt, chưa đăng ký một study xác nhận, chưa chạy thêm model.

## 1. Phạm vi review và độ chắc chắn

Đã đối chiếu proposal ban đầu, README, lịch sử Git, các tổng kết MMLU/ECRT, AppWorld/DART, RouterBench, ba research cycles, hồ sơ pilot, code ECRT/audit/decision-value và prototype, bộ tài liệu trình bày 27/10, các audit/summary liên quan. Đã kiểm kê lại các nhóm mã chính và tra cứu nguồn gốc của các công trình gần nhất. Đây là review nghiên cứu và các đường mã quan trọng; không phải kiểm toán từng dòng của toàn bộ repo hay tái chạy tất cả thí nghiệm.

Nguồn ưu tiên khi tài liệu mâu thuẫn: artifacts/summary và protocol đã khóa → audit đã lưu → báo cáo kết quả mới nhất → proposal/kế hoạch cũ. Không coi một việc ghi trong kế hoạch là việc đã làm.

- HEAD đọc được: `27b4bc7`, 27/10/2026. Commit triển khai nghiên cứu trước đó: `f3c7446`, 24/10.
- Kiểm kê hiện tại: `src/repguard` 41 Python files/8.280 dòng; `thesis_pilot` 42/3.739; `tests` 45/4.101; `docs/analysis` 128 Markdown files.
- Mốc kết quả suy luận nghiên cứu mới nhất xác định được: cycle 03 ngày 20/10. Hồ sơ 27/10 tái kiểm artifacts và tests, không phải một đợt model evaluation mới.
- Test suite gần nhất **được hồ sơ ghi nhận**: 308 passed/1 skipped ngày 27/10. Lượt 09/11 không chạy lại suite, không suy diễn đây là kết quả test mới.
- EvalPlus vẫn là source preparation: 32 task, **0 model calls, 0 program executions**, chưa có score trong hồ sơ được tìm thấy.
- Không mở nhãn confirmation mới; không truy vấn trạng thái cloud hiện tại; không thay frozen sources hoặc điểm cũ.

Chi tiết nguồn ngoài và giới hạn novelty nằm trong [Literature và research gap](LITERATURE_VA_RESEARCH_GAP.md). Các số liệu repo có nguồn nội bộ ở cuối tài liệu.

## 2. Từ đầu đến giờ đã làm được gì?

### 2.1. Ý tưởng xuất phát và hạ tầng

Proposal tách hai câu hỏi đúng về mặt bài toán: phản hồi lịch sử có đáng tin không, và lịch sử ấy có liên quan nhiệm vụ mới không? ECRT hiệu chỉnh feedback, gán trọng số transfer rồi cộng soft evidence vào reputation. HistRepEval là tên bộ giao thức đánh giá dự kiến.

Đã có harness nhiều provider, chia tập và manifests/hashes, cache và resume, tách gold khỏi đầu vào solver, ledger, baselines, audit sampling, replay, phân tích decision value và prototype gọi model thật. Đây là tài sản tái sử dụng lớn nhất. **Chưa có nghĩa** đã có benchmark công bố hoàn chỉnh, posterior uncertainty có guarantee, hay sản phẩm được người dùng thực tế kiểm chứng.

### 2.2. Các giai đoạn và kết luận còn đứng

| Giai đoạn | Bằng chứng quan trọng | Kết luận hợp lệ |
|---|---|---|
| Prototype/simulation ban đầu | Có kết quả mô phỏng và pilot nhỏ; sau đó phát hiện vấn đề cấu hình/model và cách suy correctness | Giữ làm lịch sử phát triển; không dùng các kết luận GO-B cũ làm bằng chứng thắng phương pháp |
| MMLU-Pro, real rerun | 18.064 đáp án thật: 4 model × (1.400 history + 700 dev + 2.416 test); đủ 14 môn | Có nền dữ liệu thật; nghiên cứu được feedback và transfer trong setup này |
| ECRT, lưới Q×T | So FixedBorrow ở ô chính: +0,02 điểm %, CI95 [−0,04; +0,10]; một số chế độ nhiễu mạnh có Brier tốt hơn | Calibration có thể cải thiện; superiority về quyết định chưa được hỗ trợ |
| Pool/expertise | Best single direct 47,76%; oracle cấp câu 68,34%; chỉ một specialist được xác nhận; subject router 47,19% | Có bổ trợ ở cấp câu, nhưng phân loại theo môn không khai thác được; không được nói MMLU đã hết headroom |
| Thinking/fallback/selector | Trên 560 dev: thinking 372; fallback invalid 388; selector 396 nhưng cần gọi thêm model cho mọi câu; router 388 với 172 extra calls thay vì 40 | Solver và fallback cải thiện; selector chưa đạt gain/cost gate |
| Stress tests reputation | Poisoning có chọn lọc làm ECRT cũ suy giảm; audited variant hồi phục một phần nhưng chưa thắng AuditOnly rõ ràng | Đã nhận diện vulnerability trong các can thiệp cụ thể; chưa chứng minh chống tấn công tổng quát |
| AppWorld agent mới | Nhiều pilot v1–v10; v8 hai policy cùng 3/6, không rescue riêng; v9 0/6; v10 1/6 | Năng lực scaffold/pool chưa đủ để nghiên cứu coordination; không gộp với archive khác version |
| DART/AppWorld archive | 14 agent × 168 task/56 generator; 2.352 real judgments; đã thử correction, paired audit, factor/history/neural/halving | Archive có headroom; chưa có phương pháp thắng đầy đủ controls trên xác nhận độc lập |
| DART candidate tốt nhất ở 10% gold | 74,15/168 so PairedGlobal 71,95; CI chênh với Uniform và PairedSH còn chứa 0 | Có development signal; chưa đủ chốt method superiority; nhiều lần xem cùng dữ liệu làm tăng nguy cơ chọn nhầm finalist |
| LLMRouterBench intake | 649 file, 467.023 metadata records; MATH500/FinQA/MBPP follow-ups | Tái sử dụng archive được cho development; không tự thành benchmark mới |
| MATH500 pilot | Pair residual ratio 0,69467; nhưng RawJudge, best fixed và oracle đều 46/48 | Proxy có signal nhưng sample này không còn accuracy gain trên baseline đó |
| Headroom archive | MBPP 78,0% best fixed → 94,5% oracle; FinQA 74,0% → 88,5%, mỗi bộ 200 câu | Bổ trợ có tồn tại trong archive; không đồng nghĩa một router triển khai được sẽ khai thác nó |
| FinQA judge/consensus | Judge ratio 1,0454; consensus 0,9234 trên một pool khác; cả hai fail gate | Pooled prediction tốt hơn chưa đủ giúp so agent trên cùng câu; hai pool khác nhau không tạo phép so paired |
| FinQA live pilot 18/10 | 200 responses/100 report; screen 20 câu: RepGuard 1/20, bằng AlwaysB nhưng nhiều calls hơn | Đã có hệ chạy thật; chưa có lợi ích research/product; precision trên một câu được duyệt không đủ ý nghĩa |
| Cycle 01 | 160 responses; bốn nhánh repair cùng 6/24; PoT 14 strict, 16/17 theo hai readout hậu kiểm; local history 17/24, compute proxy +13,6% | Baseline/interface là nút thắt lớn; không có reputation win |
| Cycle 02 | 136 responses; direct/self1/self2 17/24; compose 16/24; backbone 8B/14B cùng 11/16 với mask giống nhau | Composition không tạo rescue trong bank đó; model khác tên không đảm bảo lỗi khác nhau |
| Cycle 03 TAT-QA TRAIN | 264 responses/24 contexts; scoped oracle 16 < Plain 19; cross-family union 20 = best fixed 20 | Bank hiện tại không cho selection gain; ngừng fit learner trên bank này |
| Hậu kiểm cycle 03 | Count contract, metadata parser và receiver giải thích một số chênh lệch; còn 4 semantic flags, 0 human adjudications | Sửa compiler/readout là software gain; không được quy thành reputation gain hay tự kết luận gold sai |
| Hồ sơ 27/10 | Review/literature/slide, audit lại cycle 03 và scorer; ghi 308 pass/1 skip | Tăng chất lượng bằng chứng và trình bày; không phải thêm independent research result |

Không cộng các response, replay configurations, seeds, model-task cells và unique tasks thành một “cỡ mẫu” duy nhất. Riêng ba cycles có 560 responses, không phải 560 nhiệm vụ độc lập.

### 2.3. Sản phẩm hiện tại thực chất ở mức nào?

`thesis_pilot/web_demo.py` và live CLI đã gọi model thật, cho xem bằng chứng, chương trình tính, traces, tokens và chế độ so sánh. Có guard về nguồn/đơn vị và các nhánh typed tools. Đây là **research prototype chạy được**.

Chưa thấy bằng chứng về người dùng mục tiêu đã dùng thường xuyên, workflow được xác nhận, giảm thời gian kiểm tra, tỷ lệ lỗi chấp thuận trên dữ liệu mới, hay vận hành sản phẩm rộng. Demo trên report đã dùng trong pilot là integration demo. Không nên giới thiệu nó như một trợ lý tài chính đã đáng tin hoặc có tiết kiệm chi phí được xác nhận.

## 3. Vì sao dự án mất định hướng?

### 3.1. Một hệ thống đang chứa nhiều bài toán khác nhau

Repo đã lần lượt nghiên cứu weighted voting, chọn default model, prompt routing, cascade sau khi thấy output, audit labels, agent repair và numerical QA. Chúng có quyền quan sát và chi phí khác nhau. Một ý tưởng có vẻ hợp lý ở bài này không tự giải bài kia.

Ví dụ, chọn sau khi đã xem hai output cần tính hai solver calls; không thể mô tả kết quả ấy như pre-call routing. Một phương pháp chọn default model từ history cũng không tự là cơ chế hợp tác nhiều agent trong một nhiệm vụ thực.

### 3.2. Đã đầu tư vào estimator trước khi xác nhận giá trị hành động

Chuỗi cần thỏa là: có hành động khác thực sự sửa được lỗi → biết phân biệt khi nào dùng → quyết định có lợi sau harm và cost → lặp lại trên dữ liệu mới. Nhiều nhánh bị dừng ở một trong hai điều kiện đầu, nhưng tiếp tục sinh thêm proposal/variant.

Trong ECRT hiện tại, nếu mọi agent dùng cùng calibration nhị phân, prior và tổng trọng số bằng nhau, posterior mean có dạng:

`mu_i = [alpha0 + p_minus W + (p_plus − p_minus) S_i] / [alpha0 + beta0 + W]`.

Với `p_plus > p_minus`, đây là hàm tăng của weighted positive count `S_i`: thay calibration có thể giữ nguyên ranking. Đây là giải thích đại số cho một cơ chế trong code, **không phải định lý mới về mọi reputation system**. Nó không bao trùm khác biệt evidence mass, mọi lower-bound score, hay mọi aggregator. Sửa uncertainty quantile không tự tạo ra thông tin chọn agent còn thiếu.

### 3.3. Các kết quả âm đang bị gộp thành một nguyên nhân quá mạnh

Có ít nhất năm nút thắt khác nhau: taxonomy thô; feedback không có pair signal; pool/repair bank không bổ trợ; interface làm yếu solver; và lựa chọn policy từ ít labels với nhiều candidates. Không thể suy từ các thí nghiệm này rằng “chắc chắn chỉ do tín hiệu, thuật toán không có vấn đề”. Những can thiệp đã chạy loại được **một số** lời giải thích, chưa nhận diện đầy đủ nguyên nhân của mọi thất bại.

Tương tự, 68,34% oracle trên MMLU cho thấy vẫn có question-level headroom; chỉ subject-level headroom nhỏ. Kết quả 20/24 union=best fixed áp dụng cho đúng bank TAT-QA đã sinh, không phải toàn bộ tài chính hoặc multi-agent.

### 3.4. “Có research gap” đang bị lẫn với “ghép được nhiều module”

Reputation theo skill, hiện tại+lịch sử, proxy+gold audit, cost-aware verification, memory theo lỗi, counterfactual utility và giảm lỗi nguồn chung đều có prior work rất gần. Một công thức đặt tên mới hoặc chuyển benchmark không đủ tạo gap.

Sau khi người dùng cho phép mở scope, không còn lý do khoa học phải giữ ECRT/DART là đóng góp chính. Giữ **vấn đề và hạ tầng**, cho phép bỏ cơ chế không tạo lợi ích.

## 4. Literature mới thay đổi quyết định như thế nào?

Bản [đối chiếu chi tiết](LITERATURE_VA_RESEARCH_GAP.md) phân biệt bài đã công bố với preprint, nguồn abstract với các phần full text đã kiểm tra. Một số mốc quan trọng:

- **ASB, 05/10/2026:** đã nghiên cứu mua primary outcome sau khi thấy surrogate, kết hợp decision relevance và residual uncertainty. Vì vậy “audit theo regret sau weak feedback” không đủ mới. [The Surrogate Is Not the Reward](https://arxiv.org/abs/2610.06610).
- **Portfolio vigilance, 26/09/2026:** đã nghiên cứu khi nào history được phép dùng trong chứng nhận khi evaluator thay đổi. Không nhận “không tin mù lịch sử cũ” làm novelty. [When Can Old Evaluations Certify a New Model?](https://arxiv.org/abs/2609.32267).
- **BMA-GAI, 28/09/2026:** đã phân bổ budget giữa candidates và thuộc tính kiểm chứng. Một controller “chọn verifier tiếp theo” cần so gần hơn uniform. [Budgeted Multi-Attribute Verification](https://arxiv.org/abs/2609.34322).
- **Epistemic Sybil và CAMA:** tracking nguồn, lỗi tương quan và truy hồi thêm bằng chứng độc lập đều đã có. Không gọi “nhiều agent không bằng nhiều bằng chứng” là khám phá mới. [Epistemic Sybil Resistance](https://arxiv.org/abs/2609.01873), [CAMA](https://arxiv.org/abs/2608.19701).
- **VP-CONTROL:** đã tách model diversity khỏi source diversity; kết quả transfer sang FinQA trong cấu hình thử không tái lập source effect. Đây là một động lực **kiểm tra điều kiện chuyển sang lỗi tài chính thật**, không phải lý do tuyên bố ta phát minh evidence diversity. [Engineering Reliable Commit Gates](https://arxiv.org/abs/2609.10969).
- **Trust–Agreement Gap, 22/10/2026:** trust estimates tốt chưa chắc làm negotiation tốt hơn. Hiện tượng calibration/identification–outcome disconnect không còn là claim độc quyền của RepGuard. [Knowing Whom to Trust is not Enough](https://arxiv.org/abs/2610.31971).
- **Relevant Is Not Enough, 28/10/2026:** evidence liên quan chưa chắc đủ để kết luận; cải thiện lựa chọn evidence chưa chắc chuyển thành verdict tốt hơn. Điều này khiến việc chấm đúng metric/kỳ/phạm vi rất cần thiết. [Nguồn FinNLP](https://aclanthology.org/2026.finnlp-1.32/).
- **Verified but Vacuous, 03/11/2026:** tách verifier chấp nhận, ràng buộc specification và độ đúng của specification. Không dùng executable/pass làm đồng nghĩa với semantic correctness. [Nguồn preprint](https://arxiv.org/abs/2611.05590).

Tài chính cũng đã có MoCA-Agent và CLAIR-Fin. **Chỉ làm một team extractor–calculator–critic không đủ novelty.** Nếu theo vertical này, cần so trực tiếp cơ chế gần nhất trong cùng setting, không chỉ so chatbot yếu. [MoCA-Agent](https://arxiv.org/abs/2606.11537), [CLAIR-Fin](https://arxiv.org/abs/2608.13706).

## 5. Hướng khóa luận nên chọn

### 5.1. Một vấn đề chính, một người dùng chính

**Người dùng mục tiêu:** người lập/kiểm tra báo cáo phân tích có khẳng định số liệu dựa trên tài liệu doanh nghiệp. Nhu cầu giả định: giảm thời gian lần lại nguồn, phát hiện nhầm metric/kỳ/đơn vị và hạn chế kết luận sai được coi là đã kiểm. Cần phỏng vấn/quan sát để xác nhận; repo chưa chứng minh product demand.

**Đầu vào:** tập tài liệu nguồn đã xác định phiên bản và một bản nháp/nhóm khẳng định cần rà soát.

**Đầu ra mỗi claim:** Supported / Refuted / Insufficient evidence; trích dẫn tới nguồn, metric/kỳ/phạm vi, phép tính có thể chạy lại, những gì đã kiểm và chưa kiểm; tùy chọn chuyển người xử lý. Insufficient không đồng nghĩa với claim sai.

**Phạm vi đúng của kết luận:** nhất quán với nguồn và định nghĩa đã khai báo. Không coi việc khớp báo cáo của một doanh nghiệp là chứng minh doanh nghiệp nói đúng về thế giới hay báo cáo không có gian lận.

Ví dụ minh họa, không phải kết quả nghiên cứu: bản nháp lấy doanh thu đúng nhưng so FY2024 với quý 4/2023; calculator xác nhận phép chia, ba reviewer dùng cùng đoạn trích cùng đồng ý. Hệ thống cần phát hiện thiếu căn cứ so sánh kỳ, thay vì tăng confidence theo số phiếu.

### 5.2. Vì sao hướng này hợp hơn tiếp tục MCQ hoặc coding audit làm sản phẩm chính?

| Hướng | Quyết định đề xuất | Lý do |
|---|---|---|
| Tune ECRT/MMLU, thêm model và noise | Dừng làm trục chính | Chưa có method gain; nhiều kết quả đã xem; bài toán sản phẩm không rõ |
| DART/active audit tổng quát | Giữ làm baseline/tài sản | Prior rất sát; không nên tiếp tục một chuỗi variant trên archive cũ |
| EvalPlus basic/extended | Lab phụ có giới hạn | Hữu ích để nghiên cứu partial verification; nếu full tests có sẵn và rẻ thì phải chạy full, không tạo scarcity giả |
| Kiểm chứng claim/số liệu bằng team agent | **Ưu tiên cho khóa luận tiếp nối** | Tận dụng lỗi thật và prototype; có workflow và nhãn ngữ nghĩa có thể audit; xác định được tác hại và thời gian kiểm tra |
| MAS tổng quát làm mọi tác vụ | Ngoài scope lõi | Khó khóa một giả thuyết và xác nhận; độ rộng hệ thống không tự tạo đóng góp khoa học |

Ngân sách lớn nên mua **annotations đủ chuyên môn, nguồn mới, baseline mạnh và replication**, không chỉ thêm GPU hoặc số agent.

### 5.3. Research gap phát biểu cẩn thận

**Khoảng trống thực nghiệm ưu tiên:** thiếu bằng chứng đủ trực tiếp cho việc **lịch sử hữu ích của từng reviewer, trong điều kiện bằng chứng cụ thể, có cải thiện quyết định kiểm chứng của team trên lỗi tự nhiên hay không**, sau khi giữ công bằng năng lực solver, evidence access, chi phí và mức tự động hóa. Tình huống trọng tâm là tool checks có vẻ thành công nhưng còn sai metric/kỳ/phạm vi hoặc các reviewer cùng sai theo một nguồn đầu vào.

Đây là **candidate empirical gap**, dựa trên đối chiếu các công trình đã đọc; không phải khẳng định “chưa ai từng nghiên cứu tổ hợp này”. Những thành phần của một lời giải đều đã có tiền lệ. Muốn nhận đóng góp phương pháp riêng, phải xác định chính xác cơ chế mới và thắng comparator cùng thông tin.

Lý do đáng giải quyết không nằm ở việc công thức reputation mới: sản phẩm phải biết khi nào thêm reviewer giúp, khi nào cần một đường lấy/kiểm bằng chứng khác, và khi nào nên chuyển người. Nếu kết quả chỉ là thêm vài lượt model làm tốt hơn thì đó là scaling; nếu cùng một agent đủ tools làm tương đương thì không có bằng chứng cần multi-agent cho workflow đó.

**Ba câu hỏi có thể bác bỏ:**

1. **RQ1 — giá trị phân công:** trên cùng claim và budget, reviewer có đường kiểm tra khác có giảm false approvals hơn self-review/resampling của agent mạnh không? Model diversity và evidence-access diversity đóng góp gì riêng?
2. **RQ2 — giá trị lịch sử:** thêm lịch sử hiệu quả reviewer theo trạng thái bằng chứng có cải thiện quyết định hơn current-evidence learner, global/skill reputation và controller thông thường cùng dữ liệu không?
3. **RQ3 — giá trị triển khai:** lợi ích còn trên công ty/report mới, ở cùng automated coverage, tổng chi phí và thời gian con người kiểm tra không?

**Không mặc định RQ2 phải PASS.** Nếu lịch sử không thêm ích, loại reputation khỏi runtime. Khóa luận có thể có đóng góp thực nghiệm và hệ thống vững mà không có một thuật toán reputation mới; nhưng để gọi là method paper phải có bằng chứng cao hơn.

## 6. Thiết kế nghiên cứu để thoát vòng lặp cũ

### 6.1. Cố định đối tượng kiểm chứng trước

Trong study đầu, **đóng băng claim/bản nháp và nguồn** trước khi so controller. Không cho method tự viết claim dễ hơn trong khi baseline phải duyệt claim khó. Chưa làm auto-repair nội dung ở primary study; tách verification khỏi việc thay đáp án để loại confound đã gặp ở cycles.

Team tối thiểu có các vai trò khác nhau về hành động: tìm và định vị bằng chứng; kiểm phép tính/unit bằng công cụ; kiểm semantic metric/kỳ/phạm vi bằng một đường kiểm tra riêng. Một controller quyết định giữ kết luận, gọi reviewer tiếp hoặc chuyển người. Vai trò và quyền xem dữ liệu phải khác thực chất; chỉ đổi system prompt thành “chuyên gia” không xác nhận specialization.

Giai đoạn kiểm độc lập ban đầu nên tránh cho reviewer thấy kết luận của nhau; sau đó mới có trao đổi nếu protocol cho phép. Đây là một design control phải kiểm bằng ablation, không tự gọi là phương pháp mới.

### 6.2. Dữ liệu: ba lớp, không mở ba dự án song song

1. **Dev/diagnostic cũ:** dùng toàn bộ kết quả cũ để thiết kế lỗi/interface và ước lượng công sức, không làm confirmation mới. Hoàn tất blind adjudication của các flags tài chính cũ để biết kiểm đúng đối tượng gì.
2. **External development:** thẩm định **FinED-Bench** cho error detection và một tập claim verification có nguồn, chẳng hạn **Relevant Is Not Enough**; dùng ARQA/FinMRAGBench nếu cần source-grounded numerical/multi-document cases. Chốt một bộ chính sau kiểm accessibility, labels và scope. Các bộ này đo những đối tượng khác nhau; không ghép score thẳng thành một bảng tổng. [FinED-Bench](https://aclanthology.org/2026.findings-acl.1481/), [evidence dataset](https://github.com/dweebee/dg-evidence-750), [ARQA](https://aclanthology.org/2026.eacl-industry.63/), [FinMRAGBench](https://aclanthology.org/2026.findings-acl.187/).
3. **Confirmation/workload mới:** lấy report/claim theo rule khóa trước, dùng bản nháp thật được phép sử dụng hoặc outputs model sinh từ yêu cầu khóa trước; giữ cả claim đúng, sai và thiếu bằng chứng. Không chỉ lấy failure cases. Hai annotators độc lập, chuyên gia adjudicate, lưu span/table-cell, công thức, unit, metric, kỳ và phạm vi. Chia theo company/report hoặc dependency groups trước outcomes; dành riêng pool final.

Natural errors là primary. Các phép đổi số/kỳ/unit nhân tạo chỉ là controlled diagnostic track, không trộn tỷ lệ lỗi nhân tạo vào tỷ lệ lỗi sản phẩm. “Có nguồn mới” hoặc “thêm tiếng Việt” không tự tạo novelty; nếu thêm Vietnamese pilot phải kiểm chuyên môn và tách khỏi claim khái quát đa ngôn ngữ.

### 6.3. Các đối chứng tối thiểu

| Control | Điều nó kiểm tra |
|---|---|
| Một agent mạnh + retrieval/calculator/checks | Baseline có đủ năng lực và công cụ |
| Cùng agent tự review/resample, ngang compute | Gain có chỉ đến từ gọi thêm lần? |
| Team cố định, cùng evidence bundle | Hiệu quả của nhiều agent nhưng chưa đa dạng đường chứng cứ |
| Team cố định, khác evidence-access path | Hiệu quả của thiết kế kiểm tra; không tự giả định độc lập thống kê |
| Controller dùng current evidence và checker state | Có cần lịch sử hay hiện trạng đã đủ? |
| Cùng learner, thêm global/conditional history | Lịch sử và cấu trúc transfer thêm gì? |
| Cùng learner, history bị shuffle đúng group | Có học liên hệ thật hay identity/data shortcut? |
| Adaptation gần nhất của CLAIR-Fin/MoCA/VP-CONTROL | Có vượt một hệ kiểm chứng phù hợp, thay vì baseline tự dựng yếu? |

Nếu claim liên quan memory ancestry, cần CAMA-inspired control; nếu claim chọn/skip verifier, cần xét LW2S/BMA-GAI; nếu claim mua gold chủ động, cần Ao/ASB và gold-only audit controls. **Chưa triển khai active gold acquisition trong study đầu.** Dùng historical audits ngẫu nhiên/phân tầng rõ để cô lập giá trị history; mở acquisition thành study riêng chỉ khi có lợi ích đã lặp lại.

Published system và adapted comparator phải ghi khác nhau. Nếu thay backbone/tools/data, không gọi đó là tái lập đúng toàn bộ paper. Khi baseline cần tuning, dành cùng cơ hội tuning trên development.

### 6.4. Candidate method nên bắt đầu đơn giản

So hai learners cùng features hiện tại, labels và budget: (a) predictor thông thường; (b) cùng predictor cộng cấu trúc partial pooling theo reviewer × loại lỗi × trạng thái kiểm chứng. Cho phép fallback sang fixed strong policy khi thiếu evidence. Khóa cả cost khi quyết định gọi reviewer tiếp.

Reputation ở đây phải diễn tả **lợi ích và tác hại có điều kiện của hành động kiểm**, không chỉ tỷ lệ reviewer nói đúng. Nhãn “checker không báo lỗi” và “đã có audit ngữ nghĩa” lưu tách nhau. Không cộng nhiều reports có cùng tổ tiên chứng cứ như các quan sát độc lập.

Đó là candidate implementation, **chưa là thuật toán mới**: action-value, partial pooling và selective prediction đều đã có. Phần cần chứng minh là cấu trúc cụ thể có ích trên sparse history và transfer đã định nghĩa. Nếu generic learner cùng input làm bằng hoặc tốt hơn, không nhận explicit reputation representation là contribution riêng.

### 6.5. Primary endpoint và thống kê

Primary đề xuất là **false-approval risk tại cùng automated coverage và cùng total budget**, trên report groups mới. Chốt coverage/budget dựa trên pilot và yêu cầu người dùng **trước final**. Báo toàn bộ risk–coverage–cost curves; không chỉ chọn một operating point đẹp sau khi xem final.

- `false-approval risk = số claim sai/không đủ chứng cứ nhưng được chấp thuận / tất cả claim được chấp thuận`.
- Báo thêm approval rate trên toàn claims sai/không đủ chứng cứ để tránh lẫn mẫu số; recall phát hiện lỗi, all-claim correctness, human-review load, rescue/harm và abstention.
- Tách cost thu history/annotation, cost online của mọi model/tool/retry và thời gian người dùng. Runtime proxy không phải hóa đơn; cache không xóa cost của việc tạo output.
- Unit inference là claim dependency group/report/company tùy split. Seeds, nhiều reviewer trên cùng claim và nhiều biến thể một report không là n độc lập.
- Power theo paired discordances và clustering. Ví dụ xấp xỉ độc lập: hiệu ứng 3 điểm %, 80% power, hai phía 5%, discordance 0,10–0,20 cần khoảng 870–1.740 cặp; clustering làm cần nhiều hơn. Đây là planning approximation, không phải cỡ mẫu final đã chốt.
- Zero errors không chứng minh an toàn: nếu thật sự có n approvals độc lập, cận trên một phía 95% bằng `1 − 0.05^(1/n)`. Muốn cận ≤2% với 0 lỗi cần 149 approvals độc lập; ≤1% cần 299. Claim từ cùng report có phụ thuộc nên không áp máy móc công thức iid.
- Risk calibration trên distribution hiện tại không tự có guarantee cho report hoặc checker bị shift; stress tests báo riêng. Confidence bound trong ECRT cũ không phải deployment certificate.

Thang practical effect được chọn cùng nhu cầu: ví dụ giảm đủ số false approvals để bù review time hoặc tăng coverage ở mức risk chấp nhận. Không định nghĩa “thắng” bằng một p-value nhỏ hoặc một ngưỡng vừa đủ khớp kết quả dev.

### 6.6. Các gate để không tiếp tục chạy vô định

Các ngưỡng dưới đây là **đề xuất đăng ký cho pilot**, chưa phải gate được thực thi; có thể chỉnh trước thu dữ liệu khi thẩm định nguồn và annotation.

| Gate | Bằng chứng cần có | Nếu không đạt |
|---|---|---|
| G0 — nhu cầu và oracle | 5–8 cuộc phỏng vấn/quan sát workflow; taxonomy lỗi và annotation rubric được người có chuyên môn dùng nhất quán; data/evaluator preflight | Sửa task/nhãn trước method; không dùng UI để bù bài toán chưa có người cần |
| G1 — có cơ hội sửa thực | Pilot khoảng 80–120 claims từ ≥20 report groups, có đủ false approvals tự nhiên và ≥20 discordances của các intervention để phân tích; baseline mạnh không bị format handicap | Nếu chỉ arithmetic/checks đã giải hết, thu hẹp sản phẩm về deterministic QA; không cố tạo agent yếu để có gain |
| G2 — đa tác tử thêm giá trị | Dev cho thấy team/đường kiểm khác có rescue–harm dương và có triển vọng thực dụng so self-review ở cùng cost/coverage | Nếu thêm evidence/tools là toàn bộ gain, cấp chúng cho single-agent và so lại; nếu vẫn hòa, không claim coordination benefit |
| G3 — lịch sử thêm giá trị | Group-held-out development và ablation cho thấy history structure tốt hơn current-state và same-information learner, không chỉ Brier | Loại reputation khỏi phương pháp chính; giữ kết quả âm và dùng controller đơn giản đã thắng |
| G4 — xác nhận | Finalist/baselines/scorer/splits/analysis được freeze; đánh giá một lần trên pool final có power hợp lý, kèm replication | Báo kết quả đúng phạm vi; không sửa method trên final rồi tiếp tục gọi nó untouched |

G1 là screening count cho khả năng nghiên cứu, không phải kiểm định superiority. Nếu borderline, chỉ mở rộng một lần theo rule đã khóa. Không dùng G3 để trì hoãn vô hạn: chọn tối đa một candidate chính và một comparator chính cho confirmation.

## 7. Sản phẩm đề xuất: một bàn làm việc rà soát claim

**Workflow:** nhập tài liệu và draft → hệ thống đánh dấu claim → review nguồn/phép tính/ngữ nghĩa → hiển thị kết luận và lý do → người dùng xem các điểm cần kiểm → export bản có bằng chứng và lịch sử thay đổi. Claim thiếu căn cứ vẫn giữ trạng thái chưa xác minh.

MVP cần: đối chiếu claim–nguồn; điều hướng đúng trang/ô bảng; công thức tính lại; queue các claim chưa đủ kiểm; so baseline/team trên cùng task; export evidence packet. Tái sử dụng ledger, source references, arithmetic executor, provider interface và live UI đã có. Tách mã study freeze khỏi serving code mới.

Không ưu tiên marketplace agent, nhiều biểu đồ quản trị, chat tổng quát, swarm tự chọn vô hạn hay auto-publish báo cáo. Tính thực tiễn phải xuất hiện ở thời gian kiểm tra và lỗi bị bỏ sót, không ở số màn hình.

Đánh giá sản phẩm nên so người dùng + single-agent đủ tools với người dùng + team policy, task order được cân bằng. Đo thời gian, lỗi cuối còn lại, số claim cần mở nguồn, số lần sửa verdict sai và mức hoàn thành; trust/satisfaction chỉ là phụ. Một pilot 8–12 người với task/report lặp cần mô hình thống kê theo cả người và task, không coi mọi click là mẫu độc lập. Chưa có study người dùng nào được thực hiện ở lượt này.

Kết quả sẽ trả lời câu hỏi “một model mạnh cũng làm được” bằng đối chứng cụ thể. Nếu model mạnh làm tốt ngang team, sản phẩm dùng model đó; nghiên cứu không được buộc hệ thống nhiều agent dù không có lợi ích.

## 8. Hai nhịp công việc: hồ sơ gần hạn và chiến dịch nghiên cứu

### 8.1. Trong 48 giờ làm việc đầu

Chốt với GVHD một trang gồm problem/user/RQs/controls/primary endpoint và cách xử lý nếu history không thêm ích. Mang theo bảng tiến độ ở mục 2, giới hạn và literature mới. Trình bày kết quả đã có là development results; không nói phương pháp mới đã thành công.

Gói gần hạn gồm status report có nguồn, 3–4 bảng chính, demo đang chạy thật trong phạm vi hẹp và kế hoạch thí nghiệm khóa rõ. Điều này độc lập với việc nghiên cứu tiếp cần bao lâu.

### 8.2. Kế hoạch 14 ngày đầu, 09–22/11/2026

Đây là lịch gợi ý, không phải lịch job tự chạy hoặc cam kết kết quả.

| Thời gian | Việc cụ thể | Deliverable |
|---|---|---|
| Ngày 1–2 | Chốt scientific contract; tiếp cận người dùng mục tiêu do nhóm thực hiện; đọc kỹ 5 comparator gần nhất | Một trang scope + bảng prior-work delta, không thêm acronym |
| Ngày 3–4 | Thẩm định FinED/evidence dataset và nguồn report; viết annotation rubric, group map và visibility table; semantic adjudication case cũ | Dataset card nháp, split manifest, scorer preflight, annotation disagreement log |
| Ngày 5–7 | Thu pilot cố định từ task rule; freeze claims/proposals; một strong single, self-review và team tối thiểu; giữ mọi failures | Raw traces, ledger, source/evidence references, real cost và kết quả G1 |
| Ngày 8–10 | Can thiệp có kiểm soát model/evidence access, giữ quyền tools và budget; kiểm độ đúng verdict bằng human audit | Paired rescue/harm, false approvals, phân loại lỗi và G2 |
| Ngày 11–12 | Nếu G2 đạt: thử learner đơn giản và history ablations cùng labels/features; chưa làm active acquisition | Bảng same-information controls và G3 sơ bộ |
| Ngày 13–14 | Review GO/STOP; khóa primary outcome, sample/power plan, finalist shortlist và roadmap | Protocol version 1.0 + decision memo, bao gồm kết quả âm |

Nếu không có reviewer chuyên môn hoặc dataset/evaluator chưa đúng, dùng ngày 5–12 để hoàn tất chúng. Không để áp lực lịch tạo ra labels không đáng tin. Ngân sách model không giải quyết được một oracle ngữ nghĩa sai.

### 8.3. Chiến dịch nghiên cứu khoảng 12 tuần, điều chỉnh theo thực tế

| Chặng | Trọng tâm | Điều kiện hoàn tất |
|---|---|---|
| Tuần 1–2 | Nhu cầu, dữ liệu, capability và G1/G2 | Có task thật và lý do cần team, hoặc quyết định dừng rõ |
| Tuần 3–4 | Main study và same-information baselines | Chọn một finalist; xác định history có/không thêm ích |
| Tuần 5–6 | Thu annotations mới, power plan, freeze; preflight external corpus | Confirmation packet không lẫn dev |
| Tuần 7–8 | Xác nhận độc lập và robustness giới hạn | Main table/risk–coverage–cost, subgroup limits và negative results |
| Tuần 9–10 | MVP theo policy đã được hỗ trợ, người dùng thử có đối chứng | Time/error outcomes, không chỉ demo satisfaction |
| Tuần 11–12 | Replication bởi người khác, thesis/manuscript và release pack | Mỗi claim chính nối được tới data/code/table; một máy khác chạy lại được |

Nếu muốn mức đóng góp cao hơn, mở rộng **sau** core: một workflow doanh nghiệp thứ hai, thêm verifier/model shift hoặc huấn luyện policy mới. Không tăng đồng thời domain, modality, memory, security và RL trước khi có core result.

## 9. Tiêu chuẩn để khóa luận đủ mạnh và có impact

Một đóng góp hoàn chỉnh nên gồm ba phần gắn nhau:

1. **Tri thức:** một kết luận mới trong phạm vi cụ thể về khi nào reviewer/history có ích, không có ích hoặc gây hại, với cơ chế và đối chứng đủ phân biệt.
2. **Bằng chứng/phương pháp:** giao thức và dữ liệu có annotation/provenance tốt; một controller được đánh giá công bằng. Chỉ nhận method novelty khi phần mới được định nghĩa và có ablation hỗ trợ.
3. **Giá trị dùng được:** một workflow được người thực thử, đo lỗi và công sức; artifact có thể tái lập/phát triển tiếp.

Điểm mạnh trước hội đồng sẽ là: chọn đúng vấn đề, giải thích được vì sao cần MAS, không giấu các vòng fail, biết phân biệt syntax/semantic/evidence, có tập final độc lập, và demo đúng năng lực đã kiểm. Số dòng code, số agent hoặc lượng token đã chạy không thay các tiêu chí này. Không có căn cứ bảo đảm điểm số hay acceptance.

Nếu mọi multi-agent policy đều không thắng single-agent đủ tools, hai lựa chọn trung thực là: (a) một measurement/system thesis đủ rộng và được GVHD chấp nhận; hoặc (b) chọn task mới có lý do sau G0 và dùng dữ liệu mới. Không viết lại câu chuyện rằng một baseline thắng chính là phương pháp đề xuất.

## 10. Các việc cần dừng và các tài sản cần giữ

**Dừng ở vai trò hướng chính:** tune ECRT trên MMLU cũ; fit selector trên bank union=best fixed; mua thêm history cho pool không có useful action; gom mọi thứ thành một benchmark mới; coi UI là bằng chứng khoa học. Không đặt thêm tên phương pháp trước khi biết chính xác nó khác prior ở đâu.

**Giữ và chuẩn hóa:** raw ledgers/hashes, protocols, split discipline, decision-value/rescue–harm analyzers, paired controls, arithmetic execution, source traces, capability/fallback baselines, các failure cases và live UI. Hồ sơ cũ không bị thay thế bằng normalizer mới.

**Engineering debt trước release:** khóa môi trường phù hợp dependency constraints; xử lý portability; packaging các runner/pilot; kiểm rõ approximate uncertainty bound và configurable prior; thêm kiểm thử cần thiết cho đường serving mới; đồng bộ registry/claim tracker. Các lỗi này cần sửa có version, không dùng làm lý do phủ nhận mọi kết quả mặc định cũ.

## 11. Lưu ý nếu vẫn dùng EvalPlus làm lab phụ

`F = basic AND extended pass` làm `B=0 ⇒ F=0` đúng theo định nghĩa; `B=1` chưa xác nhận full pass. Gọi đúng đây là nhãn ngữ nghĩa chưa được quan sát đầy đủ/selected audit labels, không tự gán mô hình survival censoring.

Phân biệt `P(B=1 | F=0)` với **false-pass risk** `P(F=0 | B=1)`. Sau khi đã sinh/test nhiều candidates, state hợp lệ chứa vector các kết quả đã quan sát. Hai tỷ lệ marginal `P(F_A=1 | B_A=1)` và `P(F_B=1 | B_B=1)` không tự xác định agent tốt hơn trên giao `B_A=B_B=1`: có thể đang so hai tập task khác nhau. Cần paired/joint-survivor analysis, hoặc mô hình điều kiện hóa đúng thông tin có ở quyết định.

Nếu full tests của task hiện tại có sẵn và rẻ, **run-full-suite** là comparator bắt buộc và có thể là giải pháp sản phẩm đúng. Nếu hidden tests chỉ là evaluator, không cho policy dùng chúng. Giới hạn label revelation là thiết kế nghiên cứu thống kê, không tự là cost saving trong thực tế. Không chuyển claim từ lab code sang sản phẩm tài chính khi chưa external validation.

## 12. Nguồn nội bộ để kiểm tra nhanh

- [Proposal xuất phát](../../analysis/repguard_final_research_proposal.md).
- [Tổng kết real rerun 29/09](../../analysis/repguard_comprehensive_progress_report_2026-09-29.md).
- [Status review 18/10](../../analysis/project_status_review_2026-10-18.md) — đọc cùng cycles mới hơn trong ngày và 19–20/10.
- [DART root causes](../../analysis/dart_root_causes_and_next_steps_2026-10-05.md) và [strategy 07/10](../../analysis/repguard_a_conference_strategy_2026-10-07.md).
- [Cycle 01](../../analysis/repguard_research_cycle_01_2026-10-18.md), [cycle 02](../../analysis/repguard_research_cycle_02_2026-10-19.md), [cycle 03](../../analysis/repguard_research_cycle_03_2026-10-20.md).
- [Quyết định 20/10](../../analysis/repguard_research_decision_2026-10-20.md).
- [Literature/tiến độ 27/10](../2026-10-27/REPGUARD_LITERATURE_REVIEW_VA_BAO_CAO_TIEN_DO.md) và [verification đã lưu 27/10](../2026-10-27/verification_2026-10-27.json).
- [Evidence record của lượt review này](review_evidence.json).

Bản này là đề xuất định hướng có điều kiện theo bằng chứng, không thay đổi kết quả hay protocol của các thí nghiệm đã hoàn thành.
