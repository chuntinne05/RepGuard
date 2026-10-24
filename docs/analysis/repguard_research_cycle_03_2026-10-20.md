# Vòng 3: sửa có phạm vi và đối chứng khác họ model

**Hoàn tất264 lượt suy luận mới trên24 câu; chưa có phương pháp reputation
thắng baseline.** Cả scoped-repair144 và đối chứng bổ sung120 đều audit PASS.
24 Qwen direct outputs được reuse có lineage, không tính lại thành24 calls mới.

## Kết quả chính được khóa trước inference

24 TAT-QA TRAIN arithmetic contexts,144 lượt suy luận thật,0 mock,0 unresolved,
0 output-length stops. Audit9 frozen source files, prompt hashes, model digest,
GPU L40S và re-execution của144 responses: PASS. Không dùng gold trong prompt,
không mount evaluation volume lên GPU; original primary sources không đổi.

Chấm bằng **evaluator TAT-QA gốc**, không phải FinQA round5; scale do model
dự đoán. Kết quả dưới đây là trên24 context đã chọn, không là official test score.

| Workflow | Đúng /24 | Executable /24 | Calls/câu | Mean eval giây/câu |
|---|---:|---:|---:|---:|
| Plain PoT | 19 | 22 | 1 | 8.03 |
| KEEP có bindings | 15 | 18 | 1 | 7.23 |
| Sửa evidence E | 15 | 18 | 2 | 15.23 |
| Sửa operation/unit O | 16 | 19 | 2 | 15.38 |
| Ghép EO | 15 | 18 | 3 | 23.38 |
| Self1 cùng binding contract | 15 | 18 | 2 | 14.93 |
| Self2 cùng binding contract | 15 | 18 | 3 | 22.22 |

Oracle union KEEP/E/O/EO chỉ16, thấp hơn Plain19. Có1 scoped-only correct case
so với các controls, gate cần ít nhất2 và oracle lớn hơn best control ít nhất2,
nên **FAIL**. Không fit learner. EO và Self2 có cùng correctness mask; bootstrap
hiệu trên mẫu là[0,0] và McNemar p1, không phải bằng chứng tương đương tổng thể.

Thu mới321132 input tokens và35330 output tokens. Tổng calls của các workflows
đã charge lại KEEP; không nhầm các shared cached generations thành calls miễn phí.
Eval duration không bao gồm startup, idle, CPU/memory/storage hay hóa đơn Modal.

## Nguyên nhân đã xác định từ trace

**Ràng buộc generation tạo lỗi thực thi không cần thiết.** Có5 câu trung bình
mà model đã tính đúng nhưng dùng divisor2/3. Binding contract chỉ cho một tập
constants và yêu cầu dùng `len(...)`, nên lời giải bị reject. Diagnostic hậu
nghiệm đổi đúng divisor bằng số lượng summands sang `len([1,...])`, kiểm giá trị
chương trình trước/sau không đổi, làm23 raw responses đọc được; cả23 khớp
official target. Đây là software readout của outputs thật,0 calls mới, không
phải23 câu mới hay chiến thắng của AI/reputation.

Nếu chỉ đọc lại **final artifacts của workflows đã thu**, giữ nguyên mọi quyết
định và generation context, KEEP/E/O/EO/Self1/Self2 đều đạt20/24 sau phép chuẩn
hóa count nói trên. Không đổi điểm chính15/15/16/15/15/15. Không giả vờ đã chạy
một policy acceptance mới: Self2 vẫn được sinh từ đúng incumbent cũ. Diagnostic
cho thấy không nên tiếp tục ép solver vào constant contract này.

**Negative interaction duy nhất đến từ acceptance logic.** Case
`2ba67b9a-9cf8-466f-81cc-b3cf0e3bec49` tính trung bình34,45,110 =63thousand.
KEEP bị reject divisor3. E sửa code sangsum/len nên raw answer đúng63 nhưng
vi phạm quyền “chỉ sửa source IDs”; O sửa code tương tự và được chấp nhận.
EO theo protocol đòi cả hai patches đúng permissions, nên reject cả bundle
và giữ KEEP invalid. Do đó I=-1 ở đây **không chứng minh hai sửa ngữ nghĩa
gây hại khi ghép**: đó là all-or-nothing scope rejection. Fallback chỉ giữ
component hợp lệ được replay riêng trênALL24, theo luật joint→O→E→KEEP chỉ dựa
permissions/executability:16/24,0 model calls mới. Đây là cải tiến receiver hậu
nghiệm, không đổi primary15/24; không có lý do fit một interaction learner để
học lại lỗi acceptance này.

**Source-token existence không giải quyết metric/precision/scale của nhãn.**
4/24 câu có flags cần audit, không relabel: margin nguồn in28% nhưng target
recompute28.41%; growth shares95.70534% nhưng annotation0.96scalepercent;
text operating-income change-79million nhưng target49-13=36 lấy từ charges;
fair-value table thiếu explicit multiplier thousands trong extract. File flags
ghi cả nguồn và lý do;0 independent human reviews. Không gọi mọi official
error là label noise, và không lấy một output match target làm chứng cứ đã
hiểu tài chính đúng.

## Vì sao vẫn chạy đối chứng bổ sung

Không thể dùng scoped Self2 bị count contract làm đại diện cho strongest
single-agent baseline. Đã khóa một đợt riêng120 calls mới trên **ALL24**:
Qwen Plain Self1/2 không hạn chế hằng số, và Gemma4 Plain/Self1/Self2 với cùng
nguồn, catalogue, Python executor, per-call cap và review prompt. Qwen Plain
24 outputs thật được reuse nhưng charge đủ cost khi so workflow.

Đây là post-hoc adequacy/cross-family probe, không phải độc lập confirmation.
Gemma được chọn bằng metadata của một tag cụ thể trước khi xem điểm TAT-QA;
không sweep model hoặc chọn câu theo failure. Full digest và source zip đã khóa
trước120 outputs. Cả120 đã thu xong,0 unresolved/length stops/native thinking.
12 source files, prompts, weights, actual GPU và re-execution đều audit PASS.

| Workflow không hạn chế hằng số | Đúng /24 | Executable /24 | Calls/câu | Mean eval giây/câu |
|---|---:|---:|---:|---:|
| Qwen direct | 19 | 22 | 1 | 8.03 |
| Qwen Self1 | 20 | 23 | 2 | 16.63 |
| Qwen Self2 | 20 | 23 | 3 | 23.15 |
| Gemma direct | 16 | 20 | 1 | 4.92 |
| Gemma Self1 | 16 | 20 | 2 | 6.96 |
| Gemma Self2 | 16 | 20 | 3 | 8.53 |

Union sáu workflows20, bằng best fixed20; Gemma unique0, Qwen unique4 theo
registered readout. Gate FAIL. Không fit history learner. NativeFalse/greedy0
đã được khóa cho cả hai; Gemma có recommended sampling khác, vì vậy không kết
luận giới hạn năng lực của cả family từ cấu hình này.

Qwen Plain Self2 hơn Scoped Self2 đúng5, hại0; delta20.83pp, bootstrap theo
context[8.33,37.50]pp, exact McNemar p0.0625. Đây là adequacy comparison hậu
nghiệm, không phải reputation effect hay kết quả xác nhận độc lập.

**Đối chứng readout metadata dùng chung:** bỏ duy nhất phép gán string literal
cho biến không bao giờ được đọc và không phảianswer. Không đổi numeric code,
model-declared scale, acceptance decisions hay generation contexts. Trên các
final artifacts thật, cả ba Qwen workflows20/24, cả ba Gemma18/24, executable
24/24 cho mọi workflow. Union vẫn20; Gemma unique0. Không đổi điểm chính, không
tính thành một lần rollout policy mới. Như vậy kết luận thiếu selection headroom
trong mẫu không chỉ do Gemma bị phạt format. Một phần Qwen Self1 gain so với
direct cũng là sửa code metadata, không phải cứu một phép toán sai.

Hai lỗi Gemma còn khác với Qwen sau readout này gồm chọn **net DTA** thay vì
gross DTA trong câu không yêu cầunet, và tự lấyabs của average debt discount
dù cả hai số nguồn đều âm. Đó là các quyết định metric/sign; không đổ tất cả
chênh lệch cho parser hoặc nhãn. Bốn case còn sai của Qwen trùng bốn source/
annotation flags, nhưng chưa có human adjudication để chấm một metric khác.

Lưu ý thêm ở fair-value case:1.165million và1165thousand bằng nhau về lượng,
nhưng evaluator gốc round tới2 decimals **trước** nhân scale, nên có thể chấm
khác nhau. Giữ hành vi evaluator gốc; không claim nó luôn invariant theo unit.

Tổng hai đợt572340 input tokens và59841 output tokens,264 responses mới. Bốn
app nghiên cứu đều có containers[] sau khi kết thúc; xem resource receipt. Không
dùng/sửa app Ollama gốc. Không có job tiếp tục chạy ngầm.

## Hệ quả cho phương pháp nghiên cứu

Không học reputation trên bank hiện tại. Trước hết phải giữ solver Python
đủ năng lực và checker phải báo đúng giới hạn của nó. Proof-of-token và
program validity nên là signals cho decision, không biến thành semantic truth.
Không tính gain do bỏ một ràng buộc gây suy giảm solver là research gain.

Phần nghiên cứu tiếp theo phải chứng minh historical utility/transfer
trên task mới, thắng strongest fixed/self-review và contextual action-value
learner cùng thông tin. Ghi chú đại số riêng cho thấy tách credit tuyến tính
với cùng features/penalty có thể tương đương chính xác action-value regression;
đổi tên estimator không đủ làm novelty.

24 TRAIN contexts, một sample/config, chưa report-disjoint, chưa human
adjudication; bootstrap theo context chỉ là exploratory và có thể không mô tả
phụ thuộc giữa các trích đoạn cùng report. Giữ nguyên150 FinQA confirmation
reports. Prototype không thay cho các bằng chứng phương pháp còn thiếu.
