# Quyết định nghiên cứu RepGuard — 19/10/2026

**Đã hoàn tất và kiểm lại 136 phản hồi model thật mới; chưa có phương pháp reputation vượt baseline được xác nhận.** Đây là một vòng sàng phương pháp, không phải đóng góp cuối của khóa luận. Giữ topic uy tín/chuyển bằng chứng trong hệ đa tác tử, chuyển trọng tâm khỏi weighted voting sang hiệu quả can thiệp có điều kiện.

136 responses gồm 72 trên 24 development reports đã xem và 64 trên 16 report mới so với các LIVE cohorts trước; không coi 136 là 136 task độc lập. 16 report mới vẫn là development. Chưa xác lập report overlap với archive cũ chỉ có query hashes; không nhận là final test hay contamination-free evaluation.

## Hai quyết định đã có bằng chứng

| Cấu hình trên cùng 24 report | Khớp target | Calls/câu | Mean Ollama eval giây |
|---|---:|---:|---:|
| Một agent PoT | 17/24 | 1 | 47.07 |
| Một vòng tự kiểm | 17/24 | 2 | 76.48 |
| Hai vòng tự kiểm | 17/24 | 3 | 103.36 |
| Hai lời giải + tổng hợp | 16/24 | 3 | 87.22 |

Compose: 0 rescue / 1 harm; union 17 = phương án cố định tốt nhất 17. Gate FAIL. **Không fit thêm reputation controller để chọn giữa các output này.** Self-review dùng checklist/prompt cố định, không nhận là best possible single-agent workflow. Một lượt PoT đã đủ thắng cấu hình compose này.

| Backbone, cùng 16 report/prompt/cap 4096 | Khớp target | Valid | Output tokens | Mean Ollama eval giây | GPU |
|---|---:|---:|---:|---:|---|
| qwen3:8b | 11/16 | 13/16 | 24,388 | 38.43 | L4 |
| qwen3:14b | 11/16 | 14/16 | 14,271 | 37.71 | L4 |
| qwen3.5:27b | 11/16 | 12/16 | 41,940 | 76.37 | L40S |
| qwen3.5:27b, think=False | 13/16 | 15/16 | 4,392 | 11.07 | L40S |

8B / 14B cùng 11/16 và cùng correctness mask: zero unique success, union 11. Gate FAIL. Trên mẫu này, 8B không tiết kiệm eval runtime dù ít tham số; đây không phải kết luận thống kê cho mọi workload.

Đối chứng 27B native đạt 11/16, nhưng 4 responses dùng hết 4096 tokens và không xuất answer. Không dùng đây để kết luận giới hạn năng lực model. Giữ nguyên điểm/outputs; bổ sung một control hậu nghiệm trên **toàn bộ 16 câu**, chỉ tắt native thinking, cùng prompt/weights/cap, không chọn riêng câu lỗi. Control đạt 13/16, 0 length stops, native-thinking nonempty=0.

So 14B: control think=False có 2 câu đúng riêng và 0 câu sai riêng. Model 27B đã tải và pin digest thật trên app/volume riêng. Khác GPU và model package nên không gọi cùng compute; cùng source/prompt/output cap không đủ làm matched-cost experiment. Đây là model-configuration control trên development, không phải phương pháp reputation hay independent confirmation.

Nâng backbone có cải thiện point score ở probe này. Đó là lợi ích của solver/configuration, không phải reputation. Phương pháp tiếp theo phải so với chính baseline mạnh hơn này, không chỉ so với 14B.

GPU-eval cost proxy cho cả 16 câu: 14B=0.133944 USD; 27B think=False=0.095976 USD. Đây là runtime×GPUrate, không phải billing và không gồm cold load/idle/CPU/RAM. Mọi policy về sau phải so cả cấu hình solver này; không nhận lợi ích do tắt thinking thành gain reputation.

Đây chỉ là candidate baseline trên development: accuracy point gain 12.5 pp, paired bootstrap95% [0.00, 31.25] pp; exact paired p=0.50. Cost-proxy ratio=0.717, bootstrap95% [0.411, 1.119]. Chưa xác nhận superiority/cost saving ở population. Zero harm/16 vẫn có cận trên một phía95% khoảng17.1%; không chứng minh non-inferiority2 pp.

## Đối chứng rẻ và giới hạn headroom

Bảng dưới chỉ dùng cấu hình 27B **native 4096** đã lưu, không chọn nó làm baseline duy nhất để quảng bá tiết kiệm. Fixed 14B đã có cùng 11/16 và rẻ hơn ở proxy; không cần reputation để nhận khác biệt này. Control think=False bên trên cũng phải được xét trước khi chốt comparator.

| Replay trên 16 responses thật, 27B native | Khớp target | Mean calls | GPU-eval cost proxy / direct27B native |
|---|---:|---:|---:|
| direct14b | 11/16 | 1.000 | 0.202 |
| direct27b | 11/16 | 1.000 | 1.000 |
| invalid_only_regenerate | 11/16 | 1.125 | 0.390 |
| oracle_keep_or_regenerate_DIAGNOSTIC | 11/16 | 1.000 | 0.202 |

**Đây là replay từ outputs thật, không phải policy học đã chạy live.** Rule chỉ gọi 27B khi 14B không executable; không biết gold. Dòng ORACLE dùng gold hiện tại để biết khi nào nên gọi: chỉ là trần chẩn đoán, tuyệt đối không là kết quả thuật toán. Các outputs 27B là solve độc lập, không được đổi tên thành expert repair có nhận incumbent.

Cost proxy nhân thời gian prompt/eval thực với GPUrate công bố, L4=$0.000222/s, L40S=$0.000542/s theo [Modal pricing](https://modal.com/pricing) tại 19/10/2026. Không gồm load/startup/idle, CPU/RAM, audit hay cold-reload effects, không phải hóa đơn. Chưa chứng minh non-inferiority hoặc cost saving của một policy triển khai.

## Root causes được khoanh bằng trace và can thiệp

1. **Bank hiện tại thiếu output bổ sung:** trên 24 report, mọi self-review giữ nguyên correctness; compose không tạo rescue. Trên16 report khác, 8B / 14B đúng/sai cùng câu. Thay một learner chọn output không thể vượt oracle của đúng bank đó. Không suy từ sample sang mọi hệ multi-agent.
2. **Source có tồn tại chưa xác nhận binding:** FRT: compose đổi cặp số đúng năm thành cặp source có thật nhưng gán sai năm, làm 5,908 thành 6,890. EW: compose chỉ chọn một trong hai khoản 0.6/4.1, chưa tạo tổng 4.7 mà reference dùng. Không quy lỗi này cho formatter.
3. **Official score và semantic validity cần tách:** trong 5 shared errors mới có 4 flag về entity subset, stock/flow hoặc sign convention; WRK cũ còn nhầm metric valuation allowance và deferred-tax asset. Đây là flags cần hai người kiểm, không phải 4 label errors đã xác nhận. Không relabel primary và không dùng flags để tuyên bố đã thắng.

Vì vậy, research contribution không nên là “nhiều agent tốt hơn” hay “thêm uy tín”. Cần tạo can thiệp đúng phần, có khả năng bổ sung trước, rồi mới kiểm liệu lịch sử dự báo được tác dụng của can thiệp ấy ngoài development hay không.

## Research gap và hướng phương pháp

Candidate question: **uy tín theo trạng thái bằng chứng và phạm vi sửa có giúp chọn can thiệp hữu ích trên task mới, khi verifier chỉ kiểm được một phần và audit có chi phí, hơn same-budget self-review và learned action-value với cùng dữ liệu không?**

Cơ chế cần thử: giữ PoT đủ năng lực; biểu diễn source–quantity–period–unit; actions KEEP/evidence/operation-unit/bundle; học rescue/harm và interaction từ branches đã thực thi và audit; chọn action trước khi biết correctness. Không coi source-pass là gold. History phải index configuration/model/prompt/executor, tránh dùng profile cũ sau đổi contract.

Đây là giả thuyết, chưa là novelty/superiority đã chứng minh. [MoCA-Agent](https://arxiv.org/abs/2606.11537) đã có claim-based verification; [C3](https://arxiv.org/abs/2603.06859) và [GCJR](https://arxiv.org/abs/2608.29228) đã có counterfactual/joint-repair credit hoặc localization. Khác biệt cần kiểm là transfer và lựa chọn scope repair trên task mới không có oracle chỉ lỗi; phải vượt contextual learner công bằng. Learned selector train trên history vẫn dùng lịch sử dù không có biến mang tên reputation.

## Những việc đã chuẩn bị cho bước tiếp

- 40 câu có phiếu source-only cho hai reviewer độc lập; hiện 0 annotation hoàn tất. Khóa đánh giá metric/kỳ/unit/scope trước xem method identity. Giữ FinQA official score và semantic audit riêng.
- TAT-QA: pin TRAIN/evaluator và chọn 64 arithmetic contexts theo metadata. Chạy evaluator gốc: 64 gold roundtrip và zero-interface software checks; **chưa có inference/model score** trên corpus này. Không lấy software selfcheck làm kết quả model.
- Giữ 200 development/50 calibration/150 confirmation report IDs, tách 124 report LIVE đã dùng. Confirmation chưa có inference hay extracted outcome;150 không mặc nhận đủ power. Archive report-disjointness còn phải làm rõ/disclose.
- Ứng viên scope/interaction repair cần preflight bảo toàn năng lực solver, rồi thử trên report development mới sau audit; nếu corpus có quá nhiều target ambiguity, dùng corpus có contract rõ hơn trước mở rộng history. Không tiếp tục tune trên 24 câu cũ.
- Sau khi bank có headroom mới train/calibrate và đánh giá policy thật trên confirmation. So strong single-agent, fixed expert, rule, contextual action-value, global/conditional history và các ablations. Prototype chỉ là phần trình diễn nhỏ.

Một khóa luận nghiên cứu vững cần phương pháp có cơ chế và bằng chứng end-to-end rõ; không cần nhận thắng mọi ChatGPT/Claude. Đợt này chưa so trực tiếp hai sản phẩm đó và không nhận đã đánh bại chúng.

## Hồ sơ để đọc

- `repguard_research_cycle_02_2026-10-19.md`:72 calls, chi tiết FRT/EW/WRK và gate.
- `repguard_research_gap_2026-10-19.md`:ma trận related work và những novelty claims cần tránh.
- `repguard_method_candidate_2026-10-19.md`:thiết kế phương pháp cụ thể, ghi rõ chưa triển khai.
- Bốn verifier/manifest JSON và các run directories giữ raw responses/source snapshots. 7 primary files của pilot cũ không đổi.
- Tất cả scores là kết quả thật đã lưu/tái tính; không model mock. Không tự lên automation hay gửi thông điệp cho thành viên nhóm.
