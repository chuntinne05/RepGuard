# MBPP/FinQA headroom run: vận hành và kết thúc

- App/Volume: `repguard-routerbench-headroom-v1`.
- Run: `58bcf5179974f10ebe94c405`.
- Detached FunctionCall: `fc-01M48J3VHACP45FAC7EAZXQNK5`.
- Source/protocol freeze: commit `7b8fdc0`, đã push `dev` trước khi submit.
- Modal CPU, 40 selected files; không có lời gọi solver/judge mới.

Metadata intake cho thấy MBPP có 970 common hashes trong 974 records và FinQA
có 1.138 common hashes. Trước score access, đã loại khỏi toàn pool mọi hash
lặp ở bất kỳ model nào: **4 MBPP**, **9 FinQA**. Eligible còn 966/1.129. Từ
đó chốt bằng hash 200 câu development cho mỗi dataset, mỗi câu có đủ 20 model.

Status/ledger cloud đã tiến triển từ 0/40 qua 19/40 và kết thúc 40/40 lúc
**19:16:20 ngày 06/10/2026 giờ Việt Nam**
(`2026-10-06T12:16:20.311819+00:00`). FunctionCall trả thành công; state
`completed_development_headroom_review_required`. Đã tải 44 artifacts,
kiểm tra checksum của 40 score files và tính lại toàn bộ 200×20 matrix cho
hai dataset; cloud/local khớp.

Kiểm tra:

```bash
.venv/bin/python run_routerbench_headroom.py status
.venv/bin/python run_routerbench_headroom.py fetch
.venv/bin/python report_routerbench_headroom.py
```

Worker chỉ giữ `records.item.score` ở selected positions. Score còn lại không
được lưu hoặc dùng. 770 câu MBPP và 938 câu FinQA common ngoài 200 dev chưa
đọc score trong run này; trong số đó 4/9 hashes lặp không đủ điều kiện theo
rule. Đây là development diagnostic, không phải final evaluation độc lập.

[Protocol](routerbench_headroom_v1_protocol_2026-10-06.md) ·
[Kết quả](routerbench_headroom_v1_assessment_2026-10-06.md)
