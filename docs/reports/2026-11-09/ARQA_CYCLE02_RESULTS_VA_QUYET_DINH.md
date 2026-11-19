# ARQA vòng02 — kết quả và quyết định

> Mới nhất: [strategy V5 và contribution targets](RESEARCH_STRATEGY_V5_VA_CONTRIBUTIONS.md), [triển khai relational V5](RELATIONAL_V5_RESULTS_VA_QUYET_DINH.md). Bước trước là [workspace V4](WORKSPACE_V4_RESULTS_VA_PATH_TIEP.md). Báo cáo ARQA dưới đây giữ nguyên kết quả frozen của vòng02.

Plan `deaee6167f9609bd2f045f46`; registration 2026-11-09T06:59:25.246823+00:00. 288 real responses,24QA/24connected groups. Không phải official ARQA score.

**Primary checklist cross−self: +2.08pp; CI95% [-4.17; +8.33]pp. Gate: FAIL_stop_scale_and_history.**

**Measurement warning:** hậu kiểm phát hiện precision/unit và scope của câu hỏi cần adjudication; xem [phân tích oracle](ARQA_CYCLE02_ORACLE_VA_PATH_TIEP.md). Gate FAIL là quyết định không mở rộng theo protocol này, không chứng minh cross-agent vô ích hoặc mọi số bị chấm sai là lỗi nghiệp vụ thật.

Không thay primary bằng arm có điểm cao nhất. Source/program/parent/config/model/GPU receipt và attempt audit đã kiểm; xem JSON kèm theo.

|Profile / workflow|Đúng số+unit /24|Đúng số /24|Schema valid|Calls/item|Mean workflow tokens (in+out)|Mean serving s/workflow|
|---|---:|---:|---:|---:|---:|---:|
|standard/A|16|18|24|1|1470.9|10.66|
|standard/B|13|14|21|1|1638.4|8.44|
|standard/AA|15|17|24|2|3217.6|18.05|
|standard/BB|16|17|21|2|3575.5|10.74|
|standard/AB|16|18|24|2|3259.2|12.98|
|standard/BA|16|17|22|2|3548.7|17.30|
|checklist/A|15|16|24|1|1571.0|8.05|
|checklist/B|13|14|22|1|1671.3|2.92|
|checklist/AA|14|14|24|2|3447.8|16.26|
|checklist/BB|16|17|22|2|3630.3|5.26|
|checklist/AB|15|16|24|2|3481.8|10.27|
|checklist/BA|16|17|22|2|3604.4|11.53|

Hai profiles dùng cùng output schema và checker; checklist được cấp cả direct/self/cross. Self/cross có cùng call/token ceilings, nhưng token thực khác nhau. Direct1call là baseline thấp chi phí, không dùng để nhận matched-cost gain. Serving seconds là số đo request tại Ollama, không là thời gian người dùng hay USD billing.

- Secondary standard: +2.08pp, CI95% [-4.17; +10.42]pp.
- Secondary interaction: +0.00pp, CI95% [-10.42; +10.42]pp.
- Checklist cross so self: 2rescues, 1harms, rescue trên2groups.
- Tổng counters corpus: 436,254input / 77,670output tokens, không phải hóa đơn. Schema validity 95.14%; length stops 1.

## Kiểm cơ học không đủ làm semantic verification

Diagnostic final-dependency được thêm sau registration, giữ riêng score frozen. Nó bỏ program có source reads không ảnh hưởng kết quả cuối. Kể cả PASS vẫn có thể sai metric/formula/unit; các risk dưới đây chỉ so numeric/unit gold, không phải risk nghiệp vụ đã adjudicate. Không so risk giữa coverage khác nhau để kết luận thắng.

|Profile / workflow|Final-dependency filter nhận /24|Sai số+unit trong phần nhận|
|---|---:|---:|
|standard/A|24|8|
|standard/B|14|2|
|standard/AA|23|8|
|standard/BB|18|2|
|standard/AB|22|7|
|standard/BA|19|3|
|checklist/A|21|6|
|checklist/B|15|2|
|checklist/AA|19|5|
|checklist/BB|19|3|
|checklist/AB|21|6|
|checklist/BA|20|4|

## Giới hạn và bước tiếp

24groups nhỏ, một issuer, hai họ quantized model, nguồn bảng oracle sẵn; không có retrieval evaluation hoặc company transfer. Chưa có human semantic adjudication;0người dùng,0interviews. Oracle nguồn và decimal rounding được audit trước selection; vẫn có thể thiếu thẩm định diễn giải câu hỏi. Cùng schema không chứng minh cùng năng lực model.

Giữ gate đã khóa. Nếu FAIL: dừng scale/history cho bank này; xem các lỗi và semantic oracle, không chọn lại metric/subset. Nếu GO: vẫn cần human adjudication, stronger single và confirmation độc lập trước claim hiệu quả. [Path kế tiếp](GAP_RECHECK_VA_CONFIRMATION_PATH.md) và [phiếu review](SOURCE_RECEIPT_VA_HUMAN_REVIEW.md).

## Case review: tất cả24câu, hậu nghiệm

Chỉ phục vụ phân tích lỗi; không làm lại selection hoặc đổi gold theo model. Raw outputs nằm trong thư mục results cùng plan, không tái phát hành nguồn theo mặc định.

### 1. 718ffb9493

What was the total number of units sold across all models in 2019?

standard: A=1, B=1, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=1, AA=0, BB=1, AB=1, BA=1

### 2. f003fe0f98

What was the percentage change in Sales revenue from 2017 to 2018?

standard: A=1, B=1, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=1, AA=1, BB=0, AB=1, BA=1

### 3. dd0e3b2ebf

Calculate the percentage decline in Volkswagen Group's total vehicle deliveries compared to 2019.

standard: A=0, B=0, AA=0, BB=0, AB=0, BA=0; checklist: A=0, B=0, AA=0, BB=0, AB=0, BA=0

### 4. 38902f6191

What was the percentage change in Noncurrent assets from Dec. 31, 2017 to Dec. 31, 2018?

standard: A=1, B=1, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=1, AA=1, BB=1, AB=1, BA=1

### 5. bbe603cb82

What is the total authorized volume of bonds issued by Volkswagen in 2020?

standard: A=1, B=1, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=1, AA=1, BB=1, AB=1, BA=1

### 6. b942b4f982

Determine the percentage point change in Audi's operating return on sales before special items between 2019 and 2020.

standard: A=1, B=1, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=1, AA=1, BB=1, AB=1, BA=1

### 7. a92703c96b

What was the percentage change in the price of the Ordinary share from its low on Mar. 18 to its closing price on Dec. 30?

standard: A=1, B=0, AA=1, BB=1, AB=1, BA=1; checklist: A=0, B=0, AA=0, BB=1, AB=0, BA=1

### 8. 370f7b0b07

What was the percentage change in total deliveries for ŠKODA from 2018 to 2019?

standard: A=1, B=0, AA=0, BB=1, AB=1, BA=1; checklist: A=1, B=0, AA=1, BB=1, AB=1, BA=1

### 9. cf12fca083

What was the percentage change in 'Customer financing' from 2017 to 2018?

standard: A=0, B=0, AA=0, BB=0, AB=0, BA=0; checklist: A=0, B=0, AA=0, BB=0, AB=0, BA=0

### 10. c2fcfb3928

What is the variance between the actual value contribution and the target cost of capital in 2015?

standard: A=1, B=0, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=0, AA=1, BB=1, AB=1, BA=0

### 11. 7476bc2acc

What is the difference in Net cash flow between 2018 and 2017?

standard: A=1, B=1, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=1, AA=1, BB=1, AB=1, BA=1

### 12. a660204d2b

Calculate the percentage growth in SEAT's vehicle production from 2017 to 2018.

standard: A=0, B=0, AA=0, BB=1, AB=0, BA=0; checklist: A=0, B=1, AA=0, BB=1, AB=0, BA=1

### 13. 4dfc8f2ff3

What is the difference in Sales revenue (€ million) between 2017 and 2016?

standard: A=1, B=1, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=1, AA=1, BB=1, AB=1, BA=1

### 14. 212f007e27

What was the percentage change in deliveries (thousand units) from 2020 to 2021?

standard: A=1, B=1, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=1, AA=1, BB=1, AB=1, BA=1

### 15. eebf1250e1

What is the difference between the Research and development ratio (R&D ratio) and Capex/sales revenue in the Automotive Division?

standard: A=0, B=0, AA=0, BB=0, AB=0, BA=0; checklist: A=1, B=0, AA=1, BB=0, AB=1, BA=0

### 16. bbfdf7bf37

What is the ratio of research and development (R&D) expenses to sales revenue in the Automotive Division?

standard: A=0, B=0, AA=0, BB=0, AB=0, BA=0; checklist: A=0, B=0, AA=0, BB=0, AB=0, BA=0

### 17. f795ec592b

What was the total number of units sold across all models in 2015?

standard: A=0, B=0, AA=0, BB=0, AB=0, BA=0; checklist: A=0, B=0, AA=0, BB=0, AB=0, BA=0

### 18. 4f219c93b0

What was the percentage change in sales revenue for the South America region from 2015 to 2016?

standard: A=1, B=1, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=1, AA=1, BB=1, AB=1, BA=1

### 19. 1325b18bfb

What is the total sales revenue of all segments in the Volkswagen Group?

standard: A=0, B=0, AA=0, BB=0, AB=0, BA=0; checklist: A=0, B=0, AA=0, BB=0, AB=0, BA=0

### 20. 8e3eb87ea6

What was the percentage increase in Trucks production from 2016 to 2017?

standard: A=1, B=1, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=1, AA=1, BB=1, AB=1, BA=1

### 21. a0a3f4a7bf

By how many percentage points did the Operating return on sales change from 2018 to 2019?

standard: A=1, B=1, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=1, AA=1, BB=1, AB=1, BA=1

### 22. 0f29441c45

Calculate the percentage change in Bentley's vehicle production from 2015 to 2016.

standard: A=0, B=0, AA=0, BB=0, AB=0, BA=0; checklist: A=0, B=0, AA=0, BB=0, AB=0, BA=0

### 23. d5a035f3d1

What was the percentage change in the number of Trucks sold from 2016 to 2017?

standard: A=1, B=1, AA=1, BB=0, AB=1, BA=1; checklist: A=0, B=0, AA=0, BB=1, AB=0, BA=1

### 24. 84a076bf13

What is the total authorized volume of all programs in € billion?

standard: A=1, B=1, AA=1, BB=1, AB=1, BA=1; checklist: A=1, B=1, AA=1, BB=1, AB=1, BA=1

