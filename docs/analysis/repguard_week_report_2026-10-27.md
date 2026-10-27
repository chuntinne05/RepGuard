# Báo cáo tuần — 27/10/2026

**Đề tài:** RepGuard — Evidence-Calibrated Reputation Transfer under Imperfect Feedback in Multi-Agent LLM Systems
**Sinh viên:** Lương Ngọc Trung · Trịnh Trần Trung Tín — **GVHD:** PGS.TS. Quân Thanh Thọ
**Repo:** commit `f3c7446` (24/10/2026)
**Tài liệu đối chiếu:** `RepGuard Week 1.pdf`, `DACN RepGuard Week 2.pdf`, `repguard_week3_real_report.md`, `repguard_research_cycle_01/02/03`, `repguard_research_decision_2026-10-20.md`, `thesis_pilot/`, git log.

> **Cách đọc báo cáo này:** tuần trước ta *chạy thực nghiệm 4 model thật → dựng lưới Q×T → rút ra insight*. Tuần này làm đúng như vậy nhưng ở **tầng hành động**: lấy insight cuối của tuần trước làm câu hỏi, chạy 3 vòng thực nghiệm thật, rút insight mới, và insight mới đó quyết định phép thử tuần sau. Mỗi mục đều ghi rõ **nối từ insight nào**.

---

## 0. Tóm tắt 30 giây

1. **Tuần trước kết thúc bằng 3 insight**: (i) pool 4 model chỉ có **1 specialist** được xác nhận; (ii) nhãn *môn học* quá thô để định tuyến, dù pool bổ trợ rất mạnh ở cấp câu hỏi (68,34%); (iii) **Q và T đổi calibration nhưng gần như không đổi quyết định** — ECRT chỉ +0,02 điểm % team accuracy so FixedBorrow.
2. **Câu hỏi tuần này** sinh trực tiếp từ (iii): *nếu đổi từ "chọn đáp án MCQ" sang "chọn hành động sửa lỗi", reputation có tạo được lợi ích quyết định không?* → chạy **3 vòng thực nghiệm thật, 560 lượt suy luận** (160 + 136 + 264).
3. **Kết quả:** cả 3 vòng **fail gate**, nhưng fail **có cấu trúc** — và cấu trúc đó giống hệt tuần trước: tín hiệu feedback quá thô/không phân biệt, không phải thuật toán reputation kém.
4. **Insight mới quan trọng nhất:** `pass` là **feedback bị censored**: biết `B=0 ⇒ F=0` nhưng `B=1 ⇏ F=1`. Đại lượng đúng là `P(F=1 | B=1, agent, task)`.
5. **Phép thử tuần sau** vì vậy không phải "thêm module cho ECRT" mà là **tạo một tín hiệu feedback có cấu trúc lồng nhau** (EvalPlus basic vs extended tests) để đo được đúng đại lượng trên — đã chuẩn bị xong, **0 model call**.

---

## 1. Mốc nối: tuần trước đã để lại gì

### 1.1 Thực nghiệm 4 model thật (Week 2) — nền của mọi kết luận sau
18.064/18.064 lượt trả lời thật (4 model × `[1.400 history, 700 dev, 2.416 test]`), 100% câu test, 14 môn, ledger SHA-256 `1c69cd9d…`, **0 missing / 0 duplicate / 0 invalid**.

| Model | Đúng/2.416 | Micro acc | Wilson 95% CI | TB 14 môn |
|---|---:|---:|---|---:|
| Qwen3 8B | 1.154 | **47,76%** | 45,78–49,76% | 49,19% |
| Gemma2 | 1.090 | 45,12% | 43,14–47,11% | 47,53% |
| Llama3 8B | 877 | 36,30% | 34,41–38,24% | 38,52% |
| Qwen3 0.6B | 568 | 23,51% | 21,86–25,24% | 23,90% |

### 1.2 Lưới Q×T: 182 cặp × 4 mức Q × 3 seed × 9 phương pháp = 19.656 hàng

| Điều kiện / phương pháp | Team acc | Brier | Unique-expert |
|---|---:|---:|---:|
| same + oracle: Uniform | 47,82% | 0,2500 | 9,45% |
| same + oracle: GlobalBeta / FixedBorrow | 49,64% | 0,2206 | 13,76% |
| same + oracle: ECRT | 49,60% | 0,2206 | 14,19% |
| related + 25% noise: SkillConditioned | 47,82% | 0,2500 | 9,45% |
| related + 25% noise: FixedBorrow | 49,28% | 0,2422 | 12,74% |
| related + 25% noise: **ECRT** | **49,29%** | 0,2510 | 12,74% |
| same + 50% noise: ECRT vs FixedBorrow | 47,83 vs 47,89 | 0,2304 vs 0,2495 | — |
| same + directional FP: ECRT vs FixedBorrow | 49,68 vs 49,69 | **0,2243** vs 0,2763 | — |

### 1.3 Bốn insight tuần trước (dùng làm input cho tuần này)

| # | Insight (có số) | Hàm ý |
|---|---|---|
| **I1** | Heterogeneity gate **chỉ 1 specialist** được xác nhận: Qwen3 8B–physics +13,39 điểm %, CI [+7,48; +19,29]; không có model thứ hai | Tiền đề "có chuyên gia để chọn" chưa đủ mạnh |
| **I2** | Routing theo môn từ history **47,19%** vs model đơn 47,76% → **−0,58 điểm**, CI [−1,90; +0,75]. Trần oracle theo môn chỉ 48,97% (**+1,21 điểm** so model đơn) | **Nhãn môn quá thô**; nhưng cấp câu hỏi rất giàu tín hiệu: có ít nhất 1 model đúng **68,34%**, và **22,72%** câu chỉ đúng đúng 1 model |
| **I3** | Q đổi calibration rõ (lật 50%: Brier **+0,0290**, team acc **−1,75 điểm**), T đổi calibration rõ (same vs related: Brier **0,0265**), nhưng **team accuracy gần như đứng yên** (same–related **−0,02 điểm**, CI [−0,38; +0,39]). ECRT vs FixedBorrow: **+0,02 điểm %**, CI [−0,04; +0,10]. ECRT **thắng Brier** dưới nhiễu mạnh (−0,0192 / −0,0520 / −0,0429) nhưng **không thắng đáp án cuối** | **Điểm gãy: score đổi, quyết định không đổi** |
| **I4** | Ở 129 ô same/related noise 25%, ECRT và FixedBorrow cho **cùng thứ hạng 129/129**; với judge thật, chỉ **37/41 trên 2.416 câu** có đáp án cuối khác nhau dù reputation đổi trung bình ~0,10 | Cần **đo độ nhạy quyết định** như một metric hạng nhất, không chỉ Brier |

→ **Quyết định Week 3 = GO-C** (29/09): hiện tượng calibration là thật, nhưng claim *method superiority* không đứng.

---

## 2. Tuần này: 3 câu hỏi nối tiếp trực tiếp từ I1–I4

| Câu hỏi tuần này | Nối từ | Vì sao phải hỏi |
|---|---|---|
| **Q1.** Nếu chuyển từ *chọn đáp án MCQ* sang *chọn hành động sửa lỗi* (repair), history có tạo được lợi ích quyết định không? | I3 + I4 | MCQ gần như bão hoà ở 4 model generalist; hành động sửa lỗi có nhiều bậc tự do hơn ⇒ nếu "score đổi mà quyết định không đổi" là do *thiếu bậc tự do*, thì ở đây phải thấy gain |
| **Q2.** Nếu pool không có specialist (I1), thì bổ trợ **theo câu hỏi** (I2) có khai thác được bằng composition/backbone diversity không? | I1 + I2 | I2 nói tín hiệu nằm ở cấp câu, không ở cấp môn ⇒ thử "ghép output" thay vì "chọn theo môn" |
| **Q3.** Nếu feedback không phải nhãn sạch mà là *tín hiệu kiểm tra được/không được*, thì đại lượng nào thực sự cần học? | I3 | I3 cho thấy Brier tốt không ⇒ quyết định tốt; cần biết **loại feedback nào** mới có độ nhạy quyết định |

**Nguyên tắc giữ nguyên từ tuần trước** (không đổi giữa chừng): preregister → thu response thật → audit hash/digest → analyze không inference → gate viết trước → **STOP nếu fail**, giữ cả kết quả âm.

---

## 3. Ba vòng thực nghiệm tuần này (18–20/10)

### 3.1 Vòng 1 — trả lời Q1: can thiệp sửa lỗi có headroom không? (18/10, 160 responses thật, 24 dev context)

| Nhánh can thiệp | Đúng/24 |
|---|---:|
| Initial (1 agent) | 6 |
| Self-review | 6 |
| Evidence-grounded | 6 |
| Plan-then-answer | 6 |
| **Oracle union 4 nhánh** | **6** |
| **Control: PoT (program-of-thought)** | **14** |

→ **Không có headroom**: 4 nhánh trùng nhau tuyệt đối, oracle cũng 6 ⇒ *không được* train selector trên bank này.
Control định dạng/readout (0 call mới): strict **14** → bỏ whitespace thừa **16** → sửa quy ước readout **17/24**. Local-history policy cũng **17/24** nhưng compute proxy **+13,6%** so PoT trực tiếp, 1 rescue / 1 harm.

> **Insight nối I3:** lần đầu tiên thấy *cùng một hiện tượng, nguyên nhân khác*: ở MMLU-Pro là "reputation đổi, quyết định không đổi"; ở đây là **"bank không có headroom"** — mọi hành động cho cùng kết quả. Không có bậc tự do thì reputation không thể tạo gain, đúng như I3 dự báo.

### 3.2 Vòng 2 — trả lời Q2: composition & backbone diversity (19/10, 136 responses thật)

| Nhánh | Đúng/24 |
|---|---:|
| direct / self1 / self2 | 17 |
| **compose (ghép)** | **16** (0 rescue / 1 harm) |
| union | 17 |

Backbone 8B vs 14B: **11/16 giống nhau tuyệt đối**, oracle union cũng 11 → hai model **không bổ trợ**.
Native 27B: 11/16 **kèm 4 length stops**; cùng 16 case với `think=False`: **13/16, 0 length stop**.

> **Insight nối I1/I2:** I2 nói tín hiệu bổ trợ nằm ở cấp câu hỏi (68,34% oracle). Vòng này cho thấy **"bổ trợ ở cấp đáp án" ≠ "bổ trợ ở cấp hành động"**: hai backbone đúng y hệt nhau trên 11/16 case, nên ghép không tạo rescue. Đây là mảnh còn thiếu của I1: không chỉ *thiếu specialist theo môn*, mà **thiếu đa dạng lỗi** để ghép.

### 3.3 Vòng 3 — Q1 lần 2 trên domain tài chính, có baseline ngang quyền (20/10, 264 responses thật, 24 TAT-QA TRAIN context)

Chấm bằng **evaluator TAT-QA gốc**; audit PASS trên 9 frozen source files, prompt hash, model digest, GPU, re-execution toàn bộ; 0 mock / 0 unresolved / 0 length stop.

| Workflow (scoped) | Đúng/24 | Executable/24 | Calls/câu | Eval giây/câu |
|---|---:|---:|---:|---:|
| **Plain PoT** | **19** | 22 | 1 | 8,03 |
| KEEP có bindings | 15 | 18 | 1 | 7,23 |
| Sửa evidence (E) | 15 | 18 | 2 | 15,23 |
| Sửa operation/unit (O) | 16 | 19 | 2 | 15,38 |
| Ghép EO | 15 | 18 | 3 | 23,38 |
| Self1 / Self2 | 15 / 15 | 18 | 2 / 3 | 14,93 / 22,22 |

Oracle union KEEP/E/O/EO = **16 < Plain 19**; chỉ **1** case scoped-only đúng (gate cần ≥2) → **FAIL**.

Đối chứng **120 call bổ sung** (vì scoped Self2 bị lỗi contract, không thể làm "baseline mạnh"):

| Workflow không hạn chế hằng số | Qwen | Gemma4 |
|---|---:|---:|
| Plain | 19 | 16 |
| Self1 | 20 | 16 |
| Self2 | 20 | 16 |
| Union | **20** | — |

Union = **20 = best fixed 20**, **Gemma đóng góp 0 case duy nhất** → **FAIL** lần 2.

**Nhưng đây là phần quan trọng nhất của tuần** — hậu kiểm 0 call mới trên chính output đã lưu:

| Chẩn đoán hậu kiểm | Kết quả | Ý nghĩa |
|---|---|---|
| Chuẩn hoá *count contract* (đổi divisor hằng số → `len([...])`) | KEEP/E/O/EO/Self1/Self2 đều **20/24** | 5 câu trung bình model **đã tính đúng**, chỉ bị reject vì format |
| Prune metadata unit (parser chặn string) | Qwen **20/20/20**, Gemma **18/18/18**, union 20 | Không phải Gemma bị phạt format ⇒ bank thật sự thiếu headroom |
| Receiver fallback `joint→O→E→KEEP` | EO **15 → 16** | **(I=-1) là lỗi acceptance**, không phải "ghép 2 sửa thì hại" |
| 4/24 case còn lỗi | gross/net, dấu, scale annotation | Lỗi *ngữ nghĩa tài chính*, không phải reputation |

> **Điểm chốt:** nếu chỉ đọc lại output đã lưu (giữ nguyên mọi quyết định), **mọi nhánh đều 20/24**. Nghĩa là **toàn bộ khoảng cách 15 vs 20 không đến từ thuật toán** — nó đến từ *hợp đồng sinh code*. Điểm chính thức vẫn giữ 15/15/16/15/15/15 và **không được trình bày như gain của reputation**.

### 3.4 Chuẩn bị phép thử tuần sau — EvalPlus (0 model call, 0 execution)
Nguồn chính thức pin revision `26d6d00b…`, MBPP+ v0.2.0, license + hash. 378 tasks → **32 dev tasks chọn bằng hash task-ID** (không chọn theo điểm): **96 base inputs + 3.397 plus inputs**. Đã đọc special-oracle (1 oracle chấp nhận `output-not-None`). Chưa map overlap MBPP200 ⇒ **không được gọi là split độc lập**.

---

## 4. Insight tuần này, đặt cạnh insight tuần trước

| Tuần trước | Tuần này bổ sung gì | Hệ quả chung |
|---|---|---|
| **I2:** nhãn *môn* quá thô để định tuyến (oracle theo môn chỉ +1,21 điểm) | **I5:** *"pass"* cũng quá thô để verify — cùng loại lỗi, khác tầng: tín hiệu **không phân biệt** được người giỏi/người kém | Vấn đề cốt lõi là **độ phân giải của tín hiệu**, không phải công thức reputation |
| **I1:** chỉ 1 specialist được xác nhận | **I6:** ngay cả khi ghép 2 backbone, **11/16 case đúng y hệt** ⇒ thiếu đa dạng lỗi, không chỉ thiếu specialist | Gate (i) của Week 3 chưa thể đạt bằng pool hiện tại |
| **I3:** score đổi, quyết định không đổi; Brier tốt không ⇒ accuracy tốt | **I7:** ở tầng hành động **cũng vậy**, với nguyên nhân rõ hơn: bank *không có headroom* (oracle 16 < plain 19; union = best fixed 20) | Đổi benchmark không giải quyết; phải **tạo headroom + tín hiệu phân biệt được** trước khi học |
| **I4:** 37/41 trên 2.416 câu đổi đáp án | **I8:** "gain" tưởng thấy (14 vs 19, 16 vs 19) **biến mất** khi baseline được xử lý format đầy đủ | **Mọi so sánh phải cấp format/contract ngang nhau** — nếu không sẽ tự lừa mình |
| — | **I9:** `pass` là **feedback censored**: `B=0 ⇒ F=0`, `B=1 ⇏ F=1` ⇒ đại lượng đúng là `P(F=1 \| B=1, agent, task, trạng thái verify)`, **khác** `P(F=1 \| agent)` | Đây là **cơ chế có thể đổi ranking**, và là đối tượng của phép thử tuần sau |
| — | **I10:** 0 harm/24 chỉ cho cận trên harm **11,73%** (1/24 → 18,29%); cần **≥149 mẫu độc lập** để đưa về 2% | Không được nói "an toàn" khi accuracy bằng nhau |

**Một câu tóm mạch 2 tuần:** *tuần trước ta chứng minh tín hiệu reputation hiện có không đổi được quyết định; tuần này ta chứng minh lý do nằm ở **tín hiệu** (thô + censored + bank không headroom), chứ không ở **thuật toán** — nên phép thử tiếp theo phải tạo ra tín hiệu đúng trước.*

---

## 5. Quyết định của tuần (D1–D6)

| # | Quyết định | Nối từ |
|---|---|---|
| **D1** | **Không** có phương pháp reputation đủ bằng chứng để chốt làm đóng góp chính (560 call thật, 3 gate FAIL) | I3, I7 |
| **D2** | **Không** đổ thêm ngân sách thu history rows cho bank đã chạm trần | I7 |
| **D3** | **Không** tính gain do sửa contract/format/readout là gain reputation; contract tốt phải cấp **ngang cho mọi baseline** | I8 |
| **D4** | Giữ nguyên trục đề tài **multi-agent reputation dưới imperfect feedback**; không đổi tên đề tài, không biến khóa luận thành benchmark/forensics | I3 |
| **D5** | Phép thử kế tiếp: **EvalPlus nested tests** (basic vs extended) + **audit hướng quyết định** (giảm decision regret thay vì Brier) | I5, I9 |
| **D6** | FinQA/TAT-QA giữ làm **application track** nếu GVHD yêu cầu; **không** dùng bank oracle-context đã bão hoà làm bằng chứng reputation | I7 |

---

## 6. Codebase hiện tại (đo trong lượt này)

| Hạng mục | Số liệu | Ghi chú |
|---|---|---|
| Commit mới nhất | `f3c7446` — 24/10/2026 | Cycle 01–03 + handbook đã vào repo |
| `src/repguard/` | 41 file, **8.280 dòng** | Harness, split/hash, GT isolation, providers, logging |
| `thesis_pilot/` | 42 file, **3.739 dòng** | 4 app Modal riêng, volume riêng, không dùng Ollama của người dùng |
| `tests/` | 43 file, **4.023 dòng**, 232 test collect | — |
| Chạy test local (Windows) | **257 passed / 12 failed / 2 skipped / 13 lỗi collect** | 12 fail + 13 lỗi collect là **thiếu dependency**: `rich`, `ijson`, `fcntl` (POSIX-only) — không phải lỗi logic. **Phải chạy lại trên Linux/Modal trước khi trích số test vào báo cáo** |
| Tài liệu | **127 MD + 79 JSON** trong `docs/analysis` | Mỗi vòng: protocol + result + audit JSON |
| Chi phí 3 vòng | 160 + 136 + 264 = **560 responses**; vòng 3: 572.340 in / 59.841 out tokens | Runtime counter, **không** phải billing — không báo tiền |
| Containers sau thu thập | **0** trên cả 4 app | Không có job chạy ngầm |

---

## 7. Kế hoạch tuần sau (28/10 – 03/11): 1 gate, viết trước

**Câu hỏi duy nhất:** *Trong pool hiện tại, `basic tests pass` có dự báo sai `full-suite pass` đủ mạnh để tạo ra lợi ích khi chọn teammate không?*

| Ngày | Việc | Gate / điều kiện dừng | Nối từ |
|---|---|---|---|
| 28–29/10 | **Software preflight** trong sandbox cô lập: evaluator EvalPlus, canonical solutions, input-domain contract, deserialization, special oracle, timeout. **Không** tính là pass@1 | Fail ⇒ sửa harness, **không** chạy model study | I8 (contract phải đúng trước) |
| 29–30/10 | **Pilot khoá**: sinh code thật, chạy **cả** basic **và** full suite. Đo (a) **false-positive rate** `B=1, F=0`; (b) complementarity sau filter public-test; (c) baseline mạnh **cùng tools/calls** | Phải có regime `B=1 ⇏ F=1` **và** oracle > best fixed đủ lớn. Fail ⇒ **STOP**, không fit method | I5, I9 |
| 31/10 | Nếu PASS: khoá history/audit/validation; so **ngang quyền**: global/skill reputation, raw feedback, feedback-only calibration, ECRT cũ, **contextual action-value learner**, audit uniform/uncertainty/disagreement **cùng số label** | Budget audit = **số label tiết lộ**, không giả vờ CPU rẻ hơn model call | I3 (phải thắng control mạnh) |
| 01/11 | Ablation + cost ledger; giữ kết quả âm; chốt cỡ confirmation **trước** khi mở score | Không mở rộng nếu effect không vượt control | I10 (power) |
| 02/11 | Báo cáo tuần + cập nhật `research_log.md`, `experiment_registry.csv`, `paper_claims.md`, `open_questions.md` | Không claim nào thiếu bảng/hình | — |

**Deliverable:** preflight report (pass/fail phần mềm) · bảng false-positive + complementarity + paired CI · quyết định **GO/STOP** cho hướng EvalPlus · nháp *Evaluation Protocol* HistRepEval v0.2 nếu pilot đủ tín hiệu.

---

## 8. Rủi ro & câu hỏi xin ý kiến GVHD

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Trượt từ "reputation" sang "code repair benchmark" | **Cao** | D4: EvalPlus chỉ là *setting* tạo feedback không hoàn hảo; đóng góp vẫn là reputation/audit |
| Lặp lại hướng DART cũ (đã fail) với tên khác | **Cao** | Đọc lại toàn bộ variant DART 05/10 trước khi code; VOI/paired audit **không** phải ý mới |
| 32 dev tasks không độc lập (overlap MBPP200, pretraining) | Trung bình | Map overlap trước khi gọi là test split |
| Không đủ mẫu để kết luận non-inferiority | Trung bình | Power-check trước; 0 harm/24 chỉ cho cận 11,73% |
| Thời gian còn lại của DACN | **Cao** | Ưu tiên measurement paper có replication; prototype làm sau bằng chứng |

**Câu hỏi cho GVHD**
1. Nếu pilot EvalPlus fail gate, thầy có chấp nhận hướng **measurement paper** (đặc trưng hoá khi nào reputation từ lịch sử *không* dùng được) làm đóng góp chính không?
2. Có cần giữ domain tài chính (FinQA/TAT-QA) như **application track** song song, hay dồn toàn bộ vào coding-feedback?
3. Mức "confirmation độc lập" hội đồng yêu cầu là bao nhiêu task/mẫu để chấp nhận một kết quả âm?

---

## 9. Những gì **KHÔNG** được claim

- ❌ "Test pass chưa chắc đúng" / "thêm test là đóng góp của chúng tôi" → **EvalPlus (NeurIPS 2023)** đã làm.
- ❌ "Multi-agent generation + testing" → **AgentCoder (2023)**, **CANDOR (2025)**.
- ❌ "Diagnosis → repair" → **DARC (2026)**. "Phân rã claim/unit" → **MoCA-Agent (2026)**. "STOP/gain theo performance–cost" → **RLCascadeRouter (2026)**.
- ❌ "VOI / active audit / Bayesian reputation / conditional trust" → đều có tiền lệ; chỉ nhận nếu thắng **contextual action-value learner với cùng thông tin**.
- ❌ "20/24 (hoặc 17/24) là phương pháp thắng" → **post-hoc readout** trên output cũ, 0 call mới, điểm chính không đổi.
- ❌ "Accuracy bằng nhau ⇒ an toàn" → cận harm 11,73% ở 0/24.
- ❌ Gọi 32 task EvalPlus là "độc lập"/"không nhiễm pretraining" khi overlap chưa map.
- ❌ Dùng số test suite local (257 passed) như trạng thái CI chính thức khi chưa chạy trên Linux/Modal.

✅ **Được claim:** (i) hạ tầng thực nghiệm **có audit, có hash, không mock, tách gold khỏi GPU**; (ii) **đặc trưng hoá bằng số** rằng cả hai tầng (chọn đáp án và chọn hành động) đều bị chặn bởi **tín hiệu**, không bởi thuật toán; (iii) **truy vết nguyên nhân** tới mức contract/compiler thay vì quy kết "model yếu"; (iv) **thiết kế phép thử tiếp theo có gate viết trước**.

---

## 10. Kịch bản trình bày 5 phút

| Thời lượng | Nội dung | Câu chốt |
|---|---|---|
| 0:00–0:50 | Nhắc mốc tuần trước: 18.064 đáp án thật, 4 model, Q×T 19.656 hàng → **3 insight I1–I4** | "Tuần trước chúng em đã trả lời *Q và T có ảnh hưởng không*: có, nhưng chỉ ở calibration." |
| 0:50–1:30 | Điểm gãy I3/I4: score đổi, quyết định không đổi; 129/129 cùng ranking; +0,02 điểm % | "Đây là câu hỏi mở mà tuần này phải đóng." |
| 1:30–3:00 | 3 vòng tuần này (bảng 3.1–3.3), nhấn vòng 3: 19 vs 15 → sau khi chuẩn hoá contract **mọi nhánh 20/24** | "Ba vòng, ba gate FAIL — và nguyên nhân là **tín hiệu**, không phải thuật toán." |
| 3:00–3:50 | Insight mới I5–I9, đặc biệt I9 (`pass` là feedback censored) | "`B=0 ⇒ F=0` nhưng `B=1` không suy ra `F=1`." |
| 3:50–4:30 | Quyết định D1–D6 | "Không đổi đề tài; đổi **phép thử**." |
| 4:30–5:00 | Kế hoạch tuần sau: 1 gate + 3 câu hỏi xin ý kiến | "Nếu gate fail, chúng em có kết quả âm sạch và chuyển sang measurement paper." |

**Q&A dự kiến**
- *"Tuần trước đã GO-C, sao vẫn chạy tiếp?"* → Vì GO-C chỉ bác **method claim**, không bác **câu hỏi**. Tuần này kiểm tra xem điểm gãy nằm ở *thiếu bậc tự do hành động* hay ở *tín hiệu* — kết quả: ở tín hiệu.
- *"560 call mà vẫn fail?"* → Mỗi vòng đóng một giả thuyết và tạo control dùng lại được; rẻ hơn nhiều so với viết paper trên kết quả không tái lập.
- *"Bao giờ có kết quả dương?"* → Không hứa. Có ngưỡng: nếu pilot EvalPlus không tạo regime `B=1 ⇏ F=1` thì chuyển measurement paper.

---

## 11. Ghi chú biên tập (rút từ 2 deck cũ — sửa trước khi trình)

- **Footer sai kỳ:** Week 1 ghi "December 2025" gần như mọi slide, bìa lại là "September 16th 2026".
- **Chính tả:** "for the tas**j** at hand", "batrayal", "sciencetific", "seperate", "Greate at legal reasoning", "**ERCT** keeps the confidence band" (đúng: ECRT).
- **Slide 6 (Week 1):** ô 2×2 ghi "Reliable + Irrelevant" **hai lần** (một ô phải là *Reliable + Relevant*).
- **Slide 18 (Week 1):** nhãn "condition" lặp 12 lần, thiếu nội dung điều kiện.
- **Week 2:** 5/10 trang là hình không có dòng "takeaway" ⇒ người nghe không trích được số.
- **Nhất quán số liệu:** deck cũ ghi "14 domains / 4 agents"; báo cáo mới phải nói rõ 18.064 đáp án và **chỉ 1 specialist được xác nhận**, nếu không sẽ bị hỏi lại.
- **Bổ sung cho deck tuần này:** mỗi bảng kết quả nên có 1 dòng *"kết luận được phép rút ra"* và 1 dòng *"kết luận KHÔNG được rút ra"* — đây là cách chặn câu hỏi hóc búa nhất của hội đồng.

---

## 12. Phụ lục

**Tài liệu gốc**
- Tuần trước (nối tiếp): `docs/analysis/repguard_week3_real_report.md`, `docs/analysis/repguard_6_week_research_plan.md`
- Tuần này: `repguard_research_cycle_01_2026-10-18.md`, `repguard_research_cycle_02_2026-10-19.md`, `repguard_research_cycle_03_2026-10-20.md`, `repguard_research_decision_2026-10-20.md`
- Bức tranh toàn dự án: `docs/analysis/project_status_review_2026-10-18.md`; sổ tay `docs/book/repguard_research_handbook_2026-10-08.pdf`

**Kiểm chứng lại (không gọi model)**
```bash
./.venv/bin/python docs/analysis/verify_research_cycle_01.py
./.venv/bin/python docs/analysis/verify_composition_cycle02.py
./.venv/bin/python docs/analysis/verify_backbone_probe.py
./.venv/bin/python docs/analysis/verify_modern_probe.py
./.venv/bin/python docs/analysis/verify_modern_direct_control.py
./.venv/bin/python docs/analysis/verify_tatqa_scope_cycle03.py
./.venv/bin/python docs/analysis/verify_tatqa_crossfamily_cycle03.py
```

**Chuẩn bị EvalPlus (đã có, chưa chạy model)**
```bash
./.venv/bin/python docs/analysis/prepare_evalplus_source_inventory.py
```

**Mạch nối một dòng (dán lên slide đầu nếu cần)**
`4 model thật (18.064 đáp án) → Q×T 19.656 hàng → I1–I4 (score đổi, quyết định không đổi) → 560 call tuần này → I5–I9 (nút thắt là TÍN HIỆU: thô + censored + bank không headroom) → tuần sau: tạo tín hiệu lồng nhau bằng EvalPlus, 1 gate viết trước`

---

*Mọi con số lấy từ protocol/result/audit đã freeze trong `docs/analysis` và `results/` (private). Các phép đọc lại (readout/replay) là kiểm phần mềm hậu nghiệm trên output thật đã lưu: không tạo response mới, không thay điểm chính, không được tính là thắng lợi của phương pháp.*
