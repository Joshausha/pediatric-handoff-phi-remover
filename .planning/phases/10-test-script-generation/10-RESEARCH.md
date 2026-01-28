# Phase 10: Test Script Generation and Recording - Research

**Researched:** 2026-01-28
**Domain:** Test script generation for PHI de-identification validation
**Confidence:** HIGH

## Summary

Phase 10 is primarily a **human action phase** focused on creating test data to expose over-detection issues. The user (a pediatric resident) will generate handoff scripts, record them as audio, and process them through the PHI detection pipeline. Claude's role is to help generate script content targeting known over-detection issues (duration phrases flagged as DATE_TIME, flow terminology flagged as LOCATION).

The existing project infrastructure is well-suited for this work. The `tests/handoff_templates.py` already contains 27+ I-PASS templates with Faker placeholders, and `tests/medical_providers.py` provides clinical content generation. The gap is **targeted templates for edge cases** that expose duration phrases ("three days of symptoms") and respiratory flow terminology ("currently on high flow"). These need to be written as readable scripts (not templates with placeholders) so the user can record them naturally.

The recommended approach is to generate two categories of scripts: (1) **realistic scripts** covering typical I-PASS handoffs with respiratory and medication content, and (2) **edge-case scripts** specifically targeting known over-detection patterns. Scripts should be 30-60 seconds when read aloud (approximately 75-150 words) to match natural handoff cadence. Recording can be done with any iOS/Android voice memo app; audio quality is less critical than capturing natural speech patterns including hesitations and self-corrections.

**Primary recommendation:** Generate 10+ scripts as plain text (not Faker templates) — 6 realistic I-PASS scripts covering common pediatric scenarios, 4 edge-case scripts targeting duration/flow phrases — and record them for processing through the pipeline to document false positives.

## Standard Stack

The established approach for this domain:

### Core
| Tool | Purpose | Why Standard |
|------|---------|--------------|
| Plain text scripts | Human-readable for recording | User must speak naturally; templates with placeholders are awkward |
| Voice Memos (iOS) / Recorder (Android) | Audio capture | Already on user's device, sufficient quality for Whisper |
| Existing pipeline (`/transcribe`) | Processing | Already tested with 27 real handoffs; proven infrastructure |
| Markdown documentation | Recording false positives | Integrates with project `.planning/` structure |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `test_presidio.py -i` | Interactive testing of scripts before recording | Quick validation that script content triggers expected issues |
| `tests/handoff_templates.py` | Reference for I-PASS structure | Pattern source for generating new scripts |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Plain text scripts | Faker-generated synthetic data | Faker data already exists (500+ samples); this phase needs human-recorded audio to test transcription + detection together |
| Voice Memos | Professional recording studio | Overkill; Whisper handles phone-quality audio well |
| Recording all scripts | Recording subset | More scripts = more edge case coverage, but time-limited; prioritize edge cases |

## Architecture Patterns

### Recommended Script Structure

Scripts should follow the I-PASS mnemonic structure for realistic handoffs:

```
I - Illness Severity    "This patient is stable/sick/watch closely"
P - Patient Summary     "3 year old with bronchiolitis, day 2 of illness"
A - Action List         "Continue supportive care, wean O2 as tolerated"
S - Situation Awareness "If sats drop below 90%, escalate to high flow"
S - Synthesis           "Any questions?" (verbal confirmation)
```

### Pattern 1: Realistic Script with Respiratory Content (TEST-01)
**What:** I-PASS handoff for patient on respiratory support
**When to use:** Testing detection of clinical oxygen terminology
**Example:**
```
This is a 2 year old female with bronchiolitis, currently on day 3 of illness.
She came in with increased work of breathing and is currently on 2 liters
nasal cannula with sats in the mid-90s. We tried weaning her to room air
overnight but she desaturated to 88, so we're keeping her on low flow for now.
Action items: continue supportive care, wean oxygen as tolerated.
If she tolerates room air for 4 hours, she can go home.
```
*~75 words, targets: "day 3 of illness" (duration), "low flow" (respiratory), "4 hours" (timeline)*

### Pattern 2: Realistic Script with Medication Dosing (TEST-02)
**What:** I-PASS handoff with medication timeline language
**When to use:** Testing detection of dosing schedules vs dates
**Example:**
```
Picking up this 5 year old with pneumonia, admitted three days ago.
He's been on ceftriaxone 50 milligrams per kilogram daily for the past
72 hours. Fever-free for two days now. Plan is to transition to oral
amoxicillin today if he tolerates PO. Mom is at bedside, dad is working
but can be reached by phone. No active concerns overnight.
```
*~70 words, targets: "three days ago" (duration), "72 hours" (duration), "two days" (duration)*

### Pattern 3: Edge-Case Script for Duration Phrases (TEST-03)
**What:** Script saturated with duration expressions
**When to use:** Stress-testing DATE_TIME deny list
**Example:**
```
This kid has had symptoms for about three days now — started with
two days of runny nose, then developed cough over the last 24 hours.
Parents gave Tylenol every six hours at home for the past day and a half.
Fever broke five hours ago. We're watching for another twelve hours
before considering discharge. If still afebrile tomorrow, can go home.
```
*~70 words, targets: multiple duration phrases that should NOT be flagged*

### Pattern 4: Edge-Case Script for Flow Terminology (TEST-04)
**What:** Script with respiratory flow phrases
**When to use:** Stress-testing LOCATION deny list
**Example:**
```
This infant was placed on high flow after arrival, currently on
high at 2 liters per kilogram. We tried weaning to low flow overnight
but she didn't tolerate it — desaturated pretty quickly on low.
Plan is to stay on high flow until tomorrow, then trial regular
nasal cannula. If she fails that, we'll bump back up to high.
```
*~65 words, targets: "high flow", "on high", "low flow", "on low" — words that get falsely flagged as LOCATION*

### Anti-Patterns to Avoid
- **Including real patient names:** Scripts should use placeholder names like "Sarah" or "Baby Smith" — these ARE PHI and SHOULD be redacted (that's correct behavior)
- **Making scripts too long:** Long scripts (>2 minutes) are harder to read naturally and don't add proportional value
- **Avoiding all PHI:** Scripts need some real PHI (names, ages) to verify true positives still work
- **Using Faker placeholders in recording scripts:** User can't naturally say "{{person}}" — expand to concrete values

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| I-PASS structure | New handoff format | Existing I-PASS mnemonic (I-P-A-S-S) | Industry gold standard, user already familiar with it |
| Audio recording | Custom recording app | Voice Memos / built-in recorder | Whisper handles phone audio; no special setup needed |
| False positive tracking | Custom database | Markdown file in `.planning/phases/10-*/` | Simple, version-controlled, integrates with project |
| PHI placeholders | New synthetic data | Real names from existing Faker output | Already have 500+ synthetic handoffs with realistic names |

**Key insight:** This phase is about USER ACTIONS (recording audio) and DOCUMENTATION (tracking false positives). The technical infrastructure already exists — no new code needed.

## Common Pitfalls

### Pitfall 1: Reading Scripts Too Formally
**What goes wrong:** User reads script like reading a news broadcast — robotic, too clear
**Why it happens:** Written scripts feel formal; clinical handoffs are conversational
**How to avoid:** Tell user to imagine they're handing off to a colleague, not reading to an audience. Include natural hesitations: "um", "like", "you know"
**Warning signs:** Transcription is too clean — no filler words or corrections

### Pitfall 2: Scripts Too Clean for Edge Cases
**What goes wrong:** Scripts avoid the exact patterns that cause over-detection
**Why it happens:** Natural writing avoids repetition; edge-case scripts need repetition
**How to avoid:** Edge-case scripts should SATURATE the target pattern — multiple "three days", "two weeks", "on high" in single script
**Warning signs:** Edge-case script only has 1-2 instances of target pattern

### Pitfall 3: Not Recording Enough Scripts
**What goes wrong:** User records 2-3 scripts, misses edge cases
**Why it happens:** Recording feels tedious; user underestimates value
**How to avoid:** Set explicit minimum: 6 realistic + 4 edge-case = 10 minimum
**Warning signs:** User asks "is 3 enough?"

### Pitfall 4: Forgetting to Document False Positives
**What goes wrong:** User processes audio, sees over-redaction, doesn't capture specifics
**Why it happens:** In-the-moment observation without systematic recording
**How to avoid:** Create template for documenting false positives BEFORE recording:
```markdown
## False Positive Log

### Script: [name]
- Input phrase: "three days of symptoms"
- Detected as: DATE_TIME
- Should be: NOT flagged (duration, not specific date)
```
**Warning signs:** User says "I saw some issues" but can't recall specifics

### Pitfall 5: Server Config Caching
**What goes wrong:** Deny list changes during testing don't take effect
**Why it happens:** `@lru_cache()` on `get_settings()` in `app/config.py`
**How to avoid:** Restart uvicorn server before each test session; document this prominently
**Warning signs:** Changes to deny list in config.py have no effect on output

## Code Examples

### Example: Interactive Testing Before Recording
```bash
# Test a script phrase before recording
python test_presidio.py -i
Input> This kid has had symptoms for three days now.
Output> This kid has had symptoms for [DATE_TIME] now.
# ^ This confirms "three days" triggers false positive
```

### Example: Processing Recorded Audio
```bash
# Start the server
uvicorn app.main:app --reload

# Upload audio via browser at http://localhost:8000
# OR use curl:
curl -X POST "http://localhost:8000/transcribe" \
  -F "file=@test_script_01.m4a"
```

### Example: False Positive Documentation Template
```markdown
## Script: respiratory_edge_case.m4a

### Transcription Result
Original: "She's currently on high flow at 2 liters per kg"
De-identified: "She's currently on [LOCATION] at 2 liters per kg"

### False Positive
- **Phrase:** "on high"
- **Detected as:** LOCATION
- **Expected:** NOT flagged (respiratory support terminology)
- **Deny list fix:** Add "high" to `deny_list_location` with word boundaries

### Additional Notes
- "flow" was NOT flagged (already in deny list? verify)
- "2 liters per kg" correctly preserved
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LLM-generated synthetic text | Faker-based templates + human recording | 2024-2025 | Ground truth labels guaranteed; no hallucination risk |
| Written test data only | Audio + transcription + detection | 2025-2026 | Tests full pipeline including Whisper artifacts |
| Manual ad-hoc testing | Systematic script categories | This phase | Reproducible, targeted edge case coverage |

**Deprecated/outdated:**
- Using ChatGPT to generate test scripts: Non-deterministic, no ground truth, may leak PHI patterns
- Recording real patient handoffs for testing: HIPAA violation; synthetic scripts only

## Open Questions

### 1. Optimal Script Length
- **What we know:** 30-60 seconds (75-150 words) matches natural handoff cadence
- **What's unclear:** Longer scripts might expose more edge cases per recording
- **Recommendation:** Start with 75-word scripts; extend to 150 if needed

### 2. Recording Environment
- **What we know:** Whisper handles phone-quality audio well
- **What's unclear:** Background noise impact on transcription accuracy vs. over-detection testing
- **Recommendation:** Quiet room, but don't obsess over perfect audio — testing transcription robustness is secondary goal

### 3. Number of Scripts Needed
- **What we know:** Requirements specify 6 realistic + 4 edge-case minimum
- **What's unclear:** Diminishing returns after how many scripts?
- **Recommendation:** Stop at 10-12 scripts unless new patterns emerge during testing

## Sources

### Primary (HIGH confidence)
- **Project codebase** — `tests/handoff_templates.py` (27 I-PASS templates), `tests/medical_providers.py` (clinical content), `test_presidio.py` (testing harness)
- **I-PASS Institute** — [I-PASS Mnemonic PDF](https://news.ipassinstitute.com/hubfs/I-PASS-mnemonic.pdf) — standard handoff structure
- **v2.1 Research Summary** — `.planning/research/SUMMARY.md` — known over-detection patterns (duration phrases, flow terminology)
- **SPOKEN_HANDOFF_ANALYSIS.md** — `docs/SPOKEN_HANDOFF_ANALYSIS.md` — what PHI is actually spoken during I-PASS handoffs

### Secondary (MEDIUM confidence)
- **GoTranscript QA Checklist** — [Transcript QA Checklist for Medical Teams](https://gotranscript.com/en/blog/transcript-qa-checklist-medical-teams-ai-transcription) — documentation best practices
- **PMC Clinical Handover Study** — [Benchmarking Clinical Speech Recognition](https://pmc.ncbi.nlm.nih.gov/articles/PMC4427705/) — synthetic patient profile methodology (101 handover records)
- **Google MedASR Research** — [Medical Speech to Text with MedASR](https://research.google/blog/next-generation-medical-image-interpretation-with-medgemma-15-and-medical-speech-to-text-with-medasr/) — evaluation metrics (WER, CER)

### Tertiary (LOW confidence)
- **WebSearch: Medical NLP synthetic data** — General guidance on combining synthetic + real data; not specific to this project's methodology

## Metadata

**Confidence breakdown:**
- Script structure: HIGH — I-PASS is industry gold standard, project already uses it
- Recording approach: HIGH — existing infrastructure proven with 27 real handoffs
- Edge-case patterns: HIGH — documented in v2.1 research (duration phrases, flow terms)
- Documentation workflow: MEDIUM — recommended template, user execution varies

**Research date:** 2026-01-28
**Valid until:** 2026-03-28 (60 days — stable domain, no anticipated tooling changes)

---

## Appendix: Suggested Script Templates

Below are 10 complete scripts ready for recording. User should read these conversationally, not like reading a formal document.

### Realistic Scripts (TEST-01, TEST-02)

**Script R1: RSV Bronchiolitis with Respiratory Support**
```
This is Sarah, a 14 month old with RSV bronchiolitis. She came in yesterday
with increased work of breathing and nasal congestion. Currently on 2 liters
nasal cannula, sats stable in the mid-90s. She's tolerating feeds okay but
tires easily. Mom Jessica is at bedside, dad can be reached at the number
in the chart. Plan is to wean oxygen as tolerated and discharge when stable
on room air. No active concerns overnight.
```

**Script R2: Pneumonia with Antibiotics**
```
Picking up James, a 5 year old with community-acquired pneumonia. Admitted
three days ago with fever and cough, started on IV ceftriaxone. He's been
afebrile for two days now and eating well. Plan today is to transition to
oral amoxicillin if he continues to tolerate PO. His mom is working but
available by phone. Follow up with pediatrician in one week after discharge.
```

**Script R3: Asthma Exacerbation**
```
This is a 7 year old named Michael with acute asthma exacerbation. Came
in last night with wheezing and increased work of breathing. We gave
three rounds of albuterol in the ER and started him on oral steroids.
He's improved significantly — peak flow went from 50% to 80% of predicted.
Currently on room air, breathing comfortably. Plan is observe for another
few hours and discharge with rescue inhaler and steroid taper.
```

**Script R4: Gastroenteritis with Dehydration**
```
Baby Thompson is a 10 month old with viral gastroenteritis. Parents say
she's had vomiting for about two days and diarrhea for the past day. She
was mildly dehydrated on arrival, got a fluid bolus in the ER. Now tolerating
Pedialyte by mouth without vomiting. Mom is at bedside and understands
discharge instructions. Plan is to observe one more feed and send home
if she keeps it down.
```

**Script R5: Febrile Infant Workup**
```
This is a 6 week old male, born full term, here for fever without source.
Temperature was 38.5 at home. We did the full sepsis workup — blood, urine,
and LP all sent. Started empiric ampicillin and ceftriaxone while awaiting
cultures. CSF looked clear. Parents are understandably anxious. Plan is to
continue antibiotics for 48 hours pending cultures. Dad is staying overnight.
```

**Script R6: Croup with Stridor**
```
Emily is a 2 year old with croup. She had the barky cough at home for about
a day, then developed stridor at rest this morning. Got racemic epi in the
ER with good response, also received dexamethasone. She's been in observation
for three hours now with no recurrent stridor. Plan is to watch for another
hour and discharge if she stays stable. Mom verbalized understanding of
return precautions.
```

### Edge-Case Scripts (TEST-03, TEST-04)

**Script E1: Duration Phrase Saturation**
```
So this patient has been symptomatic for about three days now. Started with
a runny nose two days ago, then the cough came on maybe a day and a half
ago. Parents were giving Tylenol every six hours for the past day or so.
Fever broke about five hours ago. We're planning to observe for another
twelve hours before making a decision. If she's still looking good tomorrow
morning, we'll probably send her home.
```

**Script E2: More Duration Phrases**
```
This is day 4 of illness for this kid. He was diagnosed with pneumonia
three days ago at urgent care. They started azithromycin — he's had four
doses over the past two days. Cough has been improving slowly over the
last 24 hours. Still has some decreased breath sounds on the right side.
Plan is to continue outpatient management and recheck in two to three days.
```

**Script E3: Flow Terminology Stress Test**
```
This infant was placed on high flow shortly after arrival. Currently on
high at 2 liters per kilogram, sats look good. We tried weaning to low
flow overnight but she didn't tolerate it — desaturated pretty quickly
on low. So plan is to stay on high flow for now, maybe try coming down
on high later today. If she fails that, we'll keep her on high until
she shows us she's ready.
```

**Script E4: Mixed Flow and Duration**
```
This 8 month old has been on high flow for the past two days. Initially
came in requiring pretty high support — we started at 2 liters per kg on
high. Over the last day and a half she's been weaning nicely. Currently
on low flow and tolerating it well. If she stays stable on low for another
six hours, we'll try room air. Parents are comfortable with the plan.
```
