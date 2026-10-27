# Neural DART P0: kết quả thực nghiệm và quyết định tiếp theo

## 1. Kết luận dễ hiểu

Đã implement, deploy và chạy thật một encoder Transformer frozen cùng ba neural
head nhỏ trên Modal. P0 hoàn tất đủ 5/5 outer folds lúc **11:34:31 ngày
05/10/2026, UTC+7**. Không có lỗi pipeline. Trạng thái cuối: `stopped_p0_gate`.

Mô hình được chọn bằng inner CV đạt **82/168**, bằng Global baseline. Vì chưa
có bằng chứng tốt hơn baseline, gate không đạt và **P1 chưa được chạy**. Đây là
đúng quyết định đã khóa trước khi có kết quả, không phải Codex dừng hoặc laptop
sleep làm gián đoạn job.

Kết luận được hỗ trợ: cấu hình MiniLM + PCA16 + ba head + masked BCE đã thử
**chưa tạo ra lợi ích routing**. Không được mở rộng thành “neural network không
dùng được”, “mọi phương pháp DART đều thất bại” hoặc “không thể ra bài báo”.

## 2. Thực sự đã chạy gì?

| Thành phần | Thực thi |
|---|---|
| Dữ liệu | Public AppWorld 0.1.0 normal, 168 task, 56 generator, 14 agent |
| Nhãn | 2.352 kết quả task–agent thật đã có từ official trajectories |
| Encoder | all-MiniLM-L6-v2 frozen, revision SHA cố định |
| Embedding | 168 × 384; instruction dài nhất 114 token; đủ 168 chunks |
| Features | PCA tối đa 16 chiều, fit riêng trong từng train partition |
| Models | Linear, rank-2 factorization, MLP tanh 8 hidden units |
| Fitting | Adam lr .02, 300 epochs; L2 .01 hoặc .1; masked BCE |
| Selection | Grouped inner 3-fold CV, chọn theo routing utility |
| Final fit | Ensemble probabilities của 3 initialization seeds |
| Outer evaluation | 5 folds, không trộn generator giữa train và test |
| Số fit P0 | 5 × (18 inner fits + 9 final fits) = 135 |
| Bootstrap | 5.000 lượt theo generator, seed 1404 |

Đây là huấn luyện và suy luận neural thật, sau đó replay lựa chọn agent trên
outcome matrix thật. Không chạy lại solver để sinh 2.352 lời giải mới. Không có
nhãn mô phỏng trong kết quả khoa học. Các bài synthetic chỉ kiểm tra code.

P0 dùng toàn bộ nhãn của outer train: lần lượt 1.806, 2.016, 1.974, 1.890,
1.722 nhãn cho folds 0–4. **Không so sánh 82/168 này với 69,70/168 của control
10% rồi tuyên bố thắng**: lượng nhãn khác nhau. Baseline công bằng ở P0 là
Global cùng sử dụng toàn bộ nhãn train, cũng đạt 82/168.

## 3. Kết quả đầy đủ

| Phương pháp | Thành công /168 | Accuracy | Đổi agent so với Global | Rescue | Harm | Chênh lệch điểm % [CI 95%] |
|---|---:|---:|---:|---:|---:|---|
| Global | 82 | 48,81% | 0 | 0 | 0 | Mốc so sánh |
| Linear | 81 | 48,21% | 5 | 0 | 1 | −0,60 [−1,79; 0,00] |
| Low-rank | 81 | 48,21% | 5 | 0 | 1 | −0,60 [−1,79; 0,00] |
| MLP | 82 | 48,81% | 0 | 0 | 0 | 0,00 [0,00; 0,00] |
| Selected bằng inner CV | 82 | 48,81% | 0 | 0 | 0 | 0,00 [0,00; 0,00] |

Rescue = Global sai, router đúng; harm = Global đúng, router sai. Các lần đổi
agent còn lại không thay đổi outcome. CI [0,0] xuất hiện do hai dãy kết quả trên
mẫu này giống hệt nhau; không phải chứng nhận hai chính sách luôn bằng nhau trên
mọi dữ liệu tương lai. CI là exploratory, không điều chỉnh cho cả lịch sử nghiên
cứu nhiều phương pháp trên cùng public normal.

Global chọn `react_gpt4o` ở cả 168 task. MLP và Selected cũng chọn đúng agent đó
ở toàn bộ 168 task. Linear chuyển 3 task sang `plan_exec_gpt4o`, 2 task sang
`ipfuncall_gpt4turbo`; low-rank chuyển 5 task sang `plan_exec_gpt4o`. **Không có
lần chuyển nào cứu được một task mà Global làm sai.**

### Inner selection

| Outer fold | Test tasks | Candidate chọn bằng inner CV |
|---|---:|---|
| 0 | 39 | MLP |
| 1 | 24 | MLP |
| 2 | 27 | Global |
| 3 | 33 | Global |
| 4 | 45 | Global |

Ở fold 0, inner MLP đạt 42,64% so với Global 40,31%; ở fold 1 là 43,75% so với
43,06%. Tuy nhiên, khi refit và áp dụng sang outer test, MLP chọn đúng các agent
như Global. Lợi ích nhỏ trong inner validation không tạo ra cải thiện outer
test. Ba folds còn lại chọn Global theo tiêu chí và thứ tự xử lý tie đã khóa.

## 4. Phân tích nguyên nhân: điều đã biết và điều chưa biết

### Quan sát trực tiếp

1. **Mạng có khả năng học và code đã thực sự train.** Cả ba head đạt 100% trên
   synthetic rescue control, giữ đúng agent trong constant control và cho kết
   quả giống hệt khi lặp lại cùng seed. Điều này loại trừ một số lỗi huấn luyện
   cơ bản; không chứng minh cấu hình tối ưu cho AppWorld.
2. **Chính sách đầu ra gần như co về agent mạnh toàn cục.** Đây là nguyên nhân
   trực tiếp của việc không có gain: Selected không đổi quyết định nào so với
   Global; hai head có đổi thì không có rescue và có một harm.
3. **Thêm semantic embedding chưa giải quyết được việc dự báo lợi thế tương đối.**
   Mô hình có thể phân biệt chủ đề instruction nhưng điều ta cần là biết agent B
   sẽ cứu được lúc nào khi agent A thất bại. Hai khả năng này khác nhau.

### Các giả thuyết cần kiểm tra riêng, chưa phải nguyên nhân đã được chứng minh

- Dữ liệu chỉ có 56 generator; tín hiệu task–agent có thể yếu hoặc không chuyển
  tốt sang generator mới.
- PCA16 có thể bỏ một phần tín hiệu hữu ích; không được kết luận embedding gốc
  384 chiều hay encoder khác cũng chắc chắn thất bại.
- BCE + L2 có thể ưu tiên xác suất thành công trung bình và thu nhỏ interaction;
  mục tiêu này chưa trực tiếp tối ưu signed rescue so với agent mốc.
- Instruction đơn thuần có thể thiếu thông tin về trạng thái môi trường, yêu cầu
  API hoặc dạng lỗi thực thi quyết định agent nào thắng.

Muốn xác nhận từng giả thuyết phải có ablation riêng. Không thể chỉ nhìn bảng
accuracy rồi khẳng định chính xác nguyên nhân nằm ở regularization hay encoder.
P0 thất bại cũng không phải định lý rằng mọi learner dùng ít nhãn hơn đều thua;
đây là tiêu chí điều phối ngân sách đã chọn cho họ mô hình này.

## 5. Hạ tầng đã hoàn thành và kiểm chứng

- Deployed app `repguard-neural-p0p1-v1`, `.spawn()` cloud invocation độc lập.
- Run ID `32fc82877693697cb45f7d49`; call `fc-01M45584KJPXN09X5RV5863V80`.
- Commit trước kết quả: `9d1f79b`; protocol không sửa sau khi thấy outcome.
- Đã quan sát checkpoint từ 1/5 → 2/5 → 3/5 → 4/5 → 5/5 sau khi submit process
  local đã thoát. Codex hoặc laptop không giữ vòng đời worker.
- Volume lưu input identity, embedding, environment, từng fold và final analysis.
- 6 test cục bộ đạt; 1 test torch local skip vì laptop không cài torch. Kiểm tra
  torch tương ứng chạy thật và đạt trên Modal cho cả ba head.
- Integration test gây lỗi giữa chừng xác nhận resume bỏ qua case đã commit,
  không chạy lại terminal gate. Model trong test này được stub, không dùng các
  giá trị đó như kết quả thực nghiệm.
- Đã đối chiếu đủ 300 audit cases với control cũ: agent choices và success khớp.
- Đã tải 11 artifacts cloud, kiểm tra source/input identity và tính lại toàn bộ
  P0 summaries/CI từ action traces; kết quả khớp chính xác.

Phiên bản thực tế: Python 3.11.12, NumPy 1.26.4, torch 2.5.1+cpu,
transformers 4.48.3. Tài liệu vận hành và lệnh status/fetch ở
[cloud operations](dart_neural_cloud_operations_2026-10-05.md).

## 6. Hướng tiếp theo hợp lý

**Không chạy 300 case P1 của cấu hình hiện tại chỉ để kéo dài thực nghiệm.**
P1 được implement sẵn và sẽ tự kích hoạt nếu P0 đạt; lần này điều kiện không đạt.

Bước nghiên cứu kế tiếp nên là protocol chẩn đoán mới có phạm vi nhỏ:

1. **Học trực tiếp lợi thế so với anchor**: target `Y_a − Y_anchor`, tách rescue
   và harm; giữ cùng folds, full-label diagnostic trước. So với direct-BCE và
   Global, tính net rescue ngoài mẫu. Đây là giả thuyết mới, chưa được test ở P0.
2. **Kiểm tra đúng nút thắt biểu diễn** bằng một vài ablation khóa trước: giữ
   embedding gốc với ridge, hoặc thêm đặc trưng yêu cầu API có sẵn trước khi chạy
   task. Không lấy log kết quả test hay agent được oracle chọn làm input router.
3. **Kiểm tra complementarity có cấu trúc hay chỉ là outcome stochastic** bằng
   phân tích theo generator và, trên một tập riêng, repeated solver executions.
   Gap oracle 134 so với Global 82 không tự chứng minh có thể học được routing.
4. Chỉ sau khi có gain ngoài mẫu mới đầu tư vào learned feedback correction,
   acquisition của cặp agent, rồi kiểm tra ngân sách 5/10/20% và benchmark độc lập.

Các bước trên là đề xuất cho lần review tiếp theo, **chưa triển khai hoặc chạy**.
Không mở challenge/sealed holdout để chọn thiết kế. Không dùng vòng lặp chỉnh
mô hình theo outer test rồi gọi lại kết quả là xác nhận độc lập.

HistRepEval vẫn có thể chứa chẩn đoán, protocol và kết quả âm có giá trị. DART
vẫn là ứng viên phương pháp cần bằng chứng mới. P0 này chưa đủ để tuyên bố
đóng góp phương pháp vượt trội hoặc khả năng chắc chắn được nhận tại hội nghị A/A*.

## 7. Artifacts

- [Protocol khóa trước](dart_neural_p0_p1_protocol_2026-10-05.md).
- [Kết quả JSON tổng hợp, inner scores và cấu hình](dart_neural_p0_results_2026-10-05.json).
- [Hướng dẫn cloud, retry và checkpoint](dart_neural_cloud_operations_2026-10-05.md).
- Raw traces: `results/dart_neural_v1/cloud/`, không commit Git.
