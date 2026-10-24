# Ứng viên phương pháp sau hai gate thất bại

Ngày 19/10/2026. **Thiết kế nghiên cứu đề xuất, CHƯA được triển khai hoặc chứng
minh vượt baseline.** Không nhận đây là novelty đã xác nhận. Không gọi những
agent đã chạy ở vòng2 là learner mô tả dưới đây.

## Câu hỏi đủ hẹp cho khóa luận

Lịch sử được audit có giúp quyết định **sửa phần nào của một phép tính, bằng
agent nào, hoặc giữ nguyên** tốt hơn một agent mạnh tự sửa và một contextual
action-value learner với cùng dữ liệu, khi checker chỉ kiểm được một phần
source/quantity/program và phải trả giá cho cả sửa hỏng lẫn thêm compute?

Tên diễn đạt phù hợp với đề tài đã thông báo có thể là: **Điều phối sửa lỗi
trong hệ đa tác tử bằng uy tín theo trạng thái bằng chứng và hiệu quả can
thiệp**. Domain tài chính là môi trường kiểm chứng, không phải đóng góp chỉ
vì chuyển ứng dụng sang tài chính. Không đổi toàn bộ topic multi-agent/reputation.

## Những kết quả buộc thiết kế phải thay đổi

- Vòng2: direct PoT/self1/self2 cùng17/24; compose16; oracle union17. Không có
  selection headroom trong bank này. Fit learner chỉ để chọn các output đó
  không thể vượt17 trên mẫu đã thu.
- Trên16 report mới: 8B/14B cùng11/16, correctness masks trùng nhau, zero unique
  success. Đổi tên vai trò hay kích thước model chưa tạo specialization hữu ích
  trong các probes này. Không suy ra mọi backbone đều có kết quả như vậy.
- FRT cho thấy numeric source references qua check vẫn có thể gán sai năm;
  EW cho thấy hai fact đúng riêng lẻ không tự được tổng hợp đúng scope. WRK
  còn có nghi vấn metric của target, cần audit độc lập.

Do đó không tiếp tục tune global/local reputation trên bank cũ. Phải kiểm một
cơ chế can thiệp tạo output mới, đồng thời giữ baseline mạnh và feedback công bằng.

## Phương pháp cần xây, thay cho weighted voting

**1. Trạng thái kiểm được và chưa kiểm được.** Giữ chương trình PoT quen thuộc,
đọc được bởi con người; xây bản ghi kèm metric, kỳ/scope, số/đơn vị, source và
dependency của phép tính. Không quay lại một DSL làm solver suy giảm năng lực.
Giữ nguyên bảng có thứ tự và block năm; không gán hàng đầu làm header cho mọi
cell. Mỗi check ghi đúng phạm vi: token tồn tại, program chạy được, hay binding
đã được kiểm. Source existence không được đổi tên thành semantic correctness.

Đây phần lớn là engineering/representation, phải cấp cùng cho baseline. Nếu
phần này một mình đã giải quyết được vấn đề thì báo gain đúng cho representation,
không nhận là gain reputation.

**2. Action có phạm vi, bao gồm sửa phối hợp.** Bắt đầu với KEEP; sửa evidence/
period binding; sửa operation/quantity unit; và bundle sửa cả hai. Cho same-agent
self-review làm action/control riêng. Patch ghi phần nào đổi, phần nào giữ.
Acceptance kiểm permissions/execution; nó không có oracle biết đáp án đúng.
Ràng buộc scope có thể ngăn cả một sửa hữu ích, nên cần unrestricted controls.

**3. Credit từ kết quả can thiệp thực.** Với cùng incumbent trên history,
thu những repair branches thật. Nếu hai patch tương thích có thể kết hợp cơ
học, chạy chương trình kết hợp bằng executor thật, lưu trace và charge chi phí
tạo patch. Không dùng một LLM-judge tưởng tượng outcome để thay cho execution.
Program composition không có thêm LLM call nhưng vẫn là một can thiệp cần
ghi rõ; không được gán gold để chọn patch khi deployment.

Trên history đã audit, bốn kết quả KEEP/E/F/E+F có thể cho biết đóng góp bị che
bởi lỗi khác. Một interaction diagnostic là
`Y(E+F) - Y(E) - Y(F) + Y(KEEP)`.
Không coi công thức này, Shapley hay counterfactual credit là mới:
[C3](https://arxiv.org/abs/2603.06859) và
[GCJR](https://arxiv.org/abs/2608.29228) là related work trực tiếp.
Việc gán credit chỉ hữu ích nếu giúp policy trên task
mới; không thưởng vì một fact đúng mà kết quả cuối vẫn không cải thiện.

**4. Uy tín của hiệu quả sửa và transfer có cấu trúc.** Estimator học rescue,
harm và cost theo agent/configuration × repair type × trạng thái. So một model
phân cấp có shrinkage và interaction với counts/global reputation, mô hình bỏ
interaction và regularized contextual action-value có cùng inputs/labels.
History index phải chứa model digest, prompt/contract và executor version;
không dùng chung một profile chỉ vì agent giữ nguyên tên sau đổi scaffold.

Chính cách transfer/credit dưới dữ liệu thưa là candidate contribution. Nếu
learner thông thường với cùng thông tin đã làm tương đương thì chưa có đóng
góp riêng của estimator reputation. Không ép đặt tên cho một contextual bandit
để nhận novelty.

**5. Quyết định trước khi biết kết quả.** Chọn agent/scope/KEEP bằng estimated
rescue − estimated harm − λ·incremental cost, có bất định ước lượng. Gold chỉ
ở history được audit và evaluator. Không dùng correctness câu hiện tại để
quyết định gọi expert, dừng hay chọn output. Bất định Bayes/heuristic không tự
là bảo đảm an toàn; muốn claim risk bound phải có thiết kế thống kê tương ứng.

## Phép thử kế tiếp nên khóa trước khi chạy

Dữ liệu hiện có thêm một solver baseline: Qwen3.5 27B tắt native thinking,
13/16 theo official target trên development, mean Ollama eval khoảng 11.07 giây.
Đây là cải thiện cấu hình solver hậu nghiệm, không phải reputation hay test
độc lập. Native 4096 bị 4 truncations; không dùng kết quả đó để phán model lớn thiếu
năng lực. Cấu hình tắt thinking phải được cấp công bằng cho controls khi chốt
phép thử tiếp. Các điểm mơ hồ về source/metric vẫn cần audit, bất kể score tăng.

Dùng 32 report development kế tiếp trong reservation (khác 16 đã probe và khác
150 confirmation), sau một preflight interface trên dữ liệu đã xem. Chốt một
backbone nền đủ mạnh sau đối chứng27B; giữ hết case đã chọn, cả câu đúng để đo
harm. Thu KEEP và bank sửa scope/bundle, cùng self-review1/2. Sốcalls phải được
khóa theo implementation thật, không nhầm32 câu thành32 calls. Không chạy batch
lớn chỉ vì một ví dụ EW có vẻ hứa hẹn.

Chỉ mở rộng FinQA sau semantic preflight. Nếu các vấn đề scope/metric ở audit
có tính hệ thống, ưu tiên pilot trên TAT-QA với contract value/scale rõ và bộ
chấm gốc đã chuẩn bị; không tiếp tục tối ưu model để khớp những target đang
tranh chấp. Đổi corpus kiểm chứng vẫn giữ câu hỏi multi-agent/reputation, không
đổi toàn bộ topic. TAT-QA cũng cần kiểm, không mặc định nhãn của nó hoàn hảo.

Gate phải kiểm **rescue mới vượt strong self-review** và oracle headroom sau
cùng normalizers; tiếp theo mới kiểm tín hiệu chọn action ngoài fold. Không
qua thì dừng cấu hình trước train reputation. Đây là gate cho ứng viên mới,
không nới lại hai gate đã thất bại.

Khi có tín hiệu, mới thu training history trên report chưa dùng sửa phương pháp,
calibrate riêng, rồi chạy policy thật trên confirmation. Đánh giá các mức audit
budget bằng cách che nhãn đúng cho tất cả controls; phân biệt offline paired
collection với production chỉ thấy action đã gọi. Không quảng bá full-feedback
labels thành sparse/online feedback. Nếu dùng replay, gọi đúng là replay trên
real responses; final live-policy run phải thực sự gọi những action được chọn.

## Điều kiện để khóa luận có đóng góp phương pháp

1. Chỉ ra một cải tiến end-to-end có ích còn tồn tại so với same-compute self-
   review, best fixed action và learned contextual selector đủ mạnh. Không cần
   thắng mọi frontier model, nhưng phải công bố rõ phạm vi và quality–cost.
2. Ablate graph/checker, scope permissions, interaction credit và transfer;
   controls nhận cùng source/tools/labels và comparable effective training dose.
   Current-state-only learned selector vẫn dùng history qua training, nên
   không gọi nó là một comparator "không dùng lịch sử" theo nghĩa tuyệt đối.
3. Kiểm trên report chưa dùng chọn phương pháp; tính power từ paired
   discordances và effect/margin trước khi mở confirmation.150 report đang giữ
   riêng không mặc nhận đủ power. Công khai issuer overlap và pretraining risk.
4. Official FinQA score và human semantic audit giữ riêng.40 câu có phiếu blind
   review nhưng hiện0 annotation hoàn tất; không tự thay target cho method thắng.
5. Kiểm corpus/backbone thứ hai nếu tín hiệu đủ mạnh. TAT-QA hiện mới chuẩn bị
   dữ liệu/evaluator, chưa có model result. Không gọi một adapted comparator là
   tái lập nguyên bản MoCA/STAR/C3.

Prototype chỉ cần cho thấy input → calculation/claims → quyết định sửa/giữ →
nguồn và chi phí. Công sức chính vẫn dành cho estimator, protocol, thí nghiệm
đủ sức kết luận và viết luận văn. Không có bảo đảm trước superiority, novelty
hoặc điểm hội đồng.
