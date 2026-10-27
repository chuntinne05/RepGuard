# Quyết định nghiên cứu sau264 lượt suy luận mới

**Chưa có phương pháp reputation đủ bằng chứng để chốt làm đóng góp chính.**
Vòng này hoàn thành264 responses mới, trên24 TAT-QA TRAIN contexts; cả hai
study audit PASS,0 mocks,0 unresolved và0 length stops. Không fit learner lên
những bank không có headroom. Không nhận gain do parser/model/contract là
gain reputation, không dùng kết quả pilot để bảo đảm điểm khóa luận.

## Kết quả làm thay đổi quyết định

| Phép thử | Kết quả trên24 câu | Kết luận giới hạn trong mẫu |
|---|---|---|
| Scoped repair144 calls | Plain19; KEEP15; E15; O16; EO15; Self1/2 15 | Oracle scoped16, gateFAIL |
| Plain/self-review và khác họ120 calls mới | Qwen19/20/20; Gemma16/16/16 | Union20 = best fixed20, Gemma unique0; gateFAIL |
| Readout count,0 calls mới | Structured terminal artifacts đều20 sau rewrite divisor tương đương | Thiệt hại chủ yếu từ constant contract; không phải method gain |
| Readout metadata dùng chung,0 calls mới | Qwen20/20/20; Gemma18/18/18; union20 | Không phải chỉ vì Gemma bị phạt format mà bank thiếu headroom |
| Receiver fallback,0 calls mới | EO15→16 khi không bỏ component hợp lệ cùng patch vi phạm | Sửa lỗi acceptance; không phải học được interaction hữu ích |

Các readout/replay là kiểm phần mềm hậu nghiệm trên **outputs thật đã lưu**,
giữ generation contexts và workflow decisions đã thu. Không thay điểm chính,
không coi là rollout của một policy mới, không tạo thêm câu/model responses.

Qwen3.5:27b và Gemma4:26b Q4_K_M đã chạy trên hai app/volumes nghiên cứu riêng,
digest pinned, L40S, thinkFalse. Cùng4096 output cap,16384 context vàgreedy0.
Không gọi đây là model-capacity ceiling; chưa tối ưu mọi sampling/configuration.
Gemma được chọn trước khi mở điểm TAT-QA, không model sweep theo outcomes.

**Nguyên nhân xác định:** (1) constant constraint chặn divisor trung bình dù
phép toán đúng; (2) scope acceptance đòi hai patches cùng hợp lệ nên bỏ cả
O đúng khi E sửa code quá quyền; (3) metadata string trong code bị parser
chặn; (4) một số lỗi còn lại là chọn gross/net hoặc dấu, còn4 câu có metric/
precision/scale annotation flags cần review độc lập. Các nguyên nhân này
khác nhau; không gom tất cả thành model yếu, label noise hay credit sai.

20/24 của Qwen sau readout và4 case còn lại có flags **gợi ý** task với oracle
context đã ít chỗ cải thiện trên mẫu này. Chưa chứng minh cả FinQA/TAT-QA dễ,
nhãn sai hàng loạt hoặc multi-agent nói chung vô ích. Context không phải report;
chưa có independent human adjudication hay independent confirmation.

## Không nên làm tiếp

Không đổ thêm ngân sách thu hàng trăm history rows cho scoped bank này;
không tune thêm reputation score để chọn giữa outputs có cùng ceiling;
không ép source-bound DSL làm solver yếu rồi lấy phục hồi năng lực làm đóng
góp; không lấy một oracle chọn bằng gold làm policy triển khai.

Thay contract/compiler tốt hơn là việc nên làm và phải cấp cùng cho mọi
baseline. Self1 đã bằng Self2 trong batch; thêm calls không tự tạo cải thiện.
Một Bayesian/interaction decomposition cũng có thể tương đương một learner
thông thường: xem ghi chú đại số riêng trước khi đặt tên phương pháp mới.

## Hướng tiếp theo: feedback thực thi chưa đầy đủ, audit cho quyết định

Giữ nguyên trục đề tài gốc **multi-agent reputation dưới imperfect feedback**.
Không chốt đổi tên đề tài, không biến khóa luận thành benchmark hay nhật ký
forensics. Phép thử ứng dụng kế tiếp cần feedback có ý nghĩa ngữ nghĩa thật,
thay cho việc một phép tính nhỏ bị vướng format.

Một setting đáng kiểm tra là **agent sinh code qua test cơ bản nhưng thất bại
ở test mở rộng**. [EvalPlus](https://github.com/evalplus/evalplus) có evaluator
và các bộ test bổ sung chính thức; [bài NeurIPS2023](https://arxiv.org/abs/2305.01210)
đã chỉ ra test chưa đủ có thể bỏ sót code sai và làm đổi ranking. Vì vậy,
“test pass chưa chắc đúng” hoặc thêm nhiều test **không phải novelty** của ta.
[AgentCoder](https://arxiv.org/abs/2312.13010) và
[CANDOR](https://arxiv.org/abs/2506.02943) cũng đã dùng các agent phối hợp
testing/generation. Không gọi việc tạo coding-agent pipeline là nghiên cứu mới.

**Câu hỏi candidate:** Khi chỉ một phần history được audit đủ, có nên dành
audit cho những bằng chứng có khả năng thay đổi lựa chọn teammate, và điều
đó có giúp reputation transfer tốt hơn calibration/audit/routing thông thường
với cùng dữ liệu và budget hay không?

Lý do xem câu hỏi này: ECRT cũ có những đợt cải thiện calibration nhưng không
đổi ranking/quyết định. Tối ưu Brier trên mọi history row chưa chắc giải quyết
được chỗ quyết định sai. Đây là motivation từ kết quả dự án, **không chứng
minh decision-focused audit/value-of-information là ý tưởng mới**. Cần rà
soát active model selection/active learning/label-efficient routing trước claim.

**Không quay vòng lại đề xuất cũ:** tài liệu DART ngày05/10 đã đề xuất paired/
active audits, relative-gain learning và đã chỉ ra SaveRouter rất gần hierarchical
acquisition. Các đợt DART cũng đã thử nhiều audit/neural/factor controls mà chưa
đạt kết quả đủ mạnh. Do đó VOI, paired audit hay regret loss trong danh sách dưới
không phải một hướng mới được phát hiện hôm nay. Phải đọc lại các variants cũ
trước implementation; không chạy lại chúng với một tên khác.

Khác biệt **cần kiểm trong pilot**, không mặc nhiên đúng: test suites lồng nhau
cho một cấu trúc feedback mà LLM-judge cũ không có. Gọi B là basic-tests pass,
và F là **basic AND extended-tests pass**. Khi đó B=0 xác nhận F=0; B=1 chưa
xác nhận F=1. Đây là known failures cộng outcomes bị censored ở nhóm pass, thay
vì feedback hai chiều tùy ý. Không học toàn bộ reputation bằng cách đếm B=1
như một positive label.

Đại lượng phù hợp sau khi candidate đã qua basic tests là
`P(F=1 | B=1, agent, task, observed verification state)`, khác global accuracy
`P(F=1 | agent)`. Một model có nhiều public-test failures vẫn có thể đáng tin
trong nhóm survivors, hoặc ngược lại. Đây là cơ chế có thể dẫn tới đổi ranking,
chứ không chỉ giảm Brier cho mọi tasks. **Chưa có dữ liệu chứng minh effect đó
trong pool hiện tại.** Nếu B đã gần quyết định F hoặc cùng một agent luôn tốt
nhất trong survivors thì lại không có lý do dùng method phức tạp.

Audit một B=0 đã biết chắcF=0 là lãng phí trong setting này. Vì vậy baseline
mạnh bắt buộc gồm **uniform/uncertainty audit chỉ trong B=1**, cùng basic-test
filter và conditional learner. Một phương pháp chỉ thắng uniform audit trên cả
known failures chưa có đóng góp đáng kể. Những lập luận này phụ thuộc nested
test definition và oracle đúng phạm vi; không nhận mọi test pass là semantic truth.

Ứng viên thuật toán cần kiểm, chưa có implementation/results:

1. Lưu riêng feedback test cơ bản, bằng chứng coverage/trace quan sát được và
   outcome từ audit. Không biến “public tests passed” thành verified success.
2. Từ history được audit, ước lượng xác suất full-suite success theo agent,
   trạng thái feedback và nhóm task; giữ uncertainty, tách calibration feedback
   khỏi relevance transfer. Features/labels phải cấp ngang cho các controls.
3. Chọn history nào cần audit bằng expected reduction of **decision regret**
   sau khi có label, thay vì chỉ uncertainty/Brier. Chỉ audit quá khứ được phép;
   không mở full-suite target của task đang quyết định để chọn agent.
4. Chọn agent/kết quả hoặc repair theo estimated utility và cost. Tính đủ
   generation/test/review calls, không coi archived/cached responses là miễn phí
   khi mô tả deployment.

VOI, Bayesian reputation, conditional trust và active audit đều có tiền lệ.
Candidate contribution chỉ được nhận nếu cơ chế reliability×transfer×audit
thật sự thêm giá trị trên task mới, vượt **contextual action-value learner với
cùng thông tin**, không chỉ vượt RawPass hoặc global reputation yếu.

## Chuẩn bị đã làm, tách khỏi kết quả model

Đã tải nguồn chính thức EvalPlus, revision
`26d6d00bb1fd0fa37f39c99d5290da67891d1c5e`, cùng MBPP+v0.2.0, source zip,
license code và hashes.378tasks; chọn32development tasks bằng task-ID hash,
chưa chọn theo model score.32tasks có96 base inputs và3397 plus inputs.

**ZERO code-model calls, ZERO program executions và chưa có score EvalPlus.**
Public packet có prompt/entry-point/input-domain contracts; canonical solutions
và test inputs ở private packet. Prompt gốc vốn có một số public examples;
phải giữ visibility nhất quán, không gọi các examples đó là hidden.

Đã đọc special-oracle code: trong32tasks có một oracle chấp nhận output-not-None,
nên full-suite pass vẫn là proxy theo benchmark, không là chứng minh toán học
mọi hành vi đúng. Không có task sử dụng nhánh are_equivalent luônTrue trong
selection. Phải dùng đúng special-oracle rules và kiểm canonical solutions
trong cloud sandbox trước model study; không chạy generated code trên máy người dùng.

Overlap với MBPP200 archive cũ **chưa map xong**. Không gọi32task này độc lập
với archive hoặc không có pretraining contamination. Headroom archived20models
78%→94.5% trước đây không tự chuyển sang pool Ollama hiện tại.

## Gate và thứ tự công việc kế tiếp

1. Kiểm evaluator/reference solutions trong sandbox cô lập, giữ đúng input
   contracts/deserialization/special oracles/timeouts. Đây là software preflight,
   không tính thành model pass@1.
2. Khóa một pilot nhỏ sinh code thật và chạy **cả** basic/full test suites,
   rồi đo false-positive feedback, complementarity sau simple public-test filters
   và baseline mạnh được cùng tools/calls. Chưa fit một method trước gate này.
3. Nếu có regime phù hợp, khóa history/audit/validation và confirmation mới.
   So global/skill reputation, raw feedback, feedback-only calibration, ECRT cũ,
   contextual action-value và audit uniform/uncertainty/disagreement với cùng
   số labels. Budget audit là **labels được tiết lộ**, không giả vờ rằng CPU
   chạy full tests đắt hơn model calls nếu thực tế không phải vậy.
4. Chỉ mở rộng khi method effect vượt những controls này; chọn cỡ confirmation
   theo effect/risk mục tiêu trước khi mở scores. Prototype đi sau bằng chứng,
   không dùng UI/demo để bù một contribution nghiên cứu chưa có.

Đây là lựa chọn **phép thử tiếp theo**, chưa là lời hứa method sẽ thắng hay
quyết định chuyển toàn bộ ứng dụng cuối cùng sang code. Nếu giáo viên cần giữ
domain tài chính, có thể giữ làm application track, nhưng không dùng các bank
oracle-context đang bão hòa/thiếu phân hóa làm bằng chứng cho reputation.

## Tài nguyên và hồ sơ

264responses mới:572340 input tokens,59841 output tokens. Không có billing
statement nên không báo tổng tiền hoặc cost savings xác nhận. Bốn app nghiên
cứu đã về containers[]; không có inference job chạy ngầm. App Ollama cũ của
người dùng không được gọi hoặc sửa.150 FinQA confirmation reports vẫn chưa dùng.

Hồ sơ: `repguard_research_cycle_03_2026-10-20.md`, hai protocol, hai auditJSON,
hai thư mục results đã frozen; count/metadata/receiver diagnostics được ghi
rõ hậu nghiệm. Gói source-only review ALL24 đã có,0 human reviews hoàn tất.
