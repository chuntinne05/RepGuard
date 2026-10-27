# DART: bước tiếp theo sau vòng history rectification

## 1. Câu hỏi cần trả lời tiếp

Ứng viên hiện tại có tăng hiệu quả sử dụng nhãn đáng tin từ lịch sử bị đánh giá
sai trên dữ liệu mới hay không? Đây là câu hỏi hẹp hơn việc chứng minh một router
neural thắng mọi baseline, nhưng có giá trị triển khai: chọn agent tốt với ít
nhãn gold hơn khi đã có lịch sử execution và feedback rẻ hơn.

Chưa có cơ sở bảo đảm thắng, nhận bài A/A*, hay nâng giả thuyết này thành kết luận.
Không tiếp tục sửa hyperparameter trên 168 task AppWorld để làm CI dương.

## 2. Những thứ giữ nguyên

- Paired CFJudgeFactor ở run `cd0b2656876f7f973d7b67ce` là ứng viên development
  được giữ lại. Tất cả tham số, feature, cross-fit, estimator và predictions được
  đóng băng. Không đổi sang ablation có điểm cao hơn ở ngân sách khác.
- Giữ nguyên kết quả âm và gate cũ. Kiểm tra SH mới không thay thế gate đó.
- Các bộ sealed holdout trước đây vẫn chưa được dùng. Không mở chúng để chọn
  phương pháp hay bỏ qua điều kiện mở đã khóa trong protocol trước.
- Các kết quả hiện tại là global agent selection; không đổi tên thành routing
  theo từng task hoặc transfer đã được chứng minh.

## 3. Chọn dữ liệu phù hợp, không chọn theo accuracy

Ứng viên nguồn dữ liệu là
[LLMRouterBench](https://github.com/ynulihao/LLMRouterBench/blob/main/README.md),
đã có [bài Findings ACL 2026](https://aclanthology.org/2026.findings-acl.1881/).
Tài liệu nguồn mô tả raw model predictions, evaluator scores, token/cost metadata
và bộ adapters cho các router. Đây là khả năng tái sử dụng execution thật; chưa
chứng minh nó cung cấp sẵn noisy historical feedback cần cho DART.

### Intake trước khi học mô hình

1. Khóa revision/archive checksum đã inventory; kiểm tra nguồn và điều kiện sử
   dụng. Không mặc định mọi dữ liệu kế thừa giấy phép của code.
2. Chỉ xuất inventory không chứa outcome: dataset/model IDs, task IDs hoặc hash
   prompt, số lượng và trường dữ liệu có mặt. Không xếp hạng dataset/model bằng
   success trước khi chọn pool. Lưu các file nhãn ngoài giao diện learner.
3. Loại mọi MMLU/MMLU-Pro khỏi study mới ban đầu để không đụng các holdout đã
   khóa; kiểm tra exact/near duplicates bằng prompt trước khi chia train/test.
4. Ưu tiên các bài có evaluator objective có thể kiểm chứng (đáp án hoặc test
   chương trình). Phân biệt rõ gold objective và score vốn do LLM judge chấm;
   không gọi một judge score khác là ground truth đáng tin tuyệt đối.
5. Kiểm tra common task–model coverage bằng ID. Missing execution phải báo riêng;
   không tự đổi thành failure. Nếu số task chung quá nhỏ, dừng và báo coverage.

Archive mới **chưa tải/chưa mở outcome** khi viết kế hoạch này. Phần này là kế
hoạch thu nhận dữ liệu, chưa phải protocol xác nhận hoặc thí nghiệm đã hoàn thành.

## 4. Hai vấn đề phải xử lý trước khi nói “chạy lại cùng phương pháp”

### Agent metadata không giống nhau

AppWorld có trục model × scaffold; FactorRidge chia sẻ thông tin trên hai trục.
LLMRouterBench chủ yếu có model IDs. Không được cắt chuỗi tên model một cách tùy
tiện rồi coi các phần là model/scaffold. Cần metadata adapter tường minh dựa trên
thông tin được công bố, hoặc một version model-only ghi rõ đã thay đổi cấu trúc.
Version đổi cấu trúc cần development split riêng và khóa trước test; không được
gọi là xác nhận nguyên trạng cấu hình AppWorld.

### Historical feedback phải độc lập với gold

Nếu archive chỉ có prediction và evaluator score, không thể đưa score vào cột
judge rồi tuyên bố học từ imperfect feedback. Cần tạo judgment thật chỉ từ
prompt và candidate output, không đưa reference answer, evaluator score, test
result hay agent identity vào prompt judge. Ghi lại model digest, prompt hash,
thinking policy, truncation, token/latency/cost và các lỗi parse.

Chỉ thử pilot có giới hạn trên development split trước để xác minh định dạng
và chi phí. Tất cả lời gọi, kể cả lỗi/retry, phải tính vào budget. Không gọi judge
cho các candidate của query test rồi tính chi phí như chỉ chạy một solver.

## 5. Thiết kế kiểm chứng cần khóa trước test

- Tách ba phần bằng task/generator/group trước khi đọc labels để lựa chọn:
  development, calibration/audit history và final evaluation. Chỉ giữ những
  task gần trùng trong cùng nhóm. Không dùng random rows nếu có template chung.
- Khóa candidate, agent pool, gold budgets, seed list, primary metric, primary
  comparison và practical improvement threshold trong protocol mới. Chọn cỡ
  mẫu bằng precision/power trên development groups, không lặp thêm seeds trên
  cùng task đến khi có ý nghĩa thống kê.
- Đối chứng tối thiểu cùng quyền truy cập: UniformGlobal, PairedGlobal,
  IndependentSH, PairedSH, gold-only structural estimator, raw feedback,
  calibration không correction và correction không feedback.
- Nếu tuyên bố routing theo task, bổ sung các router liên quan được train trên
  đúng nhãn được phép. Full-label router chỉ là upper reference khi nó được cấp
  nhiều gold hơn, không đặt vào bảng như cùng ngân sách.
- Báo primary mean và uncertainty theo đơn vị độc lập, hiệu quả trên từng
  dataset/domain, những nhóm bị hại, cùng tổng chi phí historical judging,
  annotation, training và deployment. Judge sunk cost và fresh collection cost
  cần thành hai kịch bản rõ ràng.
- Final evaluation chạy một lần cho version đã khóa. Nếu fail, lưu nguyên và
  quay lại một development version mới; không tune trên final outcomes.

## 6. Điều gì mới đủ tạo contribution phương pháp?

Ghép ridge, paired sampling và cross-fitting chưa tự đủ novelty. Đóng góp cần
chỉ rõ lợi ích nào mà các baseline thiếu, điều kiện để lợi ích tồn tại, và chi
phí phải trả. Một hướng cần nghiên cứu thêm là phân bổ nhãn cho **chênh lệch
residual giữa các agent còn cạnh tranh**, đồng thời giữ khả năng ước lượng đúng
khi nhãn được lấy thích nghi. Đây là giả thuyết mới, chưa được implement ở vòng
hiện tại; không gắn công thức rectifier uniform vào adaptive mask rồi mặc định
nó vẫn đúng. Cần biết xác suất lấy mẫu/support hoặc estimator hợp lệ khác,
sample splitting phù hợp và đối chứng adaptive gold-only.

Chỉ ưu tiên nhánh này khi kiểm tra cho thấy feedback giảm variance của residual
differences ngoài mẫu và lợi ích trả được chi phí judge. Nếu không, phương pháp
gold-only hiệu quả nhãn có thể là kết luận thực tiễn tốt hơn, dù không xác nhận
giả thuyết hiệu chỉnh imperfect feedback ban đầu.

## 7. Thứ tự làm

1. Hoàn thành kiểm chứng baseline SH và lưu toàn bộ kết quả (batch đã chạy trên
   Modal; báo cáo riêng chứa số cuối cùng).
2. Làm intake metadata, coverage và giấy phép của nguồn mới; chưa train/test.
3. Khóa task groups/model metadata và giới hạn pilot judge trên development.
4. Đo reliability và residual variance trên development; quyết định có đáng
   thu judgment lớn hay không bằng tiêu chí được khóa trước pilot.
5. Chỉ sau đó khóa protocol đầy đủ và chạy xác nhận. Đầu ra là kết quả có thể
   bác bỏ giả thuyết, không phải một quy trình bắt buộc phải cho số thắng.

Nguồn thuật toán liên quan: [Sequential Halving](https://proceedings.mlr.press/v28/karnin13.pdf),
[PPI++](https://arxiv.org/html/2311.01453v2),
[Cross-PPI](https://arxiv.org/html/2309.16598v2). Các bảo đảm của các bài này
không tự áp dụng cho estimator shrinkage và adaptive acquisition đề xuất ở đây.
