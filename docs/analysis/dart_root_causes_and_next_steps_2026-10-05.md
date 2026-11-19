# Vì sao ECRT/DART chưa thắng — điều tra cơ chế và hướng sửa

**Cập nhật 05/10/2026, giờ Việt Nam.** Báo cáo này bổ sung kết quả can thiệp có kiểm soát vào phân tích ngày 30/09 và đợt full judge ngày 04/10. Các kết luận chính dựa trên code, ledger và replay đã thực thi; không suy đoán rằng một ý tưởng mới chắc chắn thành công.

## 1. Kết luận dễ hiểu

**Mình có tín hiệu hữu ích, nhưng cách biến tín hiệu thành quyết định chưa đủ hiệu quả.** DART đang phải chọn giữa nhiều policy từ rất ít nhãn kiểm chứng cho mỗi lựa chọn. Việc hiệu chỉnh điểm cho đúng về trung bình không đảm bảo policy có điểm cao nhất thật sự là policy tốt nhất. Trong khi đó, đối chứng đơn giản dùng toàn bộ nhãn để chọn một agent mạnh thường ổn định hơn.

Đã kiểm tra một giả thuyết hấp dẫn: bỏ nhị phân hóa, giữ điểm liên tục của judge. Nó giúp dự báo xác suất tốt hơn, **nhưng chưa tăng kết quả routing trong phép thử đã khóa**. Vì thế không thể nói “đã tìm thấy lỗi chính là threshold 0,5, sửa là thắng”.

Hướng có bằng chứng tích cực hơn là **dùng nhãn hiệu quả hơn và giảm sai số khi chọn policy**. Trên đúng tập nhãn của DARTContrast với judge, một bộ chọn đơn giản dùng cả hai phần nhãn tăng từ **63,90 lên 68,90 task/168**. Tuy vậy, nó chưa thắng các control mạnh. Đây là hướng sửa đáng tiếp tục, chưa phải phương pháp đủ bằng chứng để nộp bài mạnh.

## 2. Đã hoàn thành gì trong lượt này?

| Công việc | Trạng thái / số lượng |
|---|---|
| Kiểm tra đợt real judge trước | 2.352/2.352, hoàn tất; gate cải thiện không đạt |
| Đối chiếu input judge với log và instruction gốc | 2.352 hash khớp |
| Đối chiếu nhãn với evaluator chính thức | 2.352 trường hợp khớp |
| Thiết kế mới | 2 channel × 2 acquisition × 5 fold × 20 seed × 3 budget = 1.200 cấu hình |
| Biến thể mỗi cấu hình | 12; tổng 14.400 lượt chọn policy ở bản chuẩn v2 |
| Tái tạo phương pháp gốc | Khớp toàn bộ kết quả Original; xác suất lấy mẫu, index và policy được kiểm tra |
| Kiểm tra gold-only control | ZeroHT + uniform khớp AuditOnly ở mọi budget/seed/task |
| Kiểm thử code | 236 tests passed; 73,04 giây |
| Suy luận model mới trong lượt điều tra này | 0 |
| Holdout MMLU420 và AppWorld challenge | Chưa mở outcome |

**Phân biệt đơn vị thực nghiệm:** 2.352 là các lượt Qwen judge thật đã chạy qua Modal. 14.400 là số lượt thuật toán chọn policy được chạy trên nhãn của trajectory thật đã lưu; không phải 14.400 solver/judge calls mới. Audit budget trong replay là số nhãn gold được phép tiết lộ cho learner, không phải số nhãn mới do con người trả phí đánh giá. Không có kết quả model giả hoặc outcome tự tạo.

Dữ liệu phát triển gồm 14 agent, 168 task, 56 generator của AppWorld normal, phiên bản 0.1.0. Pool chính thức có commit `c1f56015cf7c3441ff1933f5bfbec879798d7bbe`. Các experiment cũ, gồm pilot gate judge, đã xem tập này; chia fold trong learner không biến toàn bộ nghiên cứu thành kiểm chứng độc lập.

## 3. Đọc bảng kết quả như thế nào?

Mỗi số là số task thành công trung bình trên 168 task, qua 20 seed audit. Budget chính là 10% số ô lịch sử task–agent trong outer-train. Không coi 20 seed là 20 tập test độc lập.

**Can thiệp cùng tập audit** giữ nguyên task, fold, seed, ngân sách, nhãn C và S đã mua, xác suất lấy mẫu và policy bank, trừ đúng thành phần mà tên biến thể chỉ ra. C là phần xây dựng/hiệu chuẩn; S là phần chọn policy; T là phần đánh giá. Các learner không đọc gold T trước khi chọn hành động.

### Bảng chính: acquisition DARTContrast, ngân sách 10%

| Cách xử lý đúng tập nhãn đó | Self-report | Real judge |
|---|---:|---:|
| Original: categorical proxy + HT, 17 policy | 67,40 | 63,90 |
| ZeroHT: bỏ proxy | 61,45 | 60,25 |
| AgentPriorHT: chỉ dùng trung bình agent từ C làm proxy | 64,85 | 65,10 |
| BinaryRidgeHT: hiệu chuẩn ridge trên bit | 66,05 | 62,70 |
| ContinuousRidgeHT: cùng ridge trên điểm liên tục | 66,05 | 63,30 |
| RawHT: điểm thô, không hiệu chuẩn | 61,95 | 64,05 |
| Binary14HT: chỉ giữ 14 policy constant | 66,35 | 63,60 |
| BinarySN: chuẩn hóa phần hiệu chỉnh | 64,20 | 65,70 |
| ZeroSN: không proxy, có chuẩn hóa | 64,65 | 64,80 |
| SGlobal: trung bình có smoothing trên nhãn S | 62,05 | 65,40 |
| CSGlobal: cùng learner, dùng cả C và S | **71,55** | **68,90** |
| CSStratifiedHT: dùng C và S, có trọng số stratum và xác suất audit | 67,30 | 68,00 |

Đối chứng bên ngoài, cùng **số nhãn** nhưng tập lấy mẫu khác: UniformAuditGlobal **69,70**, PairedGlobal **71,95**. Không có biến thể nào trong 4 tổ hợp channel/acquisition tại budget chính đạt CI95% chênh so UniformAuditGlobal hoàn toàn dương.

Tất cả kết quả 5%, 10%, 20%, cả acquisition uniform và contrast, có ở [bảng đầy đủ](dart_same_audit_tables_2026-10-05.md). Không chọn riêng budget thắng để đổi kết luận.

## 4. Nguyên nhân thứ nhất: ECRT cũ có giới hạn đại số ở tầng quyết định

Đây là kết luận đã truy vết từ code và grid Week 3, không phải suy luận từ AppWorld mới.

ECRT cũ hiệu chuẩn một bit feedback bằng cùng một hàm cho các agent trong môn nguồn:

`p(F) = p_minus + (p_plus − p_minus) × F`.

Khi mọi agent có cùng số history và cùng transfer weight, nếu `p_plus > p_minus`, phép biến đổi này giữ nguyên thứ hạng agent. Với feedback oracle, posterior mean còn bằng FixedBorrow về đại số. Trong 129 ô same/related ở noise 25%, rank giống FixedBorrow trong **129/129 ô**. Trong 417/546 ô unrelated mỗi regime, transfer weight bằng 0 nên cả hai trả về cùng prior.

Nói đơn giản: **sửa thước đo nhưng thường không thay người được chọn**. Brier có thể tốt hơn trong khi câu trả lời cuối rất ít đổi. Weighted vote còn có thể để nhiều model yếu đồng ý sai lấn át model mạnh.

Cách sửa phải tác động vào thông tin phân biệt **agent nào tốt cho task nào** và quyết định cuối, không chỉ một phép hiệu chuẩn chung. DART trên AppWorld đã thay kiến trúc; không được lấy giới hạn đại số của ECRT làm lời giải thích duy nhất cho DART hiện tại. Xem [điều tra ECRT trước đó](ecrt_dart_failure_forensics_2026-09-30.md).

## 5. Nguyên nhân thứ hai: judge quá tự tin và chưa xác minh đúng điều kiện hoàn tất

### 5.1. Cấu hình cần nói chính xác

Đợt judge Qwen3:14b vừa chạy dùng **`think=false`, `num_predict=128`**, temperature 0. Đây là judge chấm trajectory, không phải solver thinking trong những đợt MMLU/AppWorld trước. Không có phép so sánh cùng-input judge thinking/direct trong đợt này; không thể kết luận “thinking không cứu được judge”.

### 5.2. Độ tin cậy của điểm số

| Nhóm xác suất judge | Số trường hợp | Xác suất judge trung bình | Tỷ lệ thành công thật |
|---|---:|---:|---:|
| p < 0,5 | 699 | 0,057% | 1,288% |
| 0,5 ≤ p < 0,9 | 560 | 60,795% | 14,821% |
| p ≥ 0,9 | 1.093 | **98,989%** | **45,563%** |

Đây là chẩn đoán hậu nghiệm trên toàn tập, không phải bảng calibration được phép đưa nguyên vào learner. Nhóm judge gần như chắc chắn thành công thực tế sai nhiều hơn đúng.

Trong **1.072 false positive**, có **512 log không bị cắt**; **391** trong số này còn có p≥0,9. Có 348 FP với check đáp án sai, trong đó 173 chỉ sai check đáp án; 899 có ít nhất một loại failed check khác. Các nhóm có thể chồng lấn. Không thể quy tất cả cho clipping hay thiếu context.

### 5.3. Đi sâu vào log: phân biệt chạy code xong với làm đúng nhiệm vụ

Lấy ba ví dụ theo thứ tự hash cố định trong nhóm FP p≥0,9, không clipping; không chọn thủ công ví dụ đẹp. Các case chi tiết giữ trong `results/dart_judge_errors_v1/examples_private.json`.

- **Ví dụ đếm danh sách:** task hỏi số hoạt động còn chưa làm. Note có ba dòng hoạt động chưa làm và một ký hiệu `[ ]` ở tiêu đề để giải thích định dạng. Solver dùng phép đếm chuỗi trên toàn note, đếm cả ký hiệu minh họa, trả **4**; evaluator xác nhận đáp án **3**. Nội dung note và phép đếm đều xuất hiện trong log đầy đủ. Judge vẫn trả **1,0**. Đây là lỗi ngữ nghĩa có thể kiểm tra trực tiếp từ bằng chứng, không cần thêm hidden state để nhận ra.
- **Ví dụ xử lý lời mời:** sau lỗi regex, solver thêm điều kiện để bỏ qua các tin nhắn không match rồi báo thành công. Đợt chạy cuối không exception, nhưng các check thay đổi trạng thái yêu cầu vẫn thất bại. Log không in đầy đủ các giá trị trung gian; chưa đủ căn cứ xác định chính xác từng nhánh đã chạy.
- **Ví dụ cập nhật danh sách bạn:** code sửa lỗi API rồi kết thúc thành công, nhưng evaluator xác nhận tập bạn được thêm không đúng. Không exception không đồng nghĩa hậu điều kiện đúng; log thiếu một số giá trị để tự xác minh đầy đủ.

**Điều đã xác định:** judge cho điểm cao trên những trajectory vi phạm yêu cầu, kể cả khi bằng chứng sai hiện ngay trong log. **Điều chưa xác định:** quá trình nội tại khiến model sai; chưa có counterfactual che câu báo success, bật thinking, hoặc thêm readback trên cùng case để định lượng từng yếu tố.

Hướng sửa: tạo checklist yêu cầu và bằng chứng hậu điều kiện; dùng readback quan sát được khi có; tách “có bằng chứng hoàn tất” khỏi “chỉ không thấy exception”; cho phép abstain. Kiểm tra thinking bằng thí nghiệm cùng input và ghi token/latency thực tế. Không cho hidden evaluator/nhãn test vào prompt. Chưa có lý do để lập tức chạy lại toàn bộ 2.352 case trước pilot có kiểm soát.

## 6. Nguyên nhân thứ ba: ước lượng không chệch vẫn có thể chọn nhầm người thắng

Ước lượng của một policy cố định có dạng:

`giá trị ≈ trung bình proxy + trung bình(A/q × (gold − proxy))`.

`A` cho biết nhãn đã được audit; `q` là xác suất được audit. Trong điều kiện thiết kế hiện tại, proxy/policy cố định trước S audit, công thức HT hiệu chỉnh được sai lệch kỳ vọng cho policy cố định. Nhưng bước tiếp theo lấy **max của 17 ước lượng nhiễu**. Lựa chọn có thể thắng vì sai số dương lớn, không phải vì thật sự tốt.

Trên judge ở budget 10%:

| Thiết kế | RMSE giá trị candidate trên S | Mức lạc quan của candidate được chọn | Nhãn S trùng hành động policy được chọn, trung bình |
|---|---:|---:|---:|
| RandomHistory | 0,13081 | +0,20410 | 9,53 |
| DARTContrast | 0,11514 | +0,16804 | 11,19 |

Các số đo sau cùng dùng full S gold để chẩn đoán, không được đưa lại vào quyết định. “11,19 nhãn” là số ô đã audit trùng tuyến hành động của policy được chọn, không phải effective sample size của toàn thiết kế.

### Phép thử chuẩn hóa

Giữ nguyên audit của judge/DARTContrast, ZeroHT đạt **60,25**, ZeroSN đạt **64,80**: tăng **2,708 điểm %**, CI95% **[+0,923; +4,554]**. Khi uniform, 62,85→66,55: tăng **2,202 điểm %**, CI **[+0,060; +4,256]**. Điều này chứng minh thay estimator có tác động trong replay này, phù hợp với vấn đề biến động số nhãn/weight.

Nhưng chuẩn hóa với proxy không phải thuốc chữa chung: BinarySN so Original tăng 63,90→65,70 ở judge, CI còn qua 0; ở self-report/DARTContrast lại **giảm 67,40→64,20**, CI chênh **[−3,452; −0,446] điểm %**. Không được lấy cải thiện ZeroSN để hứa chuẩn hóa mọi estimator sẽ thắng. SN có thể chệch; không gán cho nó một chứng nhận an toàn chưa chứng minh.

### Bớt ba policy kNN có cứu được không?

Không thấy bằng chứng: judge/DARTContrast 63,90→63,60 khi chỉ giữ 14 constant. Chênh **−0,179 điểm %**, CI **[−0,863; +0,536]**. Việc thêm ba candidate không đủ giải thích khoảng thua hiện tại. Vấn đề nhiễu khi chọn giữa 14 agent vẫn còn.

## 7. Nguyên nhân thứ tư: cách dùng nhãn và mục tiêu chọn policy chưa tận dụng tốt ngân sách

Thiết kế cũ dành khoảng một phần ba nhãn cho C để xây router/calibration, phần còn lại cho S để chọn policy. Nhãn C **có được dùng**, nhưng không được gộp trực tiếp vào ước lượng giá trị agent toàn bộ train. Vì vậy không nên gọi chúng là “nhãn bị bỏ đi”; vấn đề là cách sử dụng gián tiếp có thể kém hiệu quả so với control dùng toàn bộ nhãn.

Phép thử sạch hơn so sánh hai learner giống nhau, trên cùng acquisition, chỉ thêm các nhãn C vốn đã nằm trong ngân sách:

| Acquisition/channel | SGlobal | CSGlobal | Δ accuracy [CI95%], điểm % |
|---|---:|---:|---|
| Uniform, cả hai channel | 66,65 | 66,90 | +0,149 [−1,518; +1,905] |
| DARTContrast/self-report | 62,05 | 71,55 | **+5,655 [+3,185; +8,065]** |
| DARTContrast/judge | 65,40 | 68,90 | **+2,083 [+0,179; +4,018]** |

Đây là hiệu ứng của **thêm nhãn C vào cùng learner trên đúng các case này**. Nó còn thay phạm vi training từ S sang C∪S; không tách riêng tác dụng tăng số nhãn khỏi việc phủ thêm generator. Hiệu ứng nhỏ ở uniform cho thấy tương tác với acquisition và phân phối dữ liệu, không phải định luật rằng split luôn là lỗi chính.

So CSGlobal với Original trong DARTContrast/judge: tăng **5,00 task/168**, tương đương **2,976 điểm %**, CI **[+0,298; +5,626]**. So UniformAuditGlobal: **−0,476 điểm %**, CI **[−2,470; +1,607]**. Self-report CSGlobal 71,55 so Uniform 69,70 có CI **[−1,012; +3,333] điểm %**. Chưa có superiority.

CSGlobal dùng trung bình không sửa unequal inclusion, trong khi S được lấy mẫu thích nghi. Nó là đối chứng chẩn đoán mạnh, **không phải một estimator không chệch hay DART mới đã hoàn thiện**. CSStratifiedHT có tính đến stratum/q đạt 68,00 ở judge; bằng chứng chưa đủ để quyết định chính xác cách gộp tối ưu.

## 8. Giả thuyết đã kiểm tra nhưng chưa được xác nhận là cách cứu DART

### 8.1. Giữ điểm liên tục

Judge raw AUC khoảng **0,7947**; threshold làm mất thứ tự điểm (AUC binary khoảng **0,6882**). Mất thông tin là thật, nhưng lợi ích routing không tự suy ra từ AUC.

Trong cùng họ ridge, chỉ đổi đầu vào bit→điểm liên tục:

- Brier trên S giảm **0,172392→0,158111**.
- Judge/uniform: **65,25→64,65**, Δ **−0,357 điểm %**, CI **[−1,101; +0,388]**.
- Judge/DARTContrast: **62,70→63,30**, Δ **+0,357 điểm %**, CI **[−0,268; +0,982]**.

Đây là phép thử của **một calibrator đã khóa**, không phủ định mọi cách dùng continuous score. Nó bác bỏ khẳng định quá mạnh rằng chỉ cần giữ điểm liên tục là đủ sửa vấn đề.

### 8.2. Bỏ feedback hoàn toàn

Không phù hợp với bằng chứng: cùng q và audit, DARTContrast/judge Original **63,90**, ZeroHT **60,25**; CI chênh ZeroHT−Original **[−3,750; −0,714] điểm %**. Self-report cũng mất điểm khi bỏ proxy. Feedback có ích trong estimator hiện tại, dù cả hệ thống chưa thắng control. Không thể suy ra “feedback vô dụng”.

### 8.3. Chỉ tối ưu acquisition

DARTContrast giảm RMSE candidate so RandomHistory nhưng test routing judge lại 63,90 so 64,60. Mục tiêu acquisition hiện tối ưu một xấp xỉ diagonal của sai số contrast. Nó dùng `m(1−m)+0,01`, chưa mô hình đầy đủ sai lệch proxy và joint inclusion/covariance của pivotal sampling. Đây là giới hạn đọc trực tiếp từ thuật toán; chưa có can thiệp riêng chứng minh phần bỏ sót covariance là nguyên nhân cụ thể của khoảng thua.

Phương sai của contrast còn phụ thuộc sai số **giữa các agent trên cùng task**. Một proxy tốt về Brier tổng thể không nhất thiết giúp xếp đúng hai policy đang cạnh tranh. Do đó cần tối ưu/đánh giá sai số contrast và regret khi chọn policy, không chỉ Brier hoặc RMSE trung bình.

## 9. Vì sao đối chứng đơn giản thắng, còn các paper khác thì sao?

**Control thắng đã được đo trực tiếp:** UniformAuditGlobal và PairedGlobal dùng toàn budget để học chất lượng agent; không cần fit một router phức tạp từ quá ít nhãn. Retrospective best single đạt 82/168, cho thấy chọn được một agent global mạnh đã là mục tiêu khó đánh bại. Con số 82 là diagnostic dùng full gold, không phải baseline học hợp lệ ở budget thấp.

**PairedGlobal** giữ các đánh giá agent cùng task gần cân bằng. Kết quả 71,95 tốt hơn Uniform 69,70, nhưng CI của chênh vẫn qua 0; chưa thể gọi pairing là nguyên nhân thắng đã được xác nhận thống kê. Oracle 134/168 chỉ cho thấy tiềm năng bổ trợ, không cung cấp tín hiệu quan sát được trước khi route.

**Các phương pháp công bố chưa được so trực tiếp trong cùng protocol thì chưa thể nói đã đánh bại DART trên dữ liệu này.** Điều học được từ literature:

| Nguồn | Điểm liên quan và giới hạn chuyển sang bài này |
|---|---|
| [PPI++](https://arxiv.org/html/2311.01453v2) | Điều chỉnh trọng số dự báo để tăng hiệu quả suy luận; gợi ý không buộc feedback luôn đóng góp cố định. Kết quả tiệm cận iid không tự trở thành bảo đảm chọn policy tốt hơn với pivotal/adaptive audits. |
| [Cross-PPI](https://arxiv.org/html/2309.16598v2) | Cross-fitting giúp mỗi nhãn phục vụ học predictor và suy luận. Cần thiết kế lại đúng giả định; S phụ thuộc C qua acquisition nên không được đảo C/S rồi mặc nhiên tuyên bố độc lập. |
| [Confident off-policy selection](https://proceedings.mlr.press/v130/kuzborskij21a.html) | Chọn policy có xét độ bất định và bias, thay vì chỉ argmax điểm. BinarySN ở đây chỉ là ablation, không phải tái hiện đầy đủ thuật toán/confidence bound của paper. |
| [Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html) | Prediction và chủ động mua nhãn đã có tiền lệ; “calibrate + active audit + correction” tự nó chưa đủ novelty. |
| [CABS](https://arxiv.org/html/2607.09015v1) | Kết hợp nhánh true reward và surrogate, có phân tích robustness theo giả định. Setting quan sát true reward của arm đã chọn khác setting phải mua nhãn archive của mình; cần tính lại quyền truy cập và cost. |
| [SELECT-LLM](https://arxiv.org/html/2510.09418v2) | Routing với giới hạn annotation là đối chứng gần cần xem xét. Annotation theo reference query và thông tin model phải được quy về ngân sách tương thích trước khi so số. |

## 10. Hướng tiếp theo nên làm: sửa learner trước khi tăng GPU

### Bước 1 — xây learner dùng đủ nhãn và có nhánh gold-only mạnh

**Ưu tiên cao nhất.** Giữ control UniformAuditGlobal/PairedGlobal. Khởi đầu với acquisition độc lập với nhãn, toàn budget, chia fold theo generator trước khi đọc gold; dùng cross-fitting để học proxy ngoài fold và hiệu chỉnh trong fold. Bắt đầu với constant-agent candidates để cô lập lợi ích đánh giá, sau đó mới thêm contextual router.

Mỗi nhãn có thể tham gia train proxy cho fold khác và đánh giá trong fold của nó. Không dùng nhãn của một fold để fit proxy rồi tự đánh giá bằng chính nhãn đó. Nếu tái sử dụng adaptive audits, phải phân tích phụ thuộc lựa chọn riêng; không áp công thức iid một cách máy móc.

### Bước 2 — làm feedback tùy chất lượng, không ép nó luôn cải thiện

Giữ một estimator chỉ dùng gold và một estimator dùng calibrated feedback. Trọng số/control-variate học từ training phù hợp thiết kế, không chọn bằng T gold; luôn có lựa chọn hệ số 0. Mục tiêu là giảm sai số **chênh lệch policy**, không chỉ dự báo đúng từng ô. Cần đối chứng PPI++/Cross-PPI phù hợp quyền truy cập; ghép các thành phần đã biết chưa phải novelty.

### Bước 3 — chỉ chuyển policy khi lợi ích đủ rõ

So với baseline mạnh bằng contrast uncertainty. Nếu chưa đủ bằng chứng, giữ baseline. Cần xử lý bias và joint inclusion hoặc chọn sampling có variance tính được. “Có fallback” không tự đảm bảo finite-sample safe improvement; phải chứng minh hoặc chỉ báo là heuristic.

Đánh giá rescue, harm, số lần switch, regret và cost. Nếu không switch thì không claim phương pháp mới tốt hơn; nếu switch sai nhiều thì sửa tín hiệu ra quyết định.

### Bước 4 — sửa verifier bằng pilot có kiểm soát

Thiết kế một mẫu development theo hash, trải các generator/agent, không chỉ lấy FP đã biết. So cùng input giữa judge direct/thinking và checklist bằng chứng; dùng ba case trên để unit-test cơ chế, không dùng chúng làm bằng chứng tổng quát. Chỉ mở rộng nếu cải thiện **decision value** sau hiệu chuẩn, không chỉ parse validity/Brier. Ghi đủ token, thời gian, truncation và abstention.

### Bước 5 — bổ sung tín hiệu task và kiểm chứng độc lập

Nếu learner global đã cạnh tranh, mới thử biểu diễn task/skill từ instruction và thông tin cho phép trước routing, học trên construction/development. Không dùng outcome, ID generator như đáp án, hay trajectory tương lai của task test làm feature miễn phí. Sau đó khóa một phương pháp, một endpoint chính, budget/cost, baseline và quy tắc dừng; đánh giá độc lập trên split chưa xem và benchmark thứ hai tương thích.

## 11. Điều kiện để thành bài phương pháp mạnh

Hiện tại chưa đủ claim DART vượt trội. Một bài thuyết phục cần đồng thời:

1. Định nghĩa đúng bài toán thực tiễn: dùng lịch sử tự báo cáo không đáng tin để phân công agent, khi kiểm chứng kết quả có giá và budget hữu hạn.
2. Đóng góp thuật toán hoặc lý thuyết khác rõ PPI/active inference/routing đã có; ví dụ thiết kế audit cho policy contrasts dưới cấu trúc lỗi và chi phí thực, **nếu** thật sự có kết quả mới.
3. Thắng control đơn giản mạnh và các baseline paper liên quan dưới cùng quyền truy cập, cùng budget, với xác nhận độc lập. Các CI exploratory hiện tại không đủ.
4. Đo tổng cost: inference solver, verifier, audit, latency. Archive hiện thiếu metadata cost đồng nhất nên chỉ so label budget/invocation, chưa claim rẻ hơn về USD/GPU.
5. Thử feedback quality shift, agent/skill corruption và failure modes có ý nghĩa vận hành; không chỉ corruption nhân tạo dễ.

**Đầu ra hiện tại:** HistRepEval/evaluation evidence + chuỗi phát hiện giới hạn + DART candidate chưa đạt superiority. **Đầu ra đang hướng đến:** evaluation đi kèm phương pháp quyết định/audit vượt control trong điều kiện cụ thể, giải thích được vì sao và khi nào có ích. Không có cách bảo đảm acceptance A/A*; một kết quả âm được phân tích kỹ có giá trị, nhưng không thay thế bằng chứng cần thiết của một claim phương pháp thắng.

## 12. Tái lập, sửa lỗi số học và giới hạn kết luận

- Protocol/code mới khóa ở commit `aec2645`; sửa thứ tự số học HT ở `d9447db` trước v2. v1 được giữ nguyên. Ở v1, phân phối phép mean qua hai tổng tạo sai số làm tròn tại các tie non-baseline; Original vẫn khớp, nhưng ZeroHT/uniform lệch nhẹ so AuditOnly. v2 giữ đúng thứ tự phép toán gốc và thêm assertion bằng nhau toàn bộ. Chỉ nhóm ZeroHT/uniform thay outcome giữa v1/v2; ở 10% từ 62,65 về đúng 62,85. Đây là lỗi tái lập trong ablation mới, không giải thích thất bại DART cũ.
- CI bootstrap theo generator sau trung bình seed, 5.000 draws; exploratory, chưa chỉnh nhiều phép thử, phụ thuộc tập/fold development hiện tại. Không cộng các mức cải thiện của các can thiệp như thể chúng là các nguyên nhân độc lập.
- Full S gold chỉ dùng cho diagnostic sau khi action đã khóa. Per-task predictions và evaluator traces giữ trong `results/`, không xuất lên Git. File aggregate có checksum và nguồn tái lập.
- Kiểm tra hàm/tests không chứng minh mọi code bug đã bị loại bỏ. Bằng chứng cụ thể hiện có là tái tạo khớp ledger/proxy/actions, cô lập quyền truy cập gold, đối chứng census/finite population và control invariance.

Các lệnh:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python run_dart_same_audit.py --output results/dart_same_audit_reproduction
.venv/bin/python analyze_dart_judge_errors.py
.venv/bin/python report_dart_same_audit.py
```

Lệnh replay yêu cầu archive normal và specs 0.1.0 đã giải nén đúng đường dẫn; không tự tải dữ liệu hoặc mở challenge. Script report đọc bản chuẩn `results/dart_same_audit_v2`, không tự nhận thư mục reproduction. Artifact v2 đã đầy đủ.

Tài liệu kèm: [protocol](dart_same_audit_protocol_2026-10-05.md), [toàn bộ bảng](dart_same_audit_tables_2026-10-05.md), [aggregate và provenance](dart_same_audit_aggregate_2026-10-05.json), [bằng chứng lỗi judge](dart_judge_error_evidence_2026-10-05.json), [đợt full run trước](dart_full_run_assessment_2026-10-04.md).
