# V5 — phát triển lớp kiểm chung và chuẩn bị nguồn đánh giá rộng hơn

**Đã implement lớp kiểm query/source/operator và bàn giao receipt, kiểm lại36trajectory cũ, chạy lại20SQL thật; chưa có model accuracy mới hoặc novelty đã được xác nhận.** Strategy tổng thể: [Research Strategy V5](RESEARCH_STRATEGY_V5_VA_CONTRIBUTIONS.md).

## Điều mới đã chạy được

- `relational.py`: host-owned contract/catalog; projection/filter/join/group/order/DISTINCT/LIMIT obligations; alias resolve về source column; status met/violated/unresolved tách khỏi release status.
- `search_schema`: tìm literal trong tất cả table/column names, gồm bảng SQLite. Không đoán tự động thuật ngữ nghiệp vụ hoặc quốc tịch qua tên.
- `validate_handoff`: kiểm query/contract/source identities **và tính lại receipt**. Matching hashes không đủ để tin một nhãn met do agent tự khai. Không là signature/authentication scheme; host phải giữ authority inputs.
- `AuditedWorkspaceTools`: query read-only có execution record riêng, audit actual artifact ID và bytes; thay nguồn/derived DB/output sẽ bị phát hiện. Agent-asserted table không được nhận SQL execution assurance.
- CLI kiểm tất cả interpretations được cung cấp, không tự chọn interpretation khớp gold. Một reviewer callback tối đa một lần dùng lại contract/catalog; không có provider call hoặc automatic repair trong package.

Đây là những năng lực triển khai của component. Contracts, deterministic validation và structured handoff đều có prior gần; chưa nhận là thuật toán mới.

## Kiểm chứng đã hoàn tất

**29 tests mới PASS**; scoped regression cùng scalar kernel và frozen workspace tools/trajectory/evaluator là **87 PASS**. Kiểm tên giả/đổi alias, đọc field không đúng vai trò, OR bypass, wrong join, extra output/filter/LIMIT, forged receipt, changed source/query/contract, numeric literals lớn và unsupported SQL. Chưa chạy full repo suite.

**Replay bao gồm toàn bộ36trajectory V4**, không chọn riêng ca thuận lợi:

| Loại artifact | Số lượng | Cách xử lý |
|---|---:|---|
| Không có final artifact | 13 | Giữ là chưa có đầu ra, không bịa query để chấm |
| Final SQL | 20 | Structural audit theo developer contracts |
| Final table từ PDF/agent assertion | 3 | Không coi là SQL proof; cần adapter khác |

Có26query receipts vì task371được giữ **hai interpretations**. Kết quả17violated/9unresolved là số receipts dưới các contract phát triển, **không là17lỗi nghiệp vụ độc lập hoặc precision/recall**. Tất cả26release statuses là needs_review vì không có independent contract approval.

Sau đó chạy lại **cả20SQL cuối trên source DB thật bằng tools mới:20/20 tái tạo đúng bytes đầu ra lịch sử**. Không sửa query, không đọc gold hoặc chạy official scorer trong replay; điều này chứng minh khả năng tái lập/tích hợp, không chứng minh20đáp án đúng.0newmodelcalls,0newhumanannotations,0users.

Artifacts: [structural replay phiên bản cuối](relational_v5_development_replay_v2.json), [SQL execution replay](relational_v5_execution_replay.json). Bản development đầu được giữ nguyên; source snapshots riêng tại `results/relational_v5/` và `analysis_v2/`.

## Những ca thực tế được xử lý khác nhau

Task380: source catalog tìm được `mf_personalinfo.Nationality`. Query dùng Name/ChiName làm proxy bị phát hiện không đáp ứng field/filter/join đã khai báo. Đây là developer source interpretation, chưa phải human-adjudicated semantic error benchmark.

Task371: giữ cả SecuAbbr và ChiNameAbbr; không dùng reference score để tự quyết nghĩa câu hỏi. CLI đánh cả hai và báo cần chọn/thẩm định interpretation. Task44: extra ID column bị chỉ ra, còn quy tắc chọn latest timestamp vẫn chưa được checker này chứng minh. Task35/PDF không được ép thành bằng chứng SQL.

## Nguồn ngoài đã chuẩn bị

[SpecBridge](https://github.com/Xyc-arch/specbridge-artifact/tree/a51be850a113a6b7c0ada57ad3c7806c6c3f25a4) pin revision, README/license/scorer-interface đã đọc. Có204task được upstream chấp nhận trên12databases; đây là labels do tác giả upstream tạo, không phải nhãn mới của đồ án.

Split theo database/metadata: **45development /67validation /92reserved-confirmation**. Ba DB development đã tải và kiểm hash/quick_check; DB validation và confirmation chưa tải. Prompt/reference tách riêng, không tải cached model outputs. [Receipt](relational_v5_external_preparation.json). Chưa chạy upstream scorer, model, native benchmark hoặc phép thử transfer. Cùng generator/choice templates có thể đi qua split, nên chưa gọi đây là independent-benchmark generalization.

## Quyết định tiếp theo

1. Qualification evaluator/SQL operator coverage trên45development tasks; không loại unsupported âm thầm.
2. Hoàn thiện baseline mạnh và same-checker controls; Gemini4Argon quota0 là trạng thái lần probe trước, chưa được giải quyết trong V5.
3. Khóa mechanism experiment có actual drafts, neutral/shuffled controls và tính đủ setup/verification cost; xác nhận khác biệt với SpecBridge/Maat/Trace Integrity và các prior V4.
4. Sau đó mới mở source-held-out confirmation và pilot người dùng. Hiện scientific expansion/history gate **chưa mở**.

Phạm vi thesis là analytical/reporting workflows qua nhiều nguồn; implementation V5 đang hỗ trợ một SQL subset. Không đánh đồng phạm vi thuật toán hỗ trợ hiện tại với việc đã chứng minh tính tổng quát. Old v1/v2/v4 code, primary scores và source ZIPs giữ nguyên.
