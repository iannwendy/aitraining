# Appendix C: Error Examples

This appendix presents characteristic error examples from model evaluation, organized into False Positive (FP) and False Negative (FN) categories. Each example includes the Vietnamese text, English translation, the model's prediction, and analysis of why the error occurred.

---

## C.1 False Positive Examples

False positives occur when the model predicts **depression** but the true label is **normal**. These errors typically arise from lexical ambiguity, physical symptoms mistaken for psychological ones, or content discussing depression as a topic rather than expressing personal distress.

---

### FP Example 1: Lexical Ambiguity of "buồn"

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

### FN Example 1: Implicit Anhedonia

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "lại một ngày nữa trôi qua" |
| **English Translation** | "another day passes by" |
| **Model Prediction** | normal (prob: 0.98) |
| **True Label** | depression |
| **Error Type** | FN: anhedonic subtext, no lexical signal |

**Analysis:** This brief statement carries strong anhedonic undertones—the commenter describes time passing with emotional flatness, detachment, and absence of meaning or engagement. A human reader perceives the existential exhaustion and lack of pleasure implicit in "trôi qua" (passing by without significance). However, the comment contains no depression keywords from the lexicon, making it invisible to keyword-based approaches. This example exemplifies the fundamental limitation of lexical detection: depression is often expressed implicitly through figurative language, understatement, and emotional tone rather than explicit vocabulary.

---

### FN Example 2: Implicit Helplessness Without Keywords

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "chẳng biết bao giờ mới ổn" |
| **English Translation** | "don't know when I'll be okay" |
| **Model Prediction** | normal (prob: 0.97) |
| **True Label** | depression |
| **Error Type** | FN: implicit distress, no strong keyword |

**Analysis:** This comment expresses hopelessness about recovery ("chẳng biết bao giờ" - don't know when) and a sense of persistent distress ("mới ổn" - will be okay). The combination of uncertainty about the future and implied current suffering is a hallmark of depressive rumination. However, the comment contains no explicit depression vocabulary, making it indistinguishable from normal uncertainty for the model. This error highlights the need for implicit depression detection methods that capture pragmatic meaning beyond keyword matching.

---

### FN Example 3: Metaphorical Depression Expression

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Với e, trầm cảm có màu xanh nước biển. Màu xanh này đậm dần khi biển sâu dần, cũng giống như e lớn dần lại thấy xung quanh lạnh lẽo dần..." |
| **English Translation** | "For me, depression has the color of ocean blue. This blue deepens as the sea grows deeper, just like as I grow older, I feel the surroundings grow colder..." |
| **Model Prediction** | normal (prob: 0.58) |
| **True Label** | depression |
| **Error Type** | FN: metaphorical depression expression, no explicit symptom keywords |

**Analysis:** This comment is a sophisticated metaphorical expression of depression—the commenter uses ocean imagery to describe the deepening of depressive symptoms over time. The metaphor conveys hopelessness, isolation, and inability to call for help ("cũng không thể mở miệng kêu cứu trong làn nước xanh đậm dần đó" - cannot even open mouth to call for help). Despite the explicit mention of "trầm cảm" (depression), the model assigns only 0.42 probability of depression, likely because the metaphorical framing diverges from the training distribution of explicit symptom descriptions.

---

### FN Example 4: Chronic Suicidal Ideation Without Explicit Keywords

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "Mình luôn nghĩ tới tự tử như nghĩ tới con luôn bỏ qua cái tự tử. Liệu có phải mình bị trầm cảm rồi hay không nhỉ" |
| **English Translation** | "I always think about suicide like thinking about my child, I set suicide aside. Do you think I might have depression already?" |
| **Model Prediction** | normal (prob: 0.998) |
| **True Label** | depression |
| **Error Type** | FN: chronic suicidal ideation expressed indirectly |

**Analysis:** This commenter describes persistent suicidal thoughts ("luôn nghĩ tới tự tử" - always think about suicide) that they actively suppress ("bỏ qua cái tự tử" - set suicide aside), possibly due to parental responsibility. They are questioning whether they have depression ("có phải mình bị trầm cảm rồi hay không"). This represents chronic, covert suicidal ideation that the model completely misses. The error may stem from the question format ("Liệu có phải... hay không nhỉ") being interpreted as uncertainty rather than distress, or from the model failing to recognize that suppressing suicidal thoughts for one's child is itself a marker of severe depression.

---

### FN Example 5: Complex Emotional Suppression

| Attribute | Value |
|-----------|-------|
| **Vietnamese** | "khi nghe postcard này mình đã khóc kh hiểu sao lại khóc, ngày thường mình là 1 người hay cười... nhưng họ đâu bt khi ở 1 mình, mình luôn suy nghĩ tiêu cực cho dù 1 việc nhỏ... mình thấy bản thân thật yếu đuối..." |
| **English Translation** | "When listening to this postcard, I cried without knowing why. Normally I'm a person who smiles a lot... but they don't know that when alone, I always think negatively even about small things... I feel so weak and fragile..." |
| **Model Prediction** | depression (prob: 0.998) |
| **True Label** | depression |
| **Error Type** | Correct (TP) |

**Analysis:** This example illustrates a **true positive** where the model correctly identifies depression. The comment combines: (1) crying without understanding why (alexithymia), (2) hiding emotional distress behind a cheerful exterior (smiling depression), (3) constant negative thinking even about trivial matters, and (4) self-criticism ("yếu đuối" - weak/fragile). The model successfully detects these depression markers. This example serves as a positive control, demonstrating that explicit emotional language and symptom descriptions are correctly classified when present.

---

## C.3 Summary of Error Patterns

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

## C.4 Recommendations for Error Reduction

1. **Expand lexicon with polysemy-aware disambiguation.** Add context rules for "buồn" (require "buồn" + additional emotional context words to trigger depression), "mệt mỏi" (require co-occurrence with hopelessness or duration qualifiers).

2. **Train on implicit depression examples.** Include more examples of figurative language, metaphorical expression, and understated distress in the training set.

3. **Add context features.** Include video metadata (depression-related video vs. general video), commenter history patterns, and response-to-other-comments indicators.

4. **Consider multi-label or uncertainty prediction.** Rather than binary classification, predict probability distributions that allow the model to express uncertainty on ambiguous cases.

---

*Generated from model evaluation on the in-domain test set (n=912) and cross-domain VSMEC test set (n=3,084), Round 4 evaluation (July 2026).*
