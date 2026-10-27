# Vòng nghiên cứu 1: kết quả thật, nguyên nhân và quyết định

Ngày 18/10/2026. **Đã hoàn tất 160 phản hồi thật; chưa có phương pháp reputation vượt baseline được xác nhận.**
Quyết định: loại cấu hình repair v1 khỏi ứng viên chính. Controller lịch sử đã được fit và đánh giá OOF, nhưng đạt cùng 17/24 với PoT đã chuẩn hóa format và đọc biến kết quả cuối, trong khi compute proxy cao hơn khoảng 13,6% trên mẫu này. Tiếp tục nghiên cứu trên các can thiệp thực sự tạo output bổ sung và trạng thái có tín hiệu chọn can thiệp. Đóng góp cuối của đồ án vẫn phải là phương pháp và thực nghiệm; diagnostics là cơ sở thiết kế.

## 1. Những gì đã chạy

- `Qwen3:14b` với digest đã pin, Ollama 0.40.6, GPU NVIDIA L4; chỉ app riêng `repguard-thesis-real-pilot-20261018`.
- 16 calls: tám HISTORY đã xem, so full evidence với gold evidence spans. Oracle chỉ là chẩn đoán, không phải phương pháp triển khai.
- 96 calls: 24 câu/24 report mới, initial và ba repair thật; loại toàn bộ 100 report pilot trước khi chọn mẫu bằng hash metadata.
- 24 calls: tám HISTORY × native DSL/numeric catalogue/numeric raw matrix. Đây là development lặp lại, không phải 24 câu test độc lập.
- 24 calls bổ sung: control kiểu PoT/PAL trên toàn bộ 24 development, chương trình Python arithmetic dùng variable names và AST interpreter. Không chọn riêng câu baseline sai; protocol đóng băng trước output PoT đầu tiên.
- Các arm triển khai chỉ nhận tài liệu công khai và output ban đầu; không nhận target/program/gold source. Lưu raw response, native thinking, model digest, prompt hash, source snapshots. Không quality retry, không model mock.

## 2. Kết quả chính trên 24 report mới

| Cấu hình | Đúng/24 | Rescue | Harm | Mean serving tokens | Calls/câu |
|---|---:|---:|---:|---:|---:|
| Initial DSL nhiều bước | 6 | 0 | 0 | 4407.2 | 1 |
| Cùng agent tự sửa | 6 | 0 | 0 | 9020.5 | 2 |
| Chỉ sửa bằng chứng | 6 | 0 | 0 | 9078.1 | 2 |
| Chỉ sửa kế hoạch tính | 6 | 0 | 0 | 9063.7 | 2 |

Invalid/constraint-violating repair bị từ chối và giữ initial; correctness không tham gia acceptance. `accepted_edits` trong JSON gốc đếm output repair qua mechanical checks, bao gồm chương trình giữ nguyên; không đồng nghĩa với số chỉnh sửa thực sự.
**Oracle union=6/24, best fixed=6/24, zero rescues.** Với chính tập output đã thu, đổi learner để chọn output không thể tăng accuracy trên mẫu này. Gate thất bại nên không fit learner reputation/OOF mới. Không suy ra reputation vô ích cho mọi pool hoặc mọi tác vụ.
Tám HISTORY full evidence đúng 3/8; gold evidence spans cũng 3/8 ở chế độ không thinking. Việc giới hạn đoạn bằng chứng một mình chưa tạo cải thiện trong điều kiện này. Đây không phải chứng minh retrieval không quan trọng, hay kiểm tra interaction giữa oracle evidence và native thinking.

## 3. Nguyên nhân đã có bằng chứng

| Phát hiện | Bằng chứng cụ thể | Mức kết luận |
|---|---|---|
| Sai thang đo ở chương trình |10 initial có trailing scale trong output percent; một phép sửa source-only hậu nghiệm cứu 6/18 câu sai | Lỗi chương trình cụ thể đã tái tính được; không phải score phương pháp xác nhận |
| Nhầm step với constant | HWM reasoning chọn 6 và 5; lookup đúng nguồn nhưng cuối dùng`K0-K1`, ra-1 thay vì dùng kết quả lookup | Trace chứng minh ánh xạ reasoning→program sai; verifier v1 còn cho phép kết quả bỏ qua evidence |
| Scale không đi theo quantity | DISH reasoning nói 359 million lớn hơn 55,999 nhưng program so 359 với 55,999, ra no | Cần giữ scale/unit trong representation; arithmetic executor không tự hiểu đơn vị văn bản |
| Parser bỏ percent ngoài ngoặc |`(3.5)%` bị đọc thành-3.5 thay vì-0.035;8 tokens/2 case trong 32 case | Lỗi frontend xác định được; đã viết v2 và kiểm trên 8 token thật |
| Row context chưa giữ rõ nhóm năm | FRT có nhiều block balance→additions; catalogue cell chỉ có row label và hàng đầu làm header | Hạn chế serialization xác định được; mức ảnh hưởng accuracy cần đối chứng riêng, không quy mọi source error cho nó |
| Target có bất nhất semantic | MO 853.5/(1+.049)≈813.63 theo source và answer, nhưng exe_ans 8.53082 | Trường hợp cụ thể cần adjudication; giữ nguyên score FinQA chính |
| Lỗi đồng thời che đóng góp thành phần | WRK self/evidence repair chọn lại đúng 229.4 và 177.2 nhưng giữ× 100, vẫn sai final target | Cần kiểm tra composition/credit theo phần; chưa chứng minh learner claim-level sẽ thắng |

Không có một nguyên nhân duy nhất cho toàn bộ dự án. Các kết luận trên áp dụng cho scaffold/pool mới; không thay thế chẩn đoán riêng của ECRT, DART và archive 20 model. Source có tồn tại và phép toán chạy được chưa chứng minh đúng year, metric, unit, hoặc đúng semantic.

AAPL/2006/page_93.pdf-1 hỏi “by how much ... increase”, không nói rõ đơn vị tuyệt đối hay tương đối: 52−46=6 triệu là chênh lệch, còn target 0.13043 là tỷ lệ tăng. AAP/2006/page_85.pdf-3 không ghi rõ thời kỳ tổng hợp; answer text ghi 20,630 nhưng chương trình tổng ba năm cho 20,664. Đây là các điểm cần hai người adjudicate độc lập; không tự relabel để nâng điểm.

## 4. Đối chứng native thinking và serialization

| Native arm, cùng 8 HISTORY | Valid output | Đúng target | Source verified? |
|---|---:|---:|---|
| dsl_native | 7/8 | 3/8 | Mechanical reference/execution only |
| numeric_native | 6/8 | 1/8 | No |
| numeric_raw_native | 7/8 | 1/8 | No |

Numeric parse được không bảo đảm nguồn đúng. Native DSL và nonthinking DSL khác cả thinking lẫn cap 4096/1536; không nhận là causal effect của riêng thinking ở cùng compute. Hai numeric native arm giữ cùng system/schema, khác serialization. Không dùng 8 HISTORY đã xem nhiều lần để kết luận generalization, chọn SOTA hoặc chốt luận văn.

### Control executable Python quen thuộc

PoT arithmetic control đúng 14/24, executable 21/24; rescue 9, harm 1 so initial DSL. Input 33,582/output 25,699 tokens, một call/câu. Đây là control lấy cảm hứng từ[PoT](https://arxiv.org/abs/2211.12588)/[PAL](https://arxiv.org/abs/2211.10435), không nhận là tái lập đầy đủ published protocol.
Control này có native thinking/cap 4096 và không ép source binding; khác cả budget/interface so với DSL 1536 nonthinking. Nó giúp tránh nhận lợi ích sửa giao diện/rounding thành đóng góp reputation; không phải so sánh nhân quả chỉ thay một biến, hay bằng chứng source fidelity. Giữ nguyên target FinQA, không oracle percent matching.

## 5. Baseline rẻ hơn đã chỉ ra vấn đề gì?

Diagnostic hậu nghiệm bỏ trailing× 100/× 1000/× 1000000 khi output percent và arg còn lại là step ngay trước đó. Quy tắc không nhìn gold để quyết định sửa, nhưng được thiết kế sau khi thấy initial development. Không đổi nhãn hay kết quả primary; có thể làm hỏng chuyển đơn vị hợp lệ ở case khác.

| Cùng một unit pass cho tất cả | Đúng/24 | Rescue so initial đã qua unit pass | Harm |
|---|---:|---:|---:|
| Initial DSL nhiều bước | 12 | 0 | 0 |
| Cùng agent tự sửa | 13 | 1 | 0 |
| Chỉ sửa bằng chứng | 13 | 1 | 0 |
| Chỉ sửa kế hoạch tính | 12 | 0 | 0 |

Union sau cùng unit pass=13, best fixed=13. Chỉ một trường hợp sửa source mang thêm final gain sau khi gỡ lỗi unit; chưa có complementary headroom để biện minh contextual reputation. Một workflow nhiều agent phải vượt baseline compiler/unit và cùng agent tự sửa đủ mạnh; không được nhận lợi ích sửa scaffold thành đóng góp reputation.

## 6. Bộ ước lượng gain từ lịch sử đã được thử thế nào?

Đã fit ba fold tách report, với paired outcomes thật của initial và PoT. Câu hiện tại không nằm trong fold train. Global prior 4, local prior 6, threshold 0.05 và key `(question skill, source family, one/multi step)` được cố định trước khi xem output PoT, sau khi đã xem initial development. Đây là pre-analysis plan trong lúc collection chạy, không phải preregistration trước mọi inference. Full supervised labels được dùng chung cho history controls; không gọi đây là 10% audit.
Các nhánh đều có cùng unit pass cho initial; PoT invalid thì giữ initial. Guard cho lỗi execution/evidence-dependency được cấp công bằng cho rule và history. Controller được replay trên các response model thật, không có model mock; chưa kiểm live policy trên report mới.
Một secondary control bỏ leading whitespace thừa khỏi từng dòng của straight-line Python, không đổi số hay phép toán. PoT strict 14/24 thành 16/24, hai rescue/zero harm. Toàn bộ raw code và điểm strict vẫn giữ nguyên. Cùng formatter được áp vào mọi nhánh; quyết định OOF không được refit sau khi xem kết quả formatter.

Một control readout riêng xử lý code HWM kết thúc bằng biểu thức biến`difference`: chương trình đã tính 6−5=1, nhưng thiếu assignment`answer`. Chỉ khi không có assignment answer và dòng cuối là một tên biến, wrapper gán chính biến đó làm output; không đổi arithmetic và không nhìn gold. Cùng readout được áp vào tất cả các nhánh, đưa PoT từ 16 lên 17/24. Đây là sửa quy ước output, không phải đóng góp reputation. Strict 14, whitespace 16 vàreadout 17 đều được lưu riêng.

| Cấu hình, cùng control format/readout | Đúng/24 | Mean calls/câu | Mean Ollama eval giây |
|---|---:|---:|---:|
| Initial + unit pass | 12 | 1.000 | 11.24 |
| Một agent PoT + format | 17 | 1.000 | 47.07 |
| Luôn tái sinh + fallback | 17 | 2.000 | 58.30 |
| Chỉ route bằng rule | 14 | 1.125 | 18.30 |
| Global history OOF | 17 | 2.000 | 58.30 |
| Local history OOF | 17 | 1.917 | 53.46 |

Đây là replay serving cost: tổng prompt_eval_duration + eval_duration của các call thực sự cần dùng theo policy. Nó loại model load khỏi compute proxy; không phải billing, latency deployment hay phép thử cost-matched đã xác nhận. Collection vẫn dùng 160 calls cho counterfactuals; fit/replay/formatter không phát sinh model calls mới.
Local history chỉ giảm từ 48 xuống 46 calls so với luôn tái sinh, trong khi direct PoT chỉ cần 24 calls. Sau format/readout, local history có 1 rescue và 1 harm so với direct PoT: cùng 17/24, compute proxy tăng 13,6%. Global history trùng hành vi luôn tái sinh. Lợi ích apparent 16 so 14 của primary comparison biến mất khi baseline xử lý format đầy đủ; không được nhận các lỗi quy ước output là đóng góp reputation.
Các target dùng để fit quyết định tùy chọn giữ nguyên sau format/readout. HWM thuộc nhánh guard bắt buộc, vốn bị loại khỏi tập train tùy chọn; các gain profiles/decision OOF vì vậy giữ nguyên. Kết quả không chứng minh lịch sử vô ích nói chung, nhưng không ủng hộ chốt controller hiện tại.
Với 0 harm/24, cận trên một phía 95% của xác suất harm còn 11,73%; với 1 harm/24 còn 18,29%. Do đó không tuyên bố non-inferiority 2 pp hay an toàn chỉ vì accuracy bằng nhau hoặc bootstrap không phát hiện khác biệt. Riêng trường hợp 0 harm, ít nhất 149 mẫu độc lập mới đưa cận harm này xuống 2%; power cho tổng accuracy còn phụ thuộc cả rescue lẫn harm.

## 7. Hướng phương pháp được giữ để nghiên cứu tiếp

**Câu hỏi:** lịch sử kiểm chứng có giúp chọn agent và phạm vi can thiệp thích hợp cho một output chưa biết đúng/sai, giảm harmful correction và chi phí so với strong single-agent và fixed repair không?
Phiên bản kế tiếp cần thực hiện theo thứ tự:

1. Chuẩn hóa giao diện quantity/source/step, giữ bảng có thứ tự và scale; xác nhận solver không bị giảm năng lực bởi protocol. So native numeric với một baseline PoT/tool tiêu chuẩn cùng backbone. Parser/dependency v2 đã có; chưa áp ngược vào v1 hoặc gọi v2 là pipeline đã chứng minh mạnh.
2. Expert nhận feedback có thể kiểm từ nguồn/trace, không chỉ lời nhắc review. Khi có nhiều lỗi, kiểm tra chuỗi sửa và interaction; không giả định một repair là đủ. Phải cấp cùng feedback/tools/cơ hội sửa cho single-agent.
3. Chỉ sau khi có rescue/harm và bổ sung thật giữa các action, học reputation theo hiệu quả can thiệp. Claim-level credit là giả thuyết cần test; reward cuối end-to-end vẫn là tiêu chuẩn chính, có charge annotation khi dùng nhãn claim.
4. So với self-repair cùng ngân sách, best fixed repair, rule từ current warnings, global history, contextual action-value/bandit cùng audit labels; ablate permissions, claim credit và history. Thắng baseline yếu hơn không đủ.
5. Giữ FinQA official score riêng với semantic audit; cần hai người adjudicate độc lập các case nghi vấn. Có thể thêm TAT-QA làm corpus kiểm chứng với scale được annotation rõ, nhưng chưa chạy corpus đó trong vòng này.

Không nhận diagnosis→repair là mới: [DARC](https://arxiv.org/abs/2608.11772) là related work trực tiếp. Phân rã claim/unit cũng đã có ở [MoCA-Agent](https://arxiv.org/abs/2606.11537). Học STOP/gain theo performance–cost có tiền lệ ở [RLCascadeRouter](https://arxiv.org/abs/2608.15817). Cần xác nhận khác biệt và lợi ích của trạng thái claim đã kiểm chứng, permissions và credit bằng ablation; hiện chưa có novelty claim được chứng minh.

## 8. Mốc quyết định trong 5–6 tuần

- Hai ngày đầu: chốt solver/evaluation đủ tin cậy và một pool can thiệp có headroom. Nếu không có headroom, đổi cách tạo/sửa output hoặc pool; không tiếp tục tune learner trên cùng output.
- Phần còn lại tuần 1: chọn một giả thuyết phương pháp từ development, đóng băng objective/controls/budget/splits.
- Tuần 2–3: thu paired outcomes, học policy từ audited history, đánh giá trên report chưa dùng để sửa phương pháp. Cỡ final sample tính từ paired discordances và effect/margin đặt trước; không mặc định 20 hay 24 câu là đủ.
- Tuần 4: ablation, chi phí, audit budget, backbone/corpus thứ hai nếu tài nguyên cho phép; giữ cả kết quả âm.
- Tuần 5–6: viết đóng góp phương pháp và giới hạn, hoàn thiện prototype từ pipeline đã kiểm chứng. Prototype là phần tích hợp nhỏ.

Các mốc này là kế hoạch nghiên cứu, không phải automation đã lên lịch, hay bảo đảm trước điểm số/superiority.

## 9. Tái lập và tài nguyên

Đợt này: 160 responses đã tái tính; input 600,180 tokens, output 82,290 tokens. Đây là bộ đếm runtime, không phải tổng billing Modal.
Đã giữ source snapshots và raw outputs tại`results/thesis_causal_repair_v1/`,`results/thesis_competence_probe_v1/`và`results/thesis_pot_control_v1/`. Bảy source chính của pilot trước còn nguyên hash. Các lượt chạy/abort trước đợt này không nằm trong 160 calls nêu trên.
Kiểm độc lập:`docs/analysis/verify_research_cycle_01.py`(local, không inference). Manifest hashes:`results/thesis_research_cycle_01_manifest_private.json`. Protocols/results JSON cùng ngày nằm trong`docs/analysis/`. Các native/causal code cùng snapshot nằm trong`thesis_pilot/`.
