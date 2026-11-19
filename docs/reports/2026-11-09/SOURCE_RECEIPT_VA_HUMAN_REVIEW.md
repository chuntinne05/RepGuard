# Receipt kiểm nguồn và phép tính: prototype có giới hạn rõ

`research_ops/source_receipt.py` là CLI chạy local, không gọi model/network. Nó đọc question/table và một câu trả lời JSON, xuất lại đúng các ô ảnh hưởng đến kết quả cuối, kiểm phép tính, schema và các source reads không được dùng. Mục đích là giúp người soát kiểm nhanh trace, chưa là sản phẩm được xác nhận nhu cầu.

```bash
PYTHONPATH=. .venv/bin/python research_ops/source_receipt.py \
  --case /path/to/case.json --answer /path/to/raw_answer.json \
  --output /path/to/receipt.json
```

`case.json` có `question` và `table` theo public schema vòng02. `raw_answer.json` có `answer_value`, `unit`, `program`, `claim_slots`, `explanation`; xem protocol/schema đã khóa. CLI không tự tải data hoặc gọi endpoint cũ.

Hai trạng thái hiện có:

- `mechanical_check_failed_or_abstained`: schema, binding, final dependency hoặc tính nhất quán chưa qua.
- `needs_semantic_review`: phép tính và nguồn qua kiểm cơ học; vẫn cần người xác nhận đúng entity, metric, kỳ, định nghĩa phép tính, đơn vị/scale và tính đầy đủ nguồn. `semantic_verified` luôn `false`.

**Không dùng màu xanh/“đã xác minh đúng” cho kết quả chỉ qua tính lại số.** Cùng một tỷ lệ tăng20% có thể đúng cho cả Revenue và Profit; checker phải hiển thị các ô thật cho người soát, không tự nhận đã trả lời đúng câu hỏi.

## Diagnostic thêm sau registration vòng02

Trong lúc run đang hoạt động, kiểm code phát hiện parser frozen chỉ yêu cầu có source read ở đâu đó trong program. Một program có thể đọc nguồn rồi kết thúc bằng constants. Vì vậy field frozen `source_bound` chỉ bảo đảm các reads hiện diện được bind; không đủ bảo đảm **final result dependency**. CLI mới truy vết dependency cuối và báo trường hợp này. 5tests kiểm literal-only tail, reads thừa, sai metric vẫn tính đúng, JSON lỗi và trạng thái luôn cần semantic review đã pass.

Đây là sửa thiếu sót checker, không là kết quả method. Primary numeric/unit và code frozen của vòng02 được giữ nguyên; nếu áp dụng lên outputs vòng02, đó là **diagnostic bổ sung sau registration**, không thay primary hoặc nhận tăng điểm nghiên cứu. Corpus scoring vẫn cần xác nhận interpretation của gold.

## Phiếu cho người thẩm định

Đã tạo24blank records trong `results/arqa_v2/human_review/source_only_24.json`, thứ tự shuffle khóa seed, chỉ có question và bảng; không model ID/outputs/gold. Mapping riêng nằm cùng thư mục. **0annotation hoàn tất.**

Hai người có kỹ năng đọc bảng/phân tích số trả lời độc lập. Mỗi người ghi entity, metric, period, formula, numeric answer/unit, source IDs, ambiguity và source sufficiency. Không xem đáp án công bố trước khi khóa lượt trả lời nguồn-only. Sau đó mới so với gold để phân loại: cùng diễn giải, khác làm tròn, sai mapping, câu hỏi mơ hồ hoặc formula chưa được nguồn cho phép. Người thứ ba/GVHD adjudicate bất đồng; giữ cả bản gốc và sensitivity adjudicated, không ghi đè published gold.

Người đánh giá không được thay bằng một model mang hai tên annotator. Cần ghi năng lực và quan hệ với tác giả; một tác giả tự soát có ích cho development nhưng không là hai independent domain experts. Việc này xác minh task/oracle, không thay nghiên cứu người dùng về lợi ích sản phẩm.

Discovery vẫn theo [kit đã chuẩn bị](USER_DISCOVERY_KIT.md): tuyển5–8người đang thực hiện workflow, ghi episode cụ thể trước khi chốt vertical. Chưa gửi lời mời hoặc liên hệ ai.
