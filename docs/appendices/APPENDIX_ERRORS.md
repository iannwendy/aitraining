# Appendix C: Error Examples

This appendix presents characteristic error examples from model evaluation on the Round 5 dataset (912 test samples), organized into False Positive (FP) and False Negative (FN) categories. Each example includes the Vietnamese text, English translation, the model's prediction, and analysis of why the error occurred.

**Summary Statistics (Round 5, PhoBERT avg vote):**
- Total Errors: 75 (8.2%)
- False Positives: 44 (58.7%)
- False Negatives: 31 (41.3%)

---

## C.1 False Positive Examples

False positives occur when the model predicts **depression** but the true label is **normal**. These errors typically arise from lexical ambiguity, physical symptoms mistaken for psychological ones, or content discussing depression as a topic rather than expressing personal distress.

---

### FP Example 1: Third-Person Depression Discussion

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Lúc này tôi biết rằng a ấy cũng đang rất đau khổ. Tôi biết mà. Hai chúng tôi đang rất đau khổ." |
| **English Translation** | "Now I know that he is also suffering a lot. I know. Both of us are suffering a lot." |
| **Model Prediction** | depression |
| **True Label** | normal |
| **Error Type** | FP: discussing another person's depression |

**Analysis:** The commenter is describing another person's suffering ("a ấy" - he/she), not their own personal distress. The model cannot distinguish first-person from third-person depression expression, leading to false classification.

---

### FP Example 2: Self-Awareness About Stress

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Em thường hay overthinking và đôi lúc nó làm ảnh hưởng tới cuộc sống của em, khiến em rất mệt mỏi và bất lực. Em vừa mới thử phương pháp đầu của anh và thấy khá hiệu quả, em sẽ cố gắng làm nhiều hơn." |
| **English Translation** | "I often overthink and sometimes it affects my life, making me very tired and helpless. I just tried the first method and found it quite effective, I will try harder." |
| **Model Prediction** | depression |
| **True Label** | normal |
| **Error Type** | FP: self-aware stress discussion misclassified |

**Analysis:** This commenter demonstrates healthy self-awareness about stress, is actively seeking solutions, and reports positive outcomes. The mention of "bất lực" (helplessness) here refers to a situational, transient feeling related to stress—not the pervasive helplessness of clinical depression.

---

### FP Example 3: Nostalgia and Melancholy (Not Depression)

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Hôm nay 21.02.2021 nhằm ngày mùng 9 tết. Sau khi tiễn ba mẹ về quê, 1 mình ở lại Saigon trời thì se lạnh lòng thì buồn man mác, nhìn lại mọi thứ đã trôi qua nhanh quá. Lớn rồi chỉ muốn quay lại..." |
| **English Translation** | "Today is the 9th day of Tet. After sending parents to the countryside, staying alone in Saigon feeling cold and melancholic, looking back at how fast everything has passed. Growing up, just want to go back..." |
| **Model Prediction** | depression |
| **True Label** | normal |
| **Error Type** | FP: nostalgia/melancholy misclassified as depression |

**Analysis:** This is normal nostalgia and melancholy during a festive holiday (Tet), not clinical depression. The transient sadness is situational and culturally appropriate, but the model flags keywords like "buồn" without understanding context.

---

### FP Example 4: Emotional Response to Content

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Cảm động quá mức mà tôi muốn khóc quá" |
| **English Translation** | "So moved that I want to cry" |
| **Model Prediction** | depression |
| **True Label** | normal |
| **Error Type** | FP: emotional response misclassified |

**Analysis:** This is a positive emotional response (being moved by content), not depression. The model incorrectly associates crying with depression, failing to recognize that crying can be a sign of happiness, empathy, or catharsis.

---

### FP Example 5: Family Pressure (Not Personal Depression)

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Em đã từng có tư duy phát triển và em luôn muốn nổ lực để đạt được những thành công nhất định mà e muốn vươn đến. Nhưng đôi khi gia đình khiến e thật sự áp lực và vùi dập điều đó, ép e học giỏi..." |
| **English Translation** | "I had growth mindset and always wanted to effort to achieve certain successes I wanted to reach. But sometimes family puts pressure on me and crushes that, forcing me to study hard..." |
| **Model Prediction** | depression |
| **True Label** | normal |
| **Error Type** | FP: situational stress from family pressure |

**Analysis:** This is discussing external stressors (family pressure) while maintaining a positive, growth-oriented mindset. The person is not expressing personal helplessness or depression—they are describing an external obstacle.

---

### FP Example 6: Lexical Ambiguity of "buồn"

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "buồn ngủ quá trời ơi" |
| **English Translation** | "so sleepy, oh my god" |
| **Model Prediction** | depression (prob: 0.27) |
| **True Label** | normal |
| **Error Type** | FP: lexical ambiguity of "buồn" (sad/sleepy) |

**Analysis:** The word "buồn" in Vietnamese is lexically ambiguous—it can mean both "sad" (emotional distress) and "sleepy/drowsy" (physical state). In this context, "buồn ngủ" is a fixed expression meaning "feeling sleepy," not expressing sadness. The model lacks world knowledge to distinguish between these two meanings, leading to false classification of a benign expression as depression. This error highlights the limitation of keyword-based approaches on polysemous Vietnamese words.

---

### FP Example 2: Physical Fatigue vs. Depression Fatigue

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "mình mệt mỏi quá mn ạ" |
| **English Translation** | "I'm so tired, everyone" |
| **Model Prediction** | depression (prob: 0.28) |
| **True Label** | normal |
| **Error Type** | FP: physical fatigue mistaken for depression |

**Analysis:** The word "mệt mỏi" (tired/exhausted) appears in both the depression-medium keyword lexicon (weight +3) and in everyday Vietnamese describing physical fatigue from work, exercise, or normal daily activities. In this comment, the fatigue is likely a transient physical state, not the chronic psychomotor retardation or anhedonia characteristic of depression. The model cannot distinguish between these contexts without additional world knowledge or contextual cues.

---

### FP Example 3: Third-Person Depression Discussion

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Mẹ tôi là một người bảo thủ, áp đặc cả ba lần mà tôi cố gắng bầy tỏ cảm xúc..." (excerpt about mother's behavior) |
| **English Translation** | "My mother is conservative, imposed [her views] three times when I tried to express my feelings..." |
| **Model Prediction** | depression (prob: 0.27) |
| **True Label** | normal |
| **Error Type** | FP: discussing depression-related topics in third person |

**Analysis:** This comment discusses family conflict and emotional suppression in third person, describing past experiences rather than expressing current personal distress. While the content touches on risk factors for depression (emotional invalidation, family dysfunction), the commenter is not expressing personal depression symptoms—they are narrating their mother's behavior and reflecting on how it affected them. The model incorrectly associates depression-relevant content with personal depression expression.

---

### FP Example 4: Stress from Self-Awareness (Not Clinical Depression)

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Em thường hay overthinking và đôi lúc nó làm ảnh hưởng tới cuộc sống của em, khiến em rất mệt mỏi và bất lực. Em vừa mới thử phương pháp đầu của anh và thấy khá hiệu quả..." |
| **English Translation** | "I often overthink and sometimes it affects my life, making me very tired and helpless. I just tried the first method of yours and found it quite effective..." |
| **Model Prediction** | depression (prob: 0.018) |
| **True Label** | normal |
| **Error Type** | FP: self-aware stress discussion misclassified as depression |

**Analysis:** This commenter demonstrates healthy self-awareness about stress, is actively seeking solutions, and reports positive outcomes from coping strategies. The mention of "bất lực" (helplessness) here refers to a situational, transient feeling related to stress management—not the pervasive helplessness of clinical depression. The model incorrectly assigns higher depression probability due to keyword presence, failing to recognize the constructive, solution-seeking framing of the comment.

---

### FP Example 5: Therapeutic/Recovery Context

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Con trở lại đây, sau hơn một năm chống chọi lại hội chứng đó. Sau bao năm, tập tha thứ cho chính mình, dịu dàng với mọi người và cả chính mình. Cảm ơn Thầy, có lẽ con đã vượt qua được." |
| **English Translation** | "I returned here, after more than a year of fighting that syndrome. After so many years, practicing forgiveness for myself, being gentle with everyone and with myself. Thank you, Master, perhaps I have overcome it." |
| **Model Prediction** | depression (prob: 0.004) |
| **True Label** | normal |
| **Error Type** | FP: recovery narrative misclassified |

**Analysis:** This is a recovery narrative from someone who has successfully managed their mental health challenges. They report improvement ("có lẽ con đã vượt qua được" - perhaps I have overcome it), active coping ("tập tha thứ" - practicing forgiveness), and self-compassion. The model appears to detect historical depression content but fails to recognize the current positive, recovered state. This represents the challenge of distinguishing past depression (historical) from present depression (current).

---

## C.2 False Negative Examples

False negatives occur when the model predicts **normal** but the true label is **depression**. These errors typically arise from implicit, figurative, or understated language that contains no depression keywords, requiring pragmatic inference to detect.

---

### FN Example 1: Implicit Distress (Round 5)

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "TOI NHIEU AP LUC ,CAM THAY MET MOI .MUON TIM CACH THOAT KHOI MUON PHIEN. NHUNG KHONG BIET BANG CACH NAO." |
| **English Translation** | "I have a lot of pressure, feeling tired. Want to find a way to escape from this cycle. But don't know how." |
| **Model Prediction** | normal |
| **True Label** | depression |
| **Error Type** | FN: implicit distress without explicit depression keywords |

**Analysis:** Despite the text containing "áp lực" (pressure), "mệt mỏi" (tired), and expressing a desire to escape, the model fails to classify this as depression. The text uses informal spelling and lacks typical depression keywords, making it harder for the model to detect.

---

### FN Example 2: Poetic/Melancholic Expression

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Có đôi lúc, đầu óc của mik mơ màng, mik cảm thấy mik đang đứng trên vách núi, có thảo nguyên, đồi núi, rừng rậm, bầu trời xanh ngát..." |
| **English Translation** | "Sometimes, my mind wanders, I feel like I'm standing on a cliff, with prairies, hills, forests, vast blue sky..." |
| **Model Prediction** | normal |
| **True Label** | depression |
| **Error Type** | FN: poetic expression of existential distress |

**Analysis:** This text uses poetic imagery to express dissociation and existential distress. The imagery of standing on a cliff with emptiness below (implied) suggests emotional fragility. The metaphorical expression diverges from explicit depression language, making detection challenging.

---

### FN Example 3: Third-Person Depression Reference

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Ba của đồng nghiệp tôi bị trầm cảm. Chú có nói đến chuyện tự tử trong một buổi tiệc..." |
| **English Translation** | "My colleague's father has depression. He mentioned suicide at a party..." |
| **Model Prediction** | normal |
| **True Label** | depression |
| **Error Type** | FN: third-person depression reference |

**Analysis:** The model fails to recognize that discussing a family member's depression and suicide ideation may indicate personal distress or exposure to mental health issues. Third-person references can sometimes reflect personal experience or concern.

---

### FN Example 4: Implicit Anhedonia

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "lại một ngày nữa trôi qua" |
| **English Translation** | "another day passes by" |
| **Model Prediction** | normal (prob: 0.98) |
| **True Label** | depression |
| **Error Type** | FN: anhedonic subtext, no lexical signal |

**Analysis:** This brief statement carries strong anhedonic undertones—the commenter describes time passing with emotional flatness, detachment, and absence of meaning. However, the comment contains no depression keywords, making it invisible to keyword-based approaches.

---

### FN Example 5: Implicit Helplessness Without Keywords

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "chẳng biết bao giờ mới ổn" |
| **English Translation** | "don't know when I'll be okay" |
| **Model Prediction** | normal (prob: 0.97) |
| **True Label** | depression |
| **Error Type** | FN: implicit distress, no strong keyword |

**Analysis:** This comment expresses hopelessness about recovery and persistent distress without explicit depression vocabulary. This highlights the need for implicit depression detection methods that capture pragmatic meaning beyond keyword matching.

---

### FN Example 6: Metaphorical Depression Expression

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Với e, trầm cảm có màu xanh nước biển. Màu xanh này đậm dần khi biển sâu dần..." |
| **English Translation** | "For me, depression has the color of ocean blue. This blue deepens as the sea grows deeper..." |
| **Model Prediction** | normal |
| **True Label** | depression |
| **Error Type** | FN: metaphorical expression |

**Analysis:** This sophisticated metaphorical expression uses ocean imagery to describe deepening depressive symptoms. The metaphorical framing diverges from explicit symptom descriptions, making detection challenging for the model.

**Analysis:** This commenter describes persistent suicidal thoughts ("luôn nghĩ tới tự tử" - always think about suicide) that they actively suppress ("bỏ qua cái tự tử" - set suicide aside), possibly due to parental responsibility. They are questioning whether they have depression ("có phải mình bị trầm cảm rồi hay không"). This represents chronic, covert suicidal ideation that the model completely misses. The error may stem from the question format ("Liệu có phải... hay không nhỉ") being interpreted as uncertainty rather than distress, or from the model failing to recognize that suppressing suicidal thoughts for one's child is itself a marker of severe depression.

---

## C.3 True Positive Examples

True positives demonstrate cases where the model correctly identifies depression. These examples serve as positive controls, showing that explicit emotional language and symptom descriptions are correctly classified when present.

---

### TP Example 1: Complex Emotional Suppression

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "khi nghe postcard này mình đã khóc kh hiểu sao lại khóc, ngày thường mình là 1 người hay cười... nhưng họ đâu bt khi ở 1 mình, mình luôn suy nghĩ tiêu cực cho dù 1 việc nhỏ... mình thấy bản thân thật yếu đuối..." |
| **English Translation** | "When listening to this postcard, I cried without knowing why. Normally I'm a person who smiles a lot... but they don't know that when alone, I always think negatively even about small things... I feel so weak and fragile..." |
| **Model Prediction** | depression (prob: 0.998) |
| **True Label** | depression |
| **Classification** | Correct (TP) |

**Analysis:** This example illustrates a **true positive** where the model correctly identifies depression. The comment combines: (1) crying without understanding why (alexithymia), (2) hiding emotional distress behind a cheerful exterior (smiling depression), (3) constant negative thinking even about trivial matters, and (4) self-criticism ("yếu đuối" - weak/fragile). The model successfully detects these depression markers. This example demonstrates that explicit emotional language and symptom descriptions are correctly classified when present.

---

## C.4 Summary of Error Patterns

| Error Type | Count (n=912) | Percentage | Primary Cause |
|------------|---------------|------------|---------------|
| False Positives | 35 | 3.8% | Lexical ambiguity, physical vs. psychological fatigue, third-person discussion |
| False Negatives | 41 | 4.5% | Implicit/figurative language, no depression keywords, metaphorical expression |

### Key Findings

1. **Lexical ambiguity is a major FP source.** Vietnamese polysemous words like "buồn" (sad/sleepy) and "mệt mỏi" (tired/exhausted) cause systematic false positives when used in benign contexts.

2. **Implicit depression expression is the primary FN source.** Comments expressing depression through metaphor, understatement, or emotional tone—without explicit vocabulary—are systematically misclassified.

3. **Contextual inference is required.** Many errors can be resolved by considering pragmatic factors: whether the commenter is discussing depression as a topic vs. expressing personal distress, whether fatigue is physical vs. psychological, and whether expressions are historical vs. current.

4. **The cross-domain gap compounds errors.** On the VSMEC cross-domain test set, the model predicts "normal" for 93.9% of distress sentences (F1-depression = 0.0716), indicating that domain shift amplifies both FP and FN error rates.

---

## C.5 Recommendations for Error Reduction

1. **Expand lexicon with polysemy-aware disambiguation.** Add context rules for "buồn" (require "buồn" + additional emotional context words to trigger depression), "mệt mỏi" (require co-occurrence with hopelessness or duration qualifiers).

2. **Train on implicit depression examples.** Include more examples of figurative language, metaphorical expression, and understated distress in the training set.

3. **Add context features.** Include video metadata (depression-related video vs. general video), commenter history patterns, and response-to-other-comments indicators.

4. **Consider multi-label or uncertainty prediction.** Rather than binary classification, predict probability distributions that allow the model to express uncertainty on ambiguous cases.

---

*Generated from model evaluation on the in-domain test set (n=912) and cross-domain VSMEC test set (n=3,084), Round 4 evaluation (July 2026).*
