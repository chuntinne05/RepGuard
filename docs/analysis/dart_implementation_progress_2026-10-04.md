# DART: báo cáo triển khai và kiểm chứng ngày 04/10/2026

## 1. Kết luận hiện tại

Đã triển khai và chạy các phiên bản DART chọn audit theo quyết định trên dữ liệu
thực nghiệm AppWorld chính thức. **Chưa chứng minh được DART vượt các baseline
mạnh.** Bản sửa khắc phục một điểm yếu trong thiết kế và tăng kết quả rõ rệt so
với bản đầu, nhưng baseline đơn giản sử dụng toàn bộ ngân sách nhãn vẫn có trung
bình cao hơn. Không diễn giải việc sửa được thuật toán thành việc đã có bài báo A*.

Kênh feedback đầu tiên là lời tự báo hoàn thành trong log agent. Kênh thứ hai là
model Qwen3-14B chấm log thực tế trên Modal, đang được kiểm tra theo protocol
đã khóa. Cả hai phục vụ cùng câu hỏi: **với ít nhãn kiểm chứng đáng tin, lịch sử
phản hồi không hoàn hảo có giúp chọn agent tốt hơn cách học đơn giản hay không?**

## 2. Dữ liệu nào đã thực sự dùng?

- Nguồn: [leaderboard AppWorld chính thức](https://github.com/StonyBrookNLP/appworld-leaderboard).
- Commit nguồn: `c1f56015cf7c3441ff1933f5bfbec879798d7bbe`.
- 14 agent khác scaffold/model; 168 task `test_normal`; 56 nhóm generator.
- Đủ 2.352 kết quả task–agent; cả 14 bundle được kiểm tra SHA256 và kích thước LFS.
- Code/data/evaluator của các trajectory đều là **0.1.0**. Instruction lấy từ
  data 0.1.0 tương ứng, không chấm lại trajectory cũ bằng evaluator mới.
- Outcome là `success` từ evaluator chính thức, đối chiếu số check pass/fail.
- Đây là phân tích lại những lần chạy agent đã có thật. **Không có 2.352 lần
  solver mới được chạy trong bước replay**; suy luận mới thuộc bước model chấm.
- AppWorld là [môi trường mô phỏng các ứng dụng và con người](https://github.com/StonyBrookNLP/appworld#ℹ️-about).
  Các lần thực thi agent là thật trong benchmark đó; không phải dữ liệu người
  dùng thật, cũng không phải kết quả thành công được tự tạo bằng xác suất.
- Không mở outcome `test_challenge` hoặc MMLU-Pro sealed holdout 420 câu.
- Chưa giải quyết khác biệt số task challenge: danh sách tải được có 417 ID,
  trong khi paper tham khảo nêu 380. Không tự xem hai tập là một.
- Usage/token/cost của solver lịch sử không đầy đủ: chỉ so số nhãn audit và số
  agent invocation; không claim ngang chi phí GPU hoặc USD.
- Raw log, ma trận per-task và derivatives riêng tư giữ trong `results/` đã
  gitignore; không công bố plaintext benchmark đã giải mã.

## 3. Pool có đủ cơ hội để nghiên cứu routing không?

| Chỉ số | Kết quả |
|---|---:|
| Agent tốt nhất xét hậu nghiệm | ReAct GPT-4o |
| Số task đúng của agent đó | 82/168 = 48,81% |
| Oracle chọn agent đúng cho từng task sau khi biết đáp án | 134/168 = 79,76% |
| Khoảng cách oracle với best single | 52 task |
| Cặp có ít nhất 10 rescue mỗi chiều | 45 cặp |

Gate bổ trợ giữa agent **đạt**. Tuy nhiên, oracle biết trước kết quả, còn router
chỉ thấy instruction trước khi chọn agent. Khoảng cách 52 task không có nghĩa
thuật toán có thể khai thác được cả 52. TF-IDF/kNN dùng toàn bộ nhãn lịch sử chỉ
đạt 71/168, thấp hơn global agent chọn từ train đạt 82/168: việc dự đoán specialist
từ instruction hiện vẫn khó. Hai giá trị này là diagnostic tốn full gold, không
là đối chứng ngang ngân sách audit thấp.

## 4. Thuật toán và đánh giá đã triển khai

### Chia dữ liệu và ngân sách

Chia 5 outer folds theo generator, tránh đưa các biến thể của cùng generator
vào cả train và test. Trong mỗi phần train, chia tiếp theo generator:

1. Construction: dùng 1/3 ngân sách gold để xây candidate policies và hiệu chỉnh
   kênh feedback. Không nhìn gold ngoài các vị trí được audit.
2. Selection: dùng 2/3 ngân sách để so giá trị các candidate policies.
3. Test: đóng băng lựa chọn agent rồi mới tra outcome để tính điểm.

Ngân sách 5%, 10%, 20% là tỷ lệ **các ô task–agent lịch sử** được xem nhãn gold,
không phải tỷ lệ test task được gọi solver. Có 20 seed chọn audit, 5 folds,
3 mức ngân sách: 300 tổ hợp. Mỗi seed tạo đủ 168 dự đoán out-of-fold.

Candidate bank gồm 14 policy luôn chọn một agent và 3 policy kNN từ anchor
(k=3, 10, 30). Feature chỉ từ instruction; không dùng required app/API suy ra
từ gold. Ngữ vựng và IDF không fit trên instruction test.

### Ước lượng và chọn audit

Ước lượng giá trị policy dùng proxy đã hiệu chỉnh cộng phần sửa sai:
`m + A/q * (y - m)`, với A chỉ báo được audit và q là xác suất được audit.
Đây là họ kỹ thuật ước lượng có sẵn, không claim bản thân công thức là novelty.

Chọn đúng B ô khác nhau bằng pivotal sampling; mọi ô có xác suất dương và
tổng q bằng B. Ước lượng một policy cố định có cơ sở về kỳ vọng; tối đa hóa
nhiều ước lượng nhiễu vẫn có thể chọn sai. Không nhầm hai tính chất này.

**DART đầu tiên:** ưu tiên policy trông có triển vọng theo proxy nhưng vẫn cho
mọi candidate tham gia quyết định cuối. **DARTContrast:** phân bổ theo mọi cặp
policy đủ điều kiện được chọn, tìm thiết kế giảm thành phần moment bậc hai
tồi nhất. Có sàn xác suất 20%; tối ưu heuristic 24 vòng; uniform là phương án
dự phòng nếu mục tiêu thiết kế không cải thiện.

Mục tiêu thiết kế bỏ qua covariance joint inclusion của pivotal sampling.
Chưa có định lý phương sai chính xác, tối ưu toàn cục hay bảo đảm an toàn triển
khai. Code ghi `certified=False`, không gọi bootstrap trên dev là safety certificate.

## 5. Kết quả đầy đủ với self-report

Số dưới đây là **số task đúng trung bình trên 168 task, qua 20 seed audit**.
Số lẻ không phải task có nhãn một phần. Seed audit không tạo thêm task độc lập.

| Phương pháp | Audit 5% | Audit 10% — chính | Audit 20% |
|---|---:|---:|---:|
| DART đầu tiên | 51,55 | 55,50 | 57,65 |
| **DARTContrast** | **62,00** | **67,40** | **69,55** |
| AuditOnly | 57,90 | 62,85 | 65,55 |
| RandomHistory | 58,70 | 64,40 | 67,55 |
| UncertaintyHistory | 61,70 | 65,50 | 65,85 |
| **UniformAuditGlobal** | **64,40** | **69,70** | **75,15** |
| UniformAuditKNN | 62,20 | 66,35 | 71,55 |
| AnchorOnly — dùng ít nhãn hơn | 56,80 | 60,60 | 64,80 |
| ProxyGlobal — không gold | 41,00 | 41,00 | 41,00 |
| ProxyKNN — không gold | 45,00 | 45,00 | 45,00 |
| GoldTrainSingle — full gold diagnostic | 82,00 | 82,00 | 82,00 |
| GoldTrainKNN — full gold diagnostic | 71,00 | 71,00 | 71,00 |

UniformAuditGlobal/UniformAuditKNN dùng đúng cùng tổng B nhãn, audit đều trên
toàn bộ train và dùng toàn bộ nhãn để học global mean hoặc kNN. Không phải
oracle, không được cấp full gold. Đây là đối chứng quan trọng hơn AnchorOnly.

### Chênh lệch ở ngân sách chính 10%

Đơn vị: điểm phần trăm accuracy; CI bootstrap 5.000 lần theo generator, sau khi
lấy trung bình seed trong từng task. CI exploratory, chưa điều chỉnh đa so sánh.

| DARTContrast trừ đối chứng | Chênh lệch | CI 95% |
|---|---:|---:|
| AuditOnly | +2,71 | [+0,18; +5,36] |
| RandomHistory | +1,79 | [−1,01; +4,61] |
| UncertaintyHistory | +1,13 | [−0,48; +2,89] |
| UniformAuditGlobal | −1,37 | [−4,17; +1,46] |
| UniformAuditKNN | +0,63 | [−1,85; +2,95] |

**Gate phương pháp không đạt.** Có một contrast thuận lợi với AuditOnly, nhưng
không đủ để claim thắng mọi baseline. Baseline global đơn giản có trung bình
cao nhất ở cả ba mức audit và không cần trả chi phí model chấm.

### Các lần chạy và tính toàn vẹn

- v1: 1.200 audit-policy runs; DART đầu tiên thua ba baseline chính, CI đều dưới 0.
- v2: 1.500 runs; thêm DARTContrast, giữ nguyên v1 và không ghi đè kết quả.
- v3: 2.100 runs; bổ sung hai baseline toàn ngân sách, giữ mọi dự đoán cũ.
- Đã kiểm tra tất cả dự đoán của các phương pháp chung giữa v2/v3 **giống hệt**.
- Các số này là số replay policy, không phải số inference hoặc cỡ mẫu thống kê.
- Aggregate máy đọc được: `dart_selfreport_v3_aggregate_2026-10-04.json`.

## 6. Vì sao bản đầu thua, và sửa được gì?

Ở ngân sách 10%, 83/100 lựa chọn cuối của DART v1 nằm ngoài tập candidate được
ưu tiên acquisition; ESS trung bình khoảng 43,38 so với 125,4 ở uniform audit.
Đây là dấu hiệu phù hợp với cơ chế: ít audit một phương án → trọng số nghịch
đảo lớn → giá trị ước lượng dao động mạnh → phương án nhiễu có thể thắng khi
lấy max. Chưa phải chứng minh nhân quả đầy đủ từ một thống kê quan sát.

Sửa acquisition để bao phủ mọi candidate cải thiện 11,9 task trung bình tại
10%. Tuy nhiên, so với cách học trực tiếp bằng tất cả nhãn, DART còn trả giá
cho chia dữ liệu construction/selection và chọn trong candidate bank hạn chế.
Feedback self-report có thể không đủ thông tin để bù chi phí đó. Đây là các
giả thuyết cần tách bằng ablation; chưa được coi là kết luận đã chứng minh.

## 7. Real judge trên Modal và tự động hóa

Protocol `dart_real_judge_protocol_2026-10-04.md` khóa trước inference: Qwen3-14B,
digest cố định, no-thinking, temperature 0; đọc instruction và environment I/O,
không đọc outcome chính thức hoặc agent identity. Log dài dùng đầu 2.000 ký tự
và cuối 10.000, đánh dấu thiếu đoạn; ghi hash và coverage để phân tích hạn chế.

Pilot 168 task–agent (12/agent) chọn bằng hash ID trước khi biết kết quả judge.
Gate: valid ít nhất 95%, balanced accuracy ít nhất 0,60 và cận dưới CI theo
generator trên 0,50. Nếu fail, dừng mở rộng. Nếu pass, hoàn thành manifest
2.352 ô rồi tự chạy replay ngang ngân sách theo protocol riêng đã khóa.

Phản hồi invalid không bị chạy lại để chọn câu đẹp; được giữ làm abstention.
Collector tách khỏi analyzer, append-only ledger, khóa chống chạy trùng,
kiểm tra digest và hash prompt khi resume. Controller có tối đa ba lần thử
collector mỗi stage; lỗi không thể phục hồi phải hiện `pipeline_failed`.

Các file trạng thái thực tế:

- `results/dart_modal_judge_v1/status.json`: collector, số record và thời gian.
- `results/dart_modal_judge_v1/judgments_private.jsonl`: bằng chứng inference.
- `results/dart_modal_judge_v1/pilot_quality.json`: kết quả gate khi đã đủ pilot.
- `results/dart_modal_judge_v1/pipeline_status.json`: controller và bước hiện tại.
- `results/dart_audit_judge_v1/analysis.json`: chỉ có sau full judge và replay.

Không gọi pipeline đang tiến triển chỉ vì process còn tồn tại; phải đối chiếu
timestamp và số record. Caffeinate chỉ hạn chế idle sleep; đóng máy/tắt mạng
có thể ngắt controller local, khi đó resume từ ledger. Không claim chống mọi
trường hợp mất điện hay tự gửi báo cáo định kỳ nếu chưa có scheduler thực tế.

## 8. Điều kiện để hướng này đủ mạnh cho bài báo

Hiện đã có hạ tầng thực nghiệm và một lỗi thiết kế được phát hiện/sửa, chưa có
phương pháp superior. Muốn viết bài phương pháp mạnh, cần đồng thời:

1. Thắng baseline audit trực tiếp và random audit ngang chi phí ở mức hiệu quả
   thực tiễn; tính cả phí judge, không chỉ đếm nhãn gold.
2. Giải thích bằng ablation vì sao history, calibration và acquisition tạo gain.
3. So sánh faithful với các công trình gần nhất trong kế hoạch nghiên cứu;
   chưa gọi các baseline nhỏ hiện tại là bản tái lập đầy đủ CABS/ContextualRouter.
4. Có phân tích ước lượng/selection hợp lệ cho đúng sampling design; hoặc thu
   hẹp claim lý thuyết rõ ràng thay vì gắn nhãn an toàn không chứng minh.
5. Kiểm tra feedback sai có mục tiêu, shift và replication độc lập với phương
   pháp, ngân sách, endpoint được khóa trước khi mở dữ liệu xác nhận.
6. Báo mọi nhánh đã thử; không biến việc lặp lại trên cùng public dev thành
   bằng chứng độc lập. Không dùng sealed holdout để tìm cấu hình thắng.

Nếu real judge không giúp vượt baseline đơn giản, kết luận hợp lý là sửa câu
hỏi hoặc candidate learner dựa trên chẩn đoán, hoặc tập trung đóng góp đo lường
HistRepEval. Không tự động bỏ DART, nhưng cũng không tiếp tục thêm độ phức tạp
chỉ để tìm một ô kết quả dương. Không thể bảo đảm hội nghị A/A* nhận bài.

## 9. Mốc mã nguồn

| Commit | Nội dung |
|---|---|
| `e7e741e` | Khóa pool trước outcome |
| `8186cb3` | Triển khai audit/policy selector và protocol đầu |
| `b613516` | Bổ sung DARTContrast sau thất bại v1 |
| `ef50d9d` | Khóa real-judge protocol và runner trước inference |
| `04b0d22` | Thêm baseline dùng toàn ngân sách trước v3 |

Kết quả test và snapshot inference cuối lượt được bổ sung sau khi kiểm tra
thực tế; phần kết luận định lượng ở trên là kết quả self-report đã hoàn tất.
