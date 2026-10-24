# RepGuard: ưu tiên phương pháp để tạo lợi ích thật

Ngày18/10/2026. Đây là đánh giá và đề xuất nghiên cứu sau đọc lại các quyết định,
mã và kết quả, cùng rà soát tài liệu liên quan. Chưa triển khai/chạy ứng viên
mới trong tài liệu này; không phải kết quả superiority hoặc xác nhận novelty.

## Phán đoán và thay đổi ưu tiên

Nên dành5–7ngày tới cho một giả thuyết phương pháp có cơ chế tạo lợi ích rõ,
thay vì tiếp tục mở rộng UI hoặc chạy nhiều prompt. Cần baseline hoạt động đúng
để đo, nhưng đó là điều kiện đầu vào; không tự thành đóng góp reputation.

Không có bằng chứng đáng tin rằng tiếp tục tinh chỉnh learner hiện tại sẽ thắng
baseline mạnh. Không thể gán xác suất thắng bằng một con số từ các pilot này.

Trong batch mới, trên20screen: A đúng0, B đúng1, RepGuard đúng1 và dùng40calls
so với20củaB. Hợp hai output hiện có cũng chỉ đúng1câu. Vì vậy, **chỉ đổi cách
chọn giữa chính hai output này không thể vượt accuracy củaB trên đúng mẫu đó**.
Không suy ra giới hạn này cho task/pool khác hoặc cho quy trình tạo output mới.

Typed-tools và native-thinking probes trên8history đều đúng và qua check2/8.
Đây là development lặp lại, không chứng minh xác suất generalization. Một demo
tính đúng69.064% xác nhận luồng tích hợp, không xác nhận method superiority.

Các kết quả cũ cũng không nên bỏ qua: ECRT thường giữ nguyên ranking;
DART/global selection, neural/factor/history/audit đã thử nhiều cơ chế mà chưa
qua đầy đủ controls. Archive FinQA20model từng có best-fixed74%, oracle88.5%
trên200development, nhưng đó là **pool khác**; không phải bằng chứng headroom
cho hai solver mới hoặc cho repair actions chưa chạy.

## Tài liệu liên quan làm thay đổi đề xuất như thế nào

Rà soát này dùng bài báo/tài liệu gốc. Phần lớn các bài2026 bên dưới là preprint;
kết quả tác giả báo cáo chưa được dự án tái lập. Không chuyển các score công bố
sang cấu hình/model/dataset của dự án.

| Nguồn | Điều đã có trong nghiên cứu liên quan | Hệ quả cho RepGuard |
|---|---|---|
| [A Unified Approach to Routing and Cascading](https://arxiv.org/abs/2410.10347) | Kết hợp chọn model và dừng cascade | Dynamic routing tự nó không mới |
| [RLCascadeRouter](https://arxiv.org/abs/2608.15817) | Học STOP/model action theo mục tiêu performance–cost, xử lý mismatch giữa dự báo và quyết định | Đổi từ dự báo accuracy sang tối ưu quyết định chưa đủ novelty |
| [CRITIC](https://arxiv.org/abs/2305.11738) | Dùng công cụ để critique và sửa output | Thêm verifier/repair agent chưa đủ đóng góp riêng |
| [STAR](https://arxiv.org/abs/2605.10057) | Routing theo trạng thái lỗi, học recovery từ cả trace thất bại | Phải so với recovery policy học từ failure, không chỉ fixed cascade |
| [MoCA-Agent](https://arxiv.org/abs/2606.11537) | Phân rã financial reasoning thành claim về fact/formula/unit/sign; specialists kiểm tra và repair | Chuyển sang claim/evidence-level không thể tự nhận là ý tưởng đầu tiên |
| [ECL](https://arxiv.org/abs/2601.21742) | Dùng hồ sơ tương tác lịch sử để đánh giá độ tin cậy của peers | History-aware trust đã có tiền lệ trực tiếp |
| [MiniRep](https://arxiv.org/abs/2609.39297) | Kết hợp tín hiệu hiện tại, reputation và xử lý response tương tự trong debate | Thêm history và tránh đồng thuận tương quan chưa đủ novelty |
| [OneFlow / strong single-agent baseline](https://arxiv.org/abs/2601.12307) | Single-agent có thể mô phỏng nhiều workflow đồng nhất trong các phép thử của bài | Phải cấp cho baseline cùng tools và cơ hội tự sửa |

Một chi tiết có ích khi đọc phương pháp MoCA: weights theo role được đặt cố
định ở phần3.4; limitations báo6–10LLMcalls cho pipeline đầy đủ. Đây là động cơ
thử lịch sử kiểm chứng và phân bổ expert calls chọn lọc, **không chứng minh**
RepGuard sẽ cải thiện hoặc chưa từng có ai nghiên cứu cách đó.

## Ứng viên nên nghiên cứu: reputation theo hiệu quả sửa lỗi

Câu hỏi trung tâm:

> Sau khi đã có một đáp án kèm bằng chứng, lịch sử có giúp chọn đúng chuyên gia
> và đúng phần cần sửa để cải thiện kết quả sau chi phí, tốt hơn một agent mạnh
> tự kiểm tra/sửa và một repair policy không dùng reputation không?

Uy tín không chỉ là tỷ lệ trả lời đúng của agent. Đại lượng cần học là:

`lợi ích(action | trạng thái, history)`
`= P(sai→đúng sau action) − P(đúng→sai sau action) − λ × chi phí tăng thêm`.

Các xác suất này chưa biết ở inference. Chúng được học từ paired outcomes trên
lịch sử đã audit. Không dùng gold của câu đang xử lý để biết nó sai, để gọi
đúng expert, hoặc để chọn đáp án cuối.

### Trạng thái và hành động cụ thể

Giữ proposer, catalogue nguồn và executor hiện có; tạo một bản ghi trung gian
rõ metric, kỳ/năm, đơn vị, source references, thứ tự toán hạng và phép toán.
Các trường này vẫn có thể do model chọn sai. Checker chỉ tạo tín hiệu quan sát
được, không được gọi là bộ biết đúng ngữ nghĩa.

Ban đầu chỉ có3repair actions và1quyết định giữ nguyên:

1. **Tìm lại bằng chứng:** đọc lại hàng/cột/đoạn văn theo metric và kỳ, đề xuất
   source references thay thế. Agent được đánh giá bằng ảnh hưởng tới đáp án
   cuối, không chỉ số passage tìm được.
2. **Sửa kế hoạch tính/đơn vị:** kiểm tra numerator/denominator, dấu, thứ tự,
   operation và ý nghĩa đơn vị; trả bản sửa có nguồn. Executor vẫn thực hiện
   arithmetic, không nhường việc tính chính xác cho model.
3. **Tự sửa bằng chính proposer:** một lần đọc lại với cùng tools, làm control
   cho lợi ích của thêm compute và làm một action hợp lệ.
4. **Giữ kết quả hoặc yêu cầu người kiểm tra** theo rule đã khóa. Chuyển người
   kiểm tra không được tính thành câu giải đúng tự động.

Mỗi câu tối đa một repair call trong phiên bản đầu. Các agent cùng nhận nguồn
được phép; tool/data privileges tương đương cũng phải cấp cho single-agent.
Không cố tạo agent yếu hoặc cắt dữ liệu baseline để tạo complementarity giả.

Nếu chỉ cần deterministic correction thì áp dụng trực tiếp và cấp rule đó cho
mọi phương pháp. Không tính lợi ích của sửa lỗi parser/percent thành lợi ích
của reputation. Reputation chỉ cần quyết định nơi semantic uncertainty còn lại.

### Lịch sử và credit assignment

Mỗi record gồm question/report group, incumbent output, trạng thái quan sát
được trước action, action/expert/configuration, candidate sau sửa, quyết định
accept/reject thực tế, final correctness và chi phí. Gold chỉ ở evaluator/audit.

Điểm thưởng phải phản ánh **final output sau rule acceptance**, không phải chỉ
vì repair từng sinh một candidate đúng nhưng hệ thống không chọn được nó.
Phải đếm cả trường hợp sửa hỏng một đáp án ban đầu đúng. Không dùng pass@K
oracle làm accuracy của thuật toán.

Có thể bắt đầu bằng count model với shrinkage theo nhóm lỗi/task hoặc một
regularized action-value learner nhỏ; không cần fine-tune LLM hoặc deep RL
ngay. Đây là lựa chọn triển khai, không phải novelty tự thân. Confidence/
uncertainty heuristic không được quảng bá thành bảo đảm an toàn thống kê.

Trong training, reputation features phải out-of-fold theo report; inference
chỉ dùng prior history. Nếu production chỉ audit action đã chọn thì phải lưu
propensity/exploration hoặc thiết kế audit phù hợp. Giai đoạn đầu dùng full
paired audited outcomes và cấp công bằng cho supervised controls; chưa claim
label-efficient10%audit.

## Tại sao ứng viên này có cơ chế để thắng, và vì sao vẫn có thể thua

Nó có thể tạo output mới bằng việc sửa nguyên nhân cụ thể, nên không bị giới
hạn bởi oracle của hai output cũ. Nó có thể tránh expert calls khi repair
thường gây hại hoặc không đáng chi phí. Reputation được dùng tại action
boundary và đúng loại vấn đề, thay vì một phép calibration giữ nguyên ranking.

Nhưng cả ba điều kiện dưới đây đều cần đo:

1. **Có khả năng sửa bổ sung thực:** repair bank giải được đủ câu mà baseline
   mạnh và self-repair cùng ngân sách chưa giải được.
2. **Có tín hiệu trước quyết định:** trạng thái và history phân biệt được action
   hữu ích trên report mới. Nếu chỉ dùng gold hậu nghiệm mới biết nên gọi ai,
   hệ thống thực tế không dùng được headroom đó.
3. **Gain vượt harm và tổng cost:** thêm expert, judge, retrieval và tiền audit
   đều phải tính. Chuyên gia tự tin hoặc qua source check vẫn có thể sửa sai.

Không có bằng chứng rằng ba điều kiện này đã thỏa mãn. Đây là ứng viên đáng
thử theo cơ chế và kết quả lỗi đã quan sát, không phải phương pháp đã thắng.

## Phép thử đầu cần làm để quyết định nghiên cứu tiếp

Đây là thiết kế đề xuất, **chưa là protocol đã khóa và chưa gửi inference**.

- Chọn khoảng40question/report mới theo metadata, không chọn dựa trên việc
  baseline sai. Có câu initial đúng để đo harm. Nhóm kiểm chứng nhãn/đơn vị;
  ambiguity được xử lý theo rule trước xem outcome, không sửa nhãn để nâng điểm.
- Dùng một baseline single-agent có schema/tools đúng và mức năng lực có ích;
  baseline5%hiện tại chưa phải thước đo đủ mạnh. Giới hạn việc sửa baseline
  trong1–2ngày, không biến nó thành một tháng prompt tuning.
- Thu initial output và các repair/self-repair outputs thật theo cùng inputs.
  Ghi cost counterfactual collection riêng với cost phục vụ của từng policy.
  Cỡ pilot nên được giới hạn trước bằng sốcalls/token/wall-time;40câu không
  đồng nghĩa chỉ40calls.
- Đo rescue, harm, best fixed action, self-repair, repair-oracle upper bound
  và các dấu hiệu có trước quyết định. Oracle chỉ là chẩn đoán, bị tính toàn
  cost khi nói về collection; không dùng nó chọn câu trả lời của method.
- Nếu repair bank hầu như không thêm đáp án đúng so với baseline/self-repair,
  dừng cấu hình trước khi train reputation. Nếu headroom có mà state/history
  không dự báo được nó ngoài fold, dừng hoặc đổi một giả thuyết có cơ sở.
- Chỉ sau gate cơ chế mới fit một ứng viên, tune trên development riêng rồi
  đánh giá một lần trên reports chưa xem. Không liên tục tune trên cùng8câu.

Ngưỡng GO/STOP cụ thể, λ và cỡ sample phải khóa trước run tương ứng. Pilot
vài chục câu nhằm loại thiết kế không có tín hiệu, không đủ xác nhận gain nhỏ.
Cỡ final nên tính từ paired discordance/report grouping và mức gain có ích;
tăng seeds trên cùng task không tạo thêm độc lập.

## Baselines quyết định ý nghĩa của kết quả

Ít nhất cần các đối chứng sau, có cùng nguồn, tools và labels hợp lệ:

| Đối chứng | Vấn đề phải loại trừ |
|---|---|
| Single-agent mạnh + tools | Method chỉ thắng vì baseline yếu |
| Cùng agent + self-repair, budget-matched | Gain chỉ do thêm suy luận/calls |
| Best fixed expert/action, chọn trên train | Một action luôn tốt, không cần reputation |
| Fixed cascade / rule-based repair | Rules đơn giản đã đủ |
| Contextual action-value learner/bandit với cùng audited data | Method chỉ đổi tên contextual routing |
| Bỏ local reputation nhưng giữ current-state features và cùng supervised labels | Gain thực từ lịch sử theo ngữ cảnh hay từ tín hiệu hiện tại |
| Reputation toàn cục và history bị shuffle trong train | Fine-grained history có thông tin hay chỉ tăng số feature |
| Recovery/claim-verification method gần nhất được triển khai trung thực | Đủ khác CRITIC/STAR/MoCA-inspired workflow hay không |

Không nhận là đã đánh bại nguyên bản MoCA/STAR/RLCascadeRouter nếu chỉ làm một
bản giản lược. Ghi rõ reproduction hay adapted control. Không cần tái lập mọi
paper trong5tuần; chọn comparator gần nhất và giới hạn claim tương ứng.

Thắng có ích là: accuracy cao hơn ở budget tương đương, hoặc cost thấp hơn với
mức chất lượng được chứng minh theo margin chốt trước. `p>0.05` của accuracy
không tự chứng minh non-inferiority. Báo all-question accuracy, wrong approvals,
coverage, rescue/harm, tokens, wall time và phí đã biết; không chỉ Brier/AUC.

## Đóng góp tiềm năng và giới hạn novelty

Đóng góp mong muốn là một **phương pháp dùng reputation để phân bổ can thiệp
sửa lỗi tại bằng chứng/kế hoạch tính**, cùng bằng chứng rằng lợi ích còn tồn tại
so với cùng-compute self-repair và learned action selection mạnh. Artefact
thực tiễn là một report assistant cho thấy claim nào bị nghi vấn, ai sửa,
source nào thay đổi và chi phí; nhóm đã có nền prototype/Modal để nối vào.

Không tuyên bố "đầu tiên dùng history", "đầu tiên failure-aware", "đầu tiên
claim-level" hoặc "multi-agent luôn tốt hơn single-agent". Các bài liên quan
đã bao phủ các khái niệm đó. Rà soát hiện tại chưa xác nhận một thuật toán mới
ở cấp cộng đồng. Nếu primary learner không hơn contextual-bandit/control gần
nhất thì không đổi tên baseline thắng thành phương pháp của mình.

Trong đồ án AI ứng dụng, một cải tiến được giải thích, so sánh công bằng và
đưa vào workflow hữu ích có giá trị hơn việc cam kết SOTA trước dữ liệu. Một
đóng góp nghiên cứu cho cộng đồng còn cần novelty audit, kết quả độc lập và
code/artefacts tái lập; chưa có gì bảo đảm điều đó hay điểm bảo vệ.

## Phân bổ5–6tuần

Ngày1–2: baseline/hợp đồng dữ liệu đủ dùng, đọc và chọn nền tảng so sánh gần
nhất, chốt hypothesis/case selection/budget. Ngày3–7: chạy pilot cơ chế thật,
đo repair headroom và lựa chọn action ngoài fold. Tuần2–3: một method nhỏ và
controls, không mở sweep lớn. Tuần4: frozen independent evaluation và ablations
quan trọng. Tuần5: hoàn thiện demo và luận văn. Tuần6nếu có: ổn định và bảo vệ.

Nếu cuối tuần1không có headroom và tín hiệu action-choice thì cần đổi agent/
workflow có lý do hoặc thu hẹp claim, không dành hết thời gian còn lại cho
cùng một giả thuyết không có tín hiệu.

Tài liệu gốc trong dự án: `project_status_review_2026-10-18.md`,
`dart_root_causes_and_next_steps_2026-10-05.md`,
`dart_gain_v1_protocol_2026-10-05.md`,
`repguard_a_conference_strategy_2026-10-07.md`,
`repguard_thesis_pilot_decision_2026-10-18.md`, và
`thesis_pilot/analysis.py`. Không sửa protocol/output của các run cũ.
