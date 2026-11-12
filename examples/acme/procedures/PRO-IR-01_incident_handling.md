# Incident Handling Procedure

> **FICTIONAL EXAMPLE.** Acme Defense Fabrication is invented. No CUI.

| Field | Value |
|---|---|
| Document ID | ACME-PRO-IR-01 |
| Version | 1.4 |
| Effective date | 2026-07-01 |
| Owner | ISSO |
| Approved by | President, Acme Defense Fabrication |
| Implements | ACME-POL-IR-01 v2.2 |

## Purpose
Gives the ISSO and IT Administrator step-by-step actions for handling a security incident.

## Steps

### Detect and report
1. Anyone who suspects an incident tells the ISSO by phone or in person.
2. The ISSO opens a TallyDesk incident ticket and records the time of discovery.

### Contain
3. The IT Administrator disconnects affected workstations from the network (leave them
   powered on).
4. Credentials for any affected privileged accounts are rotated in KeyWarden Vault.

### Investigate and recover
5. The ISSO pulls related events from SentryLake SIEM and attaches them to the ticket.
6. Affected systems are reimaged from the BaselineForge baseline before reconnecting.

### Close
7. The ISSO writes a short lessons-learned summary in the ticket and closes it.

## Testing
The ISSO runs a tabletop exercise annually using a scenario from this procedure.
