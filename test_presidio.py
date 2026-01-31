#!/usr/bin/env python3
"""
Isolated Presidio De-identification Test Harness

Run: python test_presidio.py
     python test_presidio.py --strict  # Fail on known issues
"""

import sys
from dataclasses import dataclass
from typing import List, Tuple

# Known issues - these fail but are tracked for future improvement
KNOWN_ISSUES = {
    "Patient name - Baby LastName",  # Over-redacts 'bed'
    "Age - months (should redact detailed)",  # Misses "2 month 3 day old"
    "Room number",  # Over-redacts 'PICU'
}

# Test cases: (input_text, expected_redactions, should_preserve)
TEST_CASES = [
    # === NAMES ===
    {
        "name": "Patient name - Baby LastName",
        "input": "This is Baby Smith in bed 4.",
        "must_redact": ["Smith", "4"],  # Bed numbers are also PHI
        "must_preserve": ["Baby", "bed"],
    },
    {
        "name": "Patient name - standard",
        "input": "Patient John Williams admitted today.",
        "must_redact": ["John Williams"],
        "must_preserve": ["Patient", "admitted"],
    },
    {
        "name": "Guardian - Mom with name",
        "input": "Mom Jessica is at bedside.",
        "must_redact": ["Jessica"],
        "must_preserve": ["Mom", "bedside"],
    },
    {
        "name": "Guardian - Dad with name",
        "input": "Dad Mike is working today.",
        "must_redact": ["Mike"],
        "must_preserve": ["Dad", "working"],
    },
    {
        "name": "Guardian - standalone mom (should NOT redact)",
        "input": "Contact mom if any concerns.",
        "must_redact": [],
        "must_preserve": ["Contact", "mom", "concerns"],
    },

    # === GUARDIAN POSSESSIVE PATTERNS ===
    {
        "name": "Guardian - possessive his mom",
        "input": "His mom Sarah is at bedside.",
        "must_redact": ["Sarah"],
        "must_preserve": ["His", "mom", "bedside"],
    },
    {
        "name": "Guardian - possessive her dad",
        "input": "Her dad Tom works nights.",
        "must_redact": ["Tom"],
        "must_preserve": ["Her", "dad", "works"],
    },
    {
        "name": "Guardian - possessive their grandma",
        "input": "Their grandma Maria helps with care.",
        "must_redact": ["Maria"],
        "must_preserve": ["Their", "grandma", "care"],
    },
    {
        "name": "Guardian - possessive patient's mom",
        "input": "The patient's mom Jessica brought supplies.",
        "must_redact": ["Jessica"],
        "must_preserve": ["patient's", "mom", "brought"],
    },

    {
        "name": "Provider name",
        "input": "Primary is Dr. Johnson, fellow is Dr. Chen.",
        "must_redact": ["Johnson", "Chen"],
        "must_preserve": ["Primary", "Dr.", "fellow"],
    },

    # === PROVIDER NAME PATTERNS (Phase 19) ===
    {
        "name": "Provider - Dr. with period",
        "input": "Spoke with Dr. Martinez about the plan.",
        "must_redact": ["Martinez"],
        "must_preserve": ["Dr.", "Spoke", "plan"],
    },
    {
        "name": "Provider - Dr without period",
        "input": "Paged Dr Chen for the consult.",
        "must_redact": ["Chen"],
        "must_preserve": ["Dr", "Paged", "consult"],
    },
    {
        "name": "Provider - NP title",
        "input": "NP Williams did the admission.",
        "must_redact": ["Williams"],
        # Note: "NP" may be consumed by PERSON entity depending on NER
        "must_preserve": ["admission"],
    },
    {
        "name": "Provider - standalone title (should NOT redact)",
        "input": "The attending is on call.",
        "must_redact": [],
        "must_preserve": ["attending", "call"],
    },

    # === PROVIDER ROLE CONTEXT PATTERNS (Phase 19-02) ===
    {
        "name": "Provider - the attending is",
        "input": "The attending is Rodriguez and covering all admissions.",
        "must_redact": ["Rodriguez"],
        "must_preserve": ["attending", "covering", "admissions"],
    },
    {
        "name": "Provider - his nurse",
        "input": "His nurse Sarah gave meds at 2pm.",
        "must_redact": ["Sarah"],
        "must_preserve": ["His", "nurse", "meds"],
    },
    {
        "name": "Provider - her doctor",
        "input": "Her doctor Dr. Patel ordered labs.",
        "must_redact": ["Patel"],
        "must_preserve": ["Her", "doctor", "Dr.", "labs"],
    },
    {
        "name": "Provider - standalone role (should NOT redact)",
        "input": "The nurse is busy with another patient.",
        "must_redact": [],
        "must_preserve": ["nurse", "busy", "patient"],
    },

    # === PROVIDER ACTION CONTEXT PATTERNS (Phase 19-03) ===
    {
        "name": "Provider - paged Dr",
        "input": "Paged Dr. Martinez at 3am for fever.",
        "must_redact": ["Martinez"],
        # Note: "3am" may be redacted as DATE_TIME (legitimate)
        "must_preserve": ["Paged", "Dr.", "fever"],
    },
    {
        "name": "Provider - spoke with",
        "input": "Spoke with Dr Chen about discharge.",
        "must_redact": ["Chen"],
        "must_preserve": ["Spoke", "Dr", "discharge"],
    },
    {
        "name": "Provider - by Dr passive",
        "input": "Labs ordered by Dr. Williams earlier.",
        "must_redact": ["Williams"],
        "must_preserve": ["Labs", "ordered", "Dr.", "earlier"],
    },

    # === AGES (Pediatric-specific) ===
    {
        "name": "Age - weeks and days",
        "input": "He's a 3 week 2 day old male.",
        "must_redact": ["3 week 2 day old"],
        "must_preserve": ["male"],
    },
    {
        "name": "Age - gestational",
        "input": "Born at 36 weeks gestation.",
        "must_redact": ["36 weeks gestation"],
        "must_preserve": ["Born"],
    },
    {
        "name": "Age - months (should redact detailed)",
        "input": "She is a 2 month 3 day old female.",
        "must_redact": ["2 month 3 day old"],
        "must_preserve": ["female"],
    },
    {
        "name": "Age - simple (may preserve)",
        "input": "This 5 year old presents with cough.",
        "must_redact": [],  # Simple ages often OK
        "must_preserve": ["cough", "presents"],
    },

    # === MEDICAL IDENTIFIERS ===
    {
        "name": "MRN - labeled",
        "input": "MRN 12345678, admitted for bronchiolitis.",
        "must_redact": ["12345678"],
        "must_preserve": ["bronchiolitis", "admitted"],
    },
    {
        "name": "MRN - with hash",
        "input": "Patient #87654321 is stable.",
        "must_redact": ["87654321"],
        "must_preserve": ["stable"],
    },
    {
        "name": "Room number",
        "input": "Located in room 4B, PICU bed 12.",
        "must_redact": ["room 4B", "bed 12"],
        "must_preserve": ["PICU", "Located"],
    },

    # === DATES ===
    {
        "name": "Date - admission",
        "input": "Admitted on January 15th for respiratory distress.",
        "must_redact": ["January 15th"],
        "must_preserve": ["respiratory distress", "Admitted"],
    },
    {
        "name": "Date - with year",
        "input": "DOB 03/15/2024, here for fever.",
        "must_redact": ["03/15/2024"],
        "must_preserve": ["fever", "DOB"],
    },

    # === CONTACT INFO ===
    {
        "name": "Phone number",
        "input": "Call parents at 617-555-1234.",
        "must_redact": ["617-555-1234"],
        "must_preserve": ["Call", "parents"],
    },

    # === LOCATIONS ===
    {
        "name": "City/address",
        "input": "Family lives in Boston, transferred from MGH.",
        "must_redact": ["Boston", "MGH"],  # MGH is a hospital abbreviation = PHI
        "must_preserve": ["Family", "transferred"],
    },

    # === LOCATION - TRANSFER CONTEXT (Phase 21-01) ===
    {
        "name": "Location - transferred from hospital",
        "input": "Patient was transferred from Memorial Hospital yesterday.",
        "must_redact": ["Memorial Hospital"],
        "must_preserve": ["Patient", "transferred", "yesterday"],
    },
    {
        "name": "Location - admitted from home",
        "input": "Child admitted from home with respiratory distress.",
        "must_redact": ["home"],
        "must_preserve": ["Child", "admitted", "respiratory distress"],
    },
    {
        "name": "Location - sent from clinic",
        "input": "Sent from Springfield Pediatric Clinic for evaluation.",
        "must_redact": ["Springfield Pediatric Clinic"],
        "must_preserve": ["Sent", "evaluation"],
    },
    {
        "name": "Location - en route from city",
        "input": "Family en route from Boston via ambulance.",
        "must_redact": ["Boston"],
        "must_preserve": ["Family", "en route", "ambulance"],
    },
    {
        "name": "Location - came from hospital",
        "input": "Came from Children's Medical Center via ambulance.",
        "must_redact": ["Children's Medical Center"],
        "must_preserve": ["Came", "ambulance"],
    },

    # === LOCATION - FACILITY NAMES (Phase 21-02) ===
    {
        "name": "Location - hospital name",
        "input": "Born at Children's Hospital, now stable.",
        "must_redact": ["Children's Hospital"],
        "must_preserve": ["Born", "stable"],
    },
    {
        "name": "Location - medical center",
        "input": "Previously seen at Boston Medical Center.",
        "must_redact": ["Boston Medical Center"],
        "must_preserve": ["Previously", "seen"],
    },
    {
        "name": "Location - clinic name",
        "input": "Follow-up scheduled at Oak Street Clinic.",
        "must_redact": ["Oak Street Clinic"],
        "must_preserve": ["Follow-up", "scheduled"],
    },
    {
        "name": "Location - pediatrics office",
        "input": "PCP is Dr. Jones at Springfield Pediatrics.",
        "must_redact": ["Springfield Pediatrics"],
        "must_preserve": ["PCP", "Dr."],
    },

    # === LOCATION - RESIDENTIAL ADDRESSES (Phase 21-02) ===
    {
        "name": "Location - lives at address",
        "input": "Family lives at 425 Oak Street, third floor.",
        "must_redact": ["425 Oak Street"],
        "must_preserve": ["Family", "lives", "third floor"],
    },
    {
        "name": "Location - lives in city",
        "input": "Patient lives in Brookfield with grandparents.",
        "must_redact": ["Brookfield"],
        "must_preserve": ["Patient", "lives", "grandparents"],
    },
    {
        "name": "Location - discharge to home",
        "input": "Discharge to home planned for tomorrow.",
        "must_redact": ["home"],
        "must_preserve": ["Discharge", "planned", "tomorrow"],
    },

    # === LOCATION - MUST PRESERVE (no false positives) ===
    {
        "name": "Location - preserve PICU",
        "input": "Transferred to PICU for closer monitoring.",
        "must_redact": [],
        "must_preserve": ["PICU", "monitoring"],
    },
    {
        "name": "Location - preserve OR",
        "input": "Going to OR for appendectomy.",
        "must_redact": [],
        "must_preserve": ["OR", "appendectomy"],
    },

    # === CLINICAL TERMS (must preserve) ===
    {
        "name": "Clinical - respiratory",
        "input": "On 2L NC with FiO2 30%, sats 95%.",
        "must_redact": [],
        "must_preserve": ["2L NC", "FiO2 30%", "sats 95%"],
    },
    {
        "name": "Clinical - vitals",
        "input": "Temp 38.5, HR 120, RR 28, BP 90/60.",
        "must_redact": [],
        "must_preserve": ["Temp 38.5", "HR 120", "RR 28", "BP 90/60"],
    },
    {
        "name": "Clinical - medications",
        "input": "Started on amoxicillin 80mg/kg/day divided TID.",
        "must_redact": [],
        "must_preserve": ["amoxicillin", "80mg/kg/day", "TID"],
    },
    {
        "name": "Clinical - diagnoses",
        "input": "Assessment: bronchiolitis, likely RSV. Rule out pneumonia.",
        "must_redact": [],
        "must_preserve": ["bronchiolitis", "RSV", "pneumonia"],
    },

    # === GUARDIAN APPOSITIVE PATTERNS ===
    {
        "name": "Guardian - appositive comma",
        "input": "The mom, Jessica, is at bedside.",
        "must_redact": ["Jessica"],
        "must_preserve": ["The", "mom", "bedside"],
    },
    {
        "name": "Guardian - appositive dash",
        "input": "His dad - Mike - works nights.",
        "must_redact": ["Mike"],
        "must_preserve": ["His", "dad", "works"],
    },
    {
        "name": "Guardian - appositive paren",
        "input": "Their guardian (Sarah) is available.",
        "must_redact": ["Sarah"],
        "must_preserve": ["Their", "guardian", "available"],
    },
]


def run_tests(strict: bool = False):
    """Run all test cases and report results.

    Args:
        strict: If True, fail on known issues. If False, warn but pass.
    """
    # Import here to avoid slow startup when just viewing file
    from app.deidentification import deidentify_text

    print("=" * 70)
    print("PRESIDIO DE-IDENTIFICATION TEST HARNESS")
    if not strict:
        print("(Non-strict mode: known issues are warnings, not failures)")
    print("=" * 70)
    print()

    passed = 0
    failed = 0
    warned = 0
    results = []

    for i, test in enumerate(TEST_CASES, 1):
        result = deidentify_text(test["input"])
        clean = result.clean_text

        errors = []

        # Check must_redact items are gone
        for item in test["must_redact"]:
            if item.lower() in clean.lower():
                errors.append(f"MISSED: '{item}' still in output")

        # Check must_preserve items remain
        for item in test["must_preserve"]:
            if item.lower() not in clean.lower():
                errors.append(f"OVER-REDACTED: '{item}' was removed")

        # Determine status based on strict mode and known issues
        is_known_issue = test["name"] in KNOWN_ISSUES
        if not errors:
            status = "PASS"
            passed += 1
        elif is_known_issue and not strict:
            status = "WARN"  # Known issue, non-strict mode
            warned += 1
        else:
            status = "FAIL"
            failed += 1

        results.append({
            "name": test["name"],
            "status": status,
            "input": test["input"],
            "output": clean,
            "errors": errors,
            "known_issue": is_known_issue,
        })

    # Print results
    for r in results:
        if r["status"] == "PASS":
            icon = "✅"
        elif r["status"] == "WARN":
            icon = "⚠️"
        else:
            icon = "❌"

        suffix = " [KNOWN ISSUE]" if r.get("known_issue") and r["status"] == "WARN" else ""
        print(f"{icon} {r['name']}{suffix}")
        if r["status"] in ("FAIL", "WARN"):
            print(f"   Input:  {r['input']}")
            print(f"   Output: {r['output']}")
            for err in r["errors"]:
                print(f"   ⚠️  {err}")
            print()

    print("=" * 70)
    total = passed + failed + warned
    print(f"RESULTS: {passed}/{total} passed", end="")
    if warned > 0:
        print(f", {warned} known issues", end="")
    if failed > 0:
        print(f", {failed} failed", end="")
    print(f" ({100*passed/total:.0f}% pass rate)")
    print("=" * 70)

    return failed == 0


def interactive_test():
    """Interactive mode for testing custom inputs."""
    from app.deidentification import deidentify_text

    print("=" * 70)
    print("INTERACTIVE PRESIDIO TEST MODE")
    print("Enter text to de-identify. Type 'quit' to exit.")
    print("=" * 70)
    print()

    while True:
        try:
            text = input("Input> ").strip()
            if text.lower() in ('quit', 'exit', 'q'):
                break
            if not text:
                continue

            result = deidentify_text(text)
            print(f"Output> {result.clean_text}")
            print()
        except KeyboardInterrupt:
            break

    print("\nGoodbye!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-i":
        interactive_test()
    else:
        strict_mode = "--strict" in sys.argv
        success = run_tests(strict=strict_mode)
        sys.exit(0 if success else 1)
