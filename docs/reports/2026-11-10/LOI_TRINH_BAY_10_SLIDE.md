# Lời trình bày — cập nhật tiến độ RepGuard

Thời lượng gợi ý 10–12 phút. Bắt đầu bằng agenda, không có trang bìa. Các số liệu dưới đây chốt sau chấm offline ngày 10/11/2026.

## 01 — Nội dung báo cáo

Thưa thầy, báo cáo hôm nay tập trung vào phần mới sau lần cập nhật cuối tháng 10. Nhóm sẽ trình bày bốn nội dung: các thử nghiệm đã hoàn tất; những điều học được từ kết quả và lỗi thực tế; lớp kiểm chứng đã xây; cuối cùng là hướng xác nhận và phân công tiếp theo. Thông điệp chính là nhóm đã có nhiều bằng chứng hơn để thu hẹp câu hỏi nghiên cứu, nhưng chưa có cơ sở để tuyên bố multi-agent đã cải thiện ổn định.

## 02 — Tiến độ kể từ báo cáo trước

Trong kỳ mới, nhóm thu thêm 1.265 phản hồi mô hình ở bốn bối cảnh: kiểm bằng chứng, hỏi đáp báo cáo tài chính, thao tác workspace dữ liệu và sinh SQL theo cách hiểu đã chỉ định. Con số này không tính lại dữ liệu MMLU-Pro hoặc repair đã báo cáo cuối tháng 10, và cũng không phải số task độc lập. Song song, nhóm triển khai lớp kiểm ràng buộc và quy trình tái lập đầu ra. Mục đích của các vòng là đi từ đánh giá đáp án cuối sang kiểm rõ dữ liệu nào được dùng, yêu cầu được hiểu ra sao và điều gì còn chưa được xác minh.

## 03 — Hai vòng đầu chưa xác nhận lợi thế kiểm chéo

Biểu đồ thể hiện chênh lệch kiểm chéo so với tự kiểm, lấy trung bình hai hướng để tránh chọn riêng nhánh có điểm cao nhất. Cả hai vòng đều có ước lượng khoảng cộng 2,08 điểm phần trăm, nhưng khoảng tin cậy đều đi qua 0. Vòng bằng chứng còn không đạt mức lợi ích đã khóa trước khi chạy. Vì vậy, quyết định của nhóm là chưa mở rộng học reputation. Các kết quả này giới hạn claim trong những cấu hình và nguồn đã thử; chúng không chứng minh multi-agent luôn vô ích.

## 04 — Workspace cho thấy cần đo cả việc hoàn thành

Nhóm nối mô hình với workspace có CSV, JSON, SQLite và PDF, ghi lại quá trình gọi công cụ và artifact. Trên 36 trajectory, có 9 đầu ra khớp reference, 14 có bảng nhưng không khớp strict relation và 13 chưa nộp artifact cuối. Đây là dữ liệu chẩn đoán được ghép từ hai block có gián đoạn kỹ thuật, không phải score xác nhận chính thức của DataSpace. Điều quan trọng là ba nhóm này cần cách xử lý khác nhau: không thể coi thiếu đầu ra và hiểu sai chỉ tiêu là cùng một loại lỗi.

## 05 — Ba kiểu lỗi cần phân biệt

Ví dụ đầu là hỏi quốc tịch nhưng truy vấn dùng tên làm đại diện, trong khi nguồn có trường Nationality. Ví dụ thứ hai là “tên viết tắt” có hai cột phù hợp, nên cần thẩm định cách hiểu thay vì tự chọn reference có lợi. Ví dụ thứ ba là bảng có đúng chuỗi tên nhưng thừa cột ID nên bị phép chấm strict đánh không khớp. Đây là các phân tích phát triển, chưa có người độc lập gán nhãn ngữ nghĩa. Nhóm giữ nguyên điểm gốc và dùng chúng để thiết kế kiểm chứng tốt hơn.

## 06 — Lớp kiểm chứng đã triển khai

Nhóm đã xây component kiểm ràng buộc do phía hệ thống quản lý, đối chiếu query với schema và nguồn thực tế. Khi chuyển cho tác tử tiếp theo, hệ thống kiểm lại query, contract và bằng chứng; không chỉ tin nhãn “đã kiểm” do agent ghi. Component trả ba trạng thái: đạt, vi phạm hoặc chưa đủ căn cứ. Đã có 29 tests mới và 87 scoped tests đạt; 20 SQL cũ chạy lại tái tạo đúng bytes. Đây là bằng chứng component chạy được và có thể tái lập, chưa phải bằng chứng tăng accuracy. Phạm vi SQL còn giới hạn và contract phát triển còn cần thẩm định.

## 07 — Chuẩn bị đánh giá trên nguồn mới

Nhóm chuẩn bị 204 task SpecBridge trên 12 database và chia theo database thành development, validation và reserved. Chỉ development được mở. Trên 45 task development, 90 reference SQL đều qua kiểm tra tương ứng; các kiểm soát sai cách hiểu, thêm hàng và thiếu đầu ra đều bị loại. Đây là qualification bộ chấm. Nhóm còn phát hiện một task đổi kết quả giữa hai phiên bản SQLite, nên khóa native engine. Tuy nhiên 74/90 reference có CTE hoặc nhiều scope, vượt độ phủ hiện tại của checker; cần giải quyết điểm này trước thí nghiệm cơ chế.

## 08 — Vòng SQL mới nhất: tự kiểm đang tốt hơn

Pilot gồm 12 task trên ba database, mỗi task có hai cách hiểu chỉ định, thành 24 trường hợp. Hai mô hình direct đạt 18 và 19; tự kiểm cùng đạt 21; kiểm chéo đạt 19 và 20. Chênh lệch kiểm chéo so tự kiểm là âm 6,25 điểm phần trăm trên tập này, chỉ là mô tả development. Receipt audit đạt và tất cả 144 execution record được tái lập. Pilot này chưa dùng checker V5 để can thiệp, nên chưa đánh giá checker có giúp sửa lỗi hay không. Nhóm sẽ không dùng kết quả này để nhận đã có phương pháp mới.

## 09 — Câu hỏi nghiên cứu và phần cần chứng minh

Hướng nhóm muốn xin ý kiến thầy là giá trị của bàn giao có kiểm chứng khi các bên được cấp cùng nguồn, công cụ và ngân sách. Nhóm đã có error bank và component. Phần nghiên cứu còn thiếu là đối chứng để biết lợi ích đến từ checker, loại phản hồi hay việc thêm tác tử. Nhóm dự kiến so tự kiểm, neutral recheck, diagnostic đúng và diagnostic xáo trộn, rồi xác nhận trên nguồn giữ lại. Contract và handoff đã có prior gần; novelty cần được định vị qua đối chiếu và bằng chứng mới. Outcome cần là hoàn thành đúng công việc, kèm sửa/hại, dừng sai và tổng chi phí.

## 10 — Phân công công việc tiếp theo

Đề xuất Tín phụ trách coverage và baseline, hoàn thiện harness cùng log chi phí. Trung phụ trách source-only review, đối chiếu literature và tìm workflow/người dùng để kiểm tính thực tiễn. Hai người review chéo và khóa protocol trước khi chạy tiếp; chỉ mở tập giữ lại sau khi cơ chế đã cố định. Nhóm xin ý kiến thầy về phạm vi analytics/reporting, mức contribution phù hợp và workflow thực tế nên ưu tiên. Đầu ra của đợt tới cần là bộ đánh giá rõ nghĩa và bảng đối chứng tái lập, trước khi tiếp tục scale hay học reputation.
