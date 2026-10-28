"""Remove superseded 3D exports (same kind) from project file lists.

The panel previews a file by artifact id; old FCStd/STEP records have no preview
SVG and would look empty when clicked. Keep only the newest fcstd and step per
project (the ones generated together with layout-preview.svg).

Usage: python scripts/prune_3d.py <projectRoot> [projectId ...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/projects")
targets = sys.argv[2:]

for project_file in sorted(root.glob("*/project.json")):
    project = json.loads(project_file.read_text(encoding="utf-8"))
    project_id = project.get("id")
    if targets and project_id not in targets:
        continue
    files = project.get("files") or []
    # Only superseded 3D *layout* exports share the same filename; per-equipment
    # CAD parts (设备模型.*) must all be kept, so they are excluded here.
    def is_layout_3d(item: dict) -> bool:
        return item.get("kind") in {"fcstd", "step"} and str(item.get("name") or "").startswith("三维设备布置")

    keep_index = {}
    for index, item in enumerate(files):
        if is_layout_3d(item):
            keep_index[item.get("kind")] = index
    removed = 0
    kept = []
    for index, item in enumerate(files):
        if is_layout_3d(item) and keep_index.get(item.get("kind")) != index:
            removed += 1
            continue
        kept.append(item)
    if removed:
        project["files"] = kept
        project_file.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{project_id}: removed {removed}, remaining files {len(kept)}")
