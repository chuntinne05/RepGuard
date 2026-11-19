# Hướng mở rộng: kiểm chứng cho các workflow phân tích và báo cáo bằng multi-agent

> Đã có bước triển khai và113modelcalls tiếp theo: [workspace v4 — kết quả và path](WORKSPACE_V4_RESULTS_VA_PATH_TIEP.md), [literature bổ sung](WORKSPACE_V4_LITERATURE_VA_RESEARCH_QUESTION.md). Các mục trạng thái nguồn/0newcalls bên dưới mô tả snapshot V3 trước pilot, không phải trạng thái mới nhất.

09/11/2026. Theo yêu cầu mở rộng ứng dụng; đây là strategy và implementation tiếp theo. Không thay primary/gold của hai vòng đã chạy, không coi prototype mới là phương pháp đã thắng benchmark.

**Đề xuất chốt hướng làm tiếp:** RepGuard hỗ trợ kiểm chứng đầu ra của hệ đa tác tử trong công việc **đọc dữ liệu → phân tích/tính toán → tổng hợp báo cáo → kiểm tra và sửa**. Tài chính là một workload để thử transfer. Lõi dùng chung xử lý lỗi sai nguồn, sai chỉ tiêu, kỳ, nhóm đối tượng, scale và trạng thái thực thi.

**Tên làm việc:** “Kiểm chứng và điều phối sửa lỗi dựa trên bằng chứng trong hệ đa tác tử cho phân tích dữ liệu và báo cáo”. Chưa đổi tên đề tài được GVHD phê duyệt. Không bắt buộc giữ ECRT/DART là method chính; history là nhánh có điều kiện sau khi thấy action utility.

## 1. Rộng ở đâu, ý nghĩa cụ thể là gì?

|Nhóm công việc|Ví dụ cần kiểm|Lỗi chung mà lõi có thể đối chiếu khi có metadata đáng tin|Trạng thái bằng chứng của đồ án|
|---|---|---|---|
|Phân tích vận hành/bán hàng|“Tỷ lệ giao hàng đúng hạn là95%”|Lấy đơn đã gửi thay đơn đã giao; mẫu số chỉ gồm một vùng; nhầm tuần; percent/fraction|Đã chạy engineering fixtures; chưa có task/user validation thật|
|Báo cáo thí nghiệm/nghiên cứu/phần mềm|“Model A đạt80% trên test, run đã hoàn tất”|Lấy dev thay test, model/run khác, số lần gọi thay số task, submitted thay completed|Đã replay5claim từ artifacts thật của dự án; chưa là external generalization|
|Báo cáo tài chính/doanh nghiệp|“Doanh thu tăng12%, sau điều chỉnh”|Sai kỳ/chỉ tiêu, production vs sales, tổng segment vs consolidated, scale tiền|Hai vòng model thật đã chạy; gate chưa qua và oracle còn cần semantic review|
|Theo dõi workflow thực thi|“Job đã chạy thành công và có đầu ra”|Log chấp nhận request bị dùng làm chứng cứ hoàn tất; snapshot quá hạn|Có status lookup và engineering fixtures; chưa có live integration|

Đây là cùng một vấn đề kiểm chứng ở nhiều nơi, không cần xây bốn ứng dụng riêng. Mục tiêu sản phẩm là giúp người nhận báo cáo lần về đúng dữ liệu và biết phần nào cần kiểm thêm. **Impact phải đo bằng lỗi cuối, công việc hoàn thành và thời gian soát**, chưa thể suy từ số module hoặc số use cases liệt kê.

Phạm vi đầu tiên hỗ trợ claim có giá trị cấu trúc, phép tính rõ hoặc trạng thái xác định. Với văn bản tự do/cause-effect, cần semantic verifier hoặc người thẩm định; kernel hiện tại không tự hiểu mọi loại claim.

## 2. Nghiên cứu gần làm thay đổi đề xuất thế nào?

|Nguồn chính thức, độ đọc|Điều đã được làm|Cách dùng đúng trong đồ án|
|---|---|---|
|[ProvenanceGuard,16/06/2026](https://arxiv.org/html/2606.18037v1), đọc trace interface, discussion/limitations|Kiểm support và source attribution riêng trên MCP traces; repair bị chấm lại bằng chính verifier có giới hạn|Không nhận giữ source IDs/NLI routing/repair-and-reverify là mới. Phải tách giá trị “đúng nguồn” khỏi semantic correctness.|
|[Beyond fabrication,28/10/2026](https://arxiv.org/html/2610.38691v1), đọc phương pháp và limitations|Số có thể có thật nhưng thuộc experiment/metric/run khác; checker provenance và nhãn người trên một benchmark nghiên cứu|Research reporting là workload có động lực rõ; không nhận claim-to-run binding là phát minh. Phải kiểm transfer và nhớ provenance không chứng nhận experiment đúng.|
|[MMEnterprise-Bench,21/10/2026](https://mlv.kaist.ac.kr/MMEnterprise-Bench/), đọc project/task/construction/protocol|Xung đột nguồn/thời gian và không đủ bằng chứng trong records công việc được mô phỏng; website vẫn ghi dataset/toolkit coming soon|Cho thấy scope rộng hơn finance; chưa đưa vào danh sách benchmark sẵn chạy. Không coi dữ liệu mô phỏng là nhu cầu được xác nhận.|
|[DataSpace,04/08/2026](https://arxiv.org/html/2608.03451v1), đọc construction/human review/evaluation; inspect source scorer|Workflow nhiều loại file, task-specific precision/unit/row semantics; source manifest410task nhưng60public references|Là nguồn external-preflight ưu tiên. Scorer table equality không tự chấm correctness của reasoning/attribution; không gọi410task là410ca tự chấm được.|
|[DAB,21/03/2026](https://arxiv.org/html/2603.20576v1), đọc benchmark/formative overview và README repo mới|54queries,12datasets,9domains, nhiều DB và biến đổi dữ liệu|Nguồn bổ sung cho analytics; phải kiểm dependencies, điều khoản từng dataset và validators trước dùng. Không so leaderboard có prompt/hints/task tools khác nhau như cùng điều kiện.|
|[AgentWebBench,ICML2026](https://proceedings.mlr.press/v306/zhong26n.html), abstract chính thức|Điều phối giữa user agent và content agents qua interface truy cập phân tán|Multi-agent có thể hợp lý khi quyền truy cập/nguồn phân tán; roles chỉ có tên khác nhau chưa chứng minh bổ trợ.|

VeriFin/MoCA/CLAIR-Fin và các nghiên cứu handoff đã đối chiếu trước vẫn rất gần. Generic evidence contract, provenance graph, abstention và calculator không đủ làm novelty. [Đối chiếu trước](GAP_RECHECK_VA_CONFIRMATION_PATH.md).

## 3. Gap nào còn cần chứng minh?

**Vấn đề thực tế có căn cứ:** một đội agent có thể đồng thuận trên một con số có thật nhưng áp dụng sai vào câu hỏi. Nguồn trên nhiều workload cho thấy đây là vấn đề đáng nghiên cứu. **Novelty riêng của đồ án chưa được xác nhận.**

Giả thuyết tiếp theo: khi giữ task contract và source scope độc lập với draft, một cơ chế kiểm tra rồi chọn cách sửa có thể giảm harmful revision mà vẫn giữ khả năng hoàn thành task, và chuyển được sang workload chưa dùng thiết kế.

Ba câu hỏi cần trả lời:

1. Bao nhiêu lỗi thực sự là applicability/source/scope, bao nhiêu là arithmetic/schema, bao nhiêu là oracle ambiguity? Phải có nhãn độc lập và phân tích cả trường hợp checker từ chối đáp án đúng.
2. Team có cùng source tools, contract và ngân sách có làm hơn strong single + cùng checker không? Nếu gain đến từ checker/canonical units, ghi nhận là gain của checker; không nhận là coordination.
3. Một policy khóa trước trên nhóm workload phát triển có giữ lợi ích khi đổi nguồn/workload không? Bao nhiêu công sức mapping, human labels và tokens cần để đạt lợi ích đó?

Nếu khác biệt với prior art chỉ là thêm trường metadata hoặc prompt, đóng góp phù hợp là **đánh giá có kiểm soát + hệ thống tái lập + kiểm chứng tác dụng người dùng**. Chỉ đặt tên method mới sau khi có cơ chế khác biệt và ablation hỗ trợ. Chưa hứa bài báo hoặc điểm số khóa luận.

## 4. Implementation đã làm trong lượt này

Module mới: `src/repguard/verification/`, tách khỏi frozen experiments.

- **Task contract:** entity/metric/period/population/state, qualifiers như model/split/run, phép tính, unit và tolerance; approval từ host/user hoặc mapping đã kiểm, không do agent tự khai để được thông qua.
- **Evidence store:** fact IDs, source snapshot hash, locator, lineage roots và validity intervals; admission là trách nhiệm của host. Peer assertions không tự thành observed facts.
- **Candidate:** agent chỉ đề xuất value/unit và dẫn fact IDs. Không nhận expected value, approval hoặc scope mới qua schema này.
- **Engine:** kiểm applicability, conflicts, dimensions/scale và phép tính whitelist; `consistent / inconsistent / unresolved`. Unknown không bị đổi thành false. Không tự chọn record mới nhất hoặc lấy số phiếu làm truth.
- **Adapters:** scalar từ JSON pointer và đúng một hàng CSV theo khóa chính xác. Metadata mapping vẫn cần kiểm; hash chỉ ràng buộc bytes.
- **Multi-agent integration:** tối đa một reviewer callback sau draft; recheck bằng contract/store ban đầu. Chưa nối provider/retrieval mới, không có generation mới trong lượt này.
- **Receipt:** hashes của contract/candidate, facts/source snapshots/roots và lý do; luôn `semantic_truth_certified=false`. Nó không chứng minh đúng nghĩa câu hỏi, source completeness hoặc live state.

Các field approval/admission chỉ có giá trị khi host quản lý đúng trust boundary. Đưa file do agent tự tạo vào phần “trusted” sẽ phá giả định của API. Kernel không phải sandbox/cơ chế xác thực danh tính.

**Đã chạy:**38synthetic engineering cases thuộc4workload families,5recorded claims từ kết quả thật và2controlled mutations trên artifacts thật; đều cho kết quả kỹ thuật mong đợi. Có ca hai vòng thật cùng xấp xỉ+2,08pp nhưng dẫn nhầm run vẫn bị báo unresolved. Không báo45/45 như research accuracy hoặc external validation. [Run record](general_verification_v1_engineering_results.json).

25tests cho module mới pass. Một lượt regression trước thay đổi CSV có39tests pass gồm23kernel+5receipt+11ARQA; sau thêm CSV chạy lại25kernel pass. Đây không phải full repo suite. Oldv1/v2 source/score giữ nguyên.

## 5. Trạng thái nguồn external đã làm thật

[Preflight](cross_workload_source_preflight.json):

- DataSpace code pin `6491caa4c70cc06cacb6103ba73cefb00746abfe`, HF dataset pin `96be19257d7aa251dbce4771d46a26fc36f6dc52`. Đã tải/kiểm Git blob của task manifest455.975bytes:410unique tasks,60public-reference tasks,350reference withheld. Chưa tải gold files/model outputs. Source scorer được đọc, không import/run.
- Toàn bộ public manifest có CSV;189task có video. Public references có32task không video. Chọn6input metadata bằng hash để source inspection, **không là study sample đã đăng ký**; source lineage/content grouping chưa xác nhận.
- Release ZIP metadata khoảng2,88GB compressed, README mô tả15GB context. Đã đọc directory và12input files nhỏ của6candidate workspaces qua HTTP Range, tải3.980.118bytes; CRC của member được kiểm. Chưa tải/verify SHA256 full archive, chưa có workspace đầy đủ hoặc oracle validated. Đây là partial input inspection, không end-to-end task PASS hay benchmark score mới.
- DAB repo pin `3ce514f0a601569ab2ac3569542152423794a461`: đọc README/tree, chưa validate databases hoặc license cho mọi thành phần.

Các nguồn này không thay cho corpus thực tế của product hoặc nhóm người dùng. Lựa chọn source dựa task/availability, không dựa xem method có score đẹp.

## 6. Path tiếp theo, mỗi giai đoạn có điều kiện qua

|Giai đoạn|Làm cụ thể|Điều kiện chuyển bước|
|---|---|---|
|A. Khóa workload chính|Ưu tiên báo cáo phân tích/thí nghiệm của nhóm dữ liệu/phần mềm; tài chính và vận hành là transfer workloads. Discovery5–8người đang làm việc tương tự, dùng artifact công khai/được phép|Có một episode lặp lại, lỗi đáng ngăn, đầu ra và chuẩn thành công chấm được. Hiện0interviews|
|B. Source/oracle preflight|Inspect6candidate workspaces, kiểm scope/units/precision/join/row semantics và khả năng source-disjoint grouping. Hai người review task source-only rồi so oracle|Các trường mơ hồ được adjudicate; mapping/tolerance không dựng từ draft hoặc gold answer. Ghi công sức setup|
|C. Adapter + bounded pilot|Chốt một workload chính, primary comparator và error taxonomy. Baselines: strong single đủtools; single+cùngchecker; self-review; blind reviewer; cross-review; finalist. Freeze trước calls|Chỉ mở confirmation nếu có utility/headroom thực sau checker và same-info controls, không chỉ giảm coverage|
|D. Transfer confirmation|Freeze prompts/policy/thresholds; một workload/source không dùng design, source/company/run groups tách; stronger model-family control|Primary task utility dưới cùng trần tổng tài nguyên và false-accept target được hỗ trợ bằng group uncertainty|
|E. Product study|Dùng prototype đưa claim→source→checks→revision/review. Counterbalance task order, chấm output độc lập|Giảm thời gian hoàn tất đúng hoặc lỗi/review burden có ý nghĩa so workflow hiện tại/single baseline|

Không thay “task vừa khó vừa nhiều nguồn” bằng điều kiện method có lời giải oracle hoàn hảo. Partial evidence phải có nhãn unresolved và đo coverage. Không nhận0false accepts ở mẫu nhỏ là0risk. Cỡ mẫu confirmation phải từ paired group variance/minimal meaningful effect và mức risk đích; chưa khóa số cỡ mẫu khi chưa có pilot task đúng.

Để scale qua domain, tách domain adapters và metric definitions khỏi policy/engine; báo rõ phần nào tái sử dụng, phần nào con người cấu hình. Thử giữ nguyên logic và chỉ thay adapter/schema trong held-out workload; nếu cần chỉnh threshold/prompt theo outcomes thì chuyển bộ đó thành development, dành nguồn khác cho confirmation.

History/reputation chỉ mở khi có từ hai actions/reviewers với utility khác nhau và dự báo được. Phải thắng current-state learner cùng thông tin, fixed workflow và history shuffle dưới feedback budget giống nhau. Không thêm lịch sử chỉ để giữ tên đề tài ban đầu.

## 7. Việc cần ở người dùng và việc vẫn làm độc lập được

Tác giả cần kết nối người đang làm phân tích/báo cáo; có thể bắt đầu từ nhóm nghiên cứu, đồ án, thực tập dữ liệu hoặc phần mềm của trường. Họ cần có công việc thật lặp lại; bạn cùng lớp không làm workflow đó chỉ hỗ trợ usability. Chưa ai được liên hệ bởi assistant.

Assistant tiếp tục được source inspection, adapter development, receipt/error review và preparation mà không giả làm human annotators. Các gate cần judgment người thật vẫn được giữ rõ, không chặn toàn bộ engineering và cũng không bị bỏ qua để launch nhiều calls.
