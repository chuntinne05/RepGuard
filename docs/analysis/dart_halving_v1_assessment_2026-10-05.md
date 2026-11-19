# Kiểm tra đối chứng Sequential Halving

Run `3e7b59ea64ebe3767bef00b6`: **300/300 case, 600 lần chạy phương pháp**, đã kiểm chứng.

Ứng viên paired CFJudgeFactor giữ nguyên; các baseline chỉ nhận nhãn TRAIN trả phí. Đây là replay thật trên kết quả agent đã chạy, không gọi thêm solver/judge. Dữ liệu vẫn là development pool 168 task /56 generator /14 agent.

## Kết quả

| Phương pháp | 5% | 10% primary | 20% |
|---|---:|---:|---:|
| IndependentSH | 65.00 | 69.70 | 77.20 |
| PairedSH | 67.00 | 71.90 | 78.95 |
| PairedGlobal | 62.15 | 71.95 | 76.70 |
| UniformAuditGlobal | 64.40 | 69.70 | 75.15 |
| TunedFactorRidge | 66.50 | 71.60 | 75.85 |
| FrozenPairedCFJudgeFactor | 64.70 | 74.15 | 77.50 |

Số task thành công trung bình /168; trung bình 20 seeds trên toàn bộ outer folds.

## Ứng viên trừ baseline ở ngân sách 10%

| Baseline | Chênh lệch điểm % | CI95 điểm % | Rescue | Harm |
|---|---:|---|---:|---:|
| IndependentSH | +2.65 | [+0.54, +4.94] | 18.55 | 14.10 |
| PairedSH | +1.34 | [-0.86, +3.42] | 19.30 | 17.05 |
| PairedGlobal | +1.31 | [+0.03, +2.59] | 5.95 | 3.75 |
| UniformAuditGlobal | +2.65 | [-0.60, +5.86] | 23.05 | 18.60 |
| TunedFactorRidge | +1.52 | [-1.07, +4.05] | 20.20 | 17.65 |

**Gate đối chứng mới: FAIL.**

**Gate gốc vẫn FAIL:** CI chưa dương trước cả UniformGlobal và PairedGlobal. Không thay primary endpoint, không gọi kết quả này là xác nhận DART hoặc SOTA.

Ứng viên cao điểm hơn các controls trong bảng ở10%, nhưng PairedSH cao hơn ứng viên ở cả5% và20%. Vì thế không có phương pháp thắng đều trên toàn đường ngân sách. Không dùng điểm5% hoặc20% để chọn lại primary sau thực nghiệm.

## Chẩn đoán mô tả sau thực nghiệm

Dùng toàn bộ gold TRAIN sau khi quyết định đã khóa để xác định agent tốt nhất của train và xem nó bị loại ở vòng nào. Đây không phải feature, target được cấp miễn phí hay bằng chứng nhân quả; chỉ đo việc loại sớm trong dữ liệu đã quan sát.

| Ngân sách | Baseline | Nhãn/agent vòng đầu | Còn ít nhất một agent tốt nhất TRAIN sau vòng 1/2/3/4 |
|---|---|---|---|
| 0.05 | IndependentSH | [1, 1] | 69% / 61% / 45% / 39% |
| 0.05 | PairedSH | [1, 1] | 71% / 56% / 49% / 37% |
| 0.1 | IndependentSH | [3, 3] | 71% / 62% / 51% / 43% |
| 0.1 | PairedSH | [3, 3] | 84% / 77% / 67% / 50% |
| 0.2 | IndependentSH | [6, 7] | 90% / 84% / 76% / 62% |
| 0.2 | PairedSH | [6, 7] | 92% / 89% / 86% / 77% |

## Kiểm chứng và giới hạn

- Kiểm tra source/input hash, mọi checksum, đúng số nhãn độc nhất; chạy lại 600 quyết định, đồng thời dựng lại điểm và tập agent sống sót từ log nhãn trả phí.
- 5.000 generator bootstraps, seed1404, sau seed averaging. CI chưa điều chỉnh lịch sử nghiên cứu thích nghi và chưa đo toàn bộ bất định huấn luyện.
- SH ở đây là bản thích ứng hữu hạn với ngân sách chính xác: lấy mẫu không hoàn lại, chuyển phần dư ngân sách sang vòng sau. Không tự động thừa hưởng định lý IID của bài gốc.
- Baseline không cần judge; CFJudgeFactor dùng thêm 2.352 judgment lịch sử. Cùng ngân sách gold không đồng nghĩa cùng chi phí USD.
- Kết quả với hai baseline này không đồng nghĩa thắng mọi phương pháp liên quan. Cần dữ liệu độc lập, baseline phù hợp và đóng góp thuật toán rõ trước kết luận cho bài báo.

## Bước tiếp theo

Giữ nguyên ứng viên và toàn bộ kết quả âm. Kiểm tra bộ dữ liệu độc lập và khả năng có feedback không lấy từ gold; khóa split, chi phí và tiêu chí trước khi đánh giá. Không tiếp tục chọn hyperparameter trên 168 task này để cố làm CI dương.

- [Protocol đã khóa](dart_halving_v1_protocol_2026-10-05.md).
- [Toàn bộ số liệu](dart_halving_v1_results_2026-10-05.json).
- [Karnin et al., ICML 2013, Algorithm 2](https://proceedings.mlr.press/v28/karnin13.pdf).
