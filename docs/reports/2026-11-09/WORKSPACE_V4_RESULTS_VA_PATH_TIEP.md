# Vòng workspace thật: đã chạy gì, biết thêm gì, tiếp theo làm gì?

> Đã có bước phát triển tiếp: [research strategy V5](RESEARCH_STRATEGY_V5_VA_CONTRIBUTIONS.md), [relational V5 và nguồn ngoài](RELATIONAL_V5_RESULTS_VA_QUYET_DINH.md). Kết quả V4 dưới đây giữ nguyên.

Chốt sau chấm offline ngày 09/11/2026. **Đã chạy 113 lượt gọi model thật, lưu đủ 36 trajectory trên sáu task. Chưa có bằng chứng để nhận phương pháp multi-agent mới hoặc mở rộng history/reputation.** Kết quả hữu ích nhất của vòng này là một bộ lỗi thật có thể lần lại nguồn, cùng các vấn đề đo lường cần giải quyết trước thí nghiệm lớn.

## Đọc nhanh để hiểu hướng làm tiếp

Đề tài tiếp tục giữ multi-agent và tập trung vào **kiểm chứng, bàn giao và sửa kết quả phân tích dữ liệu/báo cáo**. Hệ thống cần giúp người nhận bảng kết quả biết tác tử đã dùng đúng nguồn, chỉ tiêu, đối tượng và thời kỳ chưa; có xuất đủ đầu ra không; khi nào nên giữ, sửa hoặc chuyển người kiểm.

Lượt này đã nối model với workspace có CSV, JSON, SQLite và PDF, thay vì chỉ đưa một đoạn văn rồi hỏi đúng/sai. Tuy nhiên, đây vẫn là benchmark công khai có biến đổi dữ liệu, chưa là triển khai tại doanh nghiệp hoặc user study. Sáu task thuộc bốn nhóm nguồn có chồng lấp, chưa chứng minh áp dụng rộng giữa các lĩnh vực.

**Việc cần làm ngay:** làm rõ yêu cầu và chuẩn chấm, sửa các trở ngại hoàn thành task, có single-agent baseline mạnh; sau đó mới đo phần lợi ích riêng của tác tử phản biện. Chưa nên tiếp tục tăng số agent hoặc học reputation từ bank này.

## Kết quả đã khóa

A là Qwen3.5:27b; B là Gemma4:26b. AA/BB là tự phản biện, AB/BA là chuyển bản làm thật sang model kia kiểm lại. Mọi workflow dùng cùng source tools; reviewer nhận actual draft/history/artifacts. Direct tối đa 8 calls, review thêm tối đa 4; chi phí policy có tính bản nháp dù artifact được tái sử dụng.

| Workflow | Khớp complete relation/reference trên 6 task | Calls tính cả bản nháp cho policy |
|---|---:|---:|
| A | 1/6 | 34 |
| B | 1/6 | 33 |
| AA | 2/6 | 43 |
| BB | 1/6 | 46 |
| AB | 2/6 | 43 |
| BA | 2/6 | 48 |

**Bảng này chỉ là composite engineering diagnostic của hai block thu dữ liệu**, không là score official-original DataSpace hoặc kết quả xác nhận của một nghiên cứu sáu task liền mạch. Không cộng các calls policy để suy số request thực hoặc hóa đơn: draft được dùng lại. Tổng request corpus thực là 113; input 892.602 tokens, output 29.769 tokens. Cùng call ceilings không có nghĩa cùng lượng compute, token hoặc chi phí thực.

| Task | Điều quan sát được |
|---|---|
| 269 — phân bổ cổ phần | Cả sáu workflow hết call budget và chưa nộp bảng cuối. Trace cho thấy tìm nhiều bảng chưa đúng; đây là completion/retrieval floor, không phải sáu đáp án số đã được thẩm định là sai. |
| 391 — bản ghi bảng cân đối mới nhất | Cả sáu workflow khớp reference. Câu hỏi đã được thêm yêu cầu cột ngày công khai trước inference; giữ nguyên gold. Đây là task adapted. |
| 380 — người quản lý quỹ không mang quốc tịch Trung Quốc | Năm đầu ra dùng tên người/tên quỹ làm proxy cho quốc tịch; một self-review từ chối. Source có bảng thông tin cá nhân và trường Nationality nhưng các đầu ra không dùng đúng liên kết này. Ví dụ rõ về query chạy được nhưng không trả lời đúng thuộc tính cần hỏi; chưa là nhãn human độc lập. |
| 371 — tên viết tắt quỹ và lợi nhuận | Các workflow xuất đủ 12.962 rows nhưng dùng ChiNameAbbr; reference dùng SecuAbbr. Hai cột khác nhau ở 12.787 rows. Câu hỏi chỉ nói “fund abbreviation”: cần independent semantic review, không tự gọi toàn bộ các bảng đó là sai nghiệp vụ. |
| 44 — thủ tục tại lần ghi nhận điều trị mới nhất | A/AA/AB nộp đúng chuỗi tên và thứ tự reference nhưng thừa cột treatmentid; strict scorer chấm 0. Diagnostic hậu nghiệm bỏ riêng cột ID thì khớp, **không sửa điểm gốc**. Các nhánh từ B chưa hoàn tất và có length/token stops. Đây là truy xuất dữ liệu benchmark, không là tư vấn lâm sàng. |
| 35 — đọc số liệu trong PDF | Direct A/B chưa nộp bảng cuối; AA/AB/BA nộp bảng khớp, BB hết token budget. Ba rescues cùng nằm ở **một task**, và self-Qwen cũng cứu được. Không có cơ sở nhận đó là hiệu quả riêng của cross-model. |

Toàn bộ 36 trajectory: **9 khớp reference, 14 có bảng nhưng không khớp strict relation, 13 không có bảng cuối**. Các nhóm là quan sát kỹ thuật, không phải 27 lỗi nghiệp vụ đã được người độc lập gán nhãn. Có 13 tool/schema errors và 10 responses dừng vì output-length cap; không có native thinking text. Source/prompt/provider/model/GPU/parent/artifact/attempt audit PASS trên cả hai block; 113 attempts có 113 terminal responses. Hai synthetic service probes của Gemini nằm riêng, không tính vào corpus; probe đầu chưa ghi được HTTP status, probe sau trả quota0.

## Hai lần dừng kỹ thuật được giữ nguyên

1. Plan `c83c5fa198c76cce65a9c5d4`: guard bắt được automatic source inclusion của Modal làm lộ mã reference reconstruction vào container. Dừng trước khởi tạo GPU/invoke, **0 corpus calls**. Sửa packaging bằng explicit four-file runtime và `include_source=False`, đăng ký lại; không xóa receipt/source ZIP cũ.
2. Plan `6a325835a376d02f1440fadf`: isolation PASS; hoàn thành hai task/12 trajectory/42 calls, rồi dừng trước task380 inference do adapter fingerprint không tái lập. Đối chiếu tìm khác biệt 1 ULP ở bước SQLite đọc chuỗi số. Không nới hash hoặc làm tròn để bỏ qua. Prefix chỉ chấm diagnostic, original six-task study vẫn là **interrupted**, primary contrast để null.
3. Recovery `3af22795afdac39d725c3351`: chuyển numeric text bằng Python trước SQL binding; kiểm toàn bộ bốn workspace còn lại trước inference. Hoàn thành 24 trajectory/71 calls. Không gọi lại hai task cũ; recovery đăng ký trước khi chấm 42 calls cũ. Cả hai block giữ model/prompt/call ceilings, có adapter amendment rõ ràng.

Source intake tải và kiểm SHA256 toàn archive 2.878.651.222 bytes; đủ 96 input files và 12 gold/config files tách volume. Gold/config và reconstruction code không nằm trong runtime tạo 113 responses. Source-only reconstruction trước gold khớp 5/6; sau amendment cột ngày khớp 6/6. Điều này chỉ xác nhận tồn tại một lời giải tái lập được, **không chứng minh cách hiểu duy nhất của mọi câu hỏi**.

33 tests cho tools/trajectory/offline audit PASS. Lượt regression scoped khác gồm 25 kernel tests và 5 source-receipt tests PASS; chưa chạy full repo suite. Kernel `src/repguard/verification` là component riêng, **pilot v4 chưa kiểm chứng lợi ích của kernel như một phương pháp**. Bốn app intake/pilot của vòng này đã stopped/0 tasks theo receipt sau cleanup; không sửa app của người dùng. Không còn job inference mới được lên lịch.

## Nghiên cứu mới làm thay đổi strategy thế nào?

[VeriMAP](https://aclanthology.org/2026.eacl-long.353/) đã có planner-defined verification và refinement; [VerifyMAS v3, 30/10](https://arxiv.org/abs/2605.17467v3) đã có trajectory-level failure attribution. Các khả năng này không đủ để nhận novelty.

[ICR, 01/10](https://arxiv.org/abs/2610.01042) đã tách correction/preservation và dùng no-message revision control; [ARIA, 14/10](https://arxiv.org/abs/2610.20780) đã nghiên cứu học can thiệp sửa lỗi từ execution-verified repairs. Do đó rescue/harm, fixed drafts hoặc learned repair không phải gap mới chỉ vì đưa vào đồ án.

[ToxicBench](https://arxiv.org/abs/2609.37153) đã có field-bound, matched-parent evidence controls trên dữ liệu phân tích; [diagnostic contracts](https://arxiv.org/abs/2609.38761) đã phân biệt authoritative evidence và unknown. Vì vậy “SQL execute thành công nhưng bằng chứng sai” cũng là vấn đề đã có nghiên cứu. Phần đối chiếu chi tiết, mức đã đọc và giới hạn từng paper nằm ở [literature và research question](WORKSPACE_V4_LITERATURE_VA_RESEARCH_QUESTION.md); chưa nhận đã reproduce các method đó.

**Strategy hiện tại:** ưu tiên một nghiên cứu thực nghiệm có kiểm soát và prototype hữu ích, chưa cam kết thuật toán mới. Câu hỏi cần kiểm chứng tiếp là liệu phản hồi chỉ ra vi phạm cụ thể giữa yêu cầu đã cố định và bằng chứng thực thi có giúp sửa đúng hơn neutral recheck, khi dùng cùng nguồn/tools/budget. Đây là hypothesis, không là research gap đã được xác nhận. Cần xác định khác biệt đủ cụ thể với các prior trên trước khi đặt tên method.

## Path tiếp theo và điều kiện chuyển bước

| Bước | Làm gì cụ thể | Điều kiện qua |
|---|---|---|
| 1. Chốt đúng task/measurement | Hai người đọc nguồn độc lập; phân biệt SecuAbbr/ChiNameAbbr, output-only fields, duplicates/order, scope/unit. Giữ reference score và semantic review riêng. | Reviewers khóa source-only đáp án trước khi xem gold/model outcomes; bất đồng có adjudication. Có 12 phiếu trống, hiện 0 hoàn tất. |
| 2. Sửa completion floor | Cải thiện tìm schema/thuộc tính; output contract không dùng gold; kiểm length/context và chi phí đọc history. Dùng task development, đăng ký adapter changes riêng. | Chứng minh công cụ và baseline đủ khả năng hoàn thành task trước khi so thuật toán. Shape correction là gain của interface/checker, chưa là coordination gain. |
| 3. Bổ sung baseline mạnh | Single đủ tools, single tiếp tục với cùng checker/resources, self/cross review; strong frontier model hoạt động thật. | Model/API quota khả dụng; lưu actual calls/tokens/time. Gemini4Argon hiện quota0 nên điều kiện này chưa qua. |
| 4. Mechanism experiment | Fixed real drafts; feedback diagnostic/neutral/shuffled; cùng source access và ceilings; tách errors do thiếu nguồn, chọn sai nghĩa, output shape và revision. | Khóa mechanism/prior comparison, nhãn đáng tin, grouping và sample-size analysis trước calls. Không dùng sáu task này làm confirmation. |
| 5. Kiểm transfer và sản phẩm | Giữ nguyên policy sang source/workload chưa dùng thiết kế; ghi công sức mapping. Discovery 5–8 người đang làm báo cáo thật, rồi task study có chấm độc lập. | Có workflow lặp lại, dữ liệu được phép dùng và đo được lỗi cuối/thời gian kiểm toàn bộ. Hiện 0 users/interviews; benchmark không thay user study. |

Để ứng dụng rộng, dùng chung các khái niệm **entity, metric, period, population, unit và completeness**, còn adapter/source mapping phải được kiểm và tính công sức cấu hình. Bắt đầu từ báo cáo phân tích/thí nghiệm trong lab hoặc nhóm data/software dễ tiếp cận; vận hành/tài chính là mục tiêu transfer. Không cần xây đồng thời nhiều ứng dụng để chứng minh quy mô.

History/reputation vẫn đóng. Chỉ xem lại nhánh đó khi có nhiều hành động sửa với utility khác nhau, dự báo được và giữ lợi ích trên nguồn mới. Không fit history để giải thích một rescue task PDF hoặc để giữ tên method cũ.

## Tài liệu và artifact để xem tiếp

- [Protocol, amendments và lệnh chấm lại](WORKSPACE_V4_PROTOCOL_VA_RESEARCH_UPDATE.md).
- [Bảng 36 case và chi phí, composite diagnostic](workspace_v4_composite_engineering_error_bank.json).
- [Flags hậu nghiệm về measurement — không sửa score](workspace_v4_posthoc_measurement_flags.json).
- [Biên nhận dừng app](workspace_v4_cleanup_receipt.json).
- [Literature matrix và research question](WORKSPACE_V4_LITERATURE_VA_RESEARCH_QUESTION.md).
- [Bộ tìm người dùng](USER_DISCOVERY_KIT.md); phiếu source-only local tại `results/workspace_v4/source_only_review/`.

Raw requests, attempts, trajectories, exports, source snapshots và scores ở `results/workspace_v4/`. Old cycle01/02 primary/gold/source snapshots giữ nguyên.
