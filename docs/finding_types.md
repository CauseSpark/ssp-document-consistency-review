# Finding Types

Every row in the findings log gets exactly one **fix type**. The fix type tells the
document owner what kind of edit is needed. It's separate from **priority**, which
says how soon (see [review_method.md](review_method.md#priority-rating)).

| Fix type | Code | One-line test |
|---|---|---|
| Wording change | `WORDING` | The documents mean the same thing but say it differently, or one is ambiguous. |
| Missing content | `MISSING` | Something the SSP claims (or a requirement needs) isn't covered in the supporting document at all. |
| Version / document-control issue | `DOC_CONTROL` | A version, date, ID, owner, or cross-reference is wrong, missing, or out of date. |
| Stale tool name | `STALE_TOOL` | A document names a tool, product, or system that has been retired, renamed, or isn't in the SSP. |

> A disagreement about *how often* something happens (for example, quarterly vs.
> annually) is logged as `WORDING` if one document is simply out of date, or `MISSING`
> if a document has no frequency at all. It is almost always **High** priority, because
> it's a disagreement about what is done.

---

## 1. Wording change (`WORDING`)

**What it is.** The documents disagree in their words, or one is vague enough that a
reader could act differently from what the SSP describes.

**Examples**
- SSP: "The ISSO reviews privileged accounts quarterly." Policy: "Privileged accounts
  are reviewed annually by IT."
- Procedure says "periodically" where the SSP gives a specific interval.
- Role names don't match ("Security Lead" vs "ISSO") and no roles table maps them.

**Typical fix.** Align the wording to whichever document reflects current practice
(confirm with the client), and use the same role titles and terms everywhere.

---

## 2. Missing content (`MISSING`)

**What it is.** The SSP says something is done, but no policy or procedure supports
it. Or a procedure skips a step the SSP depends on.

**Examples**
- SSP says audit-log review failures are escalated to the ISSO; the procedure has no
  escalation step.
- SSP cites a procedure that doesn't exist in the package.
- Policy has no review-cycle statement at all.

**Typical fix.** Add the missing statement or step. If the activity isn't actually
being performed, the SSP needs to change too (and possibly a POA&M entry), which is a
question for the client.

---

## 3. Version or document-control issue (`DOC_CONTROL`)

**What it is.** Problems with the metadata that makes documents traceable.

**Examples**
- Policy cites `ACME-SSP-001 v2.1`, but the current SSP is v3.0.
- Procedure header has no version, approval date, or owner.
- Two documents share the same document ID.
- "Next review" date is in the past.

**Typical fix.** Update the reference or header. Then check whether the cited
*content* changed between versions. If it did, there may also be a wording or
missing-content finding hiding underneath.

---

## 4. Stale tool name (`STALE_TOOL`)

**What it is.** A document names a tool that was retired, renamed, or never appears in
the SSP's description of the system.

**Examples**
- Procedure says "export logs from LogHarbor", but the SSP names SentryLake SIEM as
  the log platform. (Both names are fictional.)
- Policy references a password vault by an old product version.

**Why it matters.** Evidence collected with the wrong tool may not cover the systems
in scope, and an assessor who sees an unexplained tool will ask whether it's inside
the CUI boundary.

**Typical fix.** Replace it with the current tool name, update screenshots and steps,
and confirm with the client whether the old tool has been fully decommissioned or
still holds data.
