# Protecting Patient Privacy in Pediatric Handoffs
## A Tool for Safe Audio Transcription

---

## The Problem We're Solving

**Every time a pediatric resident hands off patients to the next shift, critical information must transfer accurately.** These handoffs happen multiple times daily—and communication failures are the #1 cause of medical errors.

Many hospitals now record these handoffs to improve quality. But here's the challenge:

> **Patient names, medical record numbers, and other private information are spoken aloud during every handoff.**

Current transcription tools (like those from Google, Amazon, or OpenAI) send audio to remote servers for processing. This means **patient information leaves the hospital's control**—creating serious privacy and legal concerns.

---

## What We Built

**A completely local transcription system that automatically removes patient-identifying information before anyone sees the transcript.**

### How It Works (In Plain Terms)

1. **Record** the handoff on your phone or computer
2. **Upload** the audio file to our tool
3. **The tool listens** and converts speech to text—*entirely on your computer*
4. **Private information is automatically detected and hidden**
5. **You receive** a clean transcript ready for review or documentation

**Nothing ever leaves your computer.** No internet connection needed. No cloud servers. No privacy risk.

---

## Why This Matters

### For Patients and Families
- Their names, medical record numbers, and health details stay private
- Complies with HIPAA—the federal law protecting health information
- No risk of data breaches from third-party servers

### For Hospitals and Health Systems
- **No expensive contracts** with cloud transcription vendors
- **No Business Associate Agreements** needed (legal paperwork required when sharing patient data with outside companies)
- **Audit-ready**—can demonstrate that patient data never left institutional control

### For Residents and Quality Improvement
- Supports the **I-PASS handoff protocol** (proven to reduce errors by 23-47%)
- Enables review of handoffs for training and improvement
- Creates documentation without compromising privacy

---

## What Gets Protected

The system detects and hides:

| What's Hidden | Example |
|---------------|---------|
| Patient names | "Sarah Johnson" → "[PATIENT]" |
| Parent/guardian names | "Mom Lisa" → "Mom [NAME]" |
| Medical record numbers | "MRN 12345678" → "MRN [REDACTED]" |
| Dates of birth | "Born January 15th" → "Born [DATE]" |
| Room numbers | "Room 412 bed A" → "Room [REDACTED]" |
| Phone numbers | "Call 555-1234" → "Call [PHONE]" |

**Medical information stays intact.** Diagnoses, medications, vital signs, and clinical details are preserved—only identifying information is removed.

---

## Current Status

| Milestone | Status |
|-----------|--------|
| Core system built and tested | ✅ Complete |
| Successfully transcribed 27-minute handoff | ✅ Complete |
| Detects 78% of private information automatically | ✅ Working |
| Ready for clinical pilot testing | 🔄 Next step |

### What's Needed to Reach Clinical Use
1. **Improve detection accuracy** from 78% to 95%+ (requires additional testing with real handoff patterns)
2. **IRB approval** for pilot study with actual patient handoffs
3. **Integration** with hospital documentation systems

---

## The Bottom Line

> **We built a tool that lets hospitals safely transcribe patient handoffs without ever sending private health information to outside servers.**

This protects patient privacy, simplifies regulatory compliance, and enables quality improvement work that was previously too risky to attempt.

---

*Project developed by Josh Pankin, MD (PGY-3 Pediatrics) using open-source tools including Microsoft Presidio and OpenAI Whisper. January 2026.*
