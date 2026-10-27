# RepGuard: chiến lược nghiên cứu cho một bài hội nghị mạnh

**Ngày:** 07/10/2026, giờ Việt Nam. **Trạng thái:** đề xuất nghiên cứu sau các
gate đã hoàn tất; không phải protocol preregistered cho một run mới và không
phải lời hứa acceptance. Các ngưỡng bên dưới cần được chốt trong protocol của
từng study trước khi mở nhãn tương ứng.

## 1. Phán đoán khoa học hiện tại

Week 3 chạy thật 18.064 response trên đủ 14 môn MMLU-Pro; ECRT gần như hòa
FixedBorrow ở endpoint chính (+0,02 điểm %, CI95 [−0,04; +0,10]). DART trên
AppWorld archived normal 168 task có tín hiệu tốt nhất ở 10% gold với paired
CFJudgeFactor 74,15/168, nhưng CI so UniformAuditGlobal còn chứa zero và gate
vẫn FAIL. MATH500 pilot chứng minh judge có pair signal, nhưng best fixed và
oracle cùng 46/48 nên không có accuracy headroom trên sáu solver execution đó.
FinQA 200 câu/20 model có best fixed 74% và oracle 88,5%; pilot judge 48×20 có
pair ratio 1,0454 (FAIL), consensus trên 48 câu khác đạt 0,9234 (vẫn FAIL
so gate ≤0,90 và CI upper<1). Các run này là development, không phải một lần
test độc lập của phương pháp hoàn chỉnh.

**Quyết định:** xây **một bài có trục chính là giá trị ra quyết định của
feedback lịch sử không hoàn hảo**, với HistRepEval như giao thức/benchmark và
một thuật toán audit có điều kiện như ứng viên. Chỉ đưa DART vào title/abstract
như một method thắng khi nó qua gate độc lập. Nếu method không qua, đóng bài
measurement/benchmark bằng một phát hiện thực nghiệm rộng và tái lập được;
không đổi tên một baseline thắng thành DART. Cả hai đường đều cần thêm dữ liệu
và kiểm chứng. Không có đường nào đảm bảo nhận bài A/A*.

## 2. Vì sao một router/reputation score mới đơn thuần chưa đủ

- [LLMRouterBench, Findings ACL 2026](https://aclanthology.org/2026.findings-acl.1881/)
  đã có >400K instances, 21 datasets, 33 models và 10 routing baselines; bài
  báo cáo nhiều router không vượt best single một cách đáng tin. Dùng lại
  archive của họ không tự thành benchmark mới. HistRepEval phải đánh giá một
  trục khác: provenance/lỗi của *feedback lịch sử*, budget audit, giá trị
  quyết định, lỗi tương quan và chi phí tạo proxy.
- [RouteLLM, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5503a7c69d48a2f86fc00b3dc09de686-Abstract-Conference.html)
  và [R2-Router, ICML 2026](https://proceedings.mlr.press/v306/xue26h.html)
  làm prompt routing và quality–cost ở các cấu hình reasoning/budget. Nếu claim
  router theo từng câu, phải so đúng quyền truy cập prompt và cùng chi phí.
- [Ao et al., 2026](https://arxiv.org/abs/2601.21471) đã nghiên cứu LLM
  judge sai lệch + gold audit chọn lọc + correction/propensity + close-arm BAI.
  [PROBE, 2026](https://arxiv.org/abs/2607.06879) đã dùng proxy để giảm
  sample complexity best-arm identification. [Active Statistical Inference,
  ICML 2024](https://proceedings.mlr.press/v235/zrnic24a.html) đã phát triển
  suy luận thống kê với nhãn lấy chủ động. Vì vậy chỉ ghép ridge, proxy,
  paired audit hoặc confidence bound không đủ novelty.
- [Xia và Wang, 2026](https://arxiv.org/abs/2606.14200) đã phân tích
  reputation theo skill và rủi ro cross-skill laundering; ECRT cần đối chiếu
  trực tiếp cơ chế đó nếu giữ claim transfer/trust.
- [LLM Judges Can Be Too Generous Without a Reference, 2026](https://arxiv.org/abs/2607.12885)
  là cảnh báo liên quan tới FP judge quan sát trong dự án. Đây là động cơ kiểm
  chứng có reference/tool, không phải bằng chứng một prompt thinking sẽ sửa lỗi.

**Khoảng trống khả thi cần kiểm tra:** trong một *ma trận nhiều model trên cùng
task* với feedback proxy có lỗi chung, khi nào proxy giúp chọn model tốt hơn
gold-only ở ngân sách thực? Có thể phát hiện trước lúc quyết định rằng proxy
đang không có giá trị không? Một benchmark đo đầy đủ *answer quality →
pairwise signal → decision → cost/harm* trên nhiều chế độ sẽ khác một bảng
routing accuracy thuần túy. Một method chỉ có claim mạnh nếu cải thiện thêm
so các comparator proxy-aware gần nhất trên chính giao thức đó.

## 3. Định nghĩa bài toán thực tế trước khi chọn thuật toán

**Study chính nên là chọn một default model từ lịch sử cho workload tương lai.**
Một tổ chức đã có nhiều execution lịch sử và feedback tự động rẻ, muốn audit
một phần bằng nhãn đáng tin trước khi chọn model mặc định. Ở deployment, method
chỉ có history, proxy, nhãn đã mua, metadata có trước quyết định và chi phí;
không thấy gold của future tasks. Tính tổng tiền/compute cho việc tạo lịch sử
nếu phải thu mới, song báo riêng trường hợp lịch sử đã tồn tại. Câu hỏi có ý
nghĩa: đạt accuracy/regret nào với B nhãn audit và tổng chi phí nào?

Không gọi study đó là **router theo từng prompt**. Nếu muốn claim contextual
DART, phải có một study khác: router chọn trước khi chạy solver trên câu test,
chỉ từ prompt/history, so với RouteLLM, R2-Router, kNN retrieval, best single,
fallback và cost-matched extra solver. Không dùng 20 output của câu test để
quyết định rồi tính chi phí như một solver call. Ưu tiên giải xong global
selection trước; nhánh contextual chỉ mở khi có tín hiệu prompt-only ở dev.

## 4. Phương pháp ứng viên: paired, incumbent-preserving audit

Đây là *đề xuất cần implement và kiểm chứng*, chưa phải DART đã thắng.

1. Từ history proxy, chọn incumbent mạnh và một tập nhỏ challenger theo rule
   khóa trước; dành một phần ngân sách cho audit ngẫu nhiên có xác suất dương
   để giữ coverage, phần còn lại cho câu mà chênh proxy giữa incumbent và
   challenger không chắc hoặc hai nguồn proxy mâu thuẫn. Audit **cùng task**
   cho hai model để loại bớt biến động do độ khó task.
2. Với mỗi cặp, ước lượng chênh reward bằng mean proxy difference cộng
   residual difference trên paired gold đã audit. Ghi xác suất inclusion và
   đếm **hai nhãn** cho một cặp task–model. Chọn cơ chế estimation/CI hợp lệ
   với sampling design đã khóa; nếu adaptive theo gold trước đó, không áp
   công thức uniform sai. Tách dữ liệu chọn challenger/hiệu chuẩn khỏi dữ liệu
   chứng nhận switch, hoặc dùng suy luận tuần tự hợp lệ và multiple-comparison
   control.
3. Chỉ đổi incumbent khi bằng chứng về gain qua ngưỡng đã khóa sau khi tính
   cost/harm. Nếu không, giữ incumbent. Đây là *quy tắc quyết định thận
   trọng*, không phải bảo đảm an toàn đã được chứng minh. Phải kiểm tra rule
   này trước **gold-only paired/adaptive**, RawJudge, consensus, Ao-inspired
   proxy audit, PROBE-inspired control trong phạm vi giả định áp dụng, và một
   conservative incumbent rule không dùng proxy.
4. Thử một **verifier độc lập, một lần mỗi câu** trên FinQA development mới:
   giải hoặc kiểm tra số học chỉ từ prompt, không thấy candidate answers,
   model ID hay gold; sau đó so với parsed predictions. Đây là giả thuyết sửa
   lỗi candidate-conditioned judge và shared wrong answer. Khóa model/digest,
   thinking, extraction, abstention, token cap, retry và chi phí trước khi gọi.
   Pilot nhỏ phải vượt pair-signal gate trước khi mua hàng nghìn call. Nếu
   verifier sai/đắt, dừng nhánh này; không biến proxy chưa qua gate thành
   tiền đề mặc định của method.

Một novelty method có thể bảo vệ được, **nếu thực nghiệm ủng hộ**, là chứng
nhận quyết định incumbent/challenger dưới shared-task dependence, proxy bias,
multiple proxy sources và audit budget cố định. Phải chứng minh phần nào mới
so Ao/PROBE/active inference; nếu chỉ là bản thích ứng, mô tả trung thực là
baseline tốt trong một bài benchmark.

## 5. Dữ liệu, chia tập và quyền truy cập

1. **Development đã xem:** Week 3 MMLU test 2.416, MMLU dev 560, AppWorld
   normal 168, MATH500 pilot48, FinQA/MBPP headroom200 (gồm hai FinQA pilot
   48). Chỉ dùng để đặt giả thuyết, debug và ước lượng phương sai. Không gọi
   bất kỳ kết quả mới trên các tập này là independent confirmation.
2. **Inventory ngoài pool dev:** theo packet đã kiểm chứng, FinQA có **929**
   và MBPP **766 unique eligible** câu ngoài 200 development; con số 938/770
   trong vài tài liệu cũ tính cả hash trùng đã loại. Trước chia mới, nhóm
   exact/near-duplicate bằng prompt/template *không xem score*, rồi khóa nhóm
   vào các partition. Cỡ mỗi partition phải điều chỉnh sau grouping.
3. **Gợi ý quota trước grouping:** FinQA 100 câu proxy pilot, 100 câu method
   development, khoảng 700 câu final, còn lại reserve; MBPP 80/80/khoảng
   600/reserve. Có thể dùng pool 200 câu cũ cho phát triển nhưng đánh dấu
   nó là đã xem gold. Giữ phần lớn các câu unique mới cho final để phép so
   vài điểm phần trăm có đủ độ chính xác. Đây là kế hoạch phân bổ,
   **chưa phải split đã khóa**. Chỉ
   freeze hash/IDs sau kiểm tra duplicate và giấy phép. MBPP cần proxy/verifier
   phù hợp code; không chuyển nguyên FinQA numeric parser sang code.
4. Giữ MMLU sealed 420 như một study khác theo protocol cũ; không mở nó để
   chữa các gate MMLU đã trượt. AppWorld archived normal 168 đã dùng thích
   nghi nhiều lần và chỉ là development/transfer stress test; một claim
   interactive cần pool khác và evaluation mới. Không trộn AppWorld 0.1/0.2
   hoặc raw archived solver outcomes với pilot solver mới như cùng protocol.
5. **Release/licensing gate:** archive RouterBench chưa có quyền phát hành raw
   derivatives được chứng nhận trong audit local. Chốt quyền sử dụng và cách
   trích dẫn với nguồn trước khi lập benchmark package; nếu không thể
   redistribute raw, phát hành code/manifest/checksum và hướng dẫn lấy dữ
   liệu từ tác giả, hoặc thu lại execution trên nguồn có quyền phù hợp. Raw
   AppWorld task content cũng phải tuân theo điều kiện của project gốc.

## 6. Endpoints, controls và tiêu chuẩn bài mạnh

**Primary cho method:** ở 10% gold audit trên history, accuracy hoặc simple
regret của model được chọn trên *future held-out tasks*, với giới hạn tổng
chi phí tương đương. Khóa một practical improvement floor, gợi ý **≥3 điểm
phần trăm**, và yêu cầu paired CI95 lower >0 trước (i) gold-only control mạnh
nhất đã đăng ký và (ii) proxy-aware comparator mạnh nhất đã đăng ký. Đây là
ngưỡng đề xuất; phải power-check bằng discordance/group counts trên dev, rồi
khóa trước final. Nếu effect nhỏ hơn độ chính xác mẫu final cho phép, bài
không thể claim superiority tin cậy bằng cách tăng số seeds trên cùng task.

**Secondary bắt buộc:** accuracy–total-cost frontier; số nhãn gold đến khi
đạt regret cho trước; tỷ lệ switch, rescue, harm và worst-group harm; Brier
và *pairwise residual variance*; reliability diagram của proxy, missing
answers, correlated shared errors; token/latency/retries/judge dollars nếu
có hóa đơn. Báo riêng gold already archived và gold thật phải mua. Một
bootstrap của fitted predictions không chứng minh tính đúng của adaptive
sampling hay generalization across datasets.

**Baselines:** best single chọn bằng **đúng B nhãn train được cấp**;
best single nhìn toàn bộ train gold chỉ là upper reference. Thêm uniform/paired global,
IndependentSH/PairedSH, gold-only structured model, raw proxy, calibrated
proxy, residual correction, conservative gold-only switch, Ao-style
proxy-assisted audit, PROBE khi giả định tương thích, và prompt routers nếu
có claim contextual. Cấp cùng dữ liệu được phép và cùng *tổng* budget; nếu
không thể tái hiện một prior method trung thực, ghi rõ protocol adaptation.
Không gọi một control hậu kiểm là phương pháp mới của mình.

**Statistics:** unit là task hoặc near-duplicate group/generator; các seed
audit trên cùng task không là n độc lập. Tính paired differences và CI,
stratify theo dataset; báo kết quả riêng từng dataset, không chỉ pooled.
Khóa thứ tự kiểm định hoặc điều chỉnh nhiều primary comparisons. Với 500 câu
FinQA, một hiệu ứng cỡ 1 điểm % khó chứng minh; xác nhận cần effect thực
tiễn đủ lớn và nhiều task độc lập, không chỉ thêm compute huấn luyện.

## 7. Mốc làm việc và điều kiện dừng

| Mốc | Việc phải hoàn tất | Quyết định |
|---|---|---|
| A. Evidence hygiene | Split/group metadata, license, data card, cost ledger; khóa primary question và controls | Nếu không có quyền tái lập/phát hành khả thi, sửa nguồn dữ liệu trước khi mở gold |
| B. Proxy pilot | Verifier FinQA trên development *mới*, đối chứng no-reference judge và consensus, báo pair signal/coverage/cost | Chỉ mở rộng nếu proxy cải thiện pair contrasts đủ lớn và đáng chi phí; nếu FAIL giữ gold-only track |
| C. Method development | Implement paired incumbent audit và full controls; kiểm thử leakage, budget, propensity, resume; chạy trên dev đã khóa | Giữ tối đa một version finalist; nếu không vượt controls và practical floor, không mở final cho claim DART |
| D. Final confirmation | Freeze code, hashes, prompt, baselines và analysis; chấm một lần trên held-out FinQA+MBPP hoặc nguồn đã chốt | Chỉ claim method nếu cả primary contrasts và cost/ablation đạt; báo FAIL nguyên vẹn nếu không |
| E. Paper/release | External replication, benchmark card, repo artifacts, error audit, limitations | Chọn method+benchmark hoặc measurement paper theo kết quả, không theo mong muốn trước đó |

### Nếu method FAIL: HistRepEval cần mạnh đến mức nào?

Một bài measurement vẫn phải có ít nhất hai nguồn task khác bản chất, một
inventory đa model, nhiều nguồn feedback thật và can thiệp có kiểm soát,
metadata/licensing rõ, independent rerun và một finding khó thấy từ accuracy
tables thông thường. Candidate finding hiện nay là sự **đứt gãy giữa
calibration và decision value** và tác hại của **shared-error proxies**;
phải lặp lại ngoài các pilot đã xem trước khi viết thành kết luận tổng quát.
HistRepEval cần đo được điều kiện nào dùng history có ích, vô ích hoặc gây
hại, và cung cấp baselines đơn giản đủ mạnh để người dùng thực tế ra quyết
định về audit/solver cost. Một tập hợp failure cases không đủ làm bài A/A*.

## 8. Bước đầu tiên cụ thể

Viết và review một **protocol evidence gate** cho FinQA verifier pilot trước
khi gọi model: nguồn 100 câu mới chọn bằng hash/group, 20 model cố định,
judge độc lập không thấy candidate/gold, quy tắc parse/abstain, pair metric,
coverage, token/cost cap, negative controls, bootstrap theo câu và điều kiện
STOP. Cùng lúc audit điều kiện phát hành của RouterBench và tạo bảng quyền
truy cập cho từng baseline. Đây là bước nhanh nhất để biết một nguồn proxy
mới có thực sự khắc phục được lỗi trực tiếp của FinQA judge/consensus hay
không; nếu FAIL, không tiêu thêm ngân sách vào một DART dựa trên proxy đó.
