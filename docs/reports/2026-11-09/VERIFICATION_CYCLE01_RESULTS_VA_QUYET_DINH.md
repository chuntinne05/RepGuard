# Vòng thực nghiệm 01 — kết quả thật và quyết định kế tiếp

Ngày 09/11/2026, giờ Việt Nam. Plan `1a97e7cca4367a1fe81c9417`, đăng ký trước corpus inference.

**Kết luận:** đã hoàn tất và kiểm toán **720 responses thật trên120 claim–passage pairs/24 claim groups**. Operational audit PASS, nhưng **interaction gate FAIL**: cross-family review hơn self-review trung bình2,08 điểm %, CI95 theo claim cluster[−0,42;+4,59], dưới floor3 điểm đã khóa. Không fit history/reputation learner, không mở rộng inference tự động.

## 1. Đã làm, theo thứ tự có plan

1. Đọc lại nguồn/limitations của sufficiency dataset và các close papers; lập [execution plan](EXECUTION_PLAN_V1.md).
2. Pin DG-evidence750 tại commit`dc65e18a0a3e40e13c461c05b55103379db1fd8e`, SHA256`96354cebf802d1fb6ff4967cade1b1cb3ebe61d578212276c9962a2345cab039`.
3. Exact claim/passage duplicate links tạo147 metadata groups từ150 claims. Chia trước outcomes: pilot24claims/24groups; history-dev57/56; calibration21/20; reserve48/47. Đây không là chứng nhận mọi near-duplicate hay cùng nguồn đã được loại.
4. Hai generation smoke attempts tổng hợp: Gemini3.8 timeout không có receipt xác nhận generation; Gemma API trả được. Không blind retry; chọn Modal fallback đã viết trước, không chọn backend theo benchmark scores.
5. Khóa [registered plan](registered_verification_v1.json), source hashes, caps, prompts, bootstrap và gate.13 meaningful harness tests pass.
6. Chạy hai model thật trên app Modal mới; weights volumes cũ được mount **read-only**, không gọi deployment cũ và không đưa gold vào inference.
7. Thu đúng720 terminal responses,0transport errors; hoàn tất lúc**09:37:03 ngày09/11/2026**. Container của app pilot sau đó được kiểm tra và nhận`[]`.
8. Tải artifacts, kiểm source/receipt/prompt/parent/model/GPU, rồi chạy scorer offline đã freeze. Read-only ZIP fetch từng timeout; CLI get được khắc phục bằng staging directory có sẵn. Không generation lại vì lỗi download.

## 2. Task và ranh giới của kết luận

Task là đánh giá **một passage có độc lập đủ căn cứ để support/refute một claim không**, bốn nhãn: irrelevant, relevant-insufficient, sufficient-support, sufficient-refute. [Nguồn dataset](https://github.com/dweebee/dg-evidence-750), [paper/rubric](https://aclanthology.org/2026.finnlp-1.32.pdf).

Đây là financial/economic public fact-checking, có cả claim dạng câu hỏi và nội dung chính sách/kinh tế. **Không phải tập báo cáo tài chính doanh nghiệp**, không phải gold claim truth ngoài passage và không chấm joint sufficiency của nhiều passages. Không dùng kết quả này để nhận sản phẩm kiểm annual reports đã hiệu quả.

Pilot gold có56irrelevant,41relevant-insufficient,16support,7refute. Chỉ23/120pairs có sufficient evidence theo published labels; class imbalance và ít refutation cases giới hạn độ chính xác của các kết luận phụ. Không đổi nhãn theo model outputs.

A=Qwen3.5 27B, B=Gemma4 26B, non-thinking, temperature0, output cap2048, context16384; digests/GPU/Ollama version được lưu và audit. Đây là hai cấu hình open-weight đã khóa, chưa phải strongest frontier baseline.

## 3. Bảng kết quả chính

Arrow chỉ model thật nhận initial answer rồi re-check cùng passage. Model identity của initial answer được giấu; self/cross dùng cùng review prompt. Mọi double workflow có hai calls, nhưng không tự là matched monetary/compute cost.

| Workflow | Đúng/120 | Accuracy | Macro-F1 | Calls/case | Mean request giây/case, gồm initial |
|---|---:|---:|---:|---:|---:|
| A direct |91|75,83%|0,6813|1|3,99|
| B direct |85|70,83%|0,6198|1|2,10|
| A→A self-review |93|77,50%|0,6702|2|8,38|
| B→B self-review |85|70,83%|0,6386|2|4,23|
| A→B cross-review |96|80,00%|0,7702|2|5,12|
| B→A cross-review |87|72,50%|0,6199|2|5,44|

Primary đã khóa:`0.5×[(AB−AA)+(BA−BB)]` = **+2,0833 điểm %**, claim-cluster bootstrap5000 replicates, CI95**[−0,4167;+4,5938]**. Gate yêu cầu≥3 điểm; **FAIL**. Không đổi primary sang AB sau khi thấy AB cao nhất.

| Paired contrast | Rescue | Harm | Net |
|---|---:|---:|---:|
| AB so AA |7|4|+3/120|
| BA so BB |5|3|+2/120|
| AB so A direct, chẩn đoán phụ |5|0|+5/120|
| AA so A direct, chẩn đoán phụ |6|4|+2/120|
| BA so A direct, chẩn đoán phụ |9|13|−4/120|

Có rescue ở8claim groups trong hai primary contrasts. Oracle union sáu workflows=**105/120**, best fixed hậu nghiệm=AB96/120: có9cases headroom trong bank, khác bank TAT-QA cũ. Oracle dùng gold không là policy; headroom chưa chứng minh history/current-state learner khai thác được.

## 4. Precision/coverage: chưa đủ để tự động chấp thuận

Phải tách “đưa ra một sufficient verdict, support hoặc refute” khỏi “chấp thuận claim là supported”.

| Workflow | Sufficient verdicts | Sai trong sufficient verdicts | Supported approvals | Sai trong supported approvals |
|---|---:|---:|---:|---:|
| A |21|8|10|2|
| B |19|6|17|6|
| AA |12|3|6|1|
| BB |16|4|12|3|
| AB |18|3|12|2|
| BA |12|3|7|1|

AB có sufficient-risk3/18=16,7%, nhưng **supported-approval risk2/12=16,7%**, bằng điểm ước lượng1/6=16,7% của AA ở coverage khác nhau. Không được lấy accuracy80% hoặc sufficient-risk thấp hơn làm bằng chứng false approvals đã giảm ở cùng coverage. Các denominator nhỏ; không có deployment-risk guarantee.

99,86%responses parse-valid (719/720),0length stops,0native-thinking outputs. Exact quote grounding được audit riêng; có quote bị rút gọn/ellipsis. Không sửa parser hoặc đổi score để làm tăng accuracy. “Quote xuất hiện” cũng không chứng minh sufficiency.

## 5. Chi phí và vận hành

720corpus responses dùng535.585input và81.244output tokens theo Ollama counters. Không cộng lại cached initial outputs như các responses mới. Khi tính cost của một workflow hai bước, vẫn tính đủ initial+review.

Các request seconds trong bảng là runtime/RPC proxy của cấu hình này, không phải hóa đơn hay end-to-end production latency. Collection có thời gian khởi động, checkpoint/volume commit và chờ, không đồng nhất với tổng generation time. Chưa có billing statement nên **không báo USD savings**. Hai API smoke attempts được lưu riêng, trong đó timeout có generation/billing outcome chưa biết.

App pilot đã dừng,0containers theo lần kiểm sau collection; app bạn bè và deployments cũ không bị gọi hoặc thay đổi. Một CPU fetch task từng timeout, không tạo thêm inference.

## 6. Forensics phụ: điều gì đáng kiểm tiếp?

Đây là đọc hậu nghiệm một số paired errors, **không phải human adjudication** và không thay published labels.

- **Handoff có thể thay đổi cách hiểu claim.** Có case Qwen diễn giải một phát biểu về tương quan thành khẳng định nhân quả, rồi hạ sufficiency; Gemma nhận ra bằng chứng cho phát biểu mô tả. Cần kiểm preservation của metric/quan hệ/qualifiers, không suy từ confidence rằng review đúng.
- **Trích lời hứa/ý định chưa phải kết quả đã xảy ra.** Có case reviewer chấp thuận một phát biểu về tác dụng chính sách vì passage lặp lại lời phát biểu ấy. Reviewer khác yêu cầu bằng chứng cho kết quả thực. Cần rubric attribution/tense/scope rõ.
- **Relevance boundary gây nhiều nhầm.** Một đoạn nói về ngành/chính sách gần claim chưa hẳn đúng entity/metric; 0↔1 errors làm thay đổi accuracy dù verdict support/refute không đổi.
- Một số input là câu hỏi, không phải proposition đã chuẩn hóa. Cần review semantics của nhãn support/refute cho những trường hợp ấy. Không tự coi mismatch là gold sai.

Các ví dụ chỉ gợi cơ chế. Chưa định lượng mọi lỗi theo taxonomy bằng hai reviewers độc lập; chưa chứng minh causal mechanism. Có sẵn source-only packet cho **toàn120pairs**, không chỉ errors: `results/verification_v1/human_review/source_only_all120.json`. Hiện0human reviews.

## 7. Quyết định và path tiếp theo

1. **STOP scale/history learner trên vòng01.** Giữ nguyên FAIL của registered primary. AB là ứng viên development đáng kiểm thêm, không là phương pháp đã thắng.
2. **Tiếp theo là oracle/scope gate và một mechanism study**, không thêm công thức reputation: thẩm định dữ liệu enterprise-report thực; làm rubric cho attribution, kỳ, metric và qualifier; kiểm tra peer exposure/anchoring ở cùng năng lực và budget.
3. Nếu dùng lại DG750 để phát triển, ghi rõ pool financial fact-checking; không biến passage labels thành report/combined-evidence labels. Reserve48claims chưa được scorer này dùng, nhưng không tự là external-domain confirmation.
4. Trước một main method claim, thêm strong-single model có công cụ, self-review cùng quyền, và một close framework adaptation phù hợp. Qwen/Gemma pilot không đủ để nói thắng frontier systems.
5. Product discovery vẫn pending: người dùng chưa có nhóm tham gia. [Recruitment kit](USER_DISCOVERY_KIT.md) đã chuẩn bị; chưa có interviews hoặc user-study results. Chốt vertical sau khi có workflow thật và task được phép chấm.

Kế hoạch nghiên cứu kế tiếp nằm trong [Next study plan](NEXT_STUDY_AFTER_CYCLE01.md). Không inference nào của vòng kế được khởi tạo chỉ vì vòng01 đã hoàn tất.

## 8. Artifacts và tái lập

- [Registered protocol](registered_verification_v1.json), [execution plan](EXECUTION_PLAN_V1.md), [research bổ sung](RESEARCH_SUPPLEMENT_CYCLE01.md).
- [Summary machine-readable](verification_v1_summary.json), [receipt audit](verification_v1_audit.json), [post-hoc diagnostics](verification_v1_diagnostics.json).
- Code:`experiments/verification_v1/`; tests:`tests/test_verification_study_v1.py`; frozen source ZIP, raw responses và evaluation packets nằm dưới ignored`results/verification_v1/`.
- Offline score:`PYTHONPATH=. .venv/bin/python -m experiments.verification_v1.analysis results/verification_v1/runs/1a97e7cca4367a1fe81c9417`.
- Receipt audit:`PYTHONPATH=. .venv/bin/python docs/reports/2026-11-09/audit_verification_v1.py`.

Nguồn dữ liệu công khai vẫn cần tôn trọng điều kiện phát hành. Không phát hành lại raw excerpts nếu chưa có quyền phù hợp; code/manifests/source URLs có thể mô tả cách lấy lại dữ liệu.
