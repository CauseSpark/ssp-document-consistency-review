# Review Method: Checking an SSP Against Its Policies and Procedures

> Personal study material. This is not an official CMMC, DoD, NIST, or Cyber AB method,
> and it isn't an assessment. It's a repeatable way to find places where a document
> package contradicts itself *before* an assessor does.

## Why this matters

A System Security Plan (SSP) describes how each security requirement is implemented.
Policies say what the organization requires, and procedures say how people actually
carry it out. When these three layers disagree (different review cycles, a procedure
that names a tool the SSP never mentions, a policy pointing to a superseded SSP
version), an assessor can't tell which document reflects reality. That raises
questions about whether the requirement is implemented at all.

The requirement set used here is NIST SP 800-171 Rev 2 (the baseline CMMC Level 2
currently assesses against) with assessment objectives from NIST SP 800-171A. See the
[README](../README.md#current-baseline-as-of-november-2026) for sources.

## Inputs

| Input | What you need from it |
|---|---|
| SSP (or excerpt) | Document ID, version, date, and the implementation statement for each requirement in scope |
| Policies | Document ID, version, owner, review cycle, any documents they cite |
| Procedures | Document ID, version, steps, tools named, frequencies, roles |
| Tool / asset inventory (if available) | Current tool names, so you can tell renamed or retired tools apart |
| Retired-tools list | Tools you know have been replaced (goes in `config/check_config.json`) |

## Step-by-step

### 1. Build the document register
List every document in the package with its ID, title, version, effective date, and
owner. This is the reference you use to check every cross-reference later. If any
document is missing a version or date, log it as a **document-control** finding
straight away.

### 2. Run the automated pass
```bash
python src/consistency_check.py path/to/package --config config/check_config.json
```
The script catches the mechanical problems: version references that don't match the
register, review frequencies that disagree across documents, and retired tool names.
Treat its output as **leads, not findings.** Confirm every hit by reading the sentence
in context. A "monthly" might refer to something else entirely.

### 3. Walk each requirement top-down
For each requirement in scope (for example, 3.1.7, 3.3.1, 3.6.1):

1. Read the SSP implementation statement. Note the **who, what, how often, and with what tool.**
2. Find the policy statement that governs it. Does the policy require what the SSP describes?
3. Find the procedure that carries it out. Would someone following only the procedure
   end up doing what the SSP claims?
4. Record every gap or contradiction on a row of `templates/findings_log.csv`.

### 4. Walk each procedure bottom-up
Read every procedure on its own. Look for steps, tools, or roles that the SSP doesn't
mention at all. These are often the most important findings, because they show what
staff *actually* do.

### 5. Classify and prioritize
Give each finding a fix type ([finding_types.md](finding_types.md)) and a priority (below).

### 6. Separate findings from questions
If you can't tell which document is correct (for example, is the review really quarterly
or annual?), **don't guess.** Write a proposed fix *and* put a question for the client in
`templates/open_items.csv`. Whichever document turns out wrong, the client's answer
decides which one changes.

## Priority rating

Rate on two questions: **(A) Could this cause an assessor to doubt that the requirement
is implemented?** and **(B) Could staff follow the wrong instruction because of it?**

| Priority | Meaning | Typical examples | Target |
|---|---|---|---|
| **High** | Contradiction about *what is done* for a requirement, or a procedure that leads staff to do the wrong thing. A = yes. | Review cycle in the SSP differs from the policy or procedure; procedure uses a retired tool for evidence collection; required content missing for a requirement in scope | Fix before any assessment or self-assessment affirmation |
| **Medium** | Document-control or reference problem that undermines traceability but doesn't change the activity. A = maybe, B = no. | Policy cites a superseded SSP version; procedure cites the wrong policy ID; missing approval date | Fix in the next document revision cycle |
| **Low** | Wording or clarity problem; meaning is the same. A = no, B = no. | Inconsistent role titles ("ISSO" vs "Security Lead"); passive voice that hides who acts | Batch with other edits |

**Escalate one level** if the finding affects a requirement whose
DoD Assessment Methodology weight is 5 points, or if it touches CUI boundary or
scoping statements.

## Output

- `findings_log.csv`: one row per finding, with the current wording, the SSP wording,
  and a proposed fix.
- `open_items.csv`: questions the client must answer before a fix can be finalized.

See `examples/acme/` for a completed example on a fictional package.
