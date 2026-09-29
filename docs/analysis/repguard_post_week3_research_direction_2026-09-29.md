# RepGuard sau Week 3: hướng nghiên cứu có kiểm chứng

Ngày rà soát: 2026-09-29. Tài liệu này là **đề xuất và các giả thuyết cần thử**, không phải kết quả của một thí nghiệm mới. Bằng chứng thực nghiệm hiện có nằm trong `repguard_week3_real_report.md`.

## 1. Kết luận từ dữ liệu thật

Week 3 đã chạy xong: 18.064 câu trả lời thật của bốn model trên history/dev/toàn bộ test MMLU-Pro 14 môn. Trên 2.416 câu test, Qwen3 8B đúng 47,76%; routing chọn model theo môn từ history đúng 47,19%; oracle chọn model tốt nhất *theo môn bằng nhãn test* là 48,97%; oracle chọn model đúng *theo từng câu bằng nhãn test* là 68,34%. Hai oracle chỉ là trần chẩn đoán, không phải chính sách triển khai. Chỉ có một specialist theo tiêu chuẩn đã đặt trước: Qwen3 8B ở physics.

MMLU-Pro ở thiết lập này là **bốn model trả lời độc lập rồi được tổng hợp**, chưa phải agent tương tác trong môi trường nhiều bước. Nếu tiêu đề/bài báo muốn nói về multi-agent systems nói chung, cần ít nhất một môi trường agent thật để xác nhận ngoài kiểu ensemble nhiều lựa chọn.

Ở điều kiện chính đã đăng ký (related history + 25% feedback noise), ECRT so FixedBorrow tăng team accuracy 0,02 điểm phần trăm, CI 95% [-0,04; +0,10]; chưa có tác dụng thực dụng. ECRT có lợi ích Brier rõ dưới một số nhiễu mạnh, nhưng chưa chuyển thành outcome và còn yếu trước pilot poisoning có mục tiêu. **Không tuyên bố ECRT đã thắng.**

Một điều kiện phải kiểm tra là giao thức Week 3 dùng zero-shot, trả lời JSON trực tiếp, `think=false`. Bài MMLU-Pro gốc báo cáo CoT cải thiện so với trả lời trực tiếp; Qwen3 có thinking mode. Đây là lý do chạy pilot đối chứng prompt, **không phải bằng chứng rằng prompt gây ra thất bại**.

## 2. Khoảng trống có thể bảo vệ trước phản biện

| Bài gốc | Đã giải quyết gì | Hệ quả cho RepGuard |
|---|---|---|
| [Ebrahimi et al., IJCNLP-AACL 2025](https://aclanthology.org/2025.ijcnlp-long.90/) | Độ tin cậy lịch sử để tổng hợp câu trả lời | Reputation từ lịch sử không mới |
| [Xia & Wang 2026](https://arxiv.org/abs/2606.14200) | Trust theo skill; điều kiện dị biệt năng lực; mượn bằng chứng và laundering | Không tuyên bố mới về conditional trust, transfer hay cross-skill attack |
| [RouteLLM](https://arxiv.org/abs/2406.18665), [RouterBench](https://arxiv.org/abs/2403.12031) | Routing theo câu hỏi và benchmark routing | Query-level router đơn thuần không đủ novelty |
| [RAPS 2026](https://arxiv.org/abs/2602.08009), [Norm Enforcement 2026](https://arxiv.org/abs/2607.09766) | Watchdog/reputation Bayesian và độ tin cậy agent theo thời gian | Không tuyên bố mới về watchdog hay Beta reputation |
| [AgentAuditor 2026](https://arxiv.org/abs/2602.09341), [When to Solve, When to Verify 2025](https://arxiv.org/abs/2504.01005) | Kiểm chứng khi bất đồng, đánh đổi giữa thêm lời giải và verifier | Selective verification nói chung không mới; phải so với thêm solver cùng chi phí |
| [Proactive Routing with Safety Guarantees 2026](https://arxiv.org/abs/2603.14623) | Routing có giới hạn rủi ro qua hiệu chuẩn holdout | Không hứa bảo đảm phân phối tự do nếu thiếu điều kiện thống kê tương ứng |

**Giả thuyết đóng góp hẹp:** nghiên cứu *giá trị ra quyết định* của reputation học từ phản hồi lịch sử vừa sai lệch vừa lệch kỹ năng, và dùng một ngân sách audit hữu hạn để quyết định bằng chứng nào được phép đổi lựa chọn agent/đáp án. Phải chứng minh phần kết hợp này tạo ra outcome mới so với từng thành phần và baseline đơn giản. Tên làm việc: **Decision-Aware Audited Reputation Transfer (DART)**; chỉ đổi tên bài sau khi có kết quả.

Một ràng buộc cơ bản: nếu chỉ thấy feedback `tốt/xấu` từ một nguồn có thể gian lận, nhưng không có nhãn kiểm tra đáng tin hoặc giả định độc lập bổ sung, ta không phân biệt được “agent giỏi được đánh giá đúng” với “agent kém được đánh giá sai”. Đây là vấn đề nhận dạng, không thể sửa bằng cách tăng số phiếu hay đổi công thức Beta; lý thuyết noisy-label cũng nêu rõ cần điều kiện bổ sung để nhận dạng nhãn sạch ([Nguyen et al. 2023](https://arxiv.org/abs/2301.01405)). Vì vậy mẫu audit gold là một **giả định tài nguyên được công khai**, phải đo số lượng và chi phí của nó.

Điểm mới tiềm năng không phải đặt thêm trọng số vào phiếu bầu. Hệ thống cần tách ba biến: (1) năng lực agent trên câu hiện tại, (2) độ đáng tin của nguồn feedback cho từng agent/skill, (3) xác suất từng *đáp án* đúng khi các agent có thể cùng sai. Từ đó chọn một trong ba hành động: dùng baseline an toàn, đổi route/đáp án, hoặc trả chi phí để kiểm tra thêm. Một score Brier tốt nhưng không đổi hành động sẽ được coi là cải thiện dự đoán, **không** được coi là cải thiện team.

### Thiết kế phương pháp tối thiểu để thử

1. Trích đặc trưng câu trước khi xem đáp án đúng: skill phụ, loại suy luận, độ dài, cấu trúc đáp án; thêm mẫu vote và bất đồng sau khi agent trả lời. Không dùng nhãn test làm feature, chọn taxonomy hoặc encoder bằng train/dev.
2. Ước lượng xác suất năng lực theo agent–skill bằng history; hiệu chỉnh kênh feedback bằng một **mẫu audit có gold độc lập, chọn ngẫu nhiên/đủ bao phủ từng agent–skill và ghi chi phí**. Dùng partial pooling và khoảng bất định; feedback từ riêng một agent có thể sai lệch khác phần còn lại. Không thể suy ra chất lượng feedback có chủ đích từ dev honest nếu không có audit liên quan đến agent đó. So random audit với audit ưu tiên những quyết định có khả năng bị đảo, giữ một phần audit ngẫu nhiên để tránh blind spot.
3. Gộp xác suất ở **cấp đáp án**, có đặc trưng đồng thuận và tương quan lỗi. So sánh với một model đơn mạnh nhất được chọn từ history/dev. Chỉ thay đáp án khi estimated gain vượt ngưỡng đã cố định trên dev; nếu không thì fallback. Đây là một guard thực nghiệm, chưa phải bảo đảm toán học.
4. Khi lựa chọn nhạy với bất định của feedback hoặc vote bị chia, thử một hành động kiểm chứng độc lập. So sánh ở **cùng token, latency, số lời gọi và ngân sách audit** với việc gọi thêm solver, self-consistency, FixedBorrow, conditional trust, router theo câu, majority/weighted vote, verifier luôn bật, và verifier theo disagreement. Nếu verifier không tăng utility trên đường Pareto, bỏ nhánh verifier.

## 3. Chuỗi thí nghiệm và cổng dừng

### Gate 0: Sửa giao thức năng lực, chưa phát triển thuật toán

- Dùng các câu **chưa sử dụng** trong train/dev MMLU-Pro cho pilot cân bằng 14 môn: cùng câu, cùng model digest, so direct-answer với cấu hình reasoning/CoT phù hợp từng model; đo accuracy, năng lực bổ sung từng câu, latency và token. Không dùng 2.416 câu test Week 3 để chọn prompt.
- Đăng ký trước tối đa vài cấu hình agent đa dạng thực sự (model, scaffold, tool stack), có đối chứng bằng chi phí. Chọn pool trên train; kiểm tra specialist trên dev độc lập. Cần ít nhất hai agent khác nhau thắng rõ ở các skill khác nhau **trước khi** làm claim conditional reputation. Nếu gate này trượt, không tiếp tục paper phương pháp ECRT/DART trong pool đó.
- Các ngưỡng cần khóa trước pilot: lợi ích routing so model đơn trên dev có ý nghĩa thực dụng (đề xuất ≥2 điểm phần trăm ở cùng ngân sách); CI ghép cặp và lựa chọn specialist phải được báo cáo, không chọn pool từ test. Đây chỉ là **gate quyết định chi compute**, chưa phải kết luận khoa học.

### Gate 1: Có thể dự đoán *ai đúng ở câu này* hay không?

- Dùng lịch sử và dev để huấn luyện các baseline nhẹ cho question-aware routing và answer-aware aggregation. Báo cáo test mới, với CI ghép cặp và breakdown theo skill. Con số any-of-four 68,34% Week 3 không được dùng làm dự báo hiệu quả: nó cần nhãn đúng để biết ai là người đúng.
- Nếu router/aggregator không vượt model đơn mạnh nhất và FixedBorrow đủ rõ ở cùng chi phí, việc tinh chỉnh reputation sẽ khó sinh đóng góp outcome. Chuyển sang bài characterization có tái lập và benchmark thứ hai, hoặc dừng đề tài phương pháp.

### Gate 2: Phản hồi không tin cậy có làm thay đổi quyết định không?

- Chỉ sau Gate 1, chạy factorial quality-of-feedback × skill mismatch. Tách corruption *đồng đều* khỏi poisoning *theo agent/skill*. Có nhiều attacker, nhiều lịch sử, nhiều seed, ngân sách và khả năng tấn công; bao gồm câu trả lời độc hại do model thật tạo, không chỉ ép sai bằng nhãn gold.
- Ít nhất một nguồn feedback phải là **đánh giá thật** từ một LLM judge/kiểm thử công cụ được chạy và lưu log, có lỗi đo được trên nhãn ẩn. Các phép lật nhãn theo seed vẫn có ích để phân tích nhân quả, nhưng không đủ một mình để hỗ trợ claim triển khai.
- Primary endpoint đăng ký trước: **risk-adjusted utility hoặc team accuracy tại cùng ngân sách thật** so FixedBorrow, conditional trust, router/ensemble mạnh nhất và model đơn. Secondary: Brier, calibration, regret, tỷ lệ audit, chi phí. CI phải ghép cặp theo task, phân tầng/cluster theo nhóm phù hợp; điều chỉnh các so sánh chính nếu thử nhiều phương án.
- Audit gold phải tách riêng khỏi train selection và final test. Gold chỉ dùng để đánh giá/audit theo ngân sách được cấp; không bao giờ lộ vào prompt inference cho câu test.

### Gate 3: Xác nhận độc lập và khả năng ra bài

- Khóa mã, prompt, hyperparameter, tập baseline, attack policy và metric rồi chạy trên benchmark/pool thứ hai; AppWorld là một lựa chọn cho external validity, nhưng [Xia & Wang](https://arxiv.org/abs/2606.14200) đã dùng AppWorld nên benchmark đó không tự tạo novelty. Tính lại chi phí thực và phân tích failure cases.
- Claim mạnh chỉ khi phương pháp thắng baseline mạnh ở metric chính trên tập mới, không làm hại clean condition đáng kể, và tốt hơn hoặc ít nhất không tệ hơn dưới targeted poisoning theo tiêu chí đã đăng ký. Nếu chỉ cải thiện Brier, viết bài về calibration/decision limits; nếu ngay cả kết quả đó không lặp lại, kết luận trung thực và đổi đề tài.

## 4. Ưu tiên thực tế

1. **Ngay bây giờ:** pilot prompt/reasoning và ma trận năng lực trên dữ liệu chưa dùng; không tốn compute cho toàn bộ tập trước khi thấy hai specialist.
2. **Sau đó:** benchmark mạnh cho query router/answer aggregator trên dev, kiểm tra xem có thể rút ngắn khoảng cách giữa 47,76% baseline và 68,34% oracle trên từng câu hay không. Oracle này chỉ mô tả tiềm năng, không phải target hứa hẹn.
3. **Chỉ nếu hai bước trên qua gate:** phát triển audit/reputation decision rule và chạy adversarial study có budget; xác nhận trên benchmark thứ hai.

Không có cách nào bảo đảm bài mạnh, cải thiện accuracy, hay được nhận đăng. Có thể bảo đảm **quy trình ra quyết định trung thực và ít lãng phí**: đăng ký gate, dùng holdout mới, so baseline công bằng, dừng khi giả thuyết thất bại, và không dùng khoảng cách oracle làm thành tích phương pháp.
