# Phase 5: Validation & Compliance - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Validate PHI detection performance on real transcripts and achieve >95% recall for clinical deployment readiness. Tests the system beyond synthetic data, identifies remaining gaps through expert review, and creates publication-ready methodology documentation. MVP deployment for personal use; department rollout deferred to future phase.

</domain>

<decisions>
## Implementation Decisions

### Real Transcript Sourcing
- Two data sources: existing de-identified corpus AND IRB-approved prospective collection
- Existing data includes: prior QI project transcripts, de-identified research datasets, internal training recordings
- Target sample size: 200+ transcripts for rigorous validation with narrow confidence intervals
- IRB timeline: New submission needed (4-8 week dependency)
- Phased approach: Start validation immediately with existing de-identified data, add IRB data later
- Ground truth labeling: Single expert annotator (you, as clinician)
- Annotation method: Structured annotation tool for reproducibility

### Expert Review Process
- Reviewers: Potentially three-tier (you, peer clinician, compliance/privacy officer) — finalize during planning
- Review sample size: 10-20 transcripts (spot check for obvious issues)
- Feedback format: Annotated transcripts with direct markup and comments
- Acceptance threshold: No critical PHI missed — names/MRN must be caught, minor date variations acceptable

### Compliance Documentation
- Target audience: IRB/research submission
- Possible exemption: Project may qualify as knowledge production, not human research
- Documentation goal: Publication-ready methods section for academic paper
- Publication venue: Not decided — prepare for multiple targets (informatics journal, pediatrics journal, or conference)

### Deployment Readiness
- MVP definition: Personal use for your own handoffs, with future department rollout potential
- MVP gate: 95% recall on validation set (hard threshold)
- Department rollout requirements: Deferred to future phase
- Failure path: If validation shows <95% recall, return to Phase 4 for more pattern improvements

### Claude's Discretion
- Annotation tool selection (Prodigy, Label Studio, or alternative)
- Specific confidence interval calculation methodology
- Methods section structure and level of detail
- How to format error taxonomy for false negatives

</decisions>

<specifics>
## Specific Ideas

- "I think this might qualify for an exemption since it's for knowledge production and not human research"
- Three-tier review is aspirational — may simplify to just clinician review depending on availability
- Phased data approach allows progress without waiting for IRB approval

</specifics>

<deferred>
## Deferred Ideas

- Department-wide rollout requirements (IT security, compliance sign-off, user training) — future phase after MVP validated
- Institutional deployment considerations — out of scope for Phase 5

</deferred>

---

*Phase: 05-validation-compliance*
*Context gathered: 2026-01-23*
