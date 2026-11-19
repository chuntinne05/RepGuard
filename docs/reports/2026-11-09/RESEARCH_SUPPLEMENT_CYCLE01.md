# Research bổ sung trong vòng thực thi 01

Ngày 09/11/2026. Bổ sung cho literature review trước, không sửa protocol đang thu responses.

## Những công trình làm hẹp claim tiếp theo

| Nguồn gốc | Đã kiểm gì | Hệ quả cho study/khóa luận |
|---|---|---|
| [FinSAgent](https://arxiv.org/html/2607.18102v1), preprint 20/07/2026 | Setup và phần matched-budget retrieval ở Appendix B | Role-specialized retrieval và validity-aware reranking đã có. Nếu sau này mở raw-report retrieval, cần comparator cùng retrieval budget và corpus access; không chỉ so naive RAG |
| [CAST](https://aclanthology.org/2026.finnlp-1.26.pdf), FinNLP 28/10/2026 | Evidence scoring và limitations | Confidence đối chiếu giả thuyết dựa trên citations đã có. Bài ghi same-model roles, LLM-judged correctness và giả định citation independence là giới hạn. Pilot hiện tại dùng published expert passage labels để tránh coi đồng ý với model judge là gold mới |
| [AgenticFinBench](https://arxiv.org/html/2611.04813v2), v2 **04/11/2026** | Taxonomy, hai-stage claim audit, human validation và audit-agent protocol | Benchmark đã tách support trong trace khỏi factual verification bên ngoài, có human validation. Không nhận phân biệt grounding/correctness hay task tài chính từ yêu cầu thật là ý đầu tiên. Có thể thẩm định làm external workload về sau; chưa tải/open outcomes benchmark này |
| [BP-TD](https://arxiv.org/abs/2611.04805), preprint **03/11/2026**, tác giả ghi extended version của IEEE BigData short paper | Abstract và scope kết quả | Dependence-aware label-free truth discovery đã có; kết quả tác giả còn cho thấy một ít labels có thể làm best-single mạnh hơn aggregator. Nếu mở reputation/aggregation, luôn có equal-label best-single control |
| [More Modalities, More Problems](https://aclanthology.org/2026.aacl-short.60/), AACL/IJCNLP 11/2026 | Official abstract/metadata | Bài time-series ghi nhận shared upstream errors và overhead của debate. “Cùng đồng ý vẫn sai” không là novelty; cần outcome/cost controls cụ thể |
| [ClaimReceipt](https://arxiv.org/abs/2609.01992), preprint 02/09/2026 | Abstract/specification scope | Sufficiency của evidence cho một claim và coverage của toàn experiment set là hai việc khác nhau. Hash/ledger không tự là semantic validation; nghiên cứu này ghi riêng source/receipt audit, operational gate và scientific outcome |

Đây là targeted review, không phải tái lập các paper. Không dùng citations để tự nhập guarantees hay kết luận superiority vào RepGuard.

## Phân biệt oracle quyết định thiết kế vòng 01

[Relevant Is Not Enough](https://aclanthology.org/2026.finnlp-1.32.pdf), phần 2–3, tách nhãn standalone passage khỏi nhãn claim truth và không chấm joint sufficiency của các đoạn riêng lẻ chưa đủ. Vì vậy:

- Study 01 chỉ yêu cầu đánh giá **một claim–passage pair**, không cho thêm passages rồi dùng nhãn pair cũ chấm kết luận mới.
- Multi-agent ở vòng này là một assessor và một reviewer trao đổi trên cùng evidence; không nhận đã kiểm chứng source diversity hoặc end-to-end report checking.
- Kết quả nếu tốt chỉ cho phép bước nghiên cứu tiếp; không chứng minh một sản phẩm báo cáo đã có utility.
- Nếu mở joint evidence hoặc raw reports, cần protocol và oracle mới. Có thể tái sử dụng rubric công bố, nhưng labels mới phải có provenance/chuyên gia phù hợp.

## Thông tin người dùng cập nhật

Người dùng xác nhận chưa có nhóm người dùng mục tiêu để phỏng vấn/dùng thử. Do đó G0 về product demand **chưa đạt**. Tài chính hiện là research vertical được đề xuất để tận dụng dữ liệu và hạ tầng, không phải domain đã được người dùng thực tế chọn.

Trong khi machine pilot chạy, chuẩn bị recruitment/interview kit. Không gửi tin nhắn cho người khác, không tự tạo interviews hay human-study scores. Nếu không tiếp cận được workflow tài chính thật, lựa chọn vertical sau phải dựa vào người dùng có thể tuyển và loại lỗi có bằng chứng; không chỉ chọn theo benchmark dễ lấy.
