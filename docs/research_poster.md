# Local PHI De-identification for Pediatric Handoff Transcription
## A HIPAA-Compliant Approach Using Microsoft Presidio

**Josh Pankin, MD**
*PGY-3 Pediatrics Resident | [Institution]*

---

## BACKGROUND

### The Problem

| Challenge | Impact |
|-----------|--------|
| Communication failures account for **67% of sentinel events** | Joint Commission, 2023 |
| Pediatric handoffs involve complex patient populations with unique PHI patterns | — |
| Audio transcription tools typically send data to cloud servers | HIPAA compliance risk |
| **HIPAA requirement**: PHI must never leave institutional control without BAAs | Privacy mandate |

### I-PASS Framework
The standardized handoff protocol (**I**llness severity, **P**atient summary, **A**ction list, **S**ituation awareness, **S**ynthesis) reduces medical errors by **23-47%** in pediatric settings (Starmer et al., 2014, 2017).

**Challenge**: How do we leverage audio transcription to support I-PASS documentation while protecting PHI?

---

## METHODS

### Architecture: 100% Local Processing

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────────────┐     ┌─────────────────────┐
│ Audio Recording │ ──▶ │  faster-whisper  │ ──▶ │ Presidio + Custom          │ ──▶ │ De-identified       │
│                 │     │  (local model)   │     │ Pediatric Recognizers      │     │ Transcript          │
└─────────────────┘     └──────────────────┘     └────────────────────────────┘     └─────────────────────┘
        ↓                       ↓                            ↓                              ↓
   Local device          No cloud API            Local NLP pipeline                 Safe for review
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Transcription | faster-whisper (CTranslate2) | Local speech-to-text |
| De-identification | Microsoft Presidio | PHI detection & redaction |
| Custom Recognizers | Python regex + NLP | Pediatric-specific PHI |
| Validation | Synthetic test framework | n=500 I-PASS scenarios |

### Custom Pediatric PHI Recognizers
- **Guardian names** (e.g., "Mom Sarah", "Dad John")
- **Baby/neonate designations** (e.g., "Baby Smith", "Neonate Jones")
- **Pediatric age formats** (e.g., "3 month old", "28-weeker")
- **Room/bed numbers** (e.g., "Room 412", "Bed A")
- **Medical record numbers** (MRN patterns)

---

## RESULTS

### System Performance

| Metric | Value |
|--------|-------|
| Test audio processed | 27-minute handoff recording |
| Unit tests passing | **21/21** (100%) |
| Processing speed | ~1 minute per 10 minutes audio |
| HIPAA compliance | **100% local processing** |

### PHI Detection Accuracy

| Entity Type | Precision | Recall | F1 Score | Status |
|-------------|-----------|--------|----------|--------|
| EMAIL | 100.0% | 100.0% | **1.00** | ✓ Excellent |
| PERSON | 95.2% | 98.8% | **0.97** | ✓ Good |
| DATE_TIME | 89.1% | 96.8% | **0.93** | ✓ Good |
| PHONE | 82.3% | 74.0% | **0.78** | ⚠ Needs tuning |
| MRN | 78.5% | 70.9% | **0.74** | ⚠ Needs tuning |
| PEDIATRIC_AGE | — | 36.6% | — | ⚠ Custom recognizer needed |
| ROOM | — | 34.4% | — | ⚠ Custom recognizer needed |
| **Overall** | **87.4%** | **77.9%** | **0.82** | — |

### Benchmark Comparison

| System | Dataset | F1 Score | Source |
|--------|---------|----------|--------|
| **Our Project** | Synthetic I-PASS (n=500) | **0.82** | — |
| Presidio (out-of-box) | Australian clinical EMR | 0.847-0.898 | Kotevski et al., 2022 |
| John Snow Labs | i2b2 benchmark | 0.961 | JSL, 2022 |
| John Snow Labs | Clinical production | 0.986 | JSL, 2024 |

**Key Finding**: Our 77.9% recall aligns with Kotevski et al.'s benchmark (80.6% strict recall) for out-of-the-box Presidio on clinical text. Healthcare-tuned models achieve 96%+ F1, indicating the path forward requires domain-specific fine-tuning.

---

## CONCLUSIONS

### Principal Findings

1. **Local-only processing maintains HIPAA compliance** without Business Associate Agreements
2. **Out-of-the-box Presidio achieves 77.9% recall**—consistent with published benchmarks (80.6%) on clinical text
3. **Gap to clinical deployment**: Healthcare-tuned models achieve 96%+ F1, indicating domain-specific fine-tuning is required
4. **Pediatric-specific PHI** (ages, room numbers, guardian names) requires custom recognizers not included in base Presidio

### Clinical Implications

- ✓ Transcription can support I-PASS documentation workflows
- ✓ Local processing eliminates cloud PHI transmission risk
- ✓ Synthetic testing enables validation without real patient data
- ⚠ Human review required until recall exceeds 95% threshold

### Future Directions

| Phase | Goal | Approach |
|-------|------|----------|
| 1 | Improve recall to >90% | Fine-tune custom recognizers |
| 2 | Clinical validation | IRB-approved pilot with real handoffs |
| 3 | Integration | EHR integration for I-PASS documentation |
| 4 | Scaling | Multi-site deployment |

---

## REFERENCES

1. Starmer AJ, Spector ND, Srivastava R, et al. Changes in Medical Errors after Implementation of a Handoff Program. *N Engl J Med*. 2014;371(19):1803-1812. doi:10.1056/NEJMsa1405556

2. Starmer AJ, Sectish TC, Simon DW, et al. I-PASS Handoff Program: Description and Evidence. *Pediatrics*. 2017;140(S2). doi:10.1542/peds.2017-1000

3. The Joint Commission. Sentinel Event Data: Root Causes by Event Type. 2023. https://www.jointcommission.org/

4. Microsoft. Presidio: Data Protection and De-identification SDK. 2024. https://microsoft.github.io/presidio/

5. HHS Office for Civil Rights. Guidance Regarding Methods for De-identification of Protected Health Information. 45 CFR 164.514. https://www.hhs.gov/hipaa/

6. **Kotevski DP, Smee RI, Field M, et al. Evaluation of an automated Presidio anonymisation model for unstructured radiation oncology electronic medical records in an Australian setting. *Int J Med Inform*. 2022;168:104880. doi:10.1016/j.ijmedinf.2022.104880** ⭐ *Key Benchmark Study*

7. John Snow Labs. State-of-the-art Clinical NER on n2c2 de-identification benchmark. 2022. https://www.johnsnowlabs.com/deidentification/

8. John Snow Labs. Kuzucu M, Horta D, Cabrera-Diego LA, et al. Healthcare NLP: A Comprehensive, Open-Source Medical Language Processing Framework. arXiv:2312.08495. 2024.

---

## ACKNOWLEDGMENTS

Project developed using Claude Code AI assistance.
Microsoft Presidio is open-source under MIT License.

---

## CONTACT

**Josh Pankin, MD**
Email: josh.pankin@gmail.com
GitHub: github.com/pankin/pediatric-handoff-phi-remover

---

*Poster created: 2026-01-23*
