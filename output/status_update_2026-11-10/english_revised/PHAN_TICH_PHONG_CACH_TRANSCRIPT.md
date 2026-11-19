# Phân tích phong cách và cách áp dụng vào bài báo cáo

Phân tích dựa trên văn bản trong `technical_presentation_transcripts.txt` mà bạn gửi. Phần này là ghi chú biên tập; lời đọc hoàn chỉnh nằm trong [transcript thuyết trình](TRANSCRIPT_THUYET_TRINH_VI.md).

## 1. Con số xuất hiện để giải thích một giới hạn kỹ thuật

Mẫu không chỉ nói hệ thống xử lý hình ảnh. Nó xác định đầu vào 1280 × 960, dữ liệu 12-bit và tần số khoảng 36 Hz. Ba thông số trả lời ba câu hỏi khác nhau: một khung hình lớn bao nhiêu, mỗi giá trị được biểu diễn thế nào, và bao lâu lại có đầu vào mới. Đến đoạn 75 Hz so với 90 hoặc 120 Hz, người nghe đã có một mức hiện tại để hiểu điều hệ thống muốn cải thiện.

Cách nói đáng học là **đặt con số vào đúng bước của pipeline rồi giải thích nó giới hạn quyết định nào**. Đọc nhiều thông số liền nhau mà không giải thích quan hệ giữa chúng sẽ không tạo được chiều sâu kỹ thuật.

Mẫu có câu về hơn 10.000 clip trong chưa đầy một tuần. Đây là năng suất xử lý clip được kể trong văn bản, không phải số đo training throughput theo samples/giây. Tương tự, giảm latency hơn một nửa là mức thay đổi tương đối; mẫu không cho thời gian trước và sau theo mili giây. Khi áp dụng vào đồ án, chỉ sử dụng các đại lượng thực sự đã được đo.

Với RepGuard, các con số phục vụ ba việc:

- **Nói rõ khối lượng đã làm:** 1.265 phản hồi, bốn bối cảnh, số task và số quy trình. Phản hồi không được kể thành nhiệm vụ độc lập.
- **Giải thích kết luận:** chênh lệch +2,08 điểm phần trăm đi kèm khoảng tin cậy; 21/24 đi kèm đối chứng 19/24 và 20/24.
- **Chứng minh một phần hệ thống hoạt động:** 29 tests mới, 87 scoped tests đạt, 20/20 đầu ra tái lập và 90/90 reference SQL qua qualification. Mỗi số phải được gọi đúng là kiểm thử phần mềm, tái lập đầu ra hay kiểm tra bộ chấm.

Các số về Hz, độ phân giải và tốc độ huấn luyện trong mẫu không được đưa vào transcript của đồ án. Chúng không đo cùng vấn đề với các thực nghiệm hiện tại.

## 2. Bottleneck được giải thích qua tác động lên hệ thống

Trong mẫu, người nói nêu vấn đề, giải nghĩa thuật ngữ, rồi chỉ ra thay đổi ở pipeline. Chẳng hạn, khi nói không gian hành động có nhiều cách giải khác nhau, họ đưa ra một cách diễn giải để người nghe hiểu vì sao tối ưu khó. Đoạn sau chuyển sang các can thiệp cụ thể thay vì chỉ nói đã “tối ưu hiệu năng”.

Khung trình bày phù hợp cho đồ án là:

**Quan sát được gì → vì sao ảnh hưởng kết quả → đã xử lý phần nào → còn phải kiểm chứng phần nào.**

| Vướng mắc của đồ án | Cách xử lý đã có | Điều cần nói đúng khi thuyết trình |
|---|---|---|
| Query chạy được nhưng dùng tên làm đại diện cho quốc tịch | Đã có schema search và kiểm ràng buộc về field/join trong phạm vi SQL hỗ trợ | Component đã triển khai; chưa chứng minh tích hợp nó giúp mô hình sửa đúng hơn. |
| Một task đổi kết quả chấm giữa hai phiên bản SQLite | Khóa native engine 3.42 và kiểm bộ chấm bằng reference queries cùng các ca đối chứng | Đây là xử lý môi trường đo; không phải tăng accuracy của mô hình. |
| Có bảng không khớp reference, có trường hợp lại chưa có bảng cuối | Tách các loại đầu ra và đọc lại trace thay vì gộp thành một loại lỗi | Các vấn đề chưa hoàn tất do tìm nguồn/budget chưa được giải quyết toàn bộ. |
| Các vòng review chưa cho lợi ích ổn định | Giữ kết quả đã khóa, dừng mở rộng reputation và thiết kế phép thử feedback cụ thể | Thay đổi hướng kiểm chứng là quyết định từ bằng chứng; không phải một thuật toán đã thắng. |

Transcript vì vậy dùng các động từ cụ thể: *chạy, đối chiếu, tách, khóa phiên bản, ghi lại, kiểm lại, so sánh*. Những chỗ chưa hoàn tất dùng *sẽ kiểm, cần mở rộng, chưa đo được*.

## 3. Nhịp nói đi theo câu hỏi của người nghe

Mẫu thường đi từ một phát biểu rõ sang một giải thích ngắn, rồi đến bằng chứng hoặc quyết định. Người nghe được cho biết ý nghĩa của con số trước khi bị yêu cầu nhớ thêm một thuật ngữ.

Áp dụng vào bài này:

1. Mở đầu bằng công việc cụ thể: AI lấy dữ liệu, tạo bảng, rồi kiểm lại kết quả.
2. Giải thích một thuật ngữ ngay ở lần dùng đầu, trong một câu. SQL, schema, checker và CTE không được gom thành một đoạn từ điển.
3. Mỗi đoạn xử lý một ý: cách chạy, con số, hoặc hệ quả. Câu chuyển trang giải thích vì sao cần bước tiếp theo.
4. Khi đọc biểu đồ, xác định đối chứng và mẫu số trước. Chỉ sau đó mới đọc chênh lệch.
5. Dùng giọng của người trực tiếp làm việc: “nhóm em đã chạy”, “chúng em phát hiện”, “bước tiếp theo em sẽ kiểm”. Không dùng những câu tự đánh giá như “giải pháp vượt trội”, “kết quả ấn tượng” hoặc “nâng tầm độ tin cậy”.

Ví dụ cách viết trong transcript:

> Cả hai nhánh tự kiểm đạt 21 trên 24 trường hợp. Hai nhánh kiểm chéo đạt 19 và 20. Trên pilot này, đổi sang mô hình khác để kiểm lại chưa mang lại kết quả tốt hơn. Bước tiếp theo là thay đổi thông tin phản hồi, rồi đo lại ở cùng điều kiện.

Đoạn này cho người nghe một đối chứng, một kết quả và một quyết định. Nó không cần thêm tính từ để làm kết quả có vẻ quan trọng.

## 4. Thứ tự bài nói

Transcript đi theo thứ tự agenda đã thống nhất, sử dụng **số ảnh hiện tại**:

| Phần | Thứ tự ảnh |
|---|---|
| Agenda | 01 |
| Work completed | 02 → 06 → 07 |
| What we learned | 03 → 04 → 05 → 08 |
| Research direction | 09 |
| Next steps | 10 |

Số trang trình bày trong transcript là 01–10 theo thứ tự mới. Mỗi tiêu đề kèm số ảnh gốc để bạn không phải đoán khi chuyển slide. Nội dung thí nghiệm giữ mốc của bộ slide; việc biên soạn transcript ngày 11/11 không thêm kết quả thực nghiệm mới.
