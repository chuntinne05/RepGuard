# RepGuard — Báo cáo cập nhật tiến độ

**Nhóm:** Tín và Trung  
**Ngày cập nhật:** 10/11/2026  
**Kỳ báo cáo:** sau bản trình bày 27–28/10 đến 10/11/2026.

## 1. Tóm tắt điều cần báo cáo

Nhóm tiếp tục nghiên cứu độ tin cậy của hệ đa tác tử, tập trung vào công việc **phân tích dữ liệu và lập báo cáo có thể kiểm chứng**. Sau báo cáo trước, nhóm đã hoàn tất **1.265 lượt phản hồi mô hình mới trong bốn bối cảnh đánh giá**, phân tích lỗi trên workspace có dữ liệu thật, triển khai một lớp kiểm ràng buộc và chuẩn bị nguồn đánh giá theo database chưa dùng để phát triển. Các lượt phản hồi không tương đương 1.265 nhiệm vụ độc lập.

**Kết quả nghiên cứu chính:** các thử nghiệm hiện tại chưa xác nhận việc đổi sang mô hình khác để phản biện tốt hơn tự kiểm. Vòng mới nhất còn cho thấy tự kiểm đạt điểm cao hơn kiểm chéo trên tập phát triển. Vì vậy, nhóm chuyển trọng tâm thử nghiệm sang câu hỏi cụ thể hơn: **thông tin kiểm chứng nào phải được giữ và kiểm lại khi các tác tử bàn giao kết quả, để sửa đúng hơn mà vẫn hoàn thành công việc?**

**Kết quả kỹ thuật chính:** đã có component kiểm query, nguồn dữ liệu và ràng buộc đầu ra; trạng thái “đạt”, “vi phạm”, “chưa đủ căn cứ” được tách riêng. Có 29 kiểm thử mới, 87 kiểm thử hồi quy trong phạm vi liên quan đã đạt; 20/20 SQL lịch sử tái tạo đúng bytes đầu ra. Đây là bằng chứng triển khai và tái lập, chưa phải bằng chứng phương pháp làm tăng độ chính xác.

## 2. Mốc xuất phát và phần mới trong kỳ

Báo cáo 27–28/10 đã trình bày reputation/ECRT, MMLU-Pro và các vòng repair cũ. Khi đó chưa có bằng chứng ổn định rằng reputation cải thiện hơn đối chứng; phép thử EvalPlus mới ở bước chuẩn bị, chưa chạy. **18.064 phản hồi MMLU-Pro và 560 phản hồi repair cũ không được tính lại vào tiến độ mới.**

Trong kỳ này, nhóm bổ sung bốn bối cảnh từ kiểm bằng chứng văn bản đến thực thi truy vấn trên database. Mục tiêu là hiểu cơ chế lỗi và xây nền đánh giá đáng tin trước khi tiếp tục học reputation hoặc mở rộng số tác tử. Tên đề tài chính thức chưa được đổi; hướng làm việc dưới đây cần được trao đổi với GVHD.

## 3. Những thực nghiệm đã hoàn tất

| Bối cảnh | Dữ liệu và số phản hồi mới | Kết quả có ý nghĩa | Hàm ý |
|---|---|---|---|
| Kiểm mức đủ bằng chứng | 120 cặp claim–passage, 24 nhóm claim; **720 phản hồi** | Chênh lệch kiểm chéo − tự kiểm: **+2,08 điểm %**, CI95% **[−0,42; +4,59]**. Không đạt ngưỡng quyết định đã đăng ký. | Chưa đủ bằng chứng về lợi ích ổn định của kiểm chéo. Nhãn đánh giá mức đủ của passage, không phải sự thật của claim ngoài nguồn. |
| Hỏi đáp báo cáo tài chính, ARQA | 24 câu hỏi/24 nhóm nguồn thuộc một issuer, hai cấu hình prompt; **288 phản hồi** | Đối chiếu chính: **+2,08 điểm %**, CI95% **[−4,17; +8,33]**. Hậu kiểm phát hiện vấn đề cần thẩm định về precision, đơn vị và phạm vi câu hỏi. | Cần làm rõ chuẩn chấm ngữ nghĩa; tính đúng số học chưa đủ. Giữ nguyên điểm đã khóa. |
| Workspace dữ liệu, DataSpace đã thích nghi | 6 task thuộc bốn nhóm nguồn có chồng lấp, 36 trajectory; **113 phản hồi** | **9** đầu ra khớp reference; **14** có đầu ra nhưng không khớp strict relation; **13** chưa có artifact cuối. | Phải phân biệt lỗi hiểu dữ liệu, lỗi hình dạng đầu ra và chưa hoàn tất. Đây là tổng hợp chẩn đoán kỹ thuật từ hai block, không phải nghiên cứu xác nhận sáu task liền mạch. |
| SQL theo yêu cầu diễn giải, SpecBridge | 12 task development/3 database, mỗi task hai cách hiểu đã chỉ định, thành 24 trường hợp; **144 phản hồi** | Direct A/B: **18/24, 19/24**. Tự kiểm AA/BB: **21/24, 21/24**. Kiểm chéo AB/BA: **19/24, 20/24**. | Trong pilot này, kiểm chéo thấp hơn tự kiểm trung bình **6,25 điểm %**, chỉ là mô tả trên development. Chưa đánh giá hiệu quả lớp kiểm V5. |

A = Qwen3.5:27b; B = Gemma4:26b. AA/BB là tự kiểm; AB/BA là mô hình sau kiểm lại bản làm thật của mô hình trước. Hai lượt gọi là cùng trần số lần gọi, chưa đồng nghĩa cùng chi phí tính toán. Không gộp accuracy giữa các bối cảnh thành một con số chung.

Vòng SpecBridge được thu xong ngày 09/11 và chấm offline ngày 10/11: kiểm toán receipt **PASS**, **144/144** execution record được tái lập; 143 phản hồi đúng schema, 133 SQL chạy được, 10 SQL lỗi và một phản hồi sai schema. Không phát sinh lượt gọi mô hình mới khi chấm báo cáo. Các biến thể của cùng một task có phụ thuộc; chưa có kiểm định xác nhận trên nguồn giữ lại.

## 4. Ba insight làm thay đổi cách thiết kế hệ thống

**Một là, truy vấn chạy được vẫn có thể dùng sai thuộc tính.** Với yêu cầu tìm người quản lý quỹ không mang quốc tịch Trung Quốc, một số đầu ra dùng tên người/tên quỹ làm đại diện cho quốc tịch. Nguồn có trường `Nationality` trong bảng thông tin cá nhân nhưng cần đúng liên kết. Đây là case phát triển đọc lại từ nguồn, chưa được người độc lập gán nhãn ngữ nghĩa.

**Hai là, câu hỏi mơ hồ khiến một reference chưa đủ để kết luận sai nghiệp vụ.** Task “fund abbreviation” có hai cột `SecuAbbr` và `ChiNameAbbr`; chúng khác nhau ở 12.787/12.962 hàng. Nhóm giữ hai cách hiểu để thẩm định, không chọn lại reference theo đầu ra của mô hình.

**Ba là, lỗi định dạng cần tách khỏi lỗi nội dung.** Một task trả đúng chuỗi tên và thứ tự nhưng thừa cột ID nên không khớp phép chấm strict relation. Bỏ cột ID trong phân tích hậu nghiệm thì khớp; điểm chính ban đầu vẫn giữ nguyên. Ngược lại, không nộp artifact cuối vẫn là chưa hoàn thành công việc.

Các ví dụ gợi ý cần kiểm rõ **thuộc tính, phạm vi, cách hiểu và đầu ra yêu cầu** trước khi quy mọi khác biệt điểm số cho năng lực phối hợp tác tử. Chúng không chứng minh đây là hiện tượng mới trong literature.

## 5. Hệ thống đã xây thêm

Lớp relational verification nhận ràng buộc và catalog do phía hệ thống quản lý, kiểm query có dùng đúng nguồn/column, phép lọc, join, group, order và giới hạn đầu ra trong SQL subset đang hỗ trợ hay không. Kết quả gồm **met / violated / unresolved**; những phần chưa hỗ trợ được giữ ở trạng thái chưa đủ căn cứ.

Khi bàn giao, hệ thống kiểm lại query, contract, catalog và bằng chứng thực thi; một nhãn “đã kiểm” do agent tự khai không đủ để được chấp nhận. Source tools hỗ trợ tìm schema, thực thi chỉ đọc và ghi nhận artifact thực tế.

- **29 tests mới; 87 scoped tests PASS.** Chưa chạy toàn bộ test suite của repository trong lượt triển khai này.
- Kiểm lại toàn bộ **36 trajectory V4**, gồm 20 SQL cuối, 13 trường hợp không có artifact cuối và ba đầu ra từ PDF. Không ép PDF thành bằng chứng SQL.
- **20/20 SQL** chạy lại cho đúng bytes lịch sử. Không có nghĩa 20/20 đáp án đúng yêu cầu.
- Contract hiện do nhóm phát triển, chưa được thẩm định độc lập; các receipt phát triển vẫn cần review. Component chưa được dùng làm can thiệp trong pilot SpecBridge.

## 6. Nền đánh giá cho bước tiếp theo

Nhóm đã pin nguồn SpecBridge gồm **204 task được upstream chấp nhận trên 12 database**, tách metadata theo database thành **45 development / 67 validation / 92 reserved**. Đây là nhãn upstream, không phải nhãn mới do nhóm tạo. Chỉ ba database development đã tải và kiểm dữ liệu; validation/reserved chưa chạy.

Trên toàn bộ 45 task development, đã qualification **90 reference SQL**: 90/90 khớp cách hiểu tương ứng; cả 90 reference của cách hiểu đối lập bị loại; kiểm soát thêm hàng và thiếu đầu ra đều bị loại. Đây là kiểm tra bộ chấm, **không phải độ chính xác mô hình**.

Một task thay đổi kết quả chấm giữa SQLite 3.42 và 3.51, nên native executor được khóa ở 3.42. Đồng thời, **74/90 reference có CTE/nhiều scope**, vượt khả năng phân tích đầy đủ của checker V5 hiện tại. Cần báo và xử lý độ phủ trước khi thử hiệu quả checker trên nguồn này.

Split theo database chưa đảm bảo độc lập về generator/template và chưa loại trừ dữ liệu từng có trong huấn luyện. Chưa được kết luận đã chứng minh tính tổng quát.

## 7. Đóng góp mục tiêu và giới hạn hiện tại

Hướng đề xuất: **bảo toàn yêu cầu và bằng chứng qua bàn giao trong hệ đa tác tử phân tích dữ liệu/báo cáo**. Những công trình gần như SpecBridge, Trace Integrity và Maat đã có các thành phần về diễn giải, execution contracts và handoff validation. Nhóm không nhận các thành phần này là novelty riêng.

Đóng góp cần hướng tới gồm: **(C1)** bộ lỗi có thể truy về nguồn và được thẩm định; **(C2)** công cụ kiểm/bàn giao tái lập, có trạng thái chưa xác định rõ; **(C3)** bằng chứng có đối chứng về lợi ích riêng của cơ chế trên nguồn mới và một workflow có người sử dụng. Hiện C1 có dữ liệu phát triển nhưng chưa có human adjudication; C2 có implementation và kiểm thử; C3 chưa được chứng minh.

Chưa có baseline frontier mạnh, replication phương pháp gần, xác nhận nguồn giữ lại, phỏng vấn hoặc thử nghiệm người dùng. Chưa đo giảm thời gian kiểm báo cáo, lợi ích doanh nghiệp hay USD savings. **History/reputation learner chưa được mở lại.**

## 8. Phân công đề xuất cho đợt tiếp theo

| Phụ trách | Công việc | Đầu ra bàn giao |
|---|---|---|
| **Tín** | Mở rộng/đo SQL coverage; hoàn thiện baseline single mạnh, tự kiểm và kiểm chéo cùng tools/checker; chuẩn hóa log nguồn, tokens và thời gian. | Báo cáo coverage; baseline table tái lập; harness sẵn để khóa protocol. |
| **Trung** | Đọc nguồn độc lập, soạn rubric và thẩm định các case mơ hồ; đối chiếu prior gần với đúng claim; tìm và trao đổi với người làm phân tích/báo cáo. | Phiếu review và danh sách bất đồng; bảng contribution–prior; workflow thực tế cùng tiêu chí chấp nhận. |
| **Cả hai** | Review chéo, giải quyết bất đồng; khóa cơ chế/controls/endpoint trước khi chạy; sau đó mới mở nguồn giữ lại. | Protocol và quyết định go/no-go được thống nhất; bảng đúng việc, sửa/hại, dừng sai, coverage và tổng chi phí. |

Thứ tự thực hiện: **làm rõ measurement và coverage → thử cơ chế cùng điều kiện → xác nhận nguồn mới → pilot người dùng**. Cơ chế cần so với neutral recheck, diagnostic đúng và diagnostic xáo trộn; tất cả được cấp cùng nguồn và checker. Cỡ mẫu/ngưỡng hiệu quả phải chốt trước khi đọc outcome, dựa trên mức lợi ích thực tế và phụ thuộc theo task/source.

Nội dung xin ý kiến GVHD: phạm vi analytics/reporting có phù hợp không; contribution nên ưu tiên bằng chứng cơ chế và tính tái lập như trên hay cần điều chỉnh; tiêu chí thực tiễn nào đủ để lựa chọn workflow pilot. Không cam kết kết quả dương trước thực nghiệm.

## 9. Bằng chứng và tài liệu đối chiếu

- Mốc cũ: [handoff báo cáo 28/10](../2026-10-27/PRESENTATION_HANDOFF.md).
- [Vòng bằng chứng](../2026-11-09/VERIFICATION_CYCLE01_RESULTS_VA_QUYET_DINH.md), [ARQA](../2026-11-09/ARQA_CYCLE02_RESULTS_VA_QUYET_DINH.md), [workspace](../2026-11-09/WORKSPACE_V4_RESULTS_VA_PATH_TIEP.md), [relational V5](../2026-11-09/RELATIONAL_V5_RESULTS_VA_QUYET_DINH.md).
- [Kết quả SpecBridge mới, chấm offline 10/11](specbridge_v6_offline_results.json); plan `c1a873e7e660944f6b542767`, audit PASS, 144 lượt. Bản này sao chép nguyên bytes từ `results/specbridge_v6/offline_results.json` để lưu cùng báo cáo.
- [Qualification](../2026-11-09/specbridge_v6_qualification.json), [strategy và mức đã đọc literature](../2026-11-09/RESEARCH_STRATEGY_V5_VA_CONTRIBUTIONS.md).
- Nguồn upstream: [SpecBridge, revision đã pin](https://github.com/Xyc-arch/specbridge-artifact/tree/a51be850a113a6b7c0ada57ad3c7806c6c3f25a4). Các diễn giải literature trong báo cáo này kế thừa review đã lưu, chưa phải replication mới.

PDF `DACN_27_10_Group8.pdf` chỉ được dùng làm **mẫu thiết kế**. Không sử dụng nội dung nghiên cứu, tên tác giả hoặc logo trong PDF đó để mô tả đồ án RepGuard.
