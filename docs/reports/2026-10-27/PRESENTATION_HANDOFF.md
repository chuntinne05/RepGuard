# Deck báo cáo RepGuard — 28/10/2026

**Cập nhật khi rà soát agenda:** Canva hiện có 35 trang tổng cộng sau khi thêm trang chuyển phần. Các thông số 32 trang và ánh xạ dưới đây mô tả trạng thái lúc xuất PDF 26 trang trước đó. Xem [phân công Tín và Trung cùng rà soát agenda hiện tại](PHAN_CONG_VA_REVIEW_AGENDA.md) để dùng đúng số trang và hai vị trí chuyển phần cần chỉnh.

## Bản dùng để báo cáo

**Canva chính:** https://www.canva.com/design/DAHZNqV57vA/_lRn_fiY1M11YCo8PHAhlg/edit

Tên: **RepGuard · Literature Review & Progress · 28 Oct 2026**. Đây là bản sao đã chỉnh; deck gốc “Reguard Week 3” vẫn được giữ.

Deck có **26 trang trình chiếu**, gồm bối cảnh, literature review, pipeline, các kết quả development và phép thử tiếp theo. Canva có 32 trang tổng cộng; 6 trang khung/trùng được ẩn, không nằm trong bản xuất. Có ghi chú tiếng Việt ở 24 trang nội dung; các trang literature liên quan có đường dẫn paper trong ghi chú.

- [PDF dùng khi trình chiếu offline](../../../output/pdf/RepGuard_Literature_Review_Progress_2026-10-28.pdf)
- [PowerPoint dự phòng](../../../output/presentations/RepGuard_Literature_Review_Progress_2026-10-28.pptx)
- [Review và các đính chính khoa học](CANVA_REVIEW_VA_DINH_CHINH.md)
- [Lời thuyết trình tiếng Việt](LOI_THUYET_TRINH_PHAN_BO_SUNG.md)
- [Script đầy đủ cho 26 slide và câu chuyển từng trang](SCRIPT_THUYET_TRINH_DAY_DU_26_SLIDE.md)
- [Bản Word của script đầy đủ](../../../output/documents/RepGuard_Script_Thuyet_Trinh_26_Slide_2026-10-28.docx)
- [Bản literature review chi tiết và tiến độ](REPGUARD_LITERATURE_REVIEW_VA_BAO_CAO_TIEN_DO.md)
- [Các câu hỏi phản biện và outline tham khảo](SLIDE_OUTLINE_VA_CAU_HOI_BAO_VE.md)

Canva là bản chỉnh sửa chính. PowerPoint xuất từ Canva giữ 26 trang và ghi chú, nhưng một số bảng/biểu đồ được xuất thành đồ họa; không coi đây là các chart dữ liệu PowerPoint native. Bản PDF đã được kiểm tra bằng ảnh render; chưa mở và kiểm tra trong ứng dụng PowerPoint.

## Mạch trình bày

| Trang xuất | Nội dung |
|---|---|
| 1–3 | Trang bìa, mục lục, câu hỏi nghiên cứu |
| 4–10 | Bốn hướng literature; reputation; reliability; routing; các công trình gần nhất; execution/repair; khoảng trống |
| 11 | Pipeline và công thức cập nhật |
| 12–13 | MMLU-Pro và hàm ý |
| 14–19 | Ba repair cycles; điểm primary và chẩn đoán hậu kiểm |
| 20–22 | Giới hạn bằng chứng, tiến độ đã kiểm chứng, kết quả chính |
| 23–26 | Nested tests đề xuất, protocol, giới hạn và các quyết định xin ý kiến GVHD |

Trang Canva tương ứng: `1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 24, 26, 27, 28, 29, 30, 31`. Trang ẩn: `3, 15, 22, 23, 25, 32`. Khi xuất lại, chọn các trang trình chiếu này; không bật toàn bộ trang ẩn.

## Những kết luận cần giữ khi nói

1. **Chưa xác nhận reputation cải thiện quyết định hơn đối chứng mạnh** trong các setting đã thử. Kết quả âm có giá trị giới hạn claim, nhưng không đủ để loại trừ thuật toán như một nguyên nhân.
2. Primary score và readout hậu kiểm là hai lớp bằng chứng khác nhau. Không thay điểm chính thức bằng kết quả chẩn đoán thuận lợi hơn.
3. 560 response mới là số lượt suy luận của ba cycle ngày 18–20/10, không phải 560 nhiệm vụ độc lập. Cohort composition và backbone không được gộp thành một thí nghiệm nhân quả.
4. EvalPlus mới chuẩn bị 32 task, 96 basic inputs và 3.397 plus inputs; **0 model call, 0 program execution**. Nested tests là setting đề xuất, chưa phải kết quả mới.
5. Với `F = B AND E`, `B=0 ⇒ F=0` đúng theo định nghĩa. Full-suite pass là outcome thao tác hóa, không chứng minh correctness trên mọi input.
6. Các paper gần nhất thu hẹp novelty. Chưa replication chúng trên archive RepGuard, chưa chứng minh RepGuard vượt chúng.
7. CI và cận harm phải nói kèm giả định. 0/24 có cận một phía 95% 11,73% chỉ dưới giả định Bernoulli độc lập; 24 contexts có thể có phụ thuộc.

## Tập nói

Literature review nên giải thích theo **vấn đề → phương pháp → giả định → giới hạn → liên hệ RepGuard**, tránh đọc danh sách paper. Dùng ghi chú Canva hoặc bản lời nói để giải thích; không đọc toàn bộ chữ trên slide. Có thể dành 8–12 phút cho literature và 5–7 phút cho tiến độ/phép thử, điều chỉnh theo thời lượng GVHD.

Cuối buổi cần xin ý kiến về phạm vi đóng góp, dataset/pilot tiếp theo và điều kiện dừng. Không trình bày kế hoạch dự kiến như lịch chạy đã được duyệt.

## Phiên bản mã nguồn và giới hạn rà soát

Đã pull `dev` fast-forward tới `27b4bc7fe505387dae2eb1658bcecf895fbf409c`. Không sửa mã thực nghiệm, gold labels hay kết quả đóng băng. Rà soát code sử dụng full-file hash/AST inventory và behavioral review các critical paths; không phải chứng minh hình thức từng dòng code. Lượt này không gọi LLM mới cho thực nghiệm, không mở confirmation outcomes mới và không truy vấn cloud live.

Canva hiện báo đã hết hạn mức AI dùng thử. Deck đã lưu và vẫn có thể chỉnh sửa thủ công; không đăng ký gói trả phí trong quá trình làm.
