# Worked Example: Acme Defense Fabrication (Fictional)

Acme Defense Fabrication is an **invented** 60-person machine shop. Its people, systems,
and tools (SentryLake SIEM, KeyWarden Vault, TallyDesk, BaselineForge, LogHarbor) are
made up for this study project. Nothing here comes from a real organization or a real
SSP, and none of it is CUI.

## The package

| File | Document ID | Version |
|---|---|---|
| `ssp_excerpt.md` | ACME-SSP-001 | 3.0 |
| `policies/POL-AC-01_access_control.md` | ACME-POL-AC-01 | 2.0 |
| `policies/POL-AU-01_audit_logging.md` | ACME-POL-AU-01 | 1.1 |
| `policies/POL-IR-01_incident_response.md` | ACME-POL-IR-01 | 2.2 |
| `procedures/PRO-AC-01_account_review.md` | ACME-PRO-AC-01 | 1.3 |
| `procedures/PRO-AU-01_log_review.md` | ACME-PRO-AU-01 | 1.0 |
| `procedures/PRO-IR-01_incident_handling.md` | ACME-PRO-IR-01 | 1.4 |

The documents contain **deliberately planted inconsistencies**. Try to find them yourself
before you open the answer key.

## Run the checker

From the repo root:

```bash
python src/consistency_check.py examples/acme --config config/check_config.json
```

The script reports 7 leads. Some issues need a person to catch them (a retention
period that disagrees, a missing reporting step, mismatched role titles), so the
completed log has 9 findings.

## Answer key

- [`findings_log_acme.csv`](findings_log_acme.csv): the completed findings log (9 findings)
- [`open_items_acme.csv`](open_items_acme.csv): questions the client must answer first

| Finding | Caught by | Summary |
|---|---|---|
| F-001 | script | Privileged account review: SSP says quarterly, policy says annually |
| F-002 | script | Audit log review: SSP says weekly, procedure says monthly |
| F-003 | script | Procedure uses LogHarbor; the SSP names SentryLake SIEM |
| F-004 | reviewer | Log retention: SSP says 12 months, policy says 90 days |
| F-005 | reviewer | IR procedure has no step for the 72-hour DoD report |
| F-006 | script | SSP cites a CM procedure that isn't in the package |
| F-007 | script | IR policy cites SSP v2.1; current version is v3.0 |
| F-008 | script + reviewer | Log review procedure: blank approval, predates its own policy |
| F-009 | reviewer | "Security Lead" vs "ISSO" role naming |
