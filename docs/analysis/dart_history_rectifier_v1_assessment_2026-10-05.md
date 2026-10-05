# Historical feedback rectifier v1: thực nghiệm đầy đủ

Run `52eb04e9f9e56ca65f8a968f`. Đủ **300/300 trường hợp**, kết thúc `completed_review_required`.

## Phạm vi

168 task / 56 generator / 14 agent; ba ngân sách ×20 audit seeds ×5 folds. Dùng các xác suất judge đã được sinh thật trên Modal, không gọi thêm judge/solver. Các learner chỉ nhận nhãn đã audit và feedback của outer TRAIN. Đây là phát triển thích nghi trên public normal đã xem, chưa xác nhận độc lập.

## Tất cả kết quả

| Phương pháp | 5% | 10% (primary) | 20% |
|---|---:|---:|---:|
| UniformAuditGlobal | 64.40 | 69.70 | 75.15 |
| CFGoldFactor | 67.20 | 70.30 | 74.15 |
| CFJudgeFactor | 66.50 | 72.00 | 76.10 |
| RawJudgeRectifier | 61.65 | 71.40 | 76.95 |
| JudgeImpute | 67.30 | 72.85 | 76.85 |
| FixedFactorRidge | 66.55 | 71.40 | 75.50 |
| PairedGlobal | 62.15 | 71.95 | 76.70 |
| TunedFactorRidge | 66.50 | 71.60 | 75.85 |

Đơn vị: số task thành công trung bình /168. Không phải số solver calls mới.

## Primary CFJudgeFactor ở ngân sách 10%

| Control | Chênh lệch điểm % | CI 95% điểm % | Rescue | Harm |
|---|---:|---|---:|---:|
| UniformAuditGlobal | +1.37 | [-0.09, +2.89] | 8.00 | 5.70 |
| PairedGlobal | +0.03 | [-2.71, +2.59] | 20.70 | 20.65 |
| CFGoldFactor | +1.01 | [-0.15, +2.17] | 7.30 | 5.60 |
| TunedFactorRidge | +0.24 | [-0.80, +1.22] | 7.65 | 7.25 |

**Primary exploratory signal: FAIL.** Tiêu chí đã khóa: CI lower >0 với cả UniformAuditGlobal và PairedGlobal.

CI lấy từ 5.000 bootstrap theo generator, seed1404, sau khi trung bình audit seeds. Không điều chỉnh toàn bộ lịch sử adaptive experiments; không phải bảo đảm không thua khi deploy.

## Ý nghĩa cơ chế

- CFGoldFactor dùng cùng cross-fit và rectifier nhưng không dùng judge. Chênh lệch với nó mới phản ánh phần bổ sung từ feedback trong họ estimator này.
- TunedFactorRidge là structured control chọn regularization bằng inner CV, từ gain v1; FixedFactorRidge dùng penalty 4 cố định để tách phần tuning.
- RawJudgeRectifier bỏ calibration; JudgeImpute bỏ residual correction. Giữ lại cả hai dù chúng thắng hay thua phương pháp primary.
- Tất cả phương pháp ở đây chọn một agent toàn cục dựa trên lịch sử train. Chưa phải router học lợi thế theo từng task và chưa có adaptive pair acquisition.
- Nếu thắng về số nhãn gold, vẫn phải tính chi phí thu 2.352 judgment lịch sử; không suy ra cùng USD/compute với baseline không cần judge.

## Kiểm chứng

Đã xác minh source/input identity, 300 checkpoint checksums, đúng audit counts/control choices, generator isolation, công thức rectification và tất cả bootstrap summaries tính lại từ action traces. Unit tests kiểm tra thay nhãn chưa audit không đổi kết quả, nhãn của một generator không lọt vào mô hình dự báo cho chính generator đó, constant proxy=.5 khôi phục Global chính xác, và resume không chạy lại case đã lưu.

## Giới hạn và hướng tiếp

Bảng này là bằng chứng phát triển, không đủ xác nhận novelty hoặc khả năng nhận bài A/A*. Chỉ giữ một ứng viên khi cải thiện còn tồn tại với control gold-only mạnh và validation độc lập. Nếu phần judge không đem lại lợi ích, không gọi lợi ích của cấu trúc agent là thành công của hiệu chỉnh feedback. Không dùng chính outer test để chọn lại primary.

- [Protocol khóa trước](dart_history_rectifier_v1_protocol_2026-10-05.md).
- [JSON đầy đủ cho mọi phương pháp/ngân sách](dart_history_rectifier_v1_results_2026-10-05.json).
- [PPI++](https://arxiv.org/html/2311.01453v2) và [Cross-PPI](https://arxiv.org/html/2309.16598v2) là nền tảng tham khảo; estimator regularized ở đây không được cấp tự động các bảo đảm của chúng.
- Raw artifacts: `results/dart_history_rectifier_v1/cloud/`.
