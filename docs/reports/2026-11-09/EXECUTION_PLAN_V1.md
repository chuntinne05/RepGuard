# RepGuard — kế hoạch thực thi vòng 1

Ngày 09/11/2026. Viết trước các lượt generation của vòng này. Người dùng đã yêu cầu nghiên cứu, chuẩn bị plan và chạy thực nghiệm thật; giữ trục multi-agent, scope mở.

## Mục tiêu và đường đi

Khóa luận ưu tiên kiểm chứng claim/số liệu bằng hệ đa tác tử. Không chốt trước một thuật toán thắng. Thứ tự: (0) source/oracle và provider preflight; (1) năng lực kiểm sufficiency và giá trị trao đổi giữa agent; (2) lịch sử reviewer có thêm ích; (3) evidence acquisition trên tài liệu gốc và nhãn phù hợp; (4) xác nhận độc lập, sản phẩm và nghiên cứu người dùng.

Mỗi vòng có protocol, manifest/hash, kết quả, quyết định GO/STOP và plan kế tiếp. Không gọi labels đã dùng để debug là untouched confirmation. Không đồng nhất receipt PASS với scientific PASS.

## Vòng đầu: lựa chọn dữ liệu và ranh giới

Nguồn ứng viên đầu: [Relevant Is Not Enough](https://aclanthology.org/2026.finnlp-1.32.pdf), [repository chính thức](https://github.com/dweebee/dg-evidence-750), commit đã lookup `dc65e18a0a3e40e13c461c05b55103379db1fd8e`.

Lý do: có expert-audited passage labels, tránh tự tạo semantic oracle từ một LLM. Nhãn bốn lớp: irrelevant, relevant-insufficient, sufficient-support, sufficient-refute. Đây là **standalone passage sufficiency**, không phải claim truth trên thế giới và không phải joint sufficiency của nhiều passages. Paper tách pair labels khỏi claim verdicts; thực nghiệm này giữ đúng ranh giới đó.

Raw data lưu dưới `results/`, giữ provenance và hash, không đưa raw excerpts vào release code khi chưa xác định quyền redistribution. Chỉ public-field whitelist được gửi vào inference. Gold, labels suy ra, claim verdicts, reference answers và split outcomes không vào prompt.

Chia claim groups theo hash ID và duplicate links, trước model outcomes: dự kiến 24 groups pilot, 56 history/dev, 20 calibration, 50 reserve nếu inventory xác nhận 150 groups. Chốt chính xác trong machine-readable plan sau schema/duplicate audit; nếu grouping làm đổi số nhóm, ghi amendment **trước** generation. Không chọn group theo label/model score. Chưa dùng reserve để chọn prompt/model/method.

## Hạ tầng và provider preflight

Đã kiểm venv Python3.11, Modal1.5.5 và cấu hình Gemini. Đã đọc model inventory qua REST, chưa generation ở thời điểm lập kế hoạch này. Các app nghiên cứu cũ hiện được liệt kê 0 tasks; có một app bạn bè đang hoạt động, không gọi/thay đổi app đó.

Provider pathway được chọn theo sức khỏe dịch vụ, không theo kết quả benchmark:

1. Tối đa **2 generation smoke calls** trên ví dụ tổng hợp tách khỏi corpus: `gemini-3.8-flash` và `gemma-4-26b-a4b-it`, đã xuất hiện trong account model inventory. Lưu request/response, usage, version và mọi HTTP error; không retry generation mù khi không có receipt.
2. Nếu API pathway không dùng được, fallback đã định trước là Qwen3.5 27B và Gemma4 26B trên **app Modal mới**, dùng các weights volumes nghiên cứu riêng có sẵn. Kiểm Ollama version, model digests và GPU; không gọi/thay deployment cũ, không mount eval/gold vào GPU workers.
3. Schema/transport preflight không dùng outcome corpus để tune. Nếu phải thay prompt/schema sau generation corpus, tách version/run, giữ outputs cũ.

Backend và model IDs/digests/config được khóa trong registered plan trước corpus inference. Provider output chưa đạt contract thì ghi invalid; không xin model sửa JSON để âm thầm nâng score.

## Phép thử 1 và các controls

Task: phân loại standalone claim–passage pair thành bốn nhãn. Cùng claim, passage, metadata và rubric cho mọi model. Reviewer không được dùng web hoặc kiến thức ngoài passage để thay bằng chứng thiếu.

Hai agents A/B khác model family; cùng output contract và cap phù hợp. Thu direct A/B, sau đó bốn continuations thật: A→A, B→B, A→B và B→A. Arrow là model nhận initial answer của model trước và kiểm lại, không phải replay tưởng tượng. Reviewer không biết model identity của initial answer. Cùng review prompt cho self và cross, giữ từng initial/raw response và prompt lineage.

Tối đa 24×5×6=**720 corpus generations** nếu inventory phù hợp. Stage smoke corpus đầu tối đa 2 claim groups/10 pairs theo thứ tự hash; không xem gold, chỉ kiểm operational validity trước khi tiếp tục cùng prompt. Dừng nếu validity quá thấp, nguồn/checksum sai hoặc provider thay version; không chọn chỉ các outputs thành công. Worker có checkpoint, bounded calls, timeouts và status. Không có job mở rộng tự động sau pilot.

Primary pilot contrast: `0.5 * [(accuracy A→B − accuracy A→A) + (accuracy B→A − accuracy B→B)]`, balanced theo hướng, paired trên cùng claim groups. Đây là cross-family exchange vs repeated same-family calls, chưa phải học reputation hay source-diversity study.

Secondary: từng workflow, macro-F1, sufficient-judgment coverage/risk, support/refute direction errors, false approvals trên gold irrelevant/insufficient, rescue/harm, valid response rate, actual input/output/reasoning tokens, latency và calls. Không gọi matched call count là matched USD/GPU compute; báo cả hai khi có dữ liệu.

Ước lượng CI theo claim cluster, không lấy 120 pairs hay 720 calls làm n độc lập. Có thể thêm independent A/B agreement-with-deferral control từ hai direct outputs, ghi rõ abstention và chi phí hai calls. Oracle union là ceiling chẩn đoán, không là method score.

## Gate và quyết định kế tiếp

- Operational: mọi case có terminal record, không gold leakage, source/prompt/model/config consistency, ≥95% parse-valid responses. Invalid vẫn tính fail trong accuracy.
- Capability: các policy không chỉ dự đoán toàn bộ insufficient; báo per-class counts và sufficient precision/recall. Nếu không phân biệt được, dừng history learning và sửa năng lực/rubric trong protocol mới.
- Interaction screen: candidate GO chỉ nếu primary contrast ≥3 điểm %, có net rescue dương và ≥6 rescue cells phân bố ≥4 claim groups so self controls; CI phải báo đầy đủ. Đây là gate development, không là significance/confirmation claim.
- Nếu FAIL: không fit history learner chỉ vì đã có outputs. Phân tích liệu có complementarity chưa khai thác, shared-error hay thiếu bằng chứng; chốt **một** study can thiệp kế tiếp. Không mở rộng vô hạn pool/prompts.
- Nếu PASS: dùng history/dev groups riêng để kiểm current-state learner vs same-information learner có historical reviewer utility. Acquisition audit giữ đơn giản trong vòng kế; chưa nhận active/VOI audit là novelty.
- Trước end-to-end report claims: cần nhãn claim truth/joint evidence và nguồn raw reports phù hợp; không biến nhãn passage thành gold cho combined evidence.

## Research bổ sung cần đưa vào quyết định

[FinSAgent](https://arxiv.org/abs/2607.18102) đã có corpus-conditioned multi-agent retrieval và matched-budget study: không nhận role specialization/retrieval gating nói chung là mới. [CLAIR-Fin](https://arxiv.org/abs/2608.13706), [VP-CONTROL](https://arxiv.org/abs/2609.10969), [CAMA](https://arxiv.org/abs/2608.19701), [ASB](https://arxiv.org/abs/2610.06610) tiếp tục là close controls theo đúng claim sau pilot. [ClaimReceipt](https://arxiv.org/abs/2609.01992) phân biệt claim-relative evidence sufficiency và experiment coverage; logging/hash tự nó không chứng minh đủ bằng chứng cho mọi claim.

Nguồn Gemini REST được kiểm qua [official reference](https://ai.google.dev/api/generate-content?hl=en). Không dùng bảng giá cũ trong provider module để nhận cost savings.

## Deliverables vòng này

Protocol đã khóa; source/duplicate/schema inventory; public/private packets; collector và evaluator; meaningful harness tests; request/response ledger thật; summary + error taxonomy + gate; quyết định có lý do và kế hoạch vòng kế. Kết quả có thể FAIL và vẫn phải lưu.

Nhu cầu người dùng/chuyên gia và đánh giá sản phẩm vẫn là việc cần người tham gia thật; không tự tạo phản hồi khách hàng, human adjudication hay user-study results.
