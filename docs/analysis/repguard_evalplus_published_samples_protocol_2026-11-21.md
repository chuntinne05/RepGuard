# Protocol khoá — EvalPlus partial-feedback v2: output đã công bố (21/11/2026)

**Trạng thái:** viết và hash TRƯỚC khi chấm bất kỳ mẫu nào. Đã mở đúng 1 file mẫu
(`mistral-7b_temp_0.0.zip`, task `Mbpp_287`) để kiểm định dạng; chưa chạy code nào.
Mọi thay đổi sau khi chấm phải tạo protocol/run identity mới.

**Thay thế v1** (`repguard_evalplus_partial_feedback_protocol_2026-11-09.md`): v1 dừng ở
43/160 response, giữ nguyên artifact, **không dùng vào kết quả**. Lý do đổi (nêu trước khi có
bất kỳ số B/F nào): pool v1 gồm 5 SLM, 3/5 cùng họ Qwen, kích cỡ 0,6B–9B ⇒ chênh lệch năng
lực lấn át khác biệt về độ tin của feedback; máy local không còn Ollama; Modal không dùng được.

## 1. Câu hỏi (giữ nguyên v1)

Trong một pool model **cùng cỡ, khác họ**, `B` (pass base tests) có dự báo sai `F` (pass
base+plus) đủ thường và ở đúng chỗ ảnh hưởng lựa chọn, để reputation có điều kiện theo feedback
censored có cơ hội tạo lợi ích quyết định? `B=0 ⇒ F=0`; `B=1 ⇏ F=1`.

## 2. Dữ liệu

- **Output:** các file `*_temp_0*.zip` (greedy, 1 mẫu/task) trong release `v0.2.0` của
  `github.com/evalplus/evalplus` (22 model, công bố 11/2023). Ghi sha256 từng file lúc tải.
  Không sinh thêm output, không gọi model nào.
- **Task và test:** MBPP+ v0.2.0 đã pin (`results/thesis_evalplus_source_v1/`, 378 task;
  sha256 `af43697e…db63`). Dùng giao của 378 task này với task có trong mỗi zip. Output được sinh
  trên prompt MBPP+ v0.1.0 (399 task) — giới hạn, ghi rõ trong báo cáo.
- **Development** = đúng 32 task đã chọn bằng hash từ 20/10 (`inventory.json → case_ids`).
  **Confirmation** = toàn bộ task còn lại trong giao. Confirmation chỉ được chấm điểm/đọc
  sau khi gate development PASS, và chỉ một lần.

## 3. Chấm điểm

- Evaluator chính thức `evalplus.evaluate.evaluate("mbpp", …)` ở revision
  `26d6d00bb1fd0fa37f39c99d5290da67891d1c5e`, `MBPP_OVERRIDE_PATH` = subset tương ứng;
  trích code bằng `evalplus.sanitize.sanitize(code, entry_point)` chính thức.
- **Code do model sinh chỉ chạy trong Docker container Linux** `--network none`, giới hạn
  RAM/CPU, mount mẫu read-only. Không chạy trên host Windows.
- **Preflight G0** (lặp lại trên Docker, như v1): 32/32 canonical pass base+plus; chạy lần 2
  giống hệt; null control fail base 32/32; xác nhận container không có mạng.
- Chấm **toàn bộ 22 model** (để mô tả), nhưng phân tích chính chỉ dùng pool khai báo ở §4.
  Trên development, chấm xong mới tính gate; trên confirmation, chấm sau khi gate PASS.

## 4. Pool (khai báo trước, theo dòng họ/kích cỡ, không theo kết quả)

| Pool | Model | Vai trò |
|---|---|---|
| **P7 — primary** | `code-llama-7b` (Meta), `deepseek-coder-6.7b-base` (DeepSeek), `mistral-7b` (Mistral), `codegen-6b` (Salesforce) | Cùng cỡ 6–7B, 4 dòng họ, đều là model base |
| **P15 — secondary** | `code-llama-13b`, `starcoder` (BigCode 15.5B), `codegen-16b` | Cùng cỡ 13–16B, 3 dòng họ, base |
| **Strong — mô tả** | `deepseek-coder-33b-instruct`, `code-llama-34b`, `gpt-3.5-turbo`, `gpt-4-1106-preview` | Kiểm censoring còn xuất hiện ở model mạnh không; không có gate |

Loại khỏi P7/P15 vì trùng dòng họ: `wizardcoder-*` (fine-tune CodeLlama/StarCoder),
`zephyr-7b` (fine-tune Mistral), `codet5p-*` (decoder khởi tạo từ CodeGen). Nếu một zip trong
pool thiếu hoặc hỏng ⇒ STOP, không thay model.

## 5. Gate (development, mỗi pool P7 và P15 riêng; ngưỡng giữ như v1)

- **G1** `FP = #(B=1,F=0) ≥ 8` **và** `FPR = FP/#(B=1) ≥ 0.10`.
- **G2** `oracle − best fixed ≥ 3` (task có ≥1 model F=1, trừ số F=1 của model tốt nhất).
- **G3** `D = #task có ≥2 model B=1 và bất đồng về F ≥ 3`.
- PASS = G0 ∧ G1 ∧ G2 ∧ G3. **P7 fail ⇒ STOP** phần phương pháp; báo kết quả âm và chỉ mô tả
  FPR theo model/kích cỡ trên toàn bộ task. P15 chỉ là phân tích phụ, không cứu P7.

## 6. Replay (chỉ khi P7 PASS)

Giữ nguyên thuật toán `thesis_pilot/evalplus_replay.py` (leave-one-task-out; audit policy
Uniform / CensoredUniform / Disagreement; selector BestFixedB, RawB, GlobalRepF,
CensoredRep, ActionValue; 200 seed; bootstrap 2.000 theo task). Thay đổi duy nhất:
budget audit tính theo tỷ lệ số ô history, `k = round(0.10·|H|)` và `round(0.25·|H|)`
(v1: 16 và 39 ≈ 10%, 25% của 155 ô).

- Chạy trên development để kiểm phần mềm; **kết quả chính là confirmation**, một lần.
- **Primary:** P7, confirmation, `k = 10%`, audit `CensoredUniform`. Thành công khi
  `CensoredRep` hơn **cả** `RawB` và `ActionValue` ≥ 1 task tổng, CI bootstrap 95% có cận dưới > 0.
- Phụ: P15 cùng cách; Strong chỉ mô tả FPR.

## 7. Không được claim

- Không claim "pass test chưa chắc đúng" là mới (EvalPlus 2023).
- Output năm 2023, chủ yếu là model code chuyên dụng; prompt/cách sinh do EvalPlus quyết định,
  không đồng nhất hoàn toàn giữa các model. Không suy ra cho model hiện nay.
- Cùng số tham số ≠ cùng năng lực; báo B và F từng model.
- MBPP có khả năng nằm trong dữ liệu huấn luyện; không gọi là test sạch.
