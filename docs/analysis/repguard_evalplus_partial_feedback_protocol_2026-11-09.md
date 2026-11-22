# Protocol khoá — EvalPlus partial-feedback pilot v1 (09/11/2026)

**Trạng thái:** viết và hash TRƯỚC mọi model call. Không sửa sau khi đã sinh response;
mọi thay đổi phải tạo protocol/run identity mới và giữ artifact cũ.

**Nối từ:** I5/I9 và quyết định D5 trong `repguard_week_report_2026-10-27.md` §5, §7;
`repguard_research_decision_2026-10-20.md` mục "Gate và thứ tự công việc kế tiếp".

## 1. Câu hỏi duy nhất

> Trong pool model hiện tại, `B` (basic tests pass) có dự báo sai `F` (full suite pass)
> đủ thường, *và ở đúng chỗ ảnh hưởng tới lựa chọn teammate*, để reputation có điều
> kiện theo feedback bị censored có cơ hội tạo lợi ích quyết định?

Ký hiệu: `B` = pass toàn bộ base tests MBPP+; `F` = pass base **và** plus tests
(định nghĩa `plus_status` chính thức của EvalPlus). Theo cấu trúc: `B=0 ⇒ F=0`; `B=1 ⇏ F=1`.

## 2. Dữ liệu & evaluator (cố định)

- EvalPlus revision `26d6d00bb1fd0fa37f39c99d5290da67891d1c5e`, MBPP+ v0.2.0 (hash trong
  `results/thesis_evalplus_source_v1/inventory.json`).
- 32 dev tasks đã chọn từ 20/10 bằng SHA-256(salt + task_id), **trước** mọi outcome.
- Chấm bằng hàm `evalplus.evaluate.evaluate("mbpp", …)` chính thức (giữ deserialization,
  special oracle `MBPP_OUTPUT_NOT_NONE_TASKS`, `atol`, time limit mặc định 4s / ×4 GT),
  với `MBPP_OVERRIDE_PATH` trỏ tới subset 32 task. Code trích bằng `evalplus.sanitize.sanitize`
  với entry point chính thức.
- **Code do model sinh chỉ chạy trong Modal container `block_network=True`**, không chạy trên
  máy người dùng. GPU/máy sinh code không thấy canonical solution hay test input.

## 3. Bước 1 — Software preflight (không phải pass@1)

Gate **G0** PASS khi đồng thời:
1. 32/32 canonical solutions (`prompt + canonical_solution`) đạt `base_status = plus_status = pass`;
2. chạy lại lần 2 cho cùng status 32/32;
3. negative control (hàm trả `None`) **fail base** 32/32;
4. container chạy với `block_network=True`.

Fail ⇒ sửa harness, không sinh code.

## 4. Bước 2 — Pilot sinh code thật

- **Pool (5 model Ollama local, RTX 4050 6GB):** `qwen3:8b`, `gemma2:latest`, `llama3:8b`,
  `qwen3:0.6b` (đúng pool 4 model tuần 2) + `qwen3:4b-instruct-2507-q4_K_M`.
  `think=false` cho các model Qwen3 có thinking (tiền lệ repo).
- **Prompt:** instruction prefix chính thức của EvalPlus
  (`Please provide a self-contained Python script that solves the following problem in a markdown code block:`)
  + prompt MBPP+ trong code fence. Prompt gốc chứa 1 assert ví dụ (thuộc base tests) —
  visibility nhất quán cho mọi model, không gọi là hidden.
- **Stage greedy (PRIMARY, quyết định gate):** 32 task × 5 model × 1 mẫu, `temperature=0`,
  `seed=0`, `num_predict=1024` ⇒ **160 call**.
- **Stage sampled (MÔ TẢ, không đổi gate):** thêm 4 mẫu/ô, `temperature=0.8`, `seed=1..4`
  ⇒ **640 call**. Chỉ dùng ước lượng `P(F=0 | B=1, model)` với CI chặt hơn.
- Một request tối đa 2 lần thử khi lỗi transport. Response hợp lệ nhưng sai **không** retry.
  Bị cắt độ dài vẫn được chấm như output.

### Gate stage greedy (viết trước, trên 160 ô model×task)

| Gate | Định nghĩa | Ngưỡng |
|---|---|---|
| **G1** censoring regime | `FP = #(B=1, F=0)`; `FPR = FP / #(B=1)` | `FP ≥ 8` **và** `FPR ≥ 0.10` |
| **G2** headroom | `oracle = #task có ≥1 model F=1`; `best = max_model #F=1` | `oracle − best ≥ 3` |
| **G3** censoring ảnh hưởng quyết định | `D = #task có ≥2 model B=1 và bất đồng về F` | `D ≥ 3` |

**PASS = G0 ∧ G1 ∧ G2 ∧ G3.** Fail bất kỳ ⇒ **STOP**: không fit phương pháp, báo kết quả âm.

## 5. Bước 3 — So sánh ngang quyền (chỉ chạy nếu PASS)

Replay trên bank greedy, leave-one-task-out. Với task đích `t`: history = 31 task còn lại × 5
model. `B` thấy được trên mọi ô history và trên 5 output của `t` (basic tests chạy được lúc
triển khai). `F` chỉ lộ trên ô history được audit; ô `B=0` biết `F=0` miễn phí.
Budget audit = **số nhãn F được tiết lộ**: `k ∈ {16, 39}` (~10%, ~25% của 155 ô), 200 seed.

Audit policies: `Uniform` (mọi ô history), `CensoredUniform` (chỉ ô B=1),
`Disagreement` (ưu tiên ô B=1 ở task có ≥2 model B=1, uniform trong nhóm).

Selectors (chọn 1 output cho `t`; reward = `F` của output đó):
- `BestFixedB`: model có tỷ lệ B history cao nhất (bỏ qua B hiện tại);
- `RawB`: trong các model B=1 trên `t`, lấy tỷ lệ B history cao nhất; không có thì như BestFixedB;
- `GlobalRepF`: Beta(1,1) trên F đã biết (audit + B=0 suy ra), chọn trong B=1 của `t`;
- `CensoredRep` (**candidate**, ECRT-1 có điều kiện theo model): Beta(1,1) trên
  `P(F=1 | B=1, model)` từ ô B=1 đã audit, chọn trong B=1 của `t`;
- `ActionValue` (**control mạnh, cùng thông tin**): logistic regression
  (one-hot model, B hiện tại, tỷ lệ B history) trên ô có F đã biết, chọn argmax;
- tham chiếu không triển khai được: `Oracle`, `BestFixedF` (hindsight).

**Primary:** `CensoredRep` vs `RawB` và vs `ActionValue`, `k=16`, audit `CensoredUniform`.
Thành công khi hơn **cả hai** ≥ 1 task trung bình với CI bootstrap theo task (2.000 lần)
có cận dưới > 0. 32 task là development, **không** phải confirmation.

## 6. Không được claim

- Không claim "test pass chưa chắc đúng" hay test mở rộng là novelty (EvalPlus 2023).
- Không gọi 32 task là độc lập/không nhiễm pretraining; overlap MBPP200 archive chưa map.
- Không quy pass@1 ở đây thành năng lực tổng quát của model (32 task, quantized, 1 GPU laptop).
- Kết quả bước 3 trên 32 task là development; muốn claim cần confirmation trên task mới.
