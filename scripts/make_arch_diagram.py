"""Render the architecture diagram used in the technical document."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "Arial"]

NAVY = "#0B2239"
NAVY2 = "#15324D"
TEAL = "#1F9E8F"
AMBER = "#E8A33D"
LIGHT = "#F5F7F9"
GRAY = "#607180"
BORDER = "#D8E0E6"


def box(ax, x, y, w, h, title, body="", color=NAVY, text="white", radius=0.02):
    patch = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.01,rounding_size={radius}",
                           linewidth=1.0, edgecolor=color, facecolor=color)
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center",
            color=text, fontsize=13, fontweight="bold")
    if body:
        ax.text(x + w / 2, y + h * 0.30, body, ha="center", va="center",
                color=text, fontsize=9.2, linespacing=1.3)


def arrow(ax, x1, y1, x2, y2, color=GRAY):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                                 linewidth=1.4, color=color, shrinkA=2, shrinkB=2))


def main():
    fig, ax = plt.subplots(figsize=(13.2, 7.2), dpi=220)
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    box(ax, 0.5, 5.35, 3.5, 1.15, "DSH Web GUI / 会话",
        "模型 · 审批 · 子代理 · 面板", NAVY)
    box(ax, 4.75, 5.35, 3.7, 1.15, "Host 插件",
        "@local/dsh-chemellm\n12 个 chem_* 工具 · 阶段守卫 · 自动拉起", TEAL)
    box(ax, 9.1, 5.35, 3.55, 1.15, "本地内核 FastAPI :8765",
        "60 个可执行工具 · 确定性计算", NAVY2)
    arrow(ax, 4.0, 5.92, 4.7, 5.92)
    arrow(ax, 8.45, 5.92, 9.05, 5.92)

    box(ax, 0.5, 3.15, 12.15, 1.55, "内核能力层",
        "22 类计算模型  ·  P&ID / 设备图  ·  P&ID 数据链  · 设备数据表  ·  安全阀选型  ·  HAZOP/LOPA  ·  合规矩阵",
        "white", text=NAVY)
    arrow(ax, 10.85, 5.3, 10.85, 4.75)

    box(ax, 0.5, 1.1, 12.15, 1.45, "本机数据层",
        "data/projects（项目 JSON）  ·  data/kernel/artifacts（成果文件）  ·  data/bundles（SHA256 manifest zip）  ·  .chem（只读快照）",
        "#EAF3F1", text=NAVY)
    arrow(ax, 6.55, 3.1, 6.55, 2.6)

    ax.text(0.55, 0.55, "本机 loopback，无云端依赖　|　DSH 负责交互与编排，内核负责确定性计算",
            fontsize=9.5, color=GRAY, ha="left")

    out = Path("docs/assets/tech-architecture.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    print(out, out.stat().st_size)


if __name__ == "__main__":
    main()
