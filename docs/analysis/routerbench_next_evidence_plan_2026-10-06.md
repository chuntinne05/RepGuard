# Bước tiếp sau pilot MATH500 đã hoàn tất

## Điểm xuất phát và câu hỏi còn thiếu

Pilot `bad5a513bd5d227711eb1e0d` đã hoàn tất 288/288 judgment thật. Cả hai
screening gates PASS; phương sai chênh lệch residual giảm khoảng 30,53% trên
diagnostic cross-fit. Điều này trả lời rằng feedback có thông tin hữu ích trong
pool development đã chọn. Chưa trả lời rằng dùng feedback sẽ chọn model tốt hơn
với ít nhãn gold, hoặc tiết kiệm tổng chi phí. Toàn bộ gold của 48 câu đã được
dùng trong pilot; không biến chúng thành một test set chưa từng quan sát.

Đây là kế hoạch công việc, chưa phải protocol xác nhận đã khóa hoặc một run mới
đang chạy. Không thay đổi source, split, gate hay kết quả của pilot hoàn tất;
không mở các sealed holdout MMLU/AppWorld trước đây.

## 1. Kiểm tra gold thưa trước khi mua thêm judgment

Dùng lại đúng 48 câu, sáu model và 288 judgment đã kiểm chứng để làm development
stress test. Việc này không cần gọi solver hay judge mới. Giữ nguyên bộ features
model-only, ridge penalties và thinking policy của pilot; không chọn cấu hình
theo kết quả test này.

Tách learner khỏi evaluator bằng giao diện audit: learner chỉ nhận gold của
các cell đã mua, evaluator giữ gold của câu held-out. Cấp ngân sách 5%, 10%, 20%
trên ma trận lịch sử TRAIN; công bố số cell nguyên thực cấp, gồm mọi cell dùng
để calibration, correction, chọn mô hình hoặc tuning. Ngân sách primary là 10%.
Không học calibration từ toàn gold rồi báo kết quả dưới tên gold thưa.

So sánh ít nhất UniformGlobal, PairedGlobal, IndependentSH, PairedSH, model-only
gold ridge, raw-feedback selection, calibrated feedback và residual correction.
Mỗi baseline dùng đúng tổng số gold cells được cấp; cùng seed và fold khi thích
hợp. Những phương pháp dùng sampling khác nhau không bắt buộc nhận cùng mask,
nhưng phải ghi đầy đủ unique audit IDs và số nhãn thực đã dùng. Chốt quy tắc
rounding, tie breaking, phần dư ngân sách và các seed trước replay.

Đầu ra cần báo: success của model được chọn trên câu held-out, regret so với
best fixed model chỉ dùng làm reference sau quyết định, Brier và residual variance
của predictor học với gold thưa, model selection stability, rescue/harm và chi
phí feedback. Đơn vị bất định là task/group, không coi 20 seeds trên cùng 48 câu
là 960 câu độc lập. Replay này là exploratory development; mọi gate mới phải
khóa trước chạy, không dùng một CI dương để xóa các gate AppWorld đã FAIL.

Nếu tín hiệu biến mất khi gold thưa, phân biệt thiếu nhãn calibration, residual
correction quá nhiễu và chênh lệch model quá nhỏ. Báo các lỗi theo ablation đã
đăng ký; không mở rộng judgment chỉ để tăng số lượng. Nếu tín hiệu còn ổn định,
dùng kết quả để thiết kế study tiếp, không gọi đó là xác nhận cuối.

## 2. Chuẩn bị nhóm và dữ liệu trước study lớn hơn

Từ prompt-only metadata, kiểm tra exact/near duplicates và các template trên
MATH500. Khóa thuật toán, ngưỡng grouping và membership trước khi xem gold của
các câu ngoài pilot. Các nhóm liên quan đến pilot phải được đánh dấu đã dùng
cho development; không chuyển họ hàng gần của chúng sang final evaluation.
Giữ sáu model đã chọn, không lọc model theo accuracy.

Sau grouping, báo số nhóm độc lập còn lại và khả năng chia development,
calibration/history, evaluation. Không mặc định 500 câu đủ power hoặc tất cả
độc lập. Chọn cỡ mẫu theo mức cải thiện thực tiễn và độ rộng CI mong muốn; nếu
coverage không đủ, chọn thêm nguồn objective-scored từ inventory bằng tiêu chí
đã khóa và metadata, không bằng score đã xem. Các raw artifacts tiếp tục private.

## 3. Khóa đối tượng quyết định và chi phí

Study đầu tiên nên kiểm tra **chọn một model cho các task tương lai từ lịch sử**.
Judge được dùng trên các execution lịch sử đã có, không được xem outputs của
mọi model trên câu evaluation rồi tính chi phí như chỉ chạy một solver. Chỉ gọi
đây là global model selection. Muốn tuyên bố task-contextual DART cần protocol
riêng: decision chỉ từ prompt và lịch sử được phép, task features rõ ràng,
router controls cùng nhãn và evaluation theo nhóm chưa thấy.

Báo hai kịch bản chi phí: feedback đã có trong lịch sử; và feedback phải mua mới.
Cùng ngân sách gold chưa phải cùng tổng USD. Chi phí mới gồm toàn bộ judgment,
retry, annotation, learner và inference; không đổi token count thành tiền khi
chưa có đơn giá/hóa đơn phù hợp. Tổng inference 7,40 phút của pilot không phải
GPU wall time hay tổng phí Modal.

## 4. Điều kiện cho nhánh phương pháp mới

Calibration, ridge, cross-fitting và paired sampling riêng lẻ chưa đủ novelty.
Hướng cần kiểm tra là chọn nhãn cho những chênh lệch residual ảnh hưởng trực tiếp
đến quyết định giữa các model còn cạnh tranh, thay vì chỉ giảm lỗi dự báo trung
bình. So sánh cùng cơ chế acquisition với gold-only để tách giá trị của judge
khỏi giá trị của phân bổ nhãn tốt hơn.

Chưa implement nhánh adaptive trong kế hoạch này. Trước khi dùng phải thiết kế
sampling/support, estimator và sample splitting phù hợp; không đưa adaptive mask
vào uniform correction rồi tự coi estimator vẫn unbiased. Cần chứng minh hoặc
kiểm tra đúng điều kiện lý thuyết, kiểm thử budget/leakage và replay đối chứng
trước khi chi thêm GPU. Positive pilot không bảo đảm hướng này sẽ thắng.

## Thứ tự và các artifact cần giao

1. Hoàn tất report pilot, lưu verification và push phần public lên `dev`.
2. Khóa protocol stress test gold thưa; implement audit interface, budget log,
   controls và kiểm thử leakage; chạy development replay trên artifacts đã có.
3. Hoàn tất prompt-only grouping và báo precision/power, trước gold ngoài pilot.
4. Nếu development còn tín hiệu, khóa version, primary comparison, effect
   threshold, uncertainty và chi phí; submit collection có giới hạn bằng Modal
   detached worker với ledger, bounded retries và checkpoint.
5. Chạy evaluation một lần cho version đã khóa; báo mọi kết quả. Nếu FAIL,
   giữ nguyên kết quả, không tune trên final outcomes hoặc hứa thắng baseline.

[Kết quả đã kiểm chứng](routerbench_pilot_assessment_2026-10-06.md) ·
[Protocol pilot](routerbench_pilot_protocol_2026-10-06.md) ·
[Kế hoạch bằng chứng trước intake](dart_next_evidence_plan_2026-10-05.md)
