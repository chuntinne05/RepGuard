# Path sau vòng01 — khóa câu hỏi kế, không scale theo point estimate

Ngày09/11/2026, viết **sau** kết quả vòng01. Đây là kế hoạch mới, không là preregistration trước outputs vòng01 và chưa là lệnh launch vòng02.

## Kết quả quyết định bước kế

Cross-vs-self balanced +2,08pp, CI chứa0 và dưới floor3pp; scientific gateFAIL. Có complementary cases/oracle headroom và có directional asymmetry, nên không kết luận mọi collaboration vô ích. Dữ liệu hiện tại là public financial/economic fact-checking passages, không là enterprise annual reports. Tính thực tiễn sản phẩm chưa được người dùng thật xác nhận.

## Path A — việc được làm ngay, không cần inference mới

1. Lập source-only human review trên120pairs, hai annotators độc lập; xem riêng câu hỏi vs proposition, attribution và prediction vs observed outcome. Giữ published score; mọi adjudicated sensitivity là secondary, không thay điểm gốc. Không dùng một LLM để tự đóng vai hai con người.
2. Thẩm định một nguồn enterprise-document task: FinED-Bench/error detection hoặc ARQA/FinMRAGBench theo scope. Kiểm nguồn raw, quyền sử dụng, task unit, nhãn, duplicate/company/year groups và oracle. Chốt một bộ chính; không tải/chấm outcomes của mọi bộ rồi chọn bộ method đẹp nhất.
3. Tìm5–8 người đang lập/kiểm báo cáo. Nếu chỉ tiếp cận được nhóm phân tích dữ liệu ngoài tài chính, giữ research primitive nhưng đổi vertical có lý do trước study mới. Không khẳng định product demand khi chưa discovery.
4. Chuẩn bị oracle đủ cho task chính: Supported/Refuted/Insufficient và evidence/metric/period/scope; nếu nhiều passages cần joint sufficiency annotations. Không suy union của pair labels thành gold cho bundle.

## Path B — mechanism experiment ứng viên, chỉ sau oracle preflight

**Câu hỏi:** lợi ích AB đến từ nội dung có ích của peer, hay chỉ từ reviewer được gợi một interpretation? Những thay đổi qualifier/attribution nào gây harmful revision?

Giữ claim và evidence cố định; không thêm retrieval/repair vào cùng phép thử. Trên nhóm development mới chọn bằng metadata, preregister các arms: strong direct; cùng model self-review; blind independent reviewer; peer-exposed reviewer với identity ẩn; structured claim-preserving peer review. Cấp cùng tools và token/call budgets; thêm deterministic/no-extra-LLM aggregation control khi phù hợp.

Structured form chỉ là **prompt/interface adaptation** trừ khi có novelty riêng được chỉ rõ so CLAIR-Fin/MoCA và prior handoff verification. Nếu form giúp cả single-agent tương đương, ghi phần gain là interface/representation, không tự quy cho coordination.

**Primary ứng viên:** paired false-approval/loss ở coverage/budget khóa trước; accuracy/macro-F1 phụ để phân biệt relevance-only improvements. Chuẩn hóa policy ordering, invalid handling, task groups và propensity nếu có sampling. Power/sample size phải chọn trước outcome vòng mới; không lấy24groups pilot làm đủ confirmation.

**Gate:** phải có correction thực trên lỗi ngữ nghĩa và không chỉ thắng một baseline thiếu rubric/tools. Nếu chỉ đổi 0↔1 mà không giảm wrong support/refute decisions hoặc review load, không nhận sản phẩm đã tốt hơn. Nếu strong single làm tương đương, dừng method nhiều agent cho task đó hoặc đóng một measurement conclusion đúng phạm vi.

## Path C — khi nào mới mở history/reputation?

Chỉ khi PathB cho thấy có ít nhất hai reviewer/actions với conditional utility dự báo được và có headroom vượt fixed strong workflow. Sau đó dùng history/dev riêng để so same-information current-state learner, global history, conditional history/partial pooling và history-shuffle. Gold budget, tools và current evidence giống nhau. Nếu generic learner làm bằng, không nhận reputation structure là đóng góp riêng.

Active audit/VOI chưa là main novelty: Ao/ASB/BMA-GAI/CABS đã rất gần. Nếu mở nhánh này cần một protocol và assumptions/comparator matrix riêng.

## Path D — xác nhận và sản phẩm

Freeze một finalist và comparator chính; giữ pool final chưa dùng cho design; external corpus/task unit phù hợp; có stronger model-family control; báo risk–coverage–cost và group uncertainty. Sau đó mới tích hợp policy đã có bằng chứng vào reviewer workbench, đo time/error trong task study với người thật.

Các hướng như AgenticFinBench có thể giúp chọn workload và cách tách grounding/correctness, nhưng rubric/LLM audit không tự thay human gold cho mọi claim. Nghiên cứu người dùng và nguồn dữ liệu cần được thẩm định trước, không hứa một đề tài “tốt nhất” khi các gate còn mở.

## Deliverables trước khi launch vòng02

- Dataset/oracle card và quyền quan sát từng arm.
- Split/group manifest không chọn bằng outcomes.
- Protocol primary/controls/gates/cap, source/model/config hashes.
- Semantic annotation/adjudication status và các ambiguity chưa giải.
- Collector/scorer preflight, paired tests và actual-cost ledger plan.
- Một quyết định GO/STOP có lý do. Nhiều ngân sách không thay những điều kiện này.

## Source intake đã làm sau quyết định vòng01

Đã pin metadata, không tải model outcomes hoặc tính benchmark scores mới; [inventory](enterprise_source_intake.json).

- ARQA: commit `483e8c7b084afc6fbfb46d8609617b297b4322b8`; có `ARQA_validated.json` và `pack_context.db`. Đây là ứng viên preflight tiếp vì có QA và context đi kèm. Cần kiểm schema, mapping nguồn, arithmetic oracle và giới hạn một ngành/một issuer trước khi chia tập. Không gọi source availability là evaluation PASS.
- FinMRAGBench: commit `f6522801e6abcd77f4d1d5f4bf6832ca4aa5566b`; có năm annotation files. README chính thức cho biết full annual-report corpus/source manifest còn chờ release. Vì vậy chưa thể coi đây là end-to-end retrieval corpus sẵn chạy; cần source reconstruction/access phù hợp trước.
- FinED-Bench: trang gốc trả HTTP200 qua network probe; browser reader chưa đọc được nội dung. Chưa xác nhận file data, schema hoặc oracle. Không coi việc mở được HTML là đã tải dataset.

Ưu tiên kế tiếp: **ARQA schema/context/oracle preflight, zero model calls**, đồng thời hoàn thiện recruitment và semantic review. Nếu scope/oracle không phù hợp, ghi STOP trước khi chọn nguồn khác; không chọn dataset từ model score hậu nghiệm.

Đã bắt đầu preflight này: tải đúng hai file theo pinned Git blobs, kiểm hash và đọc schema của400QA packs cùng560context records bằng SQLite immutable/query-only. [Preflight record](arqa_schema_preflight.json) lưu cấu trúc, counts và kiểm mapping. Đây mới là schema/linkage validation, chưa chứng nhận semantic oracle hoặc tạo benchmark score. Công việc tiếp theo là thẩm định scorer/answer normalization, cấu trúc evidence và split theo document/year trước bất kỳ generation mới nào.

##Cập nhật sau vòng02đã hoàn tất

ARQA source/preflight, registration và288realresponses đã xong; gateFAIL và có measurement flags quan trọng. Path mới nhất ở [oracle findings và quyết định](ARQA_CYCLE02_ORACLE_VA_PATH_TIEP.md). Không tiếp tục launch theo phần candidate cũ; cần source-only semantic review và discovery trước protocol mới.
