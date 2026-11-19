# Kiểm lại gap sau khi tìm thêm prior art gần và triển khai vòng02

09/11/2026. Tài liệu này cập nhật strategy; không sửa preregistration hoặc đổi primary của run đang hoạt động. Đề tài chưa có đóng góp method đã chứng minh, cũng chưa có product demand được xác nhận.

## Kết luận định hướng hiện tại

Giữ multi-agent, nhưng luận điểm cần bảo vệ là **khi nào việc chuyển kết quả giữa agent giúp công việc kiểm chứng và khi nào nó gây sửa sai thành sai hơn**. Số agent, JSON schema, tính lại phép toán và claim ledger đều chưa đủ làm novelty. Lịch sử/reputation chỉ mở sau khi chứng minh có utility khác nhau giữa các actions mà learner dự báo được.

ARQA vòng02 là phép đo tách cơ chế và kiểm pipeline, không đủ làm toàn bộ khóa luận lớn: đây là static table QA có nguồn oracle sẵn, một doanh nghiệp, chưa có môi trường tương tác hoặc task từ người dùng. Không dùng chữ “agentic end-to-end” cho kết quả này.

## Những chỗ prior art đã phủ

|Nguồn chính thức, độ đọc|Đã làm gì liên quan|Hệ quả cho đồ án|
|---|---|---|
|[VeriFin v3,23/10](https://arxiv.org/html/2608.10213v3), đọc phương pháp/thiết lập/error analysis|Nguồn facts và phép tính độc lập candidate; kiểm XBRL/SMT; lỗi period/concept có thể làm formal check từ chối đáp án đúng|Không nhận source binding, formula provenance, abstain hay solver feedback là mới. Checker hiện tại còn thiếu độc lập về formula authority.|
|[Upstream Influence,13/10](https://arxiv.org/html/2610.17723v1), đọc thiết kế/handoff/limitations|Can thiệp source access và rationale handoff trên political stance chains; limitation chưa đo clean-task cost/accuracy tradeoff|Giữ original source, đổi handoff và đo re-anchoring không tự mới. Cần đúng/sai của nghiệp vụ, lợi ích sửa lỗi và chi phí thực.|
|[When Must Becomes Maybe,25/08](https://arxiv.org/html/2608.24569v1), đọc setting/identification/measurement|Tách phát hiện blocker, biến đổi artifact và hành động cuối; matched transformations, restoration và containment trên controlled synthetic episodes|“Preserve constraints across handoff” và stage-separated intervention đã có. Không đổi tên blocker thành claim rồi nhận method mới.|
|[When Code Becomes an LLM Call,17/10](https://arxiv.org/html/2610.24545v1), đọc study design/contract model/results overview|Kiểm expected vs implemented contracts ở call sites; sự tồn tại của checker không chứng minh đủ ràng buộc|Hash/schema/parser PASS là provenance/interface evidence; phải kiểm completeness của contract theo task độc lập implementation. Lỗ hổng final-dependency ở checker đồ án là ví dụ kỹ thuật, không bằng chứng paper.|
|[Capable language models can outgrow collaboration,24/07](https://www.nature.com/articles/s42256-026-01268-y), đọc phần official search-index trả về; direct page bị redirect|So cấu trúc phối hợp dưới cùng tools và system compute ceilings trên nhiều agentic tasks; khả năng dự báo tuyệt đối qua domain còn hạn chế|Không biến một threshold hay một benchmark thành quy luật chung. Tập xác nhận phải có strong single đủ tools và cùng trần tài nguyên toàn hệ, không chia budget bất lợi cho baseline.|

Các bài MoCA/CLAIR-Fin/ConditionalAgentTrust/MiniRep/Ao/ASB/CABS trong literature trước vẫn là closest comparators cho từng nhánh. Bảng này không là systematic review hoàn tất; không kết luận “chưa ai làm” chỉ vì search không thấy.

## Giả thuyết có thể kiểm tiếp, chưa gọi là gap đã xác nhận

**H1:** trên lỗi metric/period/unit/formula có oracle kiểm độc lập, handoff mang reasoning có thể vừa cứu lỗi vừa tạo harmful revision; một cơ chế kiểm phạm vi trước khi chấp nhận revision có thể cải thiện tradeoff này ở cùng resources.

**H2:** nếu nguồn không cung cấp đủ authority cho một formula, tốt hơn có thể là xin thêm nguồn hoặc chuyển người soát; tác dụng sản phẩm phải tính cả phần việc được hoàn thành và review burden, không chỉ precision của số ít câu được nhận.

**H3:** chỉ nếu correction utility khác nhau có cấu trúc theo task/state, history dưới feedback chưa đầy đủ có thể giúp chọn reviewer/check. Phải thắng current-state learner cùng thông tin, global-history và history shuffle. Không dùng chính benchmark gold để tạo feedback triển khai hoặc chọn action rồi báo như không có gold.

H1/H2 có thể vẫn trùng method gần; trước khi đặt tên thuật toán, phải lập bảng assumptions + available information + action space + counterfactual target cho finalist so với VeriFin/MoCA/CLAIR. Nếu khác biệt chỉ thêm checklist, đóng góp nên được mô tả là empirical evaluation và hệ thống, không thuật toán mới.

## Đường tới phép xác nhận, theo điều kiện ra quyết định

1. **Hoàn tất vòng02:** giữ score frozen, kiểm receipt/parent/GPU/config, báo uncertainty, token/call/time và GO/STOP. Secondary final-dependency được ghi riêng vì thêm sau registration. Nếu near ceiling hoặc không có correction headroom, không mua thêm calls cho cùng setup.
2. **Xác thực task và nhu cầu:** hai người trả lời24source-only QA độc lập, sau đó so gold. Discovery5–8người đang kiểm/lập báo cáo; xác định một episode lặp lại, đầu ra có người duyệt và nguồn dùng được. Hai công việc này làm độc lập với việc score có đẹp không.
3. **Chốt một workload:** ưu tiên thao tác kiểm báo cáo thật cần đi qua nguồn/bảng/thuyết minh và quyết định chấp nhận/sửa/xin thêm bằng chứng. Chỉ thêm retrieval hoặc nhiều tài liệu khi task cần. Không tự ghép pair labels thành joint truth.
4. **Chọn một mechanism từ lỗi đã kiểm:** định nghĩa sai khác cụ thể, ví dụ period/formula bị thay qua handoff dù numerical checker PASS. Một can thiệp một lần; so blind independent reasoning, self-review, peer reasoning, single-agent cùng contract và deterministic checker. Stress injection nếu dùng phải tách synthetic intervention khỏi natural errors; không gộp để tăng error prevalence.
5. **Khóa confirmation:** nguồn/company/document groups không dùng design; external corpus; finalist và một primary comparator; stronger single model; trần tổng tokens/tool calls và budget dùng thực. Chọn sample size theo paired group variance và minimal meaningful effect trước outcomes, có reserve cho ambiguity/source missing; không lấy24QA làm đủ.
6. **Đo tác dụng sản phẩm:** người dùng làm task có đầu ra chấm độc lập, counterbalance task order, đo thời gian hoàn tất đúng, lỗi cuối, false approvals, số lần mở nguồn và phần việc phải escalation. Không thay số này bằng demo hoặc satisfaction.

## Cách đặt tiêu chuẩn ý nghĩa

Chốt cùng người dùng và GVHD trước confirmation: lỗi nào đáng ngăn, mức sửa lỗi/tốn thêm bao nhiêu thời gian có giá trị, và khối lượng review nào chấp nhận được. Có thể dùng mục tiêu phát triển như giảm thời gian kiểm một task nhưng không tăng harmful approvals; đây chưa là kết quả, threshold cuối phải từ workflow và đo variance.

Với metric false-approval hiếm, 0lỗi quan sát không là chứng nhận0risk. Theo bound nhị thức một phía95%, nếu0lỗi trong n accepted independent cases thì upper bound là `1−0.05^(1/n)`; để bound<1% cần ít nhất299accepted cases. Nếu có clustering theo report/company, giả định độc lập không còn đúng và cần thiết kế/bound phù hợp. Vì thế pilot24groups không chứng minh độ an toàn cao dù quan sát0false accepts.

Một khóa luận thuyết phục có thể có kết quả âm nhưng phải trả lời câu hỏi rõ, artifact tái lập, comparator mạnh, oracle đáng tin và giải thích hệ quả thực tế. Không ép một kết quả âm thành method superiority; cũng chưa được hứa bài báo, điểm cao hoặc “tốt nhất” khi các gate này chưa qua.
