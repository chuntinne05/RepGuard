# RepGuard: pilot đồ án chạy model thật

100 câu FinQA TRAIN,100 báo cáo;60history/10calibration/10validation/20development screen.
**Đây là pilot development, chưa phải xác nhận cuối hoặc so sánh SOTA.**

Run `359b8d464d5005b9c5d0f967`; app `repguard-thesis-real-pilot-20261018`;200 phản hồi thật đã kiểm checksum và tính lại local.

| Phương pháp | Đúng/20 | Accuracy | Approved coverage | Sai được approved | Mean tokens | Calls/20 |
|---|---:|---:|---:|---:|---:|---:|
| AlwaysA | 0 | 0.0% | 0.0% | 0 | 1902.0 | 20 |
| AlwaysB | 1 | 5.0% | 5.0% | 0 | 1927.8 | 20 |
| GlobalGold | 0 | 0.0% | 0.0% | 0 | 1902.0 | 20 |
| SkillGold | 0 | 0.0% | 0.0% | 0 | 1902.0 | 20 |
| RawFeedbackSkill | 0 | 0.0% | 0.0% | 0 | 1902.0 | 20 |
| FixedCascade | 1 | 5.0% | 5.0% | 0 | 3829.7 | 40 |
| EvidenceOnly | 1 | 5.0% | 5.0% | 0 | 3829.7 | 40 |
| RepGuard | 1 | 5.0% | 5.0% | 0 | 3829.7 | 40 |

**Pilot signal gate: FAIL.**

Cả hai learner được huấn luyện supervised từ outcome thực; nhãn history được cấp công bằng cho controls. Không gọi kết quả này là10%audit.
Source/operation checks không chứng minh đúng ngữ nghĩa. Token/request seconds không phải tổng billing Modal.
Các policy được replay trên phản hồi thật đã thu;200calls thu counterfactual không phải cost serving của mỗi policy.

| RepGuard so với | Accuracy difference | CI95 | Rescue | Harm |
|---|---:|---|---:|---:|
| AlwaysB | +0.0% | [+0.0%,+0.0%] | 0 | 0 |
| FixedCascade | +0.0% | [+0.0%,+0.0%] | 0 | 0 |
| EvidenceOnly | +0.0% | [+0.0%,+0.0%] | 0 | 0 |
| SkillGold | +5.0% | [+0.0%,+15.0%] | 1 | 0 |

Giới hạn: chỉ20câu screen; bootstrap exploratory, chưa adjustment; model cùng họ; latency chịu thứ tự block/cold load. Giữ nguyên kết quả âm và không tune trên screen.
