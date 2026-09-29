# RepGuard Week 4 — báo cáo pilot thinking thật trên MMLU-Pro

**Ngày:** 29/09/2026. **Trạng thái:** pilot 70 cặp hoàn tất; screen 420 cặp trên cùng manifest đang chạy. Đây là báo cáo capability/protocol, **không** phải bằng chứng ECRT thắng baseline.

## Câu hỏi và thiết kế

Liệu cùng Qwen3 8B trên Modal/Ollama, bật thinking có cải thiện đáp án MMLU-Pro so với direct answer, và cần bao nhiêu compute? Lấy **5 câu/môn × 14 môn = 70 câu** từ train/calibration chưa nằm trong 100 câu history/môn của Week 3. Hash split seed 42, selection seed 314159, chọn task ID trước khi đọc nhãn. Hai arm trả lời **cùng 70 câu**, cùng prompt direct và JSON schema enum, temperature 0, top_p 1, cùng model digest. A: `think=false`, `num_predict=64`; B: `think=true`, `num_predict=8192`. Đáp án chỉ lấy từ `message.content`; `message.thinking` chỉ ghi metadata hiện diện/độ dài, không ghép vào đáp án và không lưu nguyên reasoning trace. Câu không trả JSON hợp lệ hoặc bị cắt được tính là sai.

Modal/Ollama trả phiên bản `0.34.4`, Qwen3 digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`, `/api/show` công bố capability `thinking`. Manifest giữ `protocol_hash=74f421ecab1f1d2cc83ecd44320c3b56612ffd7f3b0d3b6a4d73e5b63a8cff78`. Verifier offline đã kiểm tra 140 prediction không trùng, đúng task/split, prompt hash, model digest, arm và token limit. Nhãn chỉ được đọc offline khi chấm.

Hai thử nghiệm kỹ thuật trước v3 trên **cùng một câu biology khó** dùng trần 1.024 và 4.096 token đều bị cắt trước đáp án. Chúng nằm ở ledger v1/v2 riêng và **không** tính vào 70 cặp này. Ở v3, trần 8.192 vẫn cắt 5 câu; đó là kết quả của protocol, không được tự động retry với trần lớn hơn rồi thay đáp án.

## Kết quả ghép cặp

| Chỉ số | Direct | Thinking |
|---|---:|---:|
| Đúng / tổng | 28/70 | 41/70 |
| Accuracy | 40,00% | 58,57% |
| JSON không hợp lệ / không có đáp án | 0/70 | 5/70 |
| Bị cắt ở token limit | 0/70 | 5/70 |
| Response có `message.thinking` | 0/70 | 70/70 |
| Tổng output tokens | 679 | 179.031 |
| Median output tokens | 10 | 1.793,5 |
| p95 output tokens | 10 | 8.192 |
| Tổng thời gian request | 78,84 giây | 4.908,31 giây |
| Median latency/request | 1,07 giây | 48,93 giây |
| p95 latency/request | 1,71 giây | 226,51 giây |

Thinking đúng khi direct sai ở **17** câu; direct đúng khi thinking sai ở **4** câu; chênh ròng **+13/70 = +18,57 điểm phần trăm**. Khoảng bootstrap 95% ghép cặp, lấy mẫu lại câu trong từng môn: **[+7,14; +30,00] điểm phần trăm**. Kiểm định McNemar exact hai phía trên 21 cặp bất đồng: **p=0,0072**. Đây là phân tích **thăm dò trên tập train dùng chọn cấu hình**, không phải xác nhận độc lập hoặc p-value cho claim bài báo. Cỡ mẫu 5/môn không đủ khẳng định model nào là specialist ở từng môn.

| Môn | Direct đúng / 5 | Thinking đúng / 5 | Thinking bị cắt / 5 |
|---|---:|---:|---:|
| Biology | 3 | 4 | 0 |
| Business | 1 | 2 | 0 |
| Chemistry | 4 | 4 | 1 |
| Computer science | 1 | 4 | 1 |
| Economics | 4 | 4 | 0 |
| Engineering | 2 | 3 | 1 |
| Health | 2 | 2 | 0 |
| History | 2 | 3 | 0 |
| Law | 0 | 1 | 0 |
| Math | 0 | 2 | 0 |
| Other | 1 | 2 | 1 |
| Philosophy | 2 | 4 | 0 |
| Physics | 3 | 3 | 1 |
| Psychology | 3 | 3 | 0 |

**Đánh đổi compute:** tổng thời gian request thinking gấp khoảng **62,3 lần** direct trên mẫu này. Đây là thời gian phía client; không đồng nhất với GPU billable time hoặc USD Modal. Tỷ lệ cắt **7,14%** làm thinking-on chưa phải một agent production ổn định. Nhiều câu cần 100–227 giây; dùng median riêng để dự toán sẽ quá thấp.

## Quyết định sau pilot và giới hạn claim

**GO để mở screen capability 420 cặp trên tập train đã chọn trước**, vì tín hiệu gain accuracy tồn tại ngay cả khi 5 câu bị cắt được tính sai. Screen dùng cùng manifest, digest, prompt, schema và token limit; 70 cặp pilot là một phần trong 420, **không** được xem là tập xác nhận độc lập. Theo mean latency pilot, 350 cặp còn lại dự kiến khoảng 6,9 giờ thời gian request nếu tốc độ tương tự, chưa tính gián đoạn/cold start. Runner đã bắt đầu từ 140 response có sẵn và ghi append-only; ngày giờ/đếm cuối sẽ được cập nhật khi xong.

**NO-GO hiện tại cho claim ECRT đã được cứu hoặc HistRepEval đã thành benchmark mạnh.** Pilot chỉ chứng minh một biến thể Qwen3 thinking có tín hiệu capability trên 70 câu train, với chi phí lớn. Bước kế tiếp là kiểm tra gain/validity trên 420 câu, đánh giá tính bổ sung so Qwen direct và các model khác cùng câu, thiết kế router hoặc cascade theo câu có ngân sách, rồi xác nhận trên dev chưa dùng. Chỉ khi pool và baseline cùng compute rõ ràng mới thử ECRT/feedback/audit trên tập mới và quyết định GO/NO-GO phương pháp. Cần benchmark thứ hai nếu muốn claim tổng quát.

## Artefact và lệnh tái lập phân tích

- `results/real_week4_thinking_pilot_v3/manifest.json`: 420 task ID train đã khóa và toàn bộ protocol.
- `results/real_week4_thinking_pilot_v3/pilot_70_predictions.jsonl`: 140 response đầu tiên, snapshot bất biến cho báo cáo này, SHA-256 `e0d15533ba01cdc90e0d3207c94286f74a7dee19944f7939902aa4ce77ef71d7`.
- `results/real_week4_thinking_pilot_v3/summary_70_pairs.json`: bảng chấm offline machine-readable.
- `run_real_week4_thinking.py`, `analyze_real_week4_thinking.py`: runner thật, resume và verifier/chấm offline.

Chạy lại phân tích từ snapshot với cache MMLU-Pro gốc trong `data/`:

```bash
.venv/bin/python analyze_real_week4_thinking.py \
  --output results/real_week4_thinking_pilot_v3 \
  --predictions-file results/real_week4_thinking_pilot_v3/pilot_70_predictions.jsonl
```
