# Nội dung báo cáo RepGuard — 27/10/2026

**Phân công tiếp theo và agenda:** [Danh sách công việc của Tín và Trung cùng phạm vi bốn phần](PHAN_CONG_VA_REVIEW_AGENDA.md). Canva hiện có 35 trang tổng cộng; bản PDF đã xuất vẫn có 26 trang. Hai trang chuyển phần Progress và Next experiment cần được dời để khớp nội dung như bản rà soát.

**Bản trình chiếu ngày 28/10 đã hoàn thành:** [Canva, PDF, PowerPoint, ghi chú và hướng dẫn dùng](PRESENTATION_HANDOFF.md). Đọc [review/đính chính](CANVA_REVIEW_VA_DINH_CHINH.md) và [lời thuyết trình](LOI_THUYET_TRINH_PHAN_BO_SUNG.md) trước khi tập nói. Outline 22 trang bên dưới là tài liệu tham khảo ban đầu; deck cuối có 26 trang trình chiếu.

**Script đầy đủ để tập nói:** [Lời trình bày cho cả 26 slide và câu chuyển từng trang](SCRIPT_THUYET_TRINH_DAY_DU_26_SLIDE.md), hoặc [bản Word](../../../output/documents/RepGuard_Script_Thuyet_Trinh_26_Slide_2026-10-28.docx). Bản này mở rộng ghi chú bổ sung thành một bài trình bày liên tục, giải thích thuật ngữ khi xuất hiện và có hướng dẫn rút gọn.

## Đọc và dùng để làm slide

1. **[Báo cáo chi tiết](REPGUARD_LITERATURE_REVIEW_VA_BAO_CAO_TIEN_DO.md)**: 26 mục, 49 nguồn nghiên cứu gốc, literature theo nhóm vấn đề, cơ sở lý thuyết, kiến trúc code, kết quả từng giai đoạn, giới hạn, metrics và thiết kế nghiên cứu tiếp theo. Có đoạn lời nói dùng trực tiếp khi báo cáo.
2. **[Kịch bản 22 slide và 22 câu hỏi](SLIDE_OUTLINE_VA_CAU_HOI_BAO_VE.md)**: nội dung trên slide, speaker notes, gợi ý hình, nguồn, bản rút gọn 12–15 phút và câu trả lời cho các câu hỏi phản biện. Đây là outline, chưa phải PowerPoint.
3. **[Tài liệu tham khảo BibTeX](references.bib)**: metadata cơ bản đã đối chiếu; venue hoặc preprint version nằm trong trường `note`. [JSON tương ứng](references.json) giúp tìm nhanh nguồn theo mã R01–R49. Không bổ sung DOI/volume khi chưa xác minh.

## Kết luận tiến độ cần giữ chính xác

Các vòng development đã hoàn tất nhiều công việc kỹ thuật và thực nghiệm; **chưa xác nhận lợi ích riêng của phương pháp reputation trước đầy đủ đối chứng mạnh**. Kết quả mới nhất được lưu là vòng 3 ngày 20/10: 264 phản hồi mới trên 24 TAT-QA contexts. Strong fixed workflow đạt 20/24, oracle union cũng 20/24; các gate không hỗ trợ fit thêm history learner lên bank đó. EvalPlus/MBPP+ mới chuẩn bị nguồn và 32 tasks, chưa có model calls hoặc program executions.

Tài liệu phân biệt primary score, post-hoc diagnostics, oracle reference, development và confirmation. Không dùng số calls như số task độc lập hoặc coi audit PASS là method superiority.

## Kiểm chứng trong lượt rà soát

- [Hồ sơ kiểm chứng](verification_2026-10-27.json): Git revision, source inventory, audit reruns, official TAT-QA scoring, counts và kết quả test.
- [Danh mục mã nguồn](source_inventory.md): 291 Python files / 35.579 dòng; [hash và định nghĩa từng file](source_inventory.json).
- Bộ test hiện tại: **308 pass, 1 skip**, skip do local thiếu Torch cho test được thiết kế chạy trong pinned Modal image.
- Hai receipt/source/execution audits vòng 3 chạy lại đều PASS; evaluator TAT-QA gốc tái lập đúng các scores và oracle trong summaries.
- [Kiểm tra biên tập](editorial_checks.json): đủ 49 nguồn, 22 slide, 22 câu hỏi, links nội bộ tồn tại và hashes tài liệu.

Phạm vi: full-file hash/AST inventory, behavioral review tập trung critical paths; không phải chứng minh hình thức mọi dòng code hoặc human semantic adjudication. Không gọi solver/judge mới, không mở confirmation outcomes mới, không truy vấn cloud live. Các source và artifacts thí nghiệm cũ được giữ nguyên; output kiểm tra mới chỉ nằm trong thư mục này.

## Tái chạy các kiểm tra báo cáo

Từ repo root:

```bash
./.venv/bin/python docs/reports/2026-10-27/audit_report_evidence.py
./.venv/bin/python docs/reports/2026-10-27/prepare_report_index.py
```

Lệnh đầu đọc saved artifacts và dùng evaluator gốc; SciPy được đặt riêng ở `/tmp/repguard_tatqa_eval_deps` trong lượt rà soát. Nếu thư mục tạm đã mất, script báo thiếu dependency, không thay scorer. Trường `pytest_run_observed` ghi lần test suite thực sự đã chạy ngày 27/10, không chạy lại pytest khi chỉ gọi script audit.
