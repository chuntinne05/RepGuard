# Tiếp tục pipeline và kiểm tra cơ chế — 04/10/2026

## Sự cố đã kiểm chứng

Full collection dừng ghi sau record 1.707 lúc 17:38:02 giờ Việt Nam; record tiếp
theo xuất hiện lúc 21:45:44. Khoảng trống 4 giờ 8 phút làm ETA trước đó không còn
đúng. Log có lỗi `Modal request retries exhausted`. Controller tự chuyển sang
collector attempt 2, tạo lại container Modal và resume từ index 1707. Không có
bằng chứng đủ để khẳng định sleep máy là nguyên nhân gốc; transport status cụ
thể của mọi retry chưa được lưu. Không gọi thời gian này là suy luận liên tục.

Tại kiểm tra 22:15, ledger đã tăng đến 2.177/2.352, 100% record lúc đó có response
đúng schema. Tình trạng này không xác nhận judge chấm đúng nội dung. Trạng thái
live nằm trong `results/dart_modal_judge_v1/status.json`.

## Bước tiếp theo đã thực hiện

1. Triển khai analyzer post-run riêng, bắt buộc có đủ full matrix và replay.
   So feedback trên cùng task–agent, kiểm tra control bất biến, phân tích lỗi
   ước lượng giá trị policy và giới hạn candidate/generalization.
2. Dùng outcome self-report đã hoàn tất để kiểm tra analyzer: đã tái dựng đúng
   toàn bộ action test được lưu từ candidate bank. Không dùng gold diagnostic
   để thay action hoặc điểm của phương pháp.
3. Triển khai và chạy một ablation đã khóa: audit theo task, giữ đúng B nhãn.
   Hoàn tất 300 tổ hợp / 1.200 audit-policy runs với self-report. Không gọi solver
   hoặc model judge mới trong bước replay này.
4. Controller follow-up đã khởi động, chờ full replay cũ hoàn tất rồi tự chạy
   diagnostics → ablation tương tự trên real judge → báo cáo tổng hợp.
5. Toàn bộ test suite: **233 passed, 70,38 giây**.

## Chẩn đoán self-report tại audit 10%

| Method | Đúng thực /168 | RMSE value trên selection history | Giá trị ước lượng cao quá mức ở policy được chọn |
|---|---:|---:|---:|
| AuditOnly | 62,85 | 0,15867 | +0,28519 |
| RandomHistory | 64,40 | 0,13033 | +0,19547 |
| UncertaintyHistory | 65,50 | 0,11808 | +0,18494 |
| DART đầu tiên | 55,50 | 0,20229 | +0,42792 |
| DARTContrast | 67,40 | 0,11365 | +0,15703 |

Đây là bằng chứng mô tả phù hợp với lỗi lấy max nhiều ước lượng nhiễu. DART bản
đầu có 24/100 lần policy được chọn có estimate ngoài [0,1]; DARTContrast 0/100.
Ước lượng Horvitz–Thompson có thể vượt [0,1] mà không phải bug, nhưng tối đa hóa
nó có thể chọn phương án quá lạc quan. Không suy từ unbiasedness của một policy
cố định ra unbiasedness của policy được chọn bằng max.

Nếu được cấp toàn bộ gold của selection history để chọn trong cùng bank, điểm
test diagnostic là **74,35/168**. Nếu chọn cả candidate bằng gold của chính test
fold, diagnostic là **89,60/168**. Cả hai không phải score triển khai của DART.
Khoảng cách giữa chúng cho thấy còn vấn đề generalization/khác biệt history–test,
ngoài sai số do lấy ít audit. Chưa phân rã nhân quả được các thành phần này.

## Kết quả ablation lấy mẫu theo task

Mỗi task được chọn sẽ kiểm chứng tất cả 14 agent; phần dư cuối lấy một tập agent
ngẫu nhiên để dùng đúng B nhãn. Tính marginal và joint inclusion được kiểm tra
bằng liệt kê mọi mẫu trên ma trận nhỏ. Công thức phương sai dùng toàn bộ residual
chỉ phục vụ diagnostic; không phải confidence bound có thể dùng khi deploy.

| Method | 5% | 10% (chính) | 20% |
|---|---:|---:|---:|
| PairedAuditOnly | 64,60 | 63,35 | 66,80 |
| PairedHistory | 63,85 | 65,85 | 64,85 |
| PairedGlobal | 62,15 | 71,95 | 76,70 |
| PairedKNN | 62,25 | 70,45 | 73,95 |
| RandomHistory cũ | 58,70 | 64,40 | 67,55 |
| DARTContrast cũ | 62,00 | 67,40 | 69,55 |
| UniformAuditGlobal cũ | 64,40 | 69,70 | 75,15 |

PairedHistory − RandomHistory tại primary 10%: **+0,86 điểm phần trăm**, CI 95%
**[−1,49; +3,27]**. PairedGlobal − UniformAuditGlobal: **+1,34 điểm phần trăm**,
CI **[−1,52; +4,23]**. Không đủ bằng chứng rằng đổi sampling luôn cải thiện.

Ở 5%, một số contrast dương; ở 20%, PairedHistory có trung bình thấp hơn random.
Không chọn mức 5% sau khi xem kết quả để thay primary 10%. Gate all-comparisons
của PairedHistory **FAIL**. Các control này không phải DART mới và không phải
bản tái lập CABS/SELECT-LLM.

## Ghi nhận giới hạn về thời điểm commit

Protocol và code được viết trước khi chạy self-report paired ablation; source
hashes được ghi vào manifest trước vòng tính kết quả. Tuy nhiên lệnh Git commit
trước run bị lỗi `index.lock write error: Operation timed out`. Commit `8e85898`
chỉ thành công sau run bằng temporary index ngoài iCloud. Vì vậy không gọi lần
ablation này là thí nghiệm đã commit trước outcome. Không xóa/chạy lại kết quả
để che sự cố. Đây là phân tích development exploratory đã được ghi rõ từ đầu.

Commit `60d6816` thêm follow-up controller và report; commit này dùng temporary
index, khóa độc quyền index gốc và đồng bộ atomically. Không thay source collector
hoặc thuật toán của full replay đang chạy.

## Artifact sau khi full pipeline xong

- `docs/analysis/dart_real_judge_result_2026-10-04.md`: full replay ban đầu.
- `docs/analysis/dart_postrun_diagnostics_2026-10-04.json`: chẩn đoán đầy đủ.
- `docs/analysis/dart_followup_report_2026-10-04.md`: tổng hợp và giới hạn claim.
- `results/dart_followup_v1/status.json`: trạng thái thực hiện follow-up.

Không truy cập outcome challenge hoặc sealed MMLU trong các bước trên. Sau đó
cần quyết định dựa trên kết quả full về việc dùng toàn bộ nhãn đã trả phí để học
policy, cải thiện candidate theo instruction, hay dừng claim phương pháp superior.
