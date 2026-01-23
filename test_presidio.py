#!/usr/bin/env python3
"""
Isolated Presidio De-identification Test Harness

Run: python test_presidio.py
"""

import sys
from dataclasses import dataclass
from typing import List, Tuple

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
    {
        "name": "Provider name",
        "input": "Primary is Dr. Johnson, fellow is Dr. Chen.",
        "must_redact": ["Johnson", "Chen"],
        "must_preserve": ["Primary", "Dr.", "fellow"],
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
        "must_redact": ["Boston"],
        "must_preserve": ["Family", "transferred", "MGH"],
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
]


def run_tests():
    """Run all test cases and report results."""
    # Import here to avoid slow startup when just viewing file
    from app.deidentification import deidentify_text

    print("=" * 70)
    print("PRESIDIO DE-IDENTIFICATION TEST HARNESS")
    print("=" * 70)
    print()

    passed = 0
    failed = 0
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

        status = "PASS" if not errors else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1

        results.append({
            "name": test["name"],
            "status": status,
            "input": test["input"],
            "output": clean,
            "errors": errors,
        })

    # Print results
    for r in results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        print(f"{icon} {r['name']}")
        if r["status"] == "FAIL":
            print(f"   Input:  {r['input']}")
            print(f"   Output: {r['output']}")
            for err in r["errors"]:
                print(f"   ⚠️  {err}")
            print()

    print("=" * 70)
    print(f"RESULTS: {passed}/{passed+failed} passed ({100*passed/(passed+failed):.0f}%)")
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
        success = run_tests()
        sys.exit(0 if success else 1)
