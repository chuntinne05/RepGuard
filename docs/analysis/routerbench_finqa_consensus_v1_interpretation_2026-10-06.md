# FinQA consensus v1: kết quả, giới hạn và quyết định nghiên cứu

## Kết luận có thể báo cáo

Run `5f793e80665eb1d900b97026` kết thúc trên Modal lúc **17:00:46 UTC,
06/10/2026**. Worker CPU đã xác minh SHA256 archive, đọc 960 `prediction`
trên **48 câu FinQA development mới ×20 model đã chạy trước**, lưu proxy không
có gold, rồi mới đọc đúng 960 binary score. Không có solver call hoặc judge
call mới. Local đã tải sáu artifact, xác minh checksum, đối chiếu lựa chọn
câu/record với parent và tính lại toàn bộ analysis; kết quả khớp cloud.

**Operational PASS; expansion screen FAIL.** Có **892/960 =92,92%** parsed
prediction không rỗng, cao hơn ngưỡng 90%. Tỷ số phương sai của chênh lệch
residual giữa 190 cặp model là **0,923388**; CI95 question bootstrap
**[0,848729; 1,000613]**. Protocol yêu cầu ratio **≤0,90** và CI upper **<1**.
Cả hai điều kiện không đạt. Vì vậy không được gọi consensus v1 là phương pháp
đã được chứng minh, hoặc mở replay gold thưa theo nhánh PASS của protocol.

| Chỉ số cố định trước run | Kết quả |
|---|---:|
| Raw exact-agreement Brier | 0,468891 |
| Cross-fit agreement Brier | 0,204689 |
| Cross-fit gold-only Brier | 0,219816 |
| Raw proxy pair ratio | 0,945479 |
| Cross-fit pair ratio | 0,923388 |
| CI95 của cross-fit pair ratio | [0,848729; 1,000613] |

Gain Brier của cross-fit agreement so với gold-only là **0,015127**, nhưng
cross-fit ở đây học từ *toàn bộ nhãn của 36 câu huấn luyện mỗi fold*, không
phải một phép đo hiệu quả với gold thưa. Bootstrap giữ nguyên fitted
predictions, không refit. Đây là development screen sau khi đã thấy aggregate
gold của pool 200 câu headroom; chưa phải xác nhận độc lập. Tất cả số ở bảng
là kết quả trong [protocol đã khóa](routerbench_finqa_consensus_v1_protocol_2026-10-06.md).

## Tín hiệu thực có, nhưng chưa đủ mạnh

Judge v1 trên 48 câu development *khác* có pair ratio **1,045407**, còn
consensus v1 có **0,923388**. Không được trừ hai tỷ số để tạo một hiệu ứng
paired: hai tập câu khác nhau, không cùng gold. Trong consensus run, hệ số
tương quan hậu kiểm giữa score proxy và đúng/sai sau khi trừ trung bình mỗi
câu là **+0,3551**; của judge v1 trên tập trước là **+0,0427**. Raw agreement
có thông tin về sự khác biệt giữa model, nhưng độ biến thiên/đồng lỗi vẫn quá
lớn để vượt gate.

Đẳng thức phương sai trên 190 cặp trong run này cho cross-fit:

`VarSum(Ydiff - Pdiff) = 50,952571 + 5,638127 - 2 × 4,770843`.

Tỷ số đúng là **0,923388**. Covariance dương cho thấy predictor đi đúng
chiều nhiều hơn judge cũ; tuy nhiên sau khi trừ phương sai của predictor,
mức giảm chỉ khoảng **7,66%**, kém mốc 10% đã khóa. Gold-only cross-fit có
ratio **1,052925**, nên tín hiệu proxy có giá trị trong phép đo này, nhưng
không đủ để chứng minh lợi ích quyết định/chọn model.

Phân tích hậu kiểm theo mức đồng thuận cho thấy lý do không thể mặc định
"nhiều model đồng ý thì đúng":

| Nhóm cell | Đúng/tổng | Tỷ lệ đúng |
|---|---:|---:|
| Không có parsed prediction | 1/68 | 1,47% |
| Prediction không ai khác khớp | 186/371 | 50,13% |
| Có 1–3 model khác khớp | 208/274 | 75,91% |
| Có 4–9 model khác khớp | 183/214 | 85,51% |
| Có ≥10 model khác khớp | 11/33 | **33,33%** |

Trong nhóm cuối, **22 cell sai tập trung ở hai câu**. Một câu không có model
nào trong 20 model đúng; câu còn lại có năm model đúng nhưng nhóm 11 model
đồng thuận đều sai. Đây là bằng chứng mô tả về lỗi có tương quan, không phải
ước lượng ổn định cho nhóm rất nhỏ. Bỏ hai câu đó *sau khi xem gold* cho ratio
**0,901855**, vẫn trên mốc 0,90. Vì vậy lỗi đồng thuận cao là một nguyên
nhân, **không phải toàn bộ giải thích**; tuyệt đối không dùng phép loại này
làm candidate hay báo PASS.

Trên 48 câu này, model tốt nhất khi biết gold là **41/48**, oracle biết chọn
theo từng câu là **46/48**: trần rescue chỉ **5/48 =10,42 điểm phần trăm**.
Raw agreement trung bình chọn đúng model có 41/48 là Qwen3-8B trên chính
subset này, nhưng đó là quan sát hậu kiểm với output của **cả 20 model** đã
có sẵn. Không chứng minh chọn model với ít gold, cũng không chứng minh router
theo từng task. Trong 200 câu headroom FinQA trước đó, best fixed là 74,0%
và oracle 88,5%; không được thay hai số đó bằng 41/48 và 46/48.

## Quyết định và hướng tiếp theo

1. **Dừng consensus v1 đúng gate.** Không đổi normalization, ngưỡng, fold,
   model subset hoặc bỏ hai câu sai để biến run thành PASS. Giữ riêng bản
   [kết quả gốc](routerbench_finqa_consensus_v1_assessment_2026-10-06.md)
   và [chẩn đoán hậu kiểm](routerbench_finqa_consensus_v1_diagnostics_2026-10-06.json).
2. Hướng phương pháp kế tiếp phải nhắm thẳng vào **lỗi tương quan giữa model
   và pairwise decision**. Một giả thuyết đáng kiểm tra là dùng kiểm chứng
   số học độc lập trên các câu có nhiều đáp án giống nhau, cộng với audit
   gold cho những cặp model còn tranh chấp. Đây mới là giả thuyết thiết kế;
   chưa có bằng chứng nó thắng baseline. Cần định nghĩa verifier không dùng
   đáp án/gold ẩn, một scoring rule cố định, chi phí của nó và một development
   gate trên câu *ngoài* pool 200 đã mở aggregate trước khi chạy.
3. Chỉ sau khi verifier mới có pair signal đủ mạnh mới chạy phép so sánh
   **cùng ngân sách nhãn**: gold-only, chọn mẫu paired, proxy thô, hiệu chỉnh
   residual, và acquisition có kiểm soát; đánh giá regret/accuracy của model
   được chọn trên câu held-out. Tính toàn bộ chi phí tạo 20 output lịch sử,
   verifier, nhãn gold và inference. Việc có Brier thấp hơn không thay thế
   outcome quyết định này.
4. Tách mục tiêu sản phẩm/bài báo: dữ liệu hiện tại hỗ trợ nghiên cứu **chọn
   model toàn cục từ lịch sử**, chưa hỗ trợ claim DART là router nhìn prompt
   mới mà không chạy 20 model. Nếu mục tiêu là DART theo từng task, cần prompt
   features chỉ từ thông tin có trước quyết định và test trên task chưa thấy;
   mọi solver output của task evaluation phải bị che khi router chọn model.
5. Giữ một tập FinQA chưa đọc outcome cho **một lần đánh giá cuối** của version
   đã khóa, thay vì lặp nhiều lần cho đến khi xuất hiện kết quả đẹp. Một bài
   báo mạnh cần thêm cải thiện decision/cost so với baseline cùng ngân sách,
   ablation, sai số theo câu/nhóm, và ít nhất một domain/benchmark thứ hai.
   Không có phép đo nào hiện tại bảo đảm DART vượt phương pháp khác hoặc được
   nhận ở hội nghị A*.

Kết quả có ý nghĩa thực tiễn ngay bây giờ là một cảnh báo đo lường: judge LLM
có thể cải thiện Brier chung nhưng làm hỏng tín hiệu chọn model, còn đồng
thuận output khôi phục một phần tín hiệu nhưng sụp ở các lỗi có tương quan.
Điều này ủng hộ việc dùng **pairwise contrast và matched cost** làm tiêu chí
phát triển, không chỉ accuracy của feedback. Đó là một phát hiện development,
không phải kết luận cuối của paper.
