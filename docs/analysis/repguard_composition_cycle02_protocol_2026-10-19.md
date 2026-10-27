# Vòng 2 — kiểm tra giá trị phối hợp trước khi học reputation

Đóng băng trước phản hồi mới đầu tiên. Run `9fc4557bcf3505242c0f32e6`;
protocol máy đọc và timestamp nằm trong `results/thesis_composition_cycle_02/`.
Đây là development có lặp lại, không phải final test.

## Câu hỏi và đối chứng

Một phép tính có thể sai dù một số fact thành phần đúng. Vòng này kiểm tra xem
đọc và đối chiếu hai lời giải có tạo ra đáp án mới hữu ích hơn một agent được
phép tự kiểm tra hai lần hay không. Không giả định kết hợp luôn có ích.

Giữ toàn bộ 24 báo cáo development vòng 1, mỗi báo cáo một câu. Không chọn riêng
câu sai hay câu có khả năng sửa. Hai output cha là PoT và initial DSL thật đã lưu.
DSL dùng cùng unit pass đã công bố; PoT dùng cùng canonical whitespace/readout.
Mọi nhánh mới có cùng tài liệu, system prompt kiểm metric/kỳ/scope/unit/sign,
AST interpreter, native thinking, cap 4096, temperature 0 và seed 19102026.

| Nhánh | Thông tin và thứ tự |
|---|---|
| direct PoT | Một output cha thật; không phát sinh call mới |
| self_review_1 | Đọc lại tài liệu + PoT + kết quả chạy chương trình |
| self_review_2 | Đọc lại tài liệu + output self1 đã được chấp nhận cơ học |
| compose | Đọc lại tài liệu + PoT + lời giải DSL và numeric source contexts |

Self1/self2 được cấp cùng checklist như compose. Compose có quyền tạo chương
trình mới, không chỉ bỏ phiếu/chọn nguyên đáp án. Chương trình invalid giữ
current proposal. Không dùng gold để gọi agent, chấp nhận sửa hay chọn output.
Không đưa native hidden thinking của call cha vào prompt call con.

## Ngân sách và giới hạn suy luận

72 calls mới = 24 × 3; một worker L4, tối đa 7200 giây collector. Lưu trạng thái
initiated trước từng request. Request chưa rõ kết quả không được retry âm thầm.
Không retry vì câu trả lời sai, không model mock. Chỉ app nghiên cứu riêng
`repguard-thesis-real-pilot-20261018`, model qwen3:14b với digest đã pin.

Ngân sách triển khai phải tính cả output cha, dù collection tái sử dụng cache:
compose có 3 calls, cap tổng 1536+4096+4096; self2 có 3 calls, cap tổng 3×4096;
self1 có 2 calls. Đây là so cùng số calls với self2, không mặc nhận bằng compute
thực tế. Báo input/output tokens và thời gian Ollama eval riêng; đây không phải
billing. Giữ cả baseline 1-call/2-call để tránh che chi phí thêm.

Đánh giá chỉ sau collection: FinQA exe_ans, final round5, không thử ×100 để
khớp gold. Lỗi/ambiguity nhãn đã biết giữ nguyên score chính và được ghi riêng.

## Gate cố định

Chỉ cân nhắc fit history cho pool này nếu cả hai điều kiện thỏa:

1. Oracle union của direct/self1/self2/compose hơn best fixed ít nhất 2 câu.
2. Compose cứu ít nhất 2 câu mà self2 sai.

Oracle chỉ đo khả năng của pool, không là thuật toán triển khai. Qua gate cũng
chưa chứng minh học reputation sẽ khai thác được headroom. Không qua gate thì
không tune một controller khác trên cùng pool. Mọi ứng viên tiếp tục phải được
khóa và kiểm trên report mới, với learned routing/no-history và cost controls.

## Khả năng tái lập

Source snapshots, parent response hashes, protocol và receipts nằm trong thư mục
run. Không sửa bảy file primary pilot cũ, không đổi score vòng 1. Class Modal
mới được bổ sung vào app nghiên cứu riêng, giữ class cũ; không đụng app Ollama
cũ của người dùng. Gold không nằm trong volume inference.

Vòng này chưa triển khai learner reputation, không phải tái lập nguyên bản
MoCA-Agent và không tạo bằng chứng novelty hay superiority độc lập.
