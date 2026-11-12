# Audit Log Review Procedure

> **FICTIONAL EXAMPLE.** Acme Defense Fabrication is invented. No CUI.

| Field | Value |
|---|---|
| Document ID | ACME-PRO-AU-01 |
| Version | 1.0 |
| Effective date | 2025-02-10 |
| Owner | ISSO |
| Approved by | |
| Implements | ACME-POL-AU-01 v1.1 |

## Purpose
Describes how the ISSO reviews Engineering Enclave audit records for suspicious activity.

## Frequency
The ISSO reviews audit logs monthly.

## Steps
1. Sign in to the LogHarbor console with your named ISSO account.
2. Open the "Enclave Monthly" saved search.
3. Review failed logons, after-hours logons, privilege-group changes, and large file
   copies from CUI shares.
4. Export the search results to CSV and save them to the ISSO evidence folder.
5. If anything looks suspicious, open a TallyDesk incident and follow ACME-PRO-IR-01 v1.4.
6. Record "review complete" with the date in the TallyDesk review log.
