# Nghiên cứu sâu các công thức Credibility, Skill-Conditioned Reputation, Judge Calibration, Beta/Bayesian và Calibration Metrics cho RepGuard/ECRT

## Bản đồ công thức và kết luận quan trọng

Bản proposal RepGuard hiện tại của bạn đã đi đúng hướng khi tách lịch sử thành ba đại lượng $p_t$ — xác suất episode lịch sử thực sự đúng, $m_t$ — khối lượng/độ mạnh bằng chứng, và $\tau_t$ — mức độ chuyển giao sang task hiện tại, rồi đưa chúng vào cập nhật Beta. Sau khi đối chiếu trực tiếp các paper gốc, tôi khuyên giữ cấu trúc đó, nhưng có một điểm toán học rất quan trọng cần sửa cách diễn giải: cập nhật

$$
\alpha\leftarrow \alpha+m p,\qquad
\beta\leftarrow\beta+m(1-p)
$$

với $p\in(0,1)$ **không phải, nói chung, posterior Beta chính xác của mô hình Bayesian có feedback nhiễu**. Nó là một phép cập nhật fractional/expected pseudo-count hoặc một phép xấp xỉ posterior. Phần dưới tôi sẽ chứng minh điều này và chỉ ra cách viết paper sao cho chính xác về mặt xác suất.

Bức tranh tổng thể của các nguồn chính như sau:

| Thành phần | Công thức cốt lõi | Nguồn | Điều RepGuard nên lấy |
|---|---|---|---|
| Historical credibility | $CrS_t^{(i)}=CrS_{t-1}^{(i)}(1+\eta CSc_t^{(i)}r_t)$ | Ebrahimi et al. 2025 | Baseline cập nhật credibility và attribution qua contribution |
| Contribution | Shapley marginal contribution hoặc LLM Judge | Ebrahimi et al. 2025 | Phân biệt “agent ảnh hưởng bao nhiêu” với “episode đáng tin bao nhiêu” |
| Skill-conditioned trust | $\hat\tau_{i,k}=\frac{\sum_{k'}W_{k,k'}n_{i,k'}o_{i,k'}}{\sum_{k'}W_{k,k'}n_{i,k'}}$ | Xia & Wang 2026 | Khung chuẩn để borrowing theo skill |
| Adaptive borrowing | $W_{k,k'}=\beta\max(R_{k,k'},0)$ | Xia & Wang 2026 | Có thể dùng làm estimator cho transfer matrix |
| Zero-evidence gate | Không borrow nếu $n_{i,k}<1$ | Xia & Wang 2026 | Chặn reputation từ skill khác khi target chưa có bằng chứng trực tiếp |
| Judge reliability | $\mathrm{Se},\mathrm{Sp}$, likelihood ratio, Bayes | Statistical calibration | Chuyển verdict của judge thành $P(z=1\mid F)$, không coi verdict là truth |
| Beta reputation | $\theta\sim \mathrm{Beta}(\alpha,\beta)$ | Ismail & Jøsang 2002 + Beta–Bernoulli | Lưu mean và uncertainty của competence |
| Brier | $\frac1N\sum(p_i-y_i)^2$ | Brier 1950 | Metric chính cho probabilistic reputation |
| ECE | $\sum_m\frac{|B_m|}{N}|\mathrm{acc}(B_m)-\mathrm{conf}(B_m)|$ | Guo et al. 2017 | Diagnostic calibration |
| NLL | $-\frac1N\sum[y\log p+(1-y)\log(1-p)]$ | Log-loss / Guo et al. | Phạt mạnh prediction tự tin nhưng sai |

Hai paper gần nhất với câu chuyện RepGuard thực ra bổ sung cho nhau rất đẹp. Ebrahimi et al. giải quyết **ai đã đóng góp vào outcome và cập nhật historical credibility thế nào**, nhưng bản thân họ cũng quan sát thấy judge sai có thể làm hỏng CSc và CrS. Xia & Wang giải quyết **reputation nên được condition và borrow giữa các skill thế nào**, nhưng họ cố ý làm việc trong regime mà outcome đã được environment/program xác minh, tức observation được xem là đáng tin và sự khan hiếm chủ yếu nằm ở số episode.

Đó chính là khe hở đẹp cho RepGuard:

$$
\boxed{\text{Ebrahimi: historical contribution}}
$$

$$
+\quad
\boxed{\text{Xia \& Wang: skill-conditioned transfer}}
$$

$$
+\quad
\boxed{\text{RepGuard: imperfect-feedback inference + uncertainty}}
$$

thành một mô hình thống nhất.

## Credibility Scoring của Ebrahimi et al.

Paper của Ebrahimi, Dehghankar và Asudeh định nghĩa credibility score $CrS^{(i)}\in[0,1]$ như mức hệ thống tin agent $i$ dựa trên các vòng trước. Khi không có prior information, tất cả agent có thể được khởi tạo ở một giá trị mặc định, ví dụ $0.5$. Cuối mỗi vòng $t$, hệ thống nhận reward $r_t\in[-1,1]$ cho output cuối cùng và tính Contribution Score $CSc_t^{(i)}$ cho từng agent; các contribution score được thiết kế sao cho tổng bằng một. 

**Điểm cần nắm trước tiên:** trong paper này,

$$
\text{Contribution} \neq \text{Credibility}.
$$

$CSc$ hỏi:

> Agent này đã tác động bao nhiêu vào đáp án cuối?

Trong khi $CrS$ hỏi:

> Tác động lịch sử của agent này đáng tin/hữu ích đến đâu?

Paper nhấn mạnh một agent có thể tác động rất mạnh nhưng kéo cả nhóm tới đáp án sai, nên contribution cao không đồng nghĩa credibility cao.

### Công thức Contribution Score bằng Shapley

Gọi:

$$
O=\{o_1,\ldots,o_N\}
$$

là tập output của $N$ agent, và

$$
\Sigma(S)
$$

là output cuối cùng nếu chỉ aggregate một subset $S\subseteq O$.

Khi đó contribution của agent $i$ được tính theo Shapley value:

$$
\boxed{
CSc_t^{(i)}
=
\sum_{S\subseteq O\setminus\{o_i\}}
\frac{|S|!(N-|S|-1)!}{N!}
\left[
R\!\left(\Sigma(S\cup\{o_i\})\right)
-
R\!\left(\Sigma(S)\right)
\right]
}
$$

Trong đó phần

$$
R(\Sigma(S\cup\{o_i\}))-R(\Sigma(S))
$$

là **marginal contribution**: thêm output của agent $i$ vào coalition $S$ thì chất lượng output cuối thay đổi bao nhiêu. Hệ số factorial ở phía trước lấy trung bình marginal contribution trên các thứ tự coalition khác nhau. Đây chính là Eq. Shapley-based CSc trong paper.

Ví dụ trực giác: nếu agent $i$ chỉ lặp lại ý của những agent khác và không thay đổi kết quả, marginal contribution gần $0$. Nếu output của nó thường biến coalition từ sai thành đúng, contribution dương lớn.

Nhược điểm là Shapley phải xét rất nhiều subset. Ebrahimi et al. chỉ ra điều này trở nên đặc biệt khó khi các agent giao tiếp hoặc khi chính aggregation/reward cần LLM; trong những tình huống đó họ dùng một **LLM-as-a-Judge để trực tiếp ước lượng contribution** từ final answer, dialogue log và các output của agent.

### Công thức cập nhật Credibility

Công thức quan trọng nhất bạn đang cần là:

$$
\boxed{
CrS_t^{(i)}
=
CrS_{t-1}^{(i)}
\left(
1+\eta\,CSc_t^{(i)}r_t
\right)
}
$$

với:

$$
\eta = \text{learning rate},
$$

$$
CSc_t^{(i)}=\text{contribution của agent }i,
$$

$$
r_t=\text{reward của đáp án cuối tại round }t.
$$

Đây là Eq. (2) của paper.

Ý nghĩa rất dễ hiểu nếu viết thành:

$$
\frac{CrS_t^{(i)}}{CrS_{t-1}^{(i)}}
=
1+\eta CSc_t^{(i)}r_t.
$$

Tức là **credibility thay đổi theo tỉ lệ nhân**, không phải cộng một lượng cố định.

Ví dụ:

$$
CrS_{t-1}=0.6,\quad
\eta=0.2,\quad
CSc=0.4.
$$

Nếu team thành công hoàn toàn:

$$
r_t=1,
$$

thì

$$
CrS_t
=
0.6(1+0.2\times0.4)
=
0.648.
$$

Nếu cùng một mức contribution nhưng team thất bại hoàn toàn:

$$
r_t=-1,
$$

thì

$$
CrS_t
=
0.6(1-0.08)
=
0.552.
$$

Điều này tạo ra logic hợp lý:

$$
\boxed{\text{contribute nhiều vào success}\Rightarrow \text{tăng mạnh}}
$$

và

$$
\boxed{\text{contribute nhiều vào failure}\Rightarrow \text{giảm mạnh}}.
$$

Từ Eq. (2), ta có thể **suy ra đại số** sau $T$ lần cập nhật:

$$
\boxed{
CrS_T^{(i)}
=
CrS_0^{(i)}
\prod_{t=1}^{T}
\left(1+\eta CSc_t^{(i)}r_t\right)
}
$$

cho các round agent $i$ tham gia. Đây không phải công thức được paper đánh số riêng; nó là phép khai triển trực tiếp recurrence của Eq. (2).

Lấy log:

$$
\log CrS_T^{(i)}
=
\log CrS_0^{(i)}
+
\sum_t
\log(1+\eta CSc_t^{(i)}r_t).
$$

Nếu

$$
|\eta CSc_t^{(i)}r_t|\ll 1,
$$

thì dùng

$$
\log(1+x)\approx x
$$

sẽ cho:

$$
\log CrS_T^{(i)}
\approx
\log CrS_0^{(i)}
+
\eta\sum_tCSc_t^{(i)}r_t.
$$

Nghĩa là multiplicative credibility có thể được hiểu gần giống một **additive evidence accumulator trong log-space** khi mỗi update nhỏ.

### Công thức dùng CrS để aggregate

Với centroid-based aggregation, paper sử dụng:

$$
\boxed{
\vec{x}^{+}
=
\frac{1}{N}
\sum_{i:a_i\in A_t}
CrS_{t-1}^{(i)}
\vec v(O(a_i,q_t))
}
$$

rồi chọn answer gần centroid đó. 

Lưu ý kỹ: paper viết $1/N$, không phải phép weighted-average chuẩn

$$
\frac{\sum_i CrS_i v_i}{\sum_i CrS_i}.
$$

Trong centroid dùng cosine-distance, nhân toàn centroid với một hằng số dương không đổi hướng của vector, nên việc chia cho $N$ thay vì tổng weight không nhất thiết thay đổi ranking cosine. Nhưng khi chuyển sang **weighted voting** cho MMLU-Pro, tôi khuyên RepGuard dùng normalization rõ ràng:

$$
\tilde w_i
=
\frac{CrS_i}{\sum_jCrS_j},
$$

rồi:

$$
Score(c)
=
\sum_i
\tilde w_i\,
\mathbf 1[a_i=c],
$$

$$
\boxed{
\hat c=\arg\max_c Score(c)
}.
$$

Đây là adaptation phù hợp với RepGuard, không phải equation nguyên văn của Ebrahimi.

### Điểm yếu toán học khi đưa CrS vào RepGuard

Có ba điểm rất quan trọng.

Thứ nhất, $CrS$ là **credibility score**, không phải posterior probability:

$$
CrS_i\neq P(\text{agent }i\text{ đúng trên task mới}\mid \text{history})
$$

theo nghĩa Bayesian chuẩn. Eq. (2) không xác định likelihood hay prior/posterior.

Thứ hai, mặc dù paper mô tả $CrS\in[0,1]$, chính Eq. (2) không chứa toán tử projection/clipping. Nếu đọc equation thuần túy và có

$$
r_t>0,\ CSc_t>0,\ \eta>0,
$$

thì multiplier lớn hơn $1$, nên nhiều update dương liên tiếp không tự đảm bảo $CrS\le1$. Vì vậy khi reproduce baseline, nên kiểm tra implementation của authors hoặc ghi rõ clipping policy trong code của bạn thay vì giả định nó từ phương trình. Bound được paper nêu rõ và update multiplicative được nêu rõ, nhưng equation bản thân không thực hiện projection. 

Thứ ba — và đây là cầu nối trực tiếp tới RepGuard — chính Ebrahimi et al. báo cáo rằng trên HumanEval, GPT-4o-mini judge có những trường hợp đánh code sai thành reward $1$, làm biến dạng CSc rồi tiếp tục làm biến dạng CrS; với một judge yếu hơn trên GSM8K, họ còn thấy malformed contribution outputs và trajectory credibility không ổn định.

Nói cách khác:

$$
\boxed{
\text{Ebrahimi update tốt đến đâu}
\quad\text{phụ thuộc vào}\quad
\text{judge signal tốt đến đâu}.
}
$$

Đây chính xác là lý do RepGuard không nên đưa $r_t$ hoặc judge label thẳng vào reputation.

## Skill-conditioned reputation, borrowing và zero-evidence gate của Xia & Wang

Xia & Wang xây dựng bài toán với $M$ agent và $K$ skill. Agent $i$ có true competence chưa biết:

$$
\theta_{i,k}\in[0,1].
$$

Mỗi cell agent–skill $(i,k)$ có:

$$
n_{i,k}=\text{số episode đã quan sát},
$$

và

$$
o_{i,k}\in[0,1]
$$

là average verified outcome của những episode đó. Paper nhấn mạnh đây là **program/environment-verifiable outcomes**: sau khi record được quan sát, chính outcome được xem là trustworthy; tài nguyên khan hiếm là số observation $n_{i,k}$, chứ không phải độ tin cậy của feedback. 

Đây là sự khác nhau cốt lõi với RepGuard:

$$
\text{Xia \& Wang: }
o_{i,k}\text{ đáng tin, nhưng dữ liệu sparse}
$$

trong khi

$$
\text{RepGuard: }
\text{cả evidence quality lẫn transfer đều có thể bất định.}
$$

### Công thức tổng quát cho skill-conditioned reputation

Equation trung tâm là:

$$
\boxed{
\hat\tau_{i,k}(W)
=
\frac{
\displaystyle\sum_{k'}
W_{k,k'}\,n_{i,k'}\,o_{i,k'}
}{
\displaystyle\sum_{k'}
W_{k,k'}\,n_{i,k'}
}
}
$$

trong đó:

$$
W\in\mathbb R_{\ge0}^{K\times K}
$$

là **coupling matrix**, với diagonal bằng $1$. Skill $k$ borrow evidence từ skill $k'$ theo cả hai yếu tố:

$$
W_{k,k'}
$$

và

$$
n_{i,k'}.
$$

Do đó lượng effective evidence được borrow là:

$$
W_{k,k'}n_{i,k'}.
$$

Đây là Eq. (1) của Xia & Wang. 

Ta có thể viết lại trực giác hơn:

$$
\hat\tau_{i,k}
=
\frac{
\text{tổng weighted successes}
}{
\text{tổng weighted evidence}
}.
$$

### Independent reputation

Nếu:

$$
W=I,
$$

thì chỉ diagonal còn lại:

$$
\boxed{
\hat\tau_{i,k}=o_{i,k}
}.
$$

Không skill nào vay evidence của skill khác. Paper mô tả cách này là ít bias do cross-skill pooling nhưng variance cao khi $n_{i,k}$ nhỏ.

### Global reputation

Nếu:

$$
W=\mathbf 1\mathbf 1^\top,
$$

tất cả entries bằng $1$, ta có:

$$
\hat\tau_i
=
\frac{\sum_{k'}n_{i,k'}o_{i,k'}}
{\sum_{k'}n_{i,k'}}.
$$

Mọi skill nhận cùng một score của agent.

Điều này có variance thấp vì pool nhiều evidence, nhưng có thể bị bias nặng khi agent specialized: giỏi coding không có nghĩa giỏi law. Xia & Wang dùng chính contrast này để động cơ hóa skill conditioning.

### Fixed conditional borrowing

Với các skill được biết là cùng một correlated block, paper đặt:

$$
W_{k,k}=1
$$

và với $k\neq k'$:

$$
\boxed{
W_{k,k'}
=
\begin{cases}
\beta,& k,k'\text{ nằm trong cùng correlated block},\\
0,&\text{khác block}.
\end{cases}
}
$$

với:

$$
\beta\in[0,1].
$$

Khi:

$$
\beta=0,
$$

ta trở lại Independent.

Khi $\beta$ lớn, system borrow nhiều hơn. Vì vậy $\beta$ là một knob điều khiển trade-off:

$$
\boxed{\text{data efficiency}\leftrightarrow\text{cross-skill contamination}}
$$

và chính paper chỉ ra rằng cùng một borrowing channel giúp giảm variance cũng trở thành attack channel cho reputation laundering. 

### Adaptive cross-skill borrowing

Thay vì tự gán correlated block, Xia & Wang ước lượng correlation giữa skill dựa trên profile của các agent.

Đầu tiên:

$$
\bar o_{\cdot,k}
=
\frac1M
\sum_i o_{i,k},
$$

$$
\tilde o_{i,k}
=
o_{i,k}-\bar o_{\cdot,k}.
$$

Cross-agent Pearson correlation giữa skill $k$ và $k'$:

$$
\boxed{
R_{k,k'}
=
\frac{
\sum_i\tilde o_{i,k}\tilde o_{i,k'}
}{
\sqrt{\sum_i\tilde o_{i,k}^2}
\sqrt{\sum_i\tilde o_{i,k'}^2}
}
}
$$

sau đó:

$$
\boxed{
W_{k,k'}
=
\beta\max(R_{k,k'},0),
\qquad k\neq k'.
}
$$

Như vậy:

$$
R_{k,k'}\le0
\Rightarrow W_{k,k'}=0,
$$

còn skill có positive correlation thì borrow evidence. Đây là Eq. (2) và adaptive estimator của paper. 

**Ví dụ.** Giả sử target skill có:

$$
n_{i,t}=2,\quad o_{i,t}=0.5,
$$

farm/related skill có:

$$
n_{i,f}=10,\quad o_{i,f}=0.9,
$$

và:

$$
W_{t,f}=\beta=0.1.
$$

Khi đó:

$$
\hat\tau_{i,t}
=
\frac{
2(0.5)+0.1(10)(0.9)
}{
2+0.1(10)
}
$$

$$
=
\frac{1+0.9}{3}
=
0.6333.
$$

Nếu không borrow:

$$
\hat\tau=0.5.
$$

Borrowing nâng estimate từ $0.5$ lên khoảng $0.633$ vì evidence ở skill liên quan tốt hơn.

### Router và regret

Sau khi có skill-conditioned reputation, router chọn:

$$
\boxed{
a_k^\star
=
\arg\max_{i\in P}
\hat\tau_{i,k}
}
$$

và paper đánh giá bằng routing regret:

$$
\boxed{
Reg(\hat\tau)
=
\frac1K
\sum_{k=1}^{K}
\left[
\max_{i\in P}\theta_{i,k}
-
\theta_{a_k^\star,k}
\right].
}
$$

Tức là hỏi:

> Agent mà reputation router chọn kém hơn oracle-best agent của skill đó bao nhiêu?

Các equation này được paper định nghĩa trực tiếp sau coupling estimator.

### Cross-skill laundering và hiện tượng “$\beta$, $B$ triệt tiêu”

Đây là phần cực kỳ quan trọng cho RepGuard.

Giả sử attacker muốn được tin trên target skill $k_t$, nhưng **không có một episode thật nào trên target**:

$$
n_{i,k_t}=0.
$$

Nó farm reputation ở một skill khác $k_f$:

$$
n_{i,k_f}=B
$$

với observed performance:

$$
o_{i,k_f}.
$$

Nếu coupling giữa hai skill là:

$$
W_{k_t,k_f}=\beta>0,
$$

thì từ Eq. (1):

$$
\hat\tau_{i,k_t}
=
\frac{
\beta B o_{i,k_f}
+
n_{i,k_t}o_{i,k_t}
}{
\beta B+n_{i,k_t}
}.
$$

Vì:

$$
n_{i,k_t}=0,
$$

nên:

$$
\hat\tau_{i,k_t}
=
\frac{
\beta B o_{i,k_f}
}{
\beta B
}.
$$

Do đó:

$$
\boxed{
\hat\tau_{i,k_t}=o_{i,k_f}
}
$$

cho mọi:

$$
B\ge1,\qquad\beta>0.
$$

Đây chính là phép triệt tiêu algebraically mà Xia & Wang nhấn mạnh. Một khi target không có evidence trực tiếp, **chỉ một farm episode cũng đủ làm target estimate bị pin vào farm score**; giảm $\beta$ không giải quyết cấu trúc này miễn $\beta$ vẫn dương.

Ví dụ:

$$
o_{i,k_f}=1,\quad
B=1,\quad
\beta=0.01.
$$

Ta vẫn có:

$$
\hat\tau_{i,k_t}
=
\frac{0.01\times1\times1}
{0.01\times1}
=1.
$$

Tăng budget lên $B=100$:

$$
\frac{0.01\times100\times1}
{0.01\times100}
=1.
$$

Vì vậy:

$$
\boxed{\text{clip }\beta\text{ không đủ}}
$$

và

$$
\boxed{\text{rate-limit farm budget không đủ}}
$$

cho zero-target pure laundering. Paper xác nhận chính hiện tượng này và cho rằng defense phải dựa vào việc **target evidence có tồn tại hay không**.

### Zero-evidence gate

Defense của Xia & Wang cực kỳ đơn giản:

$$
\boxed{
n_{i,k}<1
\quad\Rightarrow\quad
\text{suppress cross-skill borrowing}.
}
$$

Ta có thể formalize thành:

$$
g_{i,k}
=
\mathbf 1[n_{i,k}\ge1].
$$

Khi $g=0$, off-diagonal evidence không được phép tác động vào target reputation.

Paper báo cáo rằng trong attack setup của họ tại $\beta=0.1$, gate loại bỏ lợi ích của zero-target laundering/whitewashing trong GREEN pair được nghiên cứu, nhưng authors cũng nhấn mạnh đây **không phải Sybil resistance hoàn chỉnh**: attacker chỉ cần tạo một direct target episode là vượt predicate $n_{i,k}<1$; sau đó farm evidence lại có thể đi qua. 

Đây là điểm bạn phải trình bày rất cẩn thận trong RepGuard:

$$
\boxed{\text{zero-evidence gate là bounded defense, không phải cure-all.}}
$$

### Cách map Xia & Wang sang RepGuard

Không nên dùng nguyên:

$$
n_{i,k'}o_{i,k'}
$$

vì trong RepGuard, một “success” có thể chỉ là judge nói success.

Thay vào đó, episode $t$ nên có:

$$
p_{it}
=
P(z_{it}=1\mid F_{it}),
$$

và cross-skill weight:

$$
\tau_{k^{*},k_t}
\approx W_{k^{*},k_t}.
$$

Tức là thay:

$$
\boxed{
n_{i,k'}o_{i,k'}
}
$$

bằng một dạng calibrated expected success mass:

$$
\boxed{
\sum_{t:k_t=k'}m_{it}p_{it}.
}
$$

Tương tự, raw episode count:

$$
n_{i,k'}
$$

được thay bằng effective evidence mass:

$$
\boxed{
M_{i,k'}
=
\sum_{t:k_t=k'}m_{it}.
}
$$

Khi đó phiên bản “Xia + imperfect feedback” tự nhiên trở thành:

$$
\hat\tau^{\mathrm{cal}}_{i,k^{*}}
=
\frac{
\sum_{k'}
W_{k^{*},k'}
\sum_{t:k_t=k'}m_{it}p_{it}
}{
\sum_{k'}
W_{k^{*},k'}
\sum_{t:k_t=k'}m_{it}
}.
$$

Đây là **extension của RepGuard**, không phải công thức của Xia & Wang. Nó chính là điểm giao giữa hai chiều evidence reliability và transferability mà proposal của bạn đang nhắm tới.

## Hiệu chuẩn LLM-as-a-Judge bằng confusion matrix và Bayes

Một kết luận quan trọng từ literature là không nên đồng nhất:

$$
\text{judge verdict}
$$

với:

$$
\text{ground truth}.
$$

Nghiên cứu LLM-as-a-Judge đã ghi nhận position, verbosity và self-enhancement biases; các nghiên cứu uncertainty sau đó cũng trực tiếp xây dựng các phương pháp để đo uncertainty của judge thay vì tin mọi verdict như nhau. Công trình năm 2025 về calibrating LLM judges còn huấn luyện uncertainty probe bằng Brier loss và cho thấy vấn đề calibration phải được xử lý riêng với judge correctness. Điều này đặc biệt phù hợp với observation của chính Ebrahimi et al. rằng judge sai có thể truyền lỗi sang reward, CSc và cuối cùng CrS.

Đối với RepGuard, cách đơn giản và scientifically clean nhất là có một **held-out judge calibration set** nơi bạn biết true correctness bằng answer key, unit test hoặc environment verification.

Gọi:

$$
z_t\in\{0,1\}
$$

là true correctness của agent answer và

$$
f_t\in\{0,1\}
$$

là binary judge verdict:

$$
f_t=1\Rightarrow\text{judge nói answer đúng}.
$$

### Confusion matrix

Định nghĩa:

$$
TP=\sum_t\mathbf 1[z_t=1,f_t=1],
$$

$$
FN=\sum_t\mathbf 1[z_t=1,f_t=0],
$$

$$
TN=\sum_t\mathbf 1[z_t=0,f_t=0],
$$

$$
FP=\sum_t\mathbf 1[z_t=0,f_t=1].
$$

Tôi khuyên cố định convention:

$$
\boxed{
C=
\begin{pmatrix}
TN&FP\\
FN&TP
\end{pmatrix}
}
$$

với **rows = true label**, **columns = judge verdict**, rồi ghi convention này trong paper để tránh nhầm.

### Sensitivity

Sensitivity, recall hay true-positive rate:

$$
\boxed{
Se
=
P(f=1\mid z=1)
=
\frac{TP}{TP+FN}.
}
$$

Nó trả lời:

> Trong những answer thực sự đúng, judge nhận ra đúng bao nhiêu phần?

Ví dụ:

$$
Se=0.9
$$

nghĩa là khoảng 90% positive cases được judge nhận đúng.

### Specificity

Specificity hay true-negative rate:

$$
\boxed{
Sp
=
P(f=0\mid z=0)
=
\frac{TN}{TN+FP}.
}
$$

Nó trả lời:

> Trong những answer thực sự sai, judge loại đúng bao nhiêu phần?

Từ đây:

$$
FPR=1-Sp
=
\frac{FP}{FP+TN},
$$

$$
FNR=1-Se
=
\frac{FN}{FN+TP}.
$$

Đối với reputation, **specificity đặc biệt quan trọng về security**: nếu $Sp$ thấp, malicious/weak agent có thể nhận false positive và tích lũy reputation.

### Không được nhầm sensitivity với posterior correctness

Giả sử judge nói:

$$
f=1.
$$

Ta **không được** viết:

$$
P(z=1\mid f=1)=Se.
$$

Sensitivity là:

$$
P(f=1\mid z=1),
$$

trong khi thứ RepGuard cần là chiều ngược:

$$
P(z=1\mid f=1).
$$

Phải dùng Bayes.

Gọi prior base rate:

$$
\pi=P(z=1).
$$

Nếu judge nói “đúng”:

$$
\boxed{
P(z=1\mid f=1)
=
\frac{
Se\,\pi
}{
Se\,\pi+(1-Sp)(1-\pi)
}.
}
$$

Nếu judge nói “sai”:

$$
\boxed{
P(z=1\mid f=0)
=
\frac{
(1-Se)\pi
}{
(1-Se)\pi+Sp(1-\pi)
}.
}
$$

Đây chính là đại lượng:

$$
p_t=P(z_t=1\mid F_t)
$$

mà ECRT cần.

**Ví dụ.**

Giả sử:

$$
Se=0.9,\qquad
Sp=0.8,
$$

và prior probability answer đúng:

$$
\pi=0.6.
$$

Nếu judge nói đúng:

$$
P(z=1\mid f=1)
=
\frac{0.9(0.6)}
{0.9(0.6)+0.2(0.4)}
$$

$$
=
\frac{0.54}{0.62}
\approx0.871.
$$

Vậy signal “judge says correct” **không trở thành $1$**:

$$
\boxed{p_t\approx0.871.}
$$

Ngược lại, nếu judge nói sai:

$$
P(z=1\mid f=0)
=
\frac{0.1(0.6)}
{0.1(0.6)+0.8(0.4)}
$$

$$
=
\frac{0.06}{0.38}
\approx0.158.
$$

Điều này rất phù hợp với triết lý ECRT: feedback không phải truth; feedback thay đổi posterior belief về truth.

### Dạng likelihood ratio tiện hơn

Định nghĩa positive likelihood ratio:

$$
\boxed{
LR^+
=
\frac{Se}{1-Sp}
}
$$

và negative likelihood ratio:

$$
\boxed{
LR^-
=
\frac{1-Se}{Sp}.
}
$$

Prior odds:

$$
O_{\mathrm{prior}}
=
\frac{\pi}{1-\pi}.
$$

Nếu judge nói đúng:

$$
O_{\mathrm{post}}
=
O_{\mathrm{prior}}LR^+.
$$

Nếu judge nói sai:

$$
O_{\mathrm{post}}
=
O_{\mathrm{prior}}LR^-.
$$

Sau đó:

$$
p
=
\frac{O_{\mathrm{post}}}
{1+O_{\mathrm{post}}}.
$$

Cách này đặc biệt thuận tiện khi có nhiều feedback source.

### Nhiều judges / feedback sources

Nếu có $J$ sources và **giả sử conditional independence khi biết $z$**:

$$
F=(f_1,\ldots,f_J),
$$

thì:

$$
P(F\mid z)
=
\prod_{j=1}^{J}P(f_j\mid z).
$$

Posterior odds:

$$
\boxed{
\frac{P(z=1\mid F)}
{P(z=0\mid F)}
=
\frac{\pi}{1-\pi}
\prod_{j=1}^{J}
\frac{
P(f_j\mid z=1)
}{
P(f_j\mid z=0)
}.
}
$$

Với mỗi judge:

$$
P(f_j\mid z=1)
=
Se_j^{f_j}(1-Se_j)^{1-f_j},
$$

$$
P(f_j\mid z=0)
=
(1-Sp_j)^{f_j}Sp_j^{1-f_j}.
$$

Nhưng đây là **Naive Bayes assumption**. Nếu ba judges đều cùng model family, cùng prompt và cùng failure mode, chúng có thể correlated; nhân likelihood như thể chúng độc lập sẽ làm posterior quá tự tin. Khi ground truth không có cho toàn bộ data và bạn muốn đồng thời infer latent truth và error rates của nhiều annotators/judges, Dawid–Skene là classical latent-label route: paper gốc 1979 ước lượng observer error rates bằng EM ngay cả khi true response không quan sát trực tiếp.

Đối với core RepGuard experiment, tôi vẫn khuyên **không dùng Dawid–Skene trước**. Proposal của bạn có MMLU-Pro/objective benchmarks, tức bạn hoàn toàn có thể xây calibration split có truth; phương pháp trực tiếp sẽ làm causal story sạch hơn.

### Ước lượng uncertainty của sensitivity và specificity

Không nên chỉ báo cáo point estimate:

$$
\hat{Se}=\frac{TP}{TP+FN}.
$$

Nếu calibration set nhỏ, ví dụ $TP=10,FN=0$, MLE cho:

$$
\hat{Se}=1,
$$

nhưng rõ ràng chưa đủ bằng chứng để tin judge “hoàn hảo”.

Có thể dùng Beta prior:

$$
Se\sim Beta(a_{Se},b_{Se}),
$$

sau quan sát:

$$
\boxed{
Se\mid D
\sim
Beta(a_{Se}+TP,b_{Se}+FN).
}
$$

Tương tự:

$$
Sp\sim Beta(a_{Sp},b_{Sp}),
$$

$$
\boxed{
Sp\mid D
\sim
Beta(a_{Sp}+TN,b_{Sp}+FP).
}
$$

Nếu chọn uniform prior:

$$
Beta(1,1),
$$

thì posterior mean:

$$
E[Se\mid D]
=
\frac{TP+1}{TP+FN+2},
$$

$$
E[Sp\mid D]
=
\frac{TN+1}{TN+FP+2}.
$$

Cách này tránh estimate $0$ hoặc $1$ quá sớm.

### Judge nên được calibration theo domain

Điều này rất đáng làm trong RepGuard vì Ebrahimi et al. đã quan sát judge effectiveness phụ thuộc task: code verification và mathematical reasoning cho failure pattern khác nhau.

Thay vì chỉ:

$$
Se_j,\ Sp_j,
$$

có thể estimate:

$$
Se_{j,k},\qquad Sp_{j,k}
$$

cho judge $j$, domain/skill $k$.

Nếu sample ít, dùng global estimate làm fallback hoặc hierarchical shrinkage thay vì để từng cell tự estimate cực đoan.

Đây cũng giúp bạn có một ablation rất đẹp:

$$
\text{global judge calibration}
$$

so với

$$
\text{skill-conditioned judge calibration}.
$$

### Judge output là probability thay vì binary verdict

Nếu judge cho raw confidence $s_t\in[0,1]$, đừng mặc định:

$$
s_t=P(z=1).
$$

Calibration literature định nghĩa một probability predictor là calibrated nếu các event được gán probability khoảng $p$ thực sự xảy ra với tần suất khoảng $p$. Guo et al. formalise điều này bằng:

$$
P(\hat Y=Y\mid\hat P=p)=p.
$$

Họ cũng mô tả post-hoc calibration trên held-out validation data, bao gồm histogram binning, isotonic regression và temperature scaling. 

Vì thế pipeline chuẩn là:

$$
s_t
\longrightarrow
\text{calibration function}
\longrightarrow
q_t
$$

sao cho:

$$
q_t\approx P(z_t=1\mid s_t).
$$

Các nghiên cứu LLM-judge mới cũng cho thấy verbalised confidence không nhất thiết calibrated, và calibration của uncertainty là một vấn đề riêng cần đánh giá.

## Beta/Bayesian reputation và điểm tinh tế của soft evidence

Ismail & Jøsang giới thiệu Beta Reputation System bằng cách dùng beta probability density để kết hợp feedback và tạo reputation rating. Đối với RepGuard, Beta đặc biệt hữu ích vì nó không chỉ giữ một score mà còn giữ **evidence concentration**, tức uncertainty.

### Phân phối Beta

Giả sử competence thật của agent trên một task class là:

$$
\theta\in[0,1].
$$

Đặt prior:

$$
\boxed{
\theta\sim Beta(\alpha,\beta).
}
$$

Mật độ:

$$
\boxed{
p(\theta\mid\alpha,\beta)
=
\frac{
\theta^{\alpha-1}(1-\theta)^{\beta-1}
}{
B(\alpha,\beta)
}
}
$$

với:

$$
B(\alpha,\beta)
=
\frac{\Gamma(\alpha)\Gamma(\beta)}
{\Gamma(\alpha+\beta)}.
$$

Posterior mean:

$$
\boxed{
\mu
=
E[\theta]
=
\frac{\alpha}{\alpha+\beta}.
}
$$

Variance:

$$
\boxed{
\sigma^2
=
\frac{
\alpha\beta
}{
(\alpha+\beta)^2(\alpha+\beta+1)
}.
}
$$

Đây là lý do Beta tốt hơn một raw score.

Ví dụ:

$$
Beta(2,2)
$$

và

$$
Beta(200,200)
$$

đều có:

$$
\mu=0.5.
$$

Nhưng Beta(200,200) tập trung quanh $0.5$ hơn rất nhiều.

Do đó:

$$
\boxed{\text{mean = competence estimate}}
$$

trong khi:

$$
\boxed{\alpha+\beta = \text{mức concentration/evidence}.}
$$

### Hard binary evidence: Bayesian update chính xác

Nếu episode có true correctness được quan sát:

$$
z_t\sim Bernoulli(\theta),
$$

với:

$$
z_t\in\{0,1\},
$$

thì likelihood:

$$
P(z_t\mid\theta)
=
\theta^{z_t}(1-\theta)^{1-z_t}.
$$

Vì Beta conjugate với Bernoulli:

$$
\boxed{
\alpha_t=\alpha_{t-1}+z_t
}
$$

$$
\boxed{
\beta_t=\beta_{t-1}+1-z_t.
}
$$

Sau $S$ successes và $F$ failures:

$$
\boxed{
\theta\mid D
\sim
Beta(\alpha_0+S,\beta_0+F).
}
$$

Với uniform prior:

$$
\alpha_0=\beta_0=1,
$$

nếu có $S=8,F=2$:

$$
Beta(9,3)
$$

và:

$$
E[\theta\mid D]
=
\frac9{12}
=
0.75.
$$

Lưu ý empirical accuracy là:

$$
8/10=0.8,
$$

nhưng Bayesian posterior mean bị prior kéo nhẹ về $0.5$.

### Khi feedback bị nhiễu, posterior chính xác không còn là một Beta đơn

Đây là điểm rất quan trọng đối với RepGuard.

Ta không quan sát $z$. Ta chỉ quan sát judge feedback $f$.

Mô hình:

$$
\theta\sim Beta(\alpha,\beta),
$$

$$
z\mid\theta\sim Bernoulli(\theta),
$$

$$
f\mid z
\sim\text{judge confusion model}.
$$

Đặt:

$$
L_1=P(f\mid z=1),
$$

$$
L_0=P(f\mid z=0).
$$

Ví dụ nếu $f=1$:

$$
L_1=Se,
\qquad
L_0=1-Sp.
$$

Marginal likelihood của $f$ khi biết $\theta$:

$$
P(f\mid\theta)
=
L_1\theta+L_0(1-\theta).
$$

Vì vậy exact posterior:

$$
p(\theta\mid f)
\propto
\left[
L_1\theta+L_0(1-\theta)
\right]
Beta(\theta;\alpha,\beta).
$$

Ta dùng hai identity:

$$
\theta Beta(\theta;\alpha,\beta)
=
\frac{\alpha}{\alpha+\beta}
Beta(\theta;\alpha+1,\beta),
$$

$$
(1-\theta)Beta(\theta;\alpha,\beta)
=
\frac{\beta}{\alpha+\beta}
Beta(\theta;\alpha,\beta+1).
$$

Do đó:

$$
\boxed{
p(\theta\mid f)
=
w\,Beta(\alpha+1,\beta)
+
(1-w)\,Beta(\alpha,\beta+1)
}
$$

trong đó:

$$
\boxed{
w
=
P(z=1\mid f)
=
\frac{
L_1\alpha
}{
L_1\alpha+L_0\beta
}.
}
$$

Đây là một kết quả rất hữu ích: **posterior chính xác sau một noisy verdict là mixture của hai Beta**, chứ không phải đơn giản:

$$
Beta(\alpha+w,\beta+1-w).
$$

Với prior mean:

$$
\pi=\frac{\alpha}{\alpha+\beta},
$$

công thức $w$ cũng chính là Bayes formula ở section trước.

### Vì sao fractional Beta update vẫn hấp dẫn?

Một approximation phổ biến, và cũng là dạng proposal ECRT hiện tại của bạn, là:

$$
\boxed{
\alpha'=\alpha+p
}
$$

$$
\boxed{
\beta'=\beta+(1-p)
}
$$

với:

$$
p=P(z=1\mid F).
$$

Nó rất trực quan: thay vì cộng một full success hoặc failure, ta cộng **expected success count** $p$ và expected failure count $1-p$.

Điều rất hay là fractional Beta này có **cùng posterior mean** với exact one-step mixture.

Exact mixture mean:

$$
E[\theta\mid f]
=
p\frac{\alpha+1}{\alpha+\beta+1}
+
(1-p)
\frac{\alpha}{\alpha+\beta+1}
$$

$$
=
\frac{\alpha+p}
{\alpha+\beta+1}.
$$

Fractional Beta:

$$
Beta(\alpha+p,\beta+1-p)
$$

cũng có mean:

$$
\frac{\alpha+p}
{\alpha+\beta+1}.
$$

Cho nên:

$$
\boxed{\text{fractional update bảo toàn exact one-step posterior mean}.}
$$

Nhưng nó **không bảo toàn toàn bộ posterior distribution/variance** nói chung.

Đây là lý do tôi khuyên trong paper không viết:

> “By conjugate Bayesian updating with noisy feedback, we obtain …”

nếu equation của bạn là:

$$
\alpha+=p,\quad\beta+=1-p.
$$

Câu chính xác hơn là:

> “We maintain a Beta approximation using calibrated fractional expected counts.”

hoặc:

> “We use an evidence-weighted Beta pseudo-posterior / assumed-density approximation.”

Điều này chặt chẽ hơn nhiều khi reviewer soi Bayesian semantics.

### Một counterexample rất quan trọng: judge hoàn toàn vô dụng

Giả sử judge là coin flip:

$$
Se=0.5,\qquad Sp=0.5.
$$

Khi đó:

$$
P(f\mid z=1)=P(f\mid z=0),
$$

nên feedback $f$ mang **zero information** về $z$.

Exact Bayesian posterior phải thỏa:

$$
\boxed{
p(\theta\mid f)=p(\theta)
}
$$

— tức không update gì cả.

Nhưng nếu bạn tính:

$$
p=P(z=1\mid f)=\frac{\alpha}{\alpha+\beta}
$$

rồi vẫn update:

$$
\alpha'=\alpha+p,\quad
\beta'=\beta+1-p,
$$

thì tổng concentration tăng:

$$
\alpha'+\beta'
=
\alpha+\beta+1.
$$

Nghĩa là hệ thống trở nên **tự tin hơn mặc dù vừa nhận một feedback hoàn toàn vô dụng**.

Đây là một vấn đề trực tiếp với định nghĩa $m_t$ trong ECRT hiện tại.

Vì vậy $m_t$ không nên chỉ là một hằng số $1$ cho mọi observed judge label.

### $m_t$ nên có nghĩa gì?

Tôi khuyên định nghĩa tách biệt:

$$
\boxed{
p_t=\text{hướng của evidence}
}
$$

và:

$$
\boxed{
m_t=\text{độ mạnh/information content của evidence}.
}
$$

Một perfect verifier:

$$
Se=Sp=1
$$

có thể có:

$$
m_t\approx1.
$$

Một random judge:

$$
Se+Sp=1
$$

phải có:

$$
m_t\approx0.
$$

Một heuristic rất dễ giải thích là Youden discrimination:

$$
\boxed{
m_j
=
\max(0,Se_j+Sp_j-1).
}
$$

Nó thỏa:

$$
Se=Sp=1\Rightarrow m=1,
$$

$$
Se=Sp=0.5\Rightarrow m=0.
$$

Tuy nhiên đây là **RepGuard design choice**, không phải equation từ Ebrahimi hoặc Xia & Wang.

Một cách gắn trực tiếp hơn với Bayesian evidence là dùng likelihood ratio:

$$
\ell_t
=
\log
\frac{
P(F_t\mid z=1)
}{
P(F_t\mid z=0)
}.
$$

Nếu:

$$
\ell_t=0,
$$

feedback không phân biệt $z=1$ và $z=0$.

Do đó có thể định nghĩa effective evidence mass bằng một monotonic mapping:

$$
m_t
=
g(|\ell_t|)
$$

với:

$$
g(0)=0.
$$

Ví dụ một bounded design:

$$
\boxed{
m_t
=
\tanh\left(\frac{|\ell_t|}{2}\right).
}
$$

Đây là một proposal engineering hợp lý, nhưng **phải ablate**, chứ không nên trình bày là công thức chuẩn từ literature.

Một phương án scientific đơn giản hơn cho paper đầu tiên là:

$$
m_t=
\begin{cases}
1,&\text{oracle/environment-verified},\\
m_j,&\text{judge }j,\\
0,&\text{missing feedback},
\end{cases}
$$

rồi chọn $m_j$ trên held-out calibration set sao cho downstream Brier/NLL tốt nhất.

### Transfer-weighted Beta của ECRT

Proposal hiện tại định nghĩa:

$$
\alpha_i(q^{*})
=
\alpha_0+
\sum_t
\tau_t m_t p_t,
$$

$$
\beta_i(q^{*})
=
\beta_0+
\sum_t
\tau_t m_t(1-p_t).
$$

Công thức này có interpretation rất đẹp:

$$
\boxed{
\tau_t m_t p_t
=
\text{effective transferable positive evidence}
}
$$

và:

$$
\boxed{
\tau_t m_t(1-p_t)
=
\text{effective transferable negative evidence}.
}
$$

Tổng effective evidence episode $t$:

$$
\Delta(\alpha+\beta)
=
\tau_t m_t.
$$

Do đó:

$$
\tau_t=0
\Rightarrow\text{episode không ảnh hưởng target},
$$

$$
m_t=0
\Rightarrow\text{feedback không mang evidence},
$$

$$
p_t\approx1
\Rightarrow\text{mass gần như hoàn toàn positive},
$$

$$
p_t\approx0
\Rightarrow\text{mass gần như hoàn toàn negative}.
$$

Ví dụ:

$$
p_t=0.871,
\quad
m_t=0.8,
\quad
\tau_t=0.4.
$$

Total transferable mass:

$$
\tau m=0.32.
$$

Positive increment:

$$
\Delta\alpha
=
0.4(0.8)(0.871)
\approx0.279.
$$

Negative increment:

$$
\Delta\beta
=
0.4(0.8)(0.129)
\approx0.041.
$$

Vậy episode đó không được tính là “một full success”; nó chỉ đóng góp khoảng $0.32$ effective observation sang target skill.

Đó là interpretation rất mạnh để viết Method section.

## Brier Score, ECE, NLL và mã nguồn chuẩn hóa

Calibration ở đây phải được định nghĩa đối với **probability of agent correctness**, không đơn giản là ranking.

Gọi:

$$
p_i=P(z_i=1\mid\text{history})
$$

là reputation probability được method dự đoán cho một agent–task pair và:

$$
y_i=z_i\in\{0,1\}
$$

là actual correctness offline.

Calibration lý tưởng có nghĩa:

$$
P(Y=1\mid p)=p.
$$

Nói đơn giản: trong tất cả trường hợp method nói reputation khoảng $0.8$, agent nên thực sự đúng khoảng $80\%$. Đây là cùng notion calibration được Guo et al. formalise cho prediction confidence. 

### Brier Score

Brier's original work introduced a quadratic probability score; trong binary setting mà RepGuard cần, convention hiện đại tự nhiên là mean squared probability error. 

$$
\boxed{
BS
=
\frac1N
\sum_{i=1}^{N}
(p_i-y_i)^2.
}
$$

Range trong binary convention này:

$$
0\le BS\le1.
$$

Càng thấp càng tốt.

Ví dụ $y=1$:

Nếu:

$$
p=0.9,
$$

loss:

$$
(0.9-1)^2=0.01.
$$

Nếu:

$$
p=0.1,
$$

loss:

$$
(0.1-1)^2=0.81.
$$

Vậy Brier vừa thưởng correctness vừa thưởng probability quality.

Một prediction $p=0.5$ luôn chịu:

$$
0.25
$$

bất kể outcome là 0 hay 1, phản ánh đúng việc system đang bất định.

### Negative Log-Likelihood

Guo et al. định nghĩa NLL dưới dạng tổng:

$$
L
=
-\sum_i\log\hat\pi(y_i\mid x_i).
$$

Để các experiment có sample count khác nhau dễ so sánh, tôi khuyên report **mean NLL**:

$$
\boxed{
NLL
=
-\frac1N
\sum_{i=1}^{N}
\left[
y_i\log p_i
+
(1-y_i)\log(1-p_i)
\right].
}
$$

Càng thấp càng tốt.

NLL đặc biệt phạt overconfident mistakes rất mạnh.

Nếu:

$$
y=1,\quad p=0.9,
$$

loss:

$$
-\log0.9\approx0.105.
$$

Nếu:

$$
y=1,\quad p=0.01,
$$

loss:

$$
-\log0.01\approx4.605.
$$

Do đó một reputation mechanism thường xuyên nói “99% chắc chắn agent này sai” khi agent thực ra đúng sẽ bị phạt cực nặng.

Điều này rất hữu ích cho RepGuard vì một phương pháp có thể có accuracy/ranking tốt nhưng **posterior uncertainty quá tự tin**, và NLL sẽ phát hiện failure mode đó. NLL là probabilistic objective được Guo et al. dùng trong calibration context.

### Expected Calibration Error

Chia $[0,1]$ thành $M$ bins:

$$
B_1,\ldots,B_M.
$$

Trong mỗi bin:

$$
\mathrm{acc}(B_m)
=
\frac1{|B_m|}
\sum_{i\in B_m} y_i
$$

và:

$$
\mathrm{conf}(B_m)
=
\frac1{|B_m|}
\sum_{i\in B_m}p_i.
$$

Sau đó:

$$
\boxed{
ECE
=
\sum_{m=1}^{M}
\frac{|B_m|}{N}
\left|
\mathrm{acc}(B_m)
-
\mathrm{conf}(B_m)
\right|.
}
$$

Đây là standard binned ECE formulation được Guo et al. phổ biến cùng reliability diagrams. 

Ví dụ một bin chứa 100 reputation predictions có mean:

$$
\mathrm{conf}=0.8.
$$

Nếu 70/100 agent-task cases thực sự đúng:

$$
\mathrm{acc}=0.7.
$$

Calibration gap của bin:

$$
|0.7-0.8|=0.1.
$$

Nếu bin chiếm $20\%$ toàn test set, contribution vào ECE là:

$$
0.2\times0.1=0.02.
$$

### Không nên dùng ECE một mình

ECE phụ thuộc cách binning và số bin. Nixon et al. cho thấy lựa chọn number of bins, adaptive versus fixed bins, class conditioning và norm có thể thay đổi đáng kể kết luận/ranking giữa calibration methods; fixed bins cũng có bias–variance và cancellation issues. Một paper LLM-judge calibration gần đây cũng dùng ECE nhưng lưu ý metric này nhạy với bin size.

Vì vậy main table của RepGuard nên report cả:

$$
\boxed{\text{Brier}+\text{NLL}+\text{ECE}}
$$

chứ không chỉ ECE.

Tôi khuyên:

$$
M=10
$$

làm main ECE để reliability plot dễ đọc, và supplementary sensitivity:

$$
M\in\{10,15,20,30\}.
$$

Ngoài equal-width ECE, có thể report quantile/adaptive ECE như robustness check; Nixon et al. tìm thấy adaptive binning ổn định hơn trước thay đổi số bins trong các thí nghiệm của họ.

### Mã Python chuẩn hóa

Đây là implementation tôi khuyên dùng cho HistRepEval. Nó dùng trực tiếp binary correctness probability $p=P(z=1)$, đúng với semantics của reputation trong RepGuard:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt


ArrayLike = npt.ArrayLike


def _validate_binary_inputs(
    y_true: ArrayLike,
    y_prob: ArrayLike,
) -> tuple[np.ndarray, np.ndarray]:
    """Validate binary labels and probabilities."""
    y = np.asarray(y_true, dtype=float).reshape(-1)
    p = np.asarray(y_prob, dtype=float).reshape(-1)

    if y.shape != p.shape:
        raise ValueError(
            f"Shape mismatch: y_true={y.shape}, y_prob={p.shape}"
        )

    if y.size == 0:
        raise ValueError("Inputs must not be empty.")

    if not np.all(np.isfinite(y)) or not np.all(np.isfinite(p)):
        raise ValueError("Inputs contain NaN or infinite values.")

    if not np.all((y == 0.0) | (y == 1.0)):
        raise ValueError("y_true must contain only 0/1 labels.")

    if not np.all((0.0 <= p) & (p <= 1.0)):
        raise ValueError("y_prob must lie in [0, 1].")

    return y, p


def brier_score_binary(
    y_true: ArrayLike,
    y_prob: ArrayLike,
) -> float:
    """
    Binary Brier Score:
        mean((p - y)^2)

    Lower is better.
    """
    y, p = _validate_binary_inputs(y_true, y_prob)
    return float(np.mean((p - y) ** 2))


def nll_binary(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    eps: float = 1e-15,
) -> float:
    """
    Mean binary Negative Log-Likelihood.

    Lower is better.
    Probabilities are clipped only for numerical stability.
    """
    y, p = _validate_binary_inputs(y_true, y_prob)

    if not (0.0 < eps < 0.5):
        raise ValueError("eps must lie in (0, 0.5).")

    p = np.clip(p, eps, 1.0 - eps)

    loss = -(
        y * np.log(p)
        + (1.0 - y) * np.log1p(-p)
    )
    return float(np.mean(loss))


@dataclass(frozen=True)
class CalibrationBin:
    lower: float
    upper: float
    count: int
    mean_confidence: float
    empirical_accuracy: float
    absolute_gap: float


def expected_calibration_error(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
    strategy: Literal["uniform", "quantile"] = "uniform",
) -> tuple[float, list[CalibrationBin]]:
    """
    Binary Expected Calibration Error.

    ECE = sum_b (n_b / N) * |acc_b - conf_b|

    strategy="uniform":
        Equal-width probability bins.

    strategy="quantile":
        Approximately equal-frequency bins.

    Returns:
        (ece, bin_statistics)
    """
    y, p = _validate_binary_inputs(y_true, y_prob)

    if n_bins < 2:
        raise ValueError("n_bins must be >= 2.")

    if strategy == "uniform":
        edges = np.linspace(0.0, 1.0, n_bins + 1)

    elif strategy == "quantile":
        edges = np.quantile(
            p,
            np.linspace(0.0, 1.0, n_bins + 1),
        )
        # Repeated probabilities may create duplicate edges.
        edges = np.unique(edges)

        if edges.size < 2:
            # All probabilities are identical: one effective bin.
            accuracy = float(np.mean(y))
            confidence = float(np.mean(p))
            gap = abs(accuracy - confidence)

            one_bin = CalibrationBin(
                lower=float(p[0]),
                upper=float(p[0]),
                count=int(y.size),
                mean_confidence=confidence,
                empirical_accuracy=accuracy,
                absolute_gap=gap,
            )
            return gap, [one_bin]

    else:
        raise ValueError(
            "strategy must be either 'uniform' or 'quantile'."
        )

    # Interior boundaries produce indices 0, ..., n_effective_bins - 1.
    bin_ids = np.searchsorted(
        edges[1:-1],
        p,
        side="right",
    )

    total = y.size
    ece = 0.0
    stats: list[CalibrationBin] = []

    for b in range(len(edges) - 1):
        mask = bin_ids == b
        count = int(np.sum(mask))

        if count == 0:
            continue

        confidence = float(np.mean(p[mask]))
        accuracy = float(np.mean(y[mask]))
        gap = abs(accuracy - confidence)

        ece += (count / total) * gap

        stats.append(
            CalibrationBin(
                lower=float(edges[b]),
                upper=float(edges[b + 1]),
                count=count,
                mean_confidence=confidence,
                empirical_accuracy=accuracy,
                absolute_gap=float(gap),
            )
        )

    return float(ece), stats
```

Brier ở đây sử dụng binary mean-square convention; ECE triển khai đúng weighted bin gap của Guo et al.; mean NLL chỉ khác Eq. tổng của Guo et al. ở normalization $1/N$, để số liệu có thể so sánh giữa test sets khác kích thước. 

Đối với một experiment:

```python
y_true = np.array([1, 1, 0, 1, 0])
reputation_prob = np.array([0.90, 0.70, 0.40, 0.80, 0.20])

bs = brier_score_binary(y_true, reputation_prob)
nll = nll_binary(y_true, reputation_prob)

ece10, bins10 = expected_calibration_error(
    y_true,
    reputation_prob,
    n_bins=10,
    strategy="uniform",
)

ece_quantile, bins_quantile = expected_calibration_error(
    y_true,
    reputation_prob,
    n_bins=5,
    strategy="quantile",
)
```

Semantics phải luôn là:

```text
reputation_prob[i]
    = predicted probability that the agent succeeds
      on this target task / task class

y_true[i]
    = actual offline correctness of that agent-task pair
```

Không nên tính ECE của:

$$
CrS_i
$$

trừ khi bạn **thực sự tuyên bố CrS có probability semantics**. Nếu CrS chỉ là arbitrary influence score thì Brier/NLL trên CrS không có interpretation chuẩn.

## Công thức ECRT hoàn chỉnh tôi khuyên dùng cho RepGuard

Từ toàn bộ phần trên, tôi khuyên formalisation của RepGuard nên được đóng thành pipeline sau. Cách này giữ được câu chuyện proposal hiện tại, đồng thời làm rõ phần nào lấy từ literature và phần nào thực sự là design của ECRT.

### Lớp latent historical correctness

Đối với agent $i$, episode $t$:

$$
z_{it}\in\{0,1\}
$$

là correctness thật.

Online system không được nhìn thấy $z_{it}$ ngoại trừ oracle condition.

Nó chỉ thấy:

$$
F_{it}.
$$

Từ calibrated feedback model:

$$
\boxed{
p_{it}
=
P(z_{it}=1\mid F_{it},\mathcal D_{\mathrm{cal}})
}
$$

Trong binary judge case:

$$
p_{it}
=
\begin{cases}
\dfrac{Se\,\pi}
{Se\,\pi+(1-Sp)(1-\pi)},
&f_{it}=1,\\[12pt]
\dfrac{(1-Se)\pi}
{(1-Se)\pi+Sp(1-\pi)},
&f_{it}=0.
\end{cases}
$$

Đây là layer mà Ebrahimi không có và là nơi RepGuard xử lý imperfect feedback.

### Lớp evidence strength

Định nghĩa:

$$
\boxed{
m_{it}\ge0
}
$$

là effective evidence mass.

Một policy khởi đầu dễ ablate:

$$
m_{it}
=
\begin{cases}
1,&\text{objective verified feedback},\\
m_j,&\text{judge }j,\\
0,&\text{missing feedback}.
\end{cases}
$$

Với judge $j$, một simple discrimination baseline có thể là:

$$
m_j
=
\max(0,Se_j+Sp_j-1).
$$

Nhưng trong paper nên gọi rõ đây là **effective-mass design**, không gán nó cho Ebrahimi/Xia.

Quan trọng nhất:

$$
Se+Sp\approx1
\Rightarrow
m\approx0,
$$

để random judge không làm posterior concentration tăng giả tạo.

### Lớp skill transfer

Mỗi episode có source skill:

$$
k_t.
$$

Target query có target skill:

$$
k^{*}.
$$

Định nghĩa:

$$
\boxed{
\tau_t
=
\tau(k_t,k^{*})\in[0,1].
}
$$

Một baseline trực tiếp theo Xia & Wang:

$$
\tau(k,k)=1,
$$

và:

$$
\tau(k,k')
=
\beta\max(R_{k,k'},0)
$$

cho $k\neq k'$, trong đó $R$ được ước lượng trên held-out/training histories chứ không được dùng target-test outcome để tránh leakage. Công thức adaptive coupling này dựa trên Xia & Wang, nhưng RepGuard nên tính correlation từ calibrated competence statistics thay vì raw untrusted judge outcomes. 

### Zero-evidence gate trong ECRT

Định nghĩa direct target evidence mass:

$$
\boxed{
M^{dir}_{i,k^{*}}
=
\sum_{t:k_t=k^{*}}
m_{it}.
}
$$

Phiên bản chính xác nhất theo Xia & Wang là kiểm tra số direct episode:

$$
g_{i,k^{*}}
=
\mathbf1[n_{i,k^{*}}\ge1].
$$

Nhưng vì RepGuard có feedback reliability, phiên bản tự nhiên hơn là:

$$
\boxed{
g_{i,k^{*}}
=
\mathbf1[M^{dir}_{i,k^{*}}\ge\delta].
}
$$

Sau đó đặt effective transfer:

$$
\boxed{
\tilde\tau_{it}(k^{*})
=
\begin{cases}
1,
&k_t=k^{*},\\[4pt]
g_{i,k^{*}}\tau(k_t,k^{*}),
&k_t\neq k^{*}.
\end{cases}
}
$$

Khi không có direct target evidence đủ mạnh:

$$
g=0,
$$

mọi off-target history bị chặn.

Đây là một improvement quan trọng so với kiểm tra đơn thuần:

$$
n_{i,k^{*}}\ge1,
$$

bởi một episode có judge hoàn toàn vô dụng không nên được coi là evidence đủ để “unlock” borrowing.

### ECRT Beta approximation

Cuối cùng:

$$
\boxed{
\alpha_i(k^{*})
=
\alpha_0
+
\sum_t
\tilde\tau_{it}(k^{*})
m_{it}p_{it}
}
$$

và:

$$
\boxed{
\beta_i(k^{*})
=
\beta_0
+
\sum_t
\tilde\tau_{it}(k^{*})
m_{it}(1-p_{it}).
}
$$

Posterior/pseudo-posterior mean:

$$
\boxed{
\mu_i(k^{*})
=
\frac{
\alpha_i(k^{*})
}{
\alpha_i(k^{*})+\beta_i(k^{*})
}.
}
$$

Variance:

$$
\boxed{
\sigma_i^2(k^{*})
=
\frac{
\alpha_i(k^{*})\beta_i(k^{*})
}{
[\alpha_i(k^{*})+\beta_i(k^{*})]^2
[\alpha_i(k^{*})+\beta_i(k^{*})+1]
}.
}
$$

Đây là nơi RepGuard có lợi thế rõ ràng so với point estimator:

$$
\hat\tau_{i,k}=0.8
$$

không cho biết score đó đến từ 2 hay 200 observations, trong khi Beta state cho biết cả mean lẫn concentration.

### Quy tắc influence

Không nhất thiết dùng mean trực tiếp.

**Posterior mean:**

$$
w_i=\mu_i.
$$

Đơn giản nhất và nên là main baseline.

**Mean minus uncertainty penalty:**

$$
\boxed{
w_i
=
\max(0,\mu_i-\lambda\sigma_i).
}
$$

Cách này đã nằm trong design space của proposal.

Hoặc dùng lower credible bound:

$$
\boxed{
w_i
=
Q_\gamma
\left[
Beta(\alpha_i,\beta_i)
\right],
}
$$

ví dụ lower $5\%$ quantile với:

$$
\gamma=0.05.
$$

Sau đó normalize:

$$
\tilde w_i
=
\frac{w_i}{\sum_jw_j}.
$$

Với multiple-choice answer:

$$
\boxed{
Score(c)
=
\sum_i
\tilde w_i
\mathbf1[a_i=c]
}
$$

và:

$$
\boxed{
\hat c
=
\arg\max_c Score(c).
}
$$

Điều này tạo một scientific pipeline rất sạch:

$$
\boxed{
F_{it}
\rightarrow
p_{it}
\rightarrow
m_{it}
\rightarrow
\tilde\tau_{it}
\rightarrow
(\alpha_i,\beta_i)
\rightarrow
(\mu_i,\sigma_i)
\rightarrow
w_i
\rightarrow
\text{team decision}.
}
$$

Mỗi arrow có một vai trò riêng:

$$
F\rightarrow p
$$

hỏi **“outcome lịch sử thực ra đáng tin là đúng đến đâu?”**

$$
m
$$

hỏi **“signal này có bao nhiêu sức nặng thông tin?”**

$$
\tau
$$

hỏi **“evidence đó liên quan task hiện tại đến đâu?”**

$$
Beta(\alpha,\beta)
$$

hỏi **“sau tất cả evidence, competence và uncertainty là gì?”**

và:

$$
w
$$

hỏi **“belief đó nên được đổi thành influence như thế nào?”**

Đây là cách formalise rõ nhất sự khác biệt khoa học mà RepGuard muốn nhấn mạnh: Ebrahimi et al. cho thấy historical contribution có thể được biến thành credibility nhưng cũng cho thấy judge error có thể làm hỏng quá trình đó; Xia & Wang cho thấy evidence nên condition theo skill và cross-skill borrowing vừa hữu ích vừa tạo reputation-laundering channel, nhưng họ giả định verified outcomes; Beta cho phép lưu competence cùng uncertainty; còn judge confusion modelling biến unreliable feedback thành probabilistic evidence thay vì hard truth. 

Vì vậy, về mặt toán học, claim mạnh và an toàn nhất cho ECRT không phải là “một Beta reputation score mới”, mà là:

$$
\boxed{
\textbf{reputation update}
=
\textbf{feedback inference}
\times
\textbf{evidence strength}
\times
\textbf{task transfer}
}
$$

trước khi historical performance được phép trở thành **current-task influence**. Đây cũng là cách diễn đạt phù hợp nhất với research gap và mô hình ECRT đã được đặt ra trong blueprint RepGuard của bạn.
