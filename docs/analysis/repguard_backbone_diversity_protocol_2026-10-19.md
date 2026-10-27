# Kiểm tra độ bổ sung tự nhiên giữa hai backbone

Run `63bb59fcde70e2533c1d242a`, 16 báo cáo development mới so với 124 báo cáo
của các LIVE cohorts trước. IDs lấy từ 16 phần tử đầu của development split
đã giữ riêng theo hash metadata; không chọn theo model sai/đúng. Không dùng
150 confirmation reports. Chưa xác lập report-disjointness với archive
RouterBench chỉ có origin_query hashes; không gọi đây là globally unseen test.

Mục đích: kiểm việc thay model thật, thay vì đổi tên vai trò cùng model, có tạo
được năng lực bổ sung đáng khai thác không. Đây là probe về điều kiện của pool,
không là phương pháp reputation đã triển khai hoặc xác nhận superiority.

- Qwen3 8B và 14B có weights/digests đã pin từ đợt trước; không tải model mới.
- Mỗi model giải đủ16câu, cùng source đầy đủ, prompt PoT, native thinking,
  cap4096, context16384, temperature0, seed19102026, executor/canonical readout.
- Thu hết16câu 8B rồi16câu 14B để chỉ đổi weights một lần, không stop theo chất
  lượng. Cùng cap token không mặc nhận bằng compute hoặc latency.
- Cap32 real calls, collector5400giây, một L4. Mỗi call lưu initiated trước
  request; chưa rõ kết quả thì không retry âm thầm. Không quality retry/mock.
- App nghiên cứu thứ hai `repguard-thesis-backbone-probe-20261019`, ID
  `ap-oxSrIRlGvzvy6zOfdvHV5R`; chỉ mount weights volume. Không deploy lại app
  batch composition đang chạy và không dùng app Ollama cũ của người dùng.
- Gold chỉ dùng khi analyze sau đủ32responses. Inference nhận đúng6public
  fields; không qa/program/gold_inds/targets. Giữ exact FinQA round5 và không
  oracle scale matching. Invalid tính sai, không dùng gold fallback.

Gate trước inference: union≥best-fixed+2 và mỗi model có ít nhất một câu đúng
riêng. Gate chỉ sàng headroom, không bảo đảm có tín hiệu để học router. Nếu
không qua thì không mở rộng thu history với lý do "đã chứng minh diversity".
Nếu qua, vẫn cần scoped repair/actions, learned current-state-only control và
đánh giá mới trước chốt đóng góp reputation.

Nguồn, prompts, source snapshots, timestamps, raw native responses và kết quả
nằm trong `results/thesis_backbone_diversity_probe_v1/`. Kiểm độc lập bằng
`verify_backbone_probe.py`; script này chỉ đọc dữ liệu thật đã lưu, không gọi
model. Mỗi question/report mới là đơn vị phân tích, không coi32calls là32task.
