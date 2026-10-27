# Week 5 — đánh giá judge thật trên Modal, đủ 14 môn MMLU-Pro

**Ngày chạy:** 29/09/2026. **Trạng thái:** hoàn tất lượt thu thập judge 280/280 câu, 694/694 case đáp án khác nhau. Đây là phép đo chất lượng feedback cho HistRepEval; **chưa** là kết quả ECRT sử dụng feedback này và chưa xác nhận cải thiện bài báo.

## Cấu hình và nguồn dữ liệu

- Từ history calibration Week 3, chọn trước 20 câu cho mỗi môn bằng seed 1618033. Bốn agent Week 3 đã có 1.120 câu trả lời thật. Gộp đáp án trùng trên cùng câu còn 694 request judge; mở rộng lại khi phân tích theo agent, không coi 1.120 hàng là độc lập.
- Judge chạy trên Ollama tại Modal: `qwen3:14b`, digest `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`, `think=false`, temperature 0, top-p 1, JSON schema, tối đa 256 token. Protocol hash `aea88c2c99be006561040acf1a243c4f08cbf0bd9146c27020df1557408a4f48`.
- Prompt chỉ có câu hỏi, lựa chọn và một đáp án ứng viên; không có gold hoặc tên agent. Gold được mở sau khi lưu ledger để chấm offline. Runner và analyzer tương ứng là `run_real_week5_modal_judge.py` và `analyze_real_week5_modal_judge.py`.
- 694/694 phản hồi có JSON hợp lệ, không câu nào bị cắt vì giới hạn token; có 8 mâu thuẫn giữa verdict và việc `chosen_letter` trùng đáp án ứng viên. Có một lỗi kết nối Modal ở giữa lượt chạy, đã ghi vào error ledger và resume đúng case theo manifest; không có case bị mất hoặc lặp. Tổng 194.183 input token, 19.159 output token và 1.484,73 giây thời gian request; trung vị request 1,79 giây, hai request trên 10 giây do tải/khởi động.

## Chất lượng verdict

| Chỉ số trên 694 case riêng biệt | Kết quả |
|---|---:|
| TP / TN / FP / FN | 140 / 374 / 121 / 59 |
| Accuracy | 514/694 = **74,06%** |
| CI 95% bootstrap lấy mẫu theo câu | **70,78–77,36%** |
| False positive rate trên đáp án thực sự sai | 121/495 = **24,44%** |
| False negative rate trên đáp án thực sự đúng | 59/199 = **29,65%** |
| Baseline luôn đánh dấu đáp án ứng viên sai | 495/694 = **71,33%** |
| Chênh lệch judge so baseline đó | **+2,74 điểm %**, CI 95% **−1,54 đến +7,22 điểm %** |

Baseline luôn bác đáp án chỉ là đối chứng chất lượng verdict, **không** phải chính sách routing. Khoảng tin cậy của chênh lệch chứa 0; chưa có bằng chứng rõ rằng verdict Qwen3 14B đáng dùng hơn quy tắc cực đơn giản đó trên mẫu này. Chênh lệch này còn phụ thuộc tỷ lệ đáp án sai 495/694 của mẫu đã chọn.

## Khác biệt theo môn và agent

| Môn | Số case | Accuracy verdict |
|---|---:|---:|
| Biology | 42 | 78,57% |
| Business | 48 | 77,08% |
| Chemistry | 51 | 78,43% |
| Computer science | 56 | 75,00% |
| Economics | 47 | 82,98% |
| Engineering | 60 | 76,67% |
| Health | 49 | 71,43% |
| History | 42 | 66,67% |
| Law | 54 | 64,81% |
| Math | 63 | 68,25% |
| Other | 44 | 75,00% |
| Philosophy | 44 | 79,55% |
| Physics | 55 | 72,73% |
| Psychology | 39 | 71,79% |

Mỗi agent có 280 quan sát nhưng một số quan sát dùng chung cùng request judge:

| Agent được chấm | Verdict đúng / 280 | Accuracy |
|---|---:|---:|
| Qwen3 8B | 193 | 68,93% |
| Gemma2 | 188 | 67,14% |
| Llama3 8B | 214 | 76,43% |
| Qwen3 0.6B | 222 | 79,29% |

Các chênh lệch theo môn và agent là mô tả, chưa kiểm định riêng từng cặp. Judge Qwen3 14B cùng họ với hai agent Qwen, nên đây không phải đánh giá hoàn toàn độc lập về kiến trúc.

## Tính nhất quán và độ tự tin

- 234/280 câu có hơn một đáp án ứng viên. Trong đó **112/234 = 47,86%** câu khiến judge chọn `chosen_letter` khác nhau giữa các prompt ứng viên. Điều này tương thích với khả năng bị đáp án ứng viên ảnh hưởng, nhưng chưa chứng minh nhân quả vì không có lặp lại cùng prompt để đo nhiễu sinh ngẫu nhiên.
- Lựa chọn riêng của judge khớp gold ở **297/694 = 42,80%** case; mức confidence tự báo trung bình **0,9389**, và **93,8%** case có confidence ≥0,9. Prompt hiện chưa định nghĩa thật chặt confidence dành cho verdict hay lựa chọn riêng, nên đây là cảnh báo về độ tin cậy của confidence, chưa phải kiểm định hiệu chuẩn chính thức.
- Cấu trúc lỗi không đồng nhất: History, Law và Math có accuracy thấp hơn nhiều môn khác. Không được nhân các hệ số sửa lỗi theo môn trực tiếp từ cùng mẫu rồi tuyên bố cải thiện trên mẫu đó.

## Kết luận và quyết định tiếp theo

**Kết luận chắc chắn:** pipeline Modal thật hoạt động trên đủ 14 môn và cung cấp feedback có nhiễu đo được. Verdict hiện tại sai 180/694 case, gồm nhiều false positive; đưa nó vào reputation như ground truth sẽ không đáng tin.

**Thứ tự thực nghiệm tiếp theo:**

1. Hoàn tất lượt Qwen3 8B direct/thinking lớn đang resume trên Modal, rồi phân tích paired accuracy, latency, truncation và hiệu quả theo môn.
2. Dùng tập history khác với 280 câu judge này hoặc cross-fit theo câu để ước lượng ma trận lỗi/hiệu chuẩn của judge; đánh giá `raw verdict`, `noise-adjusted feedback`, `gold feedback` (oracle trần trên) và `no feedback` trong HistRepEval. Mọi hyperparameter chọn trên calibration riêng.
3. Chạy lại ECRT, FixedBorrow và SkillConditioned ở cùng ngân sách trên tập xác nhận Week 5 đã khóa 280 câu dev chưa dùng. Chỉ tính gain thực dụng khi utility/accuracy vượt baseline với CI paired có ý nghĩa và chi phí được tính đầy đủ.
4. Để kiểm tra độ nhạy theo judge, chạy judge khác họ Qwen trên Modal theo manifest mới; không trộn vào ledger này. Lặp cùng prompt trên một phần mẫu để phân biệt tính bất định của mô hình với ảnh hưởng đáp án ứng viên.

Kết quả Week 3 về ECRT so FixedBorrow vẫn là gần hòa; báo cáo này không biến nó thành phương pháp thắng. Giá trị khoa học hiện tại là mô tả có kiểm soát về độ nhiễu và độ nhạy của feedback thật, làm cơ sở cho thí nghiệm hiệu chỉnh và routing có đối chứng.
