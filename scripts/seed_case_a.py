"""Seed case A (2026 competition) requirements and deliverable plan from the archived task PDF.

The requirement text is the original task's own list (old/app/competition.py, verified
against the PDF in the archive). This script imports source text; it does not invent
engineering answers.

Usage: python scripts/seed_case_a.py <projectId> [base-url]
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "old"))

from app.competition import REQUIREMENTS, SOURCE_EXCERPTS  # noqa: E402

BASE = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8765"
PROJECT = sys.argv[1] if len(sys.argv) > 1 else ""
if not PROJECT:
    raise SystemExit("usage: seed_case_a.py <projectId> [base-url]")


def post(path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"content-type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    items = []
    for code, title, page, mandatory in REQUIREMENTS:
        quotes = SOURCE_EXCERPTS.get(code) or []
        items.append({
            "code": code,
            "title": title,
            "mandatory": bool(mandatory),
            "applicability": f"原题第 {page} 页；按“开源替代 + 明确标注”口径交付",
            "quote": (quotes[0] if quotes else title)[:400],
            "source": f"26化工设计大赛题目.pdf p.{page}",
        })
    result = post(f"/v1/projects/{PROJECT}/requirements", {"items": items})
    print("requirements:", len(result.get("requirements") or []), "phase:", result.get("phase"))

    deliverables = [
        {"key": "A-D01", "title": "可行性研究报告（替代交付）", "formats": ["docx", "pdf"],
         "requirementCodes": ["B01", "B02", "B03", "F01", "F02", "F04", "F06", "D01"]},
        {"key": "A-D02", "title": "初步设计说明书（替代交付）", "formats": ["docx", "pdf"],
         "requirementCodes": ["F03", "F05", "P01", "P02", "P06", "E05", "L05", "C01", "D02"]},
        {"key": "A-D03", "title": "典型设备计算说明书（替代交付）", "formats": ["docx", "pdf"],
         "requirementCodes": ["E01", "E02", "E03", "E04", "D03"]},
        {"key": "A-D04", "title": "设计图集（PFD/P&ID/布置，开源 CAD 替代）", "formats": ["dxf", "pdf", "svg"],
         "requirementCodes": ["P04", "P05", "L02", "L03", "D04"]},
        {"key": "A-D05", "title": "流程模拟与优化结果（开源模拟替代）", "formats": ["md", "json", "zip"],
         "requirementCodes": ["P03", "D05"]},
        {"key": "A-L01", "title": "车间布置与配管设计说明", "formats": ["docx"], "requirementCodes": ["L01"]},
        {"key": "A-L04", "title": "三维布置源文件（FreeCAD）", "formats": ["step", "fcstd"], "requirementCodes": ["L04"]},
        {"key": "A-C01", "title": "经济分析与评价", "formats": ["xlsx", "docx"], "requirementCodes": ["C01"]},
        {"key": "A-S01", "title": "HAZOP 分析（附加项）", "formats": ["docx", "xlsx"], "requirementCodes": ["S01"]},
        {"key": "A-S02", "title": "能量集成与节能（附加项）", "formats": ["docx", "xlsx"], "requirementCodes": ["S02"]},
        {"key": "A-S03", "title": "成本估算源文件（附加项）", "formats": ["xlsx"], "requirementCodes": ["S03"]},
        {"key": "A-S04", "title": "容器结构设计（附加项）", "formats": ["docx", "step"], "requirementCodes": ["S04"]},
    ]
    plan = post(f"/v1/projects/{PROJECT}/plan", {
        "deliverables": deliverables,
        "objects": [
            {"key": "basis-main", "kind": "basis", "title": "主设计依据"},
            {"key": "streams-main", "kind": "stream", "title": "主物流表"},
            {"key": "equipment-list", "kind": "equipment", "title": "设备一览表"},
            {"key": "economics", "kind": "cost", "title": "经济分析对象"},
        ],
    })
    planned = {code for item in plan["plan"]["deliverables"] for code in item.get("requirementCodes") or []}
    mandatory = {code for code, _, _, required in REQUIREMENTS if required}
    covered = mandatory & planned
    print("deliverables:", len(plan["plan"]["deliverables"]), "phase:", plan.get("phase"))
    print(f"mandatory coverage: {len(covered)}/{len(mandatory)}")
    print("uncovered:", sorted(mandatory - planned) or "none")


if __name__ == "__main__":
    main()
