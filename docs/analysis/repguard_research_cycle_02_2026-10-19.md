# Vòng 2: đối chiếu bằng chứng và tự sửa đủ compute

Ngày 19/10/2026. **72 phản hồi model thật mới trên 24 báo cáo development đã xem.** Đây là phép sàng cơ chế, chưa là test độc lập và chưa triển khai learner reputation.

## Kết quả

| Phương án | Đúng/24 | Rescue / harm so PoT | Calls/câu | Mean Ollama eval giây |
|---|---:|---:|---:|---:|
| Một agent PoT | 17 | 0 / 0 | 1 | 47.07 |
| PoT + tự sửa 1 lần | 17 | 0 / 0 | 2 | 76.48 |
| PoT + tự sửa 2 lần | 17 | 0 / 0 | 3 | 103.36 |
| PoT + DSL + tổng hợp | 16 | 0 / 1 | 3 | 87.22 |

Compose so self2: 0 rescue, 1 harm, net -1 câu. Paired bootstrap 95% của chênh lệch là [-12.50, 0.00] pp trên development này. Không dùng interval/p-value exploratory làm xác nhận superiority hay equivalence.

Oracle union các action=17/24; best fixed=17/24. Gate cố định=FAIL. Compose tạo 0 câu đúng khi cả hai output cha sai; 0 câu đúng mà cả hai vòng self-review sai. Oracle không là accuracy của thuật toán.

## Quyết định

Không fit thêm reputation controller trên pool này. Chưa đủ bằng chứng rằng phối hợp ở cấu hình hiện tại tạo đủ headroom để học chọn can thiệp. Giữ các output và kết quả âm; không thay threshold hoặc nhãn để cứu giả thuyết.

## Thiết kế, chi phí và phạm vi kết luận

Mọi nhánh mới cùng tài liệu, checklist metric/kỳ/scope/unit/sign, native thinking, cap4096, seed19102026 và executor. Self1 xem PoT; self2 xem self1 đã acceptance; compose xem PoT cùng DSL với source contexts. Invalid giữ current proposal theo rule cơ học, không dùng gold. Baseline PoT và DSL cha là các call thật vòng trước; dùng cache chỉ để tránh thu lại, vẫn charge vào chi phí phục vụ từng phương án.

Compose và self2 cùng3calls nhưng cap tổng lần lượt9728 và12288; không mặc nhận cùng compute thực tế. Mean Ollama eval tính prompt_eval_duration+eval_duration, loại model load: là proxy runtime, không phải hóa đơn hoặc latency live. Self1/direct là đối chứng ít calls hơn vẫn phải báo.

Đợt này có 72 calls mới, input 130,985, output 48,847 tokens; 72 phản hồi có native thinking, 0 dừng do cap. Không quality retry, không model mock. Final score giữ exact FinQA round5; không oracle ×100 và không sửa các nhãn nghi vấn.

Tất cả24report đã dùng development trước đó, cùng một backbone Qwen3:14b. Không suy ra generalization, SOTA, hiệu quả history hoặc lợi ích mọi hệ multi-agent. Gold chỉ dùng khi analyze sau collection; solver không nhận gold/reference program. Source/arithmetic pass không là xác nhận semantic đúng.

## Những câu thay đổi kết quả so PoT

| Case | Target chính thức | PoT | Self1 | Self2 | Compose |
|---|---:|---:|---:|---:|---:|
| FRT/2007/page_137.pdf-1 | 5908.0 | 5908 (đúng) | 5908 (đúng) | 5908 (đúng) | 6890 (sai) |

Các giá trị trên là đối chiếu với official target, không adjudication ngữ nghĩa. Phiếu audit độc lập đã chuẩn bị nhưng chưa có người nộp annotation.

## Forensics từ các can thiệp thật

**FRT:** PoT dùng83,656→89,564 cho2005→2006, chênh5,908. Alternative DSL
gán89,564→96,454 cho hai năm đó; source references có tồn tại nhưng context
cell không giữ rõ block năm. Compose chuyển sang đúng cặp số của alternative,
ra6,890. Arithmetic vẫn đúng với cặp số đã chọn, lỗi nằm ở binding số–kỳ.
Đây là một harmful correction quan sát được, không phải lỗi formatter.
Không suy từ một case ra cơ chế attention hay tần suất lỗi trên toàn corpus.

**EW:** nguồn có0.6triệu năm2017 và4.1triệu năm2016; current PoT chọn4.1,
alternative chọn0.6. Compose chọn0.6, không tổng hợp hai khoản. Self1/self2 giữ
4.1. Official program cộng4.7rồi chia22.7. Vì câu hỏi không nói rõ năm, cần
audit cách hiểu scope; giữ nguyên official score. Cho phép tạo chương trình
mới chưa bảo đảm model thực hiện phép kết hợp cần thiết. Chưa có evidence
rằng thêm claim credit tự động sẽ giải quyết được việc này.

**WRK:** hai self-review mới đều abstain và giải thích rằng bảng là
"valuation allowances against deferred tax assets", khác metric deferred tax
assets trong câu hỏi. Fallback cơ học giữ output cũ, vì vậy official accuracy
không đổi. Đã lưu semantic flag riêng để hai người kiểm, chưa relabel. Điều
này cho thấy phải tách arithmetic/execution, khớp target và đúng nghĩa metric.

Toàn bộ72responses đều có native thinking và không response nào dừng do cap.
Do đó không quy zero-rescue của vòng này cho truncation đã quan sát; cũng
không chứng minh một cap/model/scaffold khác sẽ cho cùng kết quả.

## Artefacts

- Protocol và source snapshots: `results/thesis_composition_cycle_02/plan.json`, `registration.json`, `frozen_source.zip`.
- Raw receipts72, summary, traces_private trong cùng thư mục run.
- `verify_composition_cycle02.py` kiểm lại hash, prompts, canonical execution, acceptance/fallback, cost/outcomes và gate; không gọi model.
- `repguard_research_gap_2026-10-19.md` định vị với MoCA/CLAIR-Fin/MERIT/C3/GCJR và các routing/reputation controls.
- TAT-QA source inventory64 TRAIN contexts đã pin nguồn/metric, **chưa có inference hoặc điểm TAT-QA**. Không gọi context UID là report-disjoint.
