# RepGuard — hoàn tất pool development 560 câu, selector/audit gate và AppWorld smoke

**Chốt dữ liệu chính:** 01/10/2026 15:44 giờ Việt Nam. **Trạng thái:** MMLU-Pro development 2.800/2.800, các phép chấm đã khóa và hậu kiểm hoàn tất. Diagnostic context 8K và AppWorld pilot v2 là nghiên cứu tiếp theo riêng, không nằm trong các con số đã chốt dưới đây.

## Kết luận điều hành

1. **Model capability:** Trên 560 câu development mới, Qwen3 8B thinking đúng **372/560 = 66,43%**, so với Qwen3 8B direct **277/560 = 49,46%**. Chênh ghép cặp **+16,96 điểm phần trăm**, CI bootstrap phân tầng câu trong môn 95% **[+12,86; +21,07]**. Nhưng thinking dùng **1.264.210 output token**, khoảng **231 lần** direct Qwen8, và có **40/560 output invalid**, tất cả chạm cap 8.192 token. Đây là so hai *policy/budget*, không cô lập cờ `think`.
2. **Fallback thực dụng:** Chỉ gọi Qwen3 14B direct khi thinking invalid cứu **16/40** câu; kết quả **388/560 = 69,29%**, hơn always-thinking **+2,86 điểm** với CI ghép cặp phân tầng câu **[+1,61; +4,29]**. Nó thêm **40 lời gọi Qwen14**, 280 output token và 43,90 giây thời gian request cộng dồn đo trên cùng ledger. Đây là baseline xử lý lỗi trên development, chưa phải đóng góp thuật toán DART.
3. **Selector tốn chi phí không qua gate:** Selector dùng đáp án của cả thinking và Qwen14 trước khi chọn đạt **396/560 = 70,71%**, hơn fallback **8 câu = +1,43 điểm**, CI **[0; +2,86]**. Gate đã khóa yêu cầu ít nhất **+12 câu** để biện minh gọi Qwen14 trên *mọi* câu; kết quả chỉ +8. Selector cần **560** lời gọi Qwen14, so 40 của fallback.
4. **Router trước khi gọi Qwen14 không đem thêm độ đúng:** Router học trên pool 420 câu cũ, chỉ dùng feature nhìn thấy sau thinking và trước lời gọi Qwen14, đạt **388/560**, bằng fallback; nó gọi Qwen14 **172 lần**, hơn fallback 132 lời gọi. CI chênh router−fallback **[−2,14; +1,96] điểm**. Không có bằng chứng decision gain hay lợi ích chi phí.
5. **Audit/reputation gate STOP:** Trên 520 câu development thuộc 13 target môn ở study audit, `AuditedECRT` giữ **45,67%** khi feedback của agent yếu bị poisoning, trong khi ECRT cũ giảm từ **46,25% clean xuống 39,78% attacked**. Nhưng `AuditedECRT` chỉ hơn `AuditOnly` **+0,64 điểm** dưới attack, CI theo target **[−0,32; +1,73]**; Qwen3 14B direct đơn lẻ đạt **53,08%**. Điều kiện gate yêu cầu thắng cả FixedPlusAudit và AuditOnly dưới attack, nên **không đạt**. Không mở sealed holdout 420 câu để chỉnh tiếp vote/threshold trên pool này.
6. **AppWorld smoke thật chưa tạo năng lực:** Qwen3 14B direct chạy **ba task train**, mỗi task 16 bước trong custom local ReAct scaffold; official state-check cho **0/3 task success**. Hai task sa vào vòng lặp tra tài liệu API, task còn lại có lỗi thực thi/đăng nhập; cả ba không gọi `complete_task`. Đây là chẩn đoán **model + scaffold + step cap** trên ba task, không phải bằng chứng AppWorld không phù hợp hoặc điểm official baseline. Một protocol v2 trên ba train task khác đã được khóa trước khi chạy.

## 1. Dữ liệu, provenance và ranh giới suy luận

- `results/real_dev_pool_v1/status.json` ghi `pipeline_complete` lúc **08:44:08 UTC / 15:44:08 Việt Nam** ngày 01/10/2026. Bốn variant direct và một variant thinking đều **560/560**, tổng **2.800/2.800**. SHA-256 raw ledger: `f2cdaa92a28deea6cc7e4e781bc31df2982ca1f67d0ac0cd1e0b978f8da93f70`.
- Protocol hash: `c3c50fdb9a95bcc2de290c37283585036ec490a0dcb0b7731f17173c77b8ec67`. Tập development là 40 ID/môn × 14 môn, lấy từ phần train/calibration MMLU-Pro chưa dùng của study trước. Cùng task ID cho cả năm policy. **420 sealed holdout ID chưa suy luận hay chấm outcome**.
- `analyze_real_dev_pool.py` kiểm tra manifest, model digest, task ID, prompt hash, trùng lặp và tính đầy đủ trước khi ghi `analysis.json`. `run_real_dev_pipeline.py` tự chấm selector/audit sau khi đủ ledger. `run_post_dev_analysis.py` chạy router và đối chiếu audit; `post_analysis_status.json` là `post_analysis_complete` với cùng ledger hash.
- App Ollama Modal cũ bị người dùng dừng ở dashboard ngày 30/09. App mới `ollama-server-repguard-recovery` được deploy từ `infra/modal/ollama_modal_recovery.py`, dùng cùng volume model và T4. Preflight sau deploy trả Ollama **0.34.4**, cùng model digests và protocol hash như manifest đã khóa. Ledger nối append-only từ 2.616, không chạy lại các ID đã hoàn tất. Modal preempt container một lần trong quá trình phục hồi; watchdog retry từ ID chưa ghi và raw ledger vẫn đủ. Vì hạ tầng có preemption/warmup, tổng request time **không** phải thời gian wall-clock hoặc USD.

## 2. Capability và chi phí trên đúng 560 câu

| Policy | Đúng/560 | Accuracy | Invalid | Output token | Tổng request time (giây) |
|---|---:|---:|---:|---:|---:|
| Qwen3 8B direct | 277 | 49,46% | 0 | 5.474 | 559,76 |
| Qwen3 14B direct | 297 | 53,04% | 0 | 3.926 | 650,73 |
| Gemma2 direct | 236 | 42,14% | 0 | 3.920 | 602,59 |
| Qwen3 0.6B direct | 123 | 21,96% | 0 | 5.564 | 305,83 |
| Qwen3 8B thinking | **372** | **66,43%** | **40** | **1.264.210** | **35.381,48** |

Trên cặp Qwen8 cùng 560 ID, thinking đúng riêng 131 câu, direct đúng riêng 36, cùng đúng 241, cùng sai 152. 40 output invalid đều có `done_reason=length` và `output_tokens=8192`; không xóa chúng khỏi mẫu. Token và request time là số đo của policy khác ngân sách; 1.264.210/5.474 ≈ **231 lần output token**, 35.381,48/559,76 ≈ **63 lần tổng thời gian request**. Chi phí tiền và wall-clock phụ thuộc hạ tầng, chưa suy ra từ hai tỷ lệ này. File tái tạo: `analyze_real_dev_capability.py` → `results/real_dev_pool_v1/capability_analysis.json`.

## 3. Bảng quyết định ở cùng 560 câu

| Policy | Đúng/560 | Accuracy | Lời gọi Qwen14 bổ sung | So với fallback invalid |
|---|---:|---:|---:|---|
| Always Qwen8 thinking | 372 | 66,43% | 0 | −16 câu |
| Qwen14 chỉ khi thinking invalid | **388** | **69,29%** | **40** | Baseline thực dụng |
| Router sau thinking, trước Qwen14 | 388 | 69,29% | 172 | 0 câu; CI [−2,14; +1,96] điểm |
| Selector sau khi có cả hai output | 396 | 70,71% | 560 | +8 câu; CI [0; +2,86] điểm |
| Always Qwen14 direct | 297 | 53,04% | 560 nếu là solver bổ sung | Thấp hơn fallback 91 câu |

Selector chuyển đáp án 74 câu, cứu 29 và hại 5 so always-thinking. Trong đó fallback invalid đã cứu 16 câu với 40 call; phần tăng thêm của selector là **8 câu với 520 lời gọi Qwen14 thêm**. Router cứu 33, hại 17 so always-thinking; phần vượt fallback bằng **0**. Cả hai đều không chứng minh được một policy chọn agent có giá trị tăng thêm so quy tắc xử lý invalid đơn giản ở ngân sách hiện tại. Selector dùng Qwen14 trên mọi câu để biết hai output có bất đồng, vì vậy không được mô tả là router tiết kiệm lời gọi.

Các policy selector/router đã cố định từ 420 câu phát triển cũ *trước khi* xem 560 outcome; 560 là một phép kiểm tra development mới, nhưng **không phải sealed holdout cuối**. CI bootstrap phân tầng câu trong 14 môn; nếu suy rộng sang các môn/benchmark khác, cần dữ liệu và phép kiểm định ngoài. Source: `results/real_dev_pool_v1/selector_evaluation.json`, `selective_router_evaluation.json`.

## 4. Audit, poisoning và giới hạn claim

Study audit dùng ba direct agent có history tương ứng: Qwen3 8B, Gemma2, Qwen3 0.6B. Đối chứng audit-aware đều nhận cùng 50 gold calibration ID/môn nguồn/agent, không trùng history/test. Targeted intervention đổi feedback trên 40% câu sai của Qwen3 0.6B; câu trả lời model vẫn là output thật. Đây là **can thiệp feedback được tạo có kiểm soát**, chưa phải attacker tự phát trong AppWorld.

| Method, target related | Clean | Targeted attack |
|---|---:|---:|
| ECRT cũ | 46,25% | 39,78% |
| FixedPlusAudit | 46,06% | 43,07% |
| AuditOnly | 45,03% | 45,03% |
| AuditedECRT | 45,67% | 45,67% |
| Qwen3 14B direct đơn lẻ | **53,08%** | **53,08%** |

Under attack, `AuditedECRT−FixedPlusAudit` là **+2,61 điểm**, CI target-cluster **[+0,44; +4,91]**. Nhưng `AuditedECRT−AuditOnly` là **+0,64 điểm**, CI **[−0,32; +1,73]**, nên không chứng minh được sử dụng history đem thêm giá trị so chỉ dựa vào gold audit. So Qwen14 single, team vẫn kém **7,40 điểm**, CI **[−11,06; −3,94]**. `audit_gate=false` trong status là quyết định đúng theo protocol đã khóa, không phải lỗi pipeline.

## 5. Hướng nghiên cứu sau hai gate STOP

**MMLU-Pro generalist pool:** Không tiếp tục chỉnh trọng số biểu quyết/threshold trên 560 development hoặc mở 420 sealed holdout để săn cell thuận lợi. Có thể dùng fallback invalid như baseline vận hành, còn claim thuật toán mới cần vượt nó ở chi phí công bằng trên một pool thực sự bổ trợ. Diagnostic 8K đang chạy trên 70 ID development chọn trước để hiểu lỗi độ dài, không thay run chính.

**AppWorld:** V1 0/3 có nguyên nhân scaffold rõ ràng, nên chạy protocol v2 trên ba train task khác với 40 bước, chat history ngắn và chống lặp doc (`histrepeval_appworld_v2_protocol_2026-10-01.md`). Chỉ khi có task success và nhiều policy tạo lỗi bổ trợ, mới làm paired train pilot, feedback history/audit và dev gate. Nếu vẫn 0/3, cần thử scaffold baseline chính thức tương thích hoặc solver mạnh hơn trước khi tốn compute cho phương pháp.

**HistRepEval:** Gắn mỗi claim với final-decision value, feedback provenance, audit budget, chi phí và confidence interval; đóng gói manifest/ID/script/checksum và benchmark card. MMLU-Pro chỉ hỗ trợ claim về ensemble/routing trắc nghiệm; claim hệ agent tương tác cần AppWorld hoặc môi trường khác. Raw AppWorld task-derived content giữ trong `results/` do điều kiện phát hành; không đẩy lên Git công khai. Một bài mức A\* vẫn cần novelty so routing/trust/audit công bố, external replication, và kết quả vượt baseline mạnh. Không có bằng chứng hiện tại để bảo đảm acceptance.
