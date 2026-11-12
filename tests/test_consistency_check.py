"""Tests for consistency_check.py. All sample content is fictional."""

from pathlib import Path
import csv
import json
import textwrap

import pytest

import consistency_check as cc

REPO = Path(__file__).resolve().parents[1]
ACME = REPO / "examples" / "acme"
CONFIG = REPO / "config" / "check_config.json"


def header(doc_id, version, approved="ISSO"):
    return textwrap.dedent(f"""\
        | Field | Value |
        |---|---|
        | Document ID | {doc_id} |
        | Version | {version} |
        | Effective date | 2026-01-01 |
        | Owner | ISSO |
        | Approved by | {approved} |
        """)


def write(folder: Path, name: str, text: str) -> Path:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def config():
    return cc.load_config(CONFIG)


# --------------------------------------------------------------------------- #
# Unit tests: helpers
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("text, expected", [
    ("Logs are reviewed weekly.", ["weekly"]),
    ("Reviewed Quarterly by the ISSO.", ["quarterly"]),
    ("Performed annually.", ["annually"]),
    ("An annual review is held.", ["annually"]),
    ("Reviewed semi-annually.", ["semiannually"]),
    ("Reviewed every 90 days.", ["quarterly"]),
    ("Reviewed every 12 months.", ["annually"]),
    ("Separate from daily-use accounts.", []),
    ("No frequency here.", []),
])
def test_find_frequencies(text, expected):
    assert cc.find_frequencies(text) == expected


@pytest.mark.parametrize("a, b, equal", [
    ("2", "2.0", True),
    ("3.0", "3", True),
    ("2.1", "3.0", False),
    ("1.10", "1.1", False),
])
def test_normalize_version(a, b, equal):
    assert (cc.normalize_version(a) == cc.normalize_version(b)) is equal


def test_parse_header_reads_table_and_colon_formats():
    table = cc.parse_header(header("ACME-POL-XX-01", "1.2").splitlines())
    assert table["document id"] == "ACME-POL-XX-01"
    assert table["version"] == "1.2"
    colon = cc.parse_header(["Document ID: ACME-PRO-YY-02", "Version: v4.0"])
    assert colon["document id"] == "ACME-PRO-YY-02"
    assert colon["version"] == "v4.0"


def test_load_config_accepts_plain_keyword_lists(tmp_path):
    cfg_path = write(tmp_path, "c.json", json.dumps({
        "retired_tools": ["OldTool"],
        "review_topics": {"badge review": ["badge"]},
    }))
    cfg = cc.load_config(cfg_path)
    assert cfg["review_topics"]["badge review"] == {"control": "", "keywords": ["badge"]}
    assert "Approved by" in cfg["required_header_fields"]  # default kept


# --------------------------------------------------------------------------- #
# Check: version mismatches
# --------------------------------------------------------------------------- #

def test_version_mismatch_flagged(tmp_path, config):
    write(tmp_path, "ssp.md", header("ACME-SSP-001", "3.0") + "\nThe SSP.\n")
    write(tmp_path, "pol.md", header("ACME-POL-ZZ-01", "1.0") + "\nSupports ACME-SSP-001 v2.1.\n")
    findings = cc.check_versions(cc.load_documents(tmp_path))
    assert len(findings) == 1
    f = findings[0]
    assert f.check == "version_mismatch"
    assert f.fix_type == "DOC_CONTROL"
    assert "v2.1" in f.current_text and "v3.0" in f.ssp_text


def test_matching_version_not_flagged(tmp_path):
    write(tmp_path, "ssp.md", header("ACME-SSP-001", "3.0"))
    write(tmp_path, "pol.md", header("ACME-POL-ZZ-01", "1.0") + "\nSupports ACME-SSP-001 v3.\n")
    assert cc.check_versions(cc.load_documents(tmp_path)) == []


def test_reference_to_missing_document_flagged(tmp_path):
    write(tmp_path, "ssp.md", header("ACME-SSP-001", "3.0") + "\nFollow ACME-PRO-QQ-09 v1.0.\n")
    findings = cc.check_versions(cc.load_documents(tmp_path))
    assert [f.check for f in findings] == ["missing_reference"]
    assert findings[0].fix_type == "MISSING"


# --------------------------------------------------------------------------- #
# Check: review cycles
# --------------------------------------------------------------------------- #

def test_review_cycle_mismatch_against_ssp(tmp_path, config):
    write(tmp_path, "ssp.md", header("ACME-SSP-001", "1.0")
          + "\nThe ISSO reviews privileged accounts quarterly.\n")
    write(tmp_path, "pol.md", header("ACME-POL-AC-01", "1.0")
          + "\nPrivileged accounts are reviewed\nannually by IT.\n")  # wrapped line
    findings = cc.check_review_cycles(cc.load_documents(tmp_path), config)
    assert len(findings) == 1
    f = findings[0]
    assert f.document == "ACME-POL-AC-01"
    assert f.control == "3.1.5"
    assert f.priority == "High"
    assert "annually" in f.current_text and "quarterly" in f.ssp_text
    assert f.location.endswith(":9")  # 7 header lines + blank; sentence starts on line 9


def test_consistent_review_cycles_not_flagged(tmp_path, config):
    write(tmp_path, "ssp.md", header("ACME-SSP-001", "1.0") + "\nThe ISSO reviews audit logs weekly.\n")
    write(tmp_path, "pro.md", header("ACME-PRO-AU-01", "1.0") + "\nEvery week (weekly), audit logs are checked.\n")
    assert cc.check_review_cycles(cc.load_documents(tmp_path), config) == []


def test_review_cycle_mismatch_without_ssp(tmp_path, config):
    write(tmp_path, "a.md", header("ACME-POL-AU-01", "1.0") + "\nAudit logs are reviewed weekly.\n")
    write(tmp_path, "b.md", header("ACME-PRO-AU-01", "1.0") + "\nAudit logs are reviewed monthly.\n")
    findings = cc.check_review_cycles(cc.load_documents(tmp_path), config)
    assert {f.document for f in findings} == {"ACME-POL-AU-01", "ACME-PRO-AU-01"}
    assert all("no frequency" in f.ssp_text for f in findings)


# --------------------------------------------------------------------------- #
# Check: retired tools
# --------------------------------------------------------------------------- #

def test_retired_tool_flagged_case_insensitive(tmp_path, config):
    write(tmp_path, "pro.md", header("ACME-PRO-AU-01", "1.0") + "\nOpen the logharbor console.\n")
    findings = cc.check_retired_tools(cc.load_documents(tmp_path), config)
    assert len(findings) == 1
    assert findings[0].fix_type == "STALE_TOOL"
    assert findings[0].location.endswith(":9")


def test_multi_word_retired_tool_and_no_partial_match(tmp_path):
    cfg = cc.load_config(None)
    cfg["retired_tools"] = ["VaultKeep 6", "Trail"]
    write(tmp_path, "pro.md", header("ACME-PRO-AC-01", "1.0")
          + "\nCheck out credentials from VaultKeep  6.\nUse TicketTrail for tickets.\n")
    findings = cc.check_retired_tools(cc.load_documents(tmp_path), cfg)
    assert [f.current_text.split('"')[1] for f in findings] == ["VaultKeep 6"]


def test_retired_tools_list_is_configurable(tmp_path):
    write(tmp_path, "pro.md", header("ACME-PRO-AU-01", "1.0") + "\nOpen the LogHarbor console.\n")
    cfg = cc.load_config(None)  # empty retired-tools list
    assert cc.check_retired_tools(cc.load_documents(tmp_path), cfg) == []


# --------------------------------------------------------------------------- #
# Check: document control
# --------------------------------------------------------------------------- #

def test_blank_and_missing_header_fields_flagged(tmp_path, config):
    write(tmp_path, "pro.md", header("ACME-PRO-AU-01", "1.0", approved=""))
    write(tmp_path, "nohdr.md", "# Untitled procedure\n\nDo the thing.\n")
    findings = cc.check_document_control(cc.load_documents(tmp_path), config)
    texts = [f.current_text for f in findings]
    assert 'Header field "Approved by" is blank.' in texts
    assert 'Header field "Version" is missing.' in texts


def test_duplicate_document_id_flagged(tmp_path, config):
    write(tmp_path, "a.md", header("ACME-POL-AC-01", "1.0"))
    write(tmp_path, "b.md", header("ACME-POL-AC-01", "2.0"))
    findings = cc.check_document_control(cc.load_documents(tmp_path), config)
    assert any("also used by" in f.current_text for f in findings)


# --------------------------------------------------------------------------- #
# Integration: the fictional Acme package
# --------------------------------------------------------------------------- #

def test_acme_example_catches_every_planted_issue(config):
    findings = cc.run_checks(ACME, config)
    by_check = {}
    for f in findings:
        by_check.setdefault(f.check, []).append(f)

    # Review cycles that disagree with the SSP
    cycle_docs = {f.document for f in by_check["review_cycle_mismatch"]}
    assert cycle_docs == {"ACME-POL-AC-01", "ACME-PRO-AU-01"}

    # Policy citing the wrong SSP version
    assert {f.document for f in by_check["version_mismatch"]} == {"ACME-POL-IR-01"}

    # Procedure naming a tool the SSP doesn't
    assert [f.document for f in by_check["retired_tool"]] == ["ACME-PRO-AU-01"]

    # Referenced CM procedure isn't in the package
    assert "ACME-PRO-CM-01" in by_check["missing_reference"][0].current_text


def test_acme_example_has_no_false_positive_on_consistent_topics(config):
    findings = cc.run_checks(ACME, config)
    controls = {f.control for f in findings if f.check == "review_cycle_mismatch"}
    assert "3.6.3" not in controls  # IR test: annual everywhere
    assert "3.4.1" not in controls  # baseline review: only the SSP states it


def test_readme_files_are_skipped(config):
    docs = cc.load_documents(ACME)
    assert all(d.path.name.lower() != "readme.md" for d in docs)


def test_cli_writes_csv_with_findings_log_columns(tmp_path, capsys):
    out_csv = tmp_path / "out.csv"
    code = cc.main([str(ACME), "--config", str(CONFIG), "--csv", str(out_csv)])
    assert code == 1  # findings present
    with open(out_csv, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        assert reader.fieldnames == cc.FINDINGS_LOG_COLUMNS
    assert rows and rows[0]["ID"] == "AUTO-001"
    assert "potential inconsistencies" in capsys.readouterr().out


def test_cli_exit_zero_and_clean_package(tmp_path):
    write(tmp_path, "ssp.md", header("ACME-SSP-001", "1.0") + "\nAll good.\n")
    assert cc.main([str(tmp_path)]) == 0
    assert cc.main([str(ACME), "--config", str(CONFIG), "--exit-zero"]) == 0


def test_template_csv_headers_match_checker_output():
    with open(REPO / "templates" / "findings_log.csv", newline="", encoding="utf-8") as fh:
        assert next(csv.reader(fh)) == cc.FINDINGS_LOG_COLUMNS
