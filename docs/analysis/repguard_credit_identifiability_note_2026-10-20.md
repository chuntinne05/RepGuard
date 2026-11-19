# Gán credit không tự tạo ra một estimator tốt hơn

Ghi chú thiết kế trước khi mở điểm pilot TAT-QA vòng3. Đây là lập luận đại số,
không phải kết quả model hay một mô phỏng thay cho inference thật.

## Tránh một phương pháp mới chỉ về tên

Gọi outcomes của cùng incumbent là `Y0, YE, YO, YEO`. Đặt:

`dE = YE - Y0`, `dO = YO - Y0`,

`I = YEO - YE - YO + Y0`.

Khi đó `dEO = YEO - Y0 = dE + dO + I` đúng theo định nghĩa. Đo interaction
có thể giúp giải thích một lỗi; chưa đủ để chứng minh một thuật toán học mới.

Giả sử tất cả labels được thu trên cùng các context và dùng cùng features X,
cùng trọng số mẫu, cùng ridge penalty λ. Predictor ridge tuyến tính là một
toán tử tuyến tính theo labels:

`B(y) = (XᵀX + λP)⁻¹ Xᵀy`.

Do đó `B(dE) + B(dO) + B(I) = B(dEO)`.

Học ba regressor rồi cộng lại cho EO **cho đúng cùng dự đoán** như một
contextual action-value regressor học dEO trực tiếp. Tách credit, đặt tên
reputation cho các hệ số hoặc vẽ thêm một graph không phá được đẳng thức này.
Với cùng loss/intercept penalty và design matrix, không thể giải thích một
win bằng việc “có interaction-aware credit” nếu hai thuật toán tương đương.

Nếu bỏ I, ta áp đặt giả thiết additive effects. Nếu dùng penalty khác cho I,
ta đưa vào prior rằng interaction nhỏ/thưa. Nếu transfer giữa nhóm tasks,
ta thay đổi regularization/feature structure. Đây có thể là những lựa chọn
hữu ích, nhưng phải ablate và so với learner thông thường được cấp cùng
features, cùng history và một regularization budget hợp lý. Không so với
baseline thiếu thông tin rồi gán gain cho cơ chế credit.

## Correlation có ích trong quyết định nào?

Với một lần chọn action a rồi kết thúc, expected reward chỉ cần
`E[Ya | state]`; correlation giữa các outcomes chưa được quan sát không tự
thay đổi action tốt nhất. Một mô hình joint16patterns của bốn binary outcomes
chỉ có ý nghĩa thêm nếu đem lại một prior/transfer tốt hơn, quản lý bất định
đúng hơn, hoặc có quan sát tuần tự dùng để cập nhật quyết định kế tiếp.

Trong deployment không có Y0/YE thật của câu hiện tại. Program chạy được,
token tồn tại và hai agent đồng ý **không phải** quan sát những biến success
này. Không được condition policy vào correctness hiện tại vì history từng
có full outcomes. Muốn dùng checker observations, phải mô hình hóa/đánh giá
đúng các biến checker mà hệ thống thật sự nhìn thấy.

Vì vậy, candidate contribution hợp lý phải chỉ ra cụ thể:

1. Cấu trúc transfer/regularization nào giúp trong history thưa, có bao nhiêu
   thông tin đã dùng và vì sao không tương đương một baseline cùng thông tin.
2. Feedback nào là audit thật, feedback nào chỉ là partial check; thiếu audit
   thì đại lượng nào còn nhận dạng được, đại lượng nào không.
3. Chính sách nào dùng được các estimates trước khi biết target và thắng trên
   task mới; oracle union và fitted in-sample accuracy không trả lời câu này.

Không fit một learner trên bank thiếu headroom để chứng minh các điểm trên.
Pilot vòng3 chỉ kiểm điều kiện cơ chế đầu tiên: có interventions hữu ích hơn
strong single-agent controls trong bank thật hay không.
