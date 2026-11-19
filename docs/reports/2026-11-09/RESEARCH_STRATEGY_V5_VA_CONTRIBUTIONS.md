# Strategy V5 — đề tài đủ rộng, đóng góp phải có bằng chứng

Cập nhật 09/11/2026 sau pilot workspace v4 và phần triển khai relational v5. **Hướng làm việc: bảo toàn yêu cầu và bằng chứng qua các bước bàn giao trong hệ đa tác tử phân tích dữ liệu/báo cáo.** Không đổi tên đề tài đã được GVHD duyệt. Đây là research agenda có component đã chạy, chưa phải tuyên bố đã xác nhận novelty, generalization hoặc impact sản phẩm.

## 1. Bài toán đủ lớn nằm ở đâu?

Một workflow phổ biến là **yêu cầu → chọn dữ liệu → tính toán → tổng hợp → kiểm tra/sửa → giao báo cáo**. Mỗi tác tử có thể nhận lại bản tóm tắt, query hoặc bảng do tác tử trước tạo. Một quyết định quan trọng có thể bị mất: tính theo đơn đã giao hay đơn đã gửi, đếm người hay bản ghi, dùng tên viết tắt nào, kiểm được trường nào và còn điều gì chưa rõ. Kết quả vẫn có thể chạy được, có số liệu và được tác tử sau đồng ý.

Đồ án nghiên cứu độ tin cậy của **toàn bộ chuỗi công việc**, với analytics/reporting là họ ứng dụng chung. Nghiên cứu/thí nghiệm, vận hành và tài chính là ba workload mục tiêu, không phải ba sản phẩm phải xây cùng lúc. Hiện chưa có triển khai hoặc phỏng vấn chứng minh nhu cầu ở ba nhóm đó.

Tên làm việc đề xuất: **“Bảo toàn ràng buộc và bằng chứng trong hệ đa tác tử cho phân tích dữ liệu và báo cáo.”** Người dùng cuối cần bảng/báo cáo đúng và dễ kiểm; multi-agent là kiến trúc phải chứng minh khi nào đáng dùng, không phải điều kiện buộc mọi task phải qua nhiều model.

## 2. Những nghiên cứu mới nhất loại bỏ các claim novelty dễ nhầm

Đây là phần bổ sung cho [matrix V4](WORKSPACE_V4_LITERATURE_VA_RESEARCH_QUESTION.md), không thay việc reproduce baseline. Mức đã đọc ghi rõ; không suy số liệu từ abstract thành kết quả của đồ án.

| Nguồn sơ cấp | Phần đã kiểm và điều đã có | Hệ quả |
|---|---|---|
| [SpecBridge, 03/11/2026](https://arxiv.org/html/2611.04318v1), §2/§7 và README/license/interface | Request sets có hai cách hiểu hợp lệ; phương pháp tách quyết định diễn giải rồi trả các cách hiểu. | Không nhận “question có nhiều cách hiểu/single-reference score có vấn đề” là phát hiện mới. Dùng làm nguồn ngoài và comparator ambiguity-aware; không lấy task371 làm bằng chứng mới của hiện tượng chung. |
| [Verifying SQL under Changing Business Semantics, 30/10](https://arxiv.org/html/2610.41090v1), method/§9 | Revision-bound contracts và legal counterexamples; xác nhận trong authored schema/local producers, chưa là independent-schema transfer. | SQL chạy được chưa chứng minh đúng nghiệp vụ; contract và counterexample testing đều đã có. Không gọi checker hiện tại là SQL-equivalence verifier. |
| [Trace Integrity, 26/08](https://arxiv.org/html/2608.26036v1), §3/§6 | Execution contracts, operator/source bindings và separation giữa answer accuracy/trace validity; scoped proof-of-concept. | Operator binding và candidate-independent planning không đủ novelty. Static query checks của v5 là infrastructure, không tự là phương pháp mới. |
| [SemanticAgent, 23/04](https://arxiv.org/html/2604.21414v1), method overview | Semantic knowledge, synthesis và diagnostic refinement trong text-to-SQL data synthesis. | “Thêm semantic knowledge + verifier” đã có; cần phân biệt data synthesis với native task completion của đồ án. Chưa reproduce phương pháp. |
| [Maat](https://arxiv.org/html/2609.34017v1), system/method/results/limitations overview | Deterministic contract-based handoff validation ở nhiều controlled workflows. HTML có revision note về lỗi scorer và false halts; không coi mọi halt là defect đã ngăn được. | Giữ contract qua nhiều agent không mới. Phải đo false stop và công việc hoàn thành, không lấy số lần chặn làm impact. Chưa audit/reproduce code baseline. |
| [When Must Becomes Maybe v2, 13/10](https://arxiv.org/html/2608.24569v2), task definition và controlled design overview | Handoff có thể giữ nội dung nhưng làm yếu vai trò ràng buộc; phân biệt trạng thái được truyền với endpoint action. | Bảo toàn ràng buộc qua summary đã có nghiên cứu. Đồ án cần task/data outcomes và controls phù hợp, không đổi tên hiện tượng. |
| [Verification-Status Laundering](https://arxiv.org/html/2609.20211v1), design/overview | Mất trạng thái “chưa kiểm” qua summaries/memory trong authorization-sensitive pipelines. | Structured status propagation không mới. Research question analytics cần khác threat model và được đo riêng. Metadata ngày/id trên trang có chỗ khác kỳ vọng, nên không suy thứ tự xuất bản từ số ID. |

VeriMAP, VerifyMAS, ICR, ARIA, ToxicBench, ContractBench và các nguồn V3/V4 vẫn là prior gần. Đợt tìm này **không xác nhận một thuật toán mới độc quyền** cho đồ án.

## 3. Research gap làm việc — phát biểu đủ kiểm chứng

**Câu hỏi trung tâm:** khi tác tử phải bàn giao công việc phân tích dữ liệu có yêu cầu diễn giải/scope cụ thể, trạng thái kiểm chứng nào cần được giữ và kiểm lại để giảm lỗi cuối mà vẫn hoàn thành công việc, với cùng nguồn, checker và tài nguyên như một single-agent đủ mạnh?

Khoảng trống được đề xuất là **bằng chứng thực nghiệm về giá trị riêng của cơ chế trong điều kiện kết hợp này**, không phải sự tồn tại của contracts/critics/ambiguity. Trong phạm vi các nguồn đã đọc, chưa có kết quả nào có thể dùng trực tiếp để kết luận hệ của đồ án có lợi ích trên lỗi query tự nhiên, diễn giải đã chọn, nguồn/schema mới và chi phí cấu hình được tính đầy đủ. Điều đó chưa chứng minh không có công trình khác giải quyết nó; cần reproduce/đối chiếu native baseline trước khi viết claim novelty cuối cùng.

Ba câu hỏi cụ thể:

1. **RQ1 — nguồn lỗi:** bao nhiêu lỗi cuối đến từ chọn sai thuộc tính/phạm vi/đơn vị hoặc mất ràng buộc qua bàn giao, bao nhiêu chỉ là output shape, thiếu budget, hoặc measurement ambiguity? Giữ nhãn “chưa xác định”, không tự biến refusal thành catch.
2. **RQ2 — cơ chế:** khi giữ contract/source/checker như nhau, feedback cụ thể và handoff có cấu trúc có cải thiện task completion đúng hơn full-context/neutral recheck/self-review không? Lợi ích nào đến từ retrieval, checker, representation hay model khác?
3. **RQ3 — tính tổng quát và thực tiễn:** giữ nguyên cơ chế sang nguồn/schema/workload mới được bao nhiêu; cần bao nhiêu công sức mapping; có giảm tổng thời gian kiểm của người dùng không?

Nếu structured query compilation từ semantic layer đã giải được task, cần dùng nó làm baseline mạnh. Không bắt LLM đoán lại định nghĩa rồi nhận thắng một baseline bị thiếu thông tin. Nếu chỉ checker giúp còn số agent không giúp, kết luận là giá trị của checker; giữ kết quả đó trung thực.

## 4. Ba contribution mục tiêu và trạng thái hiện tại

| Contribution | Deliverable có thể bảo vệ | Bằng chứng hiện có / còn thiếu |
|---|---|---|
| C1 — nghiên cứu lỗi và chuẩn đánh giá | Error bank có source lineage; tách đúng task, đúng trace, ambiguity, false accept/false stop và coverage. | Có36trajectory/113realresponses V4; chưa có human adjudication của nhóm. Nguồn ngoài có upstream-reviewed labels, không tính là nhãn mới do đồ án tạo. Chưa có đánh giá held-out. |
| C2 — hệ thống tái lập | API contract/source/output; kiểm query có giới hạn; receipt và re-audit qua handoff; reviewer callback và source tools. | Đã implement, có29tests mới và87scoped tests tổng; chạy lại20SQL trên dữ liệu thật,20/20khớp bytes cũ. Chưa đo method accuracy hoặc lợi ích model từ component mới. Đây là đóng góp kỹ thuật, chưa là novelty thuật toán. |
| C3 — bằng chứng cơ chế và lợi ích sử dụng | Matched controls, nguồn/schema mới, báo cost và mapping effort; pilot người dùng trên một workflow thật. | Thiết kế bên dưới;0newmodelcalls ở V5,0users/interviews. Chưa có causal/transfer/product result. |

Khóa luận có thể tạo đóng góp tốt bằng kết quả thực nghiệm mới, công cụ tái lập và đánh giá thực tế. Không cần hứa thuật toán mới khi prior chưa cho phép; cũng không lấy số module/agent/use cases làm thước đo contribution.

## 5. Mở rộng quy mô bằng nguồn độc lập và split có thể audit

Đã chuẩn bị [SpecBridge tại commit cố định](https://github.com/Xyc-arch/specbridge-artifact/tree/a51be850a113a6b7c0ada57ad3c7806c6c3f25a4):307records,204được tác giả upstream chấp nhận,12databases từ ba benchmark nguồn. Quyền code MIT; request-set benchmark/databases theo CC BY-SA4.0 trong DATA_LICENSE.md. Chưa download cached model examples/outcomes.

Chia **theo database trước**, dựa metadata và hash trong từng nguồn upstream:45development tasks/3DB,67validation tasks/3DB,92reserved-confirmation tasks/6DB. Chỉ ba DB development được tải và kiểm Git blob/SHA256/SQLite quick_check; prompt và reference packages lưu riêng. Chưa tải DB validation/confirmation hoặc chạy model/scorer upstream. [Receipt và giới hạn](relational_v5_external_preparation.json).

Đây là **chuẩn bị split**, chưa là preregistration hay thành tích trên204task. Các choice templates/generator có thể cùng xuất hiện giữa các DB: source-disjoint không tự là choice-family-disjoint hoặc independent-benchmark transfer. BIRD/Spider/LiveSQL có thể có trong dữ liệu huấn luyện model. Khi thiết kế confirmation phải báo các hạn chế này và cân nhắc thêm một workload độc lập thực sự.

DAB được tiến thêm một bước: đọc/pin dataset manifest và downloader để biết tài sản lớn thực sự nằm đâu; chưa chạy downloader, tải DB hoặc xác minh license từng nguồn, nên chưa nhận DAB là ready benchmark. Không dùng leaderboard tuned/hinted làm comparator ngang điều kiện.

Để tránh scope bị co về một field hoặc một loại bảng:

- Lỗi: binding thuộc tính, filter/population, join/grain/multiplicity, aggregate/unit/time, output và trạng thái kiểm chứng.
- Nguồn: giữ schema/database mới; phép thử chuyển workload phải ghi phần mapping do người làm.
- Hệ: strong single, single+cùngchecker/tools và multi-agent+cùngchecker; nhiều backbone khi đủ điều kiện.
- Sản phẩm: một workflow chính có người dùng thật trước, sau đó thử transfer; không xây nhiều demo để thay đánh giá.

Checker V5 hiện chỉ hỗ trợ flat SELECT/simple INNER join và một số aggregate. **Thesis scope không được đồng nhất với coverage hiện tại của implementation.** Bước qualification phải báo tỷ lệ không hỗ trợ trên toàn development pool trước khi chọn pilot; unsupported không được âm thầm loại khỏi denominator.

## 6. Plan thực nghiệm tiếp theo

| Giai đoạn | Công việc cụ thể | Điều kiện qua |
|---|---|---|
| A — oracle và interface | Đọc đủ native scorer dependencies; kiểm reference self-consistency/negative controls trên45development tasks; map fields/operators cần thiết và ambiguity. Chỉ mở development data, giữ validation/confirmation khi chưa cần. | Có evaluator qualification và coverage report; upstream labels có phạm vi rõ. Không sửa gold theo model output. |
| B — baseline readiness | Single mạnh hoàn thành native tasks; single+cùngtools/checker, self-review, cross-review. Kiểm context/length/output floors; bổ sung frontier khi quota hoạt động. | Có đủ completed trajectories để phân biệt inference/harness floor với lỗi cơ chế. Cùng cap chưa đủ, phải báo actual tokens/time. |
| C — cơ chế với controls | Cùng actual draft; cùng contract access. So full-context/no-message, neutral recheck, diagnostic đúng và shuffled diagnostic; ablate schema retrieval và structured handoff. | Freeze component, prompt, grouping, budget, endpoint và sample-size analysis trước calls. Tính cả chi phí tạo/kiểm contract và bản nháp. |
| D — confirmation | Khóa policy; mở nguồn/schema đã reserve, không tuning theo kết quả. Nếu chỉnh policy thì bộ đó thành development, cần reserve mới. | Đo correct completed work, rescue/harm, false stop, coverage và total cost theo source/task clusters. Không báo mọi halt/abstain là success. |
| E — workflow thực | Discovery5–8người làm báo cáo/phân tích; một artifact được phép dùng; thử đối chứng và chấm độc lập, cân bằng thứ tự task. | Có dữ liệu về lỗi cuối và tổng thời gian làm+kiểm, không chỉ satisfaction. Hiện chưa tuyển người. |

Primary endpoint nên là **task hoàn tất đúng theo yêu cầu đã được xác định**, cùng báo cáo những cách hiểu còn mở. Có checker đúng nhưng không tạo được đầu ra vẫn là công việc chưa hoàn tất. False-stop và người phải xử lý thêm là chi phí, không thể biến thành protection gain.

Chưa chốt số lượng model calls hoặc ngưỡng effect bằng một con số tùy ý. Sample size cần từ variance/disagreement theo source clusters và mức lợi ích thực tế do workflow quyết định. Sáu task V4 chỉ là development, không đủ để ra confirmatory sample-size estimate.

## 7. Việc đã làm ngay trong V5

`src/repguard/verification/relational.py` là lõi chung, không chứa task269/380/...; bindings cụ thể nằm ngoài lõi trong developer contracts. Nó kiểm nguồn thực sự của column, vai trò filter/join và output operators; không xem việc đọc một field là đã dùng đúng field đó. Schema search có thể tìm columns trong SQLite; receipts bind query/contract/catalog và được re-audit khi bàn giao. Những phần chưa hỗ trợ trả unresolved. Các contract phát triển đều `development_only`, không được tự nâng thành independent approval.

Có integration với source tools và CLI; mọi static receipt vẫn `execution_verified=false`, `semantic_truth_certified=false`. Wrapper ghi actual execution riêng, không biến nó thành chứng nhận đúng nghiệp vụ. Cả20query cũ được chạy lại, không tự sửa query hoặc nâng score. [Kết quả triển khai](RELATIONAL_V5_RESULTS_VA_QUYET_DINH.md), [API và cách chạy](../../../src/repguard/verification/RELATIONAL.md).

History/reputation tiếp tục đóng. Bước tiếp theo có giá trị nhất là **qualification45development tasks và baseline/coverage**, rồi mới mở mechanism experiment có thể quy nguyên nhân. Không cần đợi tuyển được users để làm qualification; user study vẫn phải có người thật và không được thay bằng mô phỏng.
