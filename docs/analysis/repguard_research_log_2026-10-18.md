# Research log — phương pháp repair có reputation

## Câu hỏi nghiên cứu đã nhận

Ưu tiên nghiên cứu multi-agent/reputation có ích và có kiểm chứng; prototype
chỉ chứng minh tích hợp. Không hứa superiority/novelty trước thực nghiệm. Đã
bắt đầu batch thật `31ea9478aa9d2696ef401e46` trên app Modal riêng; protocol
`repguard_causal_repair_protocol_2026-10-18.md` và frozen source trước inference.

## Phát hiện trước khi xem kết quả batch mới

- Screen cũ có union A/B đúng bằng B (1/20). Không learner nào chọn lại chính
  hai output đó để vượt B trên mẫu đó; cần tạo output tốt hơn.
- Trong probe cũ, typed một operation từ chối câu nhiều bước. Executor mới
  dùng references và tối đa tám bước. Acceptance check với các số thực trong
  tài liệu DRE tính đúng 25.9+23.8+28.8=78.5; đây là kiểm phần mềm, không phải
  output model và không đưa vào score.
- Inventory trên 100 câu trước: 88 đáp án dạng số đơn có thể so tự động;
  10 mismatch flags giữa answer và exe_ans sau tolerance theo độ làm tròn
  của answer. Không tự nhận 10 annotation errors: có thể do làm tròn không
  chuẩn, convention về dấu/percent hoặc câu hỏi mơ hồ; phải đọc evidence.
- Dịch gold AST sang DSL bằng numeric equality kiểm được 87/100, và 24/24
  câu mới. 13 câu còn lại gồm table operations, hằng số chưa hỗ trợ và literal
  khác cách ghi nguồn. Mapping này chỉ chứng minh khả năng biểu diễn số,
  không chứng minh chọn đúng source, không phải thành tích solver.
- MO/2016/page_10.pdf-4: văn bản cho 853.5 triệu đơn vị năm 2016, tăng4.9%
  từ2015. Tính kinh tế là 853.5/1.049≈813.63; answer=813.63 nhưng program
  `add(const_100,4.9%),divide(853.5,#0)` với percent fractional cho8.53082.
  Đây là bất nhất cụ thể giữa câu hỏi/evidence/answer và execution target.
  Không sửa nhãn hay đổi score chính sau khi xem output.
- CCI/2004/page_32.pdf-2: câu bị chia thành nhiều span, nối lại nói 8816 sites
  tương ứng83% là leased/subleased/licensed; gold lại8816×83%=7317.28.
  Cần human adjudication do phạm vi 'licensed'/tower-site và cách hỏi 'about'.

Inventory đầy đủ: `repguard_semantic_contract_inventory_2026-10-18.json`.
Audit parser bổ sung phát hiện regex bỏ dấu `%` khi dấu này đứng SAU ngoặc
đóng, như `( 3.5 ) %`: catalogue giữ-3.5 thay vì-0.035. Trên32case của batch
có8tokens/2case bị ảnh hưởng (một case HISTORY, một fresh). Đây là lỗi thật
của frontend; không giải thích được mọi thất bại. Giữ frozen v1 để biết kết
quả pipeline chính xác, không sửa output/nhãn giữa batch; phiên bản sau phải
sửa parser và chạy lại có đối chứng. File `repguard_percent_parser_audit_2026-10-18.json`.
Issue chính thức của FinQA đã có phản ánh answer và exe_ans khác nhau, nhưng
issue đó không xác nhận các case cụ thể của chúng ta:
[FinQA issue6](https://github.com/czyssrs/FinQA/issues/6).
Evaluator gốc so kết quả chương trình với exe_ans:
[official evaluator](https://github.com/czyssrs/FinQA/blob/main/code/evaluate/evaluate.py).

## Related work bổ sung và ranh giới đóng góp

[DARC — Diagnosis Before Recovery](https://arxiv.org/abs/2608.11772)
(preprint12/8/2026) đã chẩn đoán failure trên development, giới hạn recovery
library và cố định policy theo success/cost. Vì vậy 'diagnose rồi repair'
không đủ novelty. Bản này cố định diagnosis ở task-family level; ứng viên của
ta xét quyết định cho từng output, khi correctness của output hiện tại chưa
biết. Phải so baseline recovery với cùng thông tin; không dùng oracle để
dừng ở câu đúng.

[Conditional agent trust](https://arxiv.org/abs/2606.14200)
đã nghiên cứu reputation theo skill và điều kiện để conditioning có lợi.
Không nhận conditional reputation là phát minh mới. [CRITIC](https://arxiv.org/abs/2305.11738)
là đối chứng khái niệm cho tự sửa bằng tool feedback; benchmark này cần
baseline cùng source/DSL/token budget và cùng cơ hội sửa.

Giả thuyết hẹp đang thử: một edit action có phạm vi được kiểm bằng code có
thể giảm thiệt hại khi sửa sai phần; lịch sử paired rescue/harm có thể phân
bổ action tốt hơn một agent tự sửa hoặc fixed repair. Đây là giả thuyết,
chưa phải kết quả hay tuyên bố đầu tiên trong lĩnh vực.

## Trace audit trong lúc batch chạy — không sửa protocol

Initial mới hoàn tất6/24 đúng theo target chính. Một diagnostic bổ sung được
viết SAU khi xem các initial sớm, TRƯỚC phần lớn repair outcomes: nếu output
percent kết thúc bằng multiply vớiK100/K1000/K1000000 sau step liền trước,
thử bỏ step scale đó. Không dùng gold để quyết định sửa, nhưng đây vẫn là
rule hậu nghiệm development. Tính lại trên chương trình thật:10output thay
đổi,6rescue/0harm so target, tổng12/24. Không phải inference mới, không thay
score chính, không nhận là một phương pháp được xác nhận. Quan trọng hơn,
một repair method về sau phải vượt baseline compiler/unit đủ tốt, không
được nhận công cứu các lỗi giao diện có thể sửa rẻ hơn. Chi tiết tái lập:
`repguard_unit_failure_diagnostic.py` và JSON cùng tên.

Trace HWM/2017/page_77.pdf-2 là bằng chứng rõ cho nhầm giao diện: reasoning
nêu đúng phải lấy6trừ5; program lookup đúnghai source đó nhưng cuối lại
`subtract(K0,K1)` thay vì`subtract(#0,#1)`, ra-1. Hai source lookup không
đóng góp vào kết quả cuối. Vì vậy không được gọi mọi score thấp ở DSL là
model không hiểu câu hỏi, hay gọi việc sửa alias này là đóng góp reasoning
multi-agent. Verifier hiện tại chỉ kiểm source reference có tồn tại và
arithmetic có chạy; chưa bảo đảm result thực sự phụ thuộc evidence hay
reasoning khớp program. V2 cần kiểm dependency và namespace rõ ràng.

Trace DISH/2002/page_94.pdf-4: reasoning kết luận đúng359million lớn hơn
55,999, nhưng program so359với55,999 không chuyển million/thousand nênra
no. Cần quantity scale trong intermediate representation, không chỉ token
boundary. Trace FRT/2007 bảng có các hàng năm dạng balance→additions→balance;
catalogue chỉ gắn row label với hàng đầu bảng nên mất block-year context.
Đây là hạn chế serialization thật, không chỉ lỗi chọn nguồn của model.
