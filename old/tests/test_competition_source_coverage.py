"""The 35 acceptance codes and their source fragments must match the supplied brief."""
import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader

from app.competition import GLOBAL_SOURCE_EXCERPTS, REQUIREMENTS, SOURCE_EXCERPTS, acceptance
from app.config import ROOT
from app.documents import ingest
from app.engineering import RequirementBatch, RequirementSource, engineering_status
from app.toolbox import run_tool


def normalized(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value))


def test_every_requirement_code_has_exact_original_pdf_source():
    source = ROOT / "26化工设计大赛题目.pdf"
    reader = PdfReader(source)
    assert len(reader.pages) == 5
    text = normalized("\n".join(page.extract_text() or "" for page in reader.pages))
    codes = [code for code, _, _, _ in REQUIREMENTS]
    assert len(codes) == 35 and len(set(codes)) == 35
    assert sum(mandatory for _, _, _, mandatory in REQUIREMENTS) == 31
    assert sum(not mandatory for _, _, _, mandatory in REQUIREMENTS) == 4
    assert set(SOURCE_EXCERPTS) == set(codes)
    for code in codes:
        for excerpt in SOURCE_EXCERPTS[code]:
            assert normalized(excerpt) in text, f"{code}: source fragment missing from supplied PDF: {excerpt}"
    for excerpt in GLOBAL_SOURCE_EXCERPTS:
        assert normalized(excerpt) in text, f"global output condition missing from supplied PDF: {excerpt}"


def test_original_task_hash_is_read_from_the_actual_supplied_file():
    content = (ROOT / "26化工设计大赛题目.pdf").read_bytes()
    assert content.startswith(b"%PDF-")
    assert len(content) > 100_000


def _exact_fragment(text, excerpt):
    compact = normalized(text)
    needle = normalized(excerpt)
    position = compact.find(needle)
    if position < 0:
        return None
    chars, starts, ends = [], [], []
    for index, char in enumerate(text):
        value = unicodedata.normalize("NFKC", char)
        for item in value:
            if not item.isspace():
                chars.append(item)
                starts.append(index)
                ends.append(index+1)
    if "".join(chars).find(needle) != position:
        raise AssertionError("normalized source map changed during match")
    return text[starts[position]:ends[position+len(needle)-1]]


def test_platform_binds_each_of_35_requirements_to_the_uploaded_original(project_id):
    source = (ROOT / "26化工设计大赛题目.pdf").read_bytes()
    artifact = ingest(project_id, "26化工设计大赛题目.pdf", source)
    extraction = run_tool(project_id, "document_extract", {
        "artifact_id": artifact["id"], "first_page": 1, "last_page": 5, "image_mode": "native"})
    read = run_tool(project_id, "document_read", {
        "snapshot_id": extraction["snapshot_id"], "limit": 100})
    blocks = read["blocks"]
    entries = []
    for code, title, _, mandatory in REQUIREMENTS:
        matched = None
        for fragment in SOURCE_EXCERPTS[code]:
            for block in blocks:
                quote = _exact_fragment(block["text"], fragment)
                if quote and len(normalized(quote)) >= 5:
                    matched = (block, quote)
                    break
            if matched:
                break
        assert matched, f"{code}: no exact quote could be selected from the uploaded PDF snapshot"
        block, quote = matched
        entries.append({"code": code, "title": title, "mandatory": mandatory,
            "applicability": "原题适用条件按来源原句保留；须结合设计对象校核。" if not mandatory else "原题必交项。",
            "snapshot_id": extraction["snapshot_id"], "block_id": block["id"], "quote": quote,
            "formats": ["docx", "pdf"] if code in {"D01", "D02", "D03"} else []})
    result = run_tool(project_id, "engineering_requirements", {"requirements": entries})
    assert len(result["source_bound"]) == 35 and result["added"] == []
    assert result["phase"]["source_unlinked_requirements"] == []
    status = engineering_status(project_id)
    assert len(status["requirements"]) == 35
    assert all(item.get("source", {}).get("source_sha256") for item in status["requirements"])
    assert sum(item["mandatory"] for item in status["requirements"]) == 31
