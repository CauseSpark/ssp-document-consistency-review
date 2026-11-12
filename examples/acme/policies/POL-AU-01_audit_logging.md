# Audit and Logging Policy

> **FICTIONAL EXAMPLE.** Acme Defense Fabrication is invented. No CUI.

| Field | Value |
|---|---|
| Document ID | ACME-POL-AU-01 |
| Version | 1.1 |
| Effective date | 2026-05-01 |
| Owner | ISSO |
| Approved by | President, Acme Defense Fabrication |
| Policy review cycle | Annual |
| Related documents | ACME-SSP-001 v3.0, ACME-PRO-AU-01 v1.0 |

## 1. Purpose
This policy makes sure that system activity in the Engineering Enclave can be traced to
individual users and reviewed for signs of misuse.

## 2. Policy statements

2.1 Enclave systems must generate audit records for logons, privilege use, and access to
CUI file shares.

2.2 Audit records are forwarded to SentryLake SIEM.

2.3 The ISSO reviews audit logs weekly and opens an incident for any suspicious activity.

2.4 Collected log data is retained for 90 days.

2.5 Only the ISSO and IT Administrator may change logging settings.
