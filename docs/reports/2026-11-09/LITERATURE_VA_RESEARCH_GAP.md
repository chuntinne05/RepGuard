# Literature và ranh giới research gap cho RepGuard

Rà soát ngày 09/11/2026, giờ Việt Nam. Đi cùng [review và chiến lược khóa luận](REVIEW_VA_CHIEN_LUOC_KHOA_LUAN.md).

## 1. Phạm vi và cách đọc

Tra cứu nguồn gốc trên arXiv, ACL Anthology, PMLR và repositories chính thức. Các nhóm truy vấn gồm: multi-agent reputation/conditional trust; proxy feedback/selective audits; decision-focused allocation; multi-agent evidence dependence; verification/repair; financial numerical reasoning/error detection/claim verification. Có tìm thêm các công trình tháng 10 và đầu tháng 11/2026, đồng thời mở nguồn trực tiếp để tránh dùng kết quả tìm kiếm của version cũ.

Độ sâu không giống nhau: với các công trình gần nhất đã đọc abstract và các phần setup/method/experiments/limitations liên quan; với một số benchmark lân cận mới kiểm abstract, metadata và nguồn phát hành. **Không phải systematic review vét cạn mọi publication**, không tái lập kết quả các tác giả và không suy “không tìm thấy” thành “chưa từng tồn tại”. Metadata hội nghị chỉ ghi khi có nguồn chính thức hoặc ghi rõ tác giả tự báo accepted.

Các số hiệu dưới đây là danh mục của lượt review này, không thay R01–R49 trong bộ tài liệu 27/10. Những bài chỉ xuất hiện trong tìm kiếm nhưng không dùng để lập luận không được đưa vào danh mục.

## 2. Nguồn sát nhất và hệ quả thiết kế

### 2.1. Reputation, collaboration và dependence

| ID | Nguồn/version đã kiểm | Điều đã có | Hệ quả cho RepGuard |
|---|---|---|---|
| L01 | [When Should Agent Trust Be Conditional?](https://arxiv.org/abs/2606.14200), v1 12/06/2026, preprint; đã kiểm observation model và mechanism | Reputation theo skill, evidence borrowing, regime có ích và laundering; outcome trong setup được environment verify | Không nhận conditioning/shrinkage/laundering là mới. Cần kiểm feedback chưa đầy đủ và final decision trong quyền quan sát thực |
| L02 | [MiniRep](https://arxiv.org/abs/2609.39297), v1 30/09/2026, preprint; đã kiểm cả learned feedback setup | Kết hợp history, current quality/risk và chống domination bởi responses tương tự; có learned semantic feedback | Không nói bài chỉ dùng gold sạch hoặc bỏ qua imperfect feedback; cần same-information aggregation control |
| L03 | [Towards a Science of Scaling Agent Systems](https://arxiv.org/abs/2512.08296), **v3 08/04/2026**, preprint; metadata/abstract version hiện tại | So kiến trúc với standardized tools/prompts/compute; hiệu quả tùy task và single-agent capability | Dùng version hiện tại, không chép số 180 configurations/R²=0,513 từ v1. Cần chứng minh task–architecture fit, không mặc định thêm agent sẽ tốt |
| L04 | [Epistemic Sybil Resistance](https://arxiv.org/abs/2609.01873), v1 01/09/2026, preprint; đã kiểm formulation và study | Phân biệt số reports với số evidence roots; report content không nhận diện đầy đủ ancestry; correlated extraction | Theo dõi nguồn là prior art. Provenance giúp phân tích dependence nhưng không tự chứng nhận sự thật hoặc độc lập thống kê |
| L05 | [Beyond Memory Majority / CAMA](https://arxiv.org/abs/2608.19701), v1 20/08/2026, preprint; đã kiểm methodology/experiment structure | Query-conditioned evidence grouping, ước lượng independent evidence, active recovery trong multi-agent memory | “Deduplicate evidence + tìm thêm nguồn” không đủ novelty; nếu dùng memory arbitration phải có comparator gần này |
| L06 | [Knowing Whom to Trust is not Enough](https://arxiv.org/abs/2610.31971), v1 **22/10/2026**, preprint; đã kiểm formulation/results structure | Trust–agreement gap trong repeated multi-party negotiation; trust phải ảnh hưởng quyết định phù hợp | Không nhận disconnect trust–outcome là phát hiện đầu tiên. Benchmark, causal mechanism và intervention phải khác rõ |

### 2.2. Feedback, audit, estimation và routing

| ID | Nguồn/version đã kiểm | Điều đã có | Hệ quả cho RepGuard |
|---|---|---|---|
| L07 | [Best Arm Identification with LLM Judges and Limited Human Audits](https://arxiv.org/html/2601.21471v1), v1 29/01/2026, preprint; đã kiểm setup/estimator/allocation | Biased proxy, selectively observed truth, propensity correction, anytime-valid sequences và audit allocation | Proxy+gold correction hoặc tập trung audit vào close arms không là ý tưởng mới |
| L08 | [PROBE: Best-Arm Identification with Generative Proxy](https://arxiv.org/abs/2607.06879), v1 08/07/2026, preprint; abstract/setup | Proxy–reward correlation và chứng nhận residual variance để best-arm identification | Không nhập guarantee vào binary/shared-task archive khi chưa kiểm assumptions; variance reduction không đồng nghĩa downstream selection gain |
| L09 | [Valid Best-Model Identification via Low-Rank Factorization](https://arxiv.org/abs/2605.10405), v1 11/05/2026, preprint; đã kiểm formulation/method outline | Low-rank predictions kết hợp doubly robust estimation, adaptive model selection và finite-population evaluation | Factor model và valid residual correction không mới; cần so controls cùng nhãn và acquisition cost |
| L10 | [Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html), **ICML 2024**; official proceedings/abstract | ML-assisted label acquisition đi cùng inference hợp lệ | Audit chủ động cần sampling design và inference tương ứng; uncertainty acquisition là comparator thực chất |
| L11 | [The Surrogate Is Not the Reward / ASB](https://arxiv.org/abs/2610.06610), v1 **05/10/2026**, preprint; đã kiểm formulation/acquisition roles | Chọn mua primary outcome sau surrogate; kết hợp decision relevance với residual uncertainty trong contextual bandit | Hướng “weak test rồi audit theo regret” của kế hoạch cũ có prior rất sát; không nên đổi tên để nhận mới |
| L12 | [When Can Old Evaluations Certify a New Model?](https://arxiv.org/abs/2609.32267), v1 26/09/2026, preprint; đã kiểm information models/limitations | Phân biệt history được tin trong validity với history chỉ làm advice; portfolio vigilance khi evaluator drift | Không claim label-free shift detection hay safety từ history chưa xác minh. Setup uniform audits của bài không tự áp cho adaptive collection |
| L13 | [CABS](https://arxiv.org/abs/2607.09015), **v2 13/10/2026**, preprint; đã kiểm model/algorithm/limitations structure | Contextual bandits với correlated arms và misspecified surrogate; coupled/decoupled estimators | Tách true reward/proxy và robustness trước proxy sai đã có. Phải khớp online-bandit với full-bank access assumptions |
| L14 | [SaveRouter](https://arxiv.org/abs/2609.37402), v1 29/09/2026, preprint; đã kiểm framework/cost sections | Sparse supervision acquisition và capability sharing, tính payback cả chi phí supervision | Không chỉ báo serving savings mà bỏ upfront collection; không nhận sparse feedback transfer nói chung là mới |
| L15 | [Causal LLM Routing](https://arxiv.org/abs/2505.16037), v2 03/12/2025, preprint; abstract/formulation | Regret minimization từ observational logs, thiếu counterfactual outcomes | Missing outcomes khác observed labels bị sai. Không đánh đồng hai vấn đề chỉ vì cùng có ít labels |
| L16 | [LLMRouterBench](https://aclanthology.org/2026.findings-acl.1881/), **Findings ACL 2026**; official abstract/metadata | Quy mô lớn và unified routing baselines; complementarity không đảm bảo router thắng baseline đơn giản | Dùng archive không tự là benchmark mới; cần một evaluation axis riêng và release/provenance rõ |
| L17 | [RouteGuard](https://arxiv.org/abs/2608.07583), v1 05/08/2026, preprint; abstract/formulation summary | Certification của routing gain, conditional regret và ảnh hưởng sampling/clustering | “Oracle complementarity chưa đủ” không mới; bootstrap task khác workload-cluster conclusions có thể khác |

### 2.3. Verification, recovery và code

| ID | Nguồn/version đã kiểm | Điều đã có | Hệ quả cho RepGuard |
|---|---|---|---|
| L18 | [Test-Time Scaling via Budgeted Multi-Attribute Verification](https://arxiv.org/abs/2609.34322), v1 28/09/2026, preprint; đã kiểm formulation/algorithm/assumption scope | Chọn candidate và verification attribute dưới global budget, certification theo assumptions của bài | Chỉ “chọn kiểm gì tiếp” không đủ mới. Không chuyển guarantee của stochastic attributes sang mọi semantic checker |
| L19 | [Engineering Reliable Commit Gates / VP-CONTROL](https://arxiv.org/abs/2609.10969), v1 10/09/2026, preprint; đã kiểm full-text design/results | Cost-aware verifier portfolios, model-vs-source diversity và giới hạn transfer, kể cả thử FinQA | Đây là comparator sát cho multi-agent verification. Cần kiểm ngoài controlled templates; không mặc định source effect sẽ lặp lại |
| L20 | [Verification Trap](https://arxiv.org/abs/2610.05170), v1 **04/10/2026**, preprint; đã kiểm mitigation/limitations | Generator và verifier cùng false premise; source-aware prior/robustness audit giúp chọn lại candidates | “Thêm tests vẫn có thể sai” và independent evidence mitigation đều có trước; cần same-budget, same-pool comparisons |
| L21 | [Learning What to Skip](https://arxiv.org/abs/2609.30734), v1 25/09/2026, preprint; abstract/method outline | Counterfactual skip interventions, conditional utility/safety models và held-out calibration | Nếu controller bỏ qua/gọi thêm reviewer, utility-from-history và safe skipping phải đối chiếu bài này |
| L22 | [Verified but Vacuous](https://arxiv.org/abs/2611.05590), v1 **03/11/2026**, preprint; abstract/metadata | Tách verifier acceptance, specification binding và semantic fidelity | Không gọi executable/accepted output là đúng ngữ nghĩa; đây là prior về validity boundary, không phải hiệu quả method của ta |
| L23 | [EvalPlus](https://arxiv.org/abs/2305.01210), v3 30/10/2023; **NeurIPS 2023**, [official repo](https://github.com/evalplus/evalplus) | Tests mở rộng phát hiện code sai và thay đổi model ranking | “Basic pass chưa đủ” không phải gap mới. Full-suite pass vẫn là benchmark-defined proxy |
| L24 | [LiveCodeBench](https://arxiv.org/abs/2403.07974), v2 06/06/2024; [official repo](https://github.com/LiveCodeBench/LiveCodeBench) | Temporal problem collection và nhiều code capabilities | Có thể chọn external code validation; phải kiểm release dates và model cutoff, không mặc định tên benchmark bảo đảm contamination-free cho mọi model mới |

### 2.4. Tài chính, semantic oracle và workload thực

| ID | Nguồn/version đã kiểm | Điều đã có | Hệ quả cho RepGuard |
|---|---|---|---|
| L25 | [MoCA-Agent](https://arxiv.org/abs/2606.11537), v2 17/06/2026, preprint; abstract/method overview | Typed financial claims, specialist agents, executable synthesis và repair | Phân công fact/formula/unit/sign hoặc dùng calculator không đủ novelty |
| L26 | [CLAIR-Fin](https://arxiv.org/abs/2608.13706), v3 07/09/2026; arXiv ghi accepted FinNLP 2026; đã kiểm framework/RQs | Claim ledger, claim-type authority, hand-off verification, adaptive adversarial review và abstention | Không nhận claim-level checking hoặc adaptive debate là mới; cần controller/label regime và matched-budget comparison cụ thể |
| L27 | [FinED-Bench](https://aclanthology.org/2026.findings-acl.1481/), **Findings ACL 2026**; đã kiểm PDF setup/data/error taxonomy | Error detection trong financial documents với nhiều mức reasoning | Đây là nguồn development đáng thẩm định; không tự nhận benchmark phát hiện lỗi tài chính đầu tiên; kiểm cả cách tạo lỗi và oracle |
| L28 | [FinMRAGBench](https://aclanthology.org/2026.findings-acl.187/), **Findings ACL 2026**; đã kiểm PDF task/data setup | Financial multi-page/multi-document retrieval và reasoning, có agent baseline | Bỏ oracle context là cải thiện độ thực tế, không là novelty tự thân. End-to-end retrieval phải có control riêng |
| L29 | [ARQA](https://aclanthology.org/2026.eacl-industry.63/), **EACL Industry 2026**; abstract/metadata | Grounded table–text QA, numerical recomputation và explanation/evidence alignment | Numeric answer + source evidence đã có benchmark. Cần xác định chênh task và nguồn nhóm công ty của mình |
| L30 | [Relevant Is Not Enough](https://aclanthology.org/2026.finnlp-1.32/), **FinNLP 28/10/2026**; đã kiểm PDF design và [data repo](https://github.com/dweebee/dg-evidence-750) | Expert-audited decision-grade evidence; relevance, sufficiency và downstream verification là ba tiêu chí khác | Không dùng retrieved/related passage làm verified support. Có thể tái dùng taxonomy như tiền lệ, không nhận sufficiency labels là mới |
| L31 | [Definitional or Computational?](https://aclanthology.org/2026.finnlp-1.1/), **FinNLP 2026**; abstract/metadata | XBRL-grounded oracle phân biệt khác định nghĩa với lỗi số học | Gold rubric phải khóa definition và xử lý nhiều convention hợp lệ; mismatch target chưa chứng minh model sai ngữ nghĩa |
| L32 | [When FEVER Meets Finance](https://aclanthology.org/2026.finnlp-1.42/), **FinNLP 2026**; abstract/metadata | Controlled number/negation/entity/evidence edits và transfer limits | Đổi một số để tạo lỗi đã là prior. Giữ natural errors riêng, đừng gọi synthetic corruption là prevalence thực |

## 3. Khoảng trống nào không còn đủ để làm luận điểm chính?

| Phát biểu hấp dẫn | Vì sao chưa đủ | Nguồn gần nhất |
|---|---|---|
| Uy tín theo skill thay global trust | Đã nghiên cứu cả điều kiện có ích và borrowing | L01 |
| Kết hợp history và bằng chứng hiện tại | Đã có learned feedback/current risk | L02 |
| Nhiều agent cùng sai theo cùng nguồn | Đã có lý thuyết và thực nghiệm có kiểm soát | L04, L05, L19, L20 |
| Dùng gold audit ít để sửa proxy | Đã có estimator, inference và adaptive allocation | L07–L13 |
| Audit nơi có thể đổi quyết định | ASB và BAI/audit đã trực tiếp xử lý dạng gần | L07, L11 |
| Chọn reviewer/test tiếp theo theo cost | Đã có verifier portfolio và multi-attribute verification | L18, L19 |
| Dùng history để học khi nên skip/repair | Có counterfactual conditional-utility work | L21 và các repair/credit sources trong review 27/10 |
| Chuyển sang financial claims với tool và citations | Đã có các hệ và benchmarks chuyên biệt | L25–L32 |
| Calibration/trust tốt nhưng outcome không tốt | Đã có nhiều biến thể của disconnect này | L06, L16, L17, L30 |

Những điều trên vẫn có thể là motivation hoặc baseline quan trọng. Chúng không đủ để chứng minh một phương pháp mới chỉ bằng đổi tên/ghép module.

## 4. Candidate gap nên kiểm, và cách bác bỏ nó

Đề xuất dùng **một workflow financial claim review** để kiểm câu hỏi còn có ích về thực tiễn: **phân công reviewer từ lịch sử hiệu quả có điều kiện theo trạng thái bằng chứng có giảm false approvals so controller cùng thông tin và cùng budget, trên lỗi tự nhiên và report mới không?**

Phần chưa được xác nhận cho dự án này là transfer của conditional reviewer utility vào **quyết định kiểm chứng sau partial checks**. Nó khác việc chỉ nhận biết ai giỏi nói chung; cũng khác một detector của claim hiện tại. Nhưng đây là cách đặt **empirical question**, chưa là bằng chứng một thuật toán giải nó sẽ mới.

| Prior gần | So sánh cần thực hiện | Điều khiến claim mới bị bác bỏ |
|---|---|---|
| CLAIR-Fin/MoCA | Cùng claim pool, nguồn, backbone tier và tổng compute; kiểm lợi ích allocation/history sau khi các baseline có đủ tools | Cả gain đến từ claim decomposition, calculator hoặc retrieval baseline bị yếu |
| VP-CONTROL | Tách model identity với đường truy cập/check evidence; nghiên cứu lỗi ngữ nghĩa tự nhiên và report-held-out | Chỉ tái tạo source-diversity effect trên synthetic templates với tên khác |
| CAMA/Epistemic Sybil | Nếu dùng ancestry/dependence, cấp provenance ngang quyền và so recovery/discounting rule phù hợp | Chỉ thêm source graph hoặc response deduplication đã biết |
| LW2S/BMA-GAI | Nếu chọn/gọi/skip reviewer, so allocation dựa trên cùng state/outcomes/cost | Generic conditional-utility controller giải tương đương |
| MiniRep/conditional trust | Giữ cùng labels, current evidence và access; ablate history structure/identity/transfer | Gain chỉ đến từ thêm features hoặc có thêm gold labels |
| Ao/ASB/CABS | Nếu mở adaptive audit/online update, dùng matched feedback và đúng acquisition timing | Lời giải chỉ là một adaptation không đổi giả định hay estimator đáng kể |

**Một contribution thesis có thể đứng:** empirical protocol mới có natural errors và semantic adjudication, kết quả phân biệt được lợi ích của team/kiểm chứng/history, và một hệ có hiệu quả người dùng được đo. Không cần nhận tất cả cấu phần là mới.

**Một contribution method cần thêm:** chỉ ra phần representation/estimator/decision rule mới so các hàng trên, lý do nó giải một cơ chế trước đó bỏ sót, và gain lặp lại sau same-information controls. Nếu không làm được, viết rõ là adaptation/system/measurement contribution; không tô thành thuật toán mới.

## 5. Những phân biệt kỹ thuật quyết định chất lượng review

1. **Independent agent ≠ independent evidence.** Hai model khác nhau đọc cùng đoạn trích sai có thể cùng sai; hai đường parse từ cùng filing cũng chưa là hai nguồn sự thật độc lập. Traces chỉ ghi ancestry quan sát được, không đo trực tiếp mutual information hay bảo đảm độc lập.
2. **Correct calculation ≠ correct financial claim.** Metric, kỳ, denominator, scope và scale đều thuộc oracle. Giữ official benchmark score riêng với adjudicated semantic score, không sửa labels theo output mình thích.
3. **Historical success ≠ marginal review utility.** Một reviewer chính xác có thể không thêm gì sau một checker khác; final verdict có thể xấu đi khi sửa claim đúng. Cần intervention và rescue/harm, không chỉ standalone accuracy.
4. **Missing/selected labels ≠ arbitrary judge noise.** Partial nested tests, selective audit và wrong judge labels có cơ chế khác nhau. Không dùng một correction formula cho tất cả mà bỏ assumptions.
5. **Confidence score ≠ certification.** Beta soft counts, normal-style bounds và bootstrap từ reused dev không tạo guarantee cho adaptive deployment hoặc distribution shift.
6. **Research budget ≠ product verification cost.** Nhiều tiền không tạo ra hidden truth ở serving; ngược lại, full tests đã có sẵn/rẻ thì không nên bỏ qua để làm audit method có vẻ cần thiết.

## 6. Thứ tự đọc để thực thi tiếp

Không cần đọc tuyến tính 32 bài trước khi làm pilot. Nhóm nên đọc sâu theo quyết định cần đưa ra:

1. **Chốt ứng dụng và nhãn:** L26, L27, L30, L31; lấy một mẫu nguồn thực và áp annotation rubric.
2. **Chứng minh vì sao cần team:** L03, L04, L19; thiết kế controls single-agent/team và evidence-access.
3. **Nếu giữ reputation:** L01, L02, L21; viết bảng thông tin từng learner được phép thấy.
4. **Nếu muốn thêm active audit:** L07, L11, L12, L18; trước hết xác nhận conditional history có ích với audit design đơn giản.

Mọi citation trong proposal mới nên đi kèm một quyết định thiết kế hoặc comparator cụ thể. Thêm một trang tên papers không thay việc xác định cái mình cần vượt.
