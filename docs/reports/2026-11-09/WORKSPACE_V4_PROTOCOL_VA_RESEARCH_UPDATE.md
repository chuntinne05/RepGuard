# Vòng04 — workspace thật, oracle nguồn và pilot kỹ thuật có kiểm soát

Viết trước model inference của vòng này, sau source-only preflight. Đây là phần tiếp của kế hoạchV3, không thay kết quả/gateFAIL của vòng01/02. Mục tiêu là kiểm pipeline trên công việc nhiều nguồn và tạo error bank thật; chưa là thí nghiệm xác nhận novelty hoặc khả năng tổng quát.

## Amendment vận hành, ghi riêng sau launch

- Plan đầu `c83c5fa198c76cce65a9c5d4`, app `ap-KTItFFeus4WbSgWP1m81tk`: guard phát hiện Modal tự đưa cả source package vào runtime, có `preflight.py`. Dừng trước `collect`/khởi tạoGPU/invoke:0corpuscalls, không có score. Giữ registration/source ZIP/launch receipt; không xóa lần lỗi.
- Plan packaging2 `6a325835a376d02f1440fadf`, app `ap-pniE5GsCV9BuWKCVcxYhZu`: tắt automatic source inclusion, chỉ bốn runtime files; isolation receipt PASS. Hai task đầu hoàn thành12trajectories/42responses; dừng trước inference task380vì logical data fingerprint không khớp. Đối chiếu local/remote tìm8rows ở2bảng task380, chênh1ULP khi các bản SQLite chuyển chuỗi thập phân sang REAL. Không nới fingerprint hoặc làm tròn để che khác biệt.
- Recovery3 `3af22795afdac39d725c3351`, app `ap-lPZqlWFErGrT9KOYgCl8jM`: bind numeric text thành Pythonfloat/int trước SQLite; kiểm tất cả bốn workspace trước bất kỳ inference mới. Chỉ chạy `task_380,task_371,task_44,task_35`, cap128calls; không chạy lại hai task đầu. Đăng ký recovery trước khi chấm outcomes của42calls. Source/model/prompt/call ceilings giữ như protocol, adapter amendment ghi rõ.31tests tools/trajectory/offline receipts PASS trước launch.
- Vì vậy original six-task plan **interrupted**, không được báo completed hoặc một confirmatory score. Báo hai task prefix và bốn task recovery riêng; bảng gộp sáu task chỉ là engineering diagnostic dưới hai adapter versions. Tổng corpus calls tối đa42+128=170. Source-only task391amendment vẫn áp dụng ở prefix.
- Offline evaluator nằm ngoài frozen runtime tại `research_ops/workspace_v4_evaluate.py`. Prefix chỉ được chấm diagnostic nếu đúng exception adapter đã ghi, toàn bộ prefix đủ6arms/task và không có response/attempt rơi ngoài prefix; không xuất primary contrast cho interrupted plan. Recovery chỉ chấm khi hoàn tất và audit PASS.

## Điều đã hoàn tất trước launch

- Tải đúng archive DataSpace tại HF revision `96be19257d7aa251dbce4771d46a26fc36f6dc52`,2.878.651.222bytes, kiểm full SHA256 `68f221fafcf0b50396eca55f8298af1ad73d586a6cac6995916afca535a560af` PASS trên CPU.
- Lấy đủ96input files của6task đã chọn bằng metadata từ lượt trước;12gold/config files ở volume khác. Check membership đúng manifest và108downloadedfile hashes PASS. Không mở model outputs của benchmark.
- Tạo SQL convenience view từ originalSQLite/CSV/recordJSON, có metadata source/hash cho từng bảng. Cả6workspace không có structured file bị bỏ qua. Table names trùng được giữ thành aliases riêng; không gộp bản ghi hoặc chọn một nguồn thắng.
- PDF được đọc text theo page bằng PyMuPDF2.1 trong thư mục dependency tạm, ngoài virtualenv hiện có. Đã render và xem các trang4/9/10 cần cho source reconstruction task35. Không tự coi text extraction là giữ đủ layout của mọi PDF.
- Source-only reconstruction viết và khóa trước khi mở nội dung gold/config:5/6khớp official scorer. Task391thiếu cột ngày dù phần bốn khoản tiền cùng đúng số cột yêu cầu trực tiếp.
- **Sửa đổi development công khai:** task391thêm câu yêu cầu rõ ngày của bản ghi, sau đó đến bốn khoản tiền. Reconstruct từ source lại với ngày khớp reference. Giữ nguyên bản5/6, không sửa gold. Bộ sáu input có sửa một câu **không phải điểm official-original DataSpace**. Không có human adjudication mới.
- Official pinned scorer chỉ được chạy offline sau đọc code/kiểm SHA.12controls qua:6goldself-match và6extra-row rejection. Đây là kiểm evaluator, không là độ đúng model. [Original preflight](workspace_v4_oracle_preflight.json), [amendment](workspace_v4_readiness_amendment.json).
-24tests cho runtime/trajectory PASS, gồm read-onlySQL, path escape/symlink, extension/file access, dữ liệu lớn xuất đủ, giữ leading-zero codes, parent artifact reuse/tamper và no-blind-generation-retry.

## Câu hỏi và cấu hình pilot

Sáu task: `task_269,task_391,task_380,task_371,task_44,task_35`. Đây là6tasks/4coarse source families, không là6domain độc lập: hai task fund và hai task macro có liên quan schema/source. Task371có reference12.962rows; export CSV từ query giữ đủ kết quả, không ép LLM viết lại toàn bộ bảng.

Hai backbone thực tế A=Qwen3.5:27b, B=Gemma4:26b-a4b-it-q4_K_M, pinned digests như các lượt phục vụ trước; L40S/Ollama0.40.6,temperature0,seed20261109,thinkfalse,context32768/output2048. Weights read-only; app/volume riêng, không invoke deployment cũ.

Gemini4Argon có trong model list nhưng synthetic diagnostic trảHTTP429,free-tier quota0. Hai requests synthetic được ghi riêng; request đầu chỉ ghi HTTPError nên không suy trạng thái generation/billing chắc chắn. Không gửi corpus, không auto retry hoặc đổi billing. Vì vậy **frontier strong-single còn thiếu**; không dùng hai backbone hiện tại để nhận đã thắng frontier baseline.

Các workflows A,B,AA,BB,AB,BA; direct tối đa8calls, review tối đa4calls thêm. Cả self/cross nhận cùng câu hỏi, catalog/source tools, actual draft, tool observations/messages và actual exported artifacts; identity model trước bị ẩn. Review có thể giữ artifact cũ hoặc tạo bản mới; không bịa một trajectory counterfactual từ score cũ.

Tools: catalog, schema, bounded read/search, read-only query và save_table. Query artifact ghi SQL, source files/hashes và output hash; execution không chứng nhận task semantics. save_table được ghi rõ agent assertion. SQLtool không shell/Python arbitrary, network,ATTACH/write/extension hoặc gold access. Đây là một adapter variant có tiện ích tập trung structured sources; không là exact reproduction của harness DataSpace gốc.

**Cap192model calls thực**:6×(2×8 +4×4). Self/cross policy có cùng ceilings12calls gồm initial; draft được reuse nhưng phải tính chi phí draft cho mỗi policy khi báo số liệu. Token stop-check dựa counters sau mỗi non-final response; hard ceilings theo call/context/output. Không gọi đây là equal realized tokens, dollars hoặc compute. Báo lượng dùng thực và serving time riêng.

Transport/provider/integrity exception dừng worker, không retry started request. Tool/schema error được trả thành observation, tiêu tốn bước mới. Final chỉ nhận result_id đã có thật trong trajectory/parent, output được check hash. Bất kỳ unknown provider outcome phải review receipt trước resume.

## Đo gì và không được suy gì

Offline: complete relation equality theo pinned scorer, cùng config ở mọi arm; invalid/missing/abstain là task chưa hoàn tất. Báo nguyên từng task, input amendment, tool errors, source/execution lineage, rescues/harms và chi phí actual gồm draft. Paired balanced cross−self chỉ là mô tả ở6task; không bootstrap6case thành scientific superiority.

Scientific expansion/history gate **chưa mở**, bất kể point estimate của pilot. Chưa có user study hoặc human adjudication mới. Một output đúng relation không chứng minh reasoning, source attribution hoặc clinical/financial suitability. Một output sai shape không tự chứng minh sai nghiệp vụ. Không tối ưu prompt theo kết quả rồi gộp lại với run đã khóa.

Sau pilot: nếu runtime/format floor thì sửa adapter và mở run khác minh bạch; nếu có lỗi source/scope thật và action utility, mới thiết kế một mechanism experiment với comparator single+cùngchecker/tools/budget, labels độc lập và source/workload-held-out confirmation. Không tự mở thêm nhiều calls từ kết quả thuận lợi của task riêng lẻ.

## Hai cập nhật literature làm thay đổi comparator

- [Beyond fabrication v2,31/10](https://arxiv.org/abs/2610.38691), repo pin `8284de5cf99c6a89320315b9f954c7b3ad0eb07e`06/11. README mới phân biệt256labelled items với211evaluable claims sau45settings/extraction exclusions; raw submission workspaces không nằm trong repo dẫn xuất. Vì vậy chưa thể coi đây là256task end-to-end sẵn chạy. Đọc manifest/README; không tải human-label files hoặc cached verifier outcomes để chọn sample/method. Source ownership/decoy-based provenance đã có, không là novelty của kernel.
- [ContractBench](https://github.com/SecurityLab-UCD/ContractBench), pin `44858abacaa9291fd8ae7f3c5c23b5911270d836`04/11, đọc README camera-ready/scope/feedback qualifications. Đã kiểm validity/integrity của observation contracts bằng server logs. Correct-label repair không tách được khỏi neutral/wrong-label control trong probe của họ; generic feedback gains không đủ chứng minh diagnostic specificity. Nếu đồ án thêm verifier feedback phải có same-info/neutral or shuffled-feedback controls. Không nhận validity checks, contract preservation hay generic repair là method mới.

Những cập nhật này làm tiêu chuẩn chặt hơn: chứng minh lợi ích riêng của cơ chế ở cùng information/resources, và đo khả năng hoàn thành task thực. Không tìm một tên mới cho provenance/checker đã có.

## Tái lập phần phân tích offline

Không chạy lại launcher để tái lập điểm; inference receipts đã lưu. Source snapshots của từng registration nằm trong `results/workspace_v4/frozen_source*.zip`. Dùng đúng archive của block cũ vì file làm việc đã sửa cho recovery.

```sh
# Chỉ diagnostic của prefix đã hoàn tất; original six-task study bị interrupted.
PYTHONPATH=. .venv/bin/python -m research_ops.workspace_v4_evaluate \
  --plan results/workspace_v4/registered_plan_packaging2.json \
  --run-root results/workspace_v4/runs/6a325835a376d02f1440fadf \
  --source-archive results/workspace_v4/frozen_source_packaging2.zip \
  --interrupted-prefix task_269 task_391 \
  --output /private/tmp/workspace_v4_prefix_recheck.json

# Chỉ chạy khi recovery đã hoàn tất và artifacts tải đủ.
PYTHONPATH=. .venv/bin/python -m research_ops.workspace_v4_evaluate \
  --plan results/workspace_v4/registered_plan_recovery3.json \
  --run-root results/workspace_v4/runs/3af22795afdac39d725c3351 \
  --source-archive results/workspace_v4/frozen_source_recovery3.zip \
  --output /private/tmp/workspace_v4_recovery_recheck.json
```

Evaluator từ chối overwrite output, partial corpus hoặc unknown provider exception. Raw results là dữ liệu local bị gitignore, không tự xuất bản source/reference files. Bản phân tích gộp phải dùng `research_ops/workspace_v4_error_bank.py`, không ghép primary contrast của hai block thành confirmatory result. [Đối chiếu literature bổ sung và câu hỏi nghiên cứu](WORKSPACE_V4_LITERATURE_VA_RESEARCH_QUESTION.md).
