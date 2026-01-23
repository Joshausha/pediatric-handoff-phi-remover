# HIPAA Compliance Documentation

This document outlines how the Pediatric Handoff PHI Remover addresses HIPAA requirements for handling Protected Health Information (PHI).

## Executive Summary

The PHI Remover is designed for **de-identification** of patient handoff recordings. It operates entirely locally—no patient data ever leaves your network—and automatically removes 18 categories of PHI before displaying transcripts.

**Key compliance features:**
- 100% local processing (no cloud APIs)
- Automatic PHI detection and removal
- HIPAA-compliant audit logging
- No persistent storage of audio or transcripts

## PHI Handling

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER'S DEVICE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   [Browser]                                                         │
│       │                                                             │
│       ▼                                                             │
│   Audio Recording (stays in browser memory)                         │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                   LOCAL SERVER                              │   │
│   │                                                             │   │
│   │   Audio File ──► Whisper ──► Raw Transcript                │   │
│   │                  (local)            │                       │   │
│   │                                     ▼                       │   │
│   │                              Presidio PHI Detection         │   │
│   │                                     │                       │   │
│   │                                     ▼                       │   │
│   │                              Clean Transcript ──► Display   │   │
│   │                                                             │   │
│   │   [All processing in memory - no disk persistence]          │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### PHI Categories Detected

The system detects and removes all 18 HIPAA identifiers where applicable to audio transcripts:

| # | HIPAA Identifier | Detection Method |
|---|-----------------|------------------|
| 1 | Names | NER + Baby/Guardian patterns |
| 2 | Geographic data | NER (cities, addresses) |
| 3 | Dates | NER + date patterns |
| 4 | Phone numbers | Pattern matching |
| 5 | Fax numbers | Pattern matching |
| 6 | Email addresses | Pattern matching |
| 7 | SSN | Pattern matching |
| 8 | Medical record numbers | Custom patterns |
| 9 | Health plan numbers | Pattern matching |
| 10 | Account numbers | Pattern matching |
| 11 | License numbers | Pattern matching |
| 12 | Vehicle identifiers | N/A (rare in handoffs) |
| 13 | Device identifiers | N/A (rare in handoffs) |
| 14 | URLs | Pattern matching |
| 15 | IP addresses | Pattern matching |
| 16 | Biometric identifiers | N/A (audio format) |
| 17 | Full-face photos | N/A (audio only) |
| 18 | Unique identifying codes | Pattern matching |

### Custom Pediatric Recognizers

Beyond standard HIPAA identifiers, we detect pediatric-specific patterns:

- **Guardian names**: "Mom Sarah", "Dad Michael" → "Mom [NAME]", "Dad [NAME]"
- **Baby names**: "Baby Smith", "Infant Jones" → "Baby [NAME]"
- **Detailed ages**: "3 weeks 2 days old" → "[PEDIATRIC_AGE]"
- **Room/bed numbers**: "PICU bed 12" → "PICU bed [ROOM]"
- **MRN variants**: "#12345678", "MRN: 1234567"

## Data Retention

### What We Store

| Data Type | Storage | Duration | Contains PHI? |
|-----------|---------|----------|---------------|
| Audio files | Memory only | Request duration | Yes (deleted after) |
| Transcripts | Memory only | Request duration | Yes (deleted after) |
| Audit logs | Disk (optional) | Configurable | **No** |

### What We Never Store

- Raw audio files
- Raw transcripts
- Patient identifiers
- IP addresses (only hashed for correlation)

## Audit Logging

Audit logs comply with HIPAA §164.312(b) (Audit Controls) and §164.312(c) (Integrity).

### Log Contents (PHI-Free)

```json
{
  "timestamp": "2026-01-22T15:30:00.000Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "transcription_complete",
  "file_size_bytes": 5242880,
  "audio_duration_seconds": 120.5,
  "phi_entities_removed": 15,
  "phi_by_type": {
    "PERSON": 8,
    "DATE_TIME": 4,
    "ROOM": 3
  },
  "processing_time_seconds": 45.2,
  "success": true,
  "client_ip_hash": "a1b2c3d4e5f6g7h8"
}
```

### What We Log

- Timestamps and request IDs (for correlation)
- File sizes and durations (for capacity planning)
- PHI entity counts by type (for quality monitoring)
- Success/failure status
- Hashed client IPs (for security auditing)

### What We Never Log

- Actual text content
- Patient names or identifiers
- Audio content
- Raw IP addresses

## Technical Safeguards

### Access Controls (§164.312(a))

- Rate limiting prevents abuse
- CORS restricts browser origins
- Non-root container user

### Transmission Security (§164.312(e))

- All data stays local (no transmission)
- Optional TLS via reverse proxy
- No external API calls

### Encryption (§164.312(a)(2)(iv))

- TLS for network transmission (when using reverse proxy)
- At-rest encryption not required (no persistent storage)

### Integrity (§164.312(c)(1))

- Audit logs record all processing events
- Validation step confirms PHI removal
- Checksums available via request IDs

## Administrative Safeguards

### Minimum Necessary (§164.502(b))

- Only PHI necessary for de-identification is processed
- Original transcripts shown only for verification
- Clean transcripts are the primary output

### Workforce Training

Users should be trained on:
1. Never copy/paste raw transcripts externally
2. Verify clean transcripts before sharing
3. Report any suspected PHI in clean output

## Deployment Recommendations

### Hospital Network Deployment

1. **Network isolation**: Deploy on internal network only
2. **TLS termination**: Use nginx/Apache for HTTPS
3. **Firewall rules**: Restrict to authorized workstations
4. **Access logging**: Enable audit logs to persistent storage
5. **Log retention**: Configure per your retention policy

### Risk Assessment

| Risk | Mitigation |
|------|------------|
| PHI in logs | Logs contain only counts, never content |
| Data breach | No persistent storage of PHI |
| Unauthorized access | Rate limiting, CORS, network isolation |
| Failed de-identification | Validation step + conservative thresholds |
| Insider threat | Audit logging with request correlation |

## Compliance Checklist

Before production deployment, verify:

- [ ] Application deployed on isolated hospital network
- [ ] TLS enabled via reverse proxy
- [ ] Audit logging enabled and configured
- [ ] Log retention policy defined
- [ ] User training completed
- [ ] Risk assessment documented
- [ ] BAA not required (no cloud services)

## Disclaimer

This software is provided as a tool to assist with PHI de-identification. It should be used as part of a comprehensive HIPAA compliance program. Organizations are responsible for:

- Conducting their own risk assessments
- Implementing appropriate administrative safeguards
- Training workforce members
- Verifying de-identification quality for their use case

The developers make no warranty regarding HIPAA compliance and accept no liability for PHI breaches. Always consult with your compliance officer before deploying in a healthcare environment.

## Contact

For questions about compliance or to report security issues:
- GitHub Issues: https://github.com/Joshausha/pediatric-handoff-phi-remover/issues
