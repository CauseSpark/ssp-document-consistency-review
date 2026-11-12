# Acme Defense Fabrication: System Security Plan (Excerpt)

> **FICTIONAL EXAMPLE.** Acme Defense Fabrication, its people, systems, and tools are
> invented for study purposes. Any resemblance to a real organization or product is
> coincidental. Contains no CUI.

| Field | Value |
|---|---|
| Document ID | ACME-SSP-001 |
| Title | System Security Plan: Acme Shop Floor & Engineering Enclave |
| Version | 3.0 |
| Effective date | 2026-08-01 |
| Owner | Information System Security Officer (ISSO) |
| Approved by | President, Acme Defense Fabrication |
| Requirement set | NIST SP 800-171 Rev 2 |

## 1. System overview

Acme Defense Fabrication is a 60-person machine shop that produces precision brackets
and housings for defense prime contractors. The **Engineering Enclave** stores and
processes CUI (technical drawings received from primes). It consists of 14 engineering
workstations, two file servers, and a CNC programming station, all joined to the
`acme.local` domain.

Security tooling in scope:

| Function | Tool |
|---|---|
| Log collection and correlation | SentryLake SIEM |
| Privileged credential vault | KeyWarden Vault |
| Ticketing / change records | TallyDesk |
| Endpoint configuration baselines | BaselineForge |

## 2. Supporting documents

| Document ID | Title | Version |
|---|---|---|
| ACME-POL-AC-01 | Access Control Policy | v2.0 |
| ACME-PRO-AC-01 | Privileged Account Review Procedure | v1.3 |
| ACME-POL-AU-01 | Audit and Logging Policy | v1.1 |
| ACME-PRO-AU-01 | Audit Log Review Procedure | v1.0 |
| ACME-POL-IR-01 | Incident Response Policy | v2.2 |
| ACME-PRO-IR-01 | Incident Handling Procedure | v1.4 |
| ACME-PRO-CM-01 | Baseline Configuration Procedure | v1.0 |

## 3. Access Control (AC)

**3.1.1: Limit system access to authorized users.**
Accounts are requested through TallyDesk and approved by the requesting user's manager
and the ISSO before the IT Administrator creates them. Accounts are disabled within one
business day of separation. See ACME-POL-AC-01 v2.0.

**3.1.5: Employ the principle of least privilege.**
Administrative rights are limited to the IT Administrator and one backup. Privileged
accounts are separate from daily-use accounts, and their credentials are checked out
from KeyWarden Vault. The ISSO reviews all privileged accounts quarterly and records the
review in TallyDesk, following ACME-PRO-AC-01 v1.3.

## 4. Audit and Accountability (AU)

**3.3.1: Create and retain system audit logs and records.**
Windows event logs, firewall logs, and file-server access logs from the Engineering
Enclave are forwarded to SentryLake SIEM and retained for 12 months.

**3.3.5: Correlate audit record review, analysis, and reporting.**
The ISSO reviews audit logs weekly in SentryLake SIEM using the saved "Enclave Weekly"
dashboard, following ACME-PRO-AU-01 v1.0. Suspicious events are opened as TallyDesk
incidents and handled under ACME-POL-IR-01 v2.2.

## 5. Configuration Management (CM)

**3.4.1: Establish and maintain baseline configurations and inventories.**
Workstation and server baseline configurations are maintained in BaselineForge. The IT
Administrator reviews baseline configurations annually and after any major OS upgrade,
following ACME-PRO-CM-01 v1.0.

**3.4.2: Establish and enforce security configuration settings.**
BaselineForge enforces the approved settings at each check-in and reports drift to the
IT Administrator, who opens a TallyDesk change record for any approved exception.

## 6. Incident Response (IR)

**3.6.1: Establish an operational incident-handling capability.**
Incidents are handled according to ACME-POL-IR-01 v2.2 and ACME-PRO-IR-01 v1.4. The ISSO
is the incident lead. Cyber incidents affecting covered defense information are reported
to the DoD within 72 hours, as the contract requires.

**3.6.3: Test the organizational incident response capability.**
Acme tests its incident response capability annually with a tabletop exercise led by
the ISSO. Lessons learned are tracked in TallyDesk.
