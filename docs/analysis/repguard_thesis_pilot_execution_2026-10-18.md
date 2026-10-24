# Nhật ký triển khai pilot đồ án RepGuard — 18/10/2026

**Mục tiêu:** kiểm tra bằng inference thật liệu reputation/history và chuyển giao
agent có lợi ích ngoài evidence-only và cascade cố định, trước khi chốt phương
pháp đồ án. Đây là development pilot; chưa có claim thắng baseline hoặc điểm số.

## Hạ tầng riêng

- App mới: `repguard-thesis-real-pilot-20261018`.
- App ID: `ap-H1QBQza7gdGhq4UhD8FZoe`.
- Model volume mới: `repguard-thesis-models-20261018`.
- Response volume mới: `repguard-thesis-runs-20261018`.
- Evaluation volume mới: `repguard-thesis-evals-20261018`, chỉ CPU evaluator mount.
- Ollama pin `0.40.6`; GPU quan sát thực: NVIDIA L4,23034MiB,driver610.57.04.
- Qwen3:8b digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
- Qwen3:14b digest `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`.
- Tải weights bằng CPU. Một GPU collector, tối đa200task requests; không dùng
  endpoint/model volume/app Ollama cũ. Không có mock provider.

## Khóa dữ liệu và quyền truy cập

FinQA TRAIN chính thức tại commit `0f16e2867befa6840783e58be38c9efb9229d742`,
SHA256 `49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6`.
100câu/100company-year reports, chọn bằng hash metadata;60history,
10calibration,10validation,20development screen. Giữ nguyên câu khó/boolean/
unsupported, không thay câu theo score. Loại normalized-question hash thuộc
FinQA headroom200 đã xem trước đó và hash trùng trong pilot.

Runtime allowlist chỉ có ID/report/question/table/pre_text/post_text. Không
truyền qa.program, gold_inds, model_input, exe_ans hoặc retrieval gold. Các check
local đã xác minh100visible cases và100lần chặn trường gold được chèn vào input.

## Sửa lỗi trước phân tích

Run v1 `ca72380557dad9ef0769a382` đã bị dừng chủ động: executor ban đầu làm tròn
sau mỗi bước; evaluator FinQA gốc giữ precision trung gian và làm tròn kết quả
cuối. Giữ source zip, packet, receipts, partial raw responses và lý do dừng tại
`results/thesis_real_pilot_v1/`. Không dùng responses v1 để thay thế responses v2.
Chưa fit learner hoặc đọc screen target để chọn sửa lỗi này.

Run v2 `359b8d464d5005b9c5d0f967` sửa prompt/executor đúng quy ước làm tròn cuối,
giữ cùng100question IDs, agents, token caps, partitions, controls và policy.
Call receipt CPU worker: `fc-01M56HN00METQTPXNYQFBBCCJZ`.
Đã đối chiếu56chương trình scalar tham chiếu HISTORY thực với executor gốc:
khớp56/56;4reference ngoài phạm vi bộ kiểm tra phần mềm được ghi riêng. Đây
là kiểm tra thành phần số học, không phải56phản hồi model hoặc56task mới được giải.

## Điều kiện báo kết quả

8calls thật đầu trên history là gate kỹ thuật không dùng gold: >=6JSON đúng
schema và >=1program thực thi có nguồn; GPU offload được kiểm bằng `/api/ps`.
Chỉ sau đủ200real responses mới train/evaluate và phát hành bảng kết quả.
Completed invalid/length-capped answers không retry để nâng score. Transport
failure có tối đa2initiated attempts, giữ unknown usage nếu không nhận response.

Các controls: AlwaysA,AlwaysB,GlobalGold,SkillGold,RawFeedbackSkill,
FixedCascade,EvidenceOnly,RepGuard. Learner logistic được huấn luyện từ solver
outcomes thực, reputation train được tính out-of-fold; calibration/threshold
không dùng20screen labels. Tất cả controls được cấp cùng full history gold;
không gọi đây là study10%audit. Policy replay trên outputs thật không phải thêm
inference; collection counterfactual cost phải báo riêng.

Chi phí token/request seconds chưa là billing USD. Coverage/precision phải đọc
cùng accuracy trên toàn câu hỏi. Source binding/operation checks chưa chứng minh
đúng ngữ nghĩa. Chỉ20screen questions nên CI rất rộng và chỉ exploratory.

## Tệp và vận hành

Mã/protocol/README tại `thesis_pilot/`; packet, receipts và raw artifacts tại
`results/thesis_real_pilot_v2/` bị Gitignore. Kiểm tra từ repository root:

```bash
./.venv/bin/python -m thesis_pilot.cli status
./.venv/bin/python -m thesis_pilot.cli fetch
./.venv/bin/python -m thesis_pilot.cli report
```

`report` chỉ chốt sau checksum và cloud/local recomputation khớp. Bảng cuối dự
kiến: `repguard_thesis_pilot_assessment_2026-10-18.md` và JSON tương ứng. Không
xóa receipt để chạy lại kết quả bất lợi; thay đổi phương pháp phải giữ version
cũ và khóa protocol/run mới.

## Pilot v2 hoàn tất

Đủ200responses; collection wall1.666,61s. Checksum và fitting/policy recomputation
local khớp cloud;100official reference programs khớp stored exe_ans; numeric
boundary audit không phát hiện hard-pass bị ảnh hưởng trong200outputs.

Screen20câu: AlwaysA0/20; AlwaysB1/20; FixedCascade/EvidenceOnly/RepGuard1/20.
RepGuard dùng40calls so với20calls củaB; gateFAIL. Giữ nguyên kết quả. Đây là
khả năng của cấu hình đang thử, không chứng minh năng lực nội tại model hoặc
reputation nói chung. Chi tiết và giới hạn trong bản decision/assessment.

Thêm backend `LiveOllama` trên cùng app mới, L4,max_containers1,scaledown60s;
GPU live chỉ mount model volume. Có giao diện localhost:8765 và JSON upload,
chưa có PDF extraction. Các nhánh contract mới không dùng calibrator v2.

Hai đợt chẩn đoán history16+16calls và probe typed8calls đã xong, nguồn/outputs
riêng và source snapshots kiểm hash khớp. Typed-demo thật trênDISH/2008 cho
69.064% từ256917/371999, mộtcallB, không current gold hoặc cached answer.
Các lỗi demo cũ (double percentage và chép thêm currency symbol) vẫn giữ lại.

Một kiểm tra cuối8history calls với native thinking/4096output tokens có
protocol/source/run riêng. Không so ngang budget với1536tokens, không dùng
screen để tune, không gọi là reputation gain. Kết quả và trạng thái bàn giao
cuối được ghi ở `repguard_delivery_verification_2026-10-18.json` sau khi hoàn tất.

## Bàn giao cuối

Native thinking đã xong8/8:7/8source-bound executable,2/8đúng target và qua check;
actual thinking có trong8/8response,11.110output tokens. Bản không thinking:
6/8source-bound executable,2/8đúng và qua check,1.553output tokens. Không có
gain accuracy trong mẫu history này; không chốt native thinking mặc định.

Kiểm tra bàn giao đã PASS:200responses pilot và48responses follow-up;
4source snapshots follow-up khớp hash; executor replay local khớp từng output;
same public messages giữa hai typed configurations. Bốn lượt UI thực tế gồm
5model calls, giữ cả failures trước sửa. Typed demo69.064% khớp phép tính đối
chiếu thủ công. Bảnv1hủy có7complete responses trong checkpoint và1initiated
unresolved; usage của request chưa rõ không được tự gán bằng0.

App mới vẫn được deploy, live class idle scale xuống0 theo cấu hình; không gọi
inference lên app Ollama cũ. Không có billing USD đã xác minh; không gọi token/
request seconds là tổng hóa đơn. Không chạy thêm model study sau bàn giao.
