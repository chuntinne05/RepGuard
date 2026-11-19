# Vận hành thực nghiệm neural DART trên Modal

**Kết quả cuối 11:34:31 ngày 05/10/2026 (UTC+7): P0 hoàn tất 5/5, dừng đúng
gate `stopped_p0_gate`; P1 không chạy.** Selected = Global = 82/168.
Xem [báo cáo đầy đủ](dart_neural_p0_assessment_2026-10-05.md).

## Phạm vi

Thực thi [protocol P0/P1](dart_neural_p0_p1_protocol_2026-10-05.md).
Đây là huấn luyện và đánh giá router thật trên kết quả thực thi AppWorld đã có;
không phải chạy lại 2.352 lượt solver, không phải tạo nhãn mô phỏng.
Các dữ liệu synthetic trong `neural_smoke.py` chỉ là unit test phần huấn luyện.

- App: `repguard-neural-p0p1-v1`
- Volume: `repguard-neural-checkpoints-v1`
- Worker: CPU 2 cores, RAM 8 GiB, timeout 24 giờ mỗi invocation, tối đa 2 retry.
- Encoder: MiniLM frozen, revision cố định trong protocol; 168 instruction được
  chia chunk nếu dài, không cắt mất phần cuối.
- Run ID: `32fc82877693697cb45f7d49`.
- Call ID: `fc-01M45584KJPXN09X5RV5863V80`.
- Commit khóa protocol/code trước kết quả: `9d1f79b`.

Kiểm chứng ban đầu: 6 test cục bộ đạt, gồm crash/resume và dừng theo gate;
test PyTorch cục bộ được skip vì không
cài torch trên laptop, sau đó cả ba head đạt kiểm tra deterministic, synthetic
rescue và constant-control trong image Modal. Toàn bộ 300 audit case tái tạo
đúng agent choices và success của UniformAuditGlobal cũ. Embedding thật đã đủ
168 × 384; instruction dài nhất 114 tokens, tổng 168 chunks.

Lúc 11:32:03 ngày 05/10/2026 (UTC+7), cloud đã hoàn tất 1/5 fold P0 và đang fit
fold 1, sau khi process submit trên laptop thoát thành công. Đây là bằng chứng
job vẫn tiến triển sau khi ngắt sự phụ thuộc vào process local. Trạng thái mới
nhất xem từ lệnh `status` bên dưới, không dùng mốc trong tài liệu như số liệu live.

## Không phụ thuộc vào phiên Codex

App được deploy trước, sau đó gọi `Function.from_name(...).spawn(packet)`.
Lệnh submit chỉ gửi job và lưu receipt, rồi thoát. Job tiếp tục trên cloud khi
Codex hết lượt hoặc laptop sleep. Không cần giữ terminal, watchdog trên laptop,
Ollama cũ hoặc kết nối mạng laptop trong suốt thời gian huấn luyện.

Modal có thể gặp lỗi dịch vụ, worker hết timeout hoặc bị stop thủ công. Vì vậy
đây không phải bảo đảm chạy vô hạn. Mỗi case hoàn tất và embedding được lưu
atomically rồi commit vào Volume. Retry cùng input/hash bỏ qua case đã hoàn tất.
Không đổi code/protocol giữa một run; thay đổi sẽ tạo run ID khác.

Theo [hướng dẫn job queue của Modal](https://modal.com/docs/guide/job-queue),
deployed function với `.spawn()` phù hợp với công việc bất đồng bộ này.

## Kiểm tra và lấy kết quả

Từ thư mục project:

```bash
.venv/bin/python run_dart_neural.py status
.venv/bin/python run_dart_neural.py fetch
```

Kết quả tải về `results/dart_neural_v1/cloud/`, gồm:

- `status.json`: trạng thái bền vững và thời điểm cập nhật UTC.
- `self_test.json`: kết quả kiểm tra PyTorch trong chính image dùng chạy thật.
- `environment.json`: các phiên bản thư viện chính.
- `embeddings_private.json`: embedding và số token/chunk mỗi instruction.
- `p0_fold*_seed0.json`: lựa chọn agent, inner folds, số nhãn, hyperparameter.
- `p0_analysis.json`: tất cả mô hình, so sánh paired, bootstrap CI và gate.
- Nếu P0 đạt: các case P1 và `p1_analysis.json`.

`results/` không được commit vào Git; báo cáo tổng hợp mới đưa vào docs.
Để xem log: `.venv/bin/modal app logs repguard-neural-p0p1-v1`.

Chỉ xác nhận tiến triển khi số instruction/case đã lưu hoặc bước fit thay đổi;
không suy ra tiến triển từ một container còn sống.

## Dừng tự động theo bằng chứng

1. P0: đủ nhãn lịch sử của outer train, 5 outer folds, inner CV theo generator.
2. Nếu Selected không có CI lower > 0 so với Global: `stopped_p0_gate`.
   Đây là hoàn tất phép kiểm tra với kết quả không đạt, không phải crash.
3. Nếu đạt: tự chạy P1 với 3 ngân sách × 20 audit seeds × 5 folds = 300 case.
4. Kết thúc P1: `completed_p1_review_required`, lưu cả thắng và thua. Không tự
   đổi thuật toán/tune tiếp sau khi thấy kết quả để tìm một con số đẹp.

Lệnh `.venv/bin/python run_dart_neural.py submit` có kiểm tra receipt để tránh
gửi trùng khi call trước vẫn chạy hoặc đã hoàn tất. Nếu call trước thất bại và
đã điều tra, dùng `submit --resume` với nguyên packet/code để tiếp tục checkpoint.
Không xóa receipt nhằm ép chạy lại một kết quả đã dừng theo scientific gate.

## Diễn giải

P0 là diagnostic dùng 100% nhãn train; không dùng nó để tuyên bố thắng phương
pháp chỉ có 10% nhãn. P1 mới là so sánh cùng audit budget. Cả hai vẫn là phát
triển trên public normal đã được nghiên cứu nhiều lần; kết quả dương chưa thay
thế một benchmark độc lập và chưa chứng minh DART hoàn chỉnh.
