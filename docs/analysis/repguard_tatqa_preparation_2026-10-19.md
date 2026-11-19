# TAT-QA: dữ liệu và evaluator sẵn sàng, chưa có inference

Ngày19/10/2026. **Không có model calls hay model score TAT-QA trong đợt này.**
Đã tải duy nhất TRAIN, evaluator, utilities và license code từ repository tác
giả [NExTplusplus/TAT-QA](https://github.com/NExTplusplus/TAT-QA), revision
`870accc41953dcde885aabeb963d94aabdc0fbc3`. Dataset thuộc CC BY4.0 theo README;
giữ attribution Zhu et al., ACL2021. Code license được lưu cùng nguồn.

TRAIN có2201contexts/13215questions, gồm5543arithmetic. Chọn64arithmetic contexts
bằng hash context/question, một câu mỗi context, loại exact normalized question
và exact normalized table trùng FinQA TRAIN trước khi trích annotations. Hai
question trùng bị loại, zero exact-table matches. Không suy ra đã loại mọi
paraphrase hoặc report overlap. Context UID không phải report identity.

Public inventory chỉ có question, table, paragraphs và IDs. Answer, scale,
derivation, answer_from, rel_paragraphs, req_comparison được lưu riêng ở
`annotations_private.json`, không được đưa vào prompt. Chưa tải dev/test.
Các file nguồn, hash manifest và inventory nằm trong
`results/thesis_tatqa_source_v1/`.

## Các kiểm tra đã chạy

Đã chạy **evaluator gốc**, không viết lại metric thay thế.64ground-truth
roundtrips khớp EM/F1/scale; đây là kiểm phần mềm bằng annotation nguồn, không
là64câu do model giải hay độ đúng của nhãn ngữ nghĩa. Kiểm thêm một câu có
answer0 thật: prediction `['0']` được nhận, scalar0 bị interface gốc coi là
không có prediction. Vì vậy các outputs numeric tương lai phải đi qua đúng
list/string interface, không bỏ câu zero.

Evaluator có normalization scale và rounding riêng, khác FinQA round5. Muốn
báo official EM phải để model dự đoán scale rồi chạy evaluator gốc; không điền
gold scale vào output. Không gộp điểm hai corpus thành cùng một metric mà
không giải thích. Dataset vẫn cần audit nhãn; qua software checks không chứng
minh mọi câu rõ nghĩa.

SciPy1.16.2 được cài riêng tại `/tmp/repguard_tatqa_eval_deps`, cùng NumPy2.4.6/
pandas3.0.6 sẵn có. Không đổi dependency của remote inference hay project venv.
Wheel hash, source hash và selfchecks có trong
`repguard_tatqa_evaluator_selfcheck_2026-10-19.json`.

Để dùng corpus này cho nghiên cứu, còn phải khóa task contract về value/scale,
protocol, splits có nguồn report nếu truy được, comparator và budget trước
inference. Chưa chọn corpus vì một score model thuận lợi; chưa có score nào.
