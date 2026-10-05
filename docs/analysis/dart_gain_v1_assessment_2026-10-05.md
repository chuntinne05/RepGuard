# DART gain/structure v1: báo cáo thực nghiệm đầy đủ

Run `834f51cc00d1f3b8e9766c0a`. Trạng thái cuối `completed_review_required`; đủ **305/305 cases**.

## Phạm vi và kiểm chứng

Đây là huấn luyện/replay thật trên outcome AppWorld đã có, không phải chạy lại solver. 168 task, 56 generator, 14 agent. Public normal đã dùng trong nhiều vòng phát triển; không phải xác nhận độc lập. Không đọc challenge hoặc MMLU sealed.

Đã kiểm tra 305 checksum, 300 control choices/audit counts, tách nhóm inner/outer, và tính lại toàn bộ summaries/CI từ action traces; đều khớp.

## Full-label diagnostic R0

| Method | Thành công /168 | Chênh lệch điểm % với Global | CI 95% điểm % |
|---|---:|---:|---|
| Global | 82.00 | +0.00 | [+0.00, +0.00] |
| FactorRidge | 82.00 | +0.00 | [+0.00, +0.00] |
| SemanticRidge | 74.00 | -4.76 | [-10.71, +0.00] |
| TextRidge | 76.00 | -3.57 | [-7.14, -0.60] |
| DirectUtility | 78.00 | -2.38 | [-6.55, +1.19] |
| Selected | 77.00 | -2.98 | [-7.14, +0.60] |

R0 dùng toàn bộ nhãn train, không so nó với control chỉ được audit 10%.

## R1: cùng ngân sách audit

Mỗi ngân sách: 20 audit seeds × 5 outer folds; cùng đúng tập nhãn với UniformAuditGlobal. PairedGlobal dùng cùng tổng số nhãn với thiết kế lấy mẫu khác. Giá trị là số task thành công trung bình trên 168 task, không phải 168 solver runs mới cho mỗi router.

| Method | 5% | 10% (primary) | 20% |
|---|---:|---:|---:|
| Global | 64.40 | 69.70 | 75.15 |
| FactorRidge | 66.50 | 71.60 | 75.85 |
| SemanticRidge | 64.75 | 68.50 | 73.65 |
| TextRidge | 65.55 | 68.60 | 74.80 |
| DirectUtility | 64.60 | 65.95 | 69.45 |
| Selected | 64.95 | 67.25 | 73.30 |
| UniformAuditGlobal | 64.40 | 69.70 | 75.15 |
| PairedGlobal | 62.15 | 71.95 | 76.70 |

### Primary 10%: tất cả family so với hai controls

| Method | Control | Chênh lệch điểm % | CI 95% điểm % | Rescue | Harm |
|---|---|---:|---|---:|---:|
| Global | UniformAuditGlobal | +0.00 | [+0.00, +0.00] | 0.00 | 0.00 |
| Global | PairedGlobal | -1.34 | [-4.23, +1.52] | 20.20 | 22.45 |
| FactorRidge | UniformAuditGlobal | +1.13 | [-0.21, +2.53] | 5.80 | 3.90 |
| FactorRidge | PairedGlobal | -0.21 | [-2.53, +2.08] | 20.00 | 20.35 |
| SemanticRidge | UniformAuditGlobal | -0.71 | [-2.71, +1.37] | 9.50 | 10.70 |
| SemanticRidge | PairedGlobal | -2.05 | [-5.03, +0.77] | 19.85 | 23.30 |
| TextRidge | UniformAuditGlobal | -0.65 | [-2.14, +0.83] | 5.90 | 7.00 |
| TextRidge | PairedGlobal | -1.99 | [-4.70, +0.54] | 20.25 | 23.60 |
| DirectUtility | UniformAuditGlobal | -2.23 | [-4.82, +0.36] | 13.40 | 17.15 |
| DirectUtility | PairedGlobal | -3.57 | [-6.90, -0.24] | 18.85 | 24.85 |
| Selected | UniformAuditGlobal | -1.46 | [-3.57, +0.63] | 9.85 | 12.30 |
| Selected | PairedGlobal | -2.80 | [-5.51, -0.21] | 19.20 | 23.90 |

**Primary signal gate: FAIL.** Selected phải có CI lower > 0 với cả hai controls. Không chọn một family khác sau khi xem T để thay primary endpoint.

Bootstrap 5.000 lần theo generator, seed 1404, sau khi lấy trung bình audit seeds. CI exploratory chưa điều chỉnh toàn bộ lịch sử thử nghiệm; không phải bảo đảm triển khai.

## Ý nghĩa từng thay đổi

- FactorRidge chỉ chia sẻ thống kê model/scaffold để chọn một agent toàn cục; không phải contextual DART mới.
- SemanticRidge giữ đủ MiniLM 384 chiều; TextRidge kiểm tra lexical features với cùng squared loss.
- DirectUtility tối ưu signed utility qua softmax, thay vì dự báo xác suất bằng BCE. Nó là adaptation của hướng policy learning có trước, chưa chứng minh novelty.
- Selected chọn family/regularization trong inner CV bằng đúng nhãn đã mua; không nhìn outer gold.
- Chỉ trừ anchor khỏi ridge targets không thay thứ hạng với cùng thiết kế; đã có test kiểm chứng đại số.

## Bước tiếp theo

Nếu một family tốt hơn controls, coi đó là ứng viên phát triển: kiểm tra tính ổn định theo generator/ngân sách, khóa thiết kế và xác nhận trên dữ liệu độc lập. Nếu Selected không thắng, không thay tên family thắng nhất thành phương pháp primary. Lợi ích chỉ từ FactorRidge sẽ ủng hộ giảm nhiễu ước lượng agent, chưa chứng minh khai thác feedback sai hay transfer theo task.

Hướng bài báo cần chứng minh phần feedback correction/acquisition mang lợi ích tăng thêm so với gold-only structured controls cùng budget, rồi đối chiếu các phương pháp gần. Một con số cao hơn trên public normal chưa bảo đảm bài A/A*.

## Tài liệu

- [Protocol khóa trước](dart_gain_v1_protocol_2026-10-05.md).
- [JSON tổng hợp đầy đủ](dart_gain_v1_results_2026-10-05.json).
- [Causal LLM Routing](https://arxiv.org/html/2505.16037v2): cơ sở cho direct regret/utility optimization.
- [Offline Multi-Action Policy Learning](https://arxiv.org/abs/1810.04778): nền tảng policy learning.
- Raw artifacts: `results/dart_gain_v1/cloud/`; không commit các task/trajectory derivatives vào Git.
