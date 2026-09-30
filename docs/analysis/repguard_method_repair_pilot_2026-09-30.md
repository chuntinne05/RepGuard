# RepGuard: sửa thuật toán, đối chứng audit công bằng và pilot poisoning có mục tiêu

**Ngày:** 30/09/2026. **Trạng thái:** các replay trên ledger Week 3/420 câu đã chạy xong; bốn policy direct đã đủ 560 development ID mới, policy thinking còn đang chạy với watchdog. Mọi kết quả replay dùng test Week 3 hoặc pool 420 đã được xem trước đây, nên là **phát triển**, không phải xác nhận trên holdout. Sealed holdout 420 ID chưa chạy.

## 1. Việc đã thực hiện và ranh giới dữ liệu

- Giữ nguyên đường tính ECRT lịch sử để các con số Week 3 có thể tái lập. Sửa hai vấn đề QA: `oracle_ft` yêu cầu một oracle transfer estimator được cung cấp rõ, không dùng metadata taxonomy dưới nhãn oracle; `uncertainty_mode` có `decision_weight` rõ ràng để chọn mean/lower bound. `tests/test_ecrt.py` kiểm tra các trường hợp này.
- Tạo `AuditedECRTReputation` thử nghiệm: chỉ đọc gold trên tập audit được cấp công khai, tách kênh feedback theo agent × môn nguồn; dùng Jeffreys smoothing cho sensitivity/specificity/prior; Wilson lower bound của `sensitivity + specificity − 1` quyết định có dùng history hay không. Khi kênh không đủ tín hiệu, history được bỏ và audit gold vẫn làm evidence. Đây là **heuristic bảo thủ**, không phải posterior đúng hoàn toàn hoặc chứng nhận risk. Test kiểm tra kênh khác nhau khi chỉ một agent bị false positive và fallback khi feedback vô ích.
- Mọi đối chứng audit-aware được cấp cùng 50 câu gold calibration/môn nguồn/agent, khác ID với history và test: `AuditOnly`, `FixedPlusAudit`, `CalibratedPlusAudit`, `GuardedCalibratedPlusAudit`, `AuditedECRT`. Điều này sửa bất công thông tin của so sánh ECRT cũ với FixedBorrow: ECRT cũ dùng gold calibration để học channel còn FixedBorrow không dùng gold đó làm năng lực.
- Suy luận mới `run_real_dev_pool.py` chỉ dùng 560 development ID từ `frozen_splits.json`, 40/môn. Manifest mới SHA-256 `c3c50fdb9a95bcc2de290c37283585036ec490a0dcb0b7731f17173c77b8ec67`. Năm policy khóa trước khi chấm: Qwen3 8B direct, Qwen3 14B direct, Gemma2 direct, Qwen3 0.6B direct, Qwen3 8B thinking. Prompt/JSON schema/model digest được lưu; 420 holdout ID không nằm trong manifest suy luận.

## 2. Same-audit-budget replay trên Week 3 thật

Các số sau là team accuracy trung bình theo **target subject** ở nhóm `related`. Qwen3/Gemma/Llama/Qwen0.6 vẫn là bốn agent direct của Week 3. Chỉ feedback lịch sử bị corrupt; model answer đều là output thật.

| Feedback | FixedBorrow, không dùng audit gold | ECRT cũ | AuditOnly | Fixed + audit | AuditedECRT theo agent |
|---|---:|---:|---:|---:|---:|
| Oracle | 49,67% | 49,75% | 49,19% | 49,72% | 49,74% |
| Flip 25% | 49,28% | 49,29% | 49,19% | **49,49%** | 49,24% |
| Flip 50% | 47,74% | 48,16% | **49,19%** | 48,55% | **49,19%** |
| False positive 40% trên mọi agent sai | 49,56% | 49,55% | 49,19% | **49,49%** | 49,41% |

Ở 50% noise, guard không dùng history trong toàn bộ lần hiệu chuẩn kiểm tra, nên `AuditedECRT = AuditOnly` đúng theo thiết kế. So ECRT cũ, AuditOnly cao hơn **+1,04 điểm** (CI bootstrap theo target **[+0,23; +1,93] điểm**) trong dữ liệu đã xem. Nhưng ở 25% noise, `AuditedECRT − FixedPlusAudit = −0,25 điểm`, CI **[−0,76; +0,17]**, và Brier cũng xấu hơn. Vì vậy guard là sửa lỗi cho vùng feedback gần vô ích, **chưa phải cải thiện clean/noisy phổ quát**. Không nên tune ngưỡng guard trên chính test cũ.

## 3. Attack nhắm riêng một agent trên đáp án thật

`analyze_targeted_attack_replay.py` giữ nguyên output model thật, chỉ tạo feedback false positive trên **40% câu sai** của một agent được chọn, ở history và calibration. Audit gold vẫn độc lập với feedback. Với target `related`, n=13 môn, trung bình source và ba seed trong từng target trước bootstrap:

| Agent bị attack | Phương pháp | Clean | Attack | Thay đổi attack − clean |
|---|---|---:|---:|---:|
| Qwen3 0.6B, agent yếu | ECRT cũ | 49,75% | 45,72% | **−4,04 điểm**, CI [−5,43; −2,65] |
| Qwen3 0.6B | Fixed + audit | 49,72% | 48,23% | −1,49 điểm |
| Qwen3 0.6B | AuditedECRT | 49,74% | **49,74%** | 0,00 điểm |
| Qwen3 8B, agent mạnh | ECRT cũ | 49,75% | 49,65% | −0,11 điểm, CI chứa 0 |
| Qwen3 8B | AuditedECRT | 49,74% | 49,61% | −0,13 điểm, CI chứa 0 |

Trong điều kiện attack agent yếu, `AuditedECRT − ECRT cũ = +4,02 điểm`, CI bootstrap **[+2,54; +5,55]**; so `FixedPlusAudit`, **+1,51 điểm**, CI **[+0,57; +2,59]**. Đây là **cơ chế phòng poisoning có tiềm năng**, nhưng là corruption feedback bằng quy tắc trên Week 3 test đã xem; không phải attacker sinh câu trả lời mới, không chứng minh chống mọi agent, mọi attack hoặc hiệu quả clean tốt hơn. Attack vào agent mạnh thậm chí có thể tăng vote cho solver mạnh, nên effect phụ thuộc năng lực attacker.

Đối chứng `AuditOnly` vẫn rất mạnh: dưới attack agent yếu, `AuditedECRT − AuditOnly` ở `related` chỉ **+0,55 điểm**, CI **[−0,04; +1,27]**, còn ở `same` AuditedECRT **kém 0,64 điểm**, CI **[−1,08; −0,22]**. Do đó replay chưa chứng minh phần feedback history của phương pháp mới đem thêm lợi ích so chỉ dùng gold audit.

## 4. Selector theo câu trên pool thinking thật

Một ridge selector cố định (`λ=10`) dùng subject, độ dài câu/đáp án, độ dài output thinking và dấu hiệu số; chỉ học target rescue/harm từ bốn fold khác trong pool 420 đã xem. Nó chỉ chọn giữa Qwen3 8B thinking và Qwen3 14B direct **sau khi cả hai đã trả lời**, nên phải tính chi phí gọi cả hai trên tất cả 420 câu.

| Policy | Đúng/420 | Chi phí gọi Qwen14 bổ sung |
|---|---:|---|
| Luôn thinking | 280 | 0 |
| Qwen14 chỉ khi thinking invalid | 286 | 24 call |
| Selector theo câu 5-fold | 287 | **420 call** |

Selector đổi 45 đáp án, cứu 12 và hại 5 so always-thinking. Phần hơn fallback invalid chỉ **1 câu** trong khi phải gọi Qwen14 trên toàn bộ 420 câu (2.940 output token, 554,76 s thời gian request cộng dồn). Vì vậy **không qua gate hiệu quả chi phí** trên pool đã xem; không tìm thêm threshold để tối ưu riêng tập này. `evaluate_fresh_dev_selector.py` đã cố định cùng feature, penalty và ngưỡng trước khi chấm development mới.

## 5. Pilot Modal và phép đánh giá đã khóa

Endpoint Modal `ollama-server` đã deploy và scale-to-zero khi không có request; sau khi đánh thức, `/api/version` trả 0.34.4 và `/api/tags` có đủ model. Pilot direct 1 câu/môn × 4 model = **56/56 output hợp lệ**. Pilot thinking **14/14 request đã ghi**, có hai ca invalid do chạm trần 8.192 token và được giữ sai khi chấm sau này. Runner append-only/resumable, có prompt hash, protocol hash, model digest, raw answer và token/latency; `analyze_real_dev_pool.py` kiểm lại từng row. Không chấm accuracy khi một variant chưa đủ 560 câu.

Hai phép đánh giá mới đã viết trước khi xem outcome development: (1) selector cũ train trên 420, test trên 560 mới, tính đầy đủ chi phí gọi thêm Qwen14; (2) `AuditedECRT` so với ECRT, FixedBorrow, AuditOnly và FixedPlusAudit trên đội ba direct model chung với history cũ, dưới clean và attack Qwen0.6B. Mỗi phép yêu cầu đủ các variant liên quan và báo CI ghép cặp theo target; development mới vẫn **không phải sealed holdout cuối**.

Một router bổ sung `evaluate_fresh_dev_router.py` cũng đã được cố định **trước khi có đủ output thinking 560**: ridge λ=10 huấn luyện trên toàn bộ 420 câu cũ, cùng feature nhìn thấy sau Qwen8 thinking nhưng *trước* Qwen14; gọi Qwen14 nếu estimated accuracy delta >0 hoặc thinking invalid. Đây là policy triển khai được theo chi phí có điều kiện, khác selector cũ cần biết hai output có bất đồng. Replay 5-fold trên pool cũ đã xem: thinking **280/420**, fallback invalid **286/420 với 24 call Qwen14**, router **285/420 với 104 call**, 16 rescue và 11 harm; chi phí Qwen14 router 728 output token/117,35 s request so 2.940 token/554,76 s nếu gọi toàn bộ. **Replay không qua gate so fallback**; kết quả 560 mới vẫn được chấm theo code đã khóa để biết có replication hay không. Không mở holdout để tối ưu threshold.

**Gate phát triển được ghi trước kết quả 560:** với poisoning agent yếu ở cặp môn `related`, cả `AuditedECRT − FixedPlusAudit` **và** `AuditedECRT − AuditOnly` phải có CI bootstrap theo target nằm trên 0; đồng thời `AuditedECRT − FixedPlusAudit` ở clean không được thấp hơn 1 điểm accuracy quan sát. Đây là tiêu chí chọn xem có đáng chuẩn bị một phép xác nhận holdout hay không, **không phải kiểm định paper cuối**. Với selector, phần gain so fallback invalid phải ít nhất 2 điểm accuracy quan sát để biện minh việc gọi Qwen14 trên mọi câu; nếu không thì chỉ giữ fallback như baseline vận hành. Các ngưỡng này là quyết định quản trị compute, không phải bảo đảm thống kê.

## 6. Quyết định nghiên cứu hiện tại

### Kết quả mới trên 560 development ID (đã chấm sau khi khóa phương pháp)

`analyze_real_dev_pool.py` kiểm tra 2.240/2.240 output direct: 0 invalid và không có dòng lỗi. Năng lực trực tiếp trên 560 câu: Qwen3 8B **277**, Qwen3 14B **297**, Gemma2 **236**, Qwen3 0.6B **123** câu đúng. Qwen3 8B thinking mới đang chạy; không dùng 14 pilot để suy ra accuracy.

Phép `evaluate_fresh_dev_audit.py` dùng đội ba direct agent có history cũ (Qwen8, Gemma2, Qwen0.6). So trên **cùng 13 môn mục tiêu × 40 câu = 520 câu**. Đơn vị bootstrap là môn mục tiêu; source và ba attack seed được trung bình trong môn trước. Attack tiếp tục chỉ làm giả feedback của Qwen0.6B trên output lịch sử thật.

| Phương pháp | Related clean | Related targeted attack |
|---|---:|---:|
| ECRT cũ | 46,25% | 39,78% |
| Fixed + cùng gold audit | 46,06% | 43,07% |
| AuditOnly | 45,03% | 45,03% |
| AuditedECRT theo agent | 45,67% | **45,67%** |
| **Qwen3 14B direct đơn lẻ** | **53,08%** | **53,08%** |

ECRT cũ giảm **6,47 điểm** khi bị targeted feedback attack, CI bootstrap **[−8,79; −4,24]**; AuditedECRT không đổi. Dưới attack, AuditedECRT hơn Fixed+Audit **2,61 điểm**, CI **[+0,44; +4,92]**, nhưng chỉ hơn AuditOnly **0,64 điểm**, CI **[−0,32; +1,73]**. So Qwen14 đơn lẻ, AuditedECRT kém **7,40 điểm**, CI **[−11,06; −3,94]**. Đây là replication thực trên target ID mới của cơ chế *phòng attack so ECRT cũ*, đồng thời là bằng chứng **không đạt** mục tiêu phương pháp team accuracy trên pool này. Dữ liệu vẫn là development và attack feedback theo quy tắc; chưa kiểm chứng trên holdout/external benchmark.

So sánh Qwen14 đơn lẻ được thêm vào bảng phân tích **sau khi direct ledger đã đủ**, như một baseline mô tả. Yêu cầu đối chiếu với solver đơn mạnh nhất đã có trong kế hoạch nghiên cứu trước đó, nhưng hàng và CI này không thuộc hai phép so primary của gate đã khóa ngay trước lượt development; không dùng nó để điều chỉnh phương pháp.

Trong toàn bộ 560 request development, Qwen14 direct dùng **3.926 output token** và **650,73 s** thời gian request cộng dồn; ba thành phần direct của team dùng tổng **14.958 output token** và **1.468,18 s**. Đây là chi phí đo trên Modal T4 với warm-up/server state có thể khác nhau, không phải USD; nhưng team hiện cũng không có lợi thế chi phí quan sát để bù cho accuracy thấp hơn.

**Quyết định Gate audit trên development: STOP.** Điều kiện đã khóa yêu cầu hơn cả Fixed+Audit lẫn AuditOnly dưới attack; CI so AuditOnly chứa 0. Baseline solver đơn còn mạnh hơn rõ. Không mở sealed holdout để tiếp tục tìm biến thể vote/threshold trên pool này. Nhánh **selector theo câu trên pool MMLU-Pro generalist** cũng chưa có lợi ích đủ lớn trong replay 420 để trả chi phí gọi thêm model; vẫn chờ phép đánh giá thinking trên 560 ID đã khóa. Nếu selector cũng không qua gate, chuyển trọng tâm sang môi trường agent tương tác hoặc HistRepEval, thay vì tiếp tục thay ngưỡng trên MMLU-Pro.

**Tự động hoàn tất:** `run_real_dev_pipeline.py` đang giữ collector thinking, kiểm tra ledger tăng, tái chạy khi lỗi transient rồi chấm selector và audit khi đủ 2.800 lượt; `run_post_dev_analysis.py` đợi trạng thái `pipeline_complete`, sau đó chấm router mới và chạy lại audit theo mã mới nhất để ghi baseline Qwen14 mô tả. Cả hai có status JSON riêng trong `results/real_dev_pool_v1/`. Một process còn tồn tại không được xem là bằng chứng progress; ledger và log Modal cần được kiểm tra theo thời gian. AppWorld smoke task 3 bước đã dừng vì tranh GPU, không có task success score.

**Tái lập:** `.venv/bin/python analyze_audit_budget_replay.py`, `.venv/bin/python analyze_targeted_attack_replay.py`, `.venv/bin/python analyze_contextual_selector.py`. Các JSON đầu ra trong `results/` bị Git ignore; mọi bảng trên lấy từ ledger real Week 3 hoặc pool 420 và các script này. Test hiện tại: **202/202** suite qua, gồm core audited ECRT và protocol runner mới.
