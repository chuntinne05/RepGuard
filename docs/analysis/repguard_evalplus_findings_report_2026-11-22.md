# Báo cáo kết quả — Feedback không hoàn hảo trên EvalPlus (22/11/2026)

Tổng hợp hai thí nghiệm có protocol khoá trước trên EvalPlus (MBPP+, HumanEval+) và một phân
tích khám phá. Nhánh: `thesis/evalplus-disagreement-v3`.

## 1. Tóm tắt

> Với feedback không hoàn hảo (test cơ bản), reputation theo agent đủ để **xếp hạng agent trung
> thực**, nhưng **không chỉ ra được feedback nào sai** và **sập khi có agent lách test**. Thứ
> bảo vệ hệ thống là **audit bằng nhãn thật**; **độ bất đồng hành vi theo từng mục** là cách
> hiệu quả để chọn mục cần audit, nhưng **không** cải thiện việc chọn agent và **không** chống
> được agent gian lận thông đồng.

| # | Phát hiện | Mức bằng chứng |
|---|---|---|
| F1 | Pass giả tập trung theo task: 57% FP nằm ở 10% task (Gini 0,79) | Confirmation v3, cả 2 pool |
| F2 | Độ bất đồng bắt pass giả gấp ~2 lần reputation agent / learner (+132, CI [67, 185]) | Confirmation v3, pool 22 |
| F3 | Thêm độ tin theo mục vào ECRT không cải thiện chọn lời giải (−0,8 điểm, CI [−2,3; 0]) | Confirmation HumanEval+ (âm tính) |
| F4 | Reputation từ B thô giữ đúng thứ hạng agent (Spearman ρ = 0,98) | Khám phá, MBPP+ |
| F5 | RawRep/ECRT sập về ~0 khi có agent lách test; audit nhãn thật giữ được | Dev + confirmation, agent tổng hợp |
| F6 | Độ bất đồng bị phá khi agent gian lận cho output giống nhau | Confirmation S2, agent tổng hợp |

## 2. Thiết lập chung

- **Feedback quan sát** `B` = pass base tests; **nhãn thật** `F` = pass base + plus tests (EvalPlus).
  **Pass giả** = `B=1, F=0`.
- Lời giải: output greedy **đã công bố** của EvalPlus (năm 2023), không tự sinh. Chấm bằng
  evaluator chính thức trong Docker `--network none`.
- **Độ bất đồng** `d(m,t)`: sinh 30 input đột biến/task (mutation chính thức EvalPlus, seed
  20261122, không dùng plus input / canonical solution / expected output); chạy mọi lời giải
  `B=1`; `d` = tỷ lệ input mà output của m khác output đa số. Không dùng nhãn.

## 3. Thí nghiệm v3 — chọn mục để audit

Protocol: `repguard_evalplus_disagreement_audit_protocol_2026-11-22.md` (sha256 `dd760db8…`).
Dữ liệu: MBPP+, 22 model, calibration 32 task, confirmation 339 task (7 task làm sập evaluator
bị loại hoàn toàn: 255, 267, 274, 300, 388, 392, 752).

**Pass giả bắt được** (pool 22: 4.723 ô B=1, 783 FP)

| Budget | Random | AgentRep | ActionValue | Disagreement+AV | **Disagreement** |
|---|---|---|---|---|---|
| 5% (236) | 39,1 | 54 | 70 | 107 | **153** |
| 10% (472) | 78,3 | 103 | 146 | 182 | **278** |
| 20% (945) | 156,7 | 169 | 257 | 298 | **340** |

- **Primary (10%):** Disagreement − ActionValue = **+132**, CI 95% bootstrap theo task [67, 185] → **thành công**.
- Average precision: Random 0,166 · AgentRep 0,177 · ActionValue 0,264 · Disagreement+AV 0,334 · **Disagreement 0,393**.
- Pool P7 (4 model, 806 ô, 152 FP): +10, CI [−2, 24] → **không có ý nghĩa**; tín hiệu cần nhiều lời giải.

## 4. Phân tích khám phá — reputation có xếp hạng đúng agent không

Trên 339 task confirmation, tỷ lệ `B` của từng model so với tỷ lệ `F`:
- Spearman ρ(B, F) = **0,984**; top-3 theo B và theo F trùng nhau (GPT-4, GPT-3.5, DeepSeek-33B-instruct).
- B thổi phồng F khoảng 9–14 điểm ở mọi model; model yếu có tỷ lệ FP cao hơn vừa phải
  (ρ(B, tỷ lệ FP) = −0,53).
- Không có protocol khoá trước → chỉ là định hướng.

## 5. Thí nghiệm ECRT-v2 — chọn lời giải với reputation online

Protocol: `repguard_ecrt_v2_item_reliability_protocol_2026-11-22.md` (sha256 `361dd67e…`).
**Thay đổi so với ECRT gốc:** ECRT-1 tính `p = P(đúng | B, bin(d))` thay vì một cặp
sensitivity/specificity chung; audit theo `d`; khi quyết định nhân thêm `q(bin(d))`. τ = 1
(EvalPlus không có lĩnh vực). Mỗi task chọn một model trong các model có B=1; điểm = F.
MBPP+ chỉ là development; **confirmation = HumanEval+, chạy một lần.**

**Độ chính xác chọn lời giải**

| Phương pháp | Dev MBPP+ S1 | Dev MBPP+ S2 | **HE+ S1** | **HE+ S2** |
|---|---|---|---|---|
| Random | 0,777 | — | 0,769 | 0,471 |
| SingleBest | 0,824 | 0,824 | 0,826 | 0,826 |
| RawRep | **0,835** | 0,004 | 0,826 | 0,000 |
| ECRT (gốc) | **0,835** | 0,004 | 0,826 | 0,000 |
| AuditedECRT | 0,824 | 0,820 | 0,826 | 0,826 |
| MBR-exec | 0,783 | 0,761 | 0,765 | 0,530 |
| **ECRT-v2** | 0,820 | 0,8125 | 0,818 | 0,576 |
| ECRT-v2-noaudit | 0,824 | 0,787 | 0,811 | 0,576 |
| Oracle | 0,886 | — | 0,841 | 0,841 |

Dev: 22 model, 67 task calibration / 272 task evaluation. HE+: 12 model có mẫu greedy công
bố (code-llama 7/13/34b, codegen 2/6/16b, codet5p 2/6/16b, gpt-4-1106-preview, mistral-7b,
starcoder), 32 / 132 task, không task nào bị loại. S2 = S1 + 2 agent lách test tổng hợp
(hardcode output base tests).

- **Primary (HE+ S1):** ECRT-v2 − max baseline = **−0,0076**, CI [−0,023; 0] → **không thành công**.
- HE+ S2: ECRT-v2 − max baseline = −0,25, CI [−0,33; −0,17]; ECRT-v2 − ECRT = +0,58; ECRT-v2 − MBR-exec = +0,045, CI [0,008; 0,091].
- Dự đoán đã ghi trước "MBR-exec khó bị thắng" **sai**: MBR-exec gần như ngang Random ở bài toán chọn lời giải.

## 6. Diễn giải

1. **Độ tin là thuộc tính của mục, không của agent** (F1, F2): FP do test yếu của từng task, nên
   mọi agent đều bị thổi phồng gần như ngang nhau. Hệ quả: reputation agent vẫn xếp hạng đúng (F4)
   nhưng vô dụng để chọn mục cần audit.
2. **Hai bài toán khác nhau cần thành phần khác nhau:** chọn agent → lịch sử feedback thô là đủ;
   chọn mục để audit → độ bất đồng. Ghép độ bất đồng vào điểm quyết định (ECRT-v2) không có lợi (F3).
3. **Chống gian lận cần nhãn thật** (F5): agent lách test có B=1 ở mọi task nên mọi reputation chỉ
   dựa trên B đều bị chiếm. Khớp với claim C8 trước đó trên MMLU-Pro (AuditedECRT ≈ AuditOnly).
4. **Độ bất đồng giả định các lời giải độc lập** (F6): 2 agent gian lận giống hệt nhau trong pool 12
   model đủ tạo "đa số" giả, làm model thật bị coi là lệch.

## 7. Sai lệch và giới hạn (phải báo kèm mọi claim)

- **Lỗi thiết kế ngưỡng audit (ECRT-v2):** ngưỡng = phân vị 90% của `d` trên calibration; ở HE+ S1
  phân vị này bằng 0 nên ECRT-v2 audit **609/609 ô (100%)** thay vì 10%. Dù vậy ECRT-v2 vẫn thua,
  gợi ý phần nhân `q(d)` lúc quyết định là phần gây hại — **chưa kiểm chứng**.
- AuditedECRT được dùng nhãn calibration như audit (quyết định harness, làm baseline mạnh hơn).
- v3: giả thuyết hình thành sau khi xem dev; dòng signature dùng để lọc input lấy từ canonical
  solution (chỉ tên hàm và tham số, cũng có trong đề bài).
- Task bị loại vì làm sập evaluator không phải mẫu ngẫu nhiên.
- Agent lách test là tổng hợp, không phải hành vi model thật.
- HE+ chỉ 12 model, 132 task evaluation → CI rộng; không so trực tiếp được với MBPP+ (22 model).
- Output model năm 2023, MBPP/HumanEval có thể nằm trong dữ liệu huấn luyện.
- So output giữa nhiều lời giải đã có tiền lệ (N-version programming, differential testing,
  query-by-committee, MBR-exec, CodeT, AlphaCode); chưa tra tài liệu đầy đủ. Đóng góp là bằng
  chứng so sánh với reputation agent, không phải ý tưởng độ bất đồng.
- ECRT-2 (chuyển lĩnh vực) không được kiểm tra trên EvalPlus.

## 8. Claim đề xuất cho `research_ops/paper_claims.md`

- **C11 — Item-level disagreement allocates audits better than agent reputation:** SUPPORTED on
  MBPP+ pool 22 (pre-registered confirmation); not significant for 4-model pool; one dataset.
- **C12 — Item-reliability ECRT (ECRT-v2) improves agent/solution selection:** NOT SUPPORTED
  (HumanEval+ confirmation, −0,8 pt, CI [−2,3; 0]).
- **C13 — Feedback-only reputation is captured by test-gaming agents; gold audit protects:**
  SUPPORTED for synthetic hardcoding agents on MBPP+ dev and HumanEval+; real strategic agents untested.
- **Do not claim:** ECRT/ECRT-v2 superiority; robustness of disagreement to colluding agents;
  novelty of the disagreement idea.

## 9. Việc tiếp theo

1. Kiểm tra lại: đối chiếu code ECRT-v2 với protocol; đọc tay ~20 ca pass giả; xử lý 13 lỗi
   collection khi chạy `pytest tests`.
2. Tra tài liệu cho phần độ bất đồng trước khi viết đóng góp.
3. (Tuỳ chọn, khám phá) ablation ECRT-v2 không nhân `q(d)` trên dữ liệu đã có.
4. (Nếu còn thời gian) một thí nghiệm khoá trước về **phân bổ audit khi có agent gian lận**:
   AuditedECRT với audit chọn theo `d` (top-k, không dùng phân vị), gộp lời giải giống hệt nhau khi
   tính đa số, đo đường cong ngân sách audit; cần dữ liệu mới chưa xem để xác nhận.

## 10. File

- Code: `thesis_pilot/evalplus_disagreement.py`, `thesis_pilot/ecrt_v2_study.py`,
  `src/repguard/reputation/ecrt_item.py`, `thesis_pilot/evalplus_docker/`.
- Test: `tests/test_evalplus_disagreement.py`, `tests/test_ecrt_item.py`.
- Kết quả: `results/thesis_evalplus_disagreement_v3/results.json`,
  `results/thesis_ecrt_v2/dev_mbpp/results.json`, `results/thesis_ecrt_v2/confirm_humaneval/results.json`.
