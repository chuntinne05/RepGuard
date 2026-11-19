# Kế hoạch xây dựng và kiểm chứng DART — bản thiết kế ngày 04/10/2026

**Trạng thái:** kế hoạch nghiên cứu, chưa phải protocol xác nhận đã khóa và chưa phải kết quả DART. Bản này thay thế các bước AppWorld capability V1–V10 như hướng chạy tiếp; không thay đổi hay diễn giải lại ledger cũ. Mọi ngưỡng cuối, ID và mã phân tích phải được khóa, commit trước khi đọc kết quả ở tập xác nhận tương ứng.

## 1. Claim cần đạt và lý do đổi thứ tự

DART chỉ đáng là đóng góp phương pháp nếu lịch sử phản hồi **thay đổi quyết định đúng hướng** khi feedback không hoàn hảo và ngân sách audit/solver hữu hạn. Endpoint là exact task success hoặc accuracy ở **cùng chi phí**, không phải riêng Brier. Week 3 ECRT gần hòa FixedBorrow ở team accuracy; study 560 câu cho router bằng fallback nhưng tốn 172 thay vì 40 lời gọi Qwen14; AppWorld V8 không có rescue giữa hai model, V9 0/6 và V10 1/6. Vì vậy không triển khai thêm bộ chọn trên pool hiện tại rồi gọi là DART đã được chứng minh.

Hai giả thuyết phải kiểm nghiệm riêng:

1. Trên một pool có agent bổ trợ, lịch sử feedback theo agent/skill/nguồn có giúp chọn agent đúng hơn một baseline mạnh khi chỉ được dùng thông tin có trước đáp án không?
2. Với **cùng số nhãn gold audit**, chọn episode cần audit dựa trên giá trị quyết định có tốt hơn audit ngẫu nhiên hoặc AuditOnly không, trong điều kiện sạch và poisoning có mục tiêu?

Lợi ích của mô-đun history phải tồn tại ngoài mô-đun audit; nếu DART chỉ bằng AuditOnly thì không thể claim phần reputation đóng góp outcome. Lợi ích của audit chủ động phải tồn tại ngoài random audit cùng ngân sách; nếu không, thuật toán đơn giản hơn là kết luận đúng.

## 2. Giai đoạn A — tìm dữ liệu có cơ hội thật trước khi viết DART

**Ưu tiên 1: AppWorld leaderboard công khai.** [Kho leaderboard chính thức](https://github.com/StonyBrookNLP/appworld-leaderboard) phát hành các output bundle mã hóa và hướng dẫn unpack tại chỗ, không được đăng bản giải mã công khai. [Xia & Wang 2026](https://arxiv.org/html/2606.14200v1) đã phân tích 14 agent khác cả scaffold lẫn model trên cùng 168 task `test_normal` và 380 task `test_challenge`, thấy agent tốt nhất thay đổi theo app-skill. Đây là bằng chứng **từ paper khác** rằng một pool đáng sàng lọc tồn tại, không phải kết quả hay novelty của DART. Cần xác minh từng bundle, phiên bản AppWorld, ID giao nhau, exact success, độ đầy đủ trajectory, metadata chi phí và quyền sử dụng trước khi dùng. Không dùng số `skill-best` hay `oracle` tính bằng outcome test làm thành tích DART.

Trước khi đọc ma trận outcome từng task, tạo manifest chọn pool theo tiêu chí ngoại sinh: đúng phiên bản, đủ task chung, đủ usage metadata, khác model/scaffold và không chọn chỉ vì điểm thuận lợi. Nếu số agent quá lớn, dùng danh sách cố định theo họ scaffold/model; báo toàn bộ lần thử pool. Kiểm tra skill/feature nào thật sự thấy được **trước khi agent hành động**. `primary app`, generator, required API hoặc nhãn suy ra từ gold không được cấp cho router nếu chúng không có trong yêu cầu công khai. Chia dữ liệu theo task/generator trước khi fit hoặc xem kết quả; không đưa cùng task sang cả history và evaluation.

Vì leaderboard đã công khai và một paper đã xem aggregate toàn bộ, dùng nó làm **khám phá và kiểm tra phương pháp**, không mô tả là holdout độc lập cuối. `test_challenge` có thể là phép đánh giá phân phối khác đã khóa riêng nếu không nhìn per-task outcome, nhưng không thay thế xác nhận trên pool/benchmark mới. Nếu bundle thiếu usage đáng tin, primary cost tạm là số agent invocations; không suy ra USD từ số đó.

**Gate A:** tính success từng agent, `A-only/B-only` trên cùng ID, oracle headroom chỉ để chẩn đoán, khả năng specialist theo skill và số lượng task độc lập. Tiêu chí số tối thiểu và power được chốt từ số task/độ bất đồng trên phần development trước khi mở evaluation. Nếu không có rescue hai chiều với độ lớn đủ kiểm định, dừng pool; không huấn luyện router để săn tín hiệu không có.

## 3. Giai đoạn B — định nghĩa thuật toán DART tối thiểu

Mỗi episode lịch sử lưu: task/skill quan sát được lúc quyết định, agent, câu trả lời/hành động, feedback từ nguồn nào, thời điểm, chi phí và nhãn gold **chỉ nếu episode đã được audit**. DART không nhìn gold của task evaluation. DART gồm bốn mô-đun có thể tắt riêng:

1. **Competence theo task:** dự báo xác suất agent `a` hoàn tất task `x` từ feature công khai của task và lịch sử đã có. Bắt đầu với global, skill-conditional và retrieval/kNN đơn giản; mô hình phức tạp chỉ giữ nếu dev thắng những đối chứng này. Không dùng một trọng số cố định cho mọi task cùng môn như ECRT cũ.
2. **Reliability của feedback:** ước lượng sensitivity/specificity theo nguồn judge và, chỉ khi đủ mẫu, theo agent/skill. Dùng regularization hoặc partial pooling; đưa bất định của ước lượng vào posterior. Tránh đổi dấu feedback chỉ vì một ước lượng nhiễu gần 50%. Feedback từ judge, audit gold và can thiệp attack phải có provenance riêng.
3. **Audit có giá trị quyết định:** từ lịch sử chưa audit, ước lượng việc biết gold của một episode sẽ thay đổi phân phối chọn agent cho các task tương lai bao nhiêu, chia cho chi phí audit. Chọn episode có expected decision value cao, nhưng dành một tỷ lệ audit ngẫu nhiên đã khóa để phát hiện poisoning nhắm mục tiêu và đo thiên lệch chọn mẫu. Không dùng gold của episode để **chọn** episode ấy. Mỗi baseline được cấp cùng số gold audits.
4. **Chọn hành động có guard:** chọn agent hoặc gọi thêm solver khi lợi ích kỳ vọng sau khi tính chi phí vượt baseline. Nếu khoảng bất định của phần cải thiện chứa rủi ro hại lớn, dùng fallback mạnh đã định trước. `Lower bound` dùng làm điều kiện chấp nhận hành động; không thay posterior mean bằng lower bound rồi coi đó là xác suất đáp án đúng.

Để giữ tính kiểm toán, triển khai phiên bản nhỏ với ít hyperparameter, ghi mọi lựa chọn, posterior, audit, API/model call và feature online. Chạy unit tests chống leakage, replay cùng seed và tính chi phí. Mô hình task-level, feedback model, audit scheduler và guard là **ablation bắt buộc**, vì chỉ tổng thể thắng không chỉ ra thành phần nào cần thiết.

## 4. Giai đoạn C — nguồn feedback thật và attack

- **Feedback thật:** dùng một judge cố định trước khi chấm episode, chỉ nhìn dữ liệu công khai và trajectory/answer mà một evaluator vận hành được phép thấy; không đưa official hidden checks hoặc gold vào prompt. Chạy một pilot để đo false positive/negative theo agent/skill và độ ổn định; nếu judge gần random, không tự động cho nó trọng số cao.
- **Gold audit:** lấy từ official state-check/answer key chỉ cho các episode lịch sử được chọn audit. Cùng ngân sách audit được cấp cho DART, AuditOnly, random audit và các baseline audit-aware. Phí judge và audit được báo riêng; nếu gold state-check là proxy cho human review, nêu rõ giả định chi phí.
- **Intervention:** clean, nhiễu judge quan sát được, false positive nhắm một agent/skill, false negative và cross-skill laundering. Tách can thiệp feedback khỏi thay đổi hành động/đáp án của agent. Đăng ký attacker, ngân sách, seed và order trước evaluation. Dùng nhiều agent mục tiêu; không chỉ báo trường hợp yếu nhất được chọn sau khi xem kết quả.

## 5. Giai đoạn D — đối chứng, endpoint và phân tích

**Primary contrast:** DART so với baseline mạnh nhất được chọn bằng development ở một operating point ngân sách cố định, cùng task ID và cùng ngân sách gold audit. Một contrast đồng chính hoặc thứ tự kiểm định kế tiếp là DART so với AuditOnly cùng ngân sách. Chốt đơn vị chi phí và mức cải thiện tối thiểu hữu ích sau power analysis trên development, **trước** khi xem xác nhận. Báo cả đường success–cost, vì một điểm có thể che trade-off.

Đối chứng tối thiểu: best single agent chọn trên train, skill-only, global reputation, FixedBorrow/ECRT, [Xia–Wang skill-conditional trust](https://arxiv.org/abs/2606.14200), retrieval/kNN từ history ([ContextualRouter](https://aclanthology.org/2026.eacl-srw.22/) cho thấy baseline này mạnh), AuditOnly, random-audit+history, một router question-only, và thêm solver ở cùng ngân sách. Với MMLU-Pro còn có always thinking, fallback khi invalid, subject/question router và [CP-Router](https://ojs.aaai.org/index.php/AAAI/article/view/40589) nếu có thể tái lập đúng input; proxy phải ghi rõ là proxy. Oracle chỉ là trần chẩn đoán.

Metrics chính: exact task success hoặc MCQ accuracy, số task cứu/hại so baseline, số switch đúng/sai, input/output tokens, số lời gọi agent/judge/audit, latency và USD **chỉ khi có billing đo được**. Metrics phụ: Brier/ECE, attack regret, worst-skill accuracy, calibration, phân tích coverage theo budget. Câu invalid/truncated tính sai, không loại khỏi mẫu. Khoảng tin cậy là **paired** theo task; với AppWorld còn báo cluster theo generator/skill, với MMLU-Pro phân tầng subject. Khi so nhiều baseline hoặc ngân sách, khóa thứ tự kiểm định/hierarchical gate để tránh chọn cell đẹp hậu nghiệm.

**Go/no-go method:** (i) pool qua gate rescue; (ii) DART có lợi ích decision/task outcome so baseline mạnh và AuditOnly ở cùng budget trên evaluation chưa xem, CI của hai contrast chính nằm trên 0, mức gain thực dụng vượt ngưỡng đã khóa; (iii) ablation xác nhận history và audit có tác dụng riêng; (iv) targeted poisoning không tạo thiệt hại vượt biên đã khóa so baseline; (v) kết quả cùng chiều trên pool/benchmark độc lập. Một điểm Brier tốt hơn hoặc oracle headroom lớn không đủ.

## 6. Xác nhận độc lập và artifact bài báo

420 MMLU-Pro sealed holdout đã khóa trong `results/real_next_study_v1/frozen_splits.json` **chưa được dùng để chọn DART**. Không mở nó để sửa pool generalist đã trượt gate. Chỉ dùng sau khi có một policy, hyperparameter, baseline, budget và endpoint đã freeze. Nếu DART được phát triển chủ yếu trên public AppWorld trajectories, cần một phép xác nhận mới bằng agent/task hoặc benchmark khác; leaderboard đã xuất bản và các AppWorld train pilot V1–V10 không thay thế phép này. Bài có thể báo MMLU-Pro như một bài kiểm tra generalization khó và kết quả âm nếu nó không chuyển được.

Artifact cuối cần: code và một lệnh tái tạo, protocol/commit hash, task IDs và split, manifest model/prompt/scaffold, ledger sử dụng được theo license, checker chống rò gold, benchmark card, bảng task success–cost, CI ghép cặp, ablation, attack matrix và limitations. Raw AppWorld output đã giải mã không được đẩy lên Git công khai theo [hướng dẫn leaderboard](https://github.com/StonyBrookNLP/appworld-leaderboard).

## 7. Thứ tự thực thi gần nhất

1. Kiểm tra license, phiên bản và schema của leaderboard bundles; tạo manifest pool/feature/split từ metadata trước khi đọc per-task outcome.
2. Chạy analyzer capability/complementarity trên dữ liệu thật; power analysis và gate. Nếu trượt, tìm pool khác trước khi viết DART.
3. Khi qua gate, triển khai DART tối thiểu và các baseline cùng input/audit/cost; chạy leakage/unit tests.
4. Thu feedback judge thật cho history và dựng attack schedule; chỉ tune trên development.
5. Freeze primary contrast, budget và code; chấm xác nhận, ablation, robustness, rồi independent replication.
6. Nếu gate phương pháp trượt, dừng claim DART superior và phát triển HistRepEval như bài đo lường giới hạn của history với kết quả âm trung thực.

**Ước lượng:** một kiểm tra pool công khai có thể làm trong vài ngày nếu bundle hợp lệ; triển khai, audit, xác nhận độc lập và bài viết mạnh cần thêm nhiều tuần. Hạn bản thảo 11/10 trong kế hoạch gốc không phải cơ sở để bỏ qua các gate. Không có thiết kế thí nghiệm nào bảo đảm DART thắng hay bảo đảm hội nghị nhận bài.
