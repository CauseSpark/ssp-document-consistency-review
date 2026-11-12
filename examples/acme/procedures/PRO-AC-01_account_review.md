# Privileged Account Review Procedure

> **FICTIONAL EXAMPLE.** Acme Defense Fabrication is invented. No CUI.

| Field | Value |
|---|---|
| Document ID | ACME-PRO-AC-01 |
| Version | 1.3 |
| Effective date | 2026-06-15 |
| Owner | ISSO |
| Approved by | ISSO |
| Implements | ACME-POL-AC-01 v2.0 |

## Purpose
Confirms that every privileged account in the Engineering Enclave is still needed and
assigned to the right person.

## Frequency
The Security Lead performs this review of privileged accounts quarterly.

## Steps
1. Export the list of members of the domain admin and local admin groups.
2. Export the list of accounts with checkout rights in KeyWarden Vault.
3. Compare both lists against the current staff roster.
4. For each account, confirm with the account owner's manager that it's still needed.
5. Disable any account that is not confirmed within five business days.
6. Record results and attach both exports to a TallyDesk ticket titled
   "Privileged Account Review YYYY-QN".

## Records
TallyDesk tickets are retained for three years.
