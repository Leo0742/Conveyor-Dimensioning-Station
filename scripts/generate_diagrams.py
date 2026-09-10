"""Generate engineering SVG diagrams from the selected station geometry."""

# SVG markup is intentionally kept as readable one-element-per-line source.
# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

from conveyor_dimensioning.hardware import GOCATOR_2880, calculate_linear_fov_layout

STYLE = """
<style>
  text { font-family: 'DejaVu Sans', Arial, sans-serif; fill: #17212b; }
  .title { font-size: 28px; font-weight: 700; }
  .label { font-size: 18px; }
  .small { font-size: 15px; fill: #455a64; }
  .hardware { fill: #e8f1fb; stroke: #145ea8; stroke-width: 2.5; }
  .process { fill: #f4f6f8; stroke: #455a64; stroke-width: 2; }
  .signal { stroke: #1565c0; stroke-width: 3; fill: none; marker-end: url(#arrow); }
  .dimension { stroke: #c62828; stroke-width: 2; fill: none; marker-start: url(#dim); marker-end: url(#dim); }
  .laser { stroke: #d32f2f; stroke-width: 3; fill: none; }
  .dash { stroke-dasharray: 8 6; }
</style>
<defs>
  <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#1565c0"/></marker>
  <marker id="dim" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,4 L8,0 L8,8 z" fill="#c62828"/></marker>
</defs>
"""


def _svg(body: str, *, width: int = 1200, height: int = 760) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{STYLE}<rect width="100%" height="100%" fill="white"/>{body}</svg>\n'
    )


def _side_view() -> str:
    layout = calculate_linear_fov_layout(GOCATOR_2880, target_top_fov_mm=680.0)
    return _svg(
        f"""
<text x="60" y="54" class="title">Измерительная станция — вид сбоку (Y–Z)</text>
<line x1="95" y1="610" x2="1110" y2="610" stroke="#263238" stroke-width="14"/>
<line x1="95" y1="628" x2="1110" y2="628" stroke="#90a4ae" stroke-width="8"/>
<text x="90" y="665" class="label">Конвейер, v = 1 m/s</text>
<path d="M300 665 H410" class="signal"/>

<rect x="535" y="82" width="130" height="68" rx="4" class="hardware"/>
<circle cx="570" cy="150" r="8" fill="#145ea8"/><circle cx="630" cy="150" r="8" fill="#145ea8"/>
<line x1="600" y1="150" x2="600" y2="610" class="laser"/>
<text x="600" y="113" text-anchor="middle" class="label">Gocator 2880</text>
<text x="600" y="137" text-anchor="middle" class="small">две камеры</text>
<text x="615" y="205" class="small">фиксированная X-Z плоскость профиля</text>

<polygon points="505,610 505,400 695,400 695,610" fill="#fff3e0" stroke="#ef6c00" stroke-width="2"/>
<text x="600" y="440" text-anchor="middle" class="label">товар</text>
<text x="600" y="466" text-anchor="middle" class="small">до 300 mm</text>

<line x1="700" y1="150" x2="700" y2="610" class="dimension"/>
<text x="716" y="390" class="label" fill="#c62828">{layout.mount_height_above_belt_mm:.0f} mm</text>
<line x1="505" y1="380" x2="695" y2="380" class="dimension"/>
<text x="600" y="365" text-anchor="middle" class="small">до 400 mm по ходу</text>

<line x1="350" y1="580" x2="850" y2="580" class="dimension"/>
<text x="600" y="566" text-anchor="middle" class="label">700 mm формируются движением по Y</text>
<line x1="350" y1="250" x2="350" y2="610" stroke="#607d8b" stroke-width="2" class="dash"/>
<line x1="850" y1="250" x2="850" y2="610" stroke="#607d8b" stroke-width="2" class="dash"/>

<line x1="170" y1="250" x2="170" y2="610" stroke="#7b1fa2" stroke-width="4"/>
<circle cx="150" cy="575" r="13" fill="#7b1fa2"/><circle cx="190" cy="575" r="13" fill="#7b1fa2"/>
<text x="170" y="232" text-anchor="middle" class="label">SICK WLF4FI</text>
<line x1="170" y1="285" x2="350" y2="285" class="dimension"/>
<text x="260" y="270" text-anchor="middle" class="small">250 mm до зоны</text>

<circle cx="980" cy="625" r="35" fill="#e8f1fb" stroke="#145ea8" stroke-width="3"/>
<circle cx="980" cy="625" r="7" fill="#145ea8"/>
<text x="980" y="690" text-anchor="middle" class="label">SICK DFS60 + мерное колесо</text>
<text x="60" y="715" class="small">PRELIMINARY CALCULATED LAYOUT: FOV {layout.target_top_fov_mm:.0f} mm на Z=300 mm, запас {layout.lateral_margin_per_side_mm:.0f} mm/сторону.</text>
<text x="60" y="738" class="small">Финальная установка определяется factory calibration model и проверкой лазерной безопасности.</text>
"""
    )


def _top_view() -> str:
    layout = calculate_linear_fov_layout(GOCATOR_2880, target_top_fov_mm=680.0)
    return _svg(
        f"""
<text x="60" y="54" class="title">Измерительная станция — вид сверху (X–Y)</text>
<rect x="360" y="180" width="480" height="420" fill="#eceff1" stroke="#263238" stroke-width="4"/>
<text x="600" y="630" text-anchor="middle" class="label">ширина ленты 600 mm</text>
<line x1="360" y1="615" x2="840" y2="615" class="dimension"/>

<rect x="320" y="180" width="560" height="420" fill="none" stroke="#607d8b" stroke-width="2" class="dash"/>
<text x="895" y="400" class="label">зона 700 mm</text>
<line x1="880" y1="180" x2="880" y2="600" class="dimension"/>

<line x1="230" y1="390" x2="970" y2="390" class="laser"/>
<text x="985" y="396" class="label">scan line</text>
<line x1="230" y1="420" x2="970" y2="420" class="dimension"/>
<text x="600" y="450" text-anchor="middle" class="small">FOV на ленте ≈{layout.belt_fov_mm:.0f} mm; {layout.target_top_fov_mm:.0f} mm на Z=300 mm</text>
<text x="600" y="476" text-anchor="middle" class="small">запас по {layout.lateral_margin_per_side_mm:.0f} mm с каждой стороны ленты</text>

<g transform="rotate(24 600 420)">
  <rect x="535" y="370" width="130" height="100" fill="#fff3e0" stroke="#ef6c00" stroke-width="3"/>
</g>
<text x="600" y="520" text-anchor="middle" class="label">произвольный yaw</text>

<line x1="300" y1="80" x2="900" y2="80" stroke="#7b1fa2" stroke-width="4"/>
<circle cx="330" cy="80" r="12" fill="#7b1fa2"/><circle cx="870" cy="80" r="12" fill="#7b1fa2"/>
<text x="930" y="87" class="label">WLF4FI trigger</text>
<line x1="900" y1="80" x2="900" y2="180" class="dimension"/>
<text x="920" y="135" class="small">250 mm</text>

<path d="M1030 260 V160" class="signal"/>
<text x="1050" y="215" class="label">Y</text>
<path d="M1030 260 H1130" class="signal"/>
<text x="1140" y="267" class="label">X</text>
<text x="60" y="690" class="small">PRELIMINARY CALCULATED LAYOUT; один Gocator 2880 по центру, две камеры смотрят на одну лазерную линию.</text>
<text x="60" y="715" class="small">Фактическая граница FOV и координаты монтажа проверяются по factory calibration model.</text>
"""
    )


def _block_diagram() -> str:
    return _svg(
        """
<text x="60" y="54" class="title">Контур данных и управления</text>

<rect x="60" y="115" width="220" height="90" rx="6" class="hardware"/>
<text x="170" y="150" text-anchor="middle" class="label">SICK WLF4FI</text><text x="170" y="177" text-anchor="middle" class="small">presence trigger</text>
<rect x="60" y="260" width="220" height="90" rx="6" class="hardware"/>
<text x="170" y="295" text-anchor="middle" class="label">SICK DFS60</text><text x="170" y="322" text-anchor="middle" class="small">encoder, шаг 1 mm</text>
<rect x="360" y="175" width="240" height="120" rx="6" class="hardware"/>
<text x="480" y="215" text-anchor="middle" class="label">Gocator 2880</text><text x="480" y="242" text-anchor="middle" class="small">dual-camera laser profiles</text><text x="480" y="268" text-anchor="middle" class="small">Gigabit Ethernet</text>

<path d="M280 160 H360" class="signal"/><path d="M280 305 H320 V260 H360" class="signal"/>
<rect x="680" y="105" width="260" height="310" rx="6" class="process"/>
<text x="810" y="142" text-anchor="middle" class="label">OnLogic Karbon K801</text>
<text x="710" y="182" class="small">1. calibration transform</text><text x="710" y="212" class="small">2. plane removal</text>
<text x="710" y="242" class="small">3. filter + cluster</text><text x="710" y="272" class="small">4. hull + minimal OBB</text>
<text x="710" y="302" class="small">5. quality checks</text><text x="710" y="332" class="small">6. multi-frame aggregation</text>
<text x="710" y="352" class="small">7. append-only JSONL outbox</text>
<text x="710" y="377" class="small">+ deterministic measurement_id</text>
<path d="M600 235 H680" class="signal"/>

<rect x="1000" y="175" width="150" height="120" rx="6" class="hardware"/>
<text x="1075" y="220" text-anchor="middle" class="label">WMS</text><text x="1075" y="246" text-anchor="middle" class="small">JSON schema: PoC</text><text x="1075" y="270" text-anchor="middle" class="small">HTTPS/mTLS: proposed</text>
<path d="M940 235 H1000" class="signal"/>

<rect x="680" y="500" width="260" height="100" rx="6" class="process"/>
<text x="810" y="537" text-anchor="middle" class="label">Production monitoring</text><text x="810" y="567" text-anchor="middle" class="small">proposed: gaps, fill, saturation, MAD</text>
<path d="M810 415 V500" class="signal"/>
<text x="60" y="690" class="small">Real-time цикл локальный. JSONL outbox содержит deterministic measurement_id для идемпотентной доставки.</text>
""",
        height=720,
    )


def _png_axes(*, height: int = 760):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 14,
            "figure.facecolor": "white",
        }
    )
    figure, axis = plt.subplots(figsize=(12, height / 100), dpi=200)
    axis.set_xlim(0, 1200)
    axis.set_ylim(0, height)
    axis.axis("off")
    return figure, axis


def _save_png(figure, path: Path) -> None:
    figure.savefig(
        path,
        dpi=200,
        facecolor="white",
        metadata={"Software": "conveyor-dimensioning deterministic diagrams"},
    )
    plt.close(figure)


def _side_png(path: Path) -> None:
    layout = calculate_linear_fov_layout(GOCATOR_2880, target_top_fov_mm=680.0)
    figure, axis = _png_axes()
    axis.text(60, 705, "Измерительная станция — вид сбоку (Y–Z)", size=21, weight="bold")
    axis.plot([85, 1110], [135, 135], color="#263238", linewidth=10)
    axis.text(90, 80, "Конвейер, v = 1 m/s", size=14)
    axis.add_patch(Rectangle((535, 610), 130, 68, facecolor="#e8f1fb", edgecolor="#145ea8", lw=2))
    axis.text(600, 650, "Gocator 2880", ha="center", weight="bold")
    axis.text(600, 625, "две камеры", ha="center", size=11, color="#455a64")
    axis.plot([600, 600], [610, 135], color="#d32f2f", linewidth=2.5)
    axis.text(615, 560, "фиксированная X-Z плоскость профиля", size=10, color="#455a64")
    axis.add_patch(Rectangle((505, 135), 190, 210, facecolor="#fff3e0", edgecolor="#ef6c00", lw=2))
    axis.text(600, 250, "товар\nдо 300 mm", ha="center", va="center")
    axis.annotate(
        "",
        xy=(730, 610),
        xytext=(730, 135),
        arrowprops={"arrowstyle": "<->", "color": "#c62828", "lw": 1.8},
    )
    axis.text(748, 365, f"{layout.mount_height_above_belt_mm:.0f} mm", color="#c62828")
    axis.axvline(350, ymin=0.18, ymax=0.70, color="#607d8b", ls="--")
    axis.axvline(850, ymin=0.18, ymax=0.70, color="#607d8b", ls="--")
    axis.annotate(
        "",
        xy=(850, 165),
        xytext=(350, 165),
        arrowprops={"arrowstyle": "<->", "color": "#c62828"},
    )
    axis.text(600, 180, "700 mm формируются движением по Y", ha="center")
    axis.plot([170, 170], [135, 475], color="#7b1fa2", linewidth=3)
    axis.scatter([155, 185], [150, 150], s=110, color="#7b1fa2", zorder=4)
    axis.text(170, 495, "SICK WLF4FI", ha="center", weight="bold")
    axis.annotate(
        "",
        xy=(350, 455),
        xytext=(170, 455),
        arrowprops={"arrowstyle": "<->", "color": "#c62828"},
    )
    axis.text(260, 470, "250 mm до зоны", ha="center", size=10)
    axis.add_patch(plt.Circle((980, 105), 30, facecolor="#e8f1fb", edgecolor="#145ea8", lw=2))
    axis.add_patch(plt.Circle((980, 105), 6, facecolor="#145ea8"))
    axis.text(980, 55, "SICK DFS60 + мерное колесо", ha="center", size=11)
    axis.add_patch(
        FancyArrowPatch(
            (300, 75), (420, 75), arrowstyle="->", mutation_scale=18, color="#1565c0", lw=2
        )
    )
    axis.text(435, 75, "Y", va="center", weight="bold")
    axis.text(
        60,
        28,
        f"PRELIMINARY CALCULATED LAYOUT: FOV {layout.target_top_fov_mm:.0f} mm на Z=300 mm; "
        f"запас {layout.lateral_margin_per_side_mm:.0f} mm/сторону. Проверить factory calibration model.",
        size=10,
        color="#455a64",
    )
    _save_png(figure, path)


def _top_png(path: Path) -> None:
    layout = calculate_linear_fov_layout(GOCATOR_2880, target_top_fov_mm=680.0)
    figure, axis = _png_axes()
    axis.text(60, 680, "Измерительная станция — вид сверху (X–Y)", size=21, weight="bold")
    axis.add_patch(Rectangle((360, 145), 480, 385, facecolor="#eceff1", edgecolor="#263238", lw=2.5))
    axis.add_patch(Rectangle((320, 145), 560, 385, fill=False, edgecolor="#607d8b", lw=1.5, ls="--"))
    axis.plot([180, 1020], [335, 335], color="#d32f2f", lw=2.5)
    axis.add_patch(Rectangle((535, 285), 130, 100, angle=24, facecolor="#fff3e0", edgecolor="#ef6c00", lw=2))
    axis.text(600, 105, "ширина ленты 600 mm", ha="center")
    axis.text(900, 335, "зона 700 mm", rotation=90, va="center")
    axis.text(
        600,
        600,
        f"FOV на ленте ≈{layout.belt_fov_mm:.0f} mm; {layout.target_top_fov_mm:.0f} mm на Z=300 mm",
        ha="center",
    )
    axis.text(
        600,
        565,
        f"запас по {layout.lateral_margin_per_side_mm:.0f} mm с каждой стороны ленты",
        ha="center",
        color="#455a64",
    )
    axis.add_patch(FancyArrowPatch((1000, 230), (1110, 230), arrowstyle="->", mutation_scale=18, color="#1565c0", lw=2))
    axis.add_patch(FancyArrowPatch((1000, 230), (1000, 330), arrowstyle="->", mutation_scale=18, color="#1565c0", lw=2))
    axis.text(1120, 230, "X", va="center")
    axis.text(1000, 345, "Y", ha="center")
    axis.text(
        60,
        28,
        "PRELIMINARY CALCULATED LAYOUT; один Gocator 2880 по центру; две камеры наблюдают одну лазерную линию.",
        size=10,
        color="#455a64",
    )
    _save_png(figure, path)


def _block_png(path: Path) -> None:
    figure, axis = _png_axes(height=720)
    axis.text(60, 670, "Контур данных и управления", size=21, weight="bold")
    boxes = [
        (60, 485, 220, 80, "SICK WLF4FI\npresence trigger", "#e8f1fb"),
        (60, 330, 220, 80, "SICK DFS60\nencoder, шаг 1 mm", "#e8f1fb"),
        (355, 405, 240, 105, "Gocator 2880\ndual-camera profiles\nGigabit Ethernet", "#e8f1fb"),
        (675, 280, 270, 330, "OnLogic Karbon K801\n\n1. transform\n2. plane removal\n3. filter + cluster\n4. hull + minimal OBB\n5. quality gates\n6. aggregation\n7. append-only JSONL\noutbox + measurement_id", "#f4f6f8"),
        (985, 405, 180, 105, "WMS\nJSON: PoC\nHTTPS/mTLS\nproposed", "#e8f1fb"),
        (675, 90, 270, 90, "Production monitoring\nproposed: gaps, fill,\nsaturation, MAD", "#f4f6f8"),
    ]
    for x, y, width, height, label, color in boxes:
        axis.add_patch(Rectangle((x, y), width, height, facecolor=color, edgecolor="#145ea8", lw=1.8))
        axis.text(x + width / 2, y + height / 2, label, ha="center", va="center", size=11)
    arrows = [((280, 525), (355, 470)), ((280, 370), (355, 440)), ((595, 455), (675, 455)), ((945, 455), (985, 455)), ((810, 280), (810, 180))]
    for start, end in arrows:
        axis.add_patch(FancyArrowPatch(start, end, arrowstyle="->", mutation_scale=15, color="#1565c0", lw=2))
    axis.text(
        60,
        28,
        "Real-time цикл локальный; JSONL outbox содержит deterministic measurement_id для идемпотентной доставки.",
        size=10,
        color="#455a64",
    )
    _save_png(figure, path)


def generate_all(output_dir: str | Path) -> list[Path]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    diagrams = {
        "layout_side.svg": _side_view(),
        "layout_top.svg": _top_view(),
        "system_block.svg": _block_diagram(),
    }
    generated = []
    for name, content in diagrams.items():
        path = destination / name
        path.write_text(content, encoding="utf-8")
        generated.append(path)
    for name, renderer in {
        "layout_side.png": _side_png,
        "layout_top.png": _top_png,
        "system_block.png": _block_png,
    }.items():
        path = destination / name
        renderer(path)
        generated.append(path)
    return generated


if __name__ == "__main__":
    generate_all(Path("assets/diagrams"))
