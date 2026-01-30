# Phase 18: Guardian Edge Cases - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Catch possessive and appositive guardian name patterns that current detection misses. Patterns like "his mom Sarah", "the mom, Jessica", and "Grandma's here. Her name is Maria" should be detected without introducing false positives.

</domain>

<decisions>
## Implementation Decisions

### Possessive Patterns
- Detect pronoun + relationship + name patterns ("his mom Sarah", "her dad Tom")
- **Preserve pronoun + relationship in output**: "his mom Sarah" → "his mom [GUARDIAN_NAME]"
- **All possessive pronouns supported**: his, her, their, the patient's, baby's, child's
- **Require relationship word**: "his mom Sarah" ✔ but NOT "his Sarah" (reduces false positives)
- **Use full caregiver word list**: core family (mom, dad, mother, father, grandma, grandpa) + extended family (aunt, uncle, cousin, sibling, brother, sister) + all caregivers (guardian, foster parent, caregiver, babysitter)

### Appositive Patterns
- Detect relationship word followed by comma/punctuation/space + name ("the mom, Jessica")
- **Any punctuation pause**: comma, dash, or space between relationship and name
- **Optional 'the'**: Both "the mom, Jessica" and "mom, Jessica" detected
- **Same caregiver word list** as possessive patterns (consistency)

### Multi-Sentence Context
- **Yes, within limits**: Detect "Grandma's here. Her name is Maria" (cross-sentence)
- **Immediately following sentence only**: No gaps allowed between relationship mention and name
- Name must appear in the sentence directly after the relationship word mention

### Pattern Priority
- **GUARDIAN_NAME wins** over standard PERSON when both match (preserves relationship context)
- **Case-insensitive matching**: "his mom sarah" and "his mom Sarah" both detected (transcripts vary)
- **Full validation**: Run against entire validation set, check recall + precision for regressions

### Claude's Discretion
- Confidence score calibration for new patterns (may be lower than existing guardian patterns)
- Output formatting details for appositive patterns
- Which specific phrases trigger cross-sentence name capture (e.g., "her name is", "called", "named")

</decisions>

<specifics>
## Specific Ideas

- Cross-sentence detection should be conservative — only immediately following sentence
- The goal is catching edge cases that slip through, not comprehensive redesign
- Relationship context preservation is important for readability of redacted output

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 18-guardian-edge-cases*
*Context gathered: 2026-01-30*
