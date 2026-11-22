# Protocol khoá — v3: độ tin của feedback theo task, audit dưới ngân sách (22/11/2026)

**Trạng thái:** viết và hash TRƯỚC khi chấm 346 task confirmation và trước khi chạy bất kỳ
input đột biến nào. **Giả thuyết hình thành sau khi xem dữ liệu development v2** (32 task):
52 ca B=1,F=0 tập trung 44/52 vào 4 task (Mbpp/794, 102, 109, 397). Vì vậy development chỉ
dùng để hiệu chuẩn baseline; **kết luận chỉ lấy từ confirmation, chạy một lần.**
Nối từ: `repguard_evalplus_published_samples_protocol_2026-11-21.md` (v2, gate dev FAIL).

## 1. Câu hỏi

Với ngân sách audit có hạn, xếp hạng các ô (model, task) có `B=1` theo **độ bất đồng hành vi
giữa các lời giải B=1 trên input mới, không dùng nhãn**, có bắt được nhiều "pass giả"
(`B=1, F=0`) hơn reputation theo agent và một learner cùng thông tin không?

## 2. Dữ liệu

- 22 model, output greedy đã công bố (v2 `download_manifest.json`), MBPP+ v0.2.0 đã pin.
- **Calibration** = 32 task development (nhãn F đã biết từ v2). **Confirmation** = 346 task
  còn lại; chấm B/F bằng evaluator chính thức trong Docker `--network none` (như v2).
- Pool chính: **cả 22 model**. Pool phụ: P7 (4 model) như v2.

## 3. Tín hiệu bất đồng (không nhãn)

- Mỗi task: sinh **30 input mới** bằng `TypedMut`/mutation chính thức của EvalPlus
  (`evalplus/gen`) từ base inputs, seed cố định `20261122`. **Không dùng plus inputs, không
  dùng canonical solution, không dùng expected output.** Nếu task có `contract` trong đặc tả thì
  dùng nó để loại input không hợp lệ; nếu không thì giữ hết.
- Chạy mọi lời giải B=1 của pool trên các input đó trong Docker (time limit mỗi lần gọi 1s;
  exception ghi thành output `EXC:<Type>`; timeout thành `TIMEOUT`).
- Điểm ô `d(m,t)` = tỷ lệ input mà output của m khác output đa số (plurality) của các lời giải
  B=1 cùng task; nếu task chỉ có 1 lời giải B=1 thì `d = 0`. So sánh output bằng `repr` sau
  chuẩn hoá float (làm tròn 6 chữ số).

## 4. Bài toán quyết định và đối chứng

Tập ứng viên = mọi ô B=1 của pool trên confirmation. Audit `k` ô = tiết lộ F của chúng.
Budget `k = 5%, 10%, 20%` số ô ứng viên. Điểm = số ô `F=0` bị audit (pass giả bắt được).

| Scorer | Thông tin |
|---|---|
| `Random` | kỳ vọng giải tích `k·FP/N` |
| `AgentRep` | `P(F=0|B=1,model)` Beta(1,1) học trên calibration (reputation theo agent, censored) |
| `ActionValue` | logistic regression học trên calibration; features: one-hot model, tỷ lệ model B=1 trên task, số base input, log độ dài lời giải |
| **`Disagreement`** (đề xuất) | `d(m,t)`, không dùng nhãn |
| `Disagreement+AV` (phụ) | ActionValue thêm feature `d` |

Hoà điểm phá bằng hash cố định của (model, task).

## 5. Tiêu chí (chỉ trên confirmation, pool 22 model)

**Primary:** budget 10%. Thành công khi `Disagreement − max(Random, AgentRep, ActionValue)`
> 0 với CI bootstrap 95% theo **task** (2.000 lần, seed 20261122) có cận dưới > 0.
Báo thêm: mọi budget, pool P7, average precision của từng scorer, phân bố FP theo task
(Gini / tỷ lệ FP nằm trong 10% task nhiều FP nhất).

## 6. Không được claim

- So output giữa nhiều lời giải đã có tiền lệ (CodeT 2022, MBR-exec 2022, EvalPlus 2023);
  đóng góp chỉ là bằng chứng so với reputation theo agent trong khung audit này.
- Output năm 2023, model code chuyên dụng; MBPP có thể nằm trong dữ liệu huấn luyện.
- Một lần chạy confirmation; không chỉnh scorer sau khi thấy kết quả.
