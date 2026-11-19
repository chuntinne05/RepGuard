## Trang 01 — Agenda · Ảnh 01

Thưa thầy, hôm nay nhóm em cập nhật phần đã làm sau báo cáo cuối tháng mười: các thực nghiệm mới, công cụ kiểm chứng đã xây, và hướng kiểm tiếp theo.

Bài toán nhóm em đang làm là để AI lấy dữ liệu, thực hiện phân tích rồi giao lại một bảng kết quả hoặc báo cáo. Công việc được chia thành các vai trò: một agent tạo kết quả, một agent kiểm lại. Hai vai trò này có thể dùng cùng một mô hình hoặc hai mô hình khác nhau.

Vấn đề là người kiểm có thể đồng ý với một kết quả vẫn dùng sai dữ liệu. Vì vậy, nhóm em cần biết phải kiểm điều gì và bàn giao bằng chứng nào để bước kiểm lại có tác dụng.

Em sẽ trình bày bốn phần: nhóm đã chạy và xây được gì; kết quả cho thấy điều gì; câu hỏi nghiên cứu cần kiểm tiếp; cuối cùng là phân công cho em và Trung.

## Phần 1 — Work completed

### Trang 02 — What we have done since the last report · Ảnh 02

Sau báo cáo trước, nhóm em thu thêm 1.265 phản hồi mô hình trong bốn bối cảnh. Đây là số phản hồi, không phải 1.265 bài toán độc lập, vì một câu hỏi được chạy qua nhiều quy trình tạo và kiểm đáp án.

Vòng đầu có 720 phản hồi trên 120 cặp phát biểu và đoạn trích. Nhiệm vụ là xác định đoạn trích có đủ căn cứ để đánh giá phát biểu hay chưa. Vòng thứ hai có 288 phản hồi cho 24 câu hỏi về báo cáo tài chính, dùng hai cách hướng dẫn mô hình.

Sau đó, nhóm chuyển sang công việc có thao tác dữ liệu. Vòng làm việc với file có 113 phản hồi trên sáu nhiệm vụ. Ở đây, mô hình phải tìm dữ liệu, gọi công cụ và xuất bảng cuối. Vòng SQL mới nhất có 144 phản hồi trên 12 bài toán, mỗi bài có hai yêu cầu diễn giải đã chỉ định, thành 24 trường hợp.

Chuỗi thử nghiệm này giúp nhóm đi từ việc chấm một câu trả lời sang xem cả quá trình tạo ra nó: đã đọc nguồn nào, dùng trường nào và có hoàn thành đầu ra hay không.

Song song, nhóm đã xây một lớp kiểm cho truy vấn dữ liệu. Em sẽ giải thích phần này trước khi đi vào các kết quả so sánh.

### Trang 03 — Building checks into the handoff · Ảnh 06

SQL là câu lệnh dùng để lấy và tổng hợp dữ liệu trong cơ sở dữ liệu. Một câu SQL chạy được chỉ cho biết máy thực hiện được câu lệnh đó. Nó chưa bảo đảm câu lệnh đang trả lời đúng yêu cầu.

Checker trên slide là chương trình đối chiếu truy vấn với cấu trúc nguồn và bộ yêu cầu do hệ thống quản lý. Cấu trúc nguồn, hay schema, cho biết có những bảng, cột và liên kết nào. Bộ yêu cầu xác định những điều cần thỏa, chẳng hạn phải dùng trường quốc tịch để lọc người quản lý, thay vì suy quốc tịch từ tên.

Checker trả ba trạng thái. Met là thỏa ràng buộc đang kiểm. Violated là phát hiện vi phạm. Unresolved là chưa đủ khả năng hoặc căn cứ để kết luận. Một phần không kiểm được sẽ giữ ở trạng thái chưa rõ, thay vì tự coi là đã đạt.

Khi bàn giao, hệ thống kiểm lại truy vấn, nguồn và ràng buộc đã dùng. agent nhận sau cần biết kết quả nào đã được kiểm và kiểm theo yêu cầu nào; một nhãn “đã kiểm” do agent trước tự ghi chưa đủ.

Nhóm đã bổ sung 29 tests, tức các ca kiểm thử phần mềm, với những tình huống như đổi query, thay nguồn hoặc tự khai sai trạng thái kiểm chứng. Tổng bộ kiểm thử trong phạm vi liên quan có 87 tests đạt. Nhóm cũng chạy lại toàn bộ 20 câu SQL cuối đã lưu từ vòng làm việc với file; cả 20 tái tạo đúng dữ liệu đầu ra cũ, đến từng byte.

Con số 20 trên 20 chứng minh đầu ra có thể tái lập. Nó chưa nói 20 đáp án đều đúng yêu cầu. Luồng tạo query, nhận kết quả kiểm, sửa rồi chạy lại trên slide là bước tích hợp nhóm sẽ đo hiệu quả tiếp theo.

Để đo được việc đó, nhóm cần chuẩn bị cả bộ đánh giá và môi trường thực thi.

### Trang 04 — Preparing a broader SQL evaluation · Ảnh 07

Nhóm đã chuẩn bị nguồn SpecBridge gồm 204 bài toán trên 12 cơ sở dữ liệu.

Nhóm chia theo cơ sở dữ liệu: 45 bài để phát triển, 67 bài để kiểm tra phương án, và 92 bài giữ lại cho đánh giá cuối.

Trước khi chạy mô hình, nhóm kiểm bộ chấm bằng 90 câu SQL tham chiếu của phần phát triển. Cả 90 tạo ra kết quả được bộ chấm nhận đúng theo cách hiểu tương ứng. Khi dùng cách hiểu đối lập, thêm hàng hoặc thiếu đầu ra, các ca đối chứng đều bị loại. Đây là kiểm tra bộ chấm bằng lời giải tham chiếu, chưa phải điểm của AI.

Nhóm gặp một lỗi môi trường cụ thể: một bài thay đổi kết quả chấm giữa SQLite 3.42 và 3.51. SQLite là bộ máy thực thi SQL trong thử nghiệm này. Nhóm đã cố định phiên bản về 3.42, theo môi trường gốc, trước khi chạy mô hình, để khác biệt phần mềm không bị nhầm thành khác biệt phương pháp.

Phần còn vướng là độ phủ của checker. Có 74 trên 90 query tham chiếu dùng CTE hoặc nhiều phạm vi truy vấn. CTE là cách đặt tên cho một kết quả trung gian rồi dùng tiếp trong câu SQL. Checker hiện chưa kiểm đầy đủ các cấu trúc này; đây là phần cần mở rộng trước khi thử cơ chế trên nhiều bài toán hơn.

Đó là phần hệ thống và dữ liệu đã chuẩn bị. Tiếp theo là những kết quả khiến nhóm chọn hướng kiểm chứng hiện tại.

## Phần 2 — What we learned

### Trang 05 — Does using a different reviewer help? · Ảnh 03

Ở hai vòng đầu, nhóm so hai cách: để mô hình kiểm lại bản làm của chính nó, gọi là self-review; hoặc giao bản làm đó cho mô hình khác kiểm, gọi là cross-model review. Người kiểm được nhận bản làm thật và cùng nguồn bằng chứng.

Biểu đồ thể hiện điểm kiểm chéo trừ điểm tự kiểm, lấy trung bình hai hướng giữa Qwen và Gemma. Điểm dương nghiêng về kiểm chéo; điểm âm nghiêng về tự kiểm.

Cả hai nghiên cứu đều có ước lượng chênh lệch cộng 2,08 điểm phần trăm. Điểm phần trăm là hiệu giữa hai tỷ lệ: ví dụ từ 70% lên 72% là tăng hai điểm phần trăm.

Đường ngang là khoảng tin cậy 95%, được ước lượng bằng cách lấy mẫu lại theo nhóm dữ liệu. Nó thể hiện độ bất định của chênh lệch. Vòng bằng chứng có khoảng từ âm 0,42 đến dương 4,59; vòng hỏi đáp báo cáo có khoảng từ âm 4,17 đến dương 8,33. Cả hai đều đi qua mốc không.

Vì vậy, kết quả hiện tại chưa đủ rõ để nói đổi sang mô hình khác giúp kiểm tốt hơn. Riêng vòng đầu còn không đạt ngưỡng ba điểm phần trăm đã đặt trước khi chạy.

Nhóm giữ nhánh reputation ở trạng thái chưa mở rộng. Reputation ở đây là điểm tín nhiệm tích lũy từ lịch sử làm việc của agent. Nếu tín hiệu đánh giá và lợi ích của review còn chưa rõ, học thêm từ lịch sử chưa giải quyết được vấn đề nền này.

Nhóm tiếp tục đọc lỗi trong các nhiệm vụ có công cụ để biết bước kiểm đang thiếu thông tin gì.

### Trang 06 — What happened when agents worked with real files · Ảnh 04

Ở vòng làm việc với file, agent dùng bảng CSV, tệp JSON, cơ sở dữ liệu SQLite và tài liệu PDF. Một nhiệm vụ có thể cần nhiều lần gọi mô hình và công cụ trước khi có bảng cuối.

Nhóm lưu 36 lượt thực hiện trên sáu nhiệm vụ. Mỗi lượt lưu cả quá trình tìm nguồn, truy vấn và tạo đầu ra; đó là thứ nhóm gọi là trace. Các số trên slide được tổng hợp từ hai đợt thu dữ liệu để phân tích lỗi.

Có chín lượt nộp bảng khớp kết quả tham chiếu. Mười bốn lượt có bảng nhưng không khớp. Mười ba lượt chưa nộp được bảng cuối.

Ba nhóm này cần được xử lý khác nhau. Nếu agent đã hết ngân sách khi tìm dữ liệu, chúng em cần xem lại cách tìm nguồn và mức tài nguyên được cấp. Nếu đã nộp bảng, chúng em phải kiểm nó dùng sai thuộc tính, hiểu khác câu hỏi hay chỉ khác cấu trúc đầu ra.

Vì vậy, nhóm không lấy toàn bộ các trường hợp chưa khớp để gọi chung là lỗi suy luận. Phải lần lại trace trước khi quyết định nên sửa công cụ, làm rõ yêu cầu hay nhờ agent khác phản biện.

Ba trường hợp ở trang tiếp theo cho thấy sự khác biệt này rõ hơn.

### Trang 07 — Three cases we looked at more closely · Ảnh 05

Trường hợp đầu yêu cầu tìm người quản lý quỹ không mang quốc tịch Trung Quốc. Một số bản làm dùng tên người hoặc tên quỹ để suy ra quốc tịch. Trong nguồn lại có trường Nationality, tức quốc tịch, ở bảng thông tin cá nhân.

Để trả lời, truy vấn cần nối đúng bản ghi người quản lý với thông tin cá nhân. Phép nối bảng này gọi là join. Truy vấn dùng tên vẫn có thể chạy và trả nhiều hàng, nhưng điều kiện lọc không bám vào thuộc tính mà câu hỏi yêu cầu. Đây là loại kiểm tra field và join mà checker cần hỗ trợ.

Trường hợp thứ hai nằm ở cách hiểu câu hỏi. Yêu cầu chỉ nói “fund abbreviation”, tức tên viết tắt quỹ. Dữ liệu có hai cột SecuAbbr và ChiNameAbbr. Hai cột khác nhau ở 12.787 trên 12.962 dòng, nên chọn cột nào sẽ thay đổi gần toàn bộ bảng kết quả.

Ở đây, nhóm cần thẩm định yêu cầu từ nguồn trước khi gọi một cách hiểu là sai. Chúng em giữ hai cách hiểu để review, không chọn lại đáp án theo cột mà mô hình tình cờ trả ra.

Trường hợp thứ ba là đầu ra thừa cột. Chuỗi tên thủ tục và thứ tự khớp với bảng tham chiếu, nhưng có thêm cột ID. Bộ chấm đối chiếu cấu trúc bảng nên đánh không khớp. Khi phân tích hậu nghiệm, bỏ riêng cột ID thì khớp; điểm gốc vẫn giữ nguyên.

Các trường hợp này đang được dùng để phát triển và lập bộ tiêu chí kiểm tra. Một lỗi cần sửa cách dùng dữ liệu; một trường hợp cần làm rõ nghĩa; một trường hợp cần sửa cấu trúc bảng. Gộp chúng lại sẽ làm phép thử reviewer khó giải thích.

### Trang 08 — Self-review did better in the SQL pilot · Ảnh 08

Vòng SQL mới nhất là một pilot, tức vòng thử ban đầu, có 12 bài toán trên ba database. Mỗi bài được chạy với hai cách hiểu đã chỉ định, thành 24 trường hợp. Nhóm dùng hai mô hình: Qwen là A, Gemma là B.

Hai cột A và B là trả lời trực tiếp. AA và BB là tự kiểm. AB nghĩa là A tạo bản nháp, B kiểm lại; BA là chiều ngược lại. Reviewer nhận bản nháp thật cùng phản hồi thực thi query, nhưng không nhận đáp án tham chiếu.

Trả lời trực tiếp đạt 18 và 19 trên 24. Hai nhánh tự kiểm đều đạt 21 trên 24. Hai nhánh kiểm chéo đạt 19 và 20 trên 24.

Lấy trung bình hai hướng, tự kiểm đạt 87,5%; kiểm chéo đạt 81,25%. Chênh lệch là 6,25 điểm phần trăm, nghiêng về tự kiểm trong pilot này.

Các nhánh tự kiểm và kiểm chéo đều có trần hai lượt suy luận cho một quy trình. Các nhánh review dùng lại bản nháp đầu tiên; khi tính chi phí mỗi nhánh, nhóm vẫn tính cả bước tạo bản nháp. Chi phí thực cần tính bằng lượng đầu vào, đầu ra và thời gian chạy, vì hai mô hình không nhất thiết tiêu tốn như nhau.

Toàn bộ 144 phản hồi được lưu và kiểm toán; khi chấm lại, các bản ghi đầu ra và lỗi đều tái lập được. Tuy nhiên, đây chưa phải phép thử can thiệp bằng checker vừa giới thiệu. Nó cho biết baseline hiện tại — tức cách làm dùng để đối chiếu — đang đạt đến đâu.

Điều cần kiểm tiếp là thông tin đưa cho reviewer có giúp sửa đúng hơn hay không, thay vì chỉ đổi mô hình nhận việc kiểm.

## Phần 3 — Research direction

### Trang 09 — Where we take the research next · Ảnh 09

Câu hỏi nghiên cứu tiếp theo là: phản hồi kiểm chứng cụ thể có giúp agent sửa một phân tích tốt hơn việc chỉ yêu cầu nó kiểm lại hay không?

Phản hồi cụ thể ở đây cần chỉ ra vấn đề có thể hành động được. Với ví dụ quốc tịch, đó có thể là: query đang lọc theo tên; yêu cầu lại nói về Nationality, và cần kiểm liên kết sang bảng thông tin cá nhân.

Nhóm dự kiến giữ cùng bản nháp ban đầu và so ba điều kiện. Một là reviewer được yêu cầu kiểm lại nhưng không nhận chẩn đoán cụ thể. Hai là nhận kết quả kiểm phù hợp với bản nháp. Ba là nhận chẩn đoán đã xáo trộn, không tương ứng với lỗi của bản nháp đang xét.

Nhánh xáo trộn giúp kiểm xem mô hình hưởng lợi từ nội dung chỉ đúng lỗi, hay chỉ từ việc được đưa thêm một đoạn phản hồi. Các nhánh được cấp cùng nguồn, cùng quyền dùng công cụ kiểm và cùng trần ngân sách; chi phí tạo và kiểm phản hồi cũng phải được tính.

Nhóm sẽ đo bốn thứ: có hoàn tất đúng công việc không; cứu được bao nhiêu bản làm sai; làm hỏng bao nhiêu bản làm vốn đúng; và tổng tài nguyên cần dùng. Tài nguyên gồm số lượt gọi, token — đơn vị đếm đầu vào và đầu ra của mô hình — cùng thời gian thực thi và kiểm tra.

Sau khi cố định cơ chế, nhóm mới lặp lại trên các database đã giữ riêng. Mục tiêu là xem cách làm còn có tác dụng khi đổi nguồn, chứ không chỉ khớp các ca đã dùng để phát triển.

Các bộ ràng buộc và cơ chế phản biện đã có trong các nghiên cứu gần. Đóng góp nhóm muốn tạo là bằng chứng có đối chứng về phần lợi ích riêng của cơ chế này, đi cùng bộ lỗi có nguồn và công cụ tái lập. Việc đó vẫn cần được đối chiếu với công trình trước và kiểm bằng thực nghiệm tiếp theo.

## Phần 4 — Next steps

### Trang 10 — Next steps for Tín and Trung · Ảnh 10

Đợt tới, em phụ trách ba việc: mở rộng checker cho CTE và các truy vấn phức tạp hơn; chạy baseline một mô hình mạnh, tự kiểm và kiểm chéo với cùng công cụ; và lưu đủ đầu ra, token cùng thời gian để chấm lại được.

Trung phụ trách đọc nguồn và xử lý các trường hợp mơ hồ theo rubric chung, tức bộ tiêu chí để hai người chấm nhất quán. Trung cũng đối chiếu đóng góp dự kiến với các công trình gần, đồng thời tìm người đang làm phân tích hoặc báo cáo để thử một quy trình công việc thực tế. Hiện nhóm chưa có người dùng tham gia.

Đầu ra của em là bảng độ phủ checker và kết quả baseline có thể chạy lại. Đầu ra của Trung là các case đã review và một công việc thực tế phù hợp để làm pilot.

Hai người sẽ review chéo, thống nhất tiêu chí đúng và khóa protocol trước khi chạy so sánh. Protocol là thiết kế đã chốt về bài toán, điều kiện thử, ngân sách và cách chấm. Sau đó mới mở phần database giữ lại.

Nhóm em xin ý kiến thầy về phạm vi phân tích dữ liệu và báo cáo, cùng tiêu chí để chọn công việc thử với người dùng. Mục tiêu của đợt tới là xác định được phản hồi kiểm chứng giúp ở đâu, bằng một bảng đối chứng đủ rõ để giải thích kết quả.
