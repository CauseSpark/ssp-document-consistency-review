# SSP Document Consistency Review

[![tests](https://github.com/CauseSpark/ssp-document-consistency-review/actions/workflows/tests.yml/badge.svg)](https://github.com/CauseSpark/ssp-document-consistency-review/actions/workflows/tests.yml)

A repeatable method, templates, and a small Python checker for finding places where a
**System Security Plan (SSP)** contradicts the **policies and procedures** that are
supposed to support it. These include review cycles that disagree, references to
superseded document versions, and procedures that name tools the SSP doesn't.

Everything is demonstrated on a **fictional** document package for "Acme Defense
Fabrication."

> **Personal study material.** This isn't an official CMMC, DoD, NIST, or Cyber AB
> product, and it doesn't represent an assessment or certification of any kind. See the
> [disclaimer](#disclaimer).

---

## Purpose

Assessors read the SSP, then check that policies, procedures, and evidence back it up.
When those documents disagree, the organization has a credibility problem before
anyone even looks at the system. This repo shows how I approach a **document-consistency
review**:

1. Build a register of every document's ID and version.
2. Run an automated pass to surface mechanical mismatches.
3. Read each requirement top-down (SSP → policy → procedure) and each procedure bottom-up.
4. Log findings with a fix type and priority, and separate open questions for the client.

## Quick start

```bash
git clone https://github.com/CauseSpark/ssp-document-consistency-review.git
cd ssp-document-consistency-review

# The checker uses only the standard library (Python 3.10+)
python src/consistency_check.py examples/acme --config config/check_config.json

# Optional: also write results in findings-log CSV format
python src/consistency_check.py examples/acme --config config/check_config.json --csv reports/auto_findings.csv

# Run the tests
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

The exit code is `1` when findings are reported (handy in CI). Pass `--exit-zero` to always exit `0`.

### What the checker flags

| Check | Example from the Acme package |
|---|---|
| **Version mismatch**: a document cites `DOC-ID vX` but that document's header says otherwise | Incident Response Policy cites `ACME-SSP-001 v2.1`; the SSP is v3.0 |
| **Missing reference**: a cited document isn't in the package | SSP cites `ACME-PRO-CM-01`, which wasn't provided |
| **Review-cycle mismatch**: different frequencies for the same review topic | SSP: privileged accounts reviewed *quarterly*; policy: *annually* |
| **Retired tool name**: any term from a configurable list | Log review procedure says to use *LogHarbor*; the SSP names *SentryLake SIEM* |
| **Document-control gaps**: blank or missing header fields, duplicate IDs | Log review procedure has a blank "Approved by" |

Retired tools and review topics (with their keywords and NIST SP 800-171 requirement
numbers) live in [`config/check_config.json`](config/check_config.json), so the checker
can be pointed at a different package without changing code.

Script output is a list of **leads, not findings**. Every hit gets confirmed in context,
and some of the most important findings (a missing incident-reporting step, a log
retention conflict) need a human reader. See the
[Acme answer key](examples/acme/README.md#answer-key).

## Repository layout

```
config/check_config.json        Retired-tools list and review-cycle topics
docs/review_method.md           How to compare an SSP to its policies and procedures; priority rating
docs/finding_types.md           Wording change, missing content, version/doc-control, stale tool name
examples/acme/                  Fictional SSP excerpt, 3 policies, 3 procedures, completed logs
templates/findings_log.csv      Blank findings log
templates/open_items.csv        Blank open-items (client questions) log
src/consistency_check.py        The checker (CLI + importable functions)
tests/                          pytest suite
.github/workflows/tests.yml     Runs the tests on Python 3.10–3.12
```

## What this demonstrates

- **GRC document review**: reading an SSP against its supporting policies and
  procedures the way an assessor would, and writing findings a document owner can act on
- **Structured findings**: a consistent fix-type taxonomy, a simple priority model, and
  a clear line between *findings* and *questions for the client*
- **Working knowledge of the baseline**: requirements referenced by NIST SP 800-171
  Rev 2 numbers (for example 3.1.5, 3.3.5, 3.6.3) in the context of CMMC Level 2
- **Practical automation**: a dependency-free Python tool with a configurable rule set,
  CSV output that matches the manual template, and 30+ pytest tests in CI
- **Professional judgment**: knowing which checks a script can do and which need a person

## Current baseline (as of November 2026)

I checked these points against public sources in November 2026. Confirm them with the official sources below before relying on them.

- **CMMC Level 2** assesses the **110 security requirements in NIST SP 800-171 Rev 2**.
  NIST published Rev 3 in May 2024, but a DoD class deviation keeps Rev 2 as the
  requirement under DFARS 252.204-7012, and CMMC assessments and SPRS scoring still use Rev 2.
- The **CMMC Program Rule (32 CFR Part 170)** took effect December 16, 2024. The
  **acquisition rule (48 CFR)** took effect **November 10, 2025**, starting **Phase 1**
  (Level 1 and Level 2 self-assessments in applicable contracts).
- **Phase 2** (Level 2 C3PAO certification as the default for CUI contracts) was
  scheduled for November 10, 2026. On **July 13, 2026**, the Department of War
  (Department of Defense) **suspended Phase 2** and later phases pending a CMMC Reform
  Task Force review. As of this writing, no restart date has been published. Phase 1
  self-assessments and DFARS 252.204-7012 obligations remain in effect.

This repo uses **Rev 2** requirement numbers to match the current assessment baseline.

### Official sources

- DoD CIO, CMMC program page and policy updates: <https://dodcio.defense.gov/CMMC/>
- 32 CFR Part 170 (CMMC Program), eCFR: <https://www.ecfr.gov/current/title-32/subtitle-A/chapter-I/subchapter-G/part-170>
- NIST SP 800-171 Rev 2: <https://csrc.nist.gov/pubs/sp/800/171/r2/upd1/final>
- NIST SP 800-171A (assessment procedures for Rev 2): <https://csrc.nist.gov/pubs/sp/800/171/a/final>
- NIST SP 800-171 Rev 3 (current NIST revision, not yet the DoD baseline): <https://csrc.nist.gov/pubs/sp/800/171/r3/final>

## Disclaimer

- **Everything is fictional.** Acme Defense Fabrication, its staff, systems, and every
  tool name (SentryLake SIEM, KeyWarden Vault, TallyDesk, BaselineForge, LogHarbor,
  VaultKeep, TicketTrail) are invented. Any resemblance to a real organization or
  product is coincidental. Nothing here comes from a real client, employer, or SSP.
- **No CUI** or other sensitive information is included.
- This is **personal study material**. It isn't legal or compliance advice, it isn't
  endorsed by the DoD, NIST, or the Cyber AB, and using it doesn't mean an organization
  meets any CMMC level. I don't claim any CMMC certification or official status.
- Requirement text is paraphrased or cited by number. Read the official NIST
  publications for authoritative wording.

## License

[MIT](LICENSE) © 2026 Peyton Seay
