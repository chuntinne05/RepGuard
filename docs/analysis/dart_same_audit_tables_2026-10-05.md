# DART — toàn bộ kết quả đối chứng cùng tập audit, 05/10/2026

Nguồn: `results/dart_same_audit_v2`. 1.200 cấu hình × 12 biến thể = 14.400 lượt chọn policy; 0 suy luận mới. Các nhãn đến từ trajectory thật đã lưu. 20 seed audit, 5 fold theo generator, 168 task. Đây là dữ liệu phát triển đã xem, không phải xác nhận độc lập.

Số trong bảng là số task thành công trung bình trên 168. Ngân sách là phần trăm số ô task–agent lịch sử được audit. Δ và CI tính bằng **điểm phần trăm** accuracy; bootstrap 5.000 lần theo generator sau khi trung bình seed. CI không chỉnh đa so sánh.

## self_report / acquisition RandomHistory

| Biến thể | 5% | 10% | 20% | Δ so Original ở 10% [CI95%] |
|---|---:|---:|---:|---|
| Original | 58.70 | 64.40 | 67.55 | +0.000 [+0.000; +0.000] |
| ZeroHT | 57.90 | 62.85 | 65.55 | -0.923 [-3.006; +1.220] |
| AgentPriorHT | 60.40 | 65.90 | 68.05 | +0.893 [-0.238; +2.113] |
| BinaryRidgeHT | 59.70 | 64.95 | 67.50 | +0.327 [-0.655; +1.310] |
| ContinuousRidgeHT | 59.70 | 64.95 | 67.50 | +0.327 [-0.655; +1.310] |
| RawHT | 58.75 | 58.95 | 63.25 | -3.244 [-5.685; -0.804] |
| Binary14HT | 57.75 | 64.50 | 68.05 | +0.060 [-0.565; +0.655] |
| BinarySN | 61.85 | 66.55 | 66.85 | +1.280 [-0.327; +2.917] |
| ZeroSN | 61.85 | 66.55 | 66.45 | +1.280 [-0.060; +2.650] |
| SGlobal | 60.00 | 66.65 | 65.95 | +1.339 [+0.179; +2.560] |
| CSGlobal | 63.30 | 66.90 | 73.65 | +1.488 [+0.000; +3.156] |
| CSStratifiedHT | 63.95 | 67.65 | 72.10 | +1.935 [-0.268; +4.107] |

### Các cặp kiểm tra cơ chế tại 10%

| Cặp | Δ accuracy, điểm % [CI95%] |
|---|---|
| ContinuousRidgeHT-BinaryRidgeHT | +0.000 [+0.000; +0.000] |
| Binary14HT-Original | +0.060 [-0.565; +0.655] |
| BinarySN-Original | +1.280 [-0.327; +2.917] |
| ZeroSN-ZeroHT | +2.202 [+0.060; +4.256] |
| CSGlobal-SGlobal | +0.149 [-1.518; +1.905] |

Brier dự báo trên phần S, chỉ dùng để chẩn đoán sau chạy: categorical=0.168648, ridge_binary=0.172346, ridge_continuous=0.172346.

## self_report / acquisition DARTContrast

| Biến thể | 5% | 10% | 20% | Δ so Original ở 10% [CI95%] |
|---|---:|---:|---:|---|
| Original | 62.00 | 67.40 | 69.55 | +0.000 [+0.000; +0.000] |
| ZeroHT | 59.50 | 61.45 | 68.10 | -3.542 [-5.268; -1.845] |
| AgentPriorHT | 62.50 | 64.85 | 69.95 | -1.518 [-2.738; -0.327] |
| BinaryRidgeHT | 62.75 | 66.05 | 69.45 | -0.804 [-1.845; +0.208] |
| ContinuousRidgeHT | 62.75 | 66.05 | 69.45 | -0.804 [-1.845; +0.208] |
| RawHT | 60.50 | 61.95 | 61.25 | -3.244 [-5.119; -1.488] |
| Binary14HT | 61.25 | 66.35 | 69.75 | -0.625 [-1.429; +0.119] |
| BinarySN | 62.05 | 64.20 | 69.05 | -1.905 [-3.452; -0.446] |
| ZeroSN | 60.60 | 64.65 | 69.40 | -1.637 [-3.690; +0.298] |
| SGlobal | 61.40 | 62.05 | 71.15 | -3.185 [-5.119; -1.280] |
| CSGlobal | 64.00 | 71.55 | 75.05 | +2.470 [+0.446; +4.405] |
| CSStratifiedHT | 61.90 | 67.30 | 73.25 | -0.060 [-2.113; +1.994] |

### Các cặp kiểm tra cơ chế tại 10%

| Cặp | Δ accuracy, điểm % [CI95%] |
|---|---|
| ContinuousRidgeHT-BinaryRidgeHT | +0.000 [+0.000; +0.000] |
| Binary14HT-Original | -0.625 [-1.429; +0.119] |
| BinarySN-Original | -1.905 [-3.452; -0.446] |
| ZeroSN-ZeroHT | +1.905 [-0.714; +4.375] |
| CSGlobal-SGlobal | +5.655 [+3.185; +8.065] |

Brier dự báo trên phần S, chỉ dùng để chẩn đoán sau chạy: categorical=0.168648, ridge_binary=0.172346, ridge_continuous=0.172346.

## judge / acquisition RandomHistory

| Biến thể | 5% | 10% | 20% | Δ so Original ở 10% [CI95%] |
|---|---:|---:|---:|---|
| Original | 61.60 | 64.60 | 67.65 | +0.000 [+0.000; +0.000] |
| ZeroHT | 57.90 | 62.85 | 65.55 | -1.042 [-2.769; +0.714] |
| AgentPriorHT | 60.40 | 65.90 | 68.05 | +0.774 [-0.476; +2.024] |
| BinaryRidgeHT | 61.50 | 65.25 | 67.55 | +0.387 [-0.238; +0.982] |
| ContinuousRidgeHT | 61.05 | 64.65 | 67.05 | +0.030 [-0.685; +0.685] |
| RawHT | 62.65 | 62.30 | 66.70 | -1.369 [-3.245; +0.417] |
| Binary14HT | 60.50 | 64.90 | 68.60 | +0.179 [-0.446; +0.833] |
| BinarySN | 64.05 | 65.90 | 67.40 | +0.774 [-0.179; +1.726] |
| ZeroSN | 61.85 | 66.55 | 66.45 | +1.161 [-0.089; +2.440] |
| SGlobal | 60.00 | 66.65 | 65.95 | +1.220 [+0.119; +2.381] |
| CSGlobal | 63.30 | 66.90 | 73.65 | +1.369 [-0.357; +3.125] |
| CSStratifiedHT | 63.95 | 67.65 | 72.10 | +1.815 [-0.060; +3.690] |

### Các cặp kiểm tra cơ chế tại 10%

| Cặp | Δ accuracy, điểm % [CI95%] |
|---|---|
| ContinuousRidgeHT-BinaryRidgeHT | -0.357 [-1.101; +0.388] |
| Binary14HT-Original | +0.179 [-0.446; +0.833] |
| BinarySN-Original | +0.774 [-0.179; +1.726] |
| ZeroSN-ZeroHT | +2.202 [+0.060; +4.256] |
| CSGlobal-SGlobal | +0.149 [-1.518; +1.905] |

Brier dự báo trên phần S, chỉ dùng để chẩn đoán sau chạy: categorical=0.168847, ridge_binary=0.172392, ridge_continuous=0.158111.

## judge / acquisition DARTContrast

| Biến thể | 5% | 10% | 20% | Δ so Original ở 10% [CI95%] |
|---|---:|---:|---:|---|
| Original | 61.25 | 63.90 | 68.35 | +0.000 [+0.000; +0.000] |
| ZeroHT | 62.10 | 60.25 | 66.10 | -2.173 [-3.750; -0.714] |
| AgentPriorHT | 59.30 | 65.10 | 69.05 | +0.714 [-0.506; +1.964] |
| BinaryRidgeHT | 61.15 | 62.70 | 68.35 | -0.714 [-1.518; +0.030] |
| ContinuousRidgeHT | 62.60 | 63.30 | 68.50 | -0.357 [-1.101; +0.357] |
| RawHT | 61.25 | 64.05 | 65.95 | +0.089 [-2.113; +2.143] |
| Binary14HT | 61.90 | 63.60 | 68.70 | -0.179 [-0.863; +0.536] |
| BinarySN | 59.95 | 65.70 | 66.80 | +1.071 [-0.208; +2.440] |
| ZeroSN | 59.65 | 64.80 | 67.75 | +0.536 [-0.565; +1.637] |
| SGlobal | 60.80 | 65.40 | 69.20 | +0.893 [-0.744; +2.560] |
| CSGlobal | 64.65 | 68.90 | 74.25 | +2.976 [+0.298; +5.626] |
| CSStratifiedHT | 61.65 | 68.00 | 71.65 | +2.440 [-0.387; +5.417] |

### Các cặp kiểm tra cơ chế tại 10%

| Cặp | Δ accuracy, điểm % [CI95%] |
|---|---|
| ContinuousRidgeHT-BinaryRidgeHT | +0.357 [-0.268; +0.982] |
| Binary14HT-Original | -0.179 [-0.863; +0.536] |
| BinarySN-Original | +1.071 [-0.208; +2.440] |
| ZeroSN-ZeroHT | +2.708 [+0.923; +4.554] |
| CSGlobal-SGlobal | +2.083 [+0.179; +4.018] |

Brier dự báo trên phần S, chỉ dùng để chẩn đoán sau chạy: categorical=0.168847, ridge_binary=0.172392, ridge_continuous=0.158111.

## Đối chứng bên ngoài cùng ngân sách

| Control | 5% | 10% | 20% |
|---|---:|---:|---:|
| UniformAuditGlobal | 64.40 | 69.70 | 75.15 |
| PairedGlobal | 62.15 | 71.95 | 76.70 |

Các control này lấy **tập nhãn khác**; chúng là đối chứng hiệu quả cuối cùng, không phải can thiệp một thành phần cùng tập audit. Không biến thể nào ở ngân sách chính 10% trong từng channel/design có CI95% chênh lệch so UniformAuditGlobal hoàn toàn dương.

v1 giữ nguyên để truy vết; v2 khôi phục đúng thứ tự phép toán HT của code cũ. Chỉ ZeroHT/RandomHistory thay kết quả ở 10% và 20%, giống nhau giữa hai channel. Tất cả Original tái tạo khớp và ZeroHT/uniform khớp AuditOnly hoàn toàn.
