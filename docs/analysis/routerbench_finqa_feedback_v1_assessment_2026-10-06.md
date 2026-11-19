# FinQA: kết quả pilot judge thật

Run `0fad63edd346eb0591fd99e1`: 48 câu ×20 model = **960/960 judgment**; đã kiểm chứng artifacts và tính lại tại local.

| Chỉ số | Giá trị |
|---|---:|
| Judgment hợp lệ | 100.00% |
| Trích được boxed answer hoàn chỉnh | 92.60% |
| Brier judge thô | 0.368354 |
| Brier judge sau cross-fit | 0.208561 |
| Brier gold-only control | 0.237974 |
| Brier gain | 0.029413 |
| Tỷ số phương sai residual differences | 1.045407 |
| CI95 tỷ số | [1.019378880562028, 1.0735299195365071] |
| Attempts / recorded responses | 960 / 960 |
| Input / output tokens ghi nhận | 1,299,117 / 11,240 |

Operational gate: **PASS**. Expansion screening: **FAIL**.

Judge thấy full FinQA prompt và candidate final answer đã trích từ archived solver output. Gold là binary score archived, không được chấm lại. Cross-fit dùng toàn gold của 36 câu khác mỗi fold; chưa đo lợi ích chọn model ở 5/10/20% gold hoặc chi phí ròng. CI bootstrap giữ nguyên fitted predictions và 48 câu development, không phải independent confirmation.

[Protocol](routerbench_finqa_feedback_v1_protocol_2026-10-06.md) · [JSON](routerbench_finqa_feedback_v1_results_2026-10-06.json) · [Headroom](routerbench_headroom_v1_assessment_2026-10-06.md)
