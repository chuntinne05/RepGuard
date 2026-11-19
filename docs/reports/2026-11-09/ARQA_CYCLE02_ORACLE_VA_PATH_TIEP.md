# Kết luận quan trọng sau vòng02: khóa oracle trước khi chạy thêm

> Trạng thái mới nhất: [strategy V5](RESEARCH_STRATEGY_V5_VA_CONTRIBUTIONS.md), [kết quả triển khai V5](RELATIONAL_V5_RESULTS_VA_QUYET_DINH.md). Bước trước là [workspace V4](WORKSPACE_V4_RESULTS_VA_PATH_TIEP.md). Các nhận định bên dưới là quyết định tại thời điểm vòng02; primary/gold vẫn giữ nguyên.

Viết hậu nghiệm sau288responses; không thay code, gold hoặc primary đã đăng ký. [Kết quả frozen](ARQA_CYCLE02_RESULTS_VA_QUYET_DINH.md): primary+2,08pp, CI[-4,17;+8,33]pp, gateFAIL. Receipt auditPASS,274/288schema valid,1length stop,0transport errors.0container còn chạy ở app nghiên cứu khi kiểm sau completion.

**Quyết định hiện tại:** không mở rộng bank này, không fit reputation/history và không coi điểm thấp là xác nhận method nhiều agent thất bại trong nghiệp vụ. Cần thẩm định task/oracle trước một vòng inference mới. Phần implement đáng tái sử dụng là source-cell adapter, restricted arithmetic interpreter, receipt lineage và công cụ cho người soát; checklist chưa có lợi ích phối hợp được hỗ trợ.

## Vấn đề đo lường đã thấy trong toàn bộ24câu

Một hậu kiểm có quy tắc áp dụng cho **tất cả24câu**, không bỏ các câu bất lợi, ghi flags ở [JSON](arqa_v2_oracle_sensitivity.json). Đây là automatic flags + tác giả/assistant đọc nguồn, **không phải independent human adjudication hoặc kết luận gold sai**.

- 4câu dùng từ sold/sales/deliveries nhưng title của bảng là Production. Sản xuất, bán và giao xe không tự tương đương. Một model làm đúng số theo gold có thể đã bỏ qua khác biệt nghiệp vụ này.
- 10câu có published decimal precision khác hơn0,005 so phép tính full precision. Protocol yêu cầu hai chữ số và dùng nguồn tính lại, trong khi bảng có sẵn tỷ lệ làm tròn một chữ số. Đây là mismatch giữa mục tiêu contract và cách báo cáo tự nhiên, không tự là lỗi suy luận.
- 1câu hỏi nhắc tên hàng xuất hiện hai lần, với scope khác nhau; 2câu có published unit rỗng; 1câu phân biệt Total segments với consolidated Group sau reconciliation. Các flags có thể chồng nhau.
- Một cặp bảng KPI có header mang dạng số thay vì nhãn kỳ/đơn vị đầy đủ. Cần quay lại original report/layout, không chỉ tin bảng đã flatten. Flag layout không khẳng định lỗi của tài liệu gốc.

## Ví dụ cần người adjudicate

**`d5a035f3d1`: Trucks sold vs Production.** Question hỏi thay đổi số xe tải bán giữa2016–2017; bảng tên Volkswagen Truck & Bus–Production. Gold tính từ188.234 và167.354. Checklist A và AB abstain vì thiếu sales; frozen scorer cho0. Chưa thể gọi đây là harmful refusal của checklist. Ngược lại, một model tính ra gold không tự chứng minh đã xác minh sales. Phải xác nhận question/source semantics độc lập.

**`cf12fca083`: Customer financing.** Bảng có cùng nhãn dưới Number of contracts và Receivables from. Gold dùng số hợp đồng5935/5672 (~4,6%); models thường dùng khoản phải thu63690/58125 (~9,6%). Câu hỏi không nêu rõ counts hay monetary value. Evidence bind thành công bằng gold operand không giải ambiguity của task.

**`1325b18bfb`: Total segments vs Group.** Bảng có Total segments263134, Reconciliation−27285 và Group235849 (€million). Question “total sales revenue of all segments” có thể dẫn tới total segments; gold cộng reconciliation để ra group. Models đều đọc cột Total segments trong nhiều arms. Đây là scope flag cần adjudication, không sửa gold theo đa số model.

**Rounding/units.** `a660204d2b` có tỷ lệ trong bảng10,2% và phép tính từ528/479 cho10,229645…%. Reading10,2 bị frozen half-cent rule tính sai, dù đây là tỷ lệ hiển thị ở nguồn. `f795ec592b` có gold unit rỗng, prediction “units” bị unit rule tính sai. Một số ratio được model báo dạng0,074 thay vì7,4%; normalized string equality không xử lý hết equivalence về scale. Những điều này cần chuẩn hóa **trước** run kế tiếp; không sửa điểm để cứu kết quả hiện tại.

**Lỗi model thật vẫn tồn tại.** `a92703c96b` có program đúng từ101,5 tới170,1, source recomputation67,5862…%, nhưng checklist A/AB khai67,29. Vì vậy không được đổ toàn bộ điểm thấp cho benchmark. Phải phân loại arithmetic assertion, source selection, semantics, schema và unit/precision riêng.

## Sensitivity để biết score phụ thuộc cách đọc đến đâu

Trên toàn24câu, giữ invalid/abstain policy, diagnostic numeric-only ở precision của đáp án công bố cho standard A21/24 thay vì frozen số+unit16/24; standard AB cũng21/24. Diagnostic này bỏ units và đổi precision, vì thế **không là điểm corrected hoặc xác nhận human truth**, không thay primary. Nó cho thấy cần hoàn thiện readout trước khi đầu tư một confirmation lớn. Program-only và declared-answer cũng khác trên một số response; đổi sang calculator execution là baseline mới phải cấp cùng cho mọi arm.

Không có trường hợp final dependency rỗng ở những outputs được frozen binding filter nhận trong run này; diagnostic sửa lỗ hổng đó không tạo gain trên bank hiện tại. Source/arithmetic filter vẫn có nhiều numeric/unit mismatches được nhận; không dùng nó để tự động chấp thuận kết luận nghiệp vụ.

## Bước tiếp đã chốt

1. Hai người làm **source-only24câu** độc lập theo [packet](SOURCE_RECEIPT_VA_HUMAN_REVIEW.md); giữ blank packet chưa model/gold và phase gold-comparison riêng. Hiện0annotations. Sau đó xác định bộ quy tắc unit/precision, loại task cần thêm nguồn, và rubric đúng/sai/không đủ bằng chứng. Sensitivity adjudicated giữ riêng published score.
2. Discovery5–8người, tập trung một công việc gần đây; [shortlist kênh](RECRUITMENT_SHORTLIST.md) đã chuẩn bị, chưa gửi tin. Chốt workflow và giá trị giảm review burden trước khi xây thêm UI/controller.
3. Xác định một **task contract nguồn-first**: quantity được hỏi, kỳ, đơn vị, formula authority và tiêu chuẩn evidence đủ. Strong single, calculator/source checker và mọi agent đều nhận cùng contract. Contract không được dựng từ đáp án đang kiểm.
4. Nếu tác dụng của coordination vẫn có headroom sau các baseline này, mới khóa một mechanism intervention và confirmation. Nếu không, giữ multi-agent như hệ phân vai cho các luồng thông tin cần thiết trong workload thật, không ép team vào bài toán một bảng mà một solver đủ làm.

## Nguồn external mới chỉ ở bước metadata

[XBRLFiling do tác giả VeriFin công bố](https://huggingface.co/datasets/bethelhall/XBRLFiling/tree/1c1d5b8ff198942e7197c5b0beb9df959c3ecedc) là candidate để kiểm transfer sau này. Đã pin revision, lưu card/license/notice/filing metadata; **chưa tải task file hoặc chạy/chấm model**. Card mô tả600questions,28companies,86filings, nhưng compact release chỉ có rendered evidence, không raw XBRL/retrieval corpus. Card cũng nêu29rows có residual giữa operands và parent; cần audit tolerance, không giả định oracle exact. Dataset card ghiCC-BY-NC4.0 cho compilation; không coi code MIT ở repo khác là quyền cho dữ liệu này. [Intake record](xbrl_external_source_intake.json).

Điều này không mở thêm một benchmark để săn điểm đẹp. Nguồn chỉ được dùng sau oracle/availability gate và split phù hợp; không hứa tái lập đầy đủ VeriFin bằng compact dataset.
