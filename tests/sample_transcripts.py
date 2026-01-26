"""
Sample pediatric handoff transcripts for testing de-identification.

These represent realistic clinical language with various PHI patterns.
"""

# Sample transcripts with expected PHI elements
SAMPLE_TRANSCRIPTS = [
    {
        "id": 1,
        "text": "This is Sarah, she's a 4 year old previously healthy female admitted yesterday with RSV bronchiolitis. She's currently stable on 2 liters nasal cannula. Mom Jessica is at bedside, dad can be reached at 555-867-5309. Continue supportive care, wean oxygen as tolerated, target sats above 90. She has a CXR pending from this morning.",
        "phi_elements": ["patient_name", "guardian_name", "phone_number", "date_reference"],
        "expected_removed": ["Sarah", "Jessica", "555-867-5309", "yesterday"],
        "expected_preserved": ["bronchiolitis", "RSV", "CXR", "nasal cannula", "oxygen"]
    },
    {
        "id": 2,
        "text": "Picking up Michael Thompson, MRN 12345678, a 2 month old former 35 weeker with BPD on home O2, here with bronchiolitis. Currently on high flow at 2 liters per kilo with FiO2 of 60%. To do: blood gas at midnight, continue nebs every 4 hours, strict I/Os. Parents are John and Mary Thompson, they're at the Ronald McDonald House and can be reached at 555-0123.",
        "phi_elements": ["patient_name", "mrn", "guardian_names", "phone_number", "location"],
        "expected_removed": ["Michael Thompson", "12345678", "John", "Mary Thompson", "555-0123"],  # Note: "Ronald McDonald House" not PHI - well-known charity
        "expected_preserved": ["bronchiolitis", "BPD", "FiO2", "blood gas", "high flow"]
    },
    {
        "id": 3,
        "text": "This is Baby Martinez in PICU bed 7, born January 15th, currently 3 weeks 2 days old. Former 28 weeker with grade 2 IVH, now on room air. Grandma Rosa is primary caregiver, parents are not involved. She's been stable overnight, planning discharge tomorrow if feeding volumes stay up.",
        "phi_elements": ["patient_name", "detailed_age", "room_number", "guardian_name", "date"],
        "expected_removed": ["Martinez", "bed 7", "January 15th", "Rosa", "3 weeks 2 days"],
        "expected_preserved": ["IVH", "PICU", "room air", "discharge", "feeding"]
    },
    {
        "id": 4,
        "text": "Signing out Tommy Wilson, 8 year old with asthma exacerbation. Lives at 425 Oak Street, goes to Jefferson Elementary. School nurse can be reached at 555-9012 if questions about his action plan. Currently on continuous albuterol, last ABG showed improving respiratory acidosis.",
        "phi_elements": ["patient_name", "address", "school_name", "phone_number"],
        "expected_removed": ["Tommy Wilson", "425 Oak Street", "Jefferson Elementary", "555-9012"],
        "expected_preserved": ["asthma", "albuterol", "ABG", "respiratory acidosis"]
    },
    {
        "id": 5,
        "text": "Stable 6 year old, day 3 of IV antibiotics for cellulitis. Afebrile x 48 hours, erythema improving. Continue current regimen, anticipate transition to oral antibiotics tomorrow. Family updated and agreeable to plan. No active issues overnight.",
        "phi_elements": ["minimal_phi"],
        "expected_removed": [],  # Minimal PHI - mostly clinical content
        "expected_preserved": ["cellulitis", "antibiotics", "erythema", "afebrile"]
    }
]


# Expected de-identification outputs for validation
EXPECTED_OUTPUTS = {
    1: {
        "input": "This is Sarah, she's a 4 year old previously healthy female admitted yesterday with RSV bronchiolitis. Mom Jessica is at bedside, dad can be reached at 555-867-5309.",
        "expected_markers": ["[NAME]", "[PHONE]"],
        "should_contain": ["4 year old", "bronchiolitis", "bedside"]
    },
    2: {
        "input": "Picking up Michael Thompson, MRN 12345678, a 2 month old former 35 weeker",
        "expected_markers": ["[NAME]", "[MRN]", "[AGE]"],  # v1.0: "35 weeker" redacted as gestational age
        "should_contain": ["2 month old"]  # Note: "35 weeker" now correctly redacted as [AGE]
    },
    3: {
        "input": "Baby Martinez in PICU bed 7, born January 15th, currently 3 weeks 2 days old. Grandma Rosa is primary caregiver.",
        "expected_markers": ["[NAME]", "[ROOM]", "[DATE]"],
        "should_contain": ["PICU", "primary caregiver"]
    },
    4: {
        "input": "Tommy Wilson, 8 year old with asthma. Lives at 425 Oak Street, goes to Jefferson Elementary.",
        "expected_markers": ["[NAME]", "[LOCATION]"],
        "should_contain": ["8 year old", "asthma"]
    },
    5: {
        "input": "Stable 6 year old, day 3 of IV antibiotics for cellulitis. Afebrile x 48 hours.",
        "expected_markers": [],  # No markers expected
        "should_contain": ["cellulitis", "antibiotics", "Afebrile"]
    }
}
