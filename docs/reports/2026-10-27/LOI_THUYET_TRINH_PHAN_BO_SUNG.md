# Lời thuyết trình phần literature review và tiến độ

Tài liệu hỗ trợ tập nói cho ngày 28/10/2026. Tên mục tương ứng nội dung, không phụ thuộc số trang sau khi sắp xếp deck. Slide dùng tiếng Anh, phần nói dưới đây dùng tiếng Việt. Có thể dành khoảng 8–12 phút cho literature review, 5–7 phút cho tiến độ và phép thử tiếp theo, tùy thời lượng Thầy cho phép.

## 1. Literature review: bản đồ các hướng nghiên cứu

“Chúng em chia các công trình liên quan theo bốn câu hỏi thay vì liệt kê từng paper. Thứ nhất, lịch sử cho biết nên tin agent nào? Thứ hai, feedback quan sát đáng tin đến mức nào? Thứ ba, chọn agent và phân bổ ngân sách như thế nào? Thứ tư, execution và repair cung cấp được loại bằng chứng gì? RepGuard nằm ở giao điểm: biến feedback không hoàn hảo thành một ước lượng có ích cho quyết định.”

Giải thích thêm nếu được hỏi: một reputation score tổng quát không đủ để phân biệt agent đúng ở nhiệm vụ này nhưng sai ở nhiệm vụ khác. Ngược lại, chia quá nhiều task/skill khiến lịch sử trong mỗi nhóm quá ít. Borrowing là đánh đổi giữa thêm dữ liệu và đưa dữ liệu không phù hợp vào ước lượng. Việc cân relevance không tự xử lý được nhãn sai.

## 2. Reputation và skill-conditional trust

“Nền tảng cổ điển là Beta Reputation System. Khi quan sát thành công và thất bại nhị phân, ta cập nhật hai tham số alpha và beta. Điểm mạnh là diễn giải được lượng bằng chứng và độ bất định. Nhưng nếu một feedback ‘đúng’ thực ra là false positive, việc đếm thẳng nó thành một thành công sẽ làm sai reputation.”

“Credibility Scoring đưa lịch sử đóng góp vào trọng số tổng hợp của một nhóm LLM. Công trình Skill-Conditional Trust đặt niềm tin theo kỹ năng, đồng thời nghiên cứu khi nào chuyển bằng chứng giữa các skill có lợi. Paper cũng chỉ ra borrowing có thể trở thành đường laundering. Vì thế chúng em không coi reputation theo task hay cross-task borrowing là ý tưởng mới.”

Phân biệt khi giải thích: adversarial agent, sai do năng lực và sai do evaluator là các cơ chế khác nhau. Không suy kết quả chống adversary thành bảo đảm trước mọi loại feedback noise. RepGuard cần kiểm tra riêng reliability của feedback và relevance của lịch sử.

Nguồn: [Jøsang & Ismail, 2002](https://www.mn.uio.no/ifi/english/people/aca/josang/publications/ji2002-bled.pdf); [Ebrahimi et al., IJCNLP-AACL 2025](https://aclanthology.org/2025.ijcnlp-long.90/); [Xia & Wang, 2026, preprint](https://arxiv.org/abs/2606.14200).

## 3. Feedback reliability và gold audit

“LLM-as-a-Judge giúp có proxy feedback rẻ và mở rộng quy mô đánh giá, nhưng judge có thể thiên lệch. Calibration nghiên cứu ý nghĩa của xác suất: trong các trường hợp được dự đoán 80% đúng, tần suất đúng có gần 80% không? Brier đo sai số xác suất. Tuy nhiên, xác suất chính xác hơn chưa chắc đổi thứ hạng agent, và thứ hạng không đổi có thể dẫn đến cùng đáp án cuối.”

“Prediction-Powered Inference kết hợp nhiều prediction với một lượng nhãn gold để sửa bias trong ước lượng thống kê. Active Statistical Inference nghiên cứu việc chủ động chọn nhãn. Điểm liên hệ là gold audit không chỉ để tính accuracy cuối cùng mà còn để học mức đáng tin của proxy. Tuy nhiên, bảo đảm cho một ước lượng trung bình không tự trở thành bảo đảm cho chính sách routing thích nghi.”

Nếu bị hỏi novelty: “Chúng em không nhận gold audit hay bias correction là mới. Chúng em cần chứng minh phần thiết kế cụ thể tạo lợi ích quyết định khi cùng thông tin và cùng chi phí.”

Nguồn: [Zheng et al., 2023](https://arxiv.org/abs/2306.05685); [Guo et al., ICML 2017](https://proceedings.mlr.press/v70/guo17a.html); [Angelopoulos et al., PPI](https://arxiv.org/abs/2301.09633); [Zrnic & Candès, Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html).

## 4. Routing và ngân sách

“Routing hỏi nên giao query cho model nào. Best-arm identification hỏi nên dùng ngân sách quan sát như thế nào để chọn arm tốt. Sequential Halving là đối chứng quan trọng vì rất đơn giản nhưng tập trung ngân sách dần vào các ứng viên còn lại. RouteLLM học router giữa model. R2-Router mở rộng quyết định sang cả model và độ dài đầu ra, nên so sánh chỉ đếm số call có thể chưa đủ công bằng.”

“Với RepGuard, phải ghi chi phí thu history, số gold label được mở, model call, output token và execution. Nếu một policy tăng accuracy bằng cách dùng gấp đôi call, ta phải so với baseline được cấp ngân sách tương ứng.”

Không trộn bài toán: một agent tốt nhất toàn cục khác với agent tốt nhất cho từng query. `infra/modal/paired_history_modal.py` là worker replay trên archive, không phải collector sinh response LLM mới và không tự chứng minh contextual routing.

Nguồn: [Karnin et al., ICML 2013](https://proceedings.mlr.press/v28/karnin13.html); [RouteLLM](https://arxiv.org/abs/2406.18665); [R2-Router, ICML 2026](https://proceedings.mlr.press/v306/xue26h.html).

## 5. Các công trình gần nhất cần so sánh trực tiếp

“Có ba công trình làm thu hẹp claim novelty khá rõ. BAI với LLM judges và limited human audits đã xét proxy bị bias theo arm/context, sửa bằng audited residual có propensity adjustment và dùng confidence sequence. SaveRouter đã xét thu feedback chọn lọc, chia sẻ thông tin giữa query liên quan và chi phí giám sát ban đầu. RouteGuard nhấn mạnh complementarity và AUC chưa đủ để suy ra gain triển khai, đồng thời cho thấy đơn vị resampling ảnh hưởng kết luận.”

“Do đó, phần mới chưa thể là ‘chúng em thêm audit’, ‘chúng em borrow evidence’ hay ‘chúng em đo headroom’. Claim cần hẹp hơn và phải qua đối chứng: trong setting feedback lồng nhau, liệu estimate có điều kiện trên trạng thái verification giúp chọn teammate hoặc audit hiệu quả hơn hay không?”

Caveat: các paper 2026 ở đây là preprint theo phiên bản đã kiểm tra. Thực nghiệm BAI là numerical/synthetic theo phần đánh giá của paper, không được mô tả như đã chứng minh hiệu quả trên archive RepGuard. Bảo đảm của RouteGuard phụ thuộc lớp chính sách và giả định của paper. Chưa có replication ba phương pháp trên cùng dữ liệu của dự án.

Nguồn: [Ao et al., BAI, 2026](https://arxiv.org/html/2601.21471v1); [Lai et al., SaveRouter, 2026](https://arxiv.org/abs/2609.37402); [Sun & Yang, RouteGuard, 2026](https://arxiv.org/abs/2608.07583).

## 6. Program execution và repair

“PAL và Program of Thoughts đưa phần tính toán sang chương trình, giảm phụ thuộc vào tính nhẩm bằng ngôn ngữ. Self-Refine dùng feedback để chỉnh sửa đầu ra. Các nghiên cứu về intrinsic self-correction cho thấy model không tự bảo đảm sửa được reasoning nếu thiếu tín hiệu bên ngoài đủ tốt.”

“Một chương trình chạy được chỉ chứng minh nó hợp lệ theo executor và tính được một kết quả. Nó vẫn có thể chọn nhầm hàng trong bảng, dùng gross thay cho net hoặc sai unit. Vì vậy chúng em tách executable rate khỏi exact-match, và tách sửa contract khỏi cải thiện reasoning hay reputation. Chẩn đoán trong ba cycle cho thấy so sánh khác contract có thể che khuất câu hỏi khoa học.”

Nguồn: [PAL, ICML 2023](https://proceedings.mlr.press/v202/gao23f.html); [PoT, TMLR 2023](https://arxiv.org/abs/2211.12588); [Self-Refine](https://arxiv.org/abs/2303.17651); [LLMs Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798).

## 7. Khoảng trống và câu hỏi của RepGuard

“Câu hỏi hiện tại của chúng em là: khi feedback chỉ xác nhận được một phần correctness, lịch sử và gold audit có giúp chọn agent tốt hơn ở cùng ngân sách hay không? Đại lượng quan tâm là correctness có điều kiện trên feedback, task và verification state. Chúng em sẽ đo xem thay đổi estimate có làm đổi quyết định và outcome, chứ không chỉ làm giảm Brier.”

“Đây là câu hỏi đang kiểm tra, chưa phải bằng chứng chúng em đã có phương pháp vượt trội. Các phần thành phần đều có tiền lệ. Nếu không có headroom hay kết quả không vượt baseline mạnh, chúng em giữ kết quả âm và xin Thầy chốt lại phạm vi đóng góp.”

## 8. Pipeline đã triển khai

“Ta có response, feedback quan sát, độ tin cậy của feedback, mức liên quan của task và khối lượng bằng chứng. p là xác suất correctness ẩn được suy ra từ feedback. tau giảm trọng số của lịch sử xa task. m cho biết lượng bằng chứng quan sát. Cập nhật alpha bằng tổng tau nhân m nhân p, beta bằng tổng tau nhân m nhân một trừ p.”

Không gọi đây là exact Bayesian posterior cho mọi cơ chế noise: soft weighted Beta là mô hình/cách cập nhật trong implementation. Trọng số chuyển giao same/related/unrelated hiện là **1/0,5/0**, lựa chọn taxonomy cố định. Lower bound hiện dùng normal approximation, không phải quantile Beta chính xác và không phải bảo đảm an toàn. Không cần đưa mọi chi tiết này lên slide chính, nhưng phải trả lời đúng nếu Thầy hỏi.

## 9. Tiến độ đã kiểm chứng

“Chúng em đã có 18.064 response MMLU-Pro thật và ba repair cycle thu 560 response mới ngày 18 đến 20/10. Đây là số lượt suy luận, không phải số task độc lập. Chúng em đã chạy lại evaluator TAT-QA gốc và hai audit receipt/source/execution trong lượt review, khớp điểm chính thức. Test suite local trên máy hiện tại có 308 pass và một skip do Torch.”

“Hạ tầng và audit là phần đã hoàn thành. Method superiority và hiệu quả trên tập confirmation độc lập vẫn chưa được xác nhận. Số test pass là chất lượng kiểm tra phần mềm hiện có, không chứng nhận nhãn semantic hay mọi nhánh pilot.”

Nguồn: [verification_2026-10-27.json](verification_2026-10-27.json). Không dùng số liệu Windows cũ như kết quả hiện tại, không khẳng định trạng thái cloud live khi chưa truy vấn.

## 10. Kết quả chính và quyết định

“Ở MMLU, chênh lệch team accuracy khoảng +0,02 điểm phần trăm và khoảng tin cậy chứa 0. Ở cycle 1, history policy không hơn direct PoT sau khi đồng nhất cách đọc output, nhưng compute proxy cao hơn 13,6%. Ở cycle 3 unrestricted, union của pool đạt 20/24, bằng best fixed. Trong bank này, oracle selection cũng chưa hơn đối chứng tốt nhất.”

“Các kết quả đó chưa xác nhận lợi ích tăng thêm của reputation. Chúng em tìm thấy các bottleneck cụ thể, nhưng chưa có thực nghiệm cô lập để loại trừ thuật toán như một nguyên nhân. Vì thế bước tiếp theo là kiểm tra chất lượng setting trước khi đầu tư học policy.”

Không cộng hay so trực tiếp các tỷ lệ khác dataset, cohort, contract, model và sampling unit. Kết quả readout hậu kiểm chỉ là diagnostic, không thay điểm chính thức hay biến thành method gain.

## 11. EvalPlus: trạng thái chuẩn bị và cơ chế feedback

“EvalPlus mở rộng test để phát hiện code mà bộ test nhỏ bỏ sót. Đây là tiền lệ trực tiếp nên chúng em không gọi ‘pass test chưa chắc đúng’ là đóng góp mới. Trong phép thử đề xuất, B là pass basic tests, E là pass extended tests và F được định nghĩa là B AND E. Vì vậy khi B bằng 0 thì F bằng 0 theo định nghĩa. Khi B bằng 1, kết quả E vẫn còn chưa biết.”

“Hiện chúng em mới chuẩn bị 32 task, 96 basic inputs và 3.397 plus inputs. Chưa có model call hoặc program execution. Chúng em chưa biết trong pool này có đủ trường hợp B bằng 1 nhưng F bằng 0 hay không. Đó chính là điều pilot phải đo, không phải điều đã được ba cycle tài chính chứng minh.”

Extended tests cũng không chứng minh correctness toán học trên mọi input. Full-suite pass là outcome thao tác hóa của nghiên cứu, không phải correctness tuyệt đối. Chưa map overlap với MBPP200, chưa gọi split độc lập.

Nguồn: [Liu et al., EvalPlus, NeurIPS 2023](https://arxiv.org/abs/2305.01210), source inventory và source pin trong `docs/analysis/`.

## 12. Protocol và điều kiện dừng

“Đầu tiên là software preflight với canonical solutions, sandbox, timeout và special oracle. Sau đó pilot đo basic-pass reliability và headroom giữa oracle và best fixed. Chỉ khi có khả năng đổi quyết định thì mới khóa split và chạy đối chứng policy. Các baseline nhận cùng tools, budget, feedback và quyền dùng contract.”

“Chúng em sẽ báo success, rescue, harm, số audit label và cost ledger, kèm paired interval theo sampling unit phù hợp. Nếu nhiều câu cùng một report thì phải xét report-level clustering. Baseline tối thiểu gồm best fixed, raw feedback, uniform audits và Sequential Halving, đồng thời cần contextual learner với cùng thông tin để kiểm tra phần giá trị tăng thêm của reputation.”

Phân biệt các rate: `P(F=0|B=1)` là tỷ lệ pass cơ bản nhưng fail toàn bộ trong số basic-pass. `P(B=1|F=0)` là FPR nếu xem B như classifier cho F. `P(B=1,F=0)` là tần suất biến cố chung. Không dùng chung một tên mà bỏ mẫu số.

## 13. Giới hạn bằng chứng

“Repair pilot nhỏ, 24 context không đương nhiên là 24 report độc lập. Bốn annotation flags vẫn cần người đánh giá. Kiểm tra readout sau khi xem kết quả không trở thành confirmation. Kể cả 0 harm trên 24 quan sát, cận trên một phía 95% vẫn khoảng 11,73% nếu giả định độc lập. Vì vậy accuracy bằng nhau chưa đủ để nói an toàn.”

“Các kiểm tra này giúp chúng em giới hạn claim và xây protocol tiếp theo. Chúng em chưa có kết quả dương để hứa một phương pháp sẽ thắng, và cũng chưa có bằng chứng mọi hướng reputation đều không hiệu quả.”

## 14. Nội dung xin ý kiến Thầy

“Chúng em xin Thầy chốt giúp ba quyết định: endpoint chính và scope dataset, ngân sách pilot với split tránh overlap, và tiêu chí GO/STOP trước khi thu response mới. Nếu setting này tiếp tục thiếu tín hiệu, chúng em muốn xin ý kiến về phạm vi kết quả đo lường hoặc hướng ứng dụng tài chính. Chúng em chưa tự coi đó là đóng góp thay thế đã được duyệt.”

Câu kết: “Mốc tiếp theo là chứng minh setting có đủ tín hiệu để lựa chọn tạo lợi ích đo được. Nếu vượt gate, chúng em mới kiểm tra phần đóng góp của policy bằng đối chứng công bằng.”

## Nguồn đầy đủ

[Literature review chi tiết](REPGUARD_LITERATURE_REVIEW_VA_BAO_CAO_TIEN_DO.md), [49 nguồn sơ cấp](references.json), [đối chiếu báo cáo tuần](CANVA_REVIEW_VA_DINH_CHINH.md). Các citation trên được diễn giải lại; không có trích dẫn dài nguyên văn.
