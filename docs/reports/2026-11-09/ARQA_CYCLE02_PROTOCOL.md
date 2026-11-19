# Vòng02: numerical QA có ràng buộc ô nguồn và kiểm tác dụng của phối hợp

Viết trước inference vòng02. Vòng01 scientific FAIL được giữ nguyên; không fit history/reputation hoặc mở rộng để tìm kết quả thuận lợi. Vòng02 chuyển sang nguồn enterprise đã nêu trong path trước, đo một cơ chế cụ thể. Đây là pilot phát triển, không phải phép xác nhận khóa luận.

## Câu hỏi và quyết định

Khi được cùng bảng nguồn, cùng schema và cùng checker, reviewer khác họ model có sửa lỗi tốt hơn self-review không? Checklist giữ entity/metric/period/operation có giúp riêng việc phối hợp, hay chỉ giúp mọi cách prompting?

Thiết kế factorial hai profiles (`standard`, `checklist`), mỗi profile sáu workflows: A, B, AA, BB, AB, BA. Chữ đầu là model tạo draft, chữ cuối là reviewer; reviewer nhận **raw draft đã lưu thật**, ẩn danh tính. Cả hai profiles đều trả cùng schema answer/unit/program/claim slots/explanation. Checklist được cấp cho cả direct và review, tránh giữ rubric tốt chỉ cho method.

Primary: trung bình cân bằng `(AB−AA + BA−BB)/2` trong checklist, mỗi nhóm nguồn một câu. Secondary: primary ở standard và interaction giữa hai profiles; các so sánh này không được thay primary sau kết quả. Self/cross cùng tối đa hai calls; direct một call chỉ là diagnostic thấp chi phí. Cùng giới hạn context/output không có nghĩa cùng token thực; phải báo token và serving time của **cả workflow**, gồm draft.

Gate mở rộng: primary ít nhất5pp, cận dưới CI bootstrap95% >0, rescue trên ít nhất4groups, schema validity>=95%, receipt audit PASS. Hai nhóm đầu là operational screen trước chạy phần còn lại; transport error hoặc screen FAIL thì dừng, không retry tự động. Cap **288 corpus generations** cho24câu×12arms. Không dùng kết quả screen để chỉnh prompt rồi gộp với run cũ.

24groups là pilot, không có power để nhận superiority nhỏ hay chứng nhận risk hiếm. Nếu gate FAIL: dừng scale/history, xem lỗi và tìm giả thuyết thực tế mới. Nếu GO: vẫn phải có semantic adjudication, stronger-model control, power calculation và tập xác nhận chưa dùng trước khi nhận method hiệu quả.

## Nguồn và oracle

[ARQA](https://aclanthology.org/2026.eacl-industry.63/) tại commit `483e8c7b084afc6fbfb46d8609617b297b4322b8`, đúng hai file đã kiểm SHA256. Chỉ dùng bảng đã cung cấp sẵn, không đo retrieval/full-report QA. Một issuer Volkswagen, 2015–2024; không có company-held-out result.

Đã đọc source scorer chính thức, không chạy/import mã bên thứ ba hoặc mở model results của repo. `evaluation/eval.py` dùng `cell.value` do prediction khai trong `run_program`; arithmetic evidence đối chiếu row/value và bỏ cột. `decimals_equal_ulp_round` còn cho phép lệch1 ở gold integer. Vì vậy không dùng official math score để chứng nhận source grounding.

Checker mới đọc giá trị trực tiếp theo cell ID bất biến, dùng Decimal và whitelist phép toán, không eval/exec mã do LLM sinh. Chỉ cho constants phục vụ tỷ lệ/scale; kiểm register, giới hạn steps, chia0, nguồn ô và consistency với answer. Không dựa vào `result` do model khai. Các cột trần năm được mở rộng bằng metric kế trước; gold tham chiếu cột năm lặp chỉ được gỡ mơ hồ khi giá trị khớp duy nhất một ô nguồn. Header-only evidence được kiểm riêng, không coi là ô dữ liệu.

Audit cuối: **561/623** arithmetic items qua kiểm source/program/evidence và rounding của đáp án công bố. 62 trường hợp chưa qua được ghi lý do, **không đồng nghĩa 62 nhãn sai**: có thể do schema, interpreter, nguồn hoặc phép tính/rounding. Không sửa gold. Bản thử parser nội bộ quá chặt đã bỏ qua precision/header metadata; đã sửa trước registration và trước mọi inference, kết quả thử đó không là kết quả nghiên cứu. [Audit](arqa_oracle_audit.json).

Chọn24nhóm kết nối bởi table content trùng hoặc paragraph ID chung; mỗi nhóm một QA theo SHA256, nguồn2015–2021, context<=14.000ký tự. Nhóm chạm2022+ ở reserve. Audit nguồn đã đọc gold chương trình toàn bộ để kiểm dữ liệu; reserve **chưa có model predictions/scores**, không được gọi là gold hoàn toàn chưa từng nhìn. Selection không dùng model outcomes; không quảng bá subset này là điểm toàn bộ ARQA.

Gold pilot để offline: giá trị tính lại từ nguồn, published value, unit và refs. Public packet chỉ có question/table/source metadata và stable cell IDs; không answer/program/evidence gold hay q_type. GPU chỉ nhận prompt, weights read-only; không mount gold. Primary accuracy yêu cầu số sai khác<=0.005000001 với source recomputation và unit qua alias rõ ràng. Không âm thầm đổi scale1000x. Numeric-only và source-binding score báo riêng.

**Giới hạn oracle:** chưa có người adjudicate entity/formula/period của24câu. Chương trình chạy đúng và trỏ ô thật vẫn có thể trả lời sai metric. Test cố ý cho thấy Revenue và Profit cùng tăng20% nên checker không phát hiện sai metric bằng số. Do đó binding filter chỉ là control không thêm LLM, không là semantic verifier hoặc chứng nhận an toàn sản phẩm. Accepted-risk ở đây chỉ relative với numeric/unit gold, không ground truth toàn bộ nghiệp vụ.

## Đối chiếu prior art mới đọc

- [VeriFin v3,23/10/2026](https://arxiv.org/html/2608.10213v3): đã tách candidate khỏi việc dựng facts/formula, ràng buộc XBRL và SMT, có abstain. Đọc phương pháp, thiết lập, error analysis. Generic source binding, executable arithmetic hoặc accept/reject/abstain **không là novelty của đồ án**. Checker hiện tại yếu hơn: không có independently authorized formula/XBRL. Không so số trực tiếp giữa corpus khác nhau.
- [Upstream Influence,13/10/2026](https://arxiv.org/html/2610.17723v1): đã can thiệp source access/handoff và đo re-anchoring trong political stance chains. Đọc thiết kế và kết luận; không suy hiệu quả sang numerical QA. Việc đổi handoff format tự nó không mới; pilot này chỉ kiểm xem tác động có tồn tại trên lỗi số/ngữ nghĩa có gold hay không.
- [A Multi-Agent Question-Answering System for Financial Statements,online30/10/2026](https://www.sciencedirect.com/science/article/pii/S1568494626021861): tìm thấy abstract chính thức về critic verification cho retrieval/reasoning và diminishing gains ở model mạnh. Full page403, chưa đọc toàn văn; đây là warning về comparator/novelty, chưa dùng số hoặc kết luận chi tiết của bài.
- MoCA-Agent và CLAIR-Fin đã được đối chiếu ở literature trước. Checklist/claim slots là adaptation và baseline cần có, chưa đủ làm đóng góp khóa luận mới.

Hướng có thể nghiên cứu tiếp **nếu pilot có bằng chứng**: điều kiện nào handoff làm reviewer đổi đúng thành sai dù source binding PASS, và cách ngăn harmful revision có giữ correction utility ở cùng ngân sách không. Đây là giả thuyết cần kiểm, chưa là gap đã chứng minh chưa ai giải.

## Reproduce và hồ sơ

Source ở `experiments/arqa_v2/`, tests `tests/test_arqa_v2.py`. Registration khóa source hashes/model digests/config/primary/cap trước launch; không sửa code đã khóa trong run. Raw nguồn, outputs và gold ở gitignored `results/arqa_v2/`; không tái phát hành annual-report data theo mặc định MIT code license. Không claim user validation:0participants, chưa outreach.

Các bước đã định: source audit → tests → registration → inference giới hạn → receipt/lineage audit → offline scoring → GO/STOP và cập nhật path. Không đụng source/output frozen vòng01 hoặc deployment khác của người dùng.
