# Protocol khoá — ECRT-v2: độ tin feedback theo từng mục (22/11/2026)

**Trạng thái:** viết và hash TRƯỚC khi chạy bất kỳ phương pháp nào dưới đây và TRƯỚC khi
tải/chấm bất kỳ dữ liệu HumanEval+ nào. **Thiết kế hình thành sau khi xem kết quả v3**
(`repguard_evalplus_disagreement_audit_protocol_2026-11-22.md`): toàn bộ MBPP+ đã bị xem nên
chỉ là **development**; **kết luận chỉ lấy từ HumanEval+, chạy một lần.**
Không có tham số nào được chỉnh trên dev: mọi lựa chọn đã cố định trong file này.

## 1. Động cơ và thay đổi

ECRT gốc (`src/repguard/reputation/ecrt.py`) có ECRT-1 dùng **một cặp sensitivity/specificity
chung** cho mọi feedback, nên mọi "pass" được tin như nhau. v3 cho thấy pass giả tập trung theo
task (57% FP ở 10% task) và độ bất đồng `d` bắt FP gấp ~2 lần baseline.
**ECRT-v2 chỉ thay ECRT-1:** `p_it = P(z=1 | F_it, bin(d_it))`. ECRT-2/3/4 giữ nguyên
(τ = 1 vì EvalPlus không có lĩnh vực; posterior Beta(1,1); quyết định bằng cận dưới tin cậy).

## 2. Câu hỏi

Trong bài toán chọn lời giải để chấp nhận cho từng task, với reputation học online từ feedback
không hoàn hảo (B), ECRT-v2 có cho tỷ lệ chấp nhận đúng (F=1) cao hơn ECRT gốc, AuditedECRT,
model đơn tốt nhất và MBR-exec (chọn theo `d`, không reputation) không?

## 3. Dữ liệu

- **Development:** MBPP+ v3 (22 model, 339 task sau khi loại 7 task crash; nhãn B/F trong
  `results/thesis_evalplus_disagreement_v3/eval_confirmation.jsonl`, output đột biến trong
  `exec_cache/`). Chỉ để kiểm tra code chạy đúng; không chỉnh gì theo kết quả.
- **Confirmation:** HumanEval+ (bản pin của EvalPlus), output greedy đã công bố của **cùng các
  model trong 22 model có mẫu HumanEval** (báo danh sách và số lượng). Pipeline giống hệt v3:
  30 input đột biến/task, seed `20261122`, contract-filter, Docker `--network none
  --ulimit core=0 --memory 4g`, B/F bằng evaluator chính thức. Task làm sập evaluator bị loại
  hoàn toàn và liệt kê (quy tắc v3).

## 4. Giao thức online

- Thứ tự task: hoán vị cố định bằng seed `20261123`. **Calibration** = 20% task đầu (làm tròn
  xuống); **evaluation** = phần còn lại theo thứ tự.
- Trên calibration (dùng nhãn F): ước lượng sensitivity/specificity chung (ECRT gốc),
  `q(b) = P(F=1 | B=1, d ∈ b)` với Beta(1,1) cho các bin cố định
  `b ∈ {d=0, 0<d≤0.1, 0.1<d≤0.5, d>0.5}` (ECRT-v2), và model đơn tốt nhất (F cao nhất).
  Calibration cũng là history khởi đầu cho mọi reputation.
- Tại mỗi task t của evaluation: mỗi phương pháp chọn **một** model; điểm = F của lời giải đó.
  Ứng viên = các model có B=1 trên t; nếu không có B=1 thì ứng viên = tất cả. Sau quyết định,
  các ô của t vào history với feedback quan sát = B (và nhãn F chỉ cho ô được audit).
- **Audit:** ngân sách 10% số ô B=1 của evaluation. Audit theo `d`: audit ô B=1 khi
  `d ≥` phân vị 90% của `d` trên các ô B=1 của calibration. Audit ngẫu nhiên: Bernoulli(0.10),
  seed `20261123`. Ô được audit dùng F thật làm bằng chứng.
- Hoà điểm: hash cố định của (model, task).

## 5. Phương pháp

| Phương pháp | Điểm để chọn trong ứng viên |
|---|---|
| `Random` | ngẫu nhiên đều (kỳ vọng giải tích) |
| `SingleBest` | luôn chọn model tốt nhất trên calibration (nếu nó không trong ứng viên: theo thứ hạng calibration) |
| `RawRep` | cận dưới Beta từ B thô (ECRT `no_reliability`) |
| `ECRT` | ECRT gốc: sens/spec chung, cận dưới |
| `AuditedECRT` | `AuditedECRTReputation` hiện có, audit ngẫu nhiên 10% |
| `MBR-exec` | `d` nhỏ nhất (không reputation) |
| **`ECRT-v2`** (đề xuất) | cận dưới reputation ECRT-v2 (p theo bin `d`, audit theo `d`) × `q(bin(d_it))` |
| `ECRT-v2-noaudit` (ablation) | như ECRT-v2 nhưng không audit |
| `Oracle` | F thật (cận trên, chỉ báo cáo) |

## 6. Kịch bản

- **S1 (primary):** pool model thật.
- **S2:** S1 + 2 agent lách test tổng hợp: trên mỗi task trả đúng output kỳ vọng của base
  inputs (hardcode), output khác `None` → B=1, F=0 (trừ khi plus inputs ⊆ base inputs), `d`
  tính như agent thật. Tổng hợp, không phải hành vi model thật.
- **S3:** đường học: độ chính xác tích luỹ sau 20, 50, 100 task evaluation (S1, S2).

## 7. Tiêu chí (chỉ HumanEval+)

**Primary (S1):** `ECRT-v2 − max(SingleBest, RawRep, ECRT, AuditedECRT, MBR-exec)` trên độ
chính xác evaluation; thành công khi CI bootstrap 95% theo task (2.000 lần, seed `20261123`,
thứ tự task giữ nguyên) có cận dưới > 0.
**Secondary:** cùng phép so trong S2; ECRT-v2 vs ECRT (riêng); ECRT-v2 vs ECRT-v2-noaudit.
Báo mọi phương pháp, Oracle, số audit thực tế, và kết quả dev MBPP+ (chỉ mô tả).

## 8. Dự đoán và không được claim

- Dự đoán trước: S1 khó thắng MBR-exec vì reputation thô đã xếp hạng agent gần đúng trên MBPP+
  (ρ=0,98); S2 nhiều khả năng ECRT-v2 thắng ECRT/RawRep nhưng chưa chắc thắng MBR-exec.
  Nếu MBR-exec ≥ ECRT-v2 thì phải báo: reputation không thêm giá trị so với tín hiệu theo mục.
- ECRT-2 (chuyển lĩnh vực) không được kiểm tra ở đây.
- S2 là agent tổng hợp; HumanEval+ nhỏ (164 task) nên CI rộng; output model năm 2023, có thể
  nhiễm dữ liệu huấn luyện. Một lần chạy confirmation; không chỉnh sau khi thấy kết quả.
