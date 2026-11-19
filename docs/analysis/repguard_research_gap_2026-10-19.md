# Research gap và điều kiện chốt phương pháp

Cập nhật 19/10/2026. Đây là định vị nghiên cứu và giả thuyết cần kiểm, không phải
tuyên bố đã tìm được phương pháp mới hoặc đạt SOTA. Các bài 2026 dưới đây chủ
yếu là preprint; kết quả tác giả báo cáo chưa được dự án tái lập.

## Những hướng không nên nhận là đóng góp mới

| Công trình gốc | Phần đã có | Điều RepGuard phải vượt qua |
|---|---|---|
| [Conditional Agent Trust](https://arxiv.org/abs/2606.14200) | Uy tín theo kỹ năng; mượn bằng chứng khi dữ liệu thưa và pool có specialization; phân tích laundering | Không nhận skill-conditioned reputation hoặc shrinkage là mới |
| [MiniRep](https://arxiv.org/abs/2609.39297) | Kết hợp lịch sử, quality/risk hiện tại, hạn chế influence của nhóm câu trả lời tương tự | Không nhận history + disagreement + chống đồng thuận tương quan là ý tưởng đầu tiên |
| [MoCA-Agent](https://arxiv.org/abs/2606.11537) | Claims fact/formula/unit/sign, specialist market, executable synthesis và repair | Claim decomposition, financial verifier hoặc thêm specialist riêng lẻ không đủ novelty |
| [CLAIR-Fin](https://arxiv.org/abs/2608.13706) | Claim ledger, evidence authority theo claim type, hand-off verification, adaptive adversarial review | Không nhận kiểm tại claim hoặc tăng debate khi có tranh chấp là mới |
| [DARC](https://arxiv.org/abs/2608.11772) | Diagnosis trước recovery, lựa chọn can thiệp có tính chi phí | Phải so với recovery được thiết kế từ development failures |
| [STAR](https://arxiv.org/abs/2605.10057) | Routing theo trạng thái và recovery từ traces | Failure-aware routing không tự là research gap |
| [RLCascadeRouter](https://arxiv.org/abs/2608.15817) | Học continuation và STOP, xét state/cost/complementarity | Tối ưu gain thay vì accuracy prediction là tiền lệ, không đủ làm novelty |
| [MERIT](https://arxiv.org/abs/2608.05906) | Positive/negative memory từ repair outcomes của episode trước; retrieval theo failure type | Không nhận ký ức sửa lỗi theo loại lỗi là mới. Bài dùng oracle-assisted benchmark feedback; không đánh đồng với kiểm nguồn ở deployment |
| [C3](https://arxiv.org/abs/2603.06859) | Đóng băng transcript context, chạy alternative continuations, credit từng message cho policy optimization | Không nhận counterfactual marginal credit trong multi-agent là mới |
| [GCJR / Minimal Repair Family Recovery](https://arxiv.org/abs/2608.29228) | Tìm các nhóm event cần sửa cùng nhau qua graph-constrained replay với clean counterparts | Interaction giữa repairs và việc pointwise attribution bỏ sót joint repair đều đã có tiền lệ; cần phân biệt oracle localization với chọn repair ở task mới |
| [Repair or Resample?](https://arxiv.org/abs/2608.25920) | So reflection/critic với rerun và selective node replay trên failures thật | Phải loại lợi ích do thêm lượt sinh; phân biệt diagnostic oracle với deployable locator |

Rà soát có giới hạn, chưa chứng minh không tồn tại bài làm đúng tổ hợp đề xuất.
Không dùng việc đổi tên hay chuyển sang FinQA làm bằng chứng novelty.

## Vấn đề hẹp có giá trị nghiên cứu

Trong một nhóm agent đã có solver và tools đủ mạnh, lịch sử **sửa đúng ở phần
nào, trong trạng thái nào** có giúp quyết định phạm vi can thiệp vào một lời
giải hiện tại tốt hơn lịch sử đúng/sai toàn đáp án hay không, khi checker chỉ
thấy một phần lỗi ngữ nghĩa và phản hồi chuẩn phải được audit tốn chi phí?

Đối tượng học là hiệu quả của can thiệp sau acceptance rule, không phải độ
đáng tin của lời văn. State cần thể hiện metric, kỳ, scope, source/quantity,
operation, units và những gì checker thực sự kiểm được. Phải phân biệt
`đã kiểm` với `chưa phát hiện lỗi`; không biến executable thành nhãn đúng.

Giả thuyết phương pháp nên khảo sát là reputation theo **phần can thiệp và
trạng thái**, học cả rescue lẫn harm, kèm quyền giữ nguyên/giới hạn sửa. Credit
cuối vẫn phụ thuộc kết quả end-to-end. Nếu hai lỗi phải sửa cùng lúc thì một
repair đúng thành phần có thể không được final reward ghi nhận; việc gán credit
trong trường hợp đó là câu hỏi thực nghiệm, không được tự thưởng vì agent nói
đúng một fact. C3 đã nghiên cứu marginal credit; phần cần kiểm riêng ở đây là
hiệu quả chọn/scope repair khi chỉ có kiểm chứng một phần, history thưa và
không có oracle chỉ lỗi tại inference.

GCJR còn nghiên cứu trực tiếp những nhóm sửa cần thực hiện cùng nhau. Do đó,
"interaction-aware repair" cũng không tự là novelty. Một khác biệt có thể kiểm
là học chuyển kinh nghiệm về repair scope/bundle sang task mới không có clean
counterparts, thay vì dùng paired clean replay để tìm nguyên nhân của failure
đã có. Cần so với contextual action-value cùng training data để chứng minh
cách transfer/credit của reputation có ích, không chỉ đổi tên action routing.

Một learned selector được train trên các outcome cũ vẫn dùng thông tin lịch
sử, dù không có biến đặt tên "reputation". Do đó, ablation hợp lệ là bỏ explicit
agent/repair-profile features hoặc cấu trúc transfer, giữ nguyên dữ liệu và
ngân sách train; không gọi toàn bộ comparator đó là "không học từ lịch sử".
Nếu một action-value learner thông thường với cùng inputs/labels làm tương
đương thì chưa chứng minh được đóng góp riêng của mô hình reputation.

Đây là **candidate gap tại giao điểm** các điều kiện trên. Chỉ được nâng thành
đóng góp khóa luận sau khi chứng minh cơ chế và lợi ích so với comparator gần
nhất. Không đủ nếu chỉ hơn majority vote hoặc một baseline bị lỗi schema.

## Hai câu hỏi nghiên cứu có thể bác bỏ

**RQ1 — Giá trị can thiệp:** sửa có scope và đối chiếu fact thành phần có tạo
được output đúng mới, vượt một agent tự sửa với đủ compute, hay chỉ diễn đạt
lại/sửa format? Vòng composition 72 calls kiểm một phần cơ chế này; không học
reputation trước khi thấy pool có headroom.

**RQ2 — Giá trị lịch sử:** khi cố định solver/action bank/checker, lịch sử
theo phần sửa có giúp quyết định tốt hơn current-state-only learner và global
history ở cùng audit budget không? Cần report mới và không dùng nhãn câu hiện
tại để chọn action. Nếu không vượt learned action-value baseline thì chưa có
đóng góp từ representation/credit của reputation.

Một objective khả dĩ là expected rescue − expected harm − λ·incremental cost.
Objective này đã có quan hệ trực tiếp với contextual routing/bandit; không nhận
công thức là thuật toán mới. Phần phương pháp phải là cách biểu diễn can thiệp,
ước lượng/transfer credit và xử lý bất định có ích, với ablation tương ứng.

## Thiết kế tối thiểu để được phép kết luận

- Tách report/context trước outcome; development dùng chọn phương pháp, final
  holdout chỉ mở sau khóa model/prompt/normalizer/policy. Tránh chọn corpus hay
  model theo vài câu sai đã xem. FinQA training pilots không là điểm test chính.
- Controls: strong PoT; self-repair đủ compute; best fixed action chọn từ train;
  current-state rule; current-state-only learned selector; global/conditional
  history cùng labels; history shuffle; adapted claim-verification control gần
  nhất. Ghi rõ adapted control khác full paper reproduction.
- Báo accuracy tất cả câu, rescue/harm, actual tokens/compute, coverage/abstain
  riêng. Chi phí collection counterfactual và chi phí phục vụ policy là hai số
  khác nhau. Không dùng oracle union như accuracy của method.
- Với audit thưa, lưu cách chọn audit/propensity và tính cả annotation cost;
  dùng cùng feedback cho controls. Không gán source-check pass làm gold.
- Có corpus/backbone kiểm tra thứ hai nếu tín hiệu đủ mạnh. TAT-QA là ứng viên
  vì có scale annotation trong gold, nhưng scale/derivation/gold mapping phải ở
  evaluator, không được gửi vào solver. Thang điểm thích nghi phải ghi riêng,
  không nhận là official TAT-QA EM nếu không chạy evaluator gốc.
- Các câu có ambiguity đơn vị/thời kỳ cần hai thành viên audit độc lập trước
  xem method identity/correctness. Giữ official score và semantic audit riêng.
- Pilot nhỏ chỉ sàng thiết kế. Power lấy từ paired discordances và effect có
  ý nghĩa đã đặt trước; không lấy `p>0.05` hay zero observed harm làm chứng minh
  non-inferiority/an toàn.

## Giá trị thực tiễn có thể bảo vệ

Ứng dụng hẹp là trợ lý tính/kiểm số liệu từ báo cáo: thấy phép tính nào được
giữ, assumption nào được xem lại, source nào thay, và tốn bao nhiêu compute.
Giá trị cần đo là cải thiện độ đúng hoặc giảm chi phí ở chất lượng đã kiểm định
so với một LLM có cùng tài liệu và calculator. Đây mới là câu trả lời bằng thực
nghiệm cho “ChatGPT/Claude cũng làm được”; có nhiều agent hoặc UI đẹp không đủ.

Không cần thắng mọi model hoặc mọi câu mới có khóa luận tốt. Cần một phạm vi
bài toán rõ, một cơ chế có lý do, thực nghiệm công bằng đủ sức kết luận và
giới hạn được công bố. Hiện dự án vẫn đang kiểm điều kiện cho cơ chế đó.
