# Protocol khoá — Lặp lại v3 (phân bổ audit theo bất đồng) trên HumanEval+ (28/11/2026)

**Trạng thái:** viết và hash TRƯỚC khi tính bất kỳ scorer audit nào trên HumanEval+.
**Đã biết trước:** dữ liệu HumanEval+ (12 model, nhãn B/F, output đột biến) đã được dùng cho
ECRT-v2 (chọn lời giải, `repguard_ecrt_v2_item_reliability_protocol_2026-11-22.md`); câu hỏi
audit chưa được tính trên dữ liệu này. Không sinh dữ liệu mới, không chỉnh gì so với v3.

## 1. Câu hỏi
Như v3 (`repguard_evalplus_disagreement_audit_protocol_2026-11-22.md` §1): xếp ô `B=1` theo
độ bất đồng `d` có bắt nhiều pass giả (`B=1,F=0`) hơn `AgentRep` và `ActionValue` không?

## 2. Dữ liệu và chia tập
- `results/thesis_ecrt_v2/confirm_humaneval/eval.jsonl` (B/F), `exec_cache/` (output trên 30
  input đột biến/task, seed 20261122), 12 model, 164 task, không task nào bị loại.
- **Calibration** = 32 task calibration của ECRT-v2 (hoán vị seed `20261123`, 20% đầu);
  **confirmation** = 132 task còn lại. Không dùng nhãn F của confirmation trừ khi chấm điểm.

## 3. Scorer, budget, tiêu chí
- Giữ nguyên v3: `d` (plurality, `repr` sau làm tròn float 6 chữ số; task có 1 ô B=1 → `d=0`),
  `Random` (kỳ vọng giải tích), `AgentRep` (Beta(1,1) của `P(F=0|B=1,model)` trên calibration),
  `ActionValue` (logistic regression, cùng features v3), `Disagreement+AV` (phụ). Phá hòa bằng
  hash cố định của (model, task). Dùng lại code v3, không viết lại công thức.
- Budget `k = round(frac·N)`, `frac ∈ {5%, 10%, 20%}`, N = số ô B=1 của confirmation.
- **Primary:** budget 10%: `Disagreement − max(Random, AgentRep, ActionValue)`; thành công khi CI
  bootstrap 95% theo task (2.000 lần, seed 20261122) có cận dưới > 0.
- Báo thêm: mọi budget, average precision, tập trung FP theo task (33/327-kiểu: số task chứa
  10% task nhiều FP nhất trên số task có ứng viên, và Gini).

## 4. Dự đoán và giới hạn
- Dự đoán: hiệu ứng cùng chiều nhưng yếu hơn MBPP+ pool 22 vì chỉ 12 model (P7 với 4 model
  không có ý nghĩa) và N nhỏ; có thể CI chạm 0.
- Một lần chạy; dữ liệu đã được dùng cho câu hỏi khác; output model năm 2023.
