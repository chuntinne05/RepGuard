# Paired historical rectifier v1: thực nghiệm đầy đủ

Run `cd0b2656876f7f973d7b67ce`. Đủ **300/300 trường hợp**, kết thúc `completed_review_required`.

## Phạm vi

Chỉ đổi acquisition sang đúng 300 paired masks cũ; estimator giữ nguyên. UniformCFJudgeFactor là phương pháp ở batch uniform trước, dùng để đo acquisition effect.

168 task / 56 generator / 14 agent; ba ngân sách ×20 audit seeds ×5 folds. Dùng các xác suất judge đã được sinh thật trên Modal, không gọi thêm judge/solver. Các learner chỉ nhận nhãn đã audit và feedback của outer TRAIN. Đây là phát triển thích nghi trên public normal đã xem, chưa xác nhận độc lập.

## Tất cả kết quả

| Phương pháp | 5% | 10% (primary) | 20% |
|---|---:|---:|---:|
| PairedGlobal | 62.15 | 71.95 | 76.70 |
| CFGoldFactor | 62.75 | 72.85 | 76.75 |
| CFJudgeFactor | 64.70 | 74.15 | 77.50 |
| RawJudgeRectifier | 66.55 | 68.80 | 75.75 |
| JudgeImpute | 66.85 | 72.55 | 77.50 |
| FixedFactorRidge | 62.60 | 72.30 | 77.35 |
| UniformAuditGlobal | 64.40 | 69.70 | 75.15 |
| TunedFactorRidge | 66.50 | 71.60 | 75.85 |
| UniformCFJudgeFactor | 66.50 | 72.00 | 76.10 |

Đơn vị: số task thành công trung bình /168. Không phải số solver calls mới.

## Primary CFJudgeFactor ở ngân sách 10%

| Control | Chênh lệch điểm % | CI 95% điểm % | Rescue | Harm |
|---|---:|---|---:|---:|
| PairedGlobal | +1.31 | [+0.03, +2.59] | 5.95 | 3.75 |
| UniformAuditGlobal | +2.65 | [-0.60, +5.86] | 23.05 | 18.60 |
| CFGoldFactor | +0.77 | [+0.00, +1.58] | 4.40 | 3.10 |
| TunedFactorRidge | +1.52 | [-1.07, +4.05] | 20.20 | 17.65 |
| UniformCFJudgeFactor | +1.28 | [-1.58, +4.14] | 21.60 | 19.45 |

**Primary exploratory signal: FAIL.** Tiêu chí đã khóa: CI lower >0 với cả UniformAuditGlobal và PairedGlobal.

CI lấy từ 5.000 bootstrap theo generator, seed1404, sau khi trung bình audit seeds. Không điều chỉnh toàn bộ lịch sử adaptive experiments; không phải bảo đảm không thua khi deploy.

## Ý nghĩa cơ chế

- CFGoldFactor dùng cùng paired audit, cross-fit và rectifier nhưng không dùng judge. Chênh lệch với nó mới phản ánh phần bổ sung từ feedback trong họ estimator này.
- TunedFactorRidge là uniform-audit structured control chọn regularization bằng inner CV, từ gain v1; FixedFactorRidge dùng penalty 4 cố định để tách phần tuning.
- RawJudgeRectifier bỏ calibration; JudgeImpute bỏ residual correction. Giữ lại cả hai dù chúng thắng hay thua phương pháp primary.
- Tất cả phương pháp ở đây chọn một agent toàn cục dựa trên lịch sử train. Chưa phải router học lợi thế theo từng task và chưa có adaptive pair acquisition.
- Nếu thắng về số nhãn gold, vẫn phải tính chi phí thu 2.352 judgment lịch sử; không suy ra cùng USD/compute với baseline không cần judge.

## Kiểm chứng

Đã xác minh source/input identity, 300 checkpoint checksums, đúng audit counts/control choices, generator isolation, công thức rectification và tất cả bootstrap summaries tính lại từ action traces. Unit tests kiểm tra thay nhãn chưa audit không đổi kết quả, nhãn của một generator không lọt vào mô hình dự báo cho chính generator đó, constant proxy=.5 khôi phục Global chính xác, và resume không chạy lại case đã lưu.

## Giới hạn và hướng tiếp

Bảng này là bằng chứng phát triển, không đủ xác nhận novelty hoặc khả năng nhận bài A/A*. Chỉ giữ một ứng viên khi cải thiện còn tồn tại với control gold-only mạnh và validation độc lập. Nếu phần judge không đem lại lợi ích, không gọi lợi ích của cấu trúc agent là thành công của hiệu chỉnh feedback. Không dùng chính outer test để chọn lại primary.

- [Protocol khóa trước](dart_paired_history_v1_protocol_2026-10-05.md).
- [JSON đầy đủ cho mọi phương pháp/ngân sách](dart_paired_history_v1_results_2026-10-05.json).
- [PPI++](https://arxiv.org/html/2311.01453v2) và [Cross-PPI](https://arxiv.org/html/2309.16598v2) là nền tảng tham khảo; estimator regularized ở đây không được cấp tự động các bảo đảm của chúng.
- Raw artifacts: `results/dart_paired_history_v1/cloud/`.
