# Phân công tiếp theo và rà soát agenda RepGuard

## Phân công đề xuất cho giai đoạn tiếp theo

**Tín**

- Hoàn thiện runner chạy basic và extended tests, kiểm tra chương trình chuẩn, timeout và log kết quả.
- Triển khai các baseline với cùng thông tin và ngân sách để so sánh với RepGuard.
- Chạy pilot sau khi chốt protocol; lưu response, kết quả test và chi phí để tái kiểm tra.

**Trung**

- Rà danh sách 32 task, kiểm tra trùng với MBPP200 và đề xuất cách chia history, validation và evaluation.
- Hoàn thiện bảng so sánh các nghiên cứu gần nhất và làm rõ câu hỏi cần kiểm chứng của đề tài.
- Phân tích kết quả pilot: basic pass có đáng tin không, oracle có vượt best fixed không, rescue và harm; tổng hợp bảng và biểu đồ báo cáo.

**Cả hai**

- Thống nhất với Thầy về dataset, ngân sách và điều kiện tiếp tục hoặc dừng trước khi thu đáp án mới; kiểm tra chéo kết quả trước buổi báo cáo tiếp theo.

## Agenda của bản PDF 26 trang đã bàn giao

Số trang trong bảng này là số trang của bản PDF và số mục trong script 26 slide. Trang bìa 1 và mục lục 2 là phần mở đầu chung.

| Phần | Trang PDF | Nội dung và kết luận rà soát |
|---|---|---|
| Problem | 3 | Câu hỏi nghiên cứu; agent và reputation; feedback chưa hoàn hảo; mục tiêu cải thiện quyết định ở cùng chi phí. Đủ cho phần đặt vấn đề trong báo cáo tiến độ, với lời mở đầu ở trang 1. |
| Literature review | 4 đến 10 | Bản đồ bốn hướng; reputation; reliability; routing; công trình gần nhất; execution và repair; tổng hợp research gap. Có cơ sở, đối chiếu và giới hạn claim. |
| Progress | 11 đến 22 | Pipeline đã triển khai; MMLU Pro; ba repair cycles; primary và post hoc; giới hạn bằng chứng; tiến độ đã kiểm chứng và kết quả chính. Pipeline thuộc phần này vì mô tả cách làm hiện có của dự án. |
| Next experiment | 23 đến 26 | Setting nested tests; trạng thái chuẩn bị; protocol và baseline; giới hạn cần tính khi thiết kế; nội dung xin ý kiến Thầy. Phân công tiếp theo được bổ sung vào script trang 26 và phụ lục. |

Trang 25 Limitations nhắc lại giới hạn của bằng chứng hiện tại để giải thích yêu cầu cho phép thử tiếp theo. Khi nói cần nối rõ vai trò này; không trình bày các giới hạn như một kết quả mới của EvalPlus.

## Đối chiếu Canva hiện tại

Canva được đọc lại trong lượt rà soát này và hiện có **35 trang tổng cộng**, đã thêm ba trang mục lục chuyển phần so với trạng thái 32 trang trước. Vì vậy, số trang Canva và số trang PDF 26 trang không còn giống bảng ánh xạ cũ. Nội dung nghiên cứu chính vẫn theo thứ tự tương ứng.

| Nội dung | Vị trí Canva hiện tại |
|---|---|
| Trang bìa và mục lục chung | 1 và 2 |
| Trang chuyển Problem và Research Question | 3 và 5 |
| Literature review | 6 đến 12 |
| Pipeline và MMLU | 13 đến 15 |
| Trang chuyển Progress | 16 |
| Ba repair cycles và diagnostics | 18 đến 23 |
| Trang chuyển Next experiment | 24 |
| Evidence Limits | 27 |
| Verified Progress và Main Evidence | 29 và 30 |
| Next Experiment đến Discussion with Supervisor | 31 đến 34 |

Các trang 4, 17, 25 và 28 là mục lục mẫu cũ; trang 26 Proposed Next Setting trùng vai trò với trang 31; trang 35 là khung cuối. Nên giữ các trang này ngoài luồng trình chiếu chính. Trạng thái ẩn hiện thời không được API liệt kê trang xác nhận trong lượt đọc này.

**Hai vị trí cần chỉnh để trang chuyển phần khớp nội dung**

1. Dời trang chuyển Progress hiện ở vị trí 16 lên ngay trước Pipeline hiện ở vị trí 13. Nếu giữ vị trí hiện tại, pipeline và kết quả MMLU xuất hiện trước khi mở phần Progress.
2. Dời trang chuyển Next experiment hiện ở vị trí 24 xuống ngay trước Next Experiment hiện ở vị trí 31. Nếu giữ vị trí hiện tại, Evidence Limits, Verified Progress và Main Evidence bị nằm sau trang chuyển sang kế hoạch mới.

Sau đúng hai thao tác dời này và không có thay đổi trang khác, các khoảng **số thứ tự thô Canva** đề xuất là Problem 3 đến 5, Literature review 6 đến 12, Progress 13 đến 29, Next experiment 30 đến 34; bỏ qua các trang mẫu hoặc trùng đã nêu khi trình chiếu. Đừng dùng các khoảng dự kiến này làm số trang hiện tại trước khi thực hiện thao tác dời.

Lượt này rà soát Canva ở chế độ đọc; không thay đổi thứ tự hoặc nội dung thiết kế. PDF và PowerPoint đã bàn giao trước đó vẫn là bản 26 trang; chưa xuất lại từ trạng thái Canva 35 trang.

## Câu nói bổ sung ở cuối slide Discussion with Supervisor

“Về phân công tiếp theo, Tín phụ trách phần chạy chương trình, các baseline và thu kết quả pilot. Trung phụ trách rà dữ liệu, hoàn thiện đối chiếu literature và phân tích kết quả. Cả hai sẽ cùng thống nhất protocol, ngân sách và tiêu chí tiếp tục hoặc dừng với Thầy trước khi chạy đợt mới, rồi kiểm tra chéo số liệu trước khi báo cáo.”

## Nguồn đối chiếu

- [Canva đang dùng](https://www.canva.com/design/DAHZNqV57vA/_lRn_fiY1M11YCo8PHAhlg/edit)
- [PDF 26 trang](../../../output/pdf/RepGuard_Literature_Review_Progress_2026-10-28.pdf)
- [Script đầy đủ](SCRIPT_THUYET_TRINH_DAY_DU_26_SLIDE.md)
