"""Record an isolated IDAES installation/runtime smoke without modifying ChemELlm."""
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AREA = ROOT / "output" / "backend-qualification"
REPORT = AREA / "idaes-install-report.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    AREA.mkdir(parents=True, exist_ok=True)
    idaes_data = AREA / "idaes-data"
    pyomo_config = AREA / "pyomo-config"
    idaes_data.mkdir(exist_ok=True)
    pyomo_config.mkdir(exist_ok=True)
    os.environ["IDAES_DATA"] = str(idaes_data)
    os.environ["PYOMO_CONFIG_DIR"] = str(pyomo_config)

    import idaes
    import pyomo
    from idaes.core import FlowsheetBlock
    from pyomo.environ import ConcreteModel, SolverFactory

    model = ConcreteModel()
    model.fs = FlowsheetBlock(dynamic=False)
    solvers = {name: bool(SolverFactory(name).available(False))
               for name in ("ipopt", "highs", "appsi_highs", "cbc", "glpk")}

    install = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}
    downloaded = {}
    for item in install.get("install", []):
        name = item.get("metadata", {}).get("name", "").lower()
        if name in {"idaes-pse", "pyomo"}:
            downloaded[name] = {
                "version": item.get("metadata", {}).get("version"),
                "sha256": item.get("download_info", {}).get("archive_info", {}).get("hashes", {}).get("sha256"),
                "url": item.get("download_info", {}).get("url"),
            }

    licenses = {}
    for name in ("idaes-pse", "pyomo"):
        distribution = metadata.distribution(name)
        licenses[name] = {
            "version": distribution.version,
            "license": distribution.metadata.get("License-Expression") or distribution.metadata.get("License"),
            "home_page": distribution.metadata.get("Home-page"),
        }

    result = {
        "date": "2026-10-21",
        "candidate": "IDAES Process Systems Engineering + Pyomo",
        "isolation": "output/backend-qualification/idaes-env",
        "installation": {
            "status": "installed",
            "install_report": str(REPORT.relative_to(ROOT)),
            "install_report_sha256": sha256(REPORT) if REPORT.exists() else None,
            "artifacts": downloaded,
            "licenses": licenses,
        },
        "runtime": {
            "idaes_version": idaes.__version__,
            "pyomo_version": pyomo.__version__,
            "flowsheet_block_constructed": model.fs is not None,
            "available_solvers": solvers,
            "status": "package_import_and_flowsheet_construction_passed; nonlinear_solve_not_run",
        },
        "platform_integration": "not integrated; no ChemELlm code or runtime changed",
        "engineering_delivery_acceptance": "not tested; no engineering files generated",
        "blocker": "No nonlinear solver executable is installed. Official IDAES extension download and read-only cloud SSH probes were blocked by network permission; escalation auto-review returned 503 and the action was not executed.",
        "vision_probe": {
            "status": "not_run",
            "reason": "No local model endpoint or API credentials configured; existing cloud endpoint could not be reached through SSH.",
        },
    }
    target = AREA / "idaes-qualification.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
