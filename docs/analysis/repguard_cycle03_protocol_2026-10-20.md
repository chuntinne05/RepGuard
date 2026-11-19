# Vòng 3: can thiệp có phạm vi trên TAT-QA

Khóa trước inference lúc **00:59:04 UTC, 20/10/2026**, run
`746ca756961393ace1ad8c57`. Đây là pilot cơ chế trên TRAIN development,
**chưa phải phép thử một reputation learner hay xác nhận phương pháp vượt baseline**.

## Câu hỏi thực nghiệm

Hai vòng trước chưa tạo được những lời giải bổ sung đủ hữu ích để reputation
chọn lựa. Vòng này kiểm xem sửa riêng việc chọn số liệu, sửa riêng phép tính/
đơn vị, và ghép hai bản sửa có tạo được kết quả mà một agent mạnh tự kiểm tra
vẫn bỏ lỡ hay không. Nếu không, chưa có căn cứ thu history lớn và học router.

Giữ đề tài multi-agent/reputation. Domain tài chính là môi trường đánh giá;
chuyển dataset hay thêm bảng số liệu không tự tạo ra đóng góp nghiên cứu.

## Dữ liệu và task contract

Lấy **24 context đầu tiên** của inventory 64 arithmetic TRAIN contexts đã
chọn bằng hash ở vòng trước, trước khi có bất kỳ output TAT-QA nào. Một câu
mỗi context. Không mở 150 FinQA confirmation reports. Context UID không phải
report ID; chưa có bảo đảm report-disjointness hoặc không nằm trong pretraining.
Exact dedup với FinQA không loại hết paraphrase và bảng liên quan.

Nguồn và evaluator: [TAT-QA của Zhu và cộng sự, ACL 2021](https://github.com/NExTplusplus/TAT-QA),
revision `870accc41953dcde885aabeb963d94aabdc0fbc3`. Dataset CC BY 4.0,
code evaluator MIT; giữ nguồn và license trong thư mục dữ liệu.

Mỗi prompt chỉ nhận question, bảng đầy đủ đúng thứ tự, paragraphs và catalogue
numeric tokens được sinh từ nguồn. Không nhận answer, derivation, gold scale,
rel_paragraphs, answer_from hay req_comparison. Catalogue chỉ định vị token,
không xác nhận token thuộc đúng metric, năm, entity hoặc đơn vị.

Model phải dự đoán cả value và scale. Ví dụ 25% được xuất thành value 25,
scale percent. Tính điểm bằng **TaTQAEmAndF1 gốc**, prediction là danh sách
chuỗi không rỗng, kể cả `['0']`; invalid/abstain là EM0. Không dùng metric
FinQA hay tự điền scale từ nhãn. Bộ thực thi làm tròn final value 5 decimals
giống mọi nhánh; evaluator gốc có normalization riêng. Arithmetic F1 = EM
trong evaluator này, không phải hai tiêu chí độc lập.

## Những nhánh được chạy

Qwen3.5:27b GGUF Q4_K_M, digest
`64ae5b1d651fb2709d5928ccb8dcfb4bb2cc9c2c8001ac34497e36a6cf905b59`,
Ollama 0.40.6, L40S, think=False, temperature0, seed20102026,
context16384 và tối đa4096 output tokens/call.

| Nhánh | Cách tạo | Lượt model mỗi câu |
|---|---|---:|
| Plain PoT | Python số liệu trực tiếp, unrestricted literals | 1 |
| KEEP | Lời giải ban đầu, số liệu bind tới token nguồn | 1 |
| E | Từ KEEP, chỉ đổi source ID của các biến đã có | 2 |
| O | Từ KEEP, chỉ đổi code/status/scale; giữ bindings | 2 |
| EO | Ghép bindings của E với program của O rồi thực thi | 3 |
| Self1 | Từ KEEP, được đổi mọi trường, thêm/bớt bindings | 2 |
| Self2 | Tự kiểm thêm từ Self1 đã qua acceptance | 3 |

Có **6 lời gọi thật/câu**, tổng144. EO tái sử dụng hai patch độc lập, không
gọi LLM thêm. Lượt sinh KEEP được chia sẻ khi thu dữ liệu, nhưng mỗi workflow
triển khai vẫn phải trả cost KEEP của nó. Không cộng tổng cost của các nhánh
như thể đó là chi phí một policy triển khai.

Plain là capability control vì binding constraint có thể làm solver yếu đi.
Self1/2 nhận cùng catalogue, nguồn và interpreter, được sửa rộng hơn E/O.
Các vai trò dùng chung backbone; chưa chứng minh heterogeneity về năng lực.
Giới hạn số calls/token giống nhau không đồng nghĩa actual compute bằng nhau.
Sẽ báo actual tokens và Ollama eval duration; chưa phải hóa đơn Modal.

Bindings được executor khởi tạo từ token thật. Chương trình dùng biến Python
có nghĩa, không dùng DSL phép toán cũ. Numeric constants chỉ phục vụ unit
conversion/counts; không cho ghi đè biến đã bind. Đây vẫn là kiểm token và
syntax, **không phải semantic verifier**. Giới hạn nguồn/constant cũng có thể
ngăn một lời giải hữu ích, phải đo bằng Plain và Self controls.

## Acceptance và credit

Patch đúng permissions và chạy được được nhận; nếu không, giữ incumbent.
Không dùng gold để giữ/sửa/chọn output. EO ghép RAW patches có permissions
hợp lệ, kể cả khi một patch riêng lẻ chưa chạy được; chỉ kiểm executable
validity sau khi ghép. Cách này không vô tình loại một sửa chỉ có tác dụng
khi kết hợp. Không có clean/oracle patch đưa vào inference.

Trên lịch sử đánh giá, ghi đủ bốn outcomes KEEP/E/O/EO và interaction:

`I = EM(EO) - EM(E) - EM(O) + EM(KEEP)`.

Đây là diagnostic trên những can thiệp đã thực hiện, không phải credit mà
LLM-judge đoán ra. Một sample/patch/config không cho biết causal effect trung
bình của mọi agent hoặc mọi cách sửa. Không suy từ I dương ra policy đã thắng.

[C3](https://arxiv.org/html/2603.06859v1) đã dùng frozen context và replay để
gán marginal credit; [GCJR](https://arxiv.org/html/2608.29228v2) đã xét repair
sets cần thiết đồng thời. Không nhận công thức interaction, replay hay joint
repair là novelty của khóa luận. [Conditional Agent Trust](https://arxiv.org/abs/2606.14200)
đã nghiên cứu trust theo skill và điều kiện borrowing hữu ích; không nhận việc
đổi global reputation sang conditional reputation là mới.

## Gate đã khóa

Thu đủ24 câu, giữ cả câu ban đầu đúng để đo harm. Sau2 context chỉ dừng vì
kỹ thuật nếu không có KEEP nào executable; dừng nếu prompt vượt12288 tokens.
Không dừng sớm theo accuracy hay chỉnh prompt sau khi xem gold.

Chỉ cân nhắc học history nếu oracle union của KEEP/E/O/EO vượt strongest fixed
control trong Plain/KEEP/Self1/Self2 ít nhất2 câu, và scoped arms cứu ít nhất2
câu mà **tất cả** các controls này đều sai. Oracle dùng gold để đo khả năng
tối đa; không được báo như policy thực tế. Gate đạt cũng chưa chứng minh các
features hiện tại dự đoán được lúc nào nên sửa.

So EO với Self2 bằng paired bootstrap20.000 lần, seed20102026 và exact
McNemar; kết quả exploratory, 24 TRAIN contexts không đủ để tuyên bố tổng
quát hóa. Nếu gate thất bại, giữ toàn bộ kết quả và phân tích nguyên nhân;
không fit learner lên một bank không có selection headroom rồi nhận win.

Đóng góp tương lai, nếu có, phải nằm ở **học và transfer hiệu quả can thiệp
dưới feedback hạn chế**, vượt strongest fixed workflow và contextual action-value
learner cùng thông tin. Full outcome-vector correlations tự nó không cải thiện
expected utility của một quyết định chỉ cần marginal reward; phải chỉ ra cơ chế
transfer/sequential information cụ thể và ablate nó, không chỉ đổi tên estimator.

## Tính tái lập và tài nguyên

Protocol máy đọc,9 source hashes, frozen source zip và registration trước
output nằm tại `results/thesis_tatqa_scoped_repair_v1/`. Mỗi lượt ghi receipt
initiated trước API và completed sau response; chưa rõ kết quả thì dừng để audit,
không tự retry theo chất lượng. Wall cap3 giờ, tối đa1 GPU container của API mới.

Chỉ deploy thêm TatqaScopeOllama lên **app nghiên cứu riêng đã tạo ở vòng trước**
`repguard-thesis-modern-backbone-20261019`, giữ hai API native/direct cũ.
Không dùng hay sửa app Ollama cũ của người dùng. GPU chỉ mount volume weights,
không mount annotations/evaluation volume. Chưa có human semantic adjudication.
