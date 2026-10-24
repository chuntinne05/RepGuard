# TAT-QA: gói review nguồn độc lập, ALL24 contexts

Không có đáp án tham chiếu, model outputs hoặc tên method trong gói này.
Hai người review riêng, chưa xem traces/flags; bất đồng nhờ người thứ ba phân xử.
Chưa có review nào được hoàn tất. Không chỉ chọn các case model sai.

Mỗi case ghi: requested metric/entity; period/scope; signs; input quantities và source coordinates; đơn vị được nguồn hỗ trợ; precision; formula; numeric answer và scale; alternate acceptable readings; ambiguity hoặc evidence missing.
Đánh giá nguồn trước, chỉ mở annotations/model outputs sau khi khóa review. Không buộc phải đoán đơn vị khi extract không đủ thông tin.

Chú ý phân biệt source token tồn tại với việc token đúng metric, năm, đơn vị hoặc phạm vi câu hỏi. Không nhận dạng một multiplier chỉ bằng cảm giác về độ lớn số tiền.

---

## Case 1: 3a302dbd-03bf-444b-8f1f-dcf7607e2665
Context UID: 561fe226-ca88-4341-a8a6-5bd33ee1ded4
**Question:** What is the gross profit margin in 2019?

**Table (original row order):**

|row|C0|C1|C2|C3|
|---|---|---|---|---|
|T0|||Fiscal year||
|T1|(in millions of €)|2019|2018|% Change|
|T2|Revenue|22,104|28,185|(22) %|
|T3|Cost of Sales|(15,825)|(21,074)|25 %|
|T4|Gross profit|6,279|7,111|(12) %|
|T5|as percentage of revenue|28 %|25 %||
|T6|Research and development expenses|(2,362)|(2,788)|15 %|
|T7|Selling and general administrative expenses|(3,979)|(3,767)|(6) %|
|T8|Other operating income (expenses), net|9,469|1|n / a|
|T9|Financial income, net thereof Income from investments, net 3,754 (prior year 5,381)|3,188|4,643|(31) %|
|T10|Income from business activity|12,596|5,199|142 %|
|T11|Income taxes|(1,377)|(653)|(111) %|
|T12|Net income|11,219|4,547|147 %|
|T13|Profit carried forward|170|134|27 %|
|T14|Allocation to other retained earnings|(6,005)|(1,451)|> (200) %|
|T15|Unappropriated net income|5,384|3,230|67 %|

**Paragraphs:**

P0 (original order 1): A.9.1 Results of operations

P1 (original order 2): Statement of Income of Siemens AG in accordance with German Commercial Code (condensed)

P2 (original order 3): Beginning of August 2018, Siemens AG carved out its mobility business to Siemens Mobility GmbH by way of singular succession. The decreases in revenue, cost of sales, gross profit and research and development (R & D) expenses were mainly driven by this carve-out.

P3 (original order 4): On a geographical basis, 75 % of revenue was generated in the Europe, C. I. S., Africa, Middle East region, 18 % in the Asia, Australia region and 7 % in the Americas region. Exports from Germany accounted for 62 % of overall revenue. In fiscal 2019, orders for Siemens AG amounted to € 21.6 billion. Within Siemens AG, the development of revenue depends strongly on the completion of contracts, primarily in connection with large orders.

P4 (original order 5): The R & D intensity (R & D as a percentage of revenue) increased by 0.8 percentage points year-over-year. The research and development activities of Siemens AG are fundamentally the same as for its fields of business activities within the Siemens Group, respectively. On an average basis, we employed 9,000 people in R & D in fiscal 2019.

P5 (original order 6): The decrease in Financial income, net was primarily attributable to lower income from investments, net. The main factor for this decrease was a significant income from the profit transfer agreement with Siemens Beteiligungen Inland GmbH, Germany, in
fiscal 2018.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 2: 28958656-bd4d-417e-8c1e-3f07488a45aa
Context UID: 78750ee7-2ac6-4ad5-a14c-406057cc731e
**Question:** What is the average total cost of revenue between 2017 to 2019?

**Table (original row order):**

|row|C0|C1|C2|C3|C4|C5|C6|C7|C8|
|---|---|---|---|---|---|---|---|---|---|
|T0||Year ended December 31,||||Year ended December 31,||||
|T1|(in thousands, except percentages)|2019|2018|$ Change|% Change|2018|2017|$ Change|% Change|
|T2|Cost of revenues|||||||||
|T3|Subscriptions|$160,320|$109,454|$50,866|46%|$109,454|$89,193|$20,261|23%|
|T4|Other|70,723|47,675|23,048|48%|47,675|32,078|15,597|49%|
|T5|Total cost of revenues|$231,043|$157,129|$73,914|47%|$157,129|$121,271|$35,858|30%|
|T6|Percentage of revenues|||||||||
|T7|Subscriptions|18%|16%|||16%|18%|||
|T8|Other|8%|7%|||7%|6%|||
|T9|Gross margins|||||||||
|T10|Subscriptions|80%|82%|||82%|81%|||
|T11|Other|17%|22%|||22%|16%|||
|T12|Total gross margin %|74%|77%|||77%|76%|||

**Paragraphs:**

P0 (original order 1): Cost of Revenues and Gross Margin

P1 (original order 2): Subscription cost of revenues and gross margin. Cost of subscriptions revenues increased by $50.9 million, or 46%, during fiscal year 2019 as compared to fiscal year 2018. Primary drivers of the increase were increases in third-party costs to support our solution offerings of $21.5 million, infrastructure support costs of $19.8 million including amortization expense from acquired intangible assets, and headcount and personnel and contractor related costs of $9.6 million including share-based compensation expense. These factors resulted in a decrease in gross margin.

P2 (original order 3): The increase in headcount and other expense categories described herein was driven primarily by investments in our infrastructure and capacity to improve the availability of our subscription offerings, while also supporting the growth in new customers and increased usage of our subscriptions by our existing customer base. We expect subscription gross margin to be within a relatively similar range in the future.

P3 (original order 4): Other cost of revenues and gross margin. Cost of other revenues increased by $23.0 million, or 48%, during fiscal year 2019 as compared to fiscal year 2018. This was primarily due to the increase in services personnel costs of $11.1 million including share-based compensation expense, cost of product sales of $10.6 million, and overhead costs of $1.3 million. Other revenues gross margin fluctuates based on timing of completion of professional services projects and discounting on phones.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 3: 2cc3d001-3758-41f6-9608-b034ea56c464
Context UID: 7cd3bc97-89ad-4cd2-a067-bcb994bf29e1
**Question:** What was the change in the Total operating expenses as a percentage of net revenues between 2018 and 2019?

**Table (original row order):**

|row|C0|C1|C2|C3|
|---|---|---|---|---|
|T0|||Year Ended ||
|T1||June 30, 2019|June 30,2018|June 30, 2017|
|T2|Research and development  |21.1%|18.7%|15.4%|
|T3|Sales and marketing  |28.7%|27.2%|26.8%|
|T4|General and administrative  |5.6%|5.2%|6.2%|
|T5|Acquisition and integration costs, net of bargain purchase gain  |0.3%|5.5%|2.2%|
|T6|Restructuring charges, net of reversals  |0.5%|0.8%|1.5%|
|T7|Amortization of intangibles  |0.6%|0.9%|1.4%|
|T8|Total operating expenses|56.8%|58.3%|53.5%|
|T9|Operating (loss) income  |(1.5)%|(3.9)%|1.0%|

**Paragraphs:**

P0 (original order 1): Operating Expenses

P1 (original order 2): The following table highlights our operating expenses and operating loss as a percentage of net revenues:

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 4: 6349e186-e6e7-40bf-98da-6a7592ea798c
Context UID: 7ac100f5-8d0a-4fb1-ad1b-6e5eebb4d3fa
**Question:** What was the change in TCE earnings in 2019 from 2018?

**Table (original row order):**

|row|C0|C1|C2|C3|
|---|---|---|---|---|
|T0|USDm|2019|2018|2017|
|T1|Reconciliation to revenue||||
|T2|Revenue|692.6|635.4|657.0|
|T3|Port expenses, bunkers and commissions|-267.7|-283.0|-259.9|
|T4|TCE earnings|424.9|352.4|397.1|

**Paragraphs:**

P0 (original order 1): ALTERNATIVE PERFORMANCE MEASURES

P1 (original order 2): Time Charter Equivalent (TCE) earnings:

P2 (original order 3): TORM defines TCE earnings, a performance measure, as revenue after port expenses, bunkers and commissions incl. freight and bunker derivatives. The Company reports TCE earnings because we believe it provides additional meaningful information to investors in relation to revenue, the most directly comparable IFRS measure. TCE earnings is a standard shipping industry performance measure used primarily to compare period-to-period changes in a shipping company’s performance irrespective of changes in the mix of charter types (i.e. spot charters, time charters and bareboat charters) under which the vessels may be employed between the periods. Below is presented a reconciliation from Revenue to TCE earnings:

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 5: 7d8beb14-2862-4b15-9102-145f245a78b3
Context UID: 92a7e213-d030-466e-87d4-1189609d7152
**Question:** What is the percentage change in total Number of Shares Purchased as part of a Publicly Announced Program from November to December 2019?

**Table (original row order):**

|row|C0|C1|C2|C3|C4|
|---|---|---|---|---|---|
|T0|Period|Total Number of Shares Repurchased|Average Price Paid per Share|Total Number of Shares Purchased as part of a Publicly Announced Program|Maximum Dollar Value of shares that may yet be purchased under the Repurchase Program|
|T1|October 1, 2019 through October 31, 2019|-|-|- -|$12,544,543|
|T2|November 1, 2019 through November 30, 2019|274,681|$4.82|191,354|$11,620,641|
|T3|December 1, 2019 through December 31, 2019|374,490|$4.70|374,490|$9,859,153|
|T4|Total shares repurchased|649,171|$4.75|565,844|$9,859,153|

**Paragraphs:**

P0 (original order 1): Net Settlement of Equity Awards

P1 (original order 2): The majority of restricted stock units are subject to vesting. The underlying shares of common stock are issued when the restricted stock units vest. The majority of participants choose to participate in a broker-assisted automatic sales program to satisfy their applicable tax withholding requirements. We do not treat the shares sold pursuant to this automatic sales program as common stock repurchases.

P2 (original order 3): In the fourth quarter of 2019, we withheld 83,327 shares through net settlements (where the award holder receives the net of the shares vested, after surrendering a portion of the shares back to the Company for tax withholding) for restricted stock units that vested for some of our executive officers.

P3 (original order 4): The following table provides a summary of the Company’s repurchase of common stock under the Repurchase Program and shares surrendered back to the Company for tax withholding on restricted stock units that vested under our equity incentive programs in the three months ended December 31, 2019:

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 6: 03c81011-5165-439a-ac47-4ec9cc33e967
Context UID: bf05ad69-e3db-420f-a2fe-dfd6615dc336
**Question:** What is the current liability to current assets ratio for 2019?

**Table (original row order):**

|row|C0|C1|C2|
|---|---|---|---|
|T0||December 31,||
|T1|(HK$ million)|2018|2019|
|T2|Current assets|15,168|13,381|
|T3|Non-current assets|5,907|7,464|
|T4|Current liabilities|7,792|4,432|
|T5|Non-current liabilities|1,122|4,781|
|T6|Equity|12,161|11,632|

**Paragraphs:**

P0 (original order 1): Summarized 100% statement of financial position information for ASMPT equity method investment excluding basis adjustments (foreign currency exchange rate per December 31, 2019 was 1 HK$: €0.11432 for December 31, 2018: 1 HK$: €0.11151).

P1 (original order 2): Equity of ASMPT per December 31, 2019 translated into euros at a rate of 0.11432 was €1,329 million (our 25.19% share: €335 million).

P2 (original order 3): The ASMPT Board is responsible for ongoing monitoring of the performance of the Back-end activities. The actual results of the Back-end operating unit are discussed with the ASMPT Audit Committee, which includes the representative of ASMI. The ASMI representative reports to the ASMI Management Board and the Audit Committee of ASMI on a quarterly basis.

P3 (original order 4): Our share of income taxes incurred directly by the associates is reported in result from investments in associates and as such is not included in income taxes in our consolidated financial statements.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 7: 457ddbe2-9555-4eba-a91c-89a3cdc32054
Context UID: 39b6adb3-0c5b-478c-8835-ce519ed08be1
**Question:** What was the difference between domestic and international deferred tax assets?

**Table (original row order):**

|row|C0|C1|C2|C3|
|---|---|---|---|---|
|T0||||December 31, 2019|
|T1|(In thousands)|Deferred Tax Assets|Valuation Allowance|Deferred Tax Assets, net|
|T2|Domestic|$46,266|$(46,266)|$ —|
|T3|International|9,911|(2,350)|7,561|
|T4|Total|$56,177|$(48,616)|$7,561|

**Paragraphs:**

P0 (original order 1): The Company continually reviews the adequacy of our valuation allowance and recognizes the benefits of deferred tax assets only as the reassessment indicates that it is more likely than not that the deferred tax assets will be realized in accordance with ASC 740, Income Taxes. Due to our recent decrease in revenue and profitability for 2019, and all other positive and negative objective evidence considered as part of our analysis, our ability to consider other subjective evidence such as projections for future growth is limited when evaluating whether our deferred tax assets will be realized. As such, the Company was no longer able to conclude that it was more likely than not that our domestic deferred tax assets would be realized and a valuation allowance against our domestic deferred tax assets was established in the third quarter of 2019. The amount of the deferred tax assets considered realizable may be adjusted in future periods in the event that sufficient evidence is present to support a conclusion that it is more likely than not that all or a portion of our domestic deferred tax assets will be realized.

P1 (original order 2): As of December 31, 2019, the Company had gross deferred tax assets totaling $56.2 million offset by a valuation allowance totaling $48.6 million. Of the valuation allowance, $42.8 million was established in the current year primarily related to our domestic deferred tax assets. The remaining $5.8 million established in prior periods related to state research and development credit carryforwards and foreign net operating loss and research and development credit carryforwards where we lack sufficient activity to realize those deferred tax assets. The remaining $7.6 million in deferred tax assets that were not offset by a valuation allowance are located in various foreign jurisdictions where the Company believes it is more likely than not we will realize these deferred tax assets.

P2 (original order 3): Supplemental balance sheet information related to deferred tax assets is as follows:

P3 (original order 4): As of December 31, 2019 and 2018, the deferred tax assets for foreign and domestic loss carry-forwards, research and development tax credits, unamortized research and development costs and state credit carryforwards totaled $41.3 million and $28.8 million, respectively. As of December 31, 2019, $19.1 million of these deferred tax assets will expire at various times between 2020 and 2039. The remaining deferred tax assets will either amortize through 2029 or carryforward indefinitely.

P4 (original order 5): As of December 31, 2019 and 2018, respectively, our cash and cash equivalents were $73.8 million and $105.5 million and short-term investments were $33.2 million and $3.2 million, which provided available short-term liquidity of $107.0 million and $108.7 million. Of these amounts, our foreign subsidiaries held cash of $52.3 million and $87.1 million, respectively, representing approximately 48.9% and 80.1% of available short-term liquidity, which is used to fund on-going liquidity needs of these subsidiaries. We intend to permanently reinvest these funds outside the U.S. except to the extent any of these funds can be repatriated without withholding tax and our current business plans do not indicate a need to repatriate to fund domestic operations. However, if all of these funds were repatriated to the U.S. or used for U.S. operations, certain amounts could be subject to tax. Due to the timing and circumstances of repatriation of such earnings, if any, it is not practical to determine the amount of funds subject to unrecognized deferred tax liability.

P5 (original order 6): During 2019, 2018 and 2017, no income tax benefit or expense was recorded for stock options exercised as an adjustment to equity.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 8: 2817d850-d1d8-4851-b2b1-6bb98aa7d1c1
Context UID: c501a508-4205-4046-a1b2-bc1d0baa25e3
**Question:** What was the percentage change in the Average invested capital for the year in 2019 from 2018?

**Table (original row order):**

|row|C0|C1|C2|C3|
|---|---|---|---|---|
|T0|USDm|2019|2018|2017|
|T1|Operating profit/(loss) (EBIT)|205.9|2.8|39.5|
|T2|Tax|-0.8|-1.6|-0.8|
|T3|EBIT less Tax|205.1|1.2|38.7|
|T4|Invested capital, opening balance|1,469.4|1,406.0|1,387.7|
|T5|Invested capital, ending balance|1,786.0|1,469.4|1,406.0|
|T6|Average invested capital for the year|1,627.7|1,437.7|1,396.9|
|T7|Return on Invested Capital (RoIC)|12.6%|0.1%|2.8%|

**Paragraphs:**

P0 (original order 1): ALTERNATIVE PERFORMANCE MEASURES – continued

P1 (original order 2): Return on Invested Capital (RoIC): TORM defines RoIC as earnings before interest and tax (EBIT) less tax, divided by the average invested capital for the period. Invested capital is defined below.

P2 (original order 3): RoIC expresses the returns generated on capital invested in the Group. The progression of RoIC is used by TORM to measure progress against our longer-term value creation goals outlined to investors. RoIC is calculated as follows:

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 9: bc43b597-d752-448b-924d-21543a3880ec
Context UID: ef2d3a03-1c94-48d9-a299-0ed831ca9033
**Question:** What was the percentage change in the Amortization of contract assets between 2018 and 2019?

**Table (original row order):**

|row|C0|C1|C2|
|---|---|---|---|
|T0||Year Ended December 31,||
|T1||2019|2018|
|T2|Beginning of period balance|$2,881|$—|
|T3|Commission costs and upfront payments to a customer capitalized in period|4,141|4,864|
|T4|Amortization of contract assets|(2,444)|(1,983)|
|T5|End of period balance|$4,578|$2,881|

**Paragraphs:**

P0 (original order 1): Note 3. Revenue from Contracts with Customers

P1 (original order 2): Contract Assets

P2 (original order 3): Our contract assets consist of capitalized commission costs and upfront payments made to customers. The current portion of capitalized commission costs and upfront payments made to customers are included in other current assets within our consolidated balance sheets. The non-current portion of capitalized commission costs and upfront payments made to customers are reflected in other assets within our consolidated balance sheets. Our amortization of contract assets during the years ended December 31, 2019 and 2018 were $2.4 million and $2.0 million, respectively. There were no amortized commission costs during the year ended December 31, 2017.

P3 (original order 4): We review the capitalized costs for impairment at least annually. Impairment exists if the carrying amount of the asset recognized from contract costs exceeds the remaining amount of consideration we expect to receive in exchange for providing the goods and services to which such asset relates, less the costs that relate directly to providing those good and services and that have not been recognized as an expense. We did not record an impairment loss on our contract assets during the years ended December 31, 2019, 2018 and 2017.

P4 (original order 5): The changes in our contract assets are as follows (in thousands):

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 10: ad442ff4-97f8-404c-a802-55f1643e2583
Context UID: 76876135-8215-48de-baa3-509a79978bc1
**Question:** What is the sum of company's total assets between 2018 to 2019?

**Table (original row order):**

|row|C0|C1|C2|
|---|---|---|---|
|T0|||As of December 31,|
|T1|(dollars in millions)|2019|2018|
|T2|Assets|||
|T3|Entertainment and Communications|$1,840.0|$1,898.8|
|T4|IT Services and Hardware|500.7|468.1|
|T5|Corporate and eliminations|313.1|363.3|
|T6|Total assets|$2,653.8|$2,730.2|

**Paragraphs:**

P0 (original order 1): Total assets for the Company decreased $76.4 million as of December 31, 2019 as compared to December 31, 2018.  Entertainment and Communications assets decreased $58.8 million due to a decrease in property, plant and equipment primarily as a result of the increased depreciation in 2019 related to Hawaiian Telcom property, plant and equipment exceeding capital expenditures. IT Services and Hardware assets increased by $32.6 million primarily due to the Company’s recognition of operating lease right-of-use assets in the Consolidated Balance Sheets upon adoption of ASU 2016-02.

P1 (original order 2): Corporate assets decreased $50.2 million primarily due to decreased receivables. Lower receivables is partially due to timing of sales in the fourth quarter as well as additional sales of certain receivables under the factoring arrangement as of December 31, 2019 compared to December 31, 2018. Deferred tax assets and liabilities totaled $59.3 million and $11.7 million as of December 31, 2019, respectively. Deferred tax assets and liabilities totaled $47.5 million and $11.4 million as of December 31, 2018, respectively. The increase in deferred tax assets in 2019, as compared to 2018, is due to increased net operating losses in 2019.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 11: c4328c5f-8793-49a9-9a4d-b0be3930dbfa
Context UID: bcecd963-c5f2-4b02-a539-bac5bb367bfc
**Question:** What was the percentage change in Debt principal from 2018 to 2019?

**Table (original row order):**

|row|C0|C1|C2|
|---|---|---|---|
|T0||December 31, 2019|December 31, 2018|
|T1||(in thousands)||
|T2|Debt principal|$460,000|$460,000|
|T3|Unamortized discount|65,313|80,019|
|T4|Net carrying amount of convertible debt|$394,687|$379,981|

**Paragraphs:**

P0 (original order 1): The below tables represents the key components of Teradyne’s convertible senior notes:

P1 (original order 2): As of December 31, 2019, the unamortized discount was $65.3 million, which will be amortized over four years using the effective interest rate method. The carrying amount of the equity component was $100.8 million. As of December 31, 2019, the conversion price was approximately $31.62 per share and if converted the value of the notes was $992.0 million.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 12: 6acd42cd-49ad-480e-9b6d-8ddc8e15fe0c
Context UID: cbd56a8f-e345-4460-9399-5e7de8af6173
**Question:** What is the increase / (decrease) in the EMEA revenue from 2018 to 2019?

**Table (original row order):**

|row|C0|C1|C2|C3|C4|C5|
|---|---|---|---|---|---|---|
|T0|||Three Months Ended||% Variation||
|T1||December 31, 2019|September 29, 2019|December 31, 2018|Sequential|Year-Over-Year|
|T2||||(Unaudited, in millions)|||
|T3|EMEA|$538|$549|$617|(2.0)%|(12.8)%|
|T4|Americas|360|326|342|10.5|5.4|
|T5|Asia Pacific|1,856|1,678|1,689|10.6|9.9|
|T6|Total|$2,754|$2,553|$2,648|7.9%|4.0%|

**Paragraphs:**

P0 (original order 1): By region of shipment, in the 2019 fourth quarter, Asia Pacific revenues grew sequentially by 10.6%, principally in Imaging, Analog and Microcontrollers, Americas was up by 10.5%, mainly driven by Digital and Power Discrete, and EMEA decreased by 2.0%.

P1 (original order 2): On a year-over-year basis, revenues grew 9.9% in Asia Pacific, mainly due to Analog, Microcontrollers and Imaging. In Americas, revenues grew 5.4%, mainly driven by Digital and Power Discrete, while it decreased by 12.8% in EMEA, mainly due to lower sales in Automotive, Power Discrete and  analog.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 13: b432b2c4-d9c6-4e7d-90ef-b128d5fa5728
Context UID: 20df23bb-3d0e-4d2e-8d54-cf05b3852cfc
**Question:** What was the increase / (decrease) in the Foreign currency transaction losses/(gains) from 2018 to 2019?

**Table (original row order):**

|row|C0|C1|C2|C3|
|---|---|---|---|---|
|T0|($ in millions)||||
|T1|For the year ended December 31:|2019|2018|Yr.-to-Yr. Percent Change|
|T2|Other (income) and expense||||
|T3|Foreign currency transaction losses/(gains)|$(279)|$(427)|(34.6)%|
|T4|(Gains)/losses on derivative instruments|15|434|(96.6)|
|T5|Interest income|(349)|(264)|32.2|
|T6|Net (gains)/losses from securities and investment assets|(32)|(101)|(67.9)|
|T7|Retirement-related costs/(income)|615|1,572|(60.9)|
|T8|Other|(937)|(63)|NM|
|T9|Total consolidated other (income) and expense|$(968)|$1,152|NM|
|T10|Non-operating adjustments||||
|T11|Amortization of acquired intangible assets|(2)|(2)|50.0%|
|T12|Acquisition-related charges|154|0|NM|
|T13|Non-operating retirement related costs/(income)|(615)|(1,572)|(60.9)%|
|T14|Operating (non-GAAP) other (income) and expense|$(1,431)|$(422)|239.4%|

**Paragraphs:**

P0 (original order 1): Other (Income) and Expense

P1 (original order 2): NM—Not meaningful

P2 (original order 3): Total consolidated other (income) and expense was income of $968 million in 2019 compared to expense of $1,152 million in 2018. The year-to-year change was primarily driven by: • Lower non-operating retirement-related costs ($957 million). Refer to “Retirement-Related Plans” for additional information. • Higher gains from divestitures ($833 million) reflected in Other; and • Higher net exchange gains (including derivative instruments) ($272 million). The company’s hedging programs help mitigate currency impacts in the Consolidated Income Statement.

P3 (original order 4): Operating (non-GAAP) other (income) and expense was $1,431 million of income in 2019 and increased $1,010 million compared to the prior-year period. The year-to-year change was primarily driven by the same factors excluding lower non-operating retirement-related costs.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 14: 8dc98f36-0579-49bc-83b5-be5a74d41908
Context UID: b29f8e9b-790c-48fc-aede-96bc09bf8054
**Question:** What was the percentage change in total employee costs in 2019 from 2018?

**Table (original row order):**

|row|C0|C1|C2|
|---|---|---|---|
|T0||Year-ended 31 March 2019|Year-ended 31 March 2018 Restated See note 2|
|T1||$M|$M|
|T2|Wages and salaries|286.0|271.8|
|T3|Social security costs|25.6|27.3|
|T4|Pension costs|8.9|8.4|
|T5|Other costs|12.7|12.1|
|T6||333.2|319.6|
|T7|Share-based payments (see note 29)|36.9|42.3|
|T8|Total employee costs|370.1|361.9|

**Paragraphs:**

P0 (original order 1): 11 Employee Costs

P1 (original order 2): Included in wages and salaries above are $4.2M (2018: $4.0M) relating to retention payments arising on business combinations.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 15: 2ba67b9a-9cf8-466f-81cc-b3cf0e3bec49
Context UID: fe1ea22e-46a1-4cee-ad55-a16b6e74739d
**Question:** What was the average Gross increases for tax positions of current year for 2017-2019?

**Table (original row order):**

|row|C0|C1|C2|C3|
|---|---|---|---|---|
|T0|||Years Ended December 31,||
|T1||2019|2018|2017|
|T2|Balance at beginning of year|$4,611|$4,672|$6,232|
|T3|Gross increases for tax positions of prior years|394|—|—|
|T4|Gross decreases for federal tax rate change for tax positions of prior years|—|—|(1,670)|
|T5|Gross increases for tax positions of current year|34|45|110|
|T6|Lapse of statute of limitations|(213)|(106)|—|
|T7|Balance at end of year|$4,826|4,611|4,672|

**Paragraphs:**

P0 (original order 1): The Company maintains liabilities for uncertain tax positions. These liabilities involve considerable judgment and estimation and are continuously monitored by management based on the best information available, including changes in tax regulations, the outcome of relevant court cases, and other information. A reconciliation of the beginning and ending amount of gross unrecognized tax benefits is as follows (in thousands):

P1 (original order 2): The unrecognized tax benefits relate primarily to federal and state research and development credits and intercompany profit on the transfer of certain IP rights to one of the Company’s foreign subsidiaries as part of the Company’s tax reorganization completed in 2015. The Company’s policy is to account for interest and penalties related to uncertain tax positions as a component of income tax expense. As of December 31, 2019, the Company accrued interest or penalties related to uncertain tax positions in the amount of $25,000. As of December 31, 2019, the total amount of unrecognized tax benefits that would affect the Company’s effective tax rate, if recognized, is $97,000.

P2 (original order 3): Because the Company has net operating loss and credit carryforwards, there are open statutes of limitations in which federal, state and foreign taxing authorities may examine the Company’s tax returns for all years from 2000 through the current period.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 16: de92ddd9-a57d-4b3f-8995-02e309da9ee5
Context UID: 5db485cf-6c57-4869-8065-14e334b4b733
**Question:** What is the percentage change in Total number of shares purchased between January 2019 and February 2019?

**Table (original row order):**

|row|C0|C1|C2|C3|C4|
|---|---|---|---|---|---|
|T0||Total Number of Shares Purchased|Average Price Paid per Share (1)|Total Number of Shares Purchased as Part of Publicly Announced Plans or Programs|Approximate Dollar Value of Shares that may be Purchased Under the Plans or Programs (2)|
|T1|December 1 - December 31, 2018|75,000|$12.96|75,000|$19,028,173|
|T2|January 1 - January 31, 2019|524,577|$14.00|524,577|$11,685,543|
|T3|February 1 - February 28, 2019|116,042|$14.53|116,042|$10,000,013|
|T4|Total|715,619|$13.97|715,619|$10,000,013|

**Paragraphs:**

P0 (original order 1): Purchases of Equity Securities by the Issuer and Affiliated Purchasers

P1 (original order 2): The following table contains information with respect to purchases made by or on behalf of CalAmp or any “affiliated purchaser” (as defined in Rule 10b-18(a)(3) under the Exchange Act), of our common stock during the following months of our fourth quarter ended February 28, 2019:

P2 (original order 3): (1) Average price paid per share for shares purchased as part of our share repurchase program (includes brokerage commissions).

P3 (original order 4): (2) On December 10, 2018, we announced that our Board of Directors authorized a new share repurchase program under which we may repurchase up to $20.0 million of our outstanding common stock over the next 12 months. As of February 28, 2019, $10.0 million of the $20.0 million had been utilized. Our share repurchase program does not obligate us to acquire any specific number of shares. Under the program, shares may be repurchased in privately negotiated and/or open market transactions, including under plans complying with Rule 10b5-1 under the Exchange Act.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 17: e76f2a50-9981-4c74-8969-b2e1e9013519
Context UID: 50be65ba-d3de-47fb-b516-f6d8f2a6dd45
**Question:** What was the change in interest expense between 2017 and 2018?

**Table (original row order):**

|row|C0|C1|C2|C3|
|---|---|---|---|---|
|T0|||Year Ended||
|T1||April 26, 2019|April 27, 2018|April 28, 2017|
|T2|Interest income|$ 88|$ 79|$ 44|
|T3|Interest expense|(58)|(62)|(52)|
|T4|Other income, net|17|24|8|
|T5|Other income, net|$ 47|$ 41|$ —|

**Paragraphs:**

P0 (original order 1): 8. Other income, net

P1 (original order 2): Other income, net consists of the following (in millions):

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 18: 28042ec5-d6a5-40e2-8c61-6ba2fb1194b5
Context UID: 4f5ebbfb-f036-4483-a015-78f3ffefabc0
**Question:** What is the average Fair value on acquisition/issuance?

**Table (original row order):**

|row|C0|C1|C2|
|---|---|---|---|
|T0||Year Ended December 31,||
|T1||2019|2018|
|T2||$|$|
|T3|Fair value at the beginning of the year|12,026|30,749|
|T4|Fair value on acquisition/issuance|—|2,330|
|T5|Unrealized gain (loss) included in earnings|26,900|(21,053)|
|T6|Realized loss included in earnings|(25,559)|—|
|T7|Settlements|(13,367)|—|
|T8|Fair value at the end of the year|—|12,026|

**Paragraphs:**

P0 (original order 1): Stock purchase warrants

P1 (original order 2): Prior to the 2019 Brookfield Transaction, Teekay held 15.5 million common unit warrants (or the Brookfield Transaction Warrants) issued by Altera to Teekay in connection with the 2017 Brookfield Transaction (see Note 4) and 1,755,000 warrants to purchase common units of Altera issued to Teekay in connection with Altera's private placement of Series D Preferred Units in June 2016 (or the Series D Warrants). In May 2019, Teekay sold to Brookfield all of the Company’s remaining interests in Altera, which included, among other things, both the Brookfield Transaction Warrants and Series D Warrants.

P2 (original order 3): Changes in fair value during the years ended December 31, 2019 and 2018 for the Company’s Brookfield Transaction Warrants and the Series D Warrants, which were measured at fair value using significant unobservable inputs (Level 3), are as follows:

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 19: 8b992296-0080-45ab-ace2-de7777b6d118
Context UID: cbc6ae9f-7526-4e3b-9440-f4876f63f716
**Question:** What was the change in Income taxes receivable in 2019 from 2018?

**Table (original row order):**

|row|C0|C1|C2|
|---|---|---|---|
|T0||December 31,||
|T1||2019|2018|
|T2|Trade accounts receivable, current|$378,616|$338,473|
|T3|Income taxes receivable|1,571|916|
|T4|Other|13,440|11,132|
|T5|Receivables, gross|393,627|350,521|
|T6|Less: Allowance for doubtful accounts|3,480|3,096|
|T7|Receivables,net|$390,147|$347,425|
|T8|Allowance for doubtful accounts as a percent of trade accounts receivable, current|0.9%|0.9%|

**Paragraphs:**

P0 (original order 1): Note 9. Receivables, Net

P1 (original order 2): Receivables, net consisted of the following (in thousands):

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 20: e1280d98-5529-4dd6-83c2-29460e38a76d
Context UID: a557ade3-c5f3-4326-9fd3-12012d9717e4
**Question:** What is the average Stock-based compensation grants for the period December 31, 2019 to December 31, 2018?

**Table (original row order):**

|row|C0|C1|C2|C3|
|---|---|---|---|---|
|T0|||Year Ended December 31,||
|T1||2019|2018|2017|
|T2|Convertible senior notes|6,733,914|3,411,199|3,411,199|
|T3|Stock-based compensation grants|2,038,174|2,562,274|3,268,610|
|T4|Total|8,772,088|5,973,473|6,679,809|

**Paragraphs:**

P0 (original order 1): (12) Basic and Diluted Net Loss per Share

P1 (original order 2): Basic net loss per common share is computed by dividing net loss by the weighted-average number of shares of common stock outstanding during the period. Diluted net loss per share is computed by giving effect to all potential dilutive shares of common stock. Basic and diluted net loss per share of common stock were the same for all periods presented as the impact of all potentially dilutive securities outstanding was anti-dilutive. The Company uses the if converted method for calculating any potential dilutive effect on diluted loss per share.

P2 (original order 3): The following common equivalent shares were excluded from the diluted net loss per share calculation because their inclusion would have been anti-dilutive:

P3 (original order 4): In connection with the issuance of the 2024 Notes in December 2019, the Company paid $44.9 million to enter into capped call option agreements to reduce the potential dilution to holders of the Company’s common stock upon conversion of the 2024 Notes. In connection with the issuance of the 2022 Notes in November 2017, the Company paid $12.9 million to enter into capped call option agreements to reduce the potential dilution to holders of the Company’s common stock upon conversion of the 2022 Notes.

P4 (original order 5): In December 2019, the Company partially terminated capped call options related to the 2022 Notes and received $5.8 million. The capped call option agreements are excluded from the calculation of diluted net loss per share attributable to common stockholders as their effect is antidilutive.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 21: 918c1037-ee49-4906-93d5-1517bfb17825
Context UID: a3ce1a9f-8c21-45d2-b30b-2edaa8167512
**Question:** What is the average Unamortized debt discount for 2018 and 2019?

**Table (original row order):**

|row|C0|C1|C2|
|---|---|---|---|
|T0||December 31, 2019|December 31, 2018|
|T1||(in thousands)||
|T2|Principal|$212,000|$262,000|
|T3|Less:|||
|T4|Unamortized debt discount|(1,328)|(1,630)|
|T5|Unamortized debt issuance costs|(3,763)|(4,613)|
|T6|Net carrying amount of long-term debt|206,909|255,757|
|T7|Less: current portion of long-term debt|—|—|
|T8|Long-term debt, non-current portion|$206,909|255,757|

**Paragraphs:**

P0 (original order 1): 8. Debt and Interest Rate Swap

P1 (original order 2): Debt The carrying amount of the Company's long-term debt consists of the following:

P2 (original order 3): On May 12, 2017, the Company entered into a credit agreement with certain lenders and a collateral agent in connection with the acquisition of Exar (Note 3). The credit agreement provides for an initial secured term B loan facility (the “Initial Term Loan”) in an aggregate principal amount of $425.0 million. The credit agreement permits the Company to request incremental loans in an aggregate principal amount not to exceed the sum of $160.0 million (subject to adjustments for any voluntary prepayments), plus an unlimited amount that is subject to pro forma compliance with certain secured leverage ratio and total leverage ratio tests. Incremental loans are subject  to certain additional conditions, including obtaining additional commitments from the lenders then party to the credit agreement or new lenders.

P3 (original order 4): Loans under the credit agreement bear interest, at the Company’s option, at a rate equal to either (i) ab ase rate equal to the highest of (x) the federal funds rate, plus 0.50%, (y) the prime rate then in effect and (z) an adjusted LIBOR rate determined on the basis of a one- three- or six-month interest period, plus 1.0% or (ii) an adjusted LIBOR rate, subject to a floor of 0.75%, in each case, plus an applicable margin of 2.50% in the case of LIBOR rate loans and 1.50% in the case of base rate loans. Commencing on September 30, 2017, the Initial Term Loan will amortize in equal quarterly installments equal to 0.25% of the original principal amount of the Initial Term Loan, with the balance payable on the maturity date. The Initial Term Loan has a term of seven years and will mature on May 12, 2024, at which time all outstanding principal and accrued and unpaid interest on the Initial Term Loan must be repaid. The Company is also required to pay fees customary for a credit facility of this size and type.

P4 (original order 5): The Company is required to make mandatory prepayments of the outstanding principal amount of term loans under the credit agreement with the net cash proceeds from the disposition of certain assets and the receipt of insurance proceeds upon certain casualty and condemnation events, in each case, to the extent not reinvested within a specified time period, from excess cash flow beyond stated threshold amounts, and from the incurrence of certain indebtedness. The Company has the right to prepay its term loans under the credit agreement, in whole or in part, at any time without premium or penalty, subject to certain limitations and a 1.0% soft call premium applicable during the first six months for the loan term. The Company exercised its right to prepay and made aggregate payments of principal of $213.0 million to date through December 31, 2019.

P5 (original order 6): The Company’s obligations under the credit agreement are required to be guaranteed by certain of its domestic subsidiaries meeting materiality thresholds set forth in the credit agreement. Such obligations, including the guaranties, are secured by substantially all of the assets of the Company and the subsidiary guarantors pursuant to a security agreement with the collateral agent.

P6 (original order 7): The credit agreement also contains customary events of default that include, among other things, certain payment defaults, cross defaults to other indebtedness, covenant defaults, change in control defaults, judgment defaults, and bankruptcy and insolvency defaults. If an event of default exists, the lenders may require immediate payment of all obligations under the credit agreement, and may exercise certain other rights and remedies provided for under the credit agreement, the other loan documents and applicable law.

P7 (original order 8): As of December 31, 2019 and 2018, the weighted average effective interest rate on long-term debt was approximately4 .9% and 4.6%, respectively.

P8 (original order 9): The debt is carried at its principal amount, net of unamortized debt discount and issuance costs, and is not adjusted to fair value each period. The issuance date fair value of the liability component of the debt in the amount of $398.5 million was determined using a discounted cash flow analysis, in which the projected interest and principal payments were discounted back to the issuance date of the term loan at a market interest rate for nonconvertible debt of 4.6%, which represents a Level 2 fair value measurement. The debt discount of $2.1 million and debt issuance costs of $6.0 million are being amortized to interest expense using the effective interest method from the issuance date through the contractual maturity date of the term loan of May 12, 2024.

P9 (original order 10): During the year ended December 31, 2017, the Company recognized amortization of debt discount of $0.2 million and debt issuance costs of $0.6 million to interest expense.

P10 (original order 11): The approximate fair value of the term loan as of December 31, 2019 and 2018 was $214.6 million and $268.1 million, respectively, which was estimated on the basis
of inputs that are observable in the market and which is considered a Level 2 measurement method in the fair value hierarchy.

P11 (original order 12): As of December 31, 2019 and 2018, the remaining principal balance on the term loan was $212.0 million and $262.0 million, respectively. The remaining principal
balance is due on May 12, 2024 at the maturity date on the term loan.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 22: 8456e6cd-3a12-4508-83a6-38d3de604bee
Context UID: 10e74936-5fac-4381-a7d8-f4b3789f5a45
**Question:** What is the change in the outstanding number of shares from December 31, 2018 to December 31, 2019?

**Table (original row order):**

|row|C0|C1|C2|
|---|---|---|---|
|T0||Number of Shares|Weighted Average Exercise Price Per Share|
|T1|Outstanding at January 1, 2018|4,376,474|$0.16|
|T2|Granted|67,394|0.17|
|T3|Exercised|–|–|
|T4|Cancelled or expired|(1,094,075)|0.14|
|T5|Outstanding at December 31, 2018|3,349,793|$0.16|
|T6|Granted|–|–|
|T7|Exercised|–|–|
|T8|Cancelled or expired|–|–|
|T9|Outstanding at December 31, 2019|3,349,793|$0.16|

**Paragraphs:**

P0 (original order 1): Transactions involving stock options issued to employees are summarized as follows:

P1 (original order 2): The expected life of awards granted represents the period of time that they are expected to be outstanding. The Company determines the expected life based on historical experience with similar awards, giving consideration to the contractual terms, vesting schedules, exercise patterns and pre-vesting and post-vesting forfeitures. The Company estimates the volatility of the Company’s common stock based on the calculated historical volatility of the Company’s common stock using the share price data for the trailing period equal to the expected term prior to the date of the award. The Company bases the risk-free interest rate used in the Black-Scholes option valuation model on the implied yield currently available on U.S. Treasury zero-coupon issues with an equivalent remaining term equal to the expected life of the award. The Company has not paid any cash dividends on the Company’s common stock and does not anticipate paying any cash dividends in the foreseeable future. Consequently, the Company uses an expected dividend yield of zero in the Black-Scholes option valuation model. The Company uses historical data to estimate pre-vesting option forfeitures and records share-based compensation for those awards that are expected to vest. In accordance with ASC 718-10, the Company calculates share-based compensation for changes to the estimate of expected equity award forfeitures based on actual forfeiture experience.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 23: cca3062d-1636-446e-8dee-b19424e29c8d
Context UID: e122b51d-6f59-49d2-896a-73404f101701
**Question:** What is the average total income from 2017 to 2019?

**Table (original row order):**

|row|C0|C1|C2|C3|
|---|---|---|---|---|
|T0|(In millions)||||
|T1|Year Ended June 30,|2019|2018|2017|
|T2|Interest and dividends income|$    2,762|$    2,214|$   1,387|
|T3|Interest expense|(2,686)|(2,733)|(2,222)|
|T4|Net recognized gains on investments|648|2,399|2,583|
|T5|Net gains (losses) on derivatives|144|(187)|(510)|
|T6|Net losses on foreign currency remeasurements|(82)|(218)|(111)|
|T7|Other, net|(57)|(59)|(251)|
|T8|Total|$  729|$ 1,416|$  876|

**Paragraphs:**

P0 (original order 1): OTHER INCOME (EXPENSE), NET

P1 (original order 2): The components of other income (expense), net were as follows:

P2 (original order 3): We use derivative instruments to: manage risks related to foreign currencies, equity prices, interest rates, and credit; enhance investment returns; and facilitate portfolio diversification. Gains and losses from changes in fair values of derivatives that are not designated as hedging instruments are primarily recognized in other income (expense), net.

P3 (original order 4): Fiscal Year 2019 Compared with Fiscal Year 2018 Interest and dividends income increased primarily due to higher yields on fixed-income securities. Interest expense decreased primarily driven by a decrease in outstanding long-term debt due to debt maturities, offset in part by higher finance lease expense. Net recognized gains on investments decreased primarily due to lower gains on sales of equity investments. Net gains on derivatives includes gains on foreign exchange and interest rate derivatives in the current period as compared to losses in the prior period.

P4 (original order 5): Fiscal Year 2018 Compared with Fiscal Year 2017 Dividends and interest income increased primarily due to higher average portfolio balances and yields on fixed-income securities. Interest expense increased primarily due to higher average outstanding long-term debt and higher finance lease expense. Net recognized gains on investments decreased primarily due to higher losses on sales of fixed-income securities, offset in part by higher gains on sales of equity securities. Net losses on derivatives decreased primarily due to lower losses on equity, foreign exchange, and commodity derivatives, offset in part by losses on interest rate derivatives in the current period as compared to gains in the prior period.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---

## Case 24: 07799e79-f4e9-443c-8651-94d27c8553a1
Context UID: 5824b219-c2f7-4573-8927-343c73ef7db2
**Question:** What was the change in Total operating income in the Communications Solutions segment in 2019 from 2018?

**Table (original row order):**

|row|C0|C1|C2|
|---|---|---|---|
|T0|||Fiscal|
|T1||2019|2018|
|T2|||(in millions)|
|T3|Restructuring and other charges, net|$  48|$  13|
|T4|Other items|1|—|
|T5|Total|$  49|$  13|

**Paragraphs:**

P0 (original order 1): In the Communications Solutions segment, operating income decreased $79 million in fiscal 2019 as compared to fiscal 2018. The Communications Solutions segment’s operating income included the following:

P1 (original order 2): Excluding these items, operating income decreased in fiscal 2019 due primarily to lower volume.

**Reviewer form:**
- Reviewer / date:
- Metric / entity:
- Period / scope:
- Inputs / source coordinates:
- Sign / units / precision:
- Formula:
- Answer / scale:
- Alternate readings / ambiguity / missing evidence:
- Confidence / reason:

---
