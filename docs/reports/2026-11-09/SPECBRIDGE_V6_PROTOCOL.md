# V6 — native SQL development pilot, khóa trước model calls

Sau qualification45development tasks/90references:90ownmatches,90opposite-reference rejections và90extra-row/90missing-output controls PASS. Dùng đúng sqlean.py0.21.5.3/SQLite3.42.0: SQLite hệ thống3.51.0 không khớp native grading ở cả hai references của task1486e0d33f. Không sửa reference hoặc loại task đó để làm điểm đẹp.

## Phạm vi và selection

Lấy12task development bằng metadata choice-type và hash, bốn task mỗi database (financial/alien/chinook). Rare-choice coverage trước, hash-fill sau; không dùng model outcomes/reference SQL để chọn. Cả specific_A và specific_B cho mỗi task:24specified cases. Không mở validation67/reserve92. Đây là native producer/review readiness và error bank; không là confirmation, không đánh giá hiệu quả checker V5 hoặc một thuật toán mới.

Các query tham chiếu phần lớn dùng CTE/arithmetic. Checker flat-SELECT V5 không được ép để chấm những query đó. Native execution/official grading là chuẩn đọc kết quả của pilot này; source/operator verification sẽ cần qualification riêng trước một method experiment.

## Arms và tài nguyên

A=Qwen3.5:27b, B=Gemma4:26b-a4b-it-q4_K_M với digests đã dùng. A/B direct mỗi case một model call; AA/BB self-review và AB/BA cross-review thêm đúng một call trên **draft thật**. Cùng original specified question/schema/docs và actual draft SQL/rawresponse/execution state/8-row preview. Không có score, answer labels hoặc reference SQL trong review input; identity model trước bị ẩn.

144calls thực tối đa:24cases×6workflows. Cached draft phải tính trong chi phí từng policy; direct1call, mỗi review policy2calls. Ollama0.40.6/L40S,temperature0,seed20261109,thinkfalse,context32768/output8192. Cùng ceilings không là cùng tokens/dollars/compute thực. Mọi schema/format/SQL failures được giữ và chấm như task chưa đúng; không có extra generation để sửa format. Provider/transport/integrity exception STOP, không retry generation mù.

Đầu ra JSON chỉ có SQL; không yêu cầu model tự gõ bảng. Executor lưu complete relation tối đa10000rows/20MiB, không coi preview là đáp án đầy đủ. SQL read-only, function whitelist và time budget60s. SQLite3.42 được kiểm ngay trong runtime.

Gemini3.8Flash synthetic probe timeout120s, provider outcome chưa rõ; không gửi corpus và không retry. Frontier commercial baseline còn thiếu, nên pilot không thể chứng minh thắng strong frontier. Hai model hiện tại là development controls.

## Cách ly và audit

Modal app riêng, weights read-only. CPU chỉ có ba source databases public và code `__init__.py/runtime.py/worker.py`; GPU chỉ weights và ba runtime files. Automatic source inclusion tắt. Không mount grader/reference/evaluation packages. Hash/membership/SQLite version checks trước inference; lưu attempt trước request, response/actual payload/model digest/GPU/counters và actual parent digest.0automatic generation retries.

Chấm offline bằng pinned native grade/matches functions đã kiểm source; tái chạy SQL trên cùng source/engine để audit execution. Kiểm đủ144trajectories/attempts/responses, actual parents, prompt bytes/options và model/GPU identities trước aggregate. Raw scores/failures giữ nguyên; mọi sửa prompt/runtime phải là đăng ký/run khác.

## Readout và quyết định

Báo taskwise specified interpretation correctness, invalid/SQL/length failures, rescues/harms, actual tokens/time và policy cost gồm draft. Phân biệt12task với24request variants/144outputs; ba DB là ba source clusters. Cross−self mô tả, không lấy144outputs như144quan sát độc lập để tuyên bố significance. Đọc cả hai cách hiểu để kiểm model có đổi theo yêu cầu hay mặc định một cách.

Scientific/history expansion gate **NOT_OPENED**, bất kể point estimate. Nếu native solving vẫn floor, sửa harness/baseline trên development trước. Nếu source/meaning choices gây lỗi và có utility/headroom sau self-review, mới khóa mechanism experiment có same-checker, neutral/shuffled feedback và baseline mạnh. Không dùng vòng lặp chạy đến khi p<0.05; phát triển trên dev, xác nhận một lần với dữ liệu giữ riêng sau khi thiết kế/power analysis đủ điều kiện.
