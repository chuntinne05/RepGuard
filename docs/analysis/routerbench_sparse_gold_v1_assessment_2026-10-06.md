# Gold thưa trên MATH500: development replay v1

Run `a4c73220bc917a52700300d0`: **240/240 case, 2.400 lựa chọn model** đã chạy trên Modal CPU; đã kiểm chứng checksum và chạy lại toàn bộ quyết định tại local.

## Phạm vi và ngân sách

48 câu development đã quan sát × 6 model; bốn outer folds, mỗi fold 36 câu lịch sử và 12 câu đánh giá; 20 seeds. Replay dùng 288 solver outcomes đã lưu và 288 judgment Qwen3-14B thật từ pilot. Không có lời gọi solver/judge mới. Learner chỉ đọc gold của cell được audit; feedback của câu đánh giá không tham gia chọn model.

| Ngân sách danh nghĩa | Gold cells / 216 history cells | Tỷ lệ thực |
|---|---:|---:|
| 5% | 11 | 5,093% |
| 10% primary | 22 | 10,185% |
| 20% | 44 | 20,370% |

RawJudge dùng 0 gold; các phương pháp khác dùng đúng 11/22/44 cell theo từng case. Đây là giới hạn truy cập nhãn trong replay, không phải các nhãn con người mới mua. Các ablation paired dùng cùng mask; SH có acquisition path riêng với tổng budget bằng nhau.

## Thành công của model được chọn

Số câu đúng trung bình /48, sau trung bình 20 seeds. Mỗi outer fold chọn một model cho toàn bộ 12 câu held-out; đây là global model selection, không phải task-contextual routing.

| Phương pháp | 5% | 10% primary | 20% |
|---|---:|---:|---:|
| UniformGlobal | 41.45 | 42.65 | 44.65 |
| PairedGlobal | 40.10 | 43.70 | 44.90 |
| GoldRidge | 39.75 | 43.70 | 44.90 |
| CFGoldRectifier | 38.45 | 42.90 | 44.70 |
| RawJudgeRectifier | 45.40 | 45.15 | 45.45 |
| CalibratedJudge | 42.50 | 44.95 | 45.85 |
| CFJudgeRectifier | 40.90 | 44.30 | 45.40 |
| IndependentSH | 40.65 | 43.65 | 44.90 |
| PairedSH | 41.05 | 44.10 | 45.35 |
| RawJudge | 46.00 | 46.00 | 46.00 |

**Development expansion gate: FAIL.**

Gate đã khóa yêu cầu CFJudgeRectifier tại 10% có CI95 lower >0 và cải thiện ít nhất 1 điểm phần trăm trước từng đối chứng UniformGlobal, PairedGlobal, GoldRidge, CFGoldRectifier, IndependentSH, PairedSH. Không đổi candidate hoặc chọn ngân sách khác sau kết quả.

## So sánh primary tại 10%

| Đối chứng | Chênh lệch điểm % | CI95 điểm % | Rescue | Harm |
|---|---:|---|---:|---:|
| UniformGlobal | +3.44 | [+1.35, +5.83] | 3.10 | 1.45 |
| PairedGlobal | +1.25 | [-0.31, +3.65] | 1.30 | 0.70 |
| GoldRidge | +1.25 | [-0.31, +3.65] | 1.30 | 0.70 |
| CFGoldRectifier | +2.92 | [+1.25, +5.42] | 2.10 | 0.70 |
| IndependentSH | +1.35 | [-0.21, +3.44] | 1.95 | 1.30 |
| PairedSH | +0.42 | [-1.25, +2.60] | 1.35 | 1.15 |

## Calibration và phương sai dưới gold thưa

Predictor diagnostic được fit riêng trên đúng B cell paired của TRAIN, sau khi quyết định đã khóa. Không dùng lại calibration full-gold của pilot. Brier thấp tốt hơn; variance ratio <1 nghĩa là residual differences ít biến động hơn outcome differences. Hai chỉ số này chưa tự chứng minh chọn model tốt hơn.

| Ngân sách | Brier judge | Brier gold-only | Residual variance ratio | CI95 ratio | Empty inner fits /240 |
|---|---:|---:|---:|---|---:|
| 5% | 0.159262 | 0.234414 | 0.839167 | [0.720002, 0.970133] | 21/240 |
| 10% | 0.130096 | 0.213957 | 0.769981 | [0.622643, 0.932881] | 0/240 |
| 20% | 0.104877 | 0.189343 | 0.723283 | [0.553189, 0.914160] | 0/240 |

## Pool và selection diagnostics sau quyết định

Best fixed model trên 48 câu: 95.83%; oracle chọn đúng theo từng câu: 95.83%; câu có model đúng và model sai: 60.42%.

| Model | Accuracy trên 48 câu |
|---|---:|
| Qwen3-8B | 95.83% |
| DeepSeek-R1-0528-Qwen3-8B | 93.75% |
| Llama-3.1-8B-Instruct | 50.00% |
| Qwen2.5-Coder-7B-Instruct | 54.17% |
| Fin-R1 | 77.08% |
| gemma-2-9b-it | 47.92% |

| Phương pháp | Chọn một TRAIN-best model tại 10% |
|---|---:|
| UniformGlobal | 52.50% |
| PairedGlobal | 55.00% |
| GoldRidge | 55.00% |
| CFGoldRectifier | 51.25% |
| RawJudgeRectifier | 73.75% |
| CalibratedJudge | 67.50% |
| CFJudgeRectifier | 66.25% |
| IndependentSH | 53.75% |
| PairedSH | 50.00% |
| RawJudge | 86.25% |

Các references này đọc gold sau quyết định; không phải controls cùng ngân sách. TRAIN-best agreement chỉ mô tả lựa chọn có khớp lịch sử toàn gold hay không, không chứng minh nguyên nhân hoặc bảo đảm thắng trên task tương lai.

## Diễn giải và giới hạn

Nếu Brier/phương sai còn tốt nhưng selection gate FAIL, feedback có giá trị dự báo mà chưa chuyển thành quyết định tốt hơn ở budget này. Nếu diagnostic suy giảm, bằng chứng pilot với calibration nhiều gold không chuyển nguyên trạng sang gold thưa. Không gọi một ablation có point score cao hơn là phương pháp mới đã thắng.

- Bootstrap 5.000 lần theo câu, sau seed averaging; không coi seeds là dữ liệu độc lập. CI giữ nguyên fitted learners, chưa refit, chưa grouping near-duplicate hoặc điều chỉnh lịch sử nghiên cứu thích nghi.
- Sáu model, 48 câu là pool development nhỏ đã được xem trong pilot; không phải final evaluation độc lập. Giữ nguyên mọi gate AppWorld/MMLU trước đây.
- CF correction dùng shrinkage count+2, không được gọi unbiased. SH là bản thích ứng finite-archive với minimum budget 11 và stage-only scores, không tự thừa hưởng bảo đảm IID của bài gốc.
- Judge được dùng trên lịch sử đã có; đối chứng gold-only không cần judge. Equal-gold-budget chưa là equal-total-cost; chưa đo annotation savings hoặc USD.

## Quyết định tiếp

Gate FAIL: dừng mở rộng judgment theo v1. Giữ nguyên kết quả; phân tích calibration và selection bằng các ablation đã khóa. Không tune tiếp trên 48 câu để ép gate PASS.

[Protocol đã khóa](routerbench_sparse_gold_v1_protocol_2026-10-06.md) · [JSON đầy đủ](routerbench_sparse_gold_v1_results_2026-10-06.json) · [Pilot trước đó](routerbench_pilot_assessment_2026-10-06.md)
