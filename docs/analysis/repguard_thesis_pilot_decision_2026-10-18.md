# Quyết định sau pilot chạy thật — 18/10/2026

## Kết luận hiện tại

**Chưa chốt phương pháp RepGuard này cho đồ án.** Pilot v2 đã hoàn thành
200/200 phản hồi thật trên app riêng `repguard-thesis-real-pilot-20261018`.
Checksum được kiểm, fitting và policy evaluation được tính lại local khớp cloud.
Không dùng mock solver. Bản v1 bị dừng do lỗi làm tròn trung gian được giữ riêng,
không lấy phản hồi v1 thay vào v2.

Trên 20 câu development screen thuộc 20 báo cáo riêng:

| Cách xử lý | Đúng | Lượt gọi khi phục vụ 20 câu | Token trung bình/câu |
|---|---:|---:|---:|
| Chỉ A / Qwen3 8B | 0/20 | 20 | 1.902,0 |
| Chỉ B / Qwen3 14B | 1/20 | 20 | 1.927,8 |
| Cascade cố định | 1/20 | 40 | 3.829,7 |
| EvidenceOnly | 1/20 | 40 | 3.829,7 |
| RepGuard | 1/20 | 40 | 3.829,7 |

RepGuard không tăng độ đúng hoặc tiết kiệm token so với cascade/EvidenceOnly.
So với chỉ B, độ đúng bằng nhau trong mẫu này nhưng token gần gấp đôi.
Gate đã khóa là **FAIL**, giữ nguyên. Coverage approved là 1/20; chỉ có một
câu approved đúng không đủ để tuyên bố hệ thống có precision cao trong thực tế.
Các bootstrap difference bằng 0 khi hai policy có cùng kết quả không chứng minh
hai phương pháp tương đương trên tổng thể.

## Nút thắt đo được

Trên toàn bộ 100 câu, A từ chối 95/100, B từ chối 94/100. Trong history,
A đúng 4/60, B đúng 1/60; trên screen, hợp của cả hai chỉ có 1 câu đúng.
Đây là kết quả của **cấu hình model/prompt/contract hiện tại**, không chứng minh
năng lực nội tại của model thấp. Đây là trần post-hoc của hai output hiện có, không phải oracle được dùng lúc
phục vụ. Với những output này, một router giỏi hơn cũng không có thêm đáp án
đúng để chọn trên 19 câu screen còn lại.

Cả hai learner đã thực sự fit logistic trên outcome thật, có loss trace và
hiệu chỉnh riêng; vấn đề không phải một placeholder chưa huấn luyện. Tuy nhiên
số positive rất ít nên chưa có cơ sở tin rằng competence model đã đủ dữ liệu.

Audit thực thi 100 chương trình tham chiếu bằng evaluator FinQA đã pin: không
có khác biệt với stored gold. Kiểm tra bổ sung biên token số, dấu âm và phần
trăm: không phát hiện trường hợp hard-pass bị ảnh hưởng trong 200 output này.
Các kiểm tra trên không xác nhận toàn bộ diễn giải ngữ nghĩa hay annotation
đều hoàn hảo.

## Hướng tiếp tục giữ nguyên chủ đề

Giữ ứng dụng **hỗ trợ hỏi đáp số liệu báo cáo có bằng chứng**, cùng chủ đề
multi-agent/reputation. Ưu tiên tiếp theo là làm bộ giải tạo được chương trình
tính đúng có nguồn trước khi tiếp tục phức tạp hóa reputation.

1. Hoàn thành chẩn đoán 16 lượt history đã khóa riêng, kiểm tra ảnh hưởng của
   constrained JSON và yêu cầu phân tích trước. Không thay kết quả v2.
2. Khi có contract khả thi, thu history mới cho contract đó và huấn luyện lại
   competence/calibrator. Không gắn xác suất đã học từ contract cũ lên output mới.
3. Tạo khác biệt năng lực có ý nghĩa giữa agent, ví dụ giải trực tiếp, phân rã
   phép tính và kiểm tra nguồn/đơn vị; đo tính bổ sung thực tế. Nhiều lời gọi
   cùng từ chối không tạo được lợi ích multi-agent.
4. Đánh giá vòng sau trên báo cáo chưa dùng phát triển. Baseline single-agent
   phải có cùng tài liệu và công cụ tính/kiểm tra; so thêm cascade cố định và
   phiên bản không dùng history. Báo độ đúng, wrong approval, coverage, chi phí
   và latency cùng nhau. Chỉ nói reputation có lợi khi phép so này ủng hộ.

Đóng góp đồ án cần hướng tới một quy trình xử lý tài liệu có bằng chứng, biết
chuyển tác tử/yêu cầu người kiểm tra và có hiệu quả đo được so với baseline
phù hợp. Chỉ dựng giao diện hoặc gọi nhiều model chưa đáp ứng được mục tiêu đó.
Chưa có kết quả để khẳng định thắng ChatGPT/Claude hoặc bảo đảm điểm bảo vệ.

## Phát hiện khi chẩn đoán contract

Chẩn đoán 16 calls trên 8 history đã hoàn thành, tách riêng khỏi pilot:

| Contract của B | Qua check nguồn/thực thi | Đúng target | Đồng thời đúng và qua check |
|---|---:|---:|---:|
| V2 gốc, dữ liệu thật đã có | 0/8 | 0/8 | 0/8 |
| Bỏ constrained grammar | 0/8 | 0/8 | 0/8 |
| Thêm reasoning trước | 5/8 | 2/8 | 1/8 |

Raw output cho thấy có câu reasoning nhận ra số trong nguồn nhưng status vẫn là
`insufficient_evidence`. Prompt v2 chưa mô tả rõ status của nhánh trả lời thành
công; đây là thiếu sót khi triển khai contract, cần sửa và đo riêng. Không quy
toàn bộ thất bại cho model hoặc kết luận reputation không có ý nghĩa nói chung.
Bản kiểm tra tiếp theo có protocol/source snapshot và tối đa 16 calls history,
thêm hướng dẫn status rõ ràng, so với cung cấp cả schema trong system prompt.

Các output đã qua check vẫn sai do chọn mẫu số, tỷ lệ/giá trị tuyệt đối, hoặc
ngữ nghĩa. Cũng phát hiện ví dụ history cần xem lại cách diễn giải nhãn: CCI
2004 có văn bản nói 8816 sites tương ứng khoảng 83% portfolio, trong khi program
tham chiếu nhân tiếp 8816×83%; ORLY hỏi total five-year return nhưng target là
348−100=248 trong bảng investment-index, còn output lấy tỷ lệ 2,48. Đây là
**cờ cần audit ngữ nghĩa/đơn vị**, không tự ý đổi nhãn hoặc chấp nhận factor100
để nâng điểm. Đối chiếu evaluator chỉ xác nhận phép tính của program tham chiếu,
không giải quyết các cờ này. Vòng dữ liệu ứng dụng cần nhãn/đơn vị được nhóm
kiểm tra độc lập với output của phương pháp.

Kiểm tra bản sửa contract cũng đã hoàn thành 16 calls history:

| Bản sửa | Qua check nguồn/thực thi | Đúng target | Đồng thời đúng và qua check |
|---|---:|---:|---:|
| Mô tả status thành công rõ ràng | 6/8 | 3/8 | 2/8 |
| Thêm cả schema vào prompt | 6/8 | 2/8 | 1/8 |

Chưa đủ chất lượng để chốt phương pháp. Lần demo schema mới trên DISH/2008
phát hiện chương trình tự nhân100 rồi display percent nhân100 lần nữa, tạo
`6906.39%`; raw output và artifact trước sửa được giữ nguyên. Thêm serving guard
đánh dấu pattern này là cần xem lại, không tự sửa số để nâng điểm. Một câu
phép cộng mới trả kết quả số đúng nhưng chép thêm ký hiệu `$` vào token không có
trong nguồn cũng bị chặn. Đây là lý do chuyển nhánh prototype sang **catalogue
ID nguồn + công cụ tính có kiểu**, thay vì yêu cầu model chép số và viết chương
trình tự do. Nhánh mới chưa có reputation/calibrator đã fit và được đo riêng
8 calls history theo protocol đã lưu.

## Kết quả nhánh typed và quyết định triển khai tiếp

Hai probe đã hoàn thành và được tính lại executor local khớp:

| Cấu hình trên cùng 8 history | Qua check | Đúng target và qua check | Output token |
|---|---:|---:|---:|
| Catalogue + typed tools, think=false, cap1536 | 6/8 | 2/8 | 1.553 |
| Cùng messages, native thinking=true, cap4096 | 7/8 | 2/8 | 11.110 |

Thinking xuất hiện thực trong8/8responses; hai cấu hình có cùng hash public
messages. Ngân sách output khác nhau nên không coi đây là so ngang cost.
Không có cải thiện exact-target accuracy trong mẫu8này, không chọn native
thinking làm mặc định chỉ vì lý thuyết. Nguồn sai/năm sai, thứ tự toán hạng,
đơn vị và giới hạn template vẫn là các lỗi cần xử lý. Không thêm model search
hoặc batch lớn tự động sau các probe này.

**Nhánh typed đã qua integration demo thật:** trênDISH/2008, model chọn
`T6C1@0` (goodwill256917) và`T7C1@0` (total assets371999), operation`percent_of`.
Executor trả fraction0.69064, hiển thị69.064%. MộtcallQwen3:14b trênL4,
không current gold, không cached solver answer, không đọc history gold hoặc
calibrator v2 cho quyết định này. Live ID
`live-35960f1760bd4f2c8becfef271ae29b8`. Đây là kiểm thử tích hợp có chủ đích,
không phải tập đánh giá độc lập hoặc bằng chứng về reputation.

Quyết định ở thời điểm bàn giao:

- Giữ hướng ứng dụng số liệu báo cáo có bằng chứng và chủ đề multi-agent/reputation.
  Giữ catalogue nguồn/công cụ tính làm nền prototype vì đã sửa được hai lớp lỗi
  cơ học cụ thể; chưa nói nhánh này có accuracy tổng thể tốt.
- Không chốt learner/policy v2 làm đóng góp chính của đồ án. Không quảng bá
  source-pass là đúng ngữ nghĩa hoặc phép thử8history là xác nhận độc lập.
- Ưu tiên tuần1: nhóm audit nhãn/đơn vị và nguồn cho phạm vi KPI rõ ràng,
  cải thiện chọn đúng hàng/năm/toán hạng, đo lại trên development reports mới.
  Chỉ thêm composition của typed operations khi có task thực yêu cầu; không
  mở rộng UI/PDF để che chất lượng thấp của bộ giải.
- Tuần2–3: phát triển agent tìm bằng chứng và agent giải/kiểm tra có vai trò
  khác nhau, đo năng lực bổ sung; fit lại reputation trên outcome của đúng
  contract mới. Feedback cơ học chỉ là weak signal, không tự coi là gold.
- Tuần4–5: đánh giá trên reports chưa dùng phát triển, so với single-agent mạnh
  được cấp cùng source/tools/budget, cascade cố định và phiên bản bỏ history.
  Hoàn thiện upload/extraction và giao diện audit theo các lỗi thực đo được.
- Tuần6 nếu có: ổn định demo, xử lý failure cases và viết/bảo vệ. Nếu không
  có lợi ích reputation đo được, trình bày giới hạn đó và tập trung đóng góp
  hệ thống đã chứng minh; không hứa điểm cao hoặc tự tạo claim tích cực.

Nhóm có thể phân công đồng thời phần dữ liệu/đơn vị, solver/điều phối và UI/demo/
báo cáo. Số lượng thành viên và tiêu chí chính thức của giảng viên chưa được
cung cấp nên đây là khung công việc, không phải phân công nhân sự đã chốt.

## Prototype và khả năng tái chạy

Đã triển khai backend live riêng trên app mới; không dùng endpoint/model volume
của app Ollama cũ. GPU live chỉ mount model volume, không mount evaluator gold.
Giao diện localhost chọn tài liệu FinQA, nhận JSON tài liệu riêng, sửa câu hỏi,
xem nguồn, phép tính, số token và toàn bộ trace thực. Mỗi lượt chạy là inference
mới. Chưa hỗ trợ trích xuất PDF hoặc cung cấp một sản phẩm hoàn chỉnh cho người
dùng cuối. Lần chạy lại một tài liệu pilot chỉ là integration demo.

Mã tại `thesis_pilot/`; hướng dẫn tại `thesis_pilot/README.md`. Raw inputs,
receipts, source snapshot và output thật tại `results/thesis_real_pilot_v2/`.
Không xóa receipt hoặc kết quả âm để chạy lại dưới cùng run identity.

200 calls ghi nhận 411.256 input+output token; tổng observed request time
610,52 giây, còn collection wall time 1.666,61 giây. Đây là các đại lượng khác
nhau, chưa phải hóa đơn Modal. Chẩn đoán và demo có usage riêng, không cộng
nhầm thành 200 phản hồi của pilot.

## Tình trạng hạ tầng khi kết thúc

Đã kiểm tra app vẫn deployed. Container native-thinking cuối đã tự dừng;
`modal container list --app-id ap-H1QBQza7gdGhq4UhD8FZoe --json` trả danh sách
rỗng sau khi hoàn tất. Backend sẽ khởi động container mới khi người dùng gọi
prototype, có cold start. Server giao diện cục bộ vẫn chạy ở127.0.0.1:8765.
