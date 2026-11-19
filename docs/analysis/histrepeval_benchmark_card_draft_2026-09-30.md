# HistRepEval — benchmark card bản nháp v0.1

**Trạng thái:** bản thiết kế/release checklist, chưa công bố như benchmark được xác nhận bên ngoài. **Ngày:** 30/09/2026. Kết quả khoa học và giới hạn hiện tại: [`repguard_final_pipeline_assessment_2026-09-30.md`](repguard_final_pipeline_assessment_2026-09-30.md).

## Mục đích

HistRepEval đo **phản hồi lịch sử không hoàn hảo có cải thiện quyết định hiện tại của một pool agent/model hay không**. Một phương pháp phải báo cả chất lượng ước lượng reputation (Brier, calibration) và tác động thực tế (đáp án/route đúng, chi phí, regret, mất mát dưới attack). Chỉ giảm Brier không đủ để nói hệ thống đã trả lời tốt hơn.

## Phạm vi v0.1 có dữ liệu thật

- Nguồn câu hỏi: bản local `TIGER-Lab/MMLU-Pro`, 12.032 câu, 14 môn; benchmark gốc: [Wang et al. 2024](https://arxiv.org/abs/2406.01574). Split deterministic seed 42: 7.241 train/calibration, 2.375 dev, 2.416 test.
- Pool chính Week 3: Qwen3 8B, Gemma2, Llama3 8B, Qwen3 0.6B, cùng prompt zero-shot direct JSON, temperature 0, `think=false`. Ledger thật 18.064 agent–task answers và manifest/digest trong `results/real_week3_json_v1/`.
- Follow-up capability: Qwen3 8B direct/thinking ghép cặp trên 420 câu train và 280 câu dev không trùng ID; 14 môn được cân bằng. Đây là **policy/cost comparison**, chưa phải pool đa reasoning model.
- Pool overlap bổ sung đã chạy thật trên đúng 420 câu screen: Gemma2, Llama3 8B và Qwen3 14B direct, 1.260 response mới, đủ cả 14 môn và cùng task ID với Qwen3 8B direct/thinking. Phân tích đầy đủ: [`repguard_pool_gate_assessment_2026-09-30.md`](repguard_pool_gate_assessment_2026-09-30.md). Pool này cho 344/420 oracle any-of-five nhưng subject router cross-fit chỉ 274/420 so 280/420 của always thinking; **không chứng minh** DART.
- Feedback thật: Qwen3 14B candidate-conditioned trên 280 câu history/694 unique answer cases; blind judge trên cùng 280 câu. Feedback can thiệp có seed (oracle/noisy/directional) được dùng cho phân tích nhân quả thuật toán, phải dán nhãn khác feedback quan sát thật.
- Attack pilot A1/A2 hiện dùng can thiệp forced-wrong bằng gold trên đáp án attacker và poisoning feedback có mục tiêu. Đây là stress test, không đại diện cho tần suất attack tự phát.

## Đơn vị dữ liệu và giao diện phương pháp

Một task có `task_id`, `subject`, câu hỏi, lựa chọn và gold **chỉ trong offline evaluator**. Online method nhận phiên bản không có gold, lịch sử gồm `(agent, task/skill, observed feedback, source, timestamp/ordering)`, và ngân sách audit/solver công khai. Mỗi response lưu model ID/digest, prompt hash, cấu hình, raw output, token và latency. Method xuất lựa chọn agent/đáp án, các hành động thêm, chi phí và score/uncertainty để kiểm toán.

Không cho phép method đọc gold test hay oracle winner trong lúc chọn. Oracle routing theo câu và `OracleFixedBorrow` chỉ là chẩn đoán upper reference, không là baseline triển khai. Khi cùng một câu có nhiều answer cases hoặc nhiều agent, bootstrap theo **task/cụm phù hợp**, không coi từng case độc lập.

## Trục đánh giá dự kiến

1. **Feedback quality:** clean oracle, nhiễu symmetric, false positive có hướng, judge thật đã khóa prompt, judge khác họ model; lưu sensitivity/specificity theo agent/skill nếu mẫu đủ.
2. **Task transfer:** same, related, unrelated theo taxonomy cố định và các skill feature được học chỉ từ train; báo nguồn và giả định của mỗi quan hệ. `tau=0` khiến posterior về prior là hiệu ứng cơ học, không phải bằng chứng mọi kỹ năng không transfer.
3. **Evidence sparsity và audit:** số feedback mỗi agent/skill, ngân sách gold audit, random audit và audit chọn theo giá trị đảo quyết định; tính cả chi phí audit khi so phương pháp.
4. **Strategic behavior:** ít nhất hai attacker, nhiều seed/history order, nhiều budget, poisoning riêng agent/skill, câu trả lời do model tạo và forced-wrong oracle được tách thành hai loại.
5. **Cost:** output/input token, số API calls, latency và nếu có GPU/USD từ billing thực; so Pareto accuracy–cost và điều kiện cùng ngân sách.

## Metrics và so sánh tối thiểu

- **Primary phải khóa trước mỗi study:** team accuracy hoặc utility/risk tại ngân sách cố định, so phương pháp mạnh nhất thích hợp; paired CI theo câu và subject/benchmark nếu suy rộng.
- Secondary: Brier, ECE/reliability diagram, competence MAE, unique-expert success, **decision sensitivity** (tỷ lệ câu mà hai phương pháp chọn đáp án khác nhau và thắng/thua trong các câu đó), attack regret, worst-group accuracy, số lần switch, tỷ lệ audit, token/latency. Báo cả số câu đúng tuyệt đối và denominator. Trong phân tích judge thật hiện có, ECRT và FixedBorrow đổi đáp án cuối ở chỉ 37/2.416 hoặc 41/2.416 câu theo hai fold dù reputation trung bình đổi khoảng 0,10; đây là kết quả thăm dò trên test đã xem.
- Thêm **rescueability gap**: số câu oracle có nguồn khác đúng khi solver chính sai, rồi so với số câu một policy không đọc gold thực sự cứu được. Trên pool mới, khoảng cách 64 câu rescue oracle so router theo môn **−6 câu** so solver chính cho thấy “có diversity” chưa đủ; chỉ số phải tách oracle ceiling khỏi realized gain.
- Hàm offline `repguard.evaluation.decision_value.paired_decision_value` đã tách số câu đổi đáp án, candidate-only correct, baseline-only correct, oracle either và realized gain trên cùng task ID; đáp án invalid được tính sai. Đây là phép đo, không cấp gold cho online policy.
- Baselines tối thiểu: best single chọn từ train, always thinking, random quota, majority, FixedBorrow, ECRT, skill-conditioned reputation, router theo subject/câu, answer-aware aggregation, self-consistency hoặc solver thêm ở cùng compute. Nếu so với phương pháp công bố như [CP-Router](https://ojs.aaai.org/index.php/AAAI/article/view/40589), phải tái lập đúng input/uncertainty; proxy khác phải ghi là proxy.
- Khi thử nhiều cấu hình, khóa primary contrast hoặc điều chỉnh multiple testing. Không đặt nhãn “confirmed” cho cell chọn sau khi xem test.

## Tình trạng tái lập và phát hành

Mã, manifest, raw ledger, model digest, prompt hash và script analysis đang có; `analyze_real_week3.py` và các analyzer Week 4/5 kiểm tra metadata/duplicate trước khi chấm. Kết quả cũ dựa trên correctness mô phỏng **bị loại khỏi benchmark evidence**. Thư mục `results/` bị Git ignore, nên repo hiện **chưa chứa release bundle**. Trước khi công bố cần đóng gói raw logs có checksum, manifest chính xác, dataset/model license, phiên bản code/container, chỉ dẫn một lệnh tái tạo, audit các câu lỗi, benchmark thứ hai/pool khác và independent rerun. Cần một bản card mới sau khi các mục này được hoàn tất.

## Giới hạn sử dụng

MMLU-Pro nhiều lựa chọn với bốn model trả lời độc lập chưa đo agent tương tác nhiều bước. Judge blind vẫn tự giải sai 129/280 câu; verdict accuracy bị ảnh hưởng bởi tỷ lệ đáp án sai. Week 3 test đã được xem và mở rộng sau pilot; Week 5 dev đã được xem; các method thiết kế từ những kết quả đó cần holdout mới. Không dùng v0.1 để tuyên bố an toàn trước tấn công, lợi ích DART, hay tính tổng quát ngoài benchmark.
