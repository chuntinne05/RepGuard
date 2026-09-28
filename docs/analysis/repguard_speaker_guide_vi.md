# RepGuard — Cẩm nang thuyết trình chi tiết bằng tiếng Việt

## Cách sử dụng tài liệu này

Tài liệu này là speaker guide cho bài bảo vệ đề cương **RepGuard: Evidence-Calibrated Reputation Transfer under Imperfect Feedback in Multi-Agent LLM Systems**. Mỗi slide gồm năm phần: mục tiêu, nội dung cần hiểu, cách đọc hình, lời thoại gợi ý và điểm cần tránh nói quá. Phần lời thoại không cần học thuộc từng chữ; hãy nắm logic và diễn đạt tự nhiên.

Thời lượng mục tiêu của deck là 15–18 phút. Với 21 slide, các slide nội dung chính nên nói khoảng 40–70 giây; slide tiêu đề và slide chuyển phần chỉ cần 10–25 giây. Đây là **đề cương nghiên cứu**, vì vậy các câu như “ECRT tốt hơn” phải được trình bày dưới dạng giả thuyết hoặc tiêu chí thành công, không phải kết quả đã được chứng minh.

### Ba khái niệm xuyên suốt

- **Feedback reliability — độ đáng tin của phản hồi:** phản hồi lịch sử có phản ánh đúng chất lượng câu trả lời hay không. Một judge có thể khen nhầm câu sai hoặc chê nhầm câu đúng.
- **Task relevance / transferability — độ liên quan hay khả năng chuyển giao:** bằng chứng thành công trong quá khứ có hữu ích để suy ra năng lực ở tác vụ hiện tại hay không.
- **Calibrated influence — mức ảnh hưởng được hiệu chỉnh:** mức ảnh hưởng phải tương xứng với xác suất agent thật sự đúng và với độ chắc chắn của bằng chứng. “Được tin 70%” nên có ý nghĩa gần với “đúng khoảng 70% trong những trường hợp tương tự”.

### Câu mô tả luận văn trong 20 giây

> RepGuard nghiên cứu cách một hệ multi-agent học reputation từ lịch sử khi phản hồi có thể sai và lịch sử có thể không liên quan đến tác vụ mới. Luận văn tách độ đáng tin của phản hồi khỏi độ liên quan của tác vụ, kiểm chứng tương tác giữa hai yếu tố bằng thí nghiệm có kiểm soát, rồi dùng chúng để tạo mức ảnh hưởng có uncertainty thay vì một điểm trust đơn giản.

---

## Slide 1 — Title: RepGuard

### Mục tiêu của slide

Giới thiệu tên đề tài, phạm vi nghiên cứu và câu hỏi trực giác mà người nghe có thể hiểu ngay cả khi chưa biết các công thức phía sau.

### Nội dung trên slide nói gì?

**RepGuard** là tên ngắn của hướng nghiên cứu. “Reputation” là danh tiếng hoặc mức tin cậy tích lũy từ lịch sử. “Guard” nhấn mạnh mục tiêu bảo vệ quá trình chuyển reputation thành quyền ảnh hưởng.

**Evidence-Calibrated Reputation Transfer** có thể hiểu là “chuyển giao reputation có hiệu chỉnh theo chất lượng bằng chứng”. Không lấy một điểm danh tiếng toàn cục rồi áp dụng cho mọi tác vụ; trước hết phải hỏi bằng chứng có đáng tin không và có liên quan không.

**Under Imperfect Feedback** nghĩa là feedback không được giả định hoàn hảo. Feedback có thể đến từ đáp án tham chiếu, unit test, công cụ, môi trường, người dùng hoặc LLM-as-a-judge. Mỗi nguồn có thể có false positive, false negative hoặc bị thao túng.

**Multi-Agent LLM Systems** là hệ gồm nhiều agent sử dụng mô hình ngôn ngữ, công cụ, vai trò hoặc scaffolding khác nhau để cùng giải quyết tác vụ.

### Cách đọc hình

Các node là những agent; các cạnh là quan hệ trao đổi hoặc trust. Cạnh khác màu biểu thị một quan hệ chưa chắc chắn: hệ thống quan sát một tín hiệu lịch sử, nhưng chưa biết tín hiệu đó đúng đến đâu hoặc có nên chuyển sang tác vụ hiện tại không.

### Lời thoại gợi ý

> Em xin trình bày đề tài RepGuard. Câu hỏi trung tâm rất đơn giản: một AI teammate phải làm gì để xứng đáng nhận được nhiều ảnh hưởng hơn, khi chính bằng chứng dùng để đánh giá nó có thể không đáng tin và có thể không liên quan đến nhiệm vụ mới? Đề tài tách hai vấn đề này, xây dựng mô hình bằng chứng có uncertainty, và kiểm tra tác động của nó trong các đội LLM đa tác tử.

### Chuyển sang slide 2

> Để trả lời câu hỏi đó, em sẽ đi từ bối cảnh, đến khoảng trống nghiên cứu, phương pháp đề xuất, thiết kế đánh giá và cuối cùng là kế hoạch thực hiện.

---

## Slide 2 — Agenda

### Mục tiêu của slide

Tạo bản đồ cho người nghe. Sáu mục không phải sáu chủ đề rời rạc mà là một chuỗi lập luận.

### Sáu phần cần hiểu

1. **Context:** Vì sao đội agent không thể chỉ bỏ phiếu đều và cần biết ai có chuyên môn phù hợp.
2. **Problem:** Reputation có vẻ là lời giải tự nhiên, nhưng dữ liệu lịch sử không sạch.
3. **Research gap:** Literature đã nghiên cứu trust, skill conditioning, attacks và unreliable feedback, nhưng chưa kiểm soát hai chiều reliability × relevance như một đối tượng thực nghiệm riêng.
4. **Proposed direction:** ECRT ước lượng chất lượng bằng chứng, độ liên quan và uncertainty trước khi chuyển thành influence.
5. **Evaluation:** Thiết kế ma trận 2D, benchmark, baseline, metric và stress test.
6. **Roadmap and success:** Mốc go/no-go, phương án dự phòng và định nghĩa thành công khoa học.

### Lời thoại gợi ý

> Bài nói có hai tầng. Năm slide đầu giải thích trực giác ở mức executive. Phần giữa chính thức hóa vấn đề và phương pháp. Phần cuối trả lời ba câu hỏi thực tế: kiểm thử thế nào, khi nào nên dừng hoặc đổi hướng, và kết quả nào được xem là đóng góp khoa học hợp lệ.

### Điểm cần tránh

Không đọc từng mục như mục lục. Chỉ cần cho hội đồng biết mạch lập luận và nhấn mạnh rằng đây là đề cương evidence-first.

---

## Slide 3 — The Setting: Multi-Agent LLM Teams

### Mục tiêu của slide

Giải thích vì sao “có nhiều agent” chưa đủ; giá trị đến từ việc sử dụng đúng agent ở đúng tác vụ.

### Kiến thức cần nắm

**Heterogeneous agents** là các agent không đồng nhất. Sự khác biệt có thể nằm ở:

- **Backbone:** mô hình nền khác nhau, ví dụ mô hình mạnh về reasoning so với mô hình nhanh và rẻ.
- **Tools:** agent có quyền truy cập code executor, search, database, calculator hoặc API khác nhau.
- **Scaffolds:** prompt hệ thống, bộ nhớ, quy trình critique, planning hoặc kiểm tra khác nhau.
- **Specializations:** agent được tối ưu hoặc có lịch sử tốt ở code, toán, luật, y khoa, v.v.

Không có agent nào mặc nhiên tốt nhất trên mọi miền. Vì vậy bài toán của hệ thống không chỉ là tạo nhiều câu trả lời mà còn là **routing influence**: quyết định câu trả lời hoặc lập luận của ai nên tác động nhiều hơn đến kết quả cuối.

### Cách đọc hình

Nút trung tâm là task. Các agent Code, Math, Law và Medicine có profile năng lực khác nhau. Đường đậm tới một agent thể hiện hệ thống định tuyến ảnh hưởng cho chuyên gia phù hợp. Đường mảnh không có nghĩa các agent kia vô dụng; chỉ có nghĩa chúng nên đóng vai trò ít hơn trong tác vụ hiện tại.

### Ví dụ dễ hiểu

Nếu câu hỏi là kiểm tra lỗi Python, agent Code có lịch sử đáng tin trong debugging nên được cân nặng cao. Nhưng nếu câu hỏi chuyển sang phân tích điều khoản hợp đồng, lịch sử Python không đủ để trao cùng mức trust; agent Law có thể phù hợp hơn.

### Lời thoại gợi ý

> Multi-agent chỉ có lợi khi sự đa dạng được khai thác. Nếu tất cả agent được bỏ phiếu như nhau, một chuyên gia đúng có thể bị ba agent không phù hợp lấn át. Do đó, vấn đề quan trọng không phải chỉ là “đội có chuyên gia không”, mà là “hệ thống có nhận diện và sử dụng đúng chuyên gia không”.

### Chuyển sang slide 4

> Và đây chính là điểm bất ngờ: nghiên cứu gần đây cho thấy ngay cả khi chuyên gia đã có mặt, đội LLM vẫn có thể không tận dụng được họ.

---

## Slide 4 — The Twist: Having an Expert ≠ Using the Expert

### Mục tiêu của slide

Chuyển bài toán từ capability sang coordination. Một đội có đủ năng lực thành phần vẫn có thể thất bại ở khâu tổng hợp ảnh hưởng.

### Kết quả nghiên cứu liên quan

Pappu và cộng sự nghiên cứu các đội LLM tự tổ chức và báo cáo rằng đội thường không đạt được hiệu năng của agent chuyên gia tốt nhất, ngay cả khi được cho biết ai là chuyên gia. Bài báo quy phần lớn thất bại cho **expert leveraging** hơn là **expert identification**: đội có thể biết ai đúng nhưng vẫn pha loãng câu trả lời đúng bằng “integrative compromise”, tức cố dung hòa các ý kiến thay vì đặt trọng số tương xứng cho chuyên môn.[^1]

Con số “tổn thất tới 37,6%” trong abstract của bài báo có thể dùng khi cần tạo ấn tượng, nhưng phải nói rõ đó là kết quả trong thiết lập và benchmark của nghiên cứu, không phải quy luật cho mọi hệ multi-agent.[^1]

### Cách đọc Before/After

- **Before:** chuyên gia đúng có mặt nhưng đường ảnh hưởng mờ; ý kiến của nhiều agent được trộn gần như ngang nhau, nên accuracy thấp hơn.
- **After:** reputation giúp tăng trọng số của agent có bằng chứng năng lực phù hợp; team decision có cơ hội tốt hơn.

Hình “After” minh họa động cơ nghiên cứu, chưa phải kết quả ECRT đã được chứng minh.

### Capability problem và coordination problem khác nhau thế nào?

- Capability problem: không agent nào biết đáp án đúng.
- Coordination problem: ít nhất một agent biết hoặc có xác suất đúng cao, nhưng hệ thống không trao đủ ảnh hưởng cho agent đó.

### Lời thoại gợi ý

> Nếu không agent nào giải được bài, đó là thiếu capability. Nhưng nếu một agent giải đúng mà đội vẫn chọn sai, đó là coordination failure. Reputation là lời giải tự nhiên: agent từng đúng sẽ dần nhận nhiều ảnh hưởng hơn. Tuy nhiên, lời giải này chỉ hoạt động nếu lịch sử dùng để tạo reputation là đáng tin và có liên quan.

---

## Slide 5 — But Reputation Needs History, and History Isn't Clean

### Mục tiêu của slide

Giới thiệu hai chiều độc lập của bằng chứng lịch sử: **reliability** và **relevance**.

### Câu hỏi thứ nhất: phản hồi lịch sử có đúng không?

Ta không trực tiếp thấy “agent thật sự đúng”; ta thấy một feedback. Nếu judge có false positive, câu trả lời sai có thể được thưởng và tạo **false reputation**. Nếu judge có false negative, agent tốt có thể bị đánh giá thấp.

Ví dụ: unit test chỉ kiểm tra happy path. Agent viết code vượt qua test nhưng vẫn sai ở edge case. Feedback “pass” là tín hiệu quan sát được nhưng không tương đương hoàn toàn với correctness thật.

### Câu hỏi thứ hai: thành công có liên quan tới task mới không?

Một kết quả lịch sử có thể được đánh giá hoàn toàn chính xác nhưng không chuyển giao. Giỏi Python debugging không tự động suy ra giỏi legal reasoning. Ngay trong cùng miền code, sửa lỗi syntax có thể không dự đoán tốt năng lực thiết kế hệ thống phân tán.

### Ma trận 2×2

| | Relevance thấp | Relevance cao |
|---|---|---|
| Reliability thấp | Không nên tin: vừa nhiễu vừa không liên quan | Có vẻ đúng miền nhưng feedback không đủ đáng tin |
| Reliability cao | Đánh giá đúng nhưng sai miền | Bằng chứng mạnh nhất để chuyển thành influence |

Hai trục độc lập có nghĩa tăng reliability không tự làm tăng relevance và ngược lại.

### Lời thoại gợi ý

> Một track record có thể reliable nhưng irrelevant, hoặc relevant nhưng unreliable. Nếu gom cả hai vào một điểm reputation, hệ thống không biết điểm đó thấp vì judge kém hay vì task khác miền. RepGuard xem đây là hai câu hỏi bằng chứng riêng biệt.

### Câu hội đồng có thể hỏi

**“Reliability và relevance có thực sự độc lập không?”** Trả lời: trong dữ liệu thực chúng có thể tương quan, nhưng thiết kế thí nghiệm chủ động thao tác độc lập để đo main effect và interaction. “Độc lập” ở đây là độc lập về mặt khái niệm và biến thực nghiệm, không khẳng định độc lập thống kê trong mọi dữ liệu tự nhiên.

---

## Slide 6 — Section Divider: The Problem, Precisely

### Mục tiêu của slide

Đánh dấu chuyển từ trực giác executive sang phát biểu kỹ thuật. Không cần thêm nội dung mới.

### Lời thoại gợi ý

> Phần vừa rồi cho thấy động cơ. Bây giờ em sẽ chính thức hóa: hệ thống quan sát gì, điều gì bị ẩn, và quyết định cuối cùng cần tính là gì.

---

## Slide 7 — Formalizing the Question

### Mục tiêu của slide

Chuyển vấn đề trực giác ở Slide 5 thành một bài toán có thể mô hình hóa và kiểm nghiệm. Slide này cần giúp người nghe phân biệt rõ ba lớp thông tin:

1. Điều hệ thống **quan sát được** trong lịch sử.
2. Điều hệ thống **muốn biết nhưng không quan sát trực tiếp được**.
3. Quyết định hệ thống **phải đưa ra** khi xuất hiện nhiệm vụ mới.

### Giải thích từng biến

Một lần tương tác trong lịch sử của tác tử $i$ tại thời điểm $t$ được biểu diễn bằng:

$$
h_{it}=(q_t,y_{it},x_t,F_{it}).
$$

- $i$ là chỉ số của **tác tử**. Ví dụ, tác tử 1 chuyên lập trình, tác tử 2 chuyên toán, tác tử 3 chuyên luật.
- $t$ là chỉ số của **lần tương tác trong lịch sử**. Một tác tử có thể đã tham gia hàng trăm nhiệm vụ ở những thời điểm khác nhau.
- $q_t$ là **nhiệm vụ hoặc câu hỏi** ở lần tương tác thứ $t$. Đây là nội dung mà cả nhóm cần giải quyết.
- $y_{it}$ là **câu trả lời hoặc hành động** mà tác tử $i$ đưa ra cho nhiệm vụ $q_t$.
- $x_t$ là **thông tin mô tả nhiệm vụ**: lĩnh vực, kỹ năng cần dùng, độ khó, loại công cụ, dạng suy luận hoặc biểu diễn số của nội dung. Thành phần này giúp hệ thống đánh giá nhiệm vụ cũ có liên quan đến nhiệm vụ mới hay không.
- $F_{it}$ là **phản hồi mà hệ thống thực sự quan sát được** về câu trả lời $y_{it}$. Phản hồi có thể là đạt/không đạt, điểm của mô hình chấm, kết quả kiểm thử chương trình, trạng thái môi trường sau hành động hoặc đánh giá của người dùng.
- $z_{it}\in\{0,1\}$ là **tính đúng đắn thực sự** của câu trả lời: $z_{it}=1$ nếu đúng và $z_{it}=0$ nếu sai.
- $q^*$ là **nhiệm vụ mới** mà hệ thống đang cần giải quyết.
- $w_i$ là **trọng số ảnh hưởng** được cấp cho tác tử $i$ trên nhiệm vụ mới. Trọng số càng lớn thì câu trả lời, lập luận hoặc lá phiếu của tác tử đó càng tác động mạnh đến quyết định chung.

### Vì sao $z_{it}$ được gọi là biến ẩn?

Trong quá trình vận hành thực tế, hệ thống thường không được nhìn trực tiếp vào “đáp án đúng tuyệt đối”. Nó chỉ nhìn thấy phản hồi $F_{it}$. Vì vậy, $F_{it}$ và $z_{it}$ không được xem là một.

Ví dụ, một chương trình vượt qua năm ca kiểm thử thì hệ thống quan sát được phản hồi “đạt”. Tuy nhiên, chương trình vẫn có thể sai ở trường hợp biên chưa được kiểm thử. Khi đó $F_{it}$ là tích cực nhưng $z_{it}$ vẫn có thể bằng 0. Ngược lại, một mô hình chấm có thể hiểu nhầm một đáp án đúng và cho điểm thấp.

“Biến ẩn” không có nghĩa là không bao giờ biết được. Trong thí nghiệm ngoại tuyến, bộ dữ liệu chuẩn có thể cung cấp đáp án đúng để nhà nghiên cứu xác định $z_{it}$ và đánh giá phương pháp. Tuy nhiên, thông tin đó chỉ dùng để **chấm kết quả sau cùng**, không được đưa trực tiếp vào cơ chế học uy tín; nếu không, bài toán phản hồi không hoàn hảo đã bị loại bỏ một cách giả tạo.

### Hệ thống thực sự phải suy luận điều gì?

Từ lịch sử $h_{it}$, hệ thống cần thực hiện ba bước suy luận riêng:

1. **Đánh giá độ đáng tin của phản hồi:** phản hồi $F_{it}$ cho thấy câu trả lời đúng với xác suất bao nhiêu? Nói cách khác, cần ước lượng $P(z_{it}=1\mid F_{it},x_t,\ldots)$ thay vì mặc định phản hồi chính là sự thật.
2. **Đánh giá khả năng chuyển giao:** bằng chứng ở nhiệm vụ $q_t$ có liên quan đến nhiệm vụ mới $q^*$ đến mức nào? Một lần làm đúng bài Python có thể hữu ích cho bài sửa lỗi Python mới, nhưng gần như không nói lên năng lực phân tích hợp đồng.
3. **Chuyển bằng chứng thành ảnh hưởng:** sau khi xét cả độ đáng tin và độ liên quan, tác tử $i$ nên nhận trọng số $w_i$ bao nhiêu? Nếu bằng chứng ít hoặc không chắc chắn, hệ thống phải giữ trọng số thận trọng thay vì tin mạnh.

### Ví dụ xuyên suốt

Giả sử tác tử A từng viết một đoạn mã cho nhiệm vụ $q_t$. Câu trả lời của A là $y_{At}$. Bộ kiểm thử báo “đạt”, tức $F_{At}=1$. Tuy nhiên, bộ kiểm thử chỉ bao phủ một phần trường hợp nên hệ thống ước lượng xác suất lời giải thật sự đúng là 0,8 chứ không phải 1.

Nhiệm vụ mới $q^*$ cũng là sửa lỗi Python và khá giống nhiệm vụ cũ, nên bằng chứng này có độ liên quan cao. Khi đó lịch sử trên có thể làm tăng $w_A$. Nếu $q^*$ là câu hỏi luật, cùng phản hồi “đạt” ấy vẫn đáng tin về nhiệm vụ cũ, nhưng gần như không nên làm tăng ảnh hưởng của A trên nhiệm vụ luật. Ví dụ này cho thấy **độ đáng tin của kết quả cũ** và **độ liên quan tới nhiệm vụ mới** là hai câu hỏi khác nhau.

### Trọng số $w_i$ được dùng ở đâu?

Tùy kiến trúc của hệ đa tác tử, $w_i$ có thể được dùng để:

- Nhân trọng số khi bỏ phiếu giữa các câu trả lời.
- Chọn tác tử nào được giao nhiệm vụ hoặc được cấp thêm lượt suy luận.
- Quyết định lập luận của tác tử nào được đưa vào bước tổng hợp cuối.
- Chọn câu trả lời cuối cùng từ nhiều phương án.

Trong thí nghiệm chính nên chọn một cách sử dụng trọng số thống nhất để tránh trộn lẫn hiệu quả của mô hình uy tín với hiệu quả của nhiều cơ chế phối hợp khác nhau.

### Lời thoại gợi ý

> Mỗi bản ghi lịch sử cho biết nhiệm vụ là gì, tác tử đã trả lời thế nào, nhiệm vụ có đặc điểm gì và hệ thống nhận được phản hồi gì. Nhưng điều quan trọng nhất là câu trả lời có thật sự đúng hay không thì lại bị ẩn. Vì vậy, khi nhiệm vụ mới xuất hiện, hệ thống không thể lấy phản hồi cũ làm sự thật rồi cộng thẳng vào điểm uy tín. Nó phải lần lượt hỏi: phản hồi cũ đáng tin đến đâu, nhiệm vụ cũ liên quan đến nhiệm vụ mới đến đâu, và với lượng bằng chứng hiện có thì tác tử nên nhận bao nhiêu ảnh hưởng. Đây chính là câu hỏi hình thức mà RepGuard muốn giải quyết.

### Các điểm dễ bị hỏi lại

- **Phản hồi và tính đúng đắn có giống nhau không?** Không. Phản hồi là tín hiệu quan sát được; tính đúng đắn thực sự là điều cần suy ra.
- **Nếu đã có đáp án chuẩn thì cần RepGuard làm gì?** Đáp án chuẩn chỉ có trong môi trường nghiên cứu để đánh giá. Khi triển khai, nhiều nhiệm vụ mở không có đáp án chuẩn ngay lập tức.
- **Tại sao cần $x_t$?** Nếu không có đặc trưng của nhiệm vụ, hệ thống khó xác định bằng chứng cũ nên chuyển sang nhiệm vụ mới ở mức nào.
- **Trọng số cao có nghĩa tác tử luôn đúng không?** Không. Nó chỉ biểu thị mức ảnh hưởng hợp lý theo bằng chứng hiện có và vẫn phải đi kèm độ không chắc chắn.

### Câu chuyển sang Slide 8

> Sau khi phát biểu rõ bài toán, câu hỏi tiếp theo là: những phần nào đã được các nghiên cứu trước giải quyết, và chính xác phần nào vẫn còn bỏ ngỏ?

---

## Slide 8 — What Already Exists (So We Don't Reinvent It)

### Mục tiêu của slide

Trình bày trung thực những hướng nghiên cứu đã có trước khi tuyên bố đóng góp mới. Slide này không nhằm nói rằng các công trình trước “làm sai”, mà nhằm chỉ ra mỗi hướng đã giải quyết một phần nào của bài toán và phần giao nào vẫn chưa được nghiên cứu đầy đủ.

### Cách đọc bảng

Mỗi hàng trong bảng nên được đọc theo ba câu hỏi:

1. Hướng nghiên cứu đó giải quyết vấn đề gì?
2. Kết quả đó giúp ích gì cho RepGuard?
3. Hướng đó còn thiếu gì so với câu hỏi trung tâm của luận văn?

### 1. Chấm điểm độ đáng tin từ lịch sử

**Điều đã giải quyết:** sử dụng các đóng góp hoặc kết quả trong quá khứ để ước lượng mức đáng tin của từng tác tử. Tác tử thường xuyên tạo ra kết quả tốt sẽ dần được ưu tiên hơn.

**Giá trị đối với RepGuard:** xác nhận rằng lịch sử là nguồn thông tin hữu ích để điều phối ảnh hưởng trong nhóm.

**Phần còn thiếu:** một điểm uy tín chung thường không cho biết phản hồi tạo ra điểm đó đáng tin đến đâu và bằng chứng thuộc loại nhiệm vụ nào. Một tác tử có thể đạt điểm cao nhờ nhiệm vụ dễ hoặc nhờ bộ chấm thiếu chính xác.

Tài liệu gốc gắn hướng này với “Ebrahimi và cộng sự, 2025”, nhưng hiện chưa có đủ tên bài báo, nơi công bố hoặc đường dẫn để xác minh chắc chắn. Cần hoàn thiện trích dẫn trước khi nộp.

### 2. Uy tín theo từng kỹ năng

**Điều đã giải quyết:** thay vì gán cho mỗi tác tử một điểm chung, hệ thống duy trì mức uy tín theo từng kỹ năng, chẳng hạn $R(i\mid k)$ là uy tín của tác tử $i$ đối với kỹ năng $k$. Cách này phản ánh đúng hơn thực tế rằng một tác tử có thể giỏi toán nhưng yếu luật.

Xia và Wang cho thấy việc điều kiện hóa uy tín theo kỹ năng đặc biệt hữu ích khi các tác tử có năng lực khác nhau, số quan sát trong từng kỹ năng còn ít và giữa các kỹ năng có mối liên hệ.[^2]

**Giá trị đối với RepGuard:** cung cấp nền tảng để xét mức độ liên quan giữa nhiệm vụ cũ và nhiệm vụ mới.

**Phần còn thiếu:** kết quả lịch sử thường vẫn được coi là đã xác minh. Nếu phản hồi ban đầu sai, việc phân loại đúng kỹ năng vẫn chỉ chuyển một bằng chứng sai vào đúng ngăn. Ngoài ra, việc mượn bằng chứng giữa các kỹ năng có thể bị lợi dụng để “rửa uy tín”: tích lũy thành tích ở kỹ năng dễ rồi đổi lấy ảnh hưởng ở kỹ năng quan trọng.

### 3. Uy tín biến đổi theo thời gian

**Điều đã giải quyết:** uy tín không nên tồn tại vĩnh viễn. Bằng chứng mới có thể quan trọng hơn bằng chứng quá cũ; năng lực và hành vi của tác tử có thể thay đổi. CogTrust sử dụng cơ chế giảm trọng số theo thời gian và tổng hợp bằng chứng theo nhiều cấp để theo dõi sự thay đổi này.[^3]

**Giá trị đối với RepGuard:** gợi ý cách xử lý độ mới của bằng chứng và hành vi thay đổi theo thời gian.

**Phần còn thiếu:** “cũ hay mới” là một chiều khác với “đáng tin hay không” và “có liên quan hay không”. Một bằng chứng rất mới vẫn có thể do bộ chấm sai tạo ra; một bằng chứng rất mới trong lĩnh vực luật vẫn không phù hợp để đánh giá năng lực lập trình.

### 4. Phát hiện tác tử có hành vi gây hại

**Điều đã giải quyết:** nhận diện tác tử hoặc thông điệp có dấu hiệu bất thường, phối hợp gây hại hoặc làm giảm chất lượng quyết định chung. SentinelNet sử dụng cơ chế phân bổ công trạng và xếp hạng động các tác tử lân cận để giảm tác động của mối đe dọa.[^4]

**Giá trị đối với RepGuard:** cung cấp các kịch bản đối kháng và cách đo khả năng chống chịu.

**Phần còn thiếu:** phát hiện tác tử xấu không đồng nghĩa với đánh giá đúng chất lượng của mọi bằng chứng lịch sử. Một tác tử trung thực vẫn có thể nhận phản hồi sai; ngược lại, tác tử có ý đồ xấu có thể cư xử tốt đủ lâu để tích lũy uy tín.

### 5. Tấn công vào cơ chế uy tín

**Điều đã giải quyết:** nghiên cứu cách một tác tử có thể tích lũy, thao túng hoặc khai thác uy tín để giành quyền ảnh hưởng. Các ví dụ gồm hành vi tốt trong giai đoạn đầu rồi phản bội, tạo thành tích ở kỹ năng nguồn rồi chuyển sang kỹ năng đích, hoặc thao túng phản hồi.

**Giá trị đối với RepGuard:** giúp xây dựng các phép thử sức chịu đựng cho phương pháp. Nếu một mô hình uy tín chỉ hoạt động khi mọi tác tử trung thực, mô hình đó chưa đủ đáng tin cho môi trường thực tế.

**Phần còn thiếu:** RepGuard không lấy việc phát hiện một kiểu tấn công mới làm đóng góp trung tâm. Các cuộc tấn công được dùng để kiểm tra xem mô hình bằng chứng có giảm được việc chuyển uy tín sai chỗ hay không.

Tên “WEREWOLF, EMNLP 2026” trong bản nội dung ban đầu chưa được xác minh bằng nguồn chính thức. Không nên phát biểu tên nơi công bố như một sự thật cho đến khi có đường dẫn hoặc mã bài báo rõ ràng.

### 6. Phản hồi từ công cụ hoặc bộ chấm không đáng tin

**Điều đã giải quyết:** nghiên cứu tình huống tác tử nhận tín hiệu sai từ công cụ, môi trường hoặc mô hình chấm. Đây là hướng gần nhất với trục **độ đáng tin của phản hồi** trong RepGuard.

**Giá trị đối với RepGuard:** cung cấp cách mô hình hóa sai số của bộ chấm, phản hồi bị đầu độc và xác suất kết quả thực sự đúng khi tín hiệu quan sát được có thể sai.

**Phần còn thiếu:** hướng này thường tập trung vào câu hỏi “có nên tin tín hiệu này không”, nhưng không nhất thiết hỏi tiếp “nếu tin thì bằng chứng nên được chuyển sang loại nhiệm vụ nào”. Một bằng chứng hoàn toàn đáng tin vẫn có thể không liên quan tới nhiệm vụ mới.

Tên bài “Trust No Tool” trong tài liệu gốc cần được đối chiếu lại tên tác giả và phiên bản công bố chính thức trước khi đưa vào danh mục tài liệu tham khảo cuối cùng.[^5]

### Bảng tóm tắt để ghi nhớ

| Hướng nghiên cứu | Câu hỏi chính đã trả lời | Điều chưa tách rõ |
|---|---|---|
| Chấm điểm từ lịch sử | Ai từng đóng góp tốt? | Phản hồi có đúng và nhiệm vụ có liên quan không? |
| Uy tín theo kỹ năng | Tác tử giỏi kỹ năng nào? | Nhãn kết quả lịch sử có đáng tin không? |
| Uy tín theo thời gian | Bằng chứng cũ nên giảm trọng số thế nào? | Bằng chứng có đúng và có phù hợp với nhiệm vụ mới không? |
| Phát hiện tác tử gây hại | Ai có hành vi bất thường hoặc nguy hiểm? | Tác tử bình thường nhận phản hồi sai thì xử lý thế nào? |
| Tấn công vào uy tín | Cơ chế uy tín có thể bị khai thác ra sao? | Cần mô hình bằng chứng nào để giảm sai lệch từ gốc? |
| Phản hồi không đáng tin | Tín hiệu từ bộ chấm hoặc công cụ có thể sai thế nào? | Bằng chứng đáng tin nên chuyển sang nhiệm vụ nào? |

### Khoảng trống nên được phát biểu thế nào?

Không nên nói tuyệt đối “chưa có ai từng nghiên cứu vấn đề này”. Cách diễn đạt chặt chẽ hơn là:

> Theo phạm vi tổng quan tài liệu hiện tại, em chưa tìm thấy công trình nào chủ động thay đổi độc lập độ đáng tin của phản hồi và mức độ liên quan giữa nhiệm vụ trong cùng một thiết kế thí nghiệm, sau đó đo riêng tác động của từng yếu tố và sự tương tác giữa chúng đối với việc chuyển giao uy tín.

### Cảnh báo khi kiểm tra tài liệu tham khảo

- “Ebrahimi và cộng sự, 2025” chưa có đủ tên bài, nơi công bố và đường dẫn.
- SentinelNet có bản arXiv mang mã `2510.16219`, cho thấy bản đăng ban đầu thuộc năm 2025; nếu muốn ghi năm 2026 thì phải xác minh đúng năm xuất bản chính thức.[^4]
- “WEREWOLF, EMNLP 2026” chưa có đủ thông tin để xác nhận.
- “Trust No Tool” cần được gắn với đúng tác giả, phiên bản và đường dẫn chính thức.

### Lời thoại gợi ý

> Slide này cho thấy RepGuard không bắt đầu từ con số không. Nghiên cứu trước đã chỉ ra cách học uy tín từ lịch sử, phân biệt uy tín theo kỹ năng, làm giảm ảnh hưởng của bằng chứng cũ, phát hiện tác tử gây hại và xử lý phản hồi không đáng tin. Tuy nhiên, các hướng này chủ yếu trả lời từng phần riêng. Uy tín theo kỹ năng thường giả định kết quả cũ đã đáng tin; còn nghiên cứu về phản hồi sai lại chưa hỏi bằng chứng đó nên được chuyển sang nhiệm vụ nào. Khoảng trống mà RepGuard tập trung là tách hai câu hỏi này trong cùng một thí nghiệm: bằng chứng cũ có đáng tin không, và dù đáng tin thì nó có liên quan đến nhiệm vụ mới không?

### Câu hội đồng có thể hỏi

**“RepGuard khác uy tín theo kỹ năng ở điểm nào?”** Uy tín theo kỹ năng chủ yếu trả lời tác tử giỏi lĩnh vực nào. RepGuard còn kiểm tra xem kết quả dùng để học mức uy tín đó có đáng tin hay không và lượng bằng chứng có đủ mạnh hay không.

**“Uy tín giảm theo thời gian đã giải quyết độ liên quan chưa?”** Chưa. Thời gian cho biết bằng chứng mới hay cũ; độ liên quan cho biết bằng chứng có phù hợp với nhiệm vụ hiện tại hay không. Hai nhiệm vụ diễn ra sát nhau vẫn có thể thuộc hai lĩnh vực hoàn toàn khác.

**“Nếu đã có nghiên cứu về phản hồi không đáng tin thì RepGuard còn mới ở đâu?”** Phần mới dự kiến không chỉ là phát hiện phản hồi sai, mà là nghiên cứu có kiểm soát cách độ đáng tin của phản hồi tương tác với khả năng chuyển giao giữa các nhiệm vụ, đồng thời giữ lại độ không chắc chắn trước khi chuyển thành ảnh hưởng.

### Câu chuyển sang Slide 9

> Từ bản đồ nghiên cứu này, ta có thể phát biểu khoảng trống một cách hẹp và kiểm chứng được: điều gì xảy ra khi chất lượng phản hồi và mức độ liên quan của nhiệm vụ cùng thay đổi nhưng được kiểm soát riêng biệt?

---

## Slide 9 — The Research Gap

### Mục tiêu của slide

Thu hẹp vấn đề thành một khoảng trống nghiên cứu cụ thể, có thể kiểm nghiệm bằng thực nghiệm và có thể bị bác bỏ nếu dữ liệu không ủng hộ. Điểm quan trọng của slide không phải là tuyên bố “chưa ai nghiên cứu uy tín”, mà là chỉ ra **hai câu hỏi đã được nghiên cứu tương đối riêng rẽ nhưng chưa được xem xét đầy đủ trong cùng một quá trình chuyển bằng chứng lịch sử thành ảnh hưởng**.

### Vòng tròn thứ nhất: độ đáng tin của phản hồi

Nhánh nghiên cứu này hỏi:

> Phản hồi mà hệ thống quan sát được có phản ánh đúng chất lượng thật của câu trả lời hay không?

Ví dụ, một mô hình chấm trả về “đúng”, nhưng xác suất câu trả lời thực sự đúng có thể chỉ là 0,7. Một bộ kiểm thử báo “đạt”, nhưng có thể chưa kiểm tra trường hợp biên. Một người dùng đánh giá tích cực, nhưng đánh giá đó có thể cảm tính hoặc bị thao túng.

Nhánh này thường quan tâm tới:

- Tỷ lệ bộ chấm nhận ra câu trả lời đúng.
- Tỷ lệ bộ chấm loại đúng câu trả lời sai.
- Khả năng phản hồi bị nhiễu hoặc bị đầu độc.
- Cách hiệu chỉnh điểm số để một mức tin cậy 0,8 thực sự tương ứng với khoảng 80% kết quả đúng.

Kết quả của nhánh này giúp trả lời **bằng chứng có đáng tin hay không**, nhưng chưa nhất thiết trả lời bằng chứng đó nên được sử dụng cho loại nhiệm vụ nào.

### Vòng tròn thứ hai: khả năng chuyển giao giữa nhiệm vụ

Nhánh nghiên cứu này hỏi:

> Thành tích trong một nhiệm vụ hoặc kỹ năng có giúp dự đoán năng lực ở nhiệm vụ mới hay không?

Ví dụ, lịch sử sửa lỗi Python có thể chuyển giao khá tốt sang một bài sửa lỗi Python khác, chuyển giao một phần sang bài thiết kế thuật toán, nhưng gần như không nên chuyển sang phân tích luật. Ngay trong cùng một lĩnh vực, hai nhiệm vụ có thể đòi hỏi kỹ năng khác nhau: viết mã đúng cú pháp không đồng nghĩa với thiết kế kiến trúc phần mềm tốt.

Nhánh này thường quan tâm tới:

- Nhiệm vụ cũ và nhiệm vụ mới có cùng kỹ năng hay không.
- Mức tương đồng về nội dung, dạng suy luận và công cụ cần dùng.
- Hiệu quả thực tế của việc dùng thành tích ở nhiệm vụ A để dự đoán kết quả ở nhiệm vụ B.
- Cách mượn bằng chứng giữa các kỹ năng khi dữ liệu trong từng kỹ năng còn ít.

Kết quả của nhánh này giúp trả lời **bằng chứng nên được chuyển tới đâu**, nhưng thường bắt đầu từ giả định rằng kết quả lịch sử đã được đánh giá tương đối chính xác.

### Phần giao mà RepGuard tập trung

RepGuard hỏi đồng thời hai câu:

1. Bằng chứng lịch sử có đáng tin không?
2. Nếu đáng tin, bằng chứng đó có liên quan tới nhiệm vụ hiện tại không?

Chỉ khi cả hai câu đều được trả lời, hệ thống mới quyết định bằng chứng nên tạo ra bao nhiêu ảnh hưởng. Điều này tạo ra bốn trường hợp cần phân biệt:

| Độ đáng tin của phản hồi | Độ liên quan của nhiệm vụ | Cách diễn giải |
|---|---|---|
| Cao | Cao | Bằng chứng mạnh nhất; có thể làm tăng ảnh hưởng rõ rệt |
| Cao | Thấp | Biết chắc tác tử đã làm tốt, nhưng ở lĩnh vực không phù hợp; không nên chuyển nhiều uy tín |
| Thấp | Cao | Nhiệm vụ cũ đúng lĩnh vực, nhưng chưa chắc tác tử thực sự làm tốt; cần giảm sức nặng bằng chứng |
| Thấp | Thấp | Vừa không chắc đúng vừa không liên quan; gần như không nên tác động tới quyết định mới |

Nếu hệ thống chỉ xem một trong hai chiều, nó sẽ nhầm hai trường hợp ở giữa. Đây chính là điểm mà một điểm uy tín duy nhất khó biểu diễn đầy đủ.

### Vì sao hai hướng nghiên cứu trước chưa giải quyết phần giao?

Các phương pháp uy tín theo kỹ năng thường tập trung vào sự khan hiếm dữ liệu và việc mượn thông tin giữa các kỹ năng. Chúng có thể biết bằng chứng thuộc kỹ năng nào, nhưng nếu nhãn “đúng” hoặc “sai” ban đầu không đáng tin thì điểm uy tín theo kỹ năng vẫn bị sai từ đầu.

Ngược lại, các phương pháp xử lý phản hồi không đáng tin có thể ước lượng tốt khả năng một kết quả lịch sử là đúng, nhưng nếu chúng áp dụng kết quả ấy cho mọi nhiệm vụ thì vẫn có thể chuyển uy tín sai lĩnh vực.

Vì vậy, hai nhánh giải quyết hai lát cắt khác nhau:

- Một nhánh kiểm tra **chất lượng của bằng chứng**.
- Một nhánh kiểm tra **phạm vi áp dụng của bằng chứng**.
- RepGuard nghiên cứu quá trình cần cả hai trước khi bằng chứng được đổi thành quyền ảnh hưởng.

### “Đối tượng thực nghiệm trung tâm” nghĩa là gì?

Độ đáng tin của phản hồi và độ liên quan của nhiệm vụ không được coi là chi tiết phụ hoặc yếu tố gây nhiễu cần bỏ qua. Chúng trở thành hai biến chính của thí nghiệm:

- Độ đáng tin của phản hồi được thay đổi qua các mức: sạch, nhiễu nhẹ, nhiễu mạnh và có chủ đích gây sai lệch.
- Khả năng chuyển giao được thay đổi qua các mức: cùng loại nhiệm vụ, nhiệm vụ có liên quan và nhiệm vụ không liên quan.
- Mỗi mức của chiều thứ nhất được kết hợp với mỗi mức của chiều thứ hai.

Nhờ đó, nghiên cứu có thể đo:

- **Tác động riêng của chất lượng phản hồi:** khi giữ mức liên quan tương đương, phản hồi kém đi làm uy tín sai lệch bao nhiêu?
- **Tác động riêng của khả năng chuyển giao:** khi giữ chất lượng phản hồi tương đương, dùng lịch sử khác lĩnh vực gây hại bao nhiêu?
- **Tác động tương tác:** ảnh hưởng của phản hồi nhiễu có trở nên nghiêm trọng hơn khi hệ thống còn chuyển bằng chứng sang nhiệm vụ khác hay không?

### Các câu hỏi nghiên cứu có thể kiểm nghiệm

Khoảng trống trên có thể được cụ thể hóa thành ba câu hỏi:

- **Câu hỏi 1:** chất lượng phản hồi có ảnh hưởng đáng kể đến độ chính xác và độ hiệu chỉnh của uy tín hay không?
- **Câu hỏi 2:** mức độ liên quan giữa nhiệm vụ lịch sử và nhiệm vụ hiện tại có ảnh hưởng đáng kể đến việc xếp hạng và phân bổ ảnh hưởng hay không?
- **Câu hỏi 3:** hai yếu tố có tương tác hay không; nghĩa là tác động của một yếu tố có thay đổi tùy theo mức của yếu tố kia hay không?

Một kết quả có thể bác bỏ giả thuyết ban đầu là: sau khi kiểm soát đủ chặt, chất lượng phản hồi hoặc khả năng chuyển giao gần như không tạo ra khác biệt đo được. Khi đó nghiên cứu phải thu hẹp hoặc thay đổi tuyên bố, thay vì cố khẳng định ECRT luôn cần thiết.

### Đóng góp dự kiến nằm ở đâu?

Đóng góp không nên được mô tả đơn giản là “thêm hai trọng số vào công thức”. Giá trị dự kiến gồm ba lớp:

1. **Mô tả hiện tượng:** xác định riêng tác động của độ đáng tin, độ liên quan và sự tương tác giữa chúng.
2. **Cơ chế xử lý:** xây dựng ECRT để định giá bằng chứng theo cả hai chiều và giữ lại độ không chắc chắn.
3. **Quy trình đánh giá:** xây dựng HistRepEval để các phương pháp uy tín khác có thể được kiểm tra trong cùng điều kiện.

### Cách đọc hình hai vòng tròn

- Vòng tròn bên trái là các nghiên cứu về độ đáng tin của phản hồi.
- Vòng tròn bên phải là các nghiên cứu về chuyển giao giữa nhiệm vụ hoặc kỹ năng.
- Vùng giao được tô nổi bật là câu hỏi của RepGuard: **một bằng chứng vừa không hoàn toàn đáng tin, vừa có phạm vi chuyển giao không chắc chắn, thì phải được chuyển thành ảnh hưởng như thế nào?**

Vùng giao không có nghĩa hoàn toàn chưa có công trình nào chạm tới cả hai ý tưởng. Nó có nghĩa, theo phạm vi tổng quan hiện tại, chưa tìm thấy một thiết kế kiểm soát tách hai chiều và đo sự tương tác của chúng như câu hỏi chính. Cách nói này chặt chẽ và an toàn hơn tuyên bố tuyệt đối “không ai từng làm”.

### Lời thoại gợi ý

> Khoảng trống ở đây không phải là chưa ai nghiên cứu uy tín. Một nhóm công trình hỏi phản hồi lịch sử có đáng tin không; nhóm khác hỏi thành tích ở kỹ năng này có nên chuyển sang kỹ năng khác không. Tuy nhiên, một hệ thống thực tế phải trả lời cả hai câu trước khi trao ảnh hưởng. Bằng chứng có thể rất đáng tin nhưng không liên quan, hoặc rất liên quan nhưng phản hồi lại không đáng tin. RepGuard biến hai chiều này thành hai biến thí nghiệm độc lập, đo tác động riêng và sự tương tác giữa chúng, rồi mới đánh giá có cần một cơ chế mới hay không.

### Câu hội đồng có thể hỏi

**“Khoảng trống này có quá hẹp không?”** Hẹp là chủ ý của đề tài. Một câu hỏi hẹp nhưng đo được và có đối chứng rõ sẽ có giá trị hơn một tuyên bố rộng về “làm hệ đa tác tử đáng tin cậy hơn” mà không thể kiểm nghiệm chính xác.

**“Chỉ thêm hai trọng số có đủ mới không?”** Tính mới dự kiến không chỉ nằm ở công thức. Nó còn nằm ở thí nghiệm tách hai yếu tố, phân tích sự tương tác, giữ lại độ không chắc chắn và xây dựng quy trình đánh giá có thể tái sử dụng.

**“Hai chiều này có thật sự độc lập không?”** Trong dữ liệu tự nhiên chúng có thể tương quan. Nghiên cứu không khẳng định chúng luôn độc lập về mặt thống kê; nghiên cứu chủ động thay đổi chúng riêng biệt trong thí nghiệm để biết tác động của từng chiều.

**“Nếu không tìm thấy sự tương tác thì sao?”** Khi đó có thể hai yếu tố tác động theo kiểu cộng đơn giản, hoặc một yếu tố chi phối yếu tố kia. Đây vẫn là kết quả giúp xác định khi nào mô hình phức tạp là không cần thiết, miễn là thí nghiệm đủ nhạy và được báo cáo trung thực.

### Câu chuyển sang Slide 10

> Khoảng trống này không chỉ mang tính lý thuyết. Khi uy tín có thể đổi thành quyền ảnh hưởng, việc không phân biệt hai loại bằng chứng sẽ tạo ra một con đường có thể bị khai thác có chủ đích.

---

## Slide 10 — Why This Gap Matters Strategically

### Mục tiêu của slide

Giải thích vì sao việc trộn lẫn độ đáng tin của phản hồi với độ liên quan của nhiệm vụ không chỉ làm giảm độ chính xác một cách ngẫu nhiên, mà còn tạo ra một điểm yếu để tác tử có chủ đích khai thác. Từ “chiến lược” ở đây nghĩa là đối thủ có thể quan sát quy tắc tạo uy tín, lựa chọn hành vi theo thời gian và chờ đến lúc uy tín có giá trị cao nhất mới sử dụng nó.

### Uy tín trở thành một loại tài sản như thế nào?

Trong hệ đa tác tử, điểm uy tín không chỉ là một con số mô tả. Nó có thể quyết định:

- Tác tử nào được chọn để trả lời.
- Tác tử nào nhận nhiều lượt suy luận hoặc nhiều công cụ hơn.
- Câu trả lời của ai có trọng số lớn hơn khi bỏ phiếu.
- Lập luận của ai được đưa vào bước tổng hợp cuối cùng.

Vì uy tín có thể đổi thành quyền tham gia và quyền ảnh hưởng, một tác tử có động cơ tìm cách tích lũy uy tín ở nơi rẻ rồi sử dụng nó ở nơi có giá trị cao.

### Ba giai đoạn của một cuộc khai thác uy tín

#### 1. Tích lũy lịch sử rẻ

Tác tử chủ động tham gia nhiều nhiệm vụ dễ, lặp lại hoặc có bộ chấm yếu. Mục tiêu chưa phải gây hại ngay, mà là tạo một hồ sơ trông đáng tin.

Ví dụ, tác tử giải hàng trăm câu hỏi lập trình cơ bản mà đáp án dễ đoán, hoặc tạo câu trả lời có hình thức thuyết phục để đánh lừa mô hình chấm. Nếu hệ thống chỉ đếm số lần được phản hồi tích cực, tác tử sẽ nhanh chóng có điểm uy tín cao.

Điểm yếu bị khai thác ở giai đoạn này là **chất lượng phản hồi**: phản hồi tích cực có thể rẻ, dễ đạt hoặc không phản ánh đúng năng lực thật.

#### 2. Chuyển thành tích sang lĩnh vực khác

Hệ thống cho phép điểm uy tín chung hoặc mượn bằng chứng giữa các kỹ năng. Tác tử dùng thành tích ở kỹ năng nguồn để được đánh giá cao ở kỹ năng đích, dù chưa có đủ bằng chứng trực tiếp.

Ví dụ, thành tích ở các câu hỏi Python đơn giản được dùng để tăng ảnh hưởng trong một nhiệm vụ kiểm tra an toàn mã nguồn quan trọng. Hai loại nhiệm vụ đều mang nhãn “lập trình”, nhưng yêu cầu năng lực và mức rủi ro rất khác nhau.

Điểm yếu bị khai thác ở giai đoạn này là **phạm vi chuyển giao**: hệ thống chuyển bằng chứng xa hơn mức mà bằng chứng thực sự hỗ trợ.

#### 3. Sử dụng uy tín ở nhiệm vụ giá trị cao

Sau khi có trọng số lớn, tác tử đưa ra câu trả lời sai, che giấu lỗi hoặc dẫn nhóm tới quyết định có lợi cho nó. Vì hệ thống đã xem tác tử là đáng tin, các tác tử khác có thể bị giảm ảnh hưởng và câu trả lời sai dễ trở thành quyết định chung.

Đây là lúc uy tín được “đổi” thành tác động thực tế. Thiệt hại không chỉ là một điểm số thấp hơn, mà có thể là quyết định sai ở nhiệm vụ quan trọng.

### Một ví dụ đầy đủ

Giả sử một tác tử tham gia 200 bài lập trình dễ. Bộ chấm tự động chỉ kiểm tra đầu ra mẫu, nên tác tử nhận 190 phản hồi tích cực. Hệ thống tạo cho nó điểm uy tín 0,95.

Sau đó xuất hiện nhiệm vụ kiểm tra một bản vá bảo mật. Vì hệ thống dùng điểm uy tín lập trình chung, tác tử được trao trọng số lớn dù chưa từng chứng minh năng lực kiểm tra bảo mật. Nó khẳng định bản vá an toàn, trong khi thực tế còn lỗ hổng. Các tác tử thận trọng hơn bị lấn át trong bước bỏ phiếu.

Trong ví dụ này có hai lỗi nối tiếp:

1. Phản hồi cũ được coi là bằng chứng mạnh hơn mức nó xứng đáng.
2. Bằng chứng từ bài lập trình dễ được chuyển quá xa sang kiểm tra bảo mật.

Nếu chỉ sửa một lỗi, đường tấn công vẫn có thể tồn tại.

### Vì sao việc mượn bằng chứng vừa hữu ích vừa nguy hiểm?

Xia và Wang chỉ ra rằng liên kết giữa các kỹ năng có tính hai mặt: nó giúp giảm vấn đề thiếu dữ liệu, nhưng đồng thời có thể tạo ra kênh “rửa uy tín”.[^2]

Nếu một tác tử mới chỉ có ít lịch sử trong kỹ năng đích, mượn thông tin từ kỹ năng liên quan có thể giúp hệ thống ra quyết định tốt hơn. Tuy nhiên, cùng cơ chế đó cho phép tác tử chủ động chọn kỹ năng nguồn dễ nhất để tích lũy thành tích. Vì vậy mục tiêu không phải là cấm mọi chuyển giao, mà là **định giá mức chuyển giao theo bằng chứng và giữ lại độ không chắc chắn**.

### Sai số thông thường và hành vi có chủ đích khác nhau thế nào?

- **Sai số thông thường:** phản hồi bị nhiễu ngẫu nhiên hoặc hệ thống vô tình dùng bằng chứng không liên quan. Tác tử không chủ động lựa chọn lịch sử.
- **Hành vi có chủ đích:** tác tử biết hoặc suy đoán cơ chế uy tín, sau đó lựa chọn nhiệm vụ, thời điểm và kiểu câu trả lời để tối đa hóa ảnh hưởng trong tương lai.

Một phương pháp có thể hoạt động tốt dưới nhiễu ngẫu nhiên nhưng thất bại khi đối thủ thích nghi với chính quy tắc của phương pháp. Vì vậy cần các phép thử có tác tử chiến lược, không chỉ thêm nhiễu ngẫu nhiên vào dữ liệu.

### Vì sao các cuộc tấn công không phải đóng góp mới cốt lõi?

Các kiểu tích lũy uy tín rồi phản bội, chuyển uy tín giữa kỹ năng hoặc đầu độc phản hồi đã xuất hiện trong những nghiên cứu liên quan. Vì vậy, luận văn không nên tuyên bố việc phát hiện các cuộc tấn công này là đóng góp mới trung tâm.

Vai trò của chúng trong RepGuard là **phép thử sức chịu đựng**:

- Khi tác tử tích lũy nhiều phản hồi chất lượng thấp, ECRT có giảm sức nặng của lịch sử đó không?
- Khi thành tích nằm ở kỹ năng khác, ECRT có hạn chế việc chuyển uy tín quá mức không?
- Khi tác tử thay đổi hành vi sau một thời gian, độ không chắc chắn và cơ chế cập nhật có phản ứng đủ nhanh không?

Đóng góp cốt lõi vẫn là mô hình bằng chứng: tách độ đáng tin, độ liên quan và độ không chắc chắn trước khi chuyển lịch sử thành ảnh hưởng.

### “Khó khai thác hơn ngay từ cấu trúc” nghĩa là gì?

Một cơ chế uy tín đơn giản có thể xem mỗi phản hồi tích cực là một đơn vị thành tích. Khi đó đối thủ chỉ cần tạo thật nhiều phản hồi tích cực.

ECRT dự kiến đặt ba điều kiện trước khi lịch sử tạo ra ảnh hưởng lớn:

1. Kết quả lịch sử có xác suất đúng đủ cao.
2. Nguồn phản hồi mang đủ thông tin và không chỉ là tín hiệu gần ngẫu nhiên.
3. Nhiệm vụ lịch sử có liên quan đủ mạnh tới nhiệm vụ hiện tại.

Ngoài ra, nếu lượng bằng chứng còn ít, phân phối niềm tin vẫn rộng và hệ thống có thể quay về trọng số trung lập. Như vậy, đối thủ không thể chỉ dựa vào số lượng lịch sử; nó phải tạo ra bằng chứng vừa đáng tin, vừa phù hợp với nhiệm vụ đích và đủ nhiều để giảm độ không chắc chắn.

Tuy nhiên, “khó khai thác hơn” không phải là bảo đảm an toàn tuyệt đối. Hiệu quả chỉ có ý nghĩa trong mô hình đối thủ được xác định rõ: đối thủ biết gì, kiểm soát được gì, có bao nhiêu lượt tương tác và có thể thao túng nguồn phản hồi tới mức nào.

### Cần đo khả năng chống chịu bằng gì?

Không nên chỉ báo cáo độ chính xác khi hệ thống không bị tấn công. Có thể theo dõi:

- Mức giảm độ chính xác từ điều kiện bình thường sang điều kiện bị tấn công.
- Xác suất đối thủ đạt được trọng số cao trên nhiệm vụ đích.
- Số lượt hoặc chi phí mà đối thủ cần để tích lũy đủ uy tín.
- Mức sai lệch giữa uy tín ước lượng và năng lực thực sự.
- Khả năng hệ thống từ chối trao ảnh hưởng khi bằng chứng chưa đủ.

Các chỉ số và ngân sách tấn công phải được định nghĩa trước, nếu không rất dễ chọn điều kiện có lợi cho phương pháp sau khi đã xem kết quả.

### Lời thoại gợi ý

> Khoảng trống này quan trọng về mặt chiến lược vì uy tín có thể đổi thành quyền ảnh hưởng. Một tác tử có thể tích lũy nhiều phản hồi tích cực ở nhiệm vụ dễ hoặc có bộ chấm yếu, chuyển thành tích đó sang một kỹ năng khác, rồi sử dụng trọng số cao ở nhiệm vụ quan trọng. Nếu hệ thống chỉ đếm lịch sử, nó sẽ thưởng cả bằng chứng kém tin cậy lẫn bằng chứng không phù hợp. RepGuard buộc lịch sử phải được đánh giá về độ đúng, sức nặng và độ liên quan trước khi tạo ảnh hưởng. Các cuộc tấn công được dùng để kiểm tra sức chịu đựng của cơ chế này, chứ không được tuyên bố là đóng góp mới cốt lõi.

### Câu hội đồng có thể hỏi

**“Tại sao tác tử phải gây hại; các mô hình ngôn ngữ có thật sự có động cơ không?”** Nghiên cứu không cần giả định mọi mô hình tự có ý đồ như con người. Tác tử có thể được lập trình, điều khiển bằng lời nhắc, bị xâm nhập hoặc tối ưu theo mục tiêu sai lệch. Mô hình đối thủ là cách kiểm tra trường hợp xấu nhất của cơ chế điều phối.

**“Tại sao không cấm hoàn toàn việc chuyển uy tín giữa các kỹ năng?”** Vì khi dữ liệu ít, các kỹ năng liên quan có thể cung cấp thông tin hữu ích. Cấm hoàn toàn sẽ bỏ phí bằng chứng. Mục tiêu là chuyển có kiểm soát, không phải không chuyển.

**“ECRT có ngăn được mọi cuộc tấn công không?”** Không. Luận văn chỉ đánh giá các kiểu tấn công và giới hạn đã nêu. ECRT được kỳ vọng làm tăng chi phí hoặc giảm tác động của việc khai thác sai bằng chứng, không đưa ra bảo đảm an toàn tổng quát.

**“Nếu đối thủ tạo được lịch sử vừa đáng tin vừa liên quan thì sao?”** Khi đó lịch sử thật sự là bằng chứng tốt cho đến thời điểm đối thủ đổi hành vi. Cần thêm cơ chế cập nhật theo thời gian, phát hiện thay đổi và giảm ảnh hưởng khi quan sát mới mâu thuẫn với lịch sử. Đây là lý do tấn công phản bội muộn được dùng làm phép thử riêng.

### Câu chuyển sang Slide 11

> Như vậy, bài toán không phải chỉ là tạo một điểm uy tín chính xác hơn, mà là kiểm soát toàn bộ đường đi từ phản hồi lịch sử tới quyền ảnh hưởng. Phần tiếp theo trình bày hướng giải quyết được đề xuất.

---

## Slide 11 — Section Divider: Proposed Direction

### Mục tiêu của slide

Đánh dấu chuyển từ problem/gap sang kế hoạch giải quyết.

### Lời thoại gợi ý

> Sau khi xác định gap, phần tiếp theo trình bày logic nghiên cứu, cơ chế ECRT và cách kiểm chứng. Thứ tự quan trọng là characterization trước, method sau.

---

## Slide 12 — Research Story

### Mục tiêu của slide

Cho hội đồng nhìn thấy toàn bộ mạch lập luận của bài nghiên cứu trên một đường thẳng. Slide này trả lời câu hỏi: **tại sao đề tài đi từ hệ đa tác tử, đến uy tín lịch sử, rồi đến thí nghiệm hai chiều, ECRT, các phép thử đối kháng và cuối cùng là HistRepEval?**

Đây là “xương sống” của luận văn. Nếu trình bày tốt slide này, người nghe sẽ hiểu rằng các phần sau không phải những ý tưởng rời rạc được ghép lại, mà là các bước cần thiết của cùng một lập luận.

### Bước 1 — Nhóm tác tử không đồng nhất cần phân bổ ảnh hưởng theo chuyên môn

Các tác tử có thể khác nhau về mô hình nền, công cụ, hướng dẫn hệ thống, bộ nhớ và lĩnh vực mạnh. Vì vậy, bỏ phiếu ngang nhau không phải lúc nào cũng hợp lý. Hệ thống cần trao nhiều ảnh hưởng hơn cho tác tử có khả năng đúng cao trong nhiệm vụ cụ thể.

Điểm khởi đầu của câu chuyện là một nhu cầu phối hợp: **không chỉ cần có chuyên gia trong nhóm, mà còn phải sử dụng đúng chuyên gia**.

### Bước 2 — Uy tín lịch sử là lời giải tự nhiên

Nếu một tác tử đã nhiều lần làm tốt trong quá khứ, lịch sử đó có thể giúp dự đoán khả năng tác tử tiếp tục làm tốt. Vì vậy, hệ thống có thể học mức uy tín từ các lần tương tác trước và dùng uy tín để phân bổ ảnh hưởng.

Đây là trực giác hợp lý: thay vì xem mọi tác tử như nhau, hệ thống học từ thành tích đã quan sát. Tuy nhiên, trực giác này chỉ đúng khi lịch sử thực sự là bằng chứng tốt.

### Bước 3 — Lịch sử không tự chứng minh độ tin cậy của chính nó

Một bản ghi “tác tử đã làm đúng” thường không đến trực tiếp từ sự thật tuyệt đối. Nó đến từ bộ kiểm thử, mô hình chấm, công cụ, trạng thái môi trường hoặc đánh giá của con người. Những nguồn này có thể:

- Đánh dấu nhầm câu sai là đúng.
- Đánh dấu nhầm câu đúng là sai.
- Chỉ kiểm tra một phần của kết quả.
- Bị thay đổi hoặc bị thao túng.
- Hoạt động tốt ở lĩnh vực này nhưng kém ở lĩnh vực khác.

Vì vậy, số lần nhận phản hồi tích cực không thể tự động được xem là số lần thật sự đúng. Lịch sử phải được định giá theo chất lượng của nguồn phản hồi.

### Bước 4 — Một kết quả đúng vẫn có thể không liên quan

Giả sử kết quả cũ đã được xác minh hoàn toàn chính xác. Điều đó vẫn chưa đủ để chuyển thành ảnh hưởng trên nhiệm vụ mới. Tác tử làm đúng một bài toán đại số không mặc nhiên đáng tin trong phân tích pháp lý. Ngay trong cùng lĩnh vực lập trình, sửa lỗi cú pháp và kiểm tra bảo mật cũng có thể yêu cầu năng lực rất khác nhau.

Do đó, đề tài phải hỏi thêm: **bằng chứng đúng này có dự đoán được năng lực trên nhiệm vụ hiện tại hay không?**

### Bước 5 — Hai loại sai lệch dễ bị trộn thành một điểm uy tín

Một điểm uy tín thấp có thể xuất phát từ hai nguyên nhân khác nhau:

- Tác tử thật sự làm không tốt, hoặc phản hồi lịch sử không đáng tin.
- Tác tử làm tốt, nhưng bằng chứng nằm ở nhiệm vụ không liên quan.

Tương tự, một điểm uy tín cao cũng có thể gây hiểu nhầm: tác tử có nhiều phản hồi tích cực nhưng phản hồi đó yếu, hoặc thành tích chỉ nằm ở lĩnh vực dễ. Nếu gộp tất cả vào một con số, hệ thống không biết cần sửa nguồn phản hồi hay sửa quy tắc chuyển giao.

### Bước 6 — Trước tiên phải thực hiện thí nghiệm có kiểm soát

Thay vì xây dựng ECRT ngay rồi tìm tình huống mà phương pháp thắng, nghiên cứu trước hết thay đổi độc lập hai yếu tố:

- Chất lượng phản hồi: từ sạch đến nhiễu hoặc bị thao túng.
- Mức độ chuyển giao: từ cùng loại nhiệm vụ đến nhiệm vụ liên quan hoặc không liên quan.

Mục tiêu là xác định:

- Mỗi yếu tố có tạo ra ảnh hưởng đo được hay không.
- Hai yếu tố có tương tác hay không.
- Phương pháp hiện có thất bại trong điều kiện nào.
- Mức độ nghiêm trọng có đủ để biện minh cho một cơ chế mới hay không.

Đây là phần mô tả hiện tượng, không phụ thuộc vào việc ECRT có thắng hay không.

### Bước 7 — Chỉ sau đó mới đề xuất ECRT

Nếu thí nghiệm xác nhận rằng cả độ đáng tin của phản hồi và khả năng chuyển giao đều quan trọng, ECRT được đưa ra như một cơ chế phù hợp với hiện tượng đã quan sát.

ECRT không cho phép lịch sử đi thẳng vào điểm uy tín. Mỗi bằng chứng phải được đánh giá về:

1. Xác suất kết quả cũ thực sự đúng.
2. Sức nặng thông tin của phản hồi.
3. Mức liên quan tới nhiệm vụ hiện tại.
4. Độ không chắc chắn còn lại sau khi tổng hợp lịch sử.

Thứ tự này làm cho phương pháp xuất hiện như hệ quả của câu hỏi nghiên cứu, thay vì một công thức được nghĩ ra trước.

### Bước 8 — Kiểm tra trong điều kiện có hành vi chiến lược

Sau khi kiểm tra trong điều kiện thông thường, phương pháp được đặt vào ba tình huống khó:

- **Phản bội muộn:** tác tử cư xử tốt để tích lũy uy tín rồi thay đổi hành vi.
- **Rửa uy tín giữa kỹ năng:** tích lũy thành tích ở kỹ năng dễ rồi chuyển ảnh hưởng sang kỹ năng đích.
- **Đầu độc phản hồi:** làm sai lệch tín hiệu mà hệ thống dùng để học uy tín.

Những tình huống này không phải đóng góp mới cốt lõi. Chúng là phép thử xem cơ chế dựa trên bằng chứng có còn giữ được lợi ích khi tác tử hoặc nguồn phản hồi không còn hoàn toàn thiện chí.

### Bước 9 — Đóng gói thành HistRepEval

Nếu chỉ công bố một công thức và một bảng kết quả, người khác khó biết sự cải thiện đến từ phương pháp hay từ cách tạo dữ liệu. HistRepEval được định hướng là một quy trình đánh giá có thể tái sử dụng, gồm:

- Cấu trúc lưu trữ từng lần tương tác lịch sử.
- Cách tạo các mức nhiễu phản hồi.
- Cách xác định quan hệ cùng nhiệm vụ, liên quan và không liên quan.
- Các phương pháp đối chứng.
- Các chỉ số đánh giá và quy tắc chia dữ liệu.
- Hạt giống ngẫu nhiên, cấu hình và nhật ký cần thiết để tái lập.

Khi đó, đóng góp không chỉ là một phương pháp riêng mà còn là cách để cộng đồng kiểm tra những phương pháp uy tín khác trong cùng điều kiện.

### Vì sao thứ tự của câu chuyện rất quan trọng?

Thứ tự đúng là:

> Nhu cầu phối hợp → hạn chế của lịch sử → khoảng trống hai chiều → mô tả hiện tượng → phương pháp → kiểm tra sức chịu đựng → công cụ tái lập.

Nếu đảo thành “có ECRT trước rồi tìm bài toán để áp dụng”, hội đồng có thể nghi ngờ nghiên cứu được thiết kế để chứng minh phương pháp thắng. Khi mô tả hiện tượng đi trước, kết quả vẫn có giá trị ngay cả khi ECRT không vượt mọi phương pháp đối chứng.

### Vì sao thí nghiệm có kiểm soát phải đi trước ECRT?

Nếu xây phương pháp trước rồi chỉ tìm điều kiện nơi phương pháp đạt kết quả tốt, nghiên cứu dễ rơi vào thiên lệch xác nhận: chỉ chú ý dữ liệu ủng hộ ý tưởng ban đầu. Thí nghiệm mô tả hiện tượng đi trước buộc nghiên cứu trả lời những câu hỏi khó hơn:

- Hai yếu tố có thật sự tạo ra khác biệt không?
- Mức ảnh hưởng lớn hay nhỏ?
- Kết quả có lặp lại qua nhiều lần chạy và nhiều lĩnh vực không?
- Phương pháp đơn giản hiện có đã đủ tốt trong điều kiện nào?
- Điều kiện nào thực sự cần ECRT?

Nếu dữ liệu cho thấy một yếu tố không quan trọng hoặc không có sự tương tác, phương pháp phải được đơn giản hóa hoặc tuyên bố phải được thu hẹp.

### Cách đọc đường thời gian chín bước

Mũi tên ngang không biểu thị chín mô-đun phần mềm, mà biểu thị chín mắt xích lập luận. Mỗi bước phải tạo ra lý do cho bước kế tiếp:

- “Đội không đồng nhất” dẫn tới nhu cầu phân bổ ảnh hưởng.
- “Phân bổ ảnh hưởng” dẫn tới uy tín lịch sử.
- “Lịch sử không sạch” dẫn tới độ đáng tin của phản hồi.
- “Lịch sử có thể sai lĩnh vực” dẫn tới khả năng chuyển giao.
- Hai vấn đề dẫn tới thí nghiệm có kiểm soát.
- Kết quả thí nghiệm mới biện minh cho ECRT.
- ECRT phải được thử dưới hành vi chiến lược.
- Toàn bộ thiết kế được đóng gói để tái lập.

Không cần đọc từng ô như danh sách. Hãy kể nó như một chuỗi nguyên nhân và hệ quả.

### Lời thoại gợi ý

> Đây là mạch lập luận của toàn bộ luận văn. Nhóm tác tử không đồng nhất cần phân bổ ảnh hưởng theo chuyên môn, nên uy tín lịch sử là một lời giải tự nhiên. Nhưng lịch sử không tự bảo đảm rằng phản hồi là đúng, và ngay cả kết quả đúng cũng có thể không liên quan tới nhiệm vụ mới. Vì vậy, em không bắt đầu bằng một công thức mới. Em trước hết thực hiện thí nghiệm có kiểm soát để đo riêng hai yếu tố và sự tương tác giữa chúng. Chỉ khi dữ liệu cho thấy vấn đề có ý nghĩa, ECRT mới được dùng để định giá bằng chứng theo cả hai chiều và giữ lại độ không chắc chắn. Sau đó phương pháp được thử trong các tình huống đối kháng và toàn bộ quy trình được đóng gói thành HistRepEval để có thể tái lập.

### Câu hội đồng có thể hỏi

**“Tại sao không triển khai ECRT ngay để tiết kiệm thời gian?”** Vì nếu chưa chứng minh hiện tượng tồn tại, ta không biết ECRT đang giải quyết vấn đề thật hay chỉ thêm độ phức tạp. Thí nghiệm có kiểm soát tạo cơ sở để quyết định có nên tiếp tục phương pháp hay không.

**“Nếu ECRT không tốt hơn thì câu chuyện có bị đổ vỡ không?”** Không. Phần mô tả hiện tượng vẫn có thể chỉ ra giới hạn hoặc điều kiện mà phương pháp đơn giản đã đủ. Khi đó đóng góp chuyển từ “phương pháp tốt hơn” sang “ranh giới áp dụng được xác định rõ”.

**“HistRepEval có phải chỉ là mã nguồn của thí nghiệm không?”** Không chỉ là mã nguồn. Nó cần quy định cách tạo lịch sử, mức nhiễu, quan hệ giữa nhiệm vụ, phương pháp đối chứng, chỉ số và cách chia dữ liệu để những phương pháp khác được so sánh công bằng.

### Câu chuyển sang slide 13

> Với mạch nghiên cứu đó, bước tiếp theo là xem ECRT định giá từng bằng chứng lịch sử như thế nào trước khi cho phép nó tác động tới quyết định mới.

---

## Slide 13 — Proposed Method: ECRT

### Mục tiêu của slide

Giải thích quy trình của **ECRT — chuyển giao uy tín được hiệu chỉnh theo bằng chứng**. Ý tưởng trung tâm là: một kết quả lịch sử không được phép tạo ảnh hưởng ngay lập tức. Trước hết, nó phải được đánh giá về độ đúng, sức nặng thông tin và mức liên quan tới nhiệm vụ hiện tại; sau đó mới được tổng hợp thành niềm tin về năng lực của tác tử.

Slide này cần giúp người nghe hiểu được đường đi của thông tin:

> Phản hồi quan sát được → xác suất kết quả thật sự đúng → sức nặng bằng chứng → độ liên quan tới nhiệm vụ mới → niềm tin hậu nghiệm và độ không chắc chắn → trọng số ảnh hưởng → quyết định của nhóm.

### Tên ECRT có nghĩa là gì?

- **Evidence-Calibrated:** bằng chứng được hiệu chỉnh, tức phản hồi không bị xem thẳng là sự thật mà được quy đổi thành xác suất và sức nặng phù hợp với độ tin cậy của nguồn.
- **Reputation:** niềm tin về năng lực của tác tử được hình thành từ lịch sử.
- **Transfer:** niềm tin đó không được áp dụng giống nhau cho mọi nhiệm vụ; mức chuyển giao phụ thuộc vào quan hệ giữa nhiệm vụ cũ và nhiệm vụ hiện tại.

Cách dịch tự nhiên có thể dùng khi thuyết trình là: **cơ chế chuyển giao uy tín có hiệu chỉnh theo chất lượng bằng chứng**.

### Đầu vào của ECRT

Với mỗi lần tương tác lịch sử, hệ thống có:

- Nhiệm vụ cũ $q_t$.
- Câu trả lời của tác tử $y_{it}$.
- Đặc trưng của nhiệm vụ $x_t$.
- Phản hồi quan sát được $F_{it}$.
- Nhiệm vụ hiện tại $q^*$ cần quyết định mức ảnh hưởng.

ECRT không nhất thiết sử dụng trực tiếp đáp án đúng thật sự $z_{it}$ trong lúc vận hành, vì đây là biến ẩn. Thay vào đó, phương pháp ước lượng xác suất của $z_{it}$ từ phản hồi và thông tin về nguồn chấm.

### Đại lượng thứ nhất: $p_t$ — kết quả cũ có khả năng đúng bao nhiêu?

$p_t$ được hiểu là:

\[
p_t=P(z_{it}=1\mid F_{it},x_t,\text{thông tin về nguồn phản hồi}).
\]

Nếu $p_t$ gần 1, bằng chứng nghiêng mạnh về phía tác tử đã trả lời đúng. Nếu $p_t$ gần 0, bằng chứng nghiêng mạnh về phía tác tử đã trả lời sai. Nếu $p_t$ gần 0,5, phản hồi chưa giúp phân biệt rõ đúng và sai.

$p_t$ có thể được ước lượng bằng:

- Hiệu chỉnh một mô hình chấm trên tập dữ liệu có nhãn riêng.
- Kết hợp nhiều bộ chấm độc lập.
- Dùng kết quả thực thi hoặc kiểm thử khi có thể.
- Sử dụng độ nhạy và độ đặc hiệu đã đo của nguồn phản hồi.

Điều quan trọng là $p_t$ không đơn giản bằng điểm mà bộ chấm trả về. Nó là xác suất về tính đúng đắn sau khi đã xét mức đáng tin của nguồn phản hồi.

### Đại lượng thứ hai: $m_t$ — phản hồi mang bao nhiêu thông tin?

$m_t\geq0$ là **khối lượng bằng chứng hiệu dụng**. Nó cho biết lần quan sát này nên đóng góp mạnh đến đâu vào niềm tin chung.

Hai phản hồi có thể cùng cho $p_t=0,5$ nhưng mang ý nghĩa khác nhau:

- Trường hợp thứ nhất: bộ chấm gần như ngẫu nhiên và không cung cấp thông tin. Khi đó $m_t$ nên gần 0.
- Trường hợp thứ hai: nhiều nguồn đáng tin đưa ra bằng chứng cân bằng theo hai hướng. Khi đó hệ thống có thông tin thật, nhưng kết luận vẫn chưa nghiêng hẳn về đúng hay sai; $m_t$ không nhất thiết bằng 0.

Tương tự, một phản hồi đáng tin cho biết câu trả lời sai có thể có $p_t$ thấp nhưng $m_t$ cao. Đây là **bằng chứng mạnh theo hướng tiêu cực**, không phải bằng chứng vô dụng.

$m_t$ ngăn hệ thống xem một tín hiệu yếu như một quan sát đầy đủ. Nhiều phản hồi gần ngẫu nhiên không nên tạo ra sự chắc chắn giả chỉ vì số lượng của chúng lớn.

### Đại lượng thứ ba: $\tau_t$ — bằng chứng liên quan đến nhiệm vụ mới đến đâu?

$\tau_t\in[0,1]$ biểu thị mức liên quan giữa nhiệm vụ lịch sử và nhiệm vụ hiện tại. Viết đầy đủ hơn có thể là $\tau(q_t,q^*)$ để nhấn mạnh rằng giá trị này phụ thuộc vào **cả nhiệm vụ cũ lẫn nhiệm vụ mới**.

- $\tau_t$ gần 1: nhiệm vụ cũ và mới đòi hỏi năng lực rất giống nhau.
- $\tau_t$ ở mức trung gian: có một phần kỹ năng chung nhưng không hoàn toàn giống nhau.
- $\tau_t$ gần 0: thành tích cũ hầu như không giúp dự đoán năng lực ở nhiệm vụ mới.

Có thể ước lượng $\tau_t$ theo ba cách:

- Phân loại kỹ năng do con người hoặc bộ dữ liệu quy định.
- Độ tương đồng từ biểu diễn nội dung của nhiệm vụ.
- Khả năng chuyển giao được đo thực nghiệm: thành tích ở loại nhiệm vụ A dự đoán thành tích ở loại nhiệm vụ B tốt đến đâu.

Cách thứ ba gần với ý nghĩa cần đo nhất, nhưng phải dùng dữ liệu huấn luyện hoặc kiểm định riêng để tránh nhìn trước kết quả ở tập kiểm tra.

### Vì sao slide nói “hai trục” nhưng có ba biến?

Slide nói có hai trục khái niệm nhưng phương pháp lại dùng ba đại lượng. Điều này không mâu thuẫn:

- Trục **độ đáng tin và chất lượng của phản hồi** được mô tả bởi $p_t$ và $m_t$.
- $p_t$ cho biết bằng chứng nghiêng về đúng hay sai.
- $m_t$ cho biết bằng chứng mạnh hay yếu.
- Trục **độ liên quan của nhiệm vụ** được mô tả bởi $\tau_t$.

Một ví dụ dễ nhớ: kim la bàn chỉ **hướng** là $p_t$, độ mạnh của tín hiệu là $m_t$, còn mức phù hợp với nơi đang cần đi là $\tau_t$.

### Bước tổng hợp: tạo niềm tin hậu nghiệm về năng lực

Thay vì cộng số lần đúng rồi chia cho tổng số lần, ECRT duy trì một **phân phối xác suất về năng lực** của tác tử. Phân phối này có hai thông tin:

- Giá trị trung tâm: năng lực của tác tử được ước lượng ở mức nào.
- Độ phân tán: hệ thống chắc chắn đến đâu về ước lượng đó.

Một dạng cập nhật Beta–Bernoulli minh họa là:

$$
\alpha_i=\alpha_0+\sum_t m_t\tau_t p_t,\qquad
\beta_i=\beta_0+\sum_t m_t\tau_t(1-p_t).
$$

Trong đó:

- $\alpha_0,\beta_0$ biểu diễn niềm tin ban đầu trước khi xem lịch sử.
- $m_t\tau_t$ là lượng bằng chứng hiệu dụng sau khi xét sức nặng và độ liên quan.
- $m_t\tau_t p_t$ đóng góp về phía “đúng”.
- $m_t\tau_t(1-p_t)$ đóng góp về phía “sai”.

Kỳ vọng hậu nghiệm có thể được tính bằng:

\[
\mathbb{E}[\theta_i]=\frac{\alpha_i}{\alpha_i+\beta_i}.
\]

Tổng $\alpha_i+\beta_i$ phản ánh gần đúng lượng bằng chứng hiệu dụng. Hai tác tử có thể có cùng kỳ vọng nhưng tác tử có nhiều bằng chứng đáng tin và liên quan hơn sẽ có phân phối tập trung hơn.

Đây là **công thức thiết kế minh họa**, chưa phải tuyên bố rằng phiên bản cuối của ECRT bắt buộc dùng đúng mô hình Beta–Bernoulli. Trước khi chốt phương pháp cần xác định rõ giả định độc lập, cách chuẩn hóa $m_t$, cách học $\tau_t$ và cách xử lý các lần tương tác có tương quan.

### Ví dụ tính toán đơn giản

Giả sử niềm tin ban đầu là $\mathrm{Beta}(1,1)$, tương ứng với trạng thái trung lập. Một kết quả lịch sử có:

- Xác suất thật sự đúng $p_t=0,9$.
- Sức nặng phản hồi $m_t=0,8$.
- Độ liên quan tới nhiệm vụ mới $\tau_t=0,75$.

Lượng bằng chứng hiệu dụng là $m_t\tau_t=0,6$. Lần quan sát này cộng:

- $0,6\times0,9=0,54$ về phía đúng.
- $0,6\times0,1=0,06$ về phía sai.

Sau cập nhật, ta có $\alpha=1,54$ và $\beta=1,06$, nên kỳ vọng năng lực xấp xỉ $1,54/(1,54+1,06)=0,592$. Dù phản hồi tích cực, hệ thống không nhảy thẳng lên 0,9 vì mới chỉ có một bằng chứng với sức nặng và độ liên quan chưa đạt mức tuyệt đối.

Ví dụ này minh họa tính thận trọng của phương pháp; không phải cấu hình bắt buộc cho thí nghiệm cuối.

### Từ niềm tin hậu nghiệm sang trọng số ảnh hưởng

Sau khi có phân phối hậu nghiệm, hệ thống mới chuyển nó thành trọng số ảnh hưởng $w_i$. Có một số lựa chọn:

- Dùng kỳ vọng hậu nghiệm: đơn giản nhưng có thể chưa đủ thận trọng.
- Dùng cận dưới của khoảng tin cậy: chỉ trao ảnh hưởng cao khi ngay cả ước lượng thận trọng cũng tốt.
- Co trọng số về mức trung lập khi lượng bằng chứng còn ít.
- Từ chối dùng uy tín lịch sử và quay về bỏ phiếu đều nếu độ không chắc chắn vượt ngưỡng.

Nếu cần chuẩn hóa để tổng trọng số bằng 1, có thể chuyển điểm của từng tác tử qua một hàm chuẩn hóa. Tuy nhiên, lựa chọn này phải được giữ giống nhau giữa các phương pháp đối chứng để kết quả không bị quyết định bởi cách tổng hợp thay vì mô hình bằng chứng.

### Cách đọc sơ đồ quy trình

1. **Phản hồi $F$:** tín hiệu thô mà hệ thống nhận được.
2. **$p_t$:** phản hồi được quy đổi thành xác suất kết quả thật sự đúng.
3. **$m_t$:** xác định tín hiệu đó xứng đáng đóng góp bao nhiêu bằng chứng.
4. **$\tau_t$:** giảm hoặc giữ bằng chứng tùy mức phù hợp với nhiệm vụ hiện tại.
5. **Niềm tin hậu nghiệm:** tổng hợp lịch sử nhưng vẫn giữ độ không chắc chắn.
6. **Trọng số $w_i$:** chuyển niềm tin thành mức ảnh hưởng có kiểm soát.
7. **Quyết định của nhóm:** kết hợp câu trả lời theo trọng số.

Mặc dù hình được vẽ như một chuỗi, $p_t$ và $m_t$ đều xuất phát từ việc đánh giá nguồn phản hồi; không nhất thiết phải hiểu rằng luôn tính xong $p_t$ rồi mới có thể tính $m_t$.

### Những giả định cần nói rõ trong luận văn

- Các lần tương tác có độc lập có điều kiện hay không. Nếu nhiều phản hồi xuất phát từ cùng một lỗi, cộng chúng như các quan sát độc lập sẽ làm hệ thống quá tự tin.
- Chất lượng của mô hình chấm có thay đổi giữa các lĩnh vực hay theo thời gian không.
- Độ liên quan $\tau_t$ được xác định trước hay được học từ dữ liệu.
- Có dùng cùng dữ liệu để học độ liên quan và đánh giá phương pháp hay không; nếu có sẽ gây rò rỉ thông tin.
- Khi không có đủ bằng chứng, hệ thống quay về mức trung lập nào.
- Trọng số ảnh hưởng được dùng cho bỏ phiếu, chọn tác tử hay tổng hợp lập luận.

### Lời thoại gợi ý

> ECRT không cho phép phản hồi lịch sử đi thẳng vào quyết định. Với mỗi lần tương tác, hệ thống trước hết ước lượng xác suất kết quả thật sự đúng là $p_t$. Sau đó $m_t$ cho biết phản hồi mang bao nhiêu sức nặng, còn $\tau_t$ cho biết bằng chứng liên quan tới nhiệm vụ hiện tại đến đâu. Ba đại lượng này được tổng hợp thành một phân phối về năng lực, chứ không chỉ một điểm đơn. Chỉ sau khi xét cả giá trị trung tâm và độ không chắc chắn, hệ thống mới chuyển niềm tin đó thành trọng số ảnh hưởng $w_i$. Nhờ vậy, nhiều phản hồi yếu hoặc thành tích ở nhiệm vụ không liên quan sẽ không tự động tạo ra quyền ảnh hưởng lớn.

### Câu hội đồng có thể hỏi

**“$m_t$ có trùng với $p_t$ không?”** Không. $p_t$ cho biết bằng chứng nghiêng về đúng hay sai; $m_t$ cho biết bằng chứng mạnh hay yếu. Một bộ chấm đáng tin kết luận câu trả lời sai có thể tạo $p_t$ thấp nhưng $m_t$ cao.

**“Tại sao không chỉ nhân $p_t$ với $\tau_t$?”** Vì phép nhân đó chưa phân biệt một xác suất gần 0,5 do nguồn phản hồi vô dụng với một kết luận cân bằng được tạo từ nhiều nguồn có thông tin. $m_t$ kiểm soát lượng bằng chứng và tốc độ hệ thống trở nên chắc chắn.

**“$\tau_t$ có phải chỉ là độ tương đồng văn bản không?”** Không. Độ tương đồng văn bản chỉ là một phương pháp đối chứng. Mức liên quan cần phản ánh khả năng thành tích ở nhiệm vụ cũ dự đoán năng lực ở nhiệm vụ mới.

**“Công thức Beta có phải ECRT cuối cùng không?”** Chưa. Đây là cách minh họa trực quan cho việc cộng bằng chứng mềm và giữ độ không chắc chắn. Phiên bản cuối phải được lựa chọn sau khi kiểm tra giả định và so sánh các biến thể.

**“Nếu tất cả bằng chứng đều yếu thì hệ thống làm gì?”** Không ép tạo ra một chuyên gia giả. Hệ thống co về mức trung lập, bỏ phiếu đều hoặc từ chối sử dụng uy tín lịch sử, tùy cơ chế được định nghĩa trước.

### Câu chuyển sang Slide 14

> Điểm quan trọng còn lại là vì sao phải giữ cả một phân phối thay vì chỉ lấy giá trị trung bình. Slide tiếp theo minh họa hai tác tử có cùng điểm trung bình nhưng mức chắc chắn hoàn toàn khác nhau.

---

## Slide 14 — Why Uncertainty Matters

### Mục tiêu của slide

Giải thích vì sao một điểm uy tín duy nhất không đủ để quyết định mức ảnh hưởng. Hệ thống không chỉ cần biết **ước lượng năng lực là bao nhiêu**, mà còn phải biết **ước lượng đó chắc chắn tới mức nào và được tạo ra từ loại bằng chứng gì**.

Thông điệp quan trọng nhất của slide là:

> Hai tác tử có thể cùng được ước lượng năng lực ở mức 0,7, nhưng không nên nhận cùng một mức ảnh hưởng nếu một tác tử chỉ có rất ít bằng chứng còn tác tử kia có lịch sử dài, đáng tin và liên quan.

### Điểm uy tín đơn lẻ đã làm mất thông tin gì?

Giả sử hệ thống chỉ lưu cho mỗi tác tử một con số 0,7. Con số đó không cho biết:

- Có bao nhiêu lần tương tác đã được quan sát.
- Phản hồi đến từ nguồn mạnh hay yếu.
- Các lần tương tác có liên quan tới nhiệm vụ hiện tại hay không.
- Kết quả có ổn định hay chỉ do may mắn.
- Khoảng giá trị năng lực nào vẫn còn hợp lý theo dữ liệu.

Vì vậy, cùng một điểm 0,7 có thể xuất phát từ một quan sát rất mỏng hoặc một khối lượng bằng chứng lớn. Nếu hệ thống đối xử hai trường hợp như nhau, nó sẽ trao quá nhiều ảnh hưởng cho tác tử chưa được kiểm chứng đầy đủ.

### Hai tác tử có cùng ước lượng trung tâm 0,7

- **Tác tử A:** chỉ có một hoặc rất ít lần thành công đã được xác minh. Ước lượng trung tâm có thể là 0,7 do niềm tin ban đầu và cách tính bằng chứng mềm, nhưng dữ liệu vẫn quá ít để kết luận năng lực ổn định. Phân phối phải rộng.
- **Tác tử B:** có khoảng 100 quan sát đáng tin và liên quan, với tỷ lệ thành công hiệu dụng tương ứng mức 0,7. Ước lượng trung tâm vẫn là 0,7, nhưng có nhiều bằng chứng hơn nên phân phối hẹp hơn.

Điểm giống nhau là **giá trị trung tâm**. Điểm khác nhau là **độ tập trung của phân phối**. Tác tử B không nhất thiết có năng lực ước lượng cao hơn A, nhưng hệ thống có cơ sở vững hơn để tin vào con số của B.

### Cần hiểu đúng cụm “một lần thành công may mắn đã được xác minh”

“Đã được xác minh” nghĩa là lần trả lời đó có bằng chứng mạnh cho thấy kết quả đúng. Nó không có nghĩa là một lần đúng đã chứng minh tác tử có năng lực ổn định ở mức 0,7.

“May mắn” nhấn mạnh rằng ngay cả một kết quả đúng thật sự vẫn có thể là biến động ngẫu nhiên. Một tác tử yếu vẫn có thể trả lời đúng một câu; một tác tử mạnh vẫn có thể trả lời sai một câu. Muốn suy luận về năng lực ổn định, cần nhiều quan sát đáng tin và phù hợp.

Vì vậy, vấn đề của tác tử A không phải là nhãn của lần thành công không đáng tin. Vấn đề là **khối lượng bằng chứng quá nhỏ**.

### Cách biểu diễn bằng phân phối Beta

Nếu năng lực chưa biết của tác tử được ký hiệu là $\theta_i\in[0,1]$, ta có thể dùng phân phối Beta:

\[
\theta_i\sim\mathrm{Beta}(\alpha_i,\beta_i).
\]

Kỳ vọng của phân phối là:

\[
\mathbb E[\theta_i]=\frac{\alpha_i}{\alpha_i+\beta_i}.
\]

Phương sai là:

\[
\mathrm{Var}(\theta_i)=
\frac{\alpha_i\beta_i}
{(\alpha_i+\beta_i)^2(\alpha_i+\beta_i+1)}.
\]

Hai phân phối có cùng tỷ lệ $\alpha_i:\beta_i$ sẽ có cùng kỳ vọng. Tuy nhiên, khi tổng $\alpha_i+\beta_i$ lớn hơn, phương sai thường nhỏ hơn nếu giữ nguyên kỳ vọng.

Ví dụ:

- $\mathrm{Beta}(7,3)$ có kỳ vọng $7/(7+3)=0,7$.
- $\mathrm{Beta}(70,30)$ cũng có kỳ vọng $70/(70+30)=0,7$.

Phân phối thứ hai hẹp hơn nhiều vì nó đại diện cho khối lượng bằng chứng hiệu dụng lớn hơn. Các con số này nhằm minh họa tính chất toán học; chúng không phải là ánh xạ chính xác “một lần” và “một trăm lần” trên hình.

### Vì sao một lần thành công vẫn có thể cho điểm trung tâm 0,7?

Trong mô hình Bayes, ước lượng sau một lần quan sát còn phụ thuộc vào niềm tin ban đầu và sức nặng của bằng chứng. Vì vậy, hình trên slide nên được hiểu là hai trường hợp đã được đưa về cùng giá trị trung tâm để so sánh độ rộng, chứ không phải phép tính đơn giản “một lần đúng chia cho một lần thử bằng 0,7”.

Nếu hội đồng hỏi sâu, nên trả lời rằng các đường cong là **hình minh họa khái niệm**. Bài báo cuối phải ghi rõ tham số, niềm tin ban đầu và cách tạo phân phối; không được để hình minh họa trông như kết quả đo thực tế.

### Độ không chắc chắn trong ECRT đến từ đâu?

Độ không chắc chắn không chỉ đến từ số lượng quan sát. Nó còn đến từ:

- Phản hồi có thể đánh giá sai kết quả.
- Nguồn phản hồi có ít khả năng phân biệt đúng và sai.
- Nhiệm vụ lịch sử chỉ liên quan một phần tới nhiệm vụ mới.
- Các lần tương tác không độc lập, chẳng hạn nhiều câu hỏi gần như trùng nhau.
- Năng lực tác tử thay đổi theo thời gian.
- Số quan sát trong lĩnh vực đích còn ít.

Trong công thức minh họa của ECRT, $m_t\tau_t$ làm giảm khối lượng bằng chứng khi phản hồi yếu hoặc nhiệm vụ ít liên quan. Nhờ vậy, một trăm quan sát chất lượng thấp không nhất thiết tạo ra mức chắc chắn tương đương một trăm quan sát tốt.

### Vì sao giá trị trung bình chưa đủ để ra quyết định?

Nếu chi phí của một quyết định sai thấp, hệ thống có thể chấp nhận dùng kỳ vọng hậu nghiệm. Nhưng trong nhiệm vụ quan trọng, hai tác tử cùng có kỳ vọng 0,7 không nên được đối xử như nhau:

- Với tác tử A, xác suất năng lực thật thấp hơn nhiều so với 0,7 vẫn có thể đáng kể.
- Với tác tử B, dữ liệu đã thu hẹp phạm vi năng lực hợp lý quanh 0,7.

Khi hậu quả của việc tin nhầm lớn, hệ thống cần xét toàn bộ phân phối hoặc ít nhất một đại lượng phản ánh rủi ro, thay vì chỉ lấy trung bình.

### Khoảng đáng tin nên được hiểu như thế nào?

Trong cách diễn giải Bayes, nên gọi vùng được tô quanh ước lượng là **khoảng đáng tin hậu nghiệm**. Chẳng hạn, khoảng đáng tin 95% là một khoảng chứa 95% khối lượng xác suất hậu nghiệm của $\theta_i$, dưới mô hình và dữ liệu đã chọn.

Không nên phát biểu rằng “có 95% xác suất tham số cố định nằm trong khoảng tin cậy” nếu đang dùng khoảng tin cậy theo trường phái tần suất. Hai khái niệm này khác nhau. Vì Slide 13 đang sử dụng phân phối hậu nghiệm Beta, cách gọi “khoảng đáng tin hậu nghiệm” là nhất quán hơn.

### ECRT có thể sử dụng độ không chắc chắn như thế nào?

#### 1. Giảm ảnh hưởng khi bằng chứng còn mỏng

Thay vì dùng trực tiếp kỳ vọng $\mathbb E[\theta_i]$, hệ thống có thể sử dụng một ước lượng thận trọng, chẳng hạn cận dưới của khoảng đáng tin. Tác tử chỉ nhận ảnh hưởng cao khi ngay cả đánh giá thận trọng cũng cho thấy năng lực tốt.

#### 2. Co về mức trung lập

Khi dữ liệu ít, ước lượng nên gần với niềm tin ban đầu hơn. Hệ thống không vội tạo ra khoảng cách lớn giữa các tác tử chỉ từ một vài lần tương tác.

#### 3. Từ chối sử dụng lịch sử

Nếu độ không chắc chắn vượt một ngưỡng định trước, hệ thống có thể tạm thời không dùng uy tín lịch sử và quay về bỏ phiếu đều, chọn thêm tác tử hoặc yêu cầu kiểm tra bổ sung.

#### 4. Thu thập thêm bằng chứng có mục tiêu

Hệ thống có thể ưu tiên giao thêm nhiệm vụ kiểm tra cho tác tử có tiềm năng nhưng phân phối còn rộng. Đây là cách dùng độ không chắc chắn để quyết định nên thu thập dữ liệu ở đâu, thay vì chỉ dùng nó để giảm trọng số.

### “Từ chối” không có nghĩa hệ thống không trả lời

Trong bối cảnh này, từ chối có thể mang nhiều mức:

- Từ chối tin vào uy tín lịch sử và quay về trọng số bằng nhau.
- Không chọn một tác tử duy nhất mà yêu cầu nhiều tác tử cùng kiểm tra.
- Chuyển nhiệm vụ sang bộ kiểm tra đáng tin hơn.
- Chỉ trong trường hợp rủi ro cao mới từ chối đưa ra quyết định cuối.

Do đó, cần định nghĩa rõ hệ thống đang từ chối **sử dụng bằng chứng**, **phân bổ ưu tiên**, hay **trả lời nhiệm vụ**. Không nên dùng từ “từ chối” chung chung.

### Cách đọc hai đường cong trên hình

- Trục ngang biểu diễn các giá trị năng lực có thể có, từ thấp tới cao.
- Trục dọc biểu diễn mật độ xác suất, không phải số lần thành công.
- Hai đường cong có tâm gần 0,7 nên có cùng ước lượng trung tâm.
- Đường cong rộng và thấp biểu thị nhiều giá trị năng lực vẫn còn hợp lý: độ không chắc chắn cao.
- Đường cong hẹp và cao biểu thị xác suất tập trung quanh 0,7: độ không chắc chắn thấp.
- Diện tích dưới mỗi đường cong bằng 1. Đường cao hơn không có nghĩa tác tử “có nhiều năng lực hơn”; nó chỉ biểu thị phân phối tập trung hơn.

### Ví dụ quyết định

Giả sử nhóm phải chọn một tác tử kiểm tra bản vá bảo mật:

- Tác tử A có kỳ vọng năng lực 0,7 nhưng khoảng đáng tin rất rộng, chẳng hạn từ 0,25 đến 0,95.
- Tác tử B cũng có kỳ vọng 0,7 nhưng khoảng đáng tin hẹp hơn, chẳng hạn từ 0,64 đến 0,76.

Nếu chỉ nhìn điểm trung bình, hai tác tử được xem là ngang nhau. Nếu xét rủi ro, B là lựa chọn an toàn hơn. A vẫn có thể rất giỏi, nhưng bằng chứng hiện tại chưa đủ để trao độc quyền quyết định. Hệ thống có thể cho A tham gia với trọng số thấp hơn hoặc yêu cầu thêm kiểm tra.

Các khoảng số trên chỉ dùng minh họa, không phải kết quả của thí nghiệm.

### Lời thoại gợi ý

> Hai tác tử có thể cùng được ước lượng ở mức 0,7 nhưng không có nghĩa bằng chứng phía sau tương đương. Một tác tử chỉ có rất ít lần thành công thì phân phối năng lực còn rộng; tác tử có nhiều kết quả đáng tin và liên quan sẽ có phân phối tập trung hơn. Nếu chỉ lưu một điểm, hệ thống làm mất sự khác biệt này và có thể trao quá nhiều ảnh hưởng cho lịch sử mỏng. Vì vậy, ECRT giữ cả giá trị trung tâm lẫn độ không chắc chắn. Khi bằng chứng chưa đủ, hệ thống giảm ảnh hưởng, quay về mức trung lập hoặc yêu cầu thêm kiểm tra, thay vì giả vờ rằng mình đã biết chắc.

### Câu hội đồng có thể hỏi

**“Tại sao một lần đúng lại cho trung bình 0,7?”** Con số và đường cong trên hình nhằm cố định cùng một giá trị trung tâm để so sánh độ không chắc chắn. Trong mô hình thực, giá trị sau một lần quan sát còn phụ thuộc niềm tin ban đầu và sức nặng bằng chứng.

**“Tại sao không chỉ dùng số lượng quan sát?”** Vì một trăm phản hồi yếu, trùng lặp hoặc không liên quan không tương đương một trăm bằng chứng độc lập và đáng tin. Cần dùng khối lượng bằng chứng hiệu dụng.

**“Đường cong cao hơn có nghĩa tác tử B tốt hơn không?”** Không. Hai tác tử có cùng ước lượng trung tâm. Đường cong cao và hẹp chỉ có nghĩa hệ thống chắc chắn hơn về ước lượng của B.

**“Giảm ảnh hưởng vì chưa chắc chắn có làm bỏ lỡ tác tử mới nhưng giỏi không?”** Có thể. Đây là sự đánh đổi giữa sử dụng kiến thức hiện có và thu thập thêm thông tin. Vì vậy hệ thống có thể giao các nhiệm vụ kiểm tra an toàn để giảm độ không chắc chắn thay vì loại bỏ tác tử mới vĩnh viễn.

**“Dùng cận dưới có quá bảo thủ không?”** Có thể, tùy chi phí của quyết định sai. Cơ chế chuyển phân phối thành trọng số phải được chọn theo mức rủi ro và được so sánh trong thí nghiệm, không mặc định một quy tắc phù hợp cho mọi tình huống.

### Điểm phải nói thật chính xác

- Hình là minh họa khái niệm, không phải kết quả thực nghiệm.
- Cùng trung bình không có nghĩa cùng độ chắc chắn.
- “Đã xác minh” một kết quả không đồng nghĩa đã xác minh năng lực lâu dài.
- Nhiều quan sát chỉ làm giảm độ không chắc chắn nếu chúng mang thông tin và không bị tính lặp quá mức.
- ECRT giữ độ không chắc chắn để hỗ trợ quyết định; nó không làm biến mất mọi nguồn không chắc chắn.

### Câu chuyển sang Slide 15

> Sau khi xác định phương pháp phải giữ cả giá trị trung tâm lẫn độ không chắc chắn, câu hỏi tiếp theo là làm thế nào kiểm tra điều đó một cách có kiểm soát. Slide tiếp theo trình bày thí nghiệm trung tâm trên hai chiều chất lượng phản hồi và khả năng chuyển giao.

---

## Slide 15 — How We'll Test It: The Central Experiment

### Mục tiêu của slide

Trình bày thí nghiệm trọng tâm dưới dạng factorial design 4×3.

### Hai factor

**Feedback quality (Q)** có bốn mức:

- Clean: feedback gần ground truth theo cơ chế đã định nghĩa.
- Mild noise: flip/noise rate nhỏ hoặc judge calibration suy giảm nhẹ.
- Strong noise: feedback sai thường xuyên hơn.
- Adversarial: feedback được tạo có chủ đích để gây sai lệch reputation.

**Task transfer (T)** có ba mức:

- Same task: history và target cùng loại.
- Related task: khác task nhưng có skill/cấu trúc liên quan.
- Unrelated task: lịch sử khác miền hoặc không nên chuyển.

Q × T ở slide 18 và appendix nên được định nghĩa thống nhất là **Quality × Transfer**.

### “Manipulated independently” nghĩa là gì?

Mỗi mức feedback quality phải xuất hiện với mỗi mức task transfer, tạo 12 conditions. Ví dụ, phải có cả “clean + unrelated” và “adversarial + same task”. Nhờ vậy ta không đồng nhất noisy feedback với unrelated task.

### Main effect và interaction

- Main effect của Q: trung bình qua các mức T, feedback quality có thay đổi reputation quality không?
- Main effect của T: trung bình qua các mức Q, relevance có ảnh hưởng không?
- Interaction Q×T: tác động của noise có thay đổi tùy mức transfer không?

Một interaction có thể là: skill-conditioned baseline hoạt động tốt khi feedback sạch, nhưng borrowing làm lỗi tăng mạnh khi feedback adversarial và target chỉ “related”.

### Heatmap biểu diễn gì?

Màu đậm là calibration error cao. Slide hiện tại chỉ là mock-up; không được nói màu là kết quả thật. Sau thí nghiệm, mỗi ô phải là mean qua seeds với uncertainty/error bars hoặc confidence interval.

### Thiết kế chống leakage

Ground truth được dùng để tính metric offline, không được đưa cho reputation mechanism. Split history/target, prompt, seed và domain phải được cố định trước. Nếu dùng cùng item hoặc paraphrase quá gần ở history và target, kết quả transfer có thể bị leakage.

### Lời thoại gợi ý

> Đây là thí nghiệm quan trọng nhất. Em tạo 12 condition bằng cách thao tác độc lập feedback quality và task transfer. Thiết kế này cho biết không chỉ mỗi yếu tố có ảnh hưởng hay không, mà còn liệu chúng có tương tác và baseline nào thất bại ở regime nào.

---

## Slide 16 — Evaluation Plan at a Glance

### Mục tiêu của slide

Cho thấy thí nghiệm có benchmark, baseline, attack, metric và output artifact rõ ràng.

### Primary benchmark: MMLU-Pro

MMLU-Pro là benchmark multiple-choice reasoning gồm hơn 12.000 câu, 14 domain và mở rộng từ 4 lên 10 lựa chọn. Paper gốc nhấn mạnh câu hỏi khó hơn, thiên về reasoning hơn và ổn định hơn trước biến thể prompt so với MMLU.[^6]

Vì có đáp án khách quan, MMLU-Pro phù hợp để giữ clean ground truth cho **offline scoring**. Ground truth không nên làm feedback trực tiếp cho cơ chế đang được đánh giá, nếu không ta đã giả định away vấn đề imperfect feedback.

### Secondary benchmark: AppWorld

AppWorld cung cấp môi trường ứng dụng có state, API và đánh giá bằng thay đổi trạng thái database. Benchmark gốc có các tác vụ tương tác phức tạp và state-based unit tests, nên feedback gần với hậu quả thực thi hơn câu hỏi trắc nghiệm.[^7] Đây là external validity stretch goal vì setup và chi phí chạy cao hơn.

### Baselines

1. Uniform voting: mọi agent có weight như nhau.
2. Global reputation: một score chung cho mỗi agent.
3. Skill-conditioned reputation: score theo skill/task type.
4. ECRT: reliability + relevance + uncertainty.
5. Oracle upper bounds: dùng thông tin lý tưởng chỉ để biết trần hiệu năng, không phải phương pháp deployable.

### Attacks

- Delayed betrayal: agent hành xử tốt để tích trust rồi đổi hành vi.
- Cross-skill laundering: farm history ở skill nguồn rồi chuyển influence sang skill đích.
- Feedback poisoning: thao túng tín hiệu đánh giá để thay đổi reputation.

### Metrics

- **Brier score:** $\frac1N\sum_i(p_i-y_i)^2$. Thấp hơn tốt hơn; là proper scoring rule cho xác suất.[^8]
- **NLL:** $-\frac1N\sum_i[y_i\log p_i+(1-y_i)\log(1-p_i)]$. Phạt nặng dự đoán sai nhưng quá tự tin.
- **ECE:** chia confidence thành bin rồi đo chênh giữa confidence và accuracy. Dễ giải thích nhưng phụ thuộc binning; không nên dùng một mình. Calibration là việc probability phản ánh đúng tần suất correctness.[^9]
- Ranking quality: agent giỏi hơn có được xếp cao hơn không.
- Team accuracy: quyết định cuối đúng bao nhiêu.
- Attack resistance: degradation dưới attack, attack success rate hoặc regret.

### HistRepEval

Protocol nên định nghĩa schema episode, cách tạo feedback noise, taxonomy transfer, split, baseline API, metric và seed. Mục tiêu là phương pháp reputation khác có thể chạy qua cùng harness.

### Lời thoại gợi ý

> MMLU-Pro cho ground truth sạch để đánh giá offline; AppWorld kiểm tra external validity trong môi trường stateful. Baseline tăng dần độ phức tạp, attack chỉ là stress test, và metric bao phủ cả calibration, ranking, team outcome lẫn robustness.

---

## Slide 17 — Section Divider: Execution Plan

### Mục tiêu của slide

Chuyển từ “đề xuất nghiên cứu” sang “làm thế nào hoàn thành và kiểm soát rủi ro”.

### Lời thoại gợi ý

> Phương pháp chỉ có giá trị nếu kế hoạch thực nghiệm khả thi. Phần cuối trình bày roadmap sáu tuần, go/no-go gate, rủi ro và tiêu chí thành công.

---

## Slide 18 — 6-Week Roadmap

### Mục tiêu của slide

Cho thấy mỗi tuần có deliverable kiểm tra được và quyết định tiếp tục dựa trên evidence.

### Week 1 — Lock gap and benchmark design

Hoàn thiện research question, operational definition của heterogeneity, reliability và relevance; chốt paper skeleton. **Gate:** agent pool có thật sự heterogeneous không? Cần capability matrix trên các domain/skill, không chỉ chọn các model có tên khác nhau.

### Week 2 — Reproduce baselines and HistRepEval v0.1

Chạy uniform/global/skill-conditioned từ đầu đến cuối; xây schema và logging. **Gate:** pipeline có end-to-end không, ground truth có leakage vào feedback/reputation không, seed có tái lập không?

### Week 3 — Core characterization experiment

Chạy Q×T và phân tích effect sizes, uncertainty và consistency theo seed/domain. **Gate:** có phenomenon thật và tái lập không? Đây là mốc quyết định vì nếu không có effect/interaction đáng kể, method phức tạp hơn có thể không được biện minh.

### Week 4 — Implement ECRT

Chốt estimator cho (p_t,m_t,\tau_t), posterior và mapping sang influence; chạy ablation. **Gate:** ECRT có lợi ở ít nhất một regime có ý nghĩa và lợi đó có phù hợp với mechanism claim không?

### Week 5 — Robustness and external validity

Chạy attack, domain shift và stretch benchmark nếu đủ thời gian. **Gate:** mọi claim ở Introduction phải có bảng/figure hoặc bị hạ giọng.

### Week 6 — Freeze and release

Đóng băng config/results, viết paper, kiểm tra reproducibility, release artifact. Không thêm experiment tùy hứng sau khi đã viết conclusion trừ khi phát hiện lỗi.

### Vì sao Week 3 là true gate?

Week 3 kiểm tra tiền đề khoa học của toàn paper. Nếu dữ liệu không ủng hộ original plan, đổi hướng sớm giúp tránh six-week confirmation exercise.

### Lời thoại gợi ý

> Mỗi tuần kết thúc bằng câu hỏi go/no-go chứ không chỉ bằng danh sách việc. Week 3 là gate thật: nếu Q×T không tạo phenomenon tái lập, em sẽ không ép ECRT thành câu chuyện thắng; em chuyển sang characterization hoặc boundary result.

---

## Slide 19 — What Could Go Wrong (and the Plan B)

### Mục tiêu của slide

Thể hiện risk ownership và phương án khoa học hợp lệ cho từng thất bại.

### Risk 1: Q×T không có effect phân biệt được

Có thể effect thật nhỏ, noise lớn hoặc operationalization chưa tốt. Trước khi kết luận null, cần power/sensitivity analysis, kiểm tra manipulation và confidence interval. Nếu thiết kế đủ nhạy mà effect vẫn nhỏ, reframe thành negative-result/characterization paper: trong regime đã kiểm tra, tách hai factor không đem lợi ích đáng kể.

### Risk 2: một chiều áp đảo chiều còn lại

Ví dụ relevance giải thích gần hết variance, reliability thêm rất ít. Đây là boundary result, không phải thất bại. Method có thể thu gọn quanh factor trội và báo cáo điều kiện factor còn lại bắt đầu quan trọng.

### Risk 3: overlap với concurrent work

Chạy novelty search ở Weeks 1/3/5/6. Nếu attack đã được công bố, giữ nó làm stress test. Novelty còn có thể nằm ở controlled interaction, uncertainty-aware model và reusable protocol.

### Risk 4: agent pool không heterogeneous

Nếu mọi model có ranking giống nhau trên mọi skill, skill routing không có đất để thể hiện. Chạy capability audit trước; thay model, scaffold hoặc tool profile nếu cần. Việc “swap models” phải được quy định trước tiêu chí để tránh cherry-picking.

### Lời thoại gợi ý

> Slide này không phải bi quan. Nó chứng minh mỗi failure mode có một quyết định hợp lý. Một thesis defensible phải nói trước điều gì sẽ làm mình đổi claim, đổi method hoặc dừng một nhánh, thay vì chỉ mô tả best case.

### Điểm cần tránh

Không gọi mọi kết quả null là publishable. Giá trị phụ thuộc vào thiết kế đủ mạnh, phân tích trung thực, reporting đầy đủ và kết luận giới hạn đúng phạm vi.

---

## Slide 20 — What “Success” Looks Like

### Mục tiêu của slide

Định nghĩa success trước khi nhìn kết quả, giảm nguy cơ đổi tiêu chí sau thí nghiệm.

### Minimum success

Controlled study cho thấy reliability và task transfer đều có ảnh hưởng đo được đến reputation quality, tái lập qua seed/domain. “Measurably” nên gắn với effect size và interval, không chỉ (p<0.05).

### Strong success

Ngoài characterization, ECRT tốt hơn global/skill-conditioned baseline ở calibration hoặc attack robustness trong regime có ý nghĩa, đồng thời HistRepEval được release. Không bắt buộc thắng mọi cell; cần giải thích **where and why**.

### Valid boundary or negative finding

Ví dụ skill conditioning đã đủ trong regime X. Một kết quả như vậy giúp cộng đồng biết khi nào không cần method phức tạp. Để hợp lệ, regime X phải được định nghĩa, test đủ power và không chọn sau khi xem kết quả mà không disclosure.

### Vì sao không bán paper bằng “X% better”?

Một con số aggregate có thể che giấu calibration kém, domain shift hoặc attack vulnerability. Claim sâu hơn là historical performance không phải một loại evidence duy nhất; reliability và relevance cần được hỏi riêng trước khi tạo trust.

### Lời thoại gợi ý

> Thành công tối thiểu là characterization rõ và tái lập. Phiên bản mạnh có thêm ECRT và HistRepEval. Ngay cả khi ECRT không thắng, một boundary finding mạnh vẫn là đóng góp. Vì vậy paper không phụ thuộc vào một con số accuracy đẹp; nó phụ thuộc vào việc trả lời đúng câu hỏi bằng chứng.

---

## Slide 21 — Summary & Discussion

### Mục tiêu của slide

Khóa lại bốn ý và mở phần hỏi đáp.

### Bốn ý cần nhắc lại

1. **Problem:** đội LLM cần influence theo expertise, nhưng reputation lịch sử đến từ feedback không hoàn hảo.
2. **Gap:** reliability của feedback và transferability của task chưa được tách và thao tác như một interaction chính trong thiết kế mục tiêu.
3. **Approach:** characterize Q×T trước, sau đó ECRT, stress test và HistRepEval.
4. **Execution:** roadmap sáu tuần với gate ở Week 3 và plan B rõ.

### Lời thoại kết thúc gợi ý

> Tóm lại, RepGuard xem reputation transfer là bài toán bằng chứng hai chiều chứ không phải một score. Em sẽ kiểm chứng interaction trước, chỉ giữ ECRT nếu dữ liệu biện minh, và release protocol để kết quả có thể tái lập. Em xin kết thúc phần trình bày và mong nhận câu hỏi, đặc biệt về operationalization của feedback reliability, task transfer và tiêu chí go/no-go.

### Câu hỏi nên chủ động mời

- Cách định nghĩa related task có đủ khách quan không?
- Làm sao ước lượng judge reliability mà không dùng ground truth lúc deployment?
- Influence weight được dùng cho routing, voting hay message aggregation?
- Null interaction sẽ làm claim thay đổi thế nào?

---

# Phần Appendix — kiến thức cần sẵn sàng khi hội đồng hỏi sâu

## A1 — Beta posterior và uncertainty

Nếu competence θ của agent được mô hình hóa bằng Beta(α,β), posterior mean và variance là:

$$
\mathbb E[\theta]=\frac{\alpha}{\alpha+\beta},\qquad
\mathrm{Var}(\theta)=\frac{\alpha\beta}{(\alpha+\beta)^2(\alpha+\beta+1)}.
$$

Hai agent có cùng mean khi tỷ lệ α:β giống nhau, nhưng agent có α+β lớn hơn sẽ có variance nhỏ hơn. Với soft evidence, mỗi episode có thể cộng fractional count theo (m_t\tau_t p_t) và (m_t\tau_t(1-p_t)). Cần nói rõ independence assumption giữa các episode; nếu episode tương quan mạnh, cộng count trực tiếp sẽ quá tự tin.

## A2 — Ước lượng (p_t) từ judge calibration

Với feedback nhị phân (F\in\{0,1\}), true label (z\), judge sensitivity (s=P(F=1\mid z=1)), specificity (c=P(F=0\mid z=0)) và prior π=P(z=1):

$$
P(z=1\mid F=1)=\frac{s\pi}{s\pi+(1-c)(1-\pi)},
$$

$$
P(z=1\mid F=0)=\frac{(1-s)\pi}{(1-s)\pi+c(1-\pi)}.
$$

Ý nghĩa: một feedback “positive” không tự động bằng xác suất 1. Kết quả phụ thuộc độ nhạy, độ đặc hiệu và base rate. Nếu judge gần ngẫu nhiên, (m_t) nên nhỏ để tránh tạo certainty giả.

## A3 — Cách định nghĩa task relevance (\tau_t)

Có thể so sánh ba family:

- Discrete taxonomy: same skill = 1, related = λ, unrelated = 0.
- Learned similarity: embedding hoặc classifier dự đoán transfer.
- Empirical transfer: competence ở task A dự đoán performance task B mạnh đến đâu trên validation data.

Để tránh circularity, relevance estimator không được học trực tiếp trên test outcomes đang dùng để đánh giá ECRT.

## A4 — Baseline và ablation tối thiểu

- B0 single best fixed agent.
- B1 uniform voting.
- B2 global reputation.
- B3 skill-conditioned reputation without borrowing.
- B4 skill-conditioned with cross-skill borrowing.
- B5 ECRT without reliability term.
- B6 ECRT without relevance term.
- B7 ECRT without uncertainty/using posterior mean only.
- Oracle relevance, oracle feedback correctness và oracle best-agent làm upper bounds.

Ablation trả lời từng thành phần có đóng góp gì; chỉ so full ECRT với baseline không đủ để chứng minh mechanism.

## A5 — Attack definitions

- **Delayed betrayal:** agent tích lũy trust trong prefix lịch sử rồi giảm correctness sau trigger.
- **Cross-skill laundering:** tối ưu history ở source skill để tăng influence ở target skill.
- **Feedback poisoning:** thay đổi hoặc tạo feedback sai; phải tách poisoning judge output khỏi việc agent trực tiếp trả lời sai.
- **Sybil amplification:** nhiều identity phối hợp tạo evidence; nếu ngoài scope phải tuyên bố rõ, không ám chỉ ECRT chống Sybil.

Nên báo cáo attack budget, knowledge, control, target và success criterion. Không so attack khi threat model khác nhau mà không giải thích.

## A6 — Metrics glossary

### Brier score

Với dự đoán (p_i) và outcome (y_i\in\{0,1\}):

$$
\mathrm{Brier}=\frac{1}{N}\sum_i(p_i-y_i)^2.
$$

Thấp hơn tốt hơn. Brier đánh giá chất lượng probability tổng thể, bao gồm cả calibration và discrimination; đừng gọi nó là “pure calibration error”.

### Negative log-likelihood

$$
\mathrm{NLL}=-\frac1N\sum_i[y_i\log p_i+(1-y_i)\log(1-p_i)].
$$

NLL rất nhạy với dự đoán quá tự tin nhưng sai. Cần clip probability để tránh log(0) trong implementation, đồng thời ghi rõ epsilon.

### Expected Calibration Error

$$
\mathrm{ECE}=\sum_{b=1}^{B}\frac{|S_b|}{N}\left|\mathrm{acc}(S_b)-\mathrm{conf}(S_b)\right|.
$$

ECE dễ trực quan hóa bằng reliability diagram nhưng phụ thuộc số bin và binning strategy. Báo cáo thêm Brier/NLL và diagram sẽ đáng tin hơn chỉ một ECE.

### Ranking quality

Có thể dùng Spearman/Kendall giữa estimated reputation và true competence, hoặc pairwise accuracy: xác suất hệ thống xếp agent tốt hơn lên trên.

### Team outcome

Team accuracy phải đi kèm chi phí token/call nếu methods có budget khác nhau. Nếu ECRT gọi judge nhiều hơn, cần so ở cùng budget hoặc báo cáo trade-off.

### Robustness

Có thể báo cáo clean-to-attack degradation, routing regret, attack success rate và calibration shift. Mọi metric phải được định nghĩa trước khi chạy main experiment.

---

# Bộ câu hỏi hội đồng có thể hỏi và câu trả lời ngắn

## 1. Tại sao không chỉ dùng skill-conditioned reputation?

Skill conditioning giải quyết “evidence thuộc skill nào”, nhưng có thể vẫn coi feedback lịch sử là đúng. RepGuard thêm câu hỏi upstream: evidence đó có đáng tin và có bao nhiêu khối lượng trước khi transfer.

## 2. Làm sao biết correctness nếu nó latent?

Trong benchmark offline, ground truth chỉ dùng để calibrate/evaluate. Trong deployment, (p_t) được suy ra từ calibrated judge, redundant evaluators, executable checks hoặc provenance. Luận văn không giả định luôn biết (z_t).

## 3. Relevance có phải chỉ là cosine similarity?

Không. Cosine similarity là một baseline khả dĩ. Relevance đúng nghĩa là khả năng evidence ở history giúp dự đoán competence trên target; cần validation thực nghiệm và tránh leakage.

## 4. Vì sao cần (m_t) ngoài (p_t)?

(p_t) cho hướng của bằng chứng; (m_t) cho độ mạnh. Feedback gần ngẫu nhiên không nên đóng góp cùng sample mass với feedback đã hiệu chỉnh tốt.

## 5. ECRT có đảm bảo an toàn không?

Không nên tuyên bố guarantee tổng quát. ECRT được thiết kế để giảm một lớp lỗi evidence transfer và sẽ được stress-test trong threat model cụ thể.

## 6. Nếu interaction không significant thì sao?

Kiểm tra effect size và interval, không chỉ p-value. Nếu design đủ nhạy mà interaction nhỏ, đó là boundary/negative finding và có thể dẫn đến method đơn giản hơn.

## 7. Vì sao MMLU-Pro là primary benchmark?

Nó có nhiều domain, đáp án khách quan và reasoning challenge, thuận lợi để tạo agent competence profile và giữ ground truth cho offline scoring.[^6] Hạn chế là multiple choice chưa phản ánh đầy đủ agentic tool use, nên AppWorld là stretch external-validity benchmark.[^7]

## 8. “Reproducible across seeds/domains” cụ thể là gì?

Không chỉ mean aggregate. Cần lặp nhiều seed, báo variance/interval và kiểm tra effect direction ở nhiều domain. Domain heterogeneity nên được báo cáo thay vì bị average che mất.

## 9. Influence được áp dụng ở đâu?

Cần chốt trong implementation: weighted voting, answer selection, routing budget, message visibility hay aggregation. Main experiments nên giữ một mechanism chính; các mechanism khác là ablation/extension.

## 10. HistRepEval khác benchmark thông thường thế nào?

Nó là protocol/harness cho reputation transfer: tạo history, perturb feedback, kiểm soát transfer relation, chạy baseline/method và đánh giá calibration/routing/robustness dưới cùng schema.

---

# Những câu tuyệt đối không nên nói khi bảo vệ

- “Ground truth luôn có sẵn.” Chỉ đúng ở offline benchmark.
- “ECRT đã chứng minh tốt hơn.” Đây mới là proposal, trừ khi đã có pilot result và chỉ rõ setup.
- “Hai chiều hoàn toàn độc lập trong thực tế.” Chỉ nói chúng được tách về khái niệm và thao tác độc lập trong experiment.
- “Không ai từng nghiên cứu vấn đề này.” Hãy nói “theo literature review hiện tại, chưa thấy thiết kế nào…”.
- “Brier/ECE chỉ đo calibration thuần túy.” Brier là proper score tổng thể; ECE phụ thuộc binning.
- “Negative result chắc chắn publishable.” Chỉ hợp lệ nếu thiết kế đủ mạnh, reporting trung thực và conclusion đúng phạm vi.
- “RepGuard chống mọi reputation attack.” Chỉ đánh giá threat model đã định nghĩa.

---

# Kiểm tra nguồn trước khi nộp bản cuối

| Citation trong deck | Trạng thái đối chiếu | Việc cần làm |
|---|---|---|
| Pappu et al., 2026 | Đã xác minh paper/arXiv và claim expert leveraging | Thêm full citation vào bibliography |
| Xia & Wang, 2026 | Đã xác minh arXiv và cross-skill laundering | Ghi rõ preprint/venue status |
| CogTrust, 2026 | Đã xác minh DOI và nội dung dynamic trust/decay | Dùng metadata publisher chính thức |
| SentinelNet, 2026 | Có paper nhưng arXiv ID bắt đầu 2510 | Kiểm tra năm muốn cite: preprint 2025 hay venue 2026 |
| Ebrahimi et al., 2025 | Chưa đủ metadata từ file gốc | Không nộp citation cho đến khi có title/URL/DOI |
| WEREWOLF, EMNLP 2026 | Chưa xác minh đầy đủ | Tìm ACL Anthology/DOI/arXiv; nếu không có thì bỏ hoặc đổi nguồn |
| Trust No Tool, 2026 | Có dấu vết paper về untrusted tool feedback, metadata cần chốt | Xác minh title/authors/version cuối |
| MMLU-Pro | Đã xác minh NeurIPS 2024 | Cite paper chính thức |
| AppWorld | Đã xác minh ACL 2024 và site/repo chính thức | Cite ACL Anthology |

---

# Nguồn tham khảo

[^1]: Pappu et al., “Multi-Agent Teams Hold Experts Back,” arXiv:2602.01011 (2026).
[^2]: Xia & Wang, “When Should Agent Trust Be Conditional? Characterizing and Attacking Skill-Conditional Reputation in Agent Swarms,” arXiv:2606.14200 (2026).
[^3]: Wang et al., “CogTrust: Cognitive Logic-Based Framework for Dynamic Trust Evaluation in Multi-Agent Systems,” *Expert Systems with Applications* (2026).
[^4]: “SentinelNet: Safeguarding Multi-Agent Collaboration Through Credit-Based Dynamic Threat Detection,” arXiv:2510.16219; cần kiểm tra lại năm/venue khi chốt bibliography.
[^5]: “Trust No Tool: Evaluating and Defending LLM Agents under Untrusted Tool Feedback”; nguồn chính thức và metadata cuối cần được xác minh trước khi nộp.
[^6]: Wang et al., “MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark,” NeurIPS 2024.
[^7]: Trivedi et al., “AppWorld: A Controllable World of Apps and People for Benchmarking Interactive Coding Agents,” ACL 2024.
[^8]: Gneiting & Raftery, “Strictly Proper Scoring Rules, Prediction, and Estimation,” JASA 2007.
[^9]: Guo et al., “On Calibration of Modern Neural Networks,” ICML 2017.

1. Aneesh Pappu et al. “[Multi-Agent Teams Hold Experts Back](https://arxiv.org/abs/2602.01011).” arXiv:2602.01011, 2026.
2. Yihan Xia and Taotao Wang. “[When Should Agent Trust Be Conditional? Characterizing and Attacking Skill-Conditional Reputation in Agent Swarms](https://arxiv.org/abs/2606.14200).” arXiv:2606.14200, 2026.
3. Jiye Wang et al. “[CogTrust: Cognitive Logic-Based Framework for Dynamic Trust Evaluation in Multi-Agent Systems](https://doi.org/10.1016/j.eswa.2026.131535).” *Expert Systems with Applications*, 2026.
4. “[SentinelNet: Safeguarding Multi-Agent Collaboration Through Credit-Based Dynamic Threat Detection](https://arxiv.org/abs/2510.16219).” arXiv:2510.16219. Kiểm tra metadata venue/năm trước khi dùng trong bản nộp.
5. “[Trust No Tool: Evaluating and Defending LLM Agents under Untrusted Tool Feedback](https://www.researchgate.net/publication/404990716_Trust_No_Tool_Evaluating_and_Defending_LLM_Agents_under_Untrusted_Tool_Feedback).” Bản truy cập để đối chiếu khái niệm; cần thay bằng URL publisher/arXiv chính thức khi hoàn thiện bibliography.
6. Yubo Wang et al. “[MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark](https://proceedings.neurips.cc/paper_files/paper/2024/hash/ad236edc564f3e3156e1b2feafb99a24-Abstract.html).” NeurIPS 2024 Datasets and Benchmarks Track.
7. Harsh Trivedi et al. “[AppWorld: A Controllable World of Apps and People for Benchmarking Interactive Coding Agents](https://aclanthology.org/2024.acl-long.850/).” ACL 2024. Xem thêm [website chính thức](https://appworld.dev/) và [repository](https://github.com/StonyBrookNLP/appworld).
8. Tilmann Gneiting and Adrian E. Raftery. “[Strictly Proper Scoring Rules, Prediction, and Estimation](https://www.eecs.harvard.edu/cs286r/courses/fall10/papers/Gneiting07.pdf).” *Journal of the American Statistical Association*, 2007.
9. Chuan Guo et al. “[On Calibration of Modern Neural Networks](https://proceedings.mlr.press/v70/guo17a.html).” ICML 2017.
10. Tài liệu nguồn của deck: `RepGuard_Presentation_Content.md`, nội dung do người dùng cung cấp, dùng làm cấu trúc chính cho speaker guide này.
