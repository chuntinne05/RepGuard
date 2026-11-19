# Protocol khóa trước khi đọc outcome từng task: AppWorld leaderboard

**Ngày:** 04/10/2026. **Pha:** kiểm tra khả năng của pool (Gate A), chưa phải đánh giá DART. Manifest đi kèm: `dart_leaderboard_pool_manifest_2026-10-04.json`, sinh bởi `freeze_dart_leaderboard_pool.py`. Đến thời điểm khóa, chỉ đã xem tên file Git, README, mã schema `pack/unpack` và danh sách ID công khai; chưa giải mã bundle, xem ma trận task × agent hoặc đọc `_leaderboard.json`. Có biết số tổng hợp từ Xia & Wang 2026 trong tài liệu trước; vì vậy leaderboard chỉ là dữ liệu **khám phá**, không phải xác nhận độc lập.

## Pool và dữ liệu đã khóa

- 14 baseline lịch sử từ bốn scaffold `react`, `plan_exec`, `full_code_refl`, `ipfuncall` và bốn model `gpt4o`, `gpt4turbo`, `llama3`, `deepseekcoder` theo những cặp hiện có trong repository. Chọn toàn bộ 14 trong nhóm này dựa trên tên/config và sự có mặt của hai bundle, không chọn theo điểm. Các submission mới hơn không nằm trong estimand này. Có thể phân tích phụ toàn bộ agent sau, nhưng phải ghi là exploratory.
- Repository leaderboard tại commit `c1f56015cf7c3441ff1933f5bfbec879798d7bbe`. Danh sách `test_normal` cục bộ AppWorld 0.1.3 có 168 task thuộc 56 generator, ba task/generator. Chia 5 outer fold bằng SHA256 ID generator; fold đã nằm trong manifest. Mỗi fold giữ nguyên generator; huấn luyện history trên bốn fold còn lại, chấm held-out fold; mọi lựa chọn hyperparameter phải nested trong train của outer fold. Đây là cross-validation khám phá trên public leaderboard, không phải sealed holdout.
- Danh sách `test_challenge` cục bộ có **417** ID; Xia & Wang báo **380** task trong phân tích của họ. Sai khác này là cảnh báo compatibility: không được đồng nhất tập của paper với tập hiện có. Chỉ dùng challenge sau khi xác minh schema, version và ID giao nhau; phải báo denominator thực tế và mọi thiếu hụt.
- Không dùng primary app, skill từ state check, kết quả agent, hoặc difficulty hậu nghiệm làm feature điều hướng. Feature online ban đầu chỉ là instruction và metadata thực sự hiện ra cho agent trước hành động. Nếu task text không lấy được hợp lệ từ dữ liệu công khai, Gate A chỉ phân tích capacity, chưa làm router.

## Kiểm tra hợp lệ trước khi đọc outcome

1. Tải nguyên vẹn 14 bundle `test_normal` bằng Git LFS, xác minh hash LFS. Đối với challenge chỉ tải khi kiểm tra normal xong.
2. Giải mã **cục bộ** bằng AppWorld, đọc `metadata.json`, `version/data.txt`, `version/code.txt`, file evaluation và log *chỉ để xác minh schema/ID/usage*. Không công bố nội dung giải mã. Lưu raw dưới thư mục tạm hoặc thư mục ignored.
3. Agent được tính eligible nếu bundle mở được, version/data và ý nghĩa exact success tương thích, evaluation có ít nhất 95% trong 168 ID đã khóa. Phân tích chính dùng complete case trên giao ID của tất cả eligible agents; vẫn báo coverage toàn bộ và lý do loại. Không loại agent chỉ vì success thấp. Nếu giao ID dưới 150/168, dừng Gate A và tìm nguồn khác.
4. Nếu evaluation có sẵn task success nhưng không có usage chuẩn hóa, endpoint cost tạm là số agent invocation; không ước lượng USD. Kiểm tra logs có thể định lượng interaction/token cho phân tích phụ, nhưng không giả định chúng đồng nhất giữa các scaffold.

## Phân tích Gate A đã định trước

- Với mỗi agent: số task đúng / tổng complete-case. Với mọi cặp: `A-only`, `B-only`, hai bên cùng đúng/sai. Báo rescue hai chiều, McNemar/paired bootstrap theo generator và CI; oracle best-of-pool chỉ là **trần bất khả thi**, không phải kết quả router.
- Mốc thực dụng để tiếp tục phát triển DART trên pool: có **ít nhất một cặp** với ≥10 task A-only và ≥10 task B-only trên complete-case, và ≥20 task bất đồng tổng cộng. Điều kiện này chỉ chứng minh có cơ hội quyết định; không chứng minh router học được hoặc hơn baseline. Nếu trượt, không fit DART trên pool này.
- Kiểm tra mức trần khi giữ một agent cố định so với oracle, độ biến thiên theo nhóm generator và độ tin cậy của feature online. Không tối ưu một cặp theo toàn ma trận rồi gọi cặp ấy là lựa chọn đã khóa. Nếu chọn subpool sau Gate A, toàn bộ kết quả trên leaderboard về subpool ấy là exploratory; xác nhận cuối cần task/agent mới.
- Nếu qua Gate A, viết protocol thứ hai khóa DART, đối chứng, audit budget, cost endpoint, mức cải thiện tối thiểu, attack schedule và kiểm định trước khi chấm xác nhận. Không mở 420 MMLU-Pro sealed holdout hiện có để chọn phương pháp.

## Giới hạn và khả năng tái lập

Leaderboard đã công khai, paper khác đã phân tích 14 agent và có thể có contamination của các model hậu kỳ. Cross-validation tránh rò task trực tiếp giữa history và prediction nhưng không biến dữ liệu này thành xác nhận độc lập. Task cùng generator được giữ chung fold; vẫn có phụ thuộc giữa các generator và app. Chỉ có 56 generator nên CI phải cluster theo generator. Bundle được mã hóa theo quy định AppWorld; Git chỉ chứa manifest, code và thống kê tổng hợp, không chứa trajectory hoặc gold đã giải mã.
