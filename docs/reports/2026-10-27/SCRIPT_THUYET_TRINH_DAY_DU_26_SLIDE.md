# Kịch bản thuyết trình RepGuard

Báo cáo literature review và tiến độ ngày 28 tháng 10 năm 2026

## Cách dùng tài liệu

Đây là lời nói hoàn chỉnh theo bản PDF 26 trang của deck **RepGuard Literature Review & Progress**. Script dùng cách xưng “chúng em” khi báo cáo với Thầy. Phần **Lời trình bày** và **Chuyển slide** có thể nói trực tiếp; các dòng **Điểm cần truyền đạt** và **Gợi ý trình bày** dành để tập, không đọc thành lời.

Mạch giải thích xuyên suốt là: hệ thống cần chọn agent; lịch sử dùng để ước lượng năng lực; lịch sử chịu ảnh hưởng của cách chấm; ước lượng chỉ có ích khi cải thiện quyết định; các thực nghiệm hiện tại chưa xác nhận lợi ích đó; phép thử tiếp theo cần đo trước chất lượng feedback và khả năng cải thiện của pool. Các thuật ngữ được giải thích ở lần xuất hiện đầu tiên. Không cần đọc tên tất cả tác giả hoặc từng hàng trong bảng.

Số slide dưới đây là **số trang 1 đến 26 của bản PDF đã bàn giao**. Canva đã được chỉnh thứ tự và thêm các trang chuyển phần cùng slide phân công. Vì vậy, hãy tìm phần lời nói theo **tiêu đề slide**, không dùng số trang Canva cũ. Các trang chuyển phần chỉ dùng để báo hiệu sang mục mới, không cần đọc lại toàn bộ agenda. Ưu tiên nói hết một ý rồi mới chuyển trang; dừng ngắn sau kết quả chính để người nghe theo kịp. Thời lượng thực tế cần chốt bằng một lượt tập nói. Cuối tài liệu có cách rút gọn khi thời gian hạn chế.

Phần lời nói chính có khoảng 6.000 đơn vị cách nhau bằng khoảng trắng trong tiếng Việt. Nếu nói khoảng 200 đến 240 đơn vị mỗi phút, thời lượng ước tính khoảng **25 đến 30 phút**, chưa gồm trao đổi với Thầy. Đây là ước tính để tập; không phải số từ theo phân tách ngôn ngữ học và không thay thế việc bấm giờ thực tế.

| Phần agenda | Trang PDF và nội dung |
|---|---|
| Mở đầu chung | 1 đến 2 gồm trang bìa và mục lục |
| Problem | 3 gồm câu hỏi nghiên cứu và mục tiêu |
| Literature review | 4 đến 10 gồm bốn hướng nghiên cứu và research gap |
| Progress | 11 đến 22 gồm cách hệ thống hoạt động, kết quả MMLU, ba vòng thử sửa đáp án và kết luận tiến độ |
| Next experiment | 23 đến 26 gồm setting, protocol, giới hạn và nội dung xin ý kiến Thầy |

## Slide 1 Giới thiệu đề tài RepGuard

**Trên slide:** RepGuard Evidence Calibrated Reputation Transfer under Imperfect Feedback in Multi Agent LLM Systems.

**Điểm cần truyền đạt:** Đề tài nghiên cứu cách dùng lịch sử để hỗ trợ chọn agent khi phản hồi đánh giá chưa hoàn toàn đáng tin.

### Lời trình bày

Dạ em chào Thầy. Hôm nay chúng em xin báo cáo phần tổng quan nghiên cứu liên quan và cập nhật tiến độ của đề tài RepGuard.

Đề tài xuất phát từ một quyết định trong hệ thống sử dụng nhiều agent AI: với một nhiệm vụ đang có, hệ thống nên sử dụng agent nào, tin vào kết quả nào, và khi nào cần kiểm tra thêm.

Chúng em muốn dùng lịch sử làm việc của các agent để hỗ trợ quyết định này. Tuy nhiên, lịch sử thường được ghi nhận thông qua một cách đánh giá, và cách đánh giá đó có thể sai hoặc chỉ kiểm tra được một phần của đáp án. Vì vậy, vấn đề cần giải quyết là làm thế nào sử dụng lịch sử khi chính tín hiệu đánh giá lịch sử cũng chưa hoàn hảo.

Trong buổi hôm nay, chúng em sẽ làm rõ cơ sở nghiên cứu của hướng tiếp cận này, những gì đã triển khai và kiểm chứng, cùng những câu hỏi còn cần thực nghiệm tiếp.

### Chuyển slide

Chúng em sẽ trình bày câu hỏi này theo bốn phần sau.

## Slide 2 Bố cục báo cáo

**Trên slide:** Table of Contents.

**Điểm cần truyền đạt:** Người nghe biết mỗi phần sẽ trả lời câu hỏi gì.

### Lời trình bày

Đầu tiên, chúng em xác định cụ thể bài toán và vai trò của lịch sử trong việc chọn agent.

Tiếp theo là literature review. Phần này tập trung vào những hướng nghiên cứu đã giải quyết các thành phần của bài toán, các giả định họ sử dụng, và phần RepGuard còn phải kiểm chứng.

Sau đó, chúng em trình bày kết quả thực nghiệm hiện có để thấy hướng tiếp cận đã được kiểm tra đến đâu và đang vướng ở điểm nào.

Cuối cùng là phép thử đề xuất tiếp theo và những nội dung chúng em muốn xin ý kiến Thầy trước khi triển khai.

### Chuyển slide

Trước hết, chúng em xin xác định rõ câu hỏi nghiên cứu của đề tài.

## Slide 3 Câu hỏi nghiên cứu

**Trên slide:** Research Question.

**Điểm cần truyền đạt:** Phân biệt năng lực agent, bằng chứng lịch sử và độ đáng tin của cách đánh giá.

### Lời trình bày

Trong phạm vi đề tài, một agent là một cấu hình thực hiện nhiệm vụ. Cấu hình này gồm model, cách hướng dẫn model, công cụ và quy trình xử lý. Hai agent có thể dùng cùng một model nhưng khác quy trình; ngược lại, hai model khác nhau vẫn có thể mắc cùng một loại lỗi.

Khi cần chọn giữa các agent, hệ thống có thể dựa vào kết quả làm việc trước đó. Chúng em gọi thông tin được tổng hợp từ lịch sử này là reputation, hay điểm uy tín. Điểm này là một ước lượng về năng lực trong điều kiện đang xét, không bảo đảm rằng đáp án hiện tại sẽ đúng.

Khó khăn là một kết quả từng được đánh giá là đúng có thể thực ra sai. Ngoài ra, lịch sử ở một loại nhiệm vụ chưa chắc phù hợp với nhiệm vụ hiện tại. Vì vậy, khi sử dụng lịch sử, chúng em cần xét cả độ đáng tin của feedback và mức liên quan giữa các nhiệm vụ. Feedback ở đây là tín hiệu đánh giá đáp án.

Câu hỏi nghiên cứu là: sau khi xét hai yếu tố đó, lịch sử có giúp hệ thống chọn agent tốt hơn không? Chúng em đánh giá bằng kết quả cuối cùng ở cùng tổng chi phí, thay vì chỉ xem điểm uy tín có thay đổi hay không.

### Chuyển slide

Để trả lời câu hỏi này, chúng em tổng hợp các nghiên cứu liên quan thành bốn nhóm.

## Slide 4 Bốn hướng nghiên cứu liên quan

**Trên slide:** Four Research Streams.

**Điểm cần truyền đạt:** Literature review tạo cơ sở cho từng quyết định thiết kế của RepGuard.

### Lời trình bày

Nhóm thứ nhất nghiên cứu reputation và niềm tin theo điều kiện nhiệm vụ. Nhóm này giúp trả lời cách tổng hợp lịch sử và cách sử dụng bằng chứng từ những nhiệm vụ có liên quan.

Nhóm thứ hai nghiên cứu độ tin cậy của feedback. Nếu cách chấm có sai lệch, hệ thống cần đo được sai lệch đó trước khi sử dụng kết quả chấm để cập nhật reputation.

Nhóm thứ ba nghiên cứu lựa chọn model và phân bổ ngân sách. Nhóm này giúp xác định quyết định nào cần tối ưu và so sánh với những đối chứng nào.

Nhóm cuối nghiên cứu thực thi chương trình và sửa đáp án. Đây là cơ sở để xây dựng các quy trình tạo kết quả và kiểm tra kết quả trong phần thực nghiệm.

RepGuard liên kết các nhóm này ở bước ra quyết định: bằng chứng thu được có giúp chọn được kết quả tốt hơn với chi phí hợp lý hay không.

### Chuyển slide

Chúng em bắt đầu với thành phần nền tảng nhất, là cách xây dựng reputation từ lịch sử.

## Slide 5 Reputation và niềm tin theo nhiệm vụ

**Trên slide:** Reputation.

**Điểm cần truyền đạt:** Reputation và chuyển giao bằng chứng đã có nền tảng nghiên cứu; vấn đề của đề tài nằm ở cách dùng bằng chứng chưa hoàn hảo.

### Lời trình bày

Một nền tảng cổ điển là Beta Reputation System của Jøsang và Ismail. Phương pháp này tích lũy kết quả thành công và thất bại để mô tả mức độ tin cậy. Khi có thêm quan sát, hệ thống cập nhật cả ước lượng năng lực và mức độ chắc chắn của ước lượng đó.

Trong các hệ LLM, nghiên cứu Credibility Scoring xem xét việc sử dụng đóng góp lịch sử để điều chỉnh trọng số của các agent khi tổng hợp kết quả. Công trình Skill Conditional Trust đi sâu hơn vào việc năng lực của một agent phụ thuộc vào kỹ năng hoặc loại nhiệm vụ đang xét, cùng việc sử dụng bằng chứng giữa các kỹ năng.

Các hướng này cho thấy chúng em không thể coi việc dùng lịch sử hoặc reputation theo nhiệm vụ là ý tưởng mới của đề tài.

Điểm cần xét thêm là chất lượng của quan sát được đưa vào lịch sử. Nếu một đáp án sai được cách chấm ghi nhận là thành công, việc cộng thẳng một lần thành công sẽ làm reputation sai lệch. Cân trọng số theo nhiệm vụ có thể làm lịch sử phù hợp hơn, nhưng vẫn cần xử lý chất lượng của nhãn đánh giá.

Vì vậy, RepGuard xem độ liên quan của lịch sử và độ đáng tin của feedback là hai yếu tố riêng cần kiểm tra.

### Chuyển slide

Từ đây, chúng em chuyển sang nhóm nghiên cứu thứ hai: làm thế nào biết feedback đáng tin đến mức nào.

## Slide 6 Độ tin cậy của feedback

**Trên slide:** Feedback Reliability.

**Điểm cần truyền đạt:** Cần đối chiếu feedback với nhãn chuẩn, và xác suất tốt hơn chưa đủ chứng minh quyết định tốt hơn.

### Lời trình bày

Một cách tạo feedback là sử dụng LLM làm người chấm, thường gọi là LLM as a Judge. Cách này giúp đánh giá nhiều đáp án, nhưng bản thân judge vẫn có sai lệch. Do đó, việc judge chấp nhận một đáp án chưa đủ để coi đáp án đó là đúng.

Trong sơ đồ, proxy feedback là tín hiệu đánh giá có thể thu với chi phí thấp hơn. Gold audit là việc kiểm tra một phần kết quả bằng nhãn chuẩn hoặc cơ chế đối chiếu được chấp nhận trong thí nghiệm. Từ phần được kiểm tra, hệ thống ước lượng độ đáng tin của proxy.

Calibration nghiên cứu xem xác suất dự đoán có phù hợp với tần suất đúng quan sát được hay không. Brier là một thước đo sai số của xác suất; trong cùng bài toán đánh giá, giá trị thấp hơn thể hiện dự đoán xác suất chính xác hơn theo thước đo này.

Prediction Powered Inference kết hợp nhiều dự đoán với một lượng nhãn chuẩn để hiệu chỉnh các ước lượng thống kê. Active Statistical Inference nghiên cứu việc chủ động chọn những quan sát cần lấy nhãn. Hai hướng này cung cấp cơ sở để suy nghĩ về cách sử dụng ngân sách kiểm tra.

Tuy nhiên, xác suất được hiệu chỉnh tốt hơn có thể vẫn giữ nguyên thứ tự các agent. Khi đó, hệ thống vẫn chọn cùng agent và kết quả cuối không thay đổi. Vì thế, chúng em cần đo thêm giá trị của việc hiệu chỉnh ở cấp quyết định.

### Chuyển slide

Để đo giá trị đó, cần xác định rõ cách chọn agent và chi phí của từng lựa chọn.

## Slide 7 Lựa chọn agent và ngân sách

**Trên slide:** Routing.

**Điểm cần truyền đạt:** Phương pháp dùng reputation phải được so với đối chứng phù hợp ở cùng quyền truy cập thông tin và chi phí.

### Lời trình bày

Routing là việc quyết định giao một yêu cầu cho model hoặc agent nào. Đối chứng đơn giản nhất là luôn dùng một agent cố định, được chọn bằng dữ liệu lịch sử hợp lệ.

Nếu hệ thống được phép kiểm tra thêm kết quả, một đối chứng khác là chia đều ngân sách kiểm tra. Sequential Halving là phương pháp phân bổ dần ngân sách cho các ứng viên còn lại sau mỗi vòng loại. Trong bài toán của chúng em, cần xác định cụ thể một lần quan sát hoặc audit tương ứng với chi phí nào để áp dụng đối chứng này.

RouteLLM học cách định tuyến giữa các model. R2 Router xét đồng thời lựa chọn model và ngân sách độ dài đầu ra. Các nghiên cứu này cho thấy chi phí cần được tính cả ở bước xây dựng phương pháp và khi sử dụng phương pháp.

Đối với RepGuard, chúng em cần ghi nhận chi phí thu lịch sử, số nhãn chuẩn đã sử dụng, số lượt gọi model và lượng token. Một phương pháp tạo ra kết quả tốt hơn nhờ được cấp nhiều thông tin hoặc nhiều lượt gọi hơn cần được so với đối chứng có ngân sách tương ứng.

Vì vậy, so sánh công bằng về thông tin và chi phí là một phần của thiết kế nghiên cứu.

### Chuyển slide

Ngoài các nền tảng này, có ba công trình gần đây liên quan trực tiếp hơn đến câu hỏi của RepGuard.

## Slide 8 Các công trình gần nhất

**Trên slide:** Closest Prior Work.

**Điểm cần truyền đạt:** Các ý tưởng audit, chia sẻ lịch sử và đo khả năng cải thiện đều đã có tiền lệ; đóng góp cần được kiểm tra cụ thể hơn.

### Lời trình bày

Công trình đầu tiên nghiên cứu chọn ứng viên tốt nhất khi LLM judge có sai lệch và số lần đánh giá bởi người bị giới hạn. Điểm gần với RepGuard là kết hợp tín hiệu đánh giá chưa hoàn hảo với một ngân sách kiểm tra bằng nhãn chuẩn.

SaveRouter nghiên cứu thu feedback có chọn lọc, chia sẻ thông tin giữa các yêu cầu liên quan và tính cả chi phí giám sát ban đầu. Điều này liên quan trực tiếp đến việc liệu lợi ích từ lịch sử có bù được chi phí xây dựng lịch sử hay không.

RouteGuard nghiên cứu khả năng cải thiện thực sự của routing và việc chứng nhận lợi ích theo các điều kiện thống kê. Liên hệ với đề tài là sự bổ trợ trong tập model đang xét, gọi là pool, chỉ cho biết có tiềm năng lựa chọn; hệ thống còn phải tìm được cách khai thác tiềm năng đó trên dữ liệu phù hợp.

Ba công trình trên đang được dẫn theo các bản preprint đã đối chiếu. Chúng em chưa tái lập chúng trên cùng dữ liệu RepGuard và chưa có bằng chứng vượt chúng.

Do đó, đóng góp cần hướng tới một câu hỏi hẹp, có phép thử và đối chứng cụ thể. Việc thêm audit hoặc sử dụng lịch sử liên quan, tự nó, chưa đủ để xác lập tính mới.

### Chuyển slide

Trước khi chốt câu hỏi đó, còn một phần cần làm rõ là bằng chứng do execution và repair cung cấp.

## Slide 9 Thực thi chương trình và sửa kết quả

**Trên slide:** Execution & Repair.

**Điểm cần truyền đạt:** Chương trình chạy được cung cấp bằng chứng về thực thi, còn tính đúng của nguồn dữ liệu và ý nghĩa phép tính vẫn cần đánh giá.

### Lời trình bày

PAL và Program of Thoughts đưa phần tính toán sang chương trình để thực thi. Thay vì chỉ sinh một kết quả bằng văn bản, model tạo ra các bước tính có thể chạy và kiểm tra.

Self Refine sử dụng feedback để sửa đầu ra qua nhiều lượt. Tuy nhiên, các nghiên cứu về tự sửa suy luận cũng cho thấy khả năng cải thiện phụ thuộc vào chất lượng tín hiệu sửa lỗi. Thêm một lượt tự xem lại chưa bảo đảm sẽ sửa đúng.

Trong thực nghiệm của chúng em, một chương trình có thể chạy thành công nhưng vẫn lấy sai số liệu, chọn sai đại lượng hoặc dùng sai đơn vị. Vì vậy, tỷ lệ thực thi thành công cần được tách khỏi tỷ lệ đáp án đúng.

Ngoài ra, các quy trình cần có quy định rõ về đầu ra nào được chấp nhận và mỗi bước được phép sửa phần nào. Chúng em gọi tập quy định này là output contract. Nếu contract khác nhau giữa các nhánh, chênh lệch điểm có thể đến từ cách chấp nhận chương trình thay vì năng lực sửa lỗi.

Đây là lý do các vòng nghiên cứu sau tập trung kiểm tra cả chương trình, contract và cách chấm trước khi học thêm chính sách lựa chọn.

### Chuyển slide

Tổng hợp các nhóm nghiên cứu trên, chúng em xác định câu hỏi mà RepGuard cần kiểm chứng như sau.

## Slide 10 Khoảng trống cần kiểm chứng

**Trên slide:** Research Gap.

**Điểm cần truyền đạt:** Đây là hướng nghiên cứu đang kiểm tra, chưa phải tuyên bố về một phương pháp đã vượt trội.

### Lời trình bày

Các nghiên cứu trước đã cung cấp nhiều thành phần của bài toán: tích lũy reputation, hiệu chỉnh feedback, phân bổ audit và định tuyến model.

Câu hỏi chúng em muốn kiểm tra là liệu có thể ước lượng độ đúng của agent dựa đồng thời trên feedback, nhiệm vụ và phần kết quả đã được kiểm tra hay không. Phần đã được kiểm tra quan trọng vì mỗi cơ chế verification chỉ xác nhận được một phạm vi nhất định.

Sau khi có ước lượng, bước đánh giá tiếp theo là xem nó có làm thay đổi lựa chọn theo hướng tốt hơn không. Phương pháp cần tạo thêm đáp án đúng hoặc đạt chất lượng tương đương với chi phí thấp hơn khi so với đối chứng được cấp cùng thông tin.

Ở thời điểm hiện tại, chúng em xem đây là câu hỏi nghiên cứu đang cần bằng chứng. Những kết quả sau đây sẽ cho thấy phần nào đã được kiểm tra và vì sao chúng em chưa kết luận phương pháp vượt đối chứng.

### Chuyển slide

Để thấy lịch sử được dùng vào việc gì, chúng em xin đi qua từng bước xử lý của hệ thống.

## Slide 11 Cách hệ thống dùng lịch sử để chọn kết quả

**Trên slide:** Pipeline. Tìm theo tiêu đề này trong Canva nếu thứ tự trang đã thay đổi.

**Điểm cần truyền đạt:** Hệ thống xem agent đã làm được gì trước đây, cách chấm có đáng tin không và lịch sử đó có phù hợp với việc hiện tại không, rồi mới sử dụng điểm uy tín.

### Lời trình bày

Ở slide này, chúng em trình bày cách hệ thống sử dụng kết quả làm việc trước đây của các agent.

Đầu tiên, chúng em lưu lại mỗi agent đã làm nhiệm vụ gì, trả lời ra sao và được đánh giá là đúng hay sai. Những thông tin này tạo thành lịch sử của agent.

Tiếp theo, hệ thống xem cách đánh giá đó đáng tin đến đâu. Việc này dựa trên một phần kết quả đã có nhãn chuẩn để đối chiếu. Nếu cách chấm thường nhầm, hệ thống không xem mọi lần được chấm đúng là một lần làm đúng chắc chắn.

Sau đó, hệ thống xét phần lịch sử nào liên quan đến nhiệm vụ đang cần giải quyết. Kết quả từ cùng loại nhiệm vụ được tính nhiều hơn; kết quả chỉ liên quan một phần được tính ít hơn; phần không liên quan được bỏ qua theo quy tắc hiện tại.

Từ những thông tin đó, hệ thống cập nhật điểm uy tín của từng agent. Điểm này tổng hợp việc agent đã làm tốt đến đâu, sau khi xét cả cách chấm và mức liên quan của lịch sử.

Trong cấu hình tổng hợp đáp án trên MMLU Pro, chúng em dùng điểm này để tăng hoặc giảm trọng số cho đáp án của từng agent. Agent có điểm cao hơn sẽ có ảnh hưởng lớn hơn khi hệ thống chọn đáp án cuối cùng.

Cuối cùng, chúng em đối chiếu đáp án đã chọn với nhãn chuẩn để kiểm tra: sử dụng lịch sử như vậy có giúp trả lời đúng thêm câu nào so với cách đơn giản hơn không, và chi phí tăng bao nhiêu.

Công thức trên slide mô tả cách cộng dồn bằng chứng ở bước cập nhật điểm. Ý chính là kết quả lịch sử không được tính ngang nhau; cách chấm và mức liên quan của nhiệm vụ quyết định mỗi kết quả được tính bao nhiêu.

**Gợi ý trình bày:** Chỉ lần lượt vào các khối trên slide khi nói đến bước tương ứng. Không cần đọc tên từng ký hiệu trong công thức khi trình bày luồng chung. Mạch cần nhớ là ghi lại lịch sử, xét cách chấm, xét độ liên quan, cập nhật điểm, dùng điểm để tổng hợp đáp án, rồi kiểm tra kết quả và chi phí.

### Chuyển slide

Đó là cách hệ thống sử dụng lịch sử. Tiếp theo, chúng em trình bày kết quả trên MMLU Pro để xem cách làm này có giúp chọn đáp án tốt hơn hay chưa.

## Slide 12 Bằng chứng từ MMLU Pro

**Trên slide:** Evidence Base.

**Điểm cần truyền đạt:** Có cải thiện về ước lượng xác suất ở một số điều kiện, nhưng chưa có bằng chứng cải thiện quyết định tương ứng.

### Lời trình bày

Ở phần này, chúng em muốn trả lời câu hỏi: dùng lịch sử làm việc để đánh giá các agent có giúp chọn được đáp án đúng hơn không?

Trước hết, chúng em thử trên MMLU Pro, một bộ câu hỏi trắc nghiệm về kiến thức và suy luận. Chúng em đã thu được 18.064 câu trả lời từ bốn mô hình AI. Một câu hỏi có thể được nhiều mô hình trả lời, nên đây là số lượt trả lời, không phải số câu hỏi khác nhau.

Trên slide, ECRT là cách của chúng em: khi tính điểm uy tín, hệ thống xét cả độ đáng tin của cách chấm và mức liên quan của nhiệm vụ trước đây. FixedBorrow là cách dùng lịch sử để so sánh, với quy tắc cố định và không điều chỉnh độ tin cậy của cách chấm như ECRT.

Trong điều kiện lịch sử có liên quan và 25 phần trăm đánh giá bị cố ý làm nhiễu, ECRT chỉ hơn FixedBorrow 0,02 điểm phần trăm về tỷ lệ trả lời đúng. Mức chênh lệch này rất nhỏ. Khoảng ước lượng 95 phần trăm còn trải từ âm 0,04 đến dương 0,10 điểm phần trăm, tức là dữ liệu vẫn phù hợp với cả khả năng tốt hơn hoặc kém hơn một chút. Vì vậy, chúng em chưa thể nói cách của mình tốt hơn.

Các biểu đồ Brier trên slide đo mức phù hợp giữa xác suất hệ thống dự đoán và kết quả đúng sai thực tế. Ở một số điều kiện, chỉ số này tốt hơn. Tuy nhiên, ước lượng xác suất tốt hơn chưa đồng nghĩa với việc chọn được nhiều đáp án đúng hơn.

Chúng em cũng kiểm tra xem bốn mô hình có giải được những câu khác nhau không. Mô hình tốt nhất đạt 47,76 phần trăm. Nếu được xem đáp án chuẩn trước rồi chọn mô hình trả lời đúng cho từng câu, mức này có thể đạt 68,34 phần trăm. Đây là phép kiểm tra để biết còn cơ hội chọn tốt hơn hay không; khi sử dụng thực tế, hệ thống không được biết trước đáp án.

Như vậy, bốn mô hình có thể bổ sung cho nhau ở một số câu hỏi. Nhưng chỉ dựa vào nhãn môn học thì chúng em chưa chọn được mô hình phù hợp cho từng câu. Theo tiêu chí kiểm tra ở giai đoạn này, cũng mới có một mô hình được xác nhận là có lợi thế ở môn chuyên biệt.

### Chuyển slide

Kết quả này khiến chúng em phải kiểm tra kỹ hơn: điểm uy tín thay đổi thì quyết định cuối cùng có thực sự tốt hơn không?

## Slide 13 Hàm ý cho thiết kế thực nghiệm

**Trên slide:** Current Implications.

**Điểm cần truyền đạt:** Cần đánh giá chuỗi từ ước lượng đến quyết định và outcome, đồng thời kiểm soát điều kiện so sánh.

### Lời trình bày

Từ kết quả vừa rồi, chúng em rút ra ba việc cần kiểm tra trước khi chạy tiếp.

Thứ nhất, điểm uy tín có làm hệ thống chọn khác đi không? Nếu điểm có thay đổi nhưng hệ thống vẫn chọn cùng một đáp án, thì số câu đúng có thể vẫn giữ nguyên.

Thứ hai, các cách được đem ra so sánh phải dùng cùng công cụ, cùng quy định xử lý chương trình và được tính chi phí theo cùng một cách. Nếu một cách được gọi AI nhiều hơn hoặc bị kiểm tra chặt hơn cách còn lại, kết quả sẽ khó cho biết riêng điểm uy tín đóng góp được gì.

Thứ ba, chúng em cần kiểm tra cách chấm đang dùng có đáng tin không. Kết quả đo độ tin cậy ở một loại đánh giá chưa chắc dùng được cho loại đánh giá khác.

Những việc này giúp phép so sánh rõ ràng hơn. Chúng em vẫn phải xem lại cả cách tính điểm uy tín của mình, vì bản thân cách tính đó cũng có thể chưa tốt.

Vì vậy, ở các vòng tiếp theo, chúng em kiểm tra từ một câu hỏi cơ bản: các cách tạo đáp án có tạo ra những câu đúng khác nhau để hệ thống lựa chọn hay không?

### Chuyển slide

Vòng đầu tiên sẽ kiểm tra điều này: nếu thử nhiều cách giải cho cùng một bài, chúng em có thu được thêm đáp án đúng không?

## Slide 14 Vòng 1 và khả năng cải thiện bằng lựa chọn

**Trên slide:** Cycle 1 No Selection Headroom.

**Điểm cần truyền đạt:** Selector không thể chọn ra một đáp án đúng chưa tồn tại trong tập đầu ra được phép chọn.

### Lời trình bày

Ở vòng đầu tiên, ngày 18 tháng 10, chúng em thu thêm tổng cộng 160 lượt trả lời từ AI cho các phép thử.

Phần chính gồm 24 trường hợp. Với mỗi trường hợp, chúng em thử bốn cách: trả lời ngay; tự xem lại câu trả lời; sửa dựa trên bằng chứng; và lập kế hoạch rồi trả lời. Cả bốn cách đều phải viết phép tính theo một dạng có cấu trúc, được ghi là DSL trên slide.

Kết quả là mỗi cách đều đúng 6 trên 24. Khi kiểm tra từng trường hợp, chúng em thấy chúng cũng chỉ giải đúng cùng sáu trường hợp đó. Tức là những trường hợp cách này làm sai thì ba cách còn lại cũng chưa làm đúng.

Vì vậy, một bộ chọn dù chọn khéo đến đâu cũng chỉ đạt tối đa 6 trên 24, nếu chỉ được chọn trong bốn kết quả đã có. Cụm “No Selection Headroom” trên slide nói về việc chưa còn cơ hội tăng số câu đúng bằng cách chọn giữa bốn cách này.

Chúng em còn thử riêng Program of Thoughts, viết tắt là PoT. Với cách này, AI viết một chương trình tính toán, sau đó hệ thống chạy chương trình để lấy kết quả. Cách này đạt 14 trên 24 theo quy tắc chấm ban đầu và nằm ngoài nhóm bốn cách vừa nêu.

Chênh lệch đó khiến chúng em kiểm tra lại: liệu cách yêu cầu AI viết chương trình và cách hệ thống lấy kết quả từ chương trình có đang ảnh hưởng lớn đến điểm số không?

### Chuyển slide

Khi kiểm tra lại các chương trình đã lưu, chúng em thấy cách lấy kết quả từ chương trình đúng là có ảnh hưởng đến điểm số.

## Slide 15 Chẩn đoán cách đọc đầu ra ở vòng 1

**Trên slide:** Cycle 1 Readout Diagnostics.

**Điểm cần truyền đạt:** Thay đổi cách đọc output có thể làm đổi điểm dù model không sinh đáp án mới.

### Lời trình bày

Ở slide này, chúng em giữ nguyên những chương trình AI đã tạo và chỉ kiểm tra lại cách hệ thống lấy kết quả để chấm. Trên slide, phần này được gọi là readout.

Với quy tắc ban đầu, cách PoT đạt 14 trên 24. Sau khi xử lý lại vấn đề định dạng, điểm là 16 trên 24. Khi thống nhất thêm cách lấy kết quả, điểm đạt 17 trên 24.

Điều cần phân biệt là AI không giải thêm lần nào để tạo ra các mức tăng này. Cùng một chương trình đã lưu, nhưng phần mềm lấy kết quả khác nhau thì điểm chấm cũng có thể khác nhau.

Khi cho cách dùng lịch sử và cách PoT trả lời trực tiếp cùng dùng quy tắc lấy kết quả tương ứng, cả hai đều đạt 17 trên 24. Trong khi đó, chỉ số dùng để ước tính lượng tính toán của cách dùng lịch sử cao hơn khoảng 13,6 phần trăm. Đây là chỉ số ước tính, không phải số tiền thực tế đã thanh toán.

Vì vậy, ở phép thử này, chúng em chưa thấy dùng lịch sử giúp trả lời đúng thêm. Phần tăng từ 14 lên 17 giúp phát hiện vấn đề ở phần mềm xử lý kết quả; chúng em không tính phần tăng đó thành hiệu quả của điểm uy tín.

### Chuyển slide

Sau khi hiểu vấn đề này, chúng em chuyển sang vòng hai để thử thêm việc ghép các phần sửa và thay đổi mô hình AI.

## Slide 16 Hai phép thăm dò riêng ở vòng 2

**Trên slide:** Cycle 2 Separate Probes.

**Điểm cần truyền đạt:** Thêm bước ghép hoặc đổi model chưa tạo được lợi ích trong các cohort đã thử; hai cohort không được gộp thành một kết luận nhân quả.

### Lời trình bày

Ở vòng hai, ngày 19 tháng 10, chúng em thu thêm 136 lượt trả lời cho hai phép kiểm tra riêng.

Phép thứ nhất gồm 24 trường hợp, nhằm xem ghép hai phần sửa có giúp trả lời tốt hơn không. Cách PoT trả lời trực tiếp và các cách tự xem lại đều đạt 17 câu đúng. Nhưng khi ghép hai phần sửa, kết quả còn 16 câu đúng.

Cụ thể, cách ghép không sửa đúng thêm câu nào mà cách trả lời trực tiếp đã làm sai. Nó còn làm sai một câu trước đó đã đúng. Trên slide, rescue chỉ số câu được sửa từ sai thành đúng; harm chỉ số câu bị đổi từ đúng thành sai. Hai số này giúp chúng em thấy rõ việc sửa có thực sự có ích không.

Phép thứ hai dùng một nhóm riêng gồm 16 trường hợp để so sánh các mô hình AI. Hai cấu hình 8B và 14B đều đúng 11 câu, và cũng đúng cùng một nhóm câu. Trong nhóm này, đổi giữa hai cấu hình chưa tạo thêm câu đúng để lựa chọn. Với cấu hình 27B, kết quả còn thay đổi theo việc bật chế độ suy nghĩ và độ dài câu trả lời được phép tạo.

Hai phép kiểm tra dùng hai nhóm trường hợp khác nhau. Vì vậy, chúng em báo cáo riêng, chưa kết luận rằng việc các mô hình sai giống nhau là nguyên nhân khiến cách ghép sửa thất bại.

Kết quả hiện tại chưa cho thấy những cấu hình này đủ tốt để tiếp tục xây dựng cách chọn dựa trên lịch sử.

### Chuyển slide

Sang vòng ba, chúng em thử giới hạn rõ mỗi lần sửa được phép thay đổi phần nào, để xem từng loại sửa có tác dụng ra sao.

## Slide 17 Kết quả chính thức của các nhánh sửa có phạm vi

**Trên slide:** Cycle 3 Primary Scoped Results.

**Điểm cần truyền đạt:** Các nhánh sửa có phạm vi chưa vượt đối chứng PoT, và contract đang ảnh hưởng đến kết quả.

### Lời trình bày

Ở vòng ba, chúng em dùng 24 trường hợp tính toán từ bảng và văn bản trong bộ dữ liệu TAT QA. Các trường hợp này lấy từ phần dữ liệu dành cho phát triển, được ghi là TRAIN. Đây chưa phải kết quả đánh giá cuối cùng trên tập kiểm tra chính thức.

Chúng em so sánh cách PoT thông thường với bốn cách có quy định chặt hơn về phần được phép thay đổi. KEEP giữ chương trình nhưng phải tuân theo quy định về nguồn số liệu. E chỉ tập trung sửa bằng chứng hoặc nguồn số liệu. O chỉ tập trung sửa phép tính và đơn vị. EO kết hợp hai phần sửa này.

Khi chấm bằng công cụ gốc của TAT QA, PoT thông thường đúng 19 trên 24. Bốn cách KEEP, E, O và EO lần lượt đúng 15, 15, 16 và 15.

Ngay cả khi xem trước đáp án chuẩn rồi chọn cách trả lời đúng cho từng trường hợp trong bốn cách bị giới hạn, cũng chỉ đạt 16 trên 24. Như vậy, nhóm này vẫn kém cách PoT thông thường. Chúng em chưa tiếp tục huấn luyện bộ chọn dựa trên lịch sử với những kết quả này.

Khi xem lại, chúng em phát hiện phần kiểm tra quy định chương trình, được gọi là contract trên slide, đã từ chối một số cách viết phép tính trung bình dù giá trị tính ra là hợp lệ. Chúng em cần kiểm tra vấn đề đó, nhưng vẫn giữ nguyên điểm của lần đánh giá ban đầu để báo cáo rõ ràng.

### Chuyển slide

Tiếp theo, chúng em thử cho AI tự xem lại mà không bị giới hạn chỉ được sửa một phần, để kiểm tra xem kết quả có tốt hơn không.

## Slide 18 Thêm lượt gọi và model family ở vòng 3

**Trên slide:** Cycle 3 Unrestricted Extra Calls.

**Điểm cần truyền đạt:** Tập đầu ra mở rộng vẫn không có oracle vượt nhánh cố định tốt nhất trong pilot này.

### Lời trình bày

Ở phần bổ sung này, chúng em thực hiện thêm 120 lượt gọi AI. Các cách tự xem lại không bị giới hạn phạm vi sửa như nhóm ở slide trước.

Với Qwen, trả lời ban đầu đúng 19 trên 24; tự xem lại lần một và lần hai đều đạt 20 trên 24. Với Gemma, cả ba cách đều đạt 16 trên 24.

Sau đó, chúng em gộp kết quả của cả hai dòng mô hình và kiểm tra từng trường hợp. Tổng cộng vẫn chỉ có 20 trường hợp mà ít nhất một cách làm đúng. Tức là cách Qwen tự xem lại đã giải được toàn bộ những trường hợp đúng có trong nhóm kết quả này. Gemma chưa bổ sung thêm trường hợp đúng nào ngoài số đó.

Vì vậy, nếu chỉ chọn giữa các kết quả đã có, bộ chọn dựa trên lịch sử cũng chưa có cơ hội vượt mức 20 trên 24 của cách tốt nhất đang có.

Phép kiểm tra bổ sung này được làm sau khi chúng em đã xem các trường hợp. Nó giúp hiểu thêm kết quả hiện tại, nhưng chưa thay cho một lần đánh giá mới trên dữ liệu độc lập. Kết luận cũng chỉ áp dụng cho những cấu hình Qwen và Gemma đã thử.

### Chuyển slide

Bên cạnh việc thử thêm cách trả lời, chúng em cũng kiểm tra lại phần mềm xử lý kết quả. Slide tiếp theo tách riêng những thay đổi do phần mềm này.

## Slide 19 Các chẩn đoán readout sau thực nghiệm

**Trên slide:** Post hoc Readout Diagnostics.

**Điểm cần truyền đạt:** Các chẩn đoán giải thích điểm số nhưng không được gộp thành mức tăng của reputation.

### Lời trình bày

Slide này trình bày các kiểm tra sau khi thực nghiệm đã kết thúc. Chúng em muốn biết điểm số thay đổi vì AI giải tốt hơn, hay vì phần mềm đọc và kiểm tra chương trình khác đi.

Kiểm tra thứ nhất liên quan đến cách viết các số dùng để đếm trong phép tính. Sau khi thống nhất cách xử lý, các cách sửa có giới hạn tương ứng đều đạt 20 trên 24 khi chấm lại chương trình đã lưu. Như vậy, quy định kiểm tra chương trình trước đó có ảnh hưởng đáng kể đến điểm.

Kiểm tra thứ hai xem lại cách lấy kết quả và thông tin đi kèm chương trình ở nhóm không giới hạn phạm vi sửa. Theo cách đọc thống nhất này, cả ba cách của Qwen đạt 20 trên 24; cả ba cách của Gemma đạt 18 trên 24. Đây là kiểm tra riêng, khác với kiểm tra cách viết số đếm vừa nói.

Kiểm tra thứ ba sửa cách hệ thống xử lý khi chỉ một phần đề xuất sửa hợp lệ. Giữ được phần hợp lệ đó giúp cách EO tăng từ 15 lên 16 trên 24.

Các mức tăng này đều đến từ việc xử lý lại chương trình đã lưu sau khi chúng em đã xem kết quả. Chúng giúp tìm lỗi hoặc điểm chưa hợp lý trong phần mềm. Chúng em giữ riêng những số này với kết quả ban đầu và không xem đây là bằng chứng rằng điểm uy tín đã giúp AI trả lời tốt hơn.

### Chuyển slide

Từ các kết quả vừa trình bày, chúng em tổng hợp lại điều gì đã biết và điều gì vẫn chưa thể kết luận.

## Slide 20 Phạm vi kết luận từ các thực nghiệm

**Trên slide:** Evidence Limits.

**Điểm cần truyền đạt:** Kết quả chỉ ra các điều kiện cần kiểm soát, chưa xác định một nguyên nhân duy nhất cho mọi thất bại.

### Lời trình bày

Đến thời điểm hiện tại, chúng em có ba nhận xét chính.

Thứ nhất, ở MMLU Pro, các mô hình có thể giải được những câu khác nhau. Nhưng chỉ nhìn vào môn học thì chúng em chưa chọn được mô hình tốt nhất cho từng câu.

Thứ hai, trong một số phép thử sửa đáp án, các cách được đem ra chọn chưa tạo thêm câu đúng ngoài cách tốt nhất đang có. Khi không có thêm đáp án đúng trong nhóm kết quả, chỉ thay đổi cách chọn sẽ chưa giúp tăng số câu đúng.

Thứ ba, cách kiểm tra chương trình và cách lấy kết quả có thể làm điểm số thay đổi đáng kể. Chúng em cần thống nhất những phần này để biết mức tăng nào thực sự đến từ phương pháp đang nghiên cứu.

Các nhận xét đó giúp chúng em điều chỉnh hướng thực nghiệm. Chúng chưa đủ để kết luận dùng điểm uy tín luôn không hiệu quả, cũng chưa chứng minh nguyên nhân chỉ nằm ở dữ liệu hay phần mềm. Cách tính điểm của chúng em vẫn cần được kiểm tra tiếp.

Phạm vi kết luận hiện tại chỉ là các bộ dữ liệu, các mô hình và các cấu hình mà nhóm đã thử.

### Chuyển slide

Đó là những gì chúng em rút ra từ thực nghiệm. Về phần công việc đã hoàn thành, tiến độ hiện tại như sau.

## Slide 21 Tiến độ đã kiểm chứng

**Trên slide:** Verified Progress.

**Điểm cần truyền đạt:** Dự án đã có dữ liệu và quy trình kiểm chứng cụ thể, trong khi câu hỏi hiệu quả phương pháp vẫn còn mở.

### Lời trình bày

Đến hiện tại, nhóm đã làm được ba phần chính.

Về dữ liệu, chúng em đã thu được 18.064 lượt trả lời từ AI ở giai đoạn MMLU Pro. Ba vòng thử sửa đáp án trong các ngày 18, 19 và 20 tháng 10 thu thêm lần lượt 160, 136 và 264 lượt, tổng cộng 560 lượt trả lời mới. Vì một trường hợp được thử bằng nhiều cách, 560 lượt này không phải 560 bài khác nhau.

Về kiểm tra kết quả, chúng em đã dùng lại công cụ chấm gốc của TAT QA và tính lại được các điểm đã báo cáo. Hai lượt rà soát ở vòng ba cũng kiểm tra lại được câu trả lời đã lưu, nguồn số liệu và việc chạy chương trình. Điều này giúp chúng em đối chiếu từng kết quả với dữ liệu gốc.

Về phần mềm, ở lần kiểm tra đã ghi nhận trên macOS, 308 bài kiểm tra tự động chạy đạt; một bài chưa chạy vì môi trường thiếu thư viện Torch. Các kiểm tra này giúp phát hiện lỗi phần mềm, nhưng chưa chứng minh phương pháp nghiên cứu đạt hiệu quả.

Như vậy, nhóm đã có quy trình thu câu trả lời, lưu lại dữ liệu, chạy chương trình và kiểm tra kết quả; đồng thời đã hoàn thành những phép thử để xác định vấn đề cần xử lý tiếp. Phần còn cần chứng minh là dùng lịch sử và điểm uy tín có giúp tốt hơn các cách đơn giản đang được so sánh hay không.

### Chuyển slide

Để kết luận về câu hỏi đó, chúng em xin nhắc lại ba kết quả quan trọng nhất.

## Slide 22 Kết quả chính cần giữ khi kết luận

**Trên slide:** Main Evidence.

**Điểm cần truyền đạt:** Chưa xác nhận lợi ích tăng thêm của reputation trong các setting đã thử.

### Lời trình bày

Kết quả thứ nhất nằm ở MMLU Pro. Khi dùng lịch sử có liên quan và thêm 25 phần trăm nhiễu vào đánh giá, cách ECRT chỉ hơn FixedBorrow 0,02 điểm phần trăm. Dữ liệu hiện tại chưa đủ để khẳng định mức chênh lệch này là một cải thiện đáng tin cậy.

Kết quả thứ hai nằm ở vòng một. Khi thống nhất cách lấy kết quả từ chương trình, cách dùng lịch sử và cách PoT trả lời trực tiếp cùng đúng 17 trên 24. Nhưng chỉ số ước tính lượng tính toán của cách dùng lịch sử cao hơn 13,6 phần trăm.

Kết quả thứ ba nằm ở vòng ba. Trong nhóm kết quả không bị giới hạn phạm vi sửa, tổng số trường hợp có ít nhất một đáp án đúng là 20 trên 24. Cách tốt nhất đang có cũng đã đạt mức đó. Vì vậy, chỉ chọn giữa những kết quả này thì chưa thể có thêm câu đúng.

Ba phép thử được đánh giá riêng, nhưng đều dẫn đến kết luận hiện tại: chúng em chưa chứng minh được dùng điểm uy tín giúp tăng kết quả so với cách so sánh tốt đã có.

Vì vậy, trước lần thực nghiệm tiếp theo, chúng em sẽ kiểm tra hai điều. Một là kết quả kiểm tra có cung cấp thông tin hữu ích để đánh giá câu trả lời không. Hai là các mô hình hoặc các cách giải có tạo ra những đáp án đúng khác nhau để hệ thống lựa chọn không. Khi có hai điều này, chúng em mới có cơ sở rõ hơn để kiểm tra vai trò của điểm uy tín.

### Chuyển slide

Để kiểm tra tiếp, chúng em đề xuất bài toán AI viết chương trình, với hai mức kiểm thử. Em xin trình bày cách thử này ở phần tiếp theo.

## Slide 23 Phép thử đề xuất với nested tests

**Trên slide:** Next Experiment.

**Điểm cần truyền đạt:** Basic pass chỉ xác nhận một phần yêu cầu; cần đo xem lịch sử và audit có giúp dự báo phần chưa được kiểm tra hay không.

### Lời trình bày

Trong setting này, một chương trình được kiểm tra trước bằng bộ test cơ bản và có thể được kiểm tra thêm bằng bộ test mở rộng. EvalPlus là nền tảng liên quan vì đã nghiên cứu việc mở rộng test để phát hiện những lỗi mà bộ test nhỏ bỏ sót.

Chúng em ký hiệu B là kết quả pass toàn bộ basic tests, E là pass toàn bộ extended tests, và F là đồng thời pass cả hai, tức pass bộ test đầy đủ hay full suite. Do F được định nghĩa là B và E, nếu B bằng không thì F cũng bằng không. Còn khi B bằng một, kết quả của phần mở rộng vẫn chưa biết nếu chưa chạy nó.

Ở các chương trình đã pass basic, câu hỏi là xác suất pass toàn bộ có phụ thuộc vào agent và loại nhiệm vụ hay không. Nếu có, lịch sử và một ngân sách audit có thể hỗ trợ quyết định chọn chương trình hoặc kiểm tra thêm. Khả năng này phải được đo trước bằng một đợt thử nhỏ ban đầu, gọi là pilot.

Trạng thái hiện tại mới là chuẩn bị 32 task, với 96 basic inputs và 3.397 extended inputs. Chưa có model call hoặc program execution trong đợt thử này.

Đích đánh giá là pass bộ test đã quy định. Điều đó cung cấp một outcome rõ để đo, nhưng vẫn không phải chứng minh chương trình đúng trên mọi input có thể có.

### Chuyển slide

Để phép thử này trả lời đúng câu hỏi nghiên cứu, chúng em đề xuất quy trình đánh giá theo các bước sau.

## Slide 24 Kế hoạch đánh giá và điều kiện dừng

**Trên slide:** Evaluation Plan.

**Điểm cần truyền đạt:** Kiểm tra tín hiệu và headroom trước khi học policy, sau đó so sánh ở cùng điều kiện.

### Lời trình bày

Trước khi thu đáp án mới, chúng em cần kiểm tra môi trường execution, timeout và bộ test bằng các chương trình chuẩn.

Trong pilot, phép đo đầu tiên là trong các chương trình pass basic có bao nhiêu chương trình vẫn fail full suite. Phép đo thứ hai là oracle của pool có vượt agent cố định tốt nhất hay không. Hai phép đo này cho biết feedback đang bỏ sót điều gì và liệu lựa chọn có thể tạo thêm lợi ích.

Tiếp theo là chia dữ liệu theo task và kiểm tra overlap với lịch sử đã sử dụng. Quan hệ với tập MBPP200 hiện vẫn cần đối chiếu, nên chúng em chưa coi bộ chuẩn bị này là một split xác nhận độc lập.

Khi đủ điều kiện tiếp tục, các đối chứng gồm best fixed, chọn theo raw basic pass, chia đều audit và Sequential Halving. Phương pháp và đối chứng cần có cùng quyền dùng feedback, công cụ và tổng ngân sách. Một bộ chọn học từ cùng thông tin cũng cần được xét để kiểm tra giá trị tăng thêm của reputation.

Kết quả sẽ báo tỷ lệ thành công, rescue, harm, số nhãn audit và chi phí, kèm khoảng tin cậy theo đơn vị lấy mẫu phù hợp.

Nếu pilot không có khả năng cải thiện bằng lựa chọn, chúng em sẽ dừng việc học selector trên tập đầu ra đó. Các ngưỡng tiếp tục và dừng cụ thể cần được chốt trước khi thu thêm đáp án model.

### Chuyển slide

Khi đọc cả kết quả hiện tại và kế hoạch tiếp theo, chúng em cũng cần giữ rõ các giới hạn sau.

## Slide 25 Giới hạn của bằng chứng hiện tại

**Trên slide:** Limitations.

**Điểm cần truyền đạt:** Cỡ mẫu nhỏ và chẩn đoán hậu kiểm giới hạn mức chắc chắn của kết luận.

### Lời trình bày

Giới hạn đầu tiên là các repair pilot còn nhỏ. 24 context chưa đương nhiên là 24 report độc lập. Nếu nhiều quan sát có chung nguồn, việc tính độ bất định cần xét quan hệ giữa chúng.

Giới hạn thứ hai là các readout đã được kiểm tra sau khi xem kết quả. Chúng giúp chẩn đoán, nhưng cần được khóa lại và kiểm tra trên dữ liệu mới trước khi dùng làm bằng chứng xác nhận.

Ngoài ra, có bốn trường hợp nguồn hoặc annotation đang được đánh dấu để người đánh giá phân xử. Chúng em chưa tự thay nhãn chuẩn và vẫn giữ điểm primary.

Về harm, kể cả khi quan sát không có harm trong 24 lần thử, ta chưa thể kết luận tỷ lệ harm thực là không. Với giả định các quan sát Bernoulli độc lập, cận trên một phía 95 phần trăm vẫn khoảng 11,73 phần trăm. Nếu các context có phụ thuộc thì còn phải xử lý điều kiện đó khi suy luận.

Vì vậy, kết quả hiện tại phù hợp để giới hạn claim và thiết kế bước tiếp theo. Để đưa ra kết luận mạnh hơn, chúng em cần dữ liệu mới và protocol được khóa trước.

### Chuyển slide

Từ những kết quả và giới hạn này, chúng em xin ý kiến Thầy về phạm vi của mốc nghiên cứu tiếp theo.

## Slide 26 Nội dung xin ý kiến Thầy và kết thúc

**Trên slide:** Discussion with Supervisor.

**Điểm cần truyền đạt:** Chốt một mốc tiếp theo có thể kiểm chứng, với phạm vi và tiêu chí rõ ràng.

### Lời trình bày

Dạ, qua phần literature review và các thực nghiệm, chúng em đã xác định rõ hơn những thành phần đã có tiền lệ, các đối chứng cần thiết và những điều kiện phải kiểm tra trước khi đánh giá reputation.

Hiện tại, chúng em đã có hạ tầng và các kết quả development, nhưng chưa xác nhận được lợi ích tăng thêm của reputation trước đối chứng mạnh trong những setting đã thử.

Chúng em xin ý kiến Thầy trước hết về outcome chính và phạm vi dataset của phép thử tiếp theo. Sau đó là ngân sách pilot và cách chia task để hạn chế overlap với lịch sử đã dùng. Chúng em cũng muốn thống nhất tiêu chí tiếp tục hoặc dừng trước khi thu thêm đáp án.

Mục tiêu gần nhất là có bằng chứng cho thấy feedback và pool đủ điều kiện để một quyết định lựa chọn tạo ra cải thiện đo được. Khi đạt mốc đó, chúng em mới kiểm tra phần đóng góp của chính sách reputation bằng các đối chứng công bằng.

Dạ, chúng em xin kết thúc phần trình bày tại đây và mong nhận được góp ý của Thầy.

**Gợi ý trình bày:** Sau câu kết, dừng lại để Thầy phản hồi. Không tiếp tục đọc lại danh sách công việc.

## Phân công công việc tiếp theo

Đây là phân công đề xuất cho giai đoạn pilot tiếp theo, để trình bày ở phần Next experiment.

**Tín**

- Hoàn thiện runner basic và extended tests, kiểm tra chương trình chuẩn, timeout và log kết quả.
- Triển khai các baseline với cùng thông tin và ngân sách.
- Chạy pilot sau khi chốt protocol và lưu kết quả cùng chi phí.

**Trung**

- Rà 32 task, kiểm tra trùng MBPP200 và đề xuất chia dữ liệu.
- Hoàn thiện bảng so sánh literature và câu hỏi cần kiểm chứng.
- Phân tích reliability, oracle headroom, rescue và harm; làm bảng và biểu đồ kết quả.

**Cả hai**

- Chốt dataset, ngân sách và điều kiện tiếp tục hoặc dừng với Thầy; kiểm tra chéo kết quả trước báo cáo tiếp theo.

### Lời nói cho slide phân công mới

Về phân công tiếp theo, chúng em dự kiến Tín phụ trách phần chạy chương trình, các baseline và thu kết quả pilot. Trung phụ trách rà dữ liệu, hoàn thiện đối chiếu literature và phân tích kết quả. Cả hai sẽ cùng thống nhất protocol, ngân sách và tiêu chí tiếp tục hoặc dừng với Thầy trước khi chạy đợt mới, rồi kiểm tra chéo số liệu trước khi báo cáo.

### Ranh giới các phần trên Canva

Dùng bảng phạm vi bốn phần ở đầu tài liệu để đối chiếu với bản PDF 26 trang. Khi trình bày trên Canva đã được chỉnh thứ tự, tìm theo tiêu đề. Slide phân công đã được chèn ở cuối deck sau khi duyệt mẫu; dùng đoạn lời nói phân công trong phụ lục này khi chuyển sang trang đó.

[Bản rà soát agenda và phân công ở thời điểm đối chiếu trước đó](PHAN_CONG_VA_REVIEW_AGENDA.md). Các số trang Canva trong bản rà soát đó là mốc lịch sử trước những lần chỉnh thứ tự tiếp theo.

## Cách rút gọn khi thời gian hạn chế

Giữ đầy đủ slide 3, 6, 10, 11, 12, 22, 23 và 26 vì đây là các trang xác định bài toán, cách làm và kết luận. Các trang literature còn lại có thể nêu vấn đề chính cùng liên hệ với RepGuard, không đọc tên từng công trình. Khi đi qua slide 14 đến 19, giữ một kết quả quyết định cho mỗi trang thay vì đọc toàn bảng.

Nếu Thầy yêu cầu đi nhanh phần các vòng thử, có thể nói ngắn theo mạch sau, vẫn chuyển qua các slide tương ứng:

“Ở vòng một, bốn cách giải đều chỉ đúng cùng 6 trên 24 trường hợp. Vì vậy, chọn giữa chúng cũng chưa có thêm câu đúng. Khi thống nhất cách lấy kết quả từ chương trình, cách dùng lịch sử và cách PoT trả lời trực tiếp cùng đạt 17 trên 24; cách dùng lịch sử có chỉ số ước tính lượng tính toán cao hơn 13,6 phần trăm. Ở vòng hai, ghép các phần sửa chưa giúp tốt hơn. Việc đổi mô hình được kiểm tra trên một nhóm dữ liệu riêng, nên chúng em báo cáo riêng. Ở vòng ba, các cách bị giới hạn phần được sửa vẫn kém PoT thông thường. Khi thử thêm cách tự xem lại và một dòng mô hình khác, tổng số trường hợp có ít nhất một đáp án đúng là 20 trên 24; cách tốt nhất đã có cũng đạt mức đó. Nhóm cũng phát hiện một số vấn đề khi phần mềm đọc kết quả. Phần điểm tăng do xử lý lại được báo cáo riêng, chưa được tính là hiệu quả của điểm uy tín.”

Sau đoạn này, tiếp tục slide 20 để trình bày giới hạn và kế hoạch. Khi nói ngắn, vẫn nêu rõ kết quả chỉ áp dụng cho nhóm dữ liệu đã thử; những kiểm tra được làm sau khi xem kết quả chưa thay cho đánh giá trên dữ liệu mới.

## Những thuật ngữ cần nói thống nhất

| Thuật ngữ trên slide | Cách giải thích bằng lời |
|---|---|
| Agent | Một cấu hình model và quy trình thực hiện nhiệm vụ |
| Reputation | Bằng chứng tổng hợp từ lịch sử để ước lượng năng lực trong điều kiện đang xét |
| Feedback | Tín hiệu đánh giá một đáp án hoặc một lần thực hiện |
| Gold audit | Kiểm tra một phần kết quả bằng nhãn chuẩn hoặc cơ chế đối chiếu đã quy định |
| Calibration | Mức phù hợp giữa xác suất dự đoán và tần suất đúng quan sát được |
| Routing | Quyết định giao yêu cầu cho agent hoặc model nào |
| Output contract | Quy định về cấu trúc đầu ra được chấp nhận và phạm vi được phép sửa |
| Readout | Quy tắc đọc kết quả từ output hoặc chương trình đã sinh |
| Oracle union | Số trường hợp ít nhất một nhánh trong pool trả lời đúng, được xác định nhờ biết nhãn chuẩn |
| Best fixed | Một nhánh cố định tốt nhất trong phép so sánh đang xét; khi triển khai phải chọn bằng dữ liệu được phép dùng |
| Selection headroom | Khoảng còn có thể tăng tỷ lệ đúng bằng việc chọn giữa các output trong pool đang xét |
| Rescue và harm | Sửa được câu đối chứng sai, và làm sai câu đối chứng đúng, trên cùng trường hợp |
| Primary và post hoc | Kết quả theo cách đánh giá chính thức, và phân tích bổ sung sau khi xem kết quả |
| Compute proxy | Chỉ số thay thế cho chi phí tính toán, không tự tương đương tiền hoặc thời gian chạy thực |

## Các điểm cần trả lời chính xác nếu được hỏi thêm

**Về công thức ở slide 11:** Đây là cập nhật Beta với bằng chứng mềm có trọng số trong implementation; chưa coi là posterior Bayes chính xác cho mọi cơ chế noise. Lower bound hiện có dùng xấp xỉ chuẩn, không phải quantile Beta chính xác hay bảo đảm an toàn.

**Về lựa chọn và tổng hợp:** Kết luận “không có headroom” áp dụng cho việc chọn giữa các output cố định đang có. Một hệ sinh đáp án mới hoặc ghép chương trình mới là một can thiệp khác, cần tính chi phí và đánh giá riêng.

**Về audit và đối chứng:** Method không được nhìn nhãn full suite trước khi quyết định audit rồi vẫn tính chi phí như chưa dùng nhãn đó. Chi phí thu history và supervision ban đầu cũng cần được ghi nhận.

**Về tỷ lệ basic pass sai:** Nếu hỏi “trong các trường hợp pass basic có bao nhiêu trường hợp fail full suite”, mẫu số là số basic pass, tương ứng P(F=0 | B=1). Đại lượng này khác P(B=1 | F=0) và khác tần suất đồng thời B=1, F=0.

**Về mức độ đã hoàn thành:** Test suite và audit giúp kiểm tra phần mềm, nguồn và tính tái lập của điểm; không thay thế đánh giá ngữ nghĩa của từng đáp án hoặc bằng chứng về hiệu quả phương pháp.

## Tài liệu đối chiếu khi tập nói

- [Deck Canva đang dùng](https://www.canva.com/design/DAHZNqV57vA/_lRn_fiY1M11YCo8PHAhlg/edit)
- [PDF 26 slide](../../../output/pdf/RepGuard_Literature_Review_Progress_2026-10-28.pdf)
- [Review và đính chính báo cáo tuần](CANVA_REVIEW_VA_DINH_CHINH.md)
- [Literature review chi tiết và bằng chứng tiến độ](REPGUARD_LITERATURE_REVIEW_VA_BAO_CAO_TIEN_DO.md)
- [Danh mục 49 nguồn sơ cấp](references.json)

Phần script diễn giải các nghiên cứu đã được đối chiếu trong bản literature review, không phải nội dung trích nguyên văn từ paper. Bản này bám theo deck đã hoàn thiện cho ngày 28 tháng 10; nếu thay số liệu hoặc thứ tự slide, cần cập nhật phần lời nói tương ứng.
