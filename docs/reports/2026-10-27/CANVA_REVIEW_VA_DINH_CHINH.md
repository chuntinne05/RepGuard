# Đối chiếu báo cáo tuần và deck Canva cho buổi 28/10/2026

Ngày đối chiếu: 27/10/2026. Đã fast-forward `dev` từ `f3c7446` lên `27b4bc7fe505387dae2eb1658bcecf895fbf409c`. Không thay mã thực nghiệm, kết quả đóng băng hay điểm chính thức.

## Kết luận về mức độ khớp

Báo cáo `docs/analysis/repguard_week_report_2026-10-27.md` khớp phần lớn **số liệu chính** với bản literature review và kiểm chứng trong thư mục này. Mạch nối MMLU-Pro → can thiệp sửa lỗi → kiểm tra contract → đề xuất nested tests là hợp lý. Tuy nhiên, một số **diễn giải nhân quả và trạng thái thực nghiệm** đang mạnh hơn bằng chứng. Không nên đưa nguyên văn các câu đó lên slide hoặc dùng trong lời nói.

Deck “Reguard Week 3” có 31 trang. Trang 1–17 chứa phần bối cảnh, ba nghiên cứu và chẩn đoán. Phần sau chủ yếu là khung mẫu. Nội dung hiện có nhiều đoạn văn dài, footer còn `Student Name (HCMUT)`, `Short Title`, `January 2024` và số trang cũ. Các nhãn biểu đồ Brier làm tròn một chữ số có thể che mất chênh lệch cần trình bày.

## Những chỉnh sửa khoa học cần áp dụng

| Vị trí trong báo cáo tuần | Vấn đề | Cách trình bày chính xác |
|---|---|---|
| Tóm tắt mục 0.3; mục 4; cuối mục 9 | “Không phải thuật toán reputation kém” loại trừ một nguyên nhân chưa được cô lập | “Chưa xác nhận lợi ích tăng thêm của reputation trong các cấu hình đã thử. Các kiểm tra chỉ ra nút thắt về pool, contract và tín hiệu.” |
| Câu hỏi Q1, mục 2 | “MCQ gần như bão hòa” không phù hợp best single 47,76% và per-task oracle 68,34% | “Nhãn môn học chưa khai thác được bổ trợ ở cấp câu hỏi.” Không gọi toàn bộ MCQ bão hòa. |
| I5, I9 và câu nối hai tuần | Quan hệ basic/full-suite được giới thiệu như phát hiện thực nghiệm từ ba vòng tài chính | Đây là **setting đề xuất** cho phép thử tiếp theo. Với `F = B AND E`, `B=0 ⇒ F=0` đúng theo định nghĩa. Mức độ basic pass không đủ tin cậy trong pool hiện tại vẫn cần đo. |
| Vòng 2, liên hệ composition và backbone | 24 case composition và 16 case backbone là các phép thử khác nhau | Báo cáo riêng từng cohort. Không khẳng định hai backbone giống nhau là nguyên nhân đã chứng minh cho thất bại composition. |
| Vòng 3: “mọi nhánh đều 20/24” | Mở rộng chẩn đoán count normalization sang toàn bộ nhánh/model | Chỉ các nhánh **structured/scoped tương ứng** đạt 20/24 dưới readout count được chuẩn hóa. Cross-family primary: Qwen 19/20/20, Gemma 16/16/16. Common metadata readout: Qwen 20/20/20, Gemma 18/18/18. |
| Vòng 3: “4/24 lỗi gross/net, dấu, scale annotation” | Trộn lỗi ngữ nghĩa của response với nghi vấn annotation nguồn | Tách **lỗi ngữ nghĩa còn lại** và **4 source-annotation flags chưa được người đánh giá phân xử**. Không tự đổi gold hay điểm chính thức. |
| I8: “gain 14 vs 19 biến mất” | 14 và 19 không cùng một so sánh đồng nhất | Dùng so sánh hợp lệ: cycle 1 strict PoT 14, format 16, readout 17; history cũng 17 với compute proxy +13,6%. Cycle 3 plain 19 so với scoped KEEP 15 phản ánh khác biệt contract trong pilot này. |
| Nguyên tắc “preregister… không đổi giữa chừng” | Dễ gây hiểu rằng mọi phân tích đã đăng ký trước lần suy luận đầu tiên | Phân biệt protocol/gate viết trước từng phép thu với kiểm tra phần mềm và phân tích hậu nghiệm. Gắn rõ nhãn exploratory/post-hoc. |
| Mục 6: tests | Số liệu Windows lịch sử không mô tả trạng thái máy hiện tại | Kiểm chứng local macOS ngày 27/10: **309 collected, 308 passed, 1 skipped** (Torch). Inventory: **45 file test, 4.101 dòng**. Đây không phải Linux/Modal CI hay chứng nhận mọi nhánh pilot. |
| Mục 6: containers | “0, không có job chạy ngầm” được viết như trạng thái hiện thời | Chỉ có quan sát lịch sử trong artifact. Lượt kiểm chứng 27/10 **không truy vấn cloud trực tiếp**. |
| Mục 7: “false-positive rate B=1,F=0” | Biến cố chung chưa phải một rate có mẫu số | Báo cáo `P(B=1,F=0)` nếu là tần suất chung. Rate basic pass sai là `P(F=0\|B=1)`. FPR theo phân loại là `P(B=1\|F=0)`. Ghi rõ mẫu số và số quan sát. |
| Mục 7: lịch 28/10–03/11 | Có thể bị đọc thành job đã lên lịch/chạy | Đây là **kế hoạch đề xuất**, phụ thuộc preflight, ngân sách và chốt phạm vi với GVHD. |
| Mục 8, kịch bản kết | “Fail thì chuyển measurement paper” nghe như phạm vi đã duyệt | Trình bày như phương án xin ý kiến GVHD, chưa phải đóng góp thay thế được chấp thuận. |

## Số liệu có thể giữ trên slide

- MMLU-Pro: 18.064 response thật. ECRT − FixedBorrow ở điều kiện related + 25% noise: khoảng **+0,02 điểm phần trăm**, CI 95% **[−0,04; +0,10]**. Không khẳng định superiority.
- Ba repair cycles ngày **18–20/10**: **160 + 136 + 264 = 560 response mới**. Đây là lượt suy luận, không phải 560 task độc lập.
- Cycle 1: bốn nhánh DSL cùng **6/24**, union **6/24**. Sau readout harmonization, direct PoT và history cùng **17/24**, history compute proxy **+13,6%**.
- Cycle 3 primary scoped: Plain PoT **19/24**; KEEP/E/O/EO **15/15/16/15**. Scoped union **16/24**.
- Cycle 3 primary unrestricted: Qwen **19/20/20**, Gemma **16/16/16**, pool union **20/24**, best fixed **20/24**. Số liệu hậu kiểm không thay các điểm primary này.
- EvalPlus: **32 task đã chọn, 96 basic inputs, 3.397 plus inputs, 0 model call, 0 program execution**. Chưa có benchmark score. Chưa map overlap MBPP200, chưa thể gọi split độc lập.
- Với giả định quan sát Bernoulli độc lập: **0 harm/24** có cận trên một phía 95% **11,73%**. Để cận này ≤2% cần ít nhất **149 quan sát và không có harm**. Đây không phải power calculation tổng quát.

Nguồn kiểm chứng nội bộ: [verification_2026-10-27.json](verification_2026-10-27.json), [báo cáo tổng hợp](REPGUARD_LITERATURE_REVIEW_VA_BAO_CAO_TIEN_DO.md), các protocol/result/audit của cycle 01–03 trong `docs/analysis/`.

## Literature review nên giải thích như thế nào

Không đọc lần lượt một danh sách paper. Với mỗi nhóm, trình bày **bài toán → phương pháp đại diện → giả định → điều chưa trả lời → quan hệ với RepGuard**.

1. **Reputation và conditional trust.** Beta Reputation System tích lũy bằng chứng thành phân phối Beta. Credibility Scoring học ảnh hưởng từ đóng góp lịch sử trong multi-agent aggregation. Skill-Conditional Trust phân biệt năng lực theo skill và chỉ ra điều kiện borrowing có lợi cũng như rủi ro laundering. RepGuard kế thừa các ý này, nhưng cần xử lý trường hợp nhãn quan sát khác correctness thật.
2. **Feedback và gold audit.** LLM-as-a-Judge cung cấp proxy rẻ hơn đánh giá người, có bias. Calibration hỏi xác suất có khớp tần suất đúng hay không. PPI dùng nhãn gold để hiệu chỉnh ước lượng từ prediction. Active Statistical Inference phân bổ việc lấy nhãn. Các bảo đảm của từng paper phụ thuộc giả định của nó, không tự chuyển thành bảo đảm cho adaptive routing của RepGuard.
3. **Decision và budget.** Sequential Halving là đối chứng phân bổ ngân sách để chọn arm. RouteLLM định tuyến giữa model. R2-Router xét cả model và output budget. Câu hỏi của RepGuard phải xét hiệu quả quyết định ở cùng thông tin và tổng ngân sách, không chỉ Brier thấp hơn.
4. **Execution và repair.** PAL/PoT tách tính toán sang chương trình. Self-Refine dùng feedback để sửa lặp. Nghiên cứu về intrinsic self-correction cho thấy kết quả không tự được bảo đảm khi thiếu feedback bên ngoài. Thực thi code kiểm tra tính toán, không chứng nhận đúng nguồn, đúng đại lượng hay đúng unit.
5. **Nested tests.** EvalPlus đã chỉ ra test yếu có thể bỏ sót lỗi và làm đổi thứ hạng model. Vì vậy “test pass chưa đủ” không phải novelty. Hướng cần kiểm tra là dùng feedback không hoàn hảo để phân bổ audit/chọn teammate có lợi hơn baseline mạnh hay không.

Nguồn sơ cấp và metadata đầy đủ: [references.json](references.json), [references.bib](references.bib). Các kết quả paper là kết quả tác giả báo cáo, không phải replication của dự án này.

## Câu chốt nên dùng khi thuyết trình

“Đến hiện tại, chúng em đã xây được hạ tầng thu và kiểm chứng response, đồng thời có kết quả âm giúp giới hạn claim. Chúng em chưa có bằng chứng reputation cải thiện quyết định so với đối chứng mạnh trong các setting đã thử. Phép thử tiếp theo sẽ kiểm tra trước xem feedback và pool có đủ tín hiệu để một chính sách lựa chọn tạo lợi ích hay không, rồi mới quyết định có học phương pháp tiếp.”

## Lưu ý trình bày

Slide giữ tiếng Anh theo deck hiện có. Lời giải thích chi tiết dùng tiếng Việt. Mỗi trang nên có một ý chính, khoảng 30–50 từ ngoài nhãn chart/citation, phần cơ chế và caveat dài đặt trong speaker notes hoặc tài liệu thuyết trình. Kết quả chính và chẩn đoán post-hoc phải có nhãn khác nhau. Các biểu đồ cần mẫu số, đơn vị và độ chính xác thập phân phù hợp.
