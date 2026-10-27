# FinQA: frozen exact-answer consensus development replay

Run `5f793e80665eb1d900b97026`: 48 câu development mới ×20 model = 960 bản ghi lịch sử; đã xác minh checksum, danh tính, proxy và tính lại toàn bộ chỉ số tại local.

| Chỉ số | Giá trị |
|---|---:|
| Prediction không rỗng | 92.92% |
| Brier agreement thô | 0.468891 |
| Brier agreement cross-fit | 0.204689 |
| Brier gold-only cross-fit | 0.219816 |
| Pair residual variance ratio cross-fit | 0.923388 |
| CI95 ratio (question bootstrap) | [0.8487292923886524, 1.000612665433285] |
| Pair ratio proxy thô | 0.945479 |
| Gold success của best fixed model | 41/48 |
| Gold success của model top theo proxy thô | 41/48 |
| Per-question oracle | 46/48 |

Operational gate: **PASS**. Expansion screen: **FAIL**.

Đây là một phép thử development mới, có rule khóa trước khi mở 48×20 score của run này. Headroom 200 câu trước đó đã xem aggregate gold, nên không phải confirmation độc lập. Cross-fit vẫn cần toàn bộ gold của 36 câu huấn luyện trong mỗi fold; chưa chứng minh ít gold hơn, chọn model theo từng câu, tiết kiệm chi phí hay thắng baseline triển khai. Proxy đồng thuận dùng sẵn đầu ra lịch sử của cả 20 model; chi phí tạo ra chúng phải được tính trong một so sánh thực tế. CI không refit các fold.

[Protocol](routerbench_finqa_consensus_v1_protocol_2026-10-06.md) · [JSON](routerbench_finqa_consensus_v1_results_2026-10-06.json) · [Judge pilot](routerbench_finqa_feedback_v1_assessment_2026-10-06.md)
