#!/usr/bin/env python3
"""SSP document consistency checker.

Scans a folder of Markdown/text documents (an SSP plus its policies and
procedures) and flags mechanical inconsistencies a reviewer should confirm:

* version mismatches: a document cites ``DOC-ID vX.Y`` but the cited
  document's own header says a different version (or the document isn't in
  the package at all)
* missing document-control fields: Document ID, Version, Approved by, etc.
* mismatched review cycles: documents give different frequencies (weekly,
  quarterly, annually, ...) for the same configured review topic
* retired tool names: any term from the configurable ``retired_tools`` list

Results are leads for a human reviewer, not final findings.
Standard library only. Personal study project; not an official tool.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG = {
    "retired_tools": [],
    "review_topics": {},
    "required_header_fields": ["Document ID", "Version", "Effective date", "Owner", "Approved by"],
}

SCAN_SUFFIXES = {".md", ".txt"}
SKIP_NAMES = {"readme.md"}

FINDINGS_LOG_COLUMNS = [
    "ID",
    "Document",
    "Control",
    "Fix Type",
    "Priority",
    "What It Says Now",
    "What The SSP Says",
    "Proposed Fix",
    "Question For Client",
]

# Document references such as "ACME-POL-AC-01 v2.0"
REFERENCE_RE = re.compile(r"\b([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\s+v(\d+(?:\.\d+)*)\b")

# Frequency vocabulary -> normalized value
_FREQ_WORDS = [
    (r"daily", "daily"),
    (r"bi-?weekly", "biweekly"),
    (r"weekly", "weekly"),
    (r"monthly", "monthly"),
    (r"quarterly", "quarterly"),
    (r"semi-?annual(?:ly)?", "semiannually"),
    (r"annual(?:ly)?", "annually"),
    (r"yearly", "annually"),
]
# Hyphen guards keep compounds like "daily-use" from counting as a frequency.
FREQ_RE = re.compile(r"(?<![\w-])(" + "|".join(p for p, _ in _FREQ_WORDS) + r")(?![\w-])", re.IGNORECASE)
EVERY_RE = re.compile(r"\bevery\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)\b", re.IGNORECASE)
_EVERY_MAP = {
    ("day", 1): "daily",
    ("week", 1): "weekly",
    ("week", 2): "biweekly",
    ("day", 7): "weekly",
    ("day", 30): "monthly",
    ("month", 1): "monthly",
    ("day", 90): "quarterly",
    ("month", 3): "quarterly",
    ("month", 6): "semiannually",
    ("day", 365): "annually",
    ("month", 12): "annually",
    ("year", 1): "annually",
}

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]\s|\d+(?:\.\d+)*[.)]?\s|\|)")


@dataclass
class Document:
    path: Path
    rel: str
    lines: list[str]
    header: dict[str, str] = field(default_factory=dict)

    @property
    def doc_id(self) -> str | None:
        return self.header.get("document id") or None

    @property
    def version(self) -> str | None:
        value = self.header.get("version")
        if not value:
            return None
        m = re.match(r"v?(\d+(?:\.\d+)*)", value.strip(), re.IGNORECASE)
        return m.group(1) if m else value.strip()

    @property
    def label(self) -> str:
        return self.doc_id or self.rel

    @property
    def is_ssp(self) -> bool:
        ident = (self.doc_id or "").upper()
        return "-SSP-" in ident or ident.startswith("SSP") or "ssp" in self.path.name.lower()


@dataclass
class Finding:
    check: str
    document: str
    location: str
    control: str
    fix_type: str
    priority: str
    current_text: str
    ssp_text: str
    proposed_fix: str
    client_question: str = ""

    def as_row(self, finding_id: str) -> dict[str, str]:
        return {
            "ID": finding_id,
            "Document": f"{self.document} ({self.location})",
            "Control": self.control,
            "Fix Type": self.fix_type,
            "Priority": self.priority,
            "What It Says Now": self.current_text,
            "What The SSP Says": self.ssp_text,
            "Proposed Fix": self.proposed_fix,
            "Question For Client": self.client_question,
        }


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def load_config(path: str | Path | None) -> dict:
    """Load a JSON config, filling in defaults for missing keys."""
    config = {k: (list(v) if isinstance(v, list) else dict(v)) for k, v in DEFAULT_CONFIG.items()}
    if path:
        with open(path, encoding="utf-8") as fh:
            user = json.load(fh)
        for key in DEFAULT_CONFIG:
            if key in user:
                config[key] = user[key]
    # Allow review topics given as a plain keyword list.
    topics = {}
    for name, spec in config["review_topics"].items():
        if isinstance(spec, list):
            spec = {"control": "", "keywords": spec}
        topics[name] = {"control": spec.get("control", ""), "keywords": list(spec.get("keywords", []))}
    config["review_topics"] = topics
    return config


def parse_header(lines: list[str]) -> dict[str, str]:
    """Read ``| Field | Value |`` table rows or ``Field: Value`` lines near the top."""
    header: dict[str, str] = {}
    for line in lines[:40]:
        stripped = line.strip()
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", stripped)
        if not m:
            m = re.match(r"^\*{0,2}([A-Za-z][A-Za-z /]+?)\*{0,2}\s*:\s*(.*)$", stripped)
        if m:
            key = m.group(1).strip().lower()
            if set(key) <= set("-: "):
                continue
            header.setdefault(key, m.group(2).strip())
    return header


def load_documents(root: str | Path) -> list[Document]:
    root = Path(root)
    paths = [root] if root.is_file() else sorted(
        p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SCAN_SUFFIXES
    )
    docs = []
    for p in paths:
        if p.name.lower() in SKIP_NAMES and not root.is_file():
            continue
        lines = p.read_text(encoding="utf-8").splitlines()
        rel = p.name if root.is_file() else p.relative_to(root).as_posix()
        docs.append(Document(path=p, rel=rel, lines=lines, header=parse_header(lines)))
    return docs


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def normalize_version(v: str) -> tuple[int, ...]:
    parts = [int(x) for x in v.split(".") if x.isdigit()]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def find_frequencies(text: str) -> list[str]:
    """Return normalized frequencies mentioned in ``text`` (order preserved, unique)."""
    found: list[str] = []
    for m in FREQ_RE.finditer(text):
        word = m.group(1).lower()
        for pattern, norm in _FREQ_WORDS:
            if re.fullmatch(pattern, word):
                found.append(norm)
                break
    for m in EVERY_RE.finditer(text):
        unit = m.group(2).lower().rstrip("s")
        norm = _EVERY_MAP.get((unit, int(m.group(1))))
        if norm:
            found.append(norm)
    return list(dict.fromkeys(found))


def iter_sentences(doc: Document):
    """Yield ``(line_number, sentence)`` pairs, joining wrapped lines."""
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] = []
    start = 0
    for i, line in enumerate(doc.lines, start=1):
        stripped = line.strip()
        is_heading = stripped.startswith("#") or (
            stripped.startswith("**") and stripped.endswith("**") and len(stripped) > 4
        )
        if not stripped or is_heading:
            if current:
                blocks.append((start, current))
            current = []
            if line.strip():
                blocks.append((i, [line]))
            continue
        if current and LIST_ITEM_RE.match(line):
            blocks.append((start, current))
            current = []
        if not current:
            start = i
        current.append(line)
    if current:
        blocks.append((start, current))

    for start_line, block_lines in blocks:
        text = "\n".join(block_lines)
        pos = 0
        for part in SENTENCE_SPLIT_RE.split(text):
            idx = text.find(part, pos)
            line_no = start_line + text.count("\n", 0, max(idx, 0))
            pos = idx + len(part) if idx >= 0 else pos
            sentence = " ".join(part.split())
            if sentence:
                yield line_no, sentence


def _clip(text: str, limit: int = 220) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

def check_document_control(docs: list[Document], config: dict) -> list[Finding]:
    findings = []
    seen_ids: dict[str, Document] = {}
    for doc in docs:
        for field_name in config["required_header_fields"]:
            value = doc.header.get(field_name.lower())
            if not value:
                state = "is blank" if field_name.lower() in doc.header else "is missing"
                findings.append(Finding(
                    check="document_control",
                    document=doc.label,
                    location=doc.rel,
                    control="Document control",
                    fix_type="DOC_CONTROL",
                    priority="Medium",
                    current_text=f'Header field "{field_name}" {state}.',
                    ssp_text="",
                    proposed_fix=f'Fill in "{field_name}" in the document-control header.',
                    client_question=f'Who should be recorded as "{field_name}" for {doc.label}?'
                    if field_name.lower() in {"approved by", "owner"} else "",
                ))
        if doc.doc_id:
            if doc.doc_id in seen_ids:
                findings.append(Finding(
                    check="document_control",
                    document=doc.label,
                    location=doc.rel,
                    control="Document control",
                    fix_type="DOC_CONTROL",
                    priority="Medium",
                    current_text=f"Document ID {doc.doc_id} is also used by {seen_ids[doc.doc_id].rel}.",
                    ssp_text="",
                    proposed_fix="Give each document a unique ID.",
                ))
            else:
                seen_ids[doc.doc_id] = doc
    return findings


def check_versions(docs: list[Document]) -> list[Finding]:
    """Flag ``DOC-ID vX`` references that don't match the cited document's header."""
    register = {d.doc_id: d for d in docs if d.doc_id}
    findings = []
    for doc in docs:
        for line_no, line in enumerate(doc.lines, start=1):
            for m in REFERENCE_RE.finditer(line):
                ref_id, ref_ver = m.group(1), m.group(2)
                if ref_id == doc.doc_id:
                    continue
                target = register.get(ref_id)
                if target is None:
                    findings.append(Finding(
                        check="missing_reference",
                        document=doc.label,
                        location=f"{doc.rel}:{line_no}",
                        control="Document control",
                        fix_type="MISSING",
                        priority="High",
                        current_text=_clip(f"Cites {ref_id} v{ref_ver}: \"{line.strip()}\""),
                        ssp_text="",
                        proposed_fix=f"Add {ref_id} to the document package, or remove the reference.",
                        client_question=f"Does {ref_id} exist? If so, please provide the current version.",
                    ))
                    continue
                if target.version and normalize_version(ref_ver) != normalize_version(target.version):
                    findings.append(Finding(
                        check="version_mismatch",
                        document=doc.label,
                        location=f"{doc.rel}:{line_no}",
                        control="Document control",
                        fix_type="DOC_CONTROL",
                        priority="Medium",
                        current_text=_clip(f"Cites {ref_id} v{ref_ver}."),
                        ssp_text=f"{ref_id} header says v{target.version}." if target.is_ssp
                        else f"{ref_id} header says v{target.version} ({target.rel}).",
                        proposed_fix=f"Update the reference to {ref_id} v{target.version} and confirm "
                                     f"the cited content didn't change between versions.",
                    ))
    return findings


def collect_review_cycles(docs: list[Document], config: dict) -> dict[str, list[tuple[Document, int, str, list[str]]]]:
    """Map topic -> list of (doc, line, sentence, frequencies)."""
    results: dict[str, list] = {name: [] for name in config["review_topics"]}
    for doc in docs:
        for line_no, sentence in iter_sentences(doc):
            lowered = sentence.lower()
            for name, spec in config["review_topics"].items():
                if any(re.search(r"\b" + re.escape(k.lower()) + r"\b", lowered) for k in spec["keywords"]):
                    freqs = find_frequencies(sentence)
                    if freqs:
                        results[name].append((doc, line_no, sentence, freqs))
    return results


def check_review_cycles(docs: list[Document], config: dict) -> list[Finding]:
    findings = []
    for topic, hits in collect_review_cycles(docs, config).items():
        all_freqs = {f for _, _, _, fs in hits for f in fs}
        if len(all_freqs) < 2:
            continue
        control = config["review_topics"][topic]["control"]
        ssp_hits = [h for h in hits if h[0].is_ssp]
        ssp_freqs = {f for _, _, _, fs in ssp_hits for f in fs}
        ssp_text = "; ".join(f"\"{_clip(s, 160)}\" ({d.rel}:{ln})" for d, ln, s, _ in ssp_hits)
        for doc, line_no, sentence, freqs in hits:
            if doc.is_ssp and len(ssp_freqs) < 2:
                continue
            if ssp_freqs and not doc.is_ssp and set(freqs) <= ssp_freqs:
                continue
            if ssp_freqs and not doc.is_ssp:
                fix = (f"Align {doc.label} with the SSP ({'/'.join(sorted(ssp_freqs))}), "
                       f"or update the SSP if {'/'.join(freqs)} is the actual practice.")
            else:
                fix = f"Pick one {topic} frequency and use it in every document."
            findings.append(Finding(
                check="review_cycle_mismatch",
                document=doc.label,
                location=f"{doc.rel}:{line_no}",
                control=control,
                fix_type="WORDING",
                priority="High",
                current_text=_clip(f"{topic}: {'/'.join(freqs)}. \"{sentence}\""),
                ssp_text=ssp_text or "(SSP gives no frequency for this topic)",
                proposed_fix=fix,
                client_question=f"How often is the {topic} actually performed, and is there evidence "
                                f"(tickets, sign-offs) for the last cycle?",
            ))
    return findings


def check_retired_tools(docs: list[Document], config: dict) -> list[Finding]:
    findings = []
    patterns = [
        (tool, re.compile(r"(?<![\w-])" + r"\s+".join(map(re.escape, tool.split())) + r"(?![\w-])", re.IGNORECASE))
        for tool in config["retired_tools"]
    ]
    for doc in docs:
        for line_no, line in enumerate(doc.lines, start=1):
            for tool, pat in patterns:
                if pat.search(line):
                    findings.append(Finding(
                        check="retired_tool",
                        document=doc.label,
                        location=f"{doc.rel}:{line_no}",
                        control="",
                        fix_type="STALE_TOOL",
                        priority="High",
                        current_text=_clip(f"Names retired tool \"{tool}\": \"{line.strip()}\""),
                        ssp_text=f"\"{tool}\" is not part of the system the SSP describes (on retired-tools list).",
                        proposed_fix=f"Replace \"{tool}\" with the current tool named in the SSP and update the steps.",
                        client_question=f"Has {tool} been fully decommissioned, and does it still hold any data?",
                    ))
    return findings


def run_checks(root: str | Path, config: dict) -> list[Finding]:
    docs = load_documents(root)
    findings: list[Finding] = []
    findings += check_review_cycles(docs, config)
    findings += check_retired_tools(docs, config)
    findings += check_versions(docs)
    findings += check_document_control(docs, config)
    order = {"High": 0, "Medium": 1, "Low": 2}
    findings.sort(key=lambda f: (order.get(f.priority, 9), f.check, f.location))
    return findings


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #

def format_report(findings: list[Finding]) -> str:
    if not findings:
        return "No inconsistencies found.\n"
    out = [f"{len(findings)} potential inconsistencies found (confirm each one in context):", ""]
    for i, f in enumerate(findings, start=1):
        out.append(f"[AUTO-{i:03d}] {f.priority:<6} {f.fix_type:<11} {f.document}  ({f.location})")
        out.append(f"    Now:  {f.current_text}")
        if f.ssp_text:
            out.append(f"    SSP:  {f.ssp_text}")
        out.append(f"    Fix:  {f.proposed_fix}")
        if f.client_question:
            out.append(f"    Ask:  {f.client_question}")
        out.append("")
    return "\n".join(out)


def write_csv(findings: list[Finding], path: str | Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FINDINGS_LOG_COLUMNS)
        writer.writeheader()
        for i, f in enumerate(findings, start=1):
            writer.writerow(f.as_row(f"AUTO-{i:03d}"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Flag inconsistencies between an SSP and its policies/procedures.")
    parser.add_argument("path", help="Folder (or single file) of .md/.txt documents to scan")
    parser.add_argument("--config", help="JSON config with retired_tools and review_topics")
    parser.add_argument("--csv", dest="csv_path", help="Also write findings to this CSV (findings-log columns)")
    parser.add_argument("--exit-zero", action="store_true", help="Exit 0 even when findings are reported")
    args = parser.parse_args(argv)

    if not Path(args.path).exists():
        parser.error(f"path not found: {args.path}")

    findings = run_checks(args.path, load_config(args.config))
    print(format_report(findings))
    if args.csv_path:
        write_csv(findings, args.csv_path)
        print(f"Wrote {len(findings)} rows to {args.csv_path}")
    return 0 if (args.exit_zero or not findings) else 1


if __name__ == "__main__":
    sys.exit(main())
