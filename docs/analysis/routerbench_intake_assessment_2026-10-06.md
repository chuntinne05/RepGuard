# External benchmark intake: đã hoàn tất

Run `c387f6364d2266bf1bf370a9`. Archive tải trên Modal và khớp SHA256 đã khóa. Đã đọc metadata của **649 file /467.023 records**, trong **29 dataset/split**; bỏ qua51file MMLU trước JSON parsing. Không thu thêm solver outputs trong bước này.

## Độ phủ

| Dataset/split | Model | Hợp tất cả query | Chung mọi model |
|---|---:|---:|---:|
| aime/hybrid | 38 | 60 | 60 |
| arc-agi/v1 | 17 | 400 | 400 |
| arcc/test | 20 | 1170 | 1170 |
| arenahard/test | 1 | 750 | 750 |
| arenahard/unspecified | 34 | 751 | 749 |
| arenahard_coding/unspecified | 33 | 253 | 253 |
| arenahard_creative_writing/unspecified | 33 | 250 | 250 |
| arenahard_math/unspecified | 33 | 247 | 247 |
| bbh/test | 20 | 1080 | 1080 |
| emorynlp/test | 20 | 696 | 696 |
| finqa/test | 20 | 1138 | 1138 |
| gpqa/test | 38 | 198 | 198 |
| hle/subset_500 | 15 | 500 | 500 |
| hle/test | 15 | 2158 | 2158 |
| humaneval/test | 22 | 164 | 164 |
| kandk/test | 20 | 700 | 700 |
| korbench/test | 20 | 1210 | 1210 |
| livecodebench/test | 38 | 1055 | 1055 |
| livemathbench/test | 35 | 121 | 121 |
| math500/test | 20 | 500 | 500 |
| mathbench/test | 20 | 150 | 150 |
| mbpp/test | 20 | 970 | 970 |
| medqa/test | 20 | 1273 | 1273 |
| meld/test | 20 | 1231 | 1231 |
| simpleqa/subset_500 | 15 | 500 | 50 |
| simpleqa/test | 15 | 4326 | 4326 |
| swe-bench/verified | 15 | 500 | 500 |
| tau2/test | 12 | 167 | 167 |
| winogrande/valid | 20 | 1267 | 1267 |

Common query dựa trên normalized query hash, không dựa trên success. Coverage chung thấp không có nghĩa model yếu; có thể khác phạm vi chạy hoặc prompt. Nhiều timestamp phải xử lý bằng quy tắc trước outcome, không chọn lần chạy có accuracy tốt hơn.

## Quyết định pilot

Chọn MATH500 vì có evaluator đối chiếu đáp án và đủ500query chung trên20model. Sáu model pilot đã định danh tường minh, mỗi model có đúng một file500records. Không dùng score để chọn model hoặc question. Chỉ lấy48câu trong development hash bucket; các gold ngoài pilot không được đưa vào phân tích.

## Sự cố và kiểm chứng

- Intake v1 tải thành công nhưng matcher theo README không khớp `bench-release/`, nhận0record. V2 sửa riêng layout theo tên file; không có outcome nào được dùng để quyết định sửa.
- Đã tải manifest, status, ledger và inventory. Đối chiếu checksum của sáu file metadata dùng chọn pilot. Bảng coverage toàn archive là aggregate từ worker; không tuyên bố đã tải và tính lại toàn649metadata file trên laptop.
- Parser chỉ xuất index, query hash/length và tên trường. Tokenizer đi qua JSON nhưng bỏ qua giá trị gold/output; không xuất score vào inventory.
- Không tìm thấy khai báo giấy phép gốc trong GitHub/HF metadata đã kiểm tra. Raw archive và derivatives nằm trong storage private, không đưa vào Git hoặc gán MIT của dự án cho dữ liệu nguồn.
- Đây là intake, chưa phải DART đã thắng trên dữ liệu mới. Pilot thật có protocol và worker riêng.

[Intake v1](routerbench_intake_protocol_2026-10-05.md) · [Layout amendment v2](routerbench_intake_v2_protocol_2026-10-05.md) · [Pilot](routerbench_pilot_protocol_2026-10-06.md)
