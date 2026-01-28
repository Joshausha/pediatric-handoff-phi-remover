# Test Scripts for PHI Detection Testing

## Purpose

These scripts are designed to test the PHI detection system with realistic pediatric handoff scenarios and edge cases targeting known over-detection patterns.

## Structure

```
tests/test_scripts/
├── realistic/          # 6 realistic I-PASS handoff scripts (R1-R6)
├── edge_cases/         # 4 edge-case scripts for specific patterns (E1-E4)
└── recordings/         # Save your audio recordings here
```

## Scripts

### Realistic Scripts (R1-R6)

These simulate actual pediatric handoffs with typical PHI:

- **R1**: RSV Bronchiolitis with Respiratory Support
- **R2**: Pneumonia with Antibiotics
- **R3**: Asthma Exacerbation
- **R4**: Gastroenteritis with Dehydration
- **R5**: Febrile Infant Workup
- **R6**: Croup with Stridor

### Edge-Case Scripts (E1-E4)

These stress-test specific over-detection patterns identified in research:

- **E1**: Duration Phrase Saturation (tests duration phrase handling)
- **E2**: More Duration Phrases (additional duration patterns)
- **E3**: Flow Terminology Stress Test (tests "high flow" vs "high" location)
- **E4**: Mixed Flow and Duration (combination stress test)

## Recording Instructions

### Before Recording

1. Review the script briefly
2. Choose a quiet environment
3. Use your phone's voice recorder or computer microphone
4. Aim for natural, conversational delivery

### Recording Tips

- **Read conversationally**, not formally
- Include natural hesitations and pauses (um, uh)
- Each script should take about 60-90 seconds when read naturally
- Don't worry about being perfect - natural speech is the goal
- Save recordings with descriptive names (e.g., `r1_rsv_bronchiolitis.m4a`)

### After Recording

1. Save all recordings to `tests/test_scripts/recordings/`
2. Process each recording through the web app
3. Document any false positives in `.planning/phases/10-test-script-generation/FALSE_POSITIVE_LOG.md`

## Expected Duration

- **Total recording time**: ~15 minutes (10 scripts × 1.5 minutes each)
- **Processing time**: ~5-10 minutes per recording
- **Total session**: 1-2 hours including documentation

## False Positive Documentation

When processing recordings, watch for:

- Medical abbreviations flagged as LOCATION (NC, OR, ER)
- Duration phrases flagged as DATE_TIME ("three days of symptoms")
- Flow terminology flagged as LOCATION ("currently on high")
- Unit names removed during ROOM redaction ("PICU bed 12" → "bed [ROOM]")

Document all findings in `FALSE_POSITIVE_LOG.md` for systematic deny list updates.

## Next Steps

After completing all recordings and documentation:

1. Batch process all recordings through the web app
2. Review FALSE_POSITIVE_LOG.md for patterns
3. Create targeted deny list updates based on findings
4. Re-test to verify fixes

---

**Last Updated**: 2026-01-28
