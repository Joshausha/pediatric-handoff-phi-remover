"""
I-PASS structured pediatric handoff templates for synthetic PHI dataset generation.

These templates follow the I-PASS framework:
- Illness Severity
- Patient Summary
- Action List
- Situation Awareness
- Synthesis by Receiver

Each template uses Faker placeholders ({{entity}}) that will be replaced with
synthetic PHI during generation, with span tracking for ground truth labels.
"""

# Comprehensive I-PASS pediatric handoff templates with PHI placeholders
# Format: {{entity_type}} for standard Faker, {{custom_type}} for custom providers

HANDOFF_TEMPLATES = [
    # ==========================================================================
    # ILLNESS SEVERITY + PATIENT SUMMARY (Heavy PHI)
    # ==========================================================================

    # Template 1: Standard admission with guardian contact
    "This is {{person}}, a {{pediatric_age}} previously healthy {{gender}} admitted on {{date}} "
    "with RSV bronchiolitis. Mom {{person}} is at bedside, dad can be reached at {{phone_number}}.",

    # Template 2: With MRN pickup
    "Picking up {{person}}, MRN {{mrn}}, born {{date}}, currently {{pediatric_age}}.",

    # Template 3: Baby LastName pattern
    "Baby {{last_name}} in PICU bed {{room_number}}, born {{date}}, currently {{pediatric_age}}. "
    "Mother {{person}} at bedside, father {{person}} available by phone.",

    # Template 4: Detailed demographics
    "{{person}}, {{mrn}}, is a {{pediatric_age}} {{gender}} with {{condition}} admitted "
    "from {{address}}. Primary caregiver is {{relationship}} {{person}}, contact {{phone_number}}.",

    # Template 5: Premature infant
    "This is Baby {{last_name}}, MRN {{mrn}}, former {{gestational_age}} weeker, now {{pediatric_age}} "
    "corrected. Parents {{person}} and {{person}} are at {{location}}.",

    # ==========================================================================
    # ACTION LIST (Task-focused with contacts)
    # ==========================================================================

    # Template 6: To-do with multiple contacts
    "To do: call {{person}} at {{phone_number}} with lab results. Lives at {{address}}. "
    "Primary pediatrician is Dr. {{last_name}}, office {{phone_number}}.",

    # Template 7: Consult follow-up
    "Action items for {{person}} in room {{room_number}}: "
    "1) GI consult following up - call Dr. {{last_name}} at {{phone_number}} "
    "2) Social work to see {{relationship}} {{person}} regarding {{service_need}} "
    "3) Discharge planning with case manager {{person}}.",

    # Template 8: Pending studies
    "{{person}}, MRN {{mrn}}, Room {{room_number}}: pending MRI at {{time}}, "
    "needs sedation consent from {{person}} (mom). NPO after midnight.",

    # Template 9: Medication reconciliation
    "Action list for {{person}}: verify home meds with {{relationship}} {{person}} at {{phone_number}}. "
    "Patient on {{medication}} from Dr. {{last_name}} at {{clinic_name}}.",

    # ==========================================================================
    # SITUATION AWARENESS (Contingency planning)
    # ==========================================================================

    # Template 10: Escalation contacts
    "If concerns about {{person}} in bed {{room_number}}, contact attending {{person}} "
    "at extension {{phone_number}}. Backup is Dr. {{last_name}} (fellow) pager {{pager_number}}.",

    # Template 11: Critical thresholds
    "For {{person}}, MRN {{mrn}}: if temp >38.5 or sats <90%, call {{person}} (fellow) "
    "and notify family ({{person}} at {{phone_number}}).",

    # Template 12: Code status
    "{{person}} is DNR/DNI per discussion with {{relationship}} {{person}} on {{date}}. "
    "Ethics consult by Dr. {{last_name}} documented. Palliative team following.",

    # ==========================================================================
    # MINIMAL PHI (Clinical content heavy)
    # ==========================================================================

    # Template 13: Purely clinical status
    "Stable on current regimen. Continue {{medication}} and monitor for {{symptom}}. "
    "Vitals stable, lungs clear, tolerating PO. No active concerns overnight.",

    # Template 14: Clinical plan
    "{{pediatric_age}} with {{condition}}, day {{number}} of antibiotics. "
    "Afebrile x48 hours, CRP trending down. Plan to transition to oral {{medication}} "
    "tomorrow if continues to improve. Family aware.",

    # Template 15: Simple update
    "Overnight, patient remained stable on {{respiratory_support}}. "
    "Continue current management. No changes to plan.",

    # ==========================================================================
    # COMPLEX SCENARIOS (Multiple PHI types)
    # ==========================================================================

    # Template 16: Multi-generational family
    "{{person}}, {{pediatric_age}}, brought in by grandma {{person}} from {{address}}. "
    "Mom {{person}} incarcerated, dad {{person}} not involved. "
    "Legal guardian is aunt {{person}} at {{phone_number}}. DCF case worker is {{person}}.",

    # Template 17: School-age with school contact
    "{{person}}, {{pediatric_age}} from {{school_name}}, admitted for {{condition}}. "
    "School nurse {{person}} at {{phone_number}} has rescue meds. "
    "Lives at {{address}} with {{relationship}} {{person}}.",

    # Template 18: Transfer summary
    "Transferred {{person}}, MRN {{mrn}}, from {{hospital_name}} for {{service}}. "
    "Referring physician Dr. {{last_name}} at {{phone_number}}. "
    "Family en route from {{city}}, ETA {{time}}.",

    # Template 19: Discharge planning
    "{{person}} ready for discharge to {{address}}. "
    "Follow up with Dr. {{last_name}} on {{date}} at {{time}}. "
    "Prescriptions sent to {{pharmacy}} at {{phone_number}}. "
    "{{relationship}} {{person}} verbalized understanding.",

    # Template 20: NICU handoff
    "Baby {{last_name}}, MRN {{mrn}}, DOL {{number}}, born {{date}} at {{time}} via {{delivery_type}} "
    "to {{person}}. Current weight {{weight}}. In isolette {{room_number}}. "
    "Dad {{person}} visited today, staying at RMH room {{room_number}}.",

    # ==========================================================================
    # EMAIL AND DIGITAL CONTACT PATTERNS
    # ==========================================================================

    # Template 21: Email coordination
    "Care coordinator {{person}} requests discharge summary to {{email}}. "
    "Insurance prior auth contact is {{person}} at {{phone_number}}.",

    # Template 22: Portal message
    "{{person}}'s {{relationship}} {{person}} sent MyChart message regarding {{concern}}. "
    "Account email: {{email}}. Please respond through portal or call {{phone_number}}.",

    # ==========================================================================
    # DETAILED AGE PATTERNS
    # ==========================================================================

    # Template 23: Newborn age
    "{{person}}, DOB {{date}}, currently {{pediatric_age}}, here for {{condition}}. "
    "Born at {{gestational_age}} weeks at {{hospital_name}}.",

    # Template 24: Adolescent
    "{{person}}, {{pediatric_age}}, presents with {{condition}}. "
    "Patient requests {{person}} ({{relationship}}) not be contacted. "
    "Emergency contact is {{person}} at {{phone_number}}.",

    # ==========================================================================
    # VARIED MRN FORMATS
    # ==========================================================================

    # Template 25: Hash MRN format
    "Picking up patient #{{mrn_numeric}}, {{person}}, from bed {{room_number}}.",

    # Template 26: Labeled MRN
    "Medical record number: {{mrn_numeric}} for {{person}}, {{pediatric_age}}.",

    # Template 27: EMR reference
    "See EMR {{mrn}} for {{person}}'s full history. "
    "Previous admission {{date}} for same diagnosis.",
]

# Alternative minimal PHI templates for balance
MINIMAL_PHI_TEMPLATES = [
    "Stable overnight. Continue supportive care.",
    "No events overnight. Plan unchanged.",
    "Improving on current regimen. Tolerating PO.",
    "Labs pending from this morning. Will reassess.",
    "Ready for discharge once teaching complete.",
    "Continue {{medication}} q{{frequency}}. Monitor {{parameter}}.",
    "Day {{number}} of {{treatment}}. Trending in right direction.",
    "Afebrile, tolerating feeds, good UOP. No concerns.",
]

# Templates with specific clinical scenarios (for realistic mix)
CLINICAL_HEAVY_TEMPLATES = [
    "{{pediatric_age}} with bronchiolitis on {{respiratory_support}}, currently requiring "
    "{{fio2}}% FiO2 with sats {{saturation}}%. Weaning as tolerated, target sats >{{target_sat}}%.",

    "Former {{gestational_age}} weeker with BPD, baseline {{respiratory_support}}. "
    "Here with viral URI, increased work of breathing. Currently on {{current_support}}.",

    "{{pediatric_age}} with {{condition}}, received {{medication}} in ED at {{time}}. "
    "Repeat exam in {{hours}} hours. If worsening, start {{escalation_med}}.",

    "Status asthmaticus, on continuous albuterol since {{time}}. "
    "Last ABG: pH {{ph}}, pCO2 {{pco2}}, pO2 {{po2}}. Trending {{trend_direction}}.",

    "Febrile neutropenia, ANC {{anc}}. Cultures sent {{time}}, started {{antibiotic}}. "
    "Monitor for deterioration, low threshold for ICU transfer.",
]

# =============================================================================
# ADVERSARIAL TEMPLATES - Edge cases for PHI detection stress testing
# =============================================================================

# Speech artifacts: stutters, corrections, hesitations typical in speech-to-text
SPEECH_ARTIFACT_TEMPLATES = [
    # Stutters and filler words
    "Um, this is uh {{person}}, a {{pediatric_age}} old with um {{condition}}.",
    "So, like, contact {{person}} at like {{phone_number}} for uh questions.",
    "The uh the patient {{person}} was seen on um {{date}}.",
    "Room room {{room_number}}, I mean room {{room_number}}, for {{person}}.",

    # Self-corrections common in dictation
    "Patient is John no wait {{person}}, age {{pediatric_age}}.",
    "Call mom at 555 uh {{phone_number}} for updates.",
    "MRN is 12 no sorry {{mrn}} for this patient.",
    "Admitted to bed 12 I mean {{room_number}} on {{date}}.",

    # Hesitation mid-name
    "Contact parent, um, {{person}}, at {{phone_number}}.",
    "The attending, uh, Dr. {{last_name}}, will follow up.",
]

# Cultural name diversity patterns
DIVERSE_NAME_TEMPLATES = [
    # Hispanic names with multiple surnames
    "Patient {{person}} admitted to {{room_number}} with {{condition}}.",
    "Mom {{person}} can be reached at {{phone_number}}.",
    "Dad {{person}} present at bedside, email {{email}}.",

    # Hyphenated names
    "Attending is Dr. {{last_name}} on service.",
    "Contact {{person}} at {{phone_number}} for family updates.",

    # Names with titles/suffixes
    "Patient {{person}} Jr., age {{pediatric_age}}, has {{condition}}.",
    "Grandmother {{person}} is primary caregiver.",
]

# Edge case word boundaries and punctuation
BOUNDARY_EDGE_TEMPLATES = [
    # Start of line/sentence (lookbehind edge case)
    "{{person}} is a {{pediatric_age}} old admitted for {{condition}}.",
    "{{phone_number}} is the callback number for the family.",
    "{{room_number}} is where patient will be transferred.",

    # End of line/sentence
    "Patient admitted is {{person}}.",
    "Family contact: {{person}}.",
    "Best number to call: {{phone_number}}.",

    # Punctuation adjacent to PHI
    "Call ({{phone_number}}) for updates.",
    "Patient: {{person}}, MRN: {{mrn}}.",
    "Room: {{room_number}}; Bed: A.",
    "Email: <{{email}}>",

    # Comma-separated lists
    "Present: {{person}}, {{person}}, and nurse.",
    "Contacts: {{phone_number}}, {{phone_number}}.",
    "Seen on {{date}}, {{date}}, and {{date}}.",

    # Reversed relationship patterns (miss "Jessica is Mom")
    "{{person}} is mom and primary decision maker.",
    "{{person}} is dad, cell {{phone_number}}.",
    "{{person}} is the grandmother, contact at {{email}}.",

    # Lowercase relationship words
    "mom {{person}} at bedside.",
    "dad {{person}} called for update.",
    "patient {{person}} stable overnight.",
]

# Transcription errors and misheard words
TRANSCRIPTION_ERROR_TEMPLATES = [
    # Numbers that could be misheard
    "MRN {{mrn}}, or is it {{mrn}}? Please verify.",
    "Call {{phone_number}} or {{phone_number}} for mom.",
    "Weight is {{weight}} kg, repeat {{weight}} kilograms.",

    # Words that sound like PHI
    "Patient stable on NC, not in NC (the state).",
    "Give IV fluids, patient from OR (operating room).",
    "Patient in ER, not from the city called ER.",

    # Partial information repeated
    "{{person}}... {{person}} is the patient name.",
    "Room {{room_number}}, that's {{room_number}}.",
    "Email again: {{email}}, {{email}}.",
]

# Complex compound patterns
COMPOUND_PATTERN_TEMPLATES = [
    # Multiple PHI in close proximity
    "{{person}} (MRN {{mrn}}) admitted to {{room_number}} on {{date}}.",
    "Mom {{person}} ({{phone_number}}) and dad {{person}} ({{phone_number}}) available.",
    "Patient {{person}}, {{pediatric_age}}, from {{city}}, MRN {{mrn}}.",

    # PHI embedded in clinical context
    "If {{person}}'s condition worsens, call {{phone_number}} immediately.",
    "{{person}} at {{email}} is the case manager.",
    "Transfer to {{room_number}} per Dr. {{last_name}}.",

    # Nested context (harder to parse)
    "According to mom ({{person}}), patient ({{person}}) has {{condition}}.",
    "Dr. {{last_name}} spoke with {{person}} at {{phone_number}} on {{date}}.",
]

# Age patterns that are tricky
AGE_EDGE_TEMPLATES = [
    # Non-standard age formats
    "Baby is {{pediatric_age}} old.",
    "Infant born on {{date}}, now {{pediatric_age}}.",
    "Patient is approximately {{pediatric_age}}.",

    # Ages that look like other numbers
    "3 week old patient, weight 3.2kg.",
    "5 day old infant in room 5.",
    "Patient 2 years 3 months, give 2.3 mL.",
]

# Combine all adversarial templates
ADVERSARIAL_TEMPLATES = (
    SPEECH_ARTIFACT_TEMPLATES +
    DIVERSE_NAME_TEMPLATES +
    BOUNDARY_EDGE_TEMPLATES +
    TRANSCRIPTION_ERROR_TEMPLATES +
    COMPOUND_PATTERN_TEMPLATES +
    AGE_EDGE_TEMPLATES
)

# All templates combined for generation
ALL_TEMPLATES = HANDOFF_TEMPLATES + MINIMAL_PHI_TEMPLATES + CLINICAL_HEAVY_TEMPLATES
