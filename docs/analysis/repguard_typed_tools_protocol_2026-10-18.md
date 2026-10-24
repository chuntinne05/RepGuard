# Typed financial tools: prototype feasibility, 18/10/2026

Sau pilot 200 calls và hai chẩn đoán 16+16 calls history, phát hiện các lỗi lặp
lại: model chép sai token tiền tệ, gắn sai source ID, chọn số/phép toán sai,
nhân100 rồi tiếp tục hiển thị như fraction-percent. Giữ nguyên mọi kết quả cũ.

Triển khai một nhánh prototype mới, không thay chủ đề multi-agent/reputation:

- Phần mềm lập catalogue các numeric span thực trong tài liệu, có ID, token,
  giá trị và context hàng/cột/văn bản. Model chỉ chọn ID, không chép lại số.
- Model chọn một operation có kiểu: lookup, sum, difference, ratio, percent_of,
  growth_percent, average, max, min, greater. Executor tính và hiển thị đơn vị.
- percent_of/growth_percent do công cụ chuyển từ fraction sang phần trăm đúng
  một lần; không có constant100 hoặc chương trình tùy ý do model điều khiển.
- Giới hạn: chỉ một operation/những template này; từ chối câu nhiều bước chưa
  hỗ trợ, không loại câu đó khỏi mẫu. Kiểm tra cơ học vẫn không chứng minh đã
  chọn đúng số/ngữ nghĩa. Nhánh này chưa có reputation/calibrator đã huấn luyện.

Kiểm tra trước khi chốt hướng: **8 calls thật, cùng B Qwen3:14b, cùng 8 câu
history đầu như các chẩn đoán**, think=false,temp0,seed18102026,1536 output
tokens,num_ctx16384. Không dùng screen, không đổi câu theo chất lượng, không
retry câu sai. Gold chỉ dùng local sau thu thập; report exact exe_ans giữ nguyên,
không factor100 oracle. Mọi cờ ambiguity từ dữ liệu history vẫn giữ riêng.

Lưu plan/hash/source zip, intent và raw response ở
`results/thesis_typed_tools_probe_v1/`. Có tối đa một lần demo riêng trên tài
liệu DISH/2008 đã dùng trước để kiểm chứng luồng UI/phần trăm. Demo không phải
đánh giá độc lập. Không áp calibrator v2 cho nhánh mới, không tự động chạy thêm
nghiên cứu lớn/model search sau 8 calls này.
