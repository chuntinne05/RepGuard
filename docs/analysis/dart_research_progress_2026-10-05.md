# DART: tổng hợp vòng nghiên cứu và triển khai ngày 05/10/2026

## 1. Kết quả quan trọng

Sau P0 neural không đạt, đã triển khai ba batch theo các protocol khóa trước từng
batch: gain/structure **305 cases**, historical rectifier uniform **300 cases**,
và historical rectifier paired **300 cases**. Cả ba đã hoàn tất trên Modal.
Sau đó hoàn tất thêm300cases kiểm tra Sequential Halving (hai baseline/case).
Tổng **1.205 cases**, không đồng nghĩa 1.205 task độc lập hoặc solver calls mới.

Ứng viên primary tốt nhất ở vòng này là **CFJudgeFactor với paired audits**:
**74,15/168** ở ngân sách gold 10%, so với PairedGlobal71,95 và Uniform69,70.
Đây là cải thiện trên dữ liệu phát triển. Gate đã khóa yêu cầu CI dương với cả
hai controls vẫn **FAIL**; không sửa tiêu chí sau khi thấy kết quả.

| So sánh primary 10% | Chênh lệch task /168 | Điểm phần trăm | CI 95% điểm phần trăm |
|---|---:|---:|---|
| So với PairedGlobal | +2,20 | +1,31 | [+0,03; +2,59] |
| So với UniformAuditGlobal | +4,45 | +2,65 | [−0,60; +5,86] |
| So với paired CFGoldFactor | +1,30 | +0,77 | [0,00; +1,58] |
| So với uniform TunedFactorRidge | +2,55 | +1,52 | [−1,07; +4,05] |
| So với uniform CFJudgeFactor | +2,15 | +1,28 | [−1,58; +4,14] |

CI đầu dương nhưng rất sát0, chưa điều chỉnh cho lịch sử nghiên cứu thích nghi.
Không gọi là bằng chứng thắng mọi baseline, xác nhận độc lập hoặc thành công A/A*.

CI với baseline có điểm thấp hơn vẫn có thể rộng hơn: các phương pháp dùng cùng
paired masks có lựa chọn tương quan hơn. Với PairedGlobal, primary cứu5,95 và
làm hỏng3,75 task trung bình; với Uniform, nó cứu23,05 và làm hỏng18,60. Hiệu
số thứ hai lớn hơn nhưng biến động theo generator cũng lớn hơn. Không có mâu
thuẫn thống kê, cũng không được bỏ comparison bất lợi khỏi gate.

## 2. Những hướng thực sự đã thử

### A. Giữ đủ biểu diễn và tối ưu utility trực tiếp

SemanticRidge dùng đủ MiniLM384 thay PCA16. TextRidge dùng TF-IDF fit trong train.
DirectUtility học policy tuyến tính bằng softmax-weighted signed utility.
FactorRidge chia sẻ thống kê giữa agent cùng model/scaffold. Selected chọn family
và regularization bằng inner CV, chỉ dùng nhãn đã audit.

| Family | 5% | 10% | 20% |
|---|---:|---:|---:|
| UniformAuditGlobal | 64,40 | 69,70 | 75,15 |
| FactorRidge | 66,50 | 71,60 | 75,85 |
| SemanticRidge | 64,75 | 68,50 | 73,65 |
| TextRidge | 65,55 | 68,60 | 74,80 |
| DirectUtility | 64,60 | 65,95 | 69,45 |
| Selected | 64,95 | 67,25 | 73,30 |
| PairedGlobal | 62,15 | 71,95 | 76,70 |

Full-label R0 của batch này cũng không cải thiện: Global82, Factor82,
Semantic74, Text76, DirectUtility78, Selected77. Không trộn các số full-label đó
vào bảng audit10% để tuyên bố thắng.

Nguồn tham khảo: [Causal LLM Routing](https://arxiv.org/html/2505.16037v2) tối ưu
quyết định thay vì chỉ dự báo metric. Bản ở đây là adaptation nhỏ, không tái lập
nguyên paper, và ý tưởng tối ưu regret/utility không phải novelty của DART.

### B. Hiệu chỉnh lịch sử, giữ nguyên uniform acquisition

Học proxy outcome từ agent identity và judge scores, cross-fit theo generator;
mỗi task được dự báo bởi mô hình không thấy gold của generator đó. Sau đó cộng
residual trên những nhãn đã audit với denominator n_a+2. Constant proxy=.5 khôi
phục chính xác Beta Global. Không đưa feedback của task test vào router.

Primary CFJudgeFactor đạt66,50 /72,00 /76,10 ở5/10/20%. Ở10%, cao hơn Uniform
2,30 task nhưng chỉ hơn Paired0,05 task; CI chưa xác nhận lợi ích. Ablation
JudgeImpute đạt72,85, nhưng không đổi nó thành primary sau khi thấy điểm.

[PPI++](https://arxiv.org/html/2311.01453v2) và
[Cross-PPI](https://arxiv.org/html/2309.16598v2) cung cấp động cơ cho correction
và cross-fitting. Estimator shrinkage và argmax ở đây không tự có các bảo đảm
của những công trình đó; chưa gọi nó là unbiased hay deployment-certified.

### C. Giữ estimator, chỉ thay acquisition sang paired

Dùng đúng các masks PairedGlobal đã lưu: audit đủ14agent ở một số task và phần
dư trên một task khác; tổng vẫn đúng B nhãn task–agent. Không chọn task từ gold.
Primary10% đạt74,15; ablations paired CFGold72,85, raw-judge rectifier68,80,
JudgeImpute72,55, fixed factor72,30.

| Paired estimator | 5% | 10% | 20% |
|---|---:|---:|---:|
| PairedGlobal | 62,15 | 71,95 | 76,70 |
| CFGoldFactor | 62,75 | 72,85 | 76,75 |
| CFJudgeFactor (primary) | 64,70 | 74,15 | 77,50 |
| RawJudgeRectifier | 66,55 | 68,80 | 75,75 |
| JudgeImpute | 66,85 | 72,55 | 77,50 |
| FixedFactorRidge | 62,60 | 72,30 | 77,35 |

Kết quả gợi ý phối hợp thiết kế audit và xử lý feedback có ích. Nhưng gain do
judge so với CFGold chỉ có CI lower bằng0; gain do acquisition so với uniform
CFJudge có CI chứa0. Do đó chưa chứng minh riêng từng cơ chế đều có lợi ích chắc.

### D. Kiểm tra với đối chứng phân bổ nhãn thích nghi

Đã khóa code/protocol ở commit `90d4262` trước chạy và hoàn tất300cases trên
Modal, run `3e7b59ea64ebe3767bef00b6`. Chạy lại và kiểm chứng600lần chọn agent
từ query logs, đối chiếu đúng ngân sách và checksum. Ứng viên CFJudgeFactor không
thay đổi theo kết quả đối chứng.

| Phương pháp | 5% | 10% primary | 20% |
|---|---:|---:|---:|
| IndependentSH | 65,00 | 69,70 | 77,20 |
| PairedSH | 67,00 | 71,90 | 78,95 |
| Paired CFJudgeFactor | 64,70 | 74,15 | 77,50 |

Ở10%, ứng viên hơn IndependentSH2,65điểm% (CI[+0,54;+4,94]), hơn PairedSH
1,34điểm% (CI[−0,86;+3,42]). Gate mới yêu cầu CI dương trước cả hai vẫn FAIL.
Ở5% và20%, PairedSH có điểm trung bình cao hơn ứng viên; các CI chênh lệch này
cũng chứa0. Không có bằng chứng phương pháp nào thắng đều toàn bộ ngân sách.

Chẩn đoán sau chạy cho thấy ở10%, SH chỉ có3nhãn/agent trong vòng loại đầu;
IndependentSH loại hết các agent đồng hạng tốt nhất của toàn TRAIN trong29/100case,
PairedSH trong16/100case. Ở20%, PairedSH giữ ít nhất một agent tốt nhất TRAIN đến
cuối trong77/100case. Đây là đo lường mô tả bằng gold TRAIN sau khi hành động đã
khóa, không phải nhãn miễn phí được đưa vào baseline. Nó cho thấy vấn đề loại
sớm khi ít nhãn và lợi ích có thể có của việc so sánh trên cùng task.

Nguồn: [Sequential Halving, Algorithm2](https://proceedings.mlr.press/v28/karnin13.pdf).
Bản triển khai dùng archive hữu hạn không hoàn lại và chuyển phần dư budget;
không mặc định có các bảo đảm của setting stochastic IID trong bài gốc.

## 3. Hiểu sâu hơn vì sao các bước trước chưa thắng

### Utility optimization có thể học nhiễu của sparse audit

Ở10%, DirectUtility có giá trị HT trên nhãn dùng huấn luyện trung bình2,18745;
objective giảm từ0,18510 xuống−0,77124. Đây **không phải accuracy218,7%**:
HT với trọng số nghịch xác suất không bị chặn ở1, và policy tối ưu trên cùng
nhãn có thể khai thác biến động của estimator. Accuracy ngoài mẫu chỉ39,26%.
Quan sát này phù hợp với overfitting sparse supervision, không phải optimizer
chưa chạy. Nó không chứng minh một định lý bất khả thi cho direct policy learning.

Ở full-label R0, training utility trung bình0,62852 và outer accuracy0,46429;
vẫn có khoảng cách tổng quát hóa ngay cả khi thiếu nhãn không còn là vấn đề.

### Inner model selection cũng nhiễu

Ở100case10%, Selected chọn DirectUtility32lần, SemanticRidge25, Global23,
FactorRidge11 và TextRidge9. Dù FactorRidge có mean outer tốt nhất trong shortlist,
inner CV không biết điều đó và thường chọn các mô hình khác. Vì vậy không có
bảo đảm “thêm nhiều ứng viên + CV” sẽ tốt hơn cấu hình nhỏ cố định.

### Sampling covariance quan trọng cho so sánh agent

Descriptive full-normal covariance của success giữa react_gpt4o và13agent còn
lại đều dương; median0,05938. Với cùng số cặp, variance của mean(Y_a−Y_b) có
thành phần−2Cov(Y_a,Y_b). Paired audits có thể loại một phần nhiễu task difficulty.
Đây là cơ sở thống kê của một đối chứng mạnh; thêm mạng neural không tự mang lại
lợi thế tương đương. Con số covariance mô tả toàn tập đã xem, không được dùng như
out-of-sample proof hoặc feature nhìn thấy gold khi triển khai.

## 4. Đầu ra hiện tại có ý nghĩa gì?

- **HistRepEval**: có protocol, audit masks, failure analyses, real-history evidence
  và các so sánh kiểm soát có thể tái lập.
- **DART**: đã có một ứng viên xử lý imperfect history cải thiện point estimate
  và có tín hiệu exploratory so với paired control. Chưa là DART hoàn chỉnh với
  transfer theo task hay acquisition thích nghi.
- Các estimator history ở vòng này chọn **một agent toàn cục từ lịch sử train**,
  không phải chọn một agent khác cho mỗi instruction test. Phải viết đúng điều đó.
- Chi phí audit gold ngang nhau; judge history có chi phí thu thập riêng. Không
  suy ra ngang USD/compute với control không cần judge.

## 5. Bước tiếp theo có cơ sở

1. **Đóng băng ứng viên paired CFJudgeFactor** cho bước nghiên cứu tiếp, giữ raw/no-judge/
   no-correction controls. Không tiếp tục chỉnh nó dựa trên cùng outer test để
   đẩy CI lower lên trên0.
2. **Mở rộng dữ liệu và xác nhận độc lập.** Đã kiểm tra metadata của
   [LLMRouterBench chính thức](https://github.com/ynulihao/LLMRouterBench): bài
   thuộc [Findings ACL2026](https://aclanthology.org/2026.findings-acl.1881/), có
   benchmark nhiều model/dataset và các baseline. Chưa chạy benchmark này.
3. Hugging Face repo `NPULH/LLMRouterBench` được inventory ở revision
   `0e5af1b84bf73437a01a1849c0f1d2468baa93fc`; archive `bench-release.tar.gz`
   1.283.503.080bytes, LFS SHA256
   `b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1`.
   Chỉ đọc metadata, **chưa tải archive hoặc mở outcome**. Trước chạy cần khóa
   phạm vi/split, kiểm tra quyền sử dụng và evaluator, tránh overlap MMLU sealed,
   và xác nhận có feedback lịch sử phù hợp; không dùng gold score làm proxy.
4. **Đo hiệu quả nhãn và chi phí thật**: cùng một pool, cùng B, tính cả judge,
   thêm gold-only structural baseline và các phương pháp gần được thích nghi
   đúng quyền truy cập. Chỉ gọi thắng SOTA sau khi có các đối chứng này.
5. **Muốn có contribution phương pháp**: cần chứng minh cơ chế thu nhận/sử dụng
   trusted labels từ imperfect history hơn các thành phần kế thừa. Neural,
   cross-fitting, ridge và PPI riêng lẻ đều có prior art. Một phép ghép có điểm
   đẹp chưa tự đủ novelty cho hội nghị A/A*.

6. Đã bổ sung kế hoạch cụ thể cho intake dữ liệu, tránh leakage, metadata agent,
   pilot judgment và xác nhận độc lập trong
   [kế hoạch bằng chứng tiếp theo](dart_next_evidence_plan_2026-10-05.md).
   Chuyển từ model×scaffold AppWorld sang model-only pool cần adapter rõ ràng;
   không tự coi đó là xác nhận nguyên trạng thuật toán. Chưa tải archive mới
   hoặc gọi judge mới trong vòng này.

## 6. Vận hành

Các jobs đã deploy rồi `.spawn()`; không cần laptop/Codex giữ vòng đời. Batch
gain hoàn thành trong lúc Codex hết hạn mức. Cả bốn có checkpoint/ledger trên
Volume, source/input hashes và giới hạn retry/timeout. Không có job tuning vô hạn.

```bash
.venv/bin/python run_dart_gain.py status
.venv/bin/python run_dart_history.py status
.venv/bin/python run_dart_paired_history.py status
.venv/bin/python run_dart_halving.py status
```

Thay `status` bằng `fetch` để lấy artifacts; chạy reporter tương ứng để kiểm chứng
và tái tạo báo cáo. Đã tải và kiểm chứng đủ1.205cases: checksum, đúng budget/control,
tách generator và tính lại bootstrap summaries. Nếu cần lấy bổ sung checkpoint
paired đã hoàn tất, `fetch_dart_paired_volume.py` chỉ tải file còn thiếu, đối chiếu
hash với ledger, tránh tải lại archive lớn. 28 targeted tests đạt,1torch test skip trên laptop; remote
training smoke đã đạt trên Modal. Synthetic tests không trộn vào kết quả khoa học.
Worker SH đã trả kết quả thành công, hoàn tất lúc15:34:26UTC ngày05/10/2026
(22:34:26giờ Việt Nam). Không còn worker thực nghiệm nào của bốn batch cần chờ.

## 7. Tài liệu chi tiết

- [Gain/structure: tất cả kết quả](dart_gain_v1_assessment_2026-10-05.md).
- [History uniform: tất cả kết quả](dart_history_rectifier_v1_assessment_2026-10-05.md).
- [History paired: tất cả kết quả](dart_paired_history_v1_assessment_2026-10-05.md).
- [Đối chứng Sequential Halving](dart_halving_v1_assessment_2026-10-05.md).
- [Kế hoạch bằng chứng và dữ liệu tiếp theo](dart_next_evidence_plan_2026-10-05.md).
- Các JSON đi kèm báo cáo giữ đầy đủ số chưa làm tròn, CI và provenance.
