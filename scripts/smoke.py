"""Local smoke test for the ChemELLM kernel.

Runs against a started kernel: python scripts/smoke.py [base-url]
Checks: health -> create project -> properties calc -> export report -> review -> bundle.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"


def call(path, payload=None, method=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        BASE + path, data=data, method=method or ("POST" if data else "GET"),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        raise SystemExit(f"FAIL {path}: HTTP {error.code} {body[:500]}")


def main():
    health = call("/v1/health")
    print("health:", health["ok"], health["version"], "phaseGate=", health["phaseGate"])

    created = call("/v1/projects", {"name": "冒烟测试项目"}, "POST")
    project_id = created["project"]["projectId"]
    print("project:", project_id)

    requirements = call(f"/v1/projects/{project_id}/requirements", {
        "items": [
            {"code": "B01", "title": "原料规格调研", "mandatory": True},
            {"code": "P06", "title": "物料及热量平衡计算书", "mandatory": True},
        ]
    })
    print("requirements:", len(requirements["requirements"]))

    plan = call(f"/v1/projects/{project_id}/plan", {
        "deliverables": [
            {"key": "D-report", "title": "物料衡算报告", "requirementCodes": ["B01", "P06"], "formats": ["docx", "pdf"]}
        ],
        "objects": [{"key": "basis-demo", "kind": "basis", "title": "演示设计依据"}],
    })
    print("plan:", len(plan["plan"]["deliverables"]))

    call(f"/v1/projects/{project_id}/objects", {
        "kind": "basis", "key": "basis-demo", "title": "演示设计依据",
        "quantities": [{
            "key": "conversion", "value": 0.6, "unit": "1",
            "origin": "assumption", "conditions": "873.15 K, 100 kPa",
            "rationale": "冒烟测试假设，非工程依据",
        }],
    })

    calc = call(f"/v1/projects/{project_id}/execute", {
        "tool": "properties",
        "args": {"compound": "styrene"},
    })
    print("calc:", calc["tool"], "id=", (calc.get("calculationId") or "")[:8])
    if calc.get("warnings"):
        print("calc warnings:", calc["warnings"])

    report = call(f"/v1/projects/{project_id}/execute", {
        "tool": "export_report",
        "args": {
            "title": "冒烟测试报告",
            "body": "这是本地内核冒烟测试生成的草稿报告。\n物料衡算示例行：乙苯进料 100 kmol/h。",
            "formats": ["docx", "pdf"],
        },
    })
    print("report artifacts:", [item["name"] for item in report.get("artifacts", [])])

    review = call(f"/v1/projects/{project_id}/review", {"note": "smoke"})
    print("review ready:", review["review"]["ready"], "blockers:", review["review"]["blockers"])

    bundle = call(f"/v1/projects/{project_id}/bundle", {})
    print("bundle:", bundle["bundle"]["name"], bundle["bundle"]["bytes"], "bytes")
    print("SMOKE OK")


if __name__ == "__main__":
    main()
