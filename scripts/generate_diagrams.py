"""Generate engineering SVG diagrams from the selected station geometry."""

# SVG markup is intentionally kept as readable one-element-per-line source.
# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.transforms import Bbox

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
<defs>
  <marker id="dim-secondary" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,4 L8,0 L8,8 z" fill="#546e7a"/></marker>
</defs>
<text x="40" y="45" class="title">Измерительная станция — вид сбоку (Y-Z)</text>
<text x="40" y="78" class="small">Один фиксированный профиль X-Z; 3D-облако накапливается при движении товара по Y.</text>

<rect x="455" y="110" width="190" height="84" rx="4" class="hardware"/>
<text x="550" y="143" text-anchor="middle" class="label">Gocator 2880</text>
<text x="550" y="171" text-anchor="middle" class="small">две камеры</text>
<circle cx="515" cy="211" r="7" fill="#145ea8"/><circle cx="585" cy="211" r="7" fill="#145ea8"/>
<line x1="550" y1="219" x2="550" y2="370" class="laser"/>
<text x="590" y="244" class="small">лазерный профиль X-Z</text>

<line x1="280" y1="290" x2="280" y2="570" stroke="#607d8b" stroke-width="2" class="dash"/>
<line x1="720" y1="290" x2="720" y2="570" stroke="#607d8b" stroke-width="2" class="dash"/>
<line x1="280" y1="320" x2="520" y2="320" stroke="#546e7a" stroke-width="2" fill="none" marker-start="url(#dim-secondary)" marker-end="url(#dim-secondary)"/>
<line x1="580" y1="320" x2="720" y2="320" stroke="#546e7a" stroke-width="2" fill="none" marker-start="url(#dim-secondary)" marker-end="url(#dim-secondary)"/>
<rect x="390" y="252" width="220" height="53" rx="3" fill="white"/>
<text x="500" y="275" text-anchor="middle" class="label">700 мм</text>
<text x="500" y="299" text-anchor="middle" class="small">окно накопления профилей</text>

<rect x="470" y="370" width="160" height="200" fill="#fff3e0" stroke="#ef6c00" stroke-width="2"/>
<text x="550" y="458" text-anchor="middle" class="label">Товар</text>
<text x="550" y="484" text-anchor="middle" class="small">h ≤ 300 мм</text>

<line x1="665" y1="219" x2="805" y2="219" stroke="#90a4ae" stroke-width="1.5"/>
<line x1="720" y1="570" x2="805" y2="570" stroke="#90a4ae" stroke-width="1.5"/>
<line x1="805" y1="219" x2="805" y2="570" stroke="#546e7a" stroke-width="2" fill="none" marker-start="url(#dim-secondary)" marker-end="url(#dim-secondary)"/>
<text x="850" y="372" class="label">≈{layout.mount_height_above_belt_mm:.0f} мм</text>
<text x="850" y="397" class="small">расчётная высота</text>

<line x1="140" y1="370" x2="140" y2="570" stroke="#7b1fa2" stroke-width="4"/>
<circle cx="123" cy="550" r="12" fill="#7b1fa2"/><circle cx="157" cy="550" r="12" fill="#7b1fa2"/>
<text x="140" y="350" text-anchor="middle" class="label">SICK WLF4FI</text>
<line x1="140" y1="420" x2="280" y2="420" stroke="#546e7a" stroke-width="2" fill="none" marker-start="url(#dim-secondary)" marker-end="url(#dim-secondary)"/>
<text x="210" y="405" text-anchor="middle" class="small">250 мм</text>

<line x1="70" y1="570" x2="1030" y2="570" stroke="#263238" stroke-width="14"/>
<line x1="70" y1="588" x2="1030" y2="588" stroke="#90a4ae" stroke-width="8"/>
<text x="70" y="632" class="label">Конвейер, v = 1 м/с</text>
<path d="M300 626 H400" class="signal"/><text x="417" y="632" class="label">Y</text>

<circle cx="930" cy="620" r="28" fill="#e8f1fb" stroke="#145ea8" stroke-width="3"/>
<circle cx="930" cy="620" r="5" fill="#145ea8"/>
<text x="930" y="674" text-anchor="middle" class="label">SICK DFS60</text>
<text x="930" y="696" text-anchor="middle" class="small">мерное колесо</text>

<text x="40" y="700" class="small">700 мм — путь товара во время накопления профилей, а не оптический FOV.</text>
<text x="40" y="725" class="small">FOV {layout.target_top_fov_mm:.0f} мм относится к направлению X на высоте Z=300 мм.</text>
""",
        width=1100,
    )


def _top_view() -> str:
    layout = calculate_linear_fov_layout(GOCATOR_2880, target_top_fov_mm=680.0)
    return _svg(
        f"""
<defs>
  <marker id="dim-secondary" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,4 L8,0 L8,8 z" fill="#546e7a"/></marker>
</defs>
<text x="40" y="45" class="title">Измерительная станция — вид сверху (X-Y)</text>
<text x="40" y="78" class="small">Товар движется по Y; последовательные поперечные профили формируют 3D-облако.</text>

<text x="550" y="120" text-anchor="middle" class="label">FOV при Z=300 мм: {layout.target_top_fov_mm:.0f} мм</text>
<text x="550" y="145" text-anchor="middle" class="small">по {layout.lateral_margin_per_side_mm:.0f} мм запаса относительно ленты</text>
<line x1="210" y1="165" x2="890" y2="165" stroke="#546e7a" stroke-width="2" fill="none" marker-start="url(#dim-secondary)" marker-end="url(#dim-secondary)"/>

<rect x="250" y="175" width="600" height="400" fill="#eceff1"/>
<line x1="250" y1="175" x2="250" y2="575" stroke="#263238" stroke-width="4"/>
<line x1="850" y1="175" x2="850" y2="575" stroke="#263238" stroke-width="4"/>
<line x1="210" y1="175" x2="210" y2="575" stroke="#607d8b" stroke-width="2" class="dash"/>
<line x1="890" y1="175" x2="890" y2="575" stroke="#607d8b" stroke-width="2" class="dash"/>

<line x1="235" y1="230" x2="865" y2="230" stroke="#90a4ae" stroke-width="2" stroke-dasharray="14 6 3 6"/>
<line x1="235" y1="520" x2="865" y2="520" stroke="#90a4ae" stroke-width="2" stroke-dasharray="14 6 3 6"/>
<line x1="930" y1="230" x2="930" y2="520" stroke="#546e7a" stroke-width="2" fill="none" marker-start="url(#dim-secondary)" marker-end="url(#dim-secondary)"/>
<text x="952" y="365" class="label">700 мм</text>
<text x="952" y="390" class="small">окно накопления</text>

<line x1="210" y1="370" x2="890" y2="370" class="laser"/>
<g transform="rotate(24 550 370)">
  <rect x="485" y="320" width="130" height="100" fill="#fff3e0" stroke="#ef6c00" stroke-width="3"/>
</g>

<line x1="250" y1="600" x2="850" y2="600" stroke="#546e7a" stroke-width="2" fill="none" marker-start="url(#dim-secondary)" marker-end="url(#dim-secondary)"/>
<text x="550" y="632" text-anchor="middle" class="label">600 мм — ширина ленты</text>

<line x1="40" y1="660" x2="100" y2="660" class="laser"/>
<text x="115" y="666" class="small">один профиль X-Z</text>

<path d="M970 640 H1060" class="signal"/><text x="1072" y="646" class="label">X</text>
<path d="M970 640 V570" class="signal"/><text x="988" y="583" class="label">Y</text>

<text x="40" y="705" class="small">Товар движется по Y через неподвижную лазерную линию.</text>
<text x="40" y="728" class="small">Последовательные профили образуют 3D-облако.</text>
""",
        width=1100,
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


def _png_axes(*, width: int = 1200, height: int = 760, compact: bool = False):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 14,
            "figure.facecolor": "white",
        }
    )
    figure, axis = plt.subplots(figsize=(width / 100, height / 100), dpi=200)
    if compact:
        figure.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.98)
    axis.set_xlim(0, width)
    axis.set_ylim(0, height)
    axis.axis("off")
    return figure, axis


def _expanded_bbox(text, renderer, padding_px: float = 3.0) -> Bbox:
    box = text.get_window_extent(renderer=renderer)
    return Bbox.from_extents(
        box.x0 - padding_px,
        box.y0 - padding_px,
        box.x1 + padding_px,
        box.y1 + padding_px,
    )


def _check_text_layout(
    figure,
    axis,
    *,
    diagram: str,
    independent_pairs=(),
    vertical_clearances=(),
    forbidden_regions=(),
) -> None:
    """Fail generation when independently positioned annotations collide."""

    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    problems = []
    for description, first, second in independent_pairs:
        if _expanded_bbox(first, renderer).overlaps(_expanded_bbox(second, renderer)):
            problems.append(description)
    for description, text, x_data in vertical_clearances:
        box = _expanded_bbox(text, renderer, padding_px=6.0)
        x_display = axis.transData.transform((x_data, 0))[0]
        if box.x0 <= x_display <= box.x1:
            problems.append(description)
    for description, text, patch in forbidden_regions:
        if _expanded_bbox(text, renderer).overlaps(patch.get_window_extent(renderer=renderer)):
            problems.append(description)
    if problems:
        raise RuntimeError(f"{diagram} layout collisions: {', '.join(problems)}")


def _assert_text_inside_patch(figure, text, patch, *, padding_px: float, description: str) -> None:
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    outer = patch.get_window_extent(renderer=renderer)
    inner = text.get_window_extent(renderer=renderer)
    contained = (
        inner.x0 >= outer.x0 + padding_px
        and inner.x1 <= outer.x1 - padding_px
        and inner.y0 >= outer.y0 + padding_px
        and inner.y1 <= outer.y1 - padding_px
    )
    if not contained:
        raise RuntimeError(f"side geometry assertion failed: {description}")


def _save_png(figure, path: Path, *, tight: bool = False) -> None:
    extra = {"bbox_inches": "tight", "pad_inches": 0.12} if tight else {}
    figure.savefig(
        path,
        dpi=200,
        facecolor="white",
        metadata={"Software": "conveyor-dimensioning deterministic diagrams"},
        **extra,
    )
    plt.close(figure)


def _side_png(path: Path) -> None:
    layout = calculate_linear_fov_layout(GOCATOR_2880, target_top_fov_mm=680.0)
    figure, axis = _png_axes(width=1100, compact=True)
    title = axis.text(40, 715, "Измерительная станция — вид сбоку (Y-Z)", size=21, weight="bold")
    subtitle = axis.text(
        40,
        682,
        "Один фиксированный профиль X-Z; 3D-облако накапливается при движении товара по Y.",
        size=11,
        color="#455a64",
    )
    sensor_x, sensor_y = 455.0, 555.0
    sensor_width, sensor_height = 190.0, 84.0
    sensor_box = Rectangle(
        (sensor_x, sensor_y),
        sensor_width,
        sensor_height,
        facecolor="#e8f1fb",
        edgecolor="#145ea8",
        lw=2,
    )
    axis.add_patch(sensor_box)
    gocator = axis.text(550, 608, "Gocator 2880", ha="center", va="center", size=13, weight="bold")
    camera_text = axis.text(550, 580, "две камеры", ha="center", va="center", size=10.5, color="#455a64")
    camera_radius = 7.0
    camera_y = 538.0
    camera_centers = (515.0, 585.0)
    for camera_x in camera_centers:
        axis.add_patch(plt.Circle((camera_x, camera_y), camera_radius, facecolor="#145ea8", edgecolor="none", zorder=4))
    laser_x = 550.0
    laser_top_y = 530.0
    axis.plot([laser_x, laser_x], [laser_top_y, 390], color="#d32f2f", linewidth=2.3)
    laser_label = axis.text(
        590,
        512,
        "лазерный профиль X-Z",
        va="center",
        size=11,
        color="#455a64",
        zorder=5,
    )

    axis.plot([280, 280], [190, 470], color="#607d8b", ls="--", lw=1.4)
    axis.plot([720, 720], [190, 470], color="#607d8b", ls="--", lw=1.4)
    axis.annotate(
        "",
        xy=(520, 440),
        xytext=(280, 440),
        arrowprops={"arrowstyle": "<->", "color": "#546e7a", "lw": 1.6},
    )
    axis.annotate(
        "",
        xy=(720, 440),
        xytext=(580, 440),
        arrowprops={"arrowstyle": "<->", "color": "#546e7a", "lw": 1.6},
    )
    window_midpoint = (280.0 + 720.0) / 2.0
    window_label = axis.text(
        window_midpoint,
        474,
        "700 мм\nокно накопления профилей",
        ha="center",
        size=11,
        color="#455a64",
        linespacing=1.1,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 2.5},
    )

    product = Rectangle((470, 190), 160, 200, facecolor="#fff3e0", edgecolor="#ef6c00", lw=2)
    axis.add_patch(product)
    axis.text(550, 292, "Товар", ha="center", va="center", size=13)
    axis.text(550, 264, "h ≤ 300 мм", ha="center", va="center", size=10.5, color="#455a64")

    axis.plot([665, 805], [530, 530], color="#90a4ae", linewidth=1.3)
    axis.plot([720, 805], [190, 190], color="#90a4ae", linewidth=1.3)
    axis.annotate(
        "",
        xy=(805, 530),
        xytext=(805, 190),
        arrowprops={"arrowstyle": "<->", "color": "#546e7a", "lw": 1.7},
    )
    height_label = axis.text(850, 350, f"≈{layout.mount_height_above_belt_mm:.0f} мм\nрасчётная высота", size=11.5, linespacing=1.15)

    axis.plot([140, 140], [190, 390], color="#7b1fa2", linewidth=3)
    axis.scatter([123, 157], [210, 210], s=100, color="#7b1fa2", zorder=4)
    wlf_label = axis.text(140, 410, "SICK WLF4FI", ha="center", weight="bold")
    axis.annotate(
        "",
        xy=(280, 340),
        xytext=(140, 340),
        arrowprops={"arrowstyle": "<->", "color": "#546e7a", "lw": 1.5},
    )
    trigger_dimension = axis.text(210, 358, "250 мм", ha="center", size=10.5, color="#455a64")

    axis.plot([70, 1030], [190, 190], color="#263238", linewidth=10)
    axis.plot([70, 1030], [172, 172], color="#90a4ae", linewidth=5)
    conveyor_label = axis.text(70, 120, "Конвейер, v = 1 м/с", size=13)
    axis.add_patch(FancyArrowPatch((300, 116), (400, 116), arrowstyle="->", mutation_scale=18, color="#1565c0", lw=2))
    axis.text(417, 116, "Y", va="center", weight="bold")

    conveyor_bottom_y = 170.0
    wheel_radius = 28.0
    wheel_center_y = conveyor_bottom_y - wheel_radius
    wheel = plt.Circle((930, wheel_center_y), wheel_radius, facecolor="#e8f1fb", edgecolor="#145ea8", lw=2)
    axis.add_patch(wheel)
    axis.add_patch(plt.Circle((930, wheel_center_y), 5, facecolor="#145ea8"))
    dfs_label = axis.text(930, 78, "SICK DFS60\nмерное колесо", ha="center", va="center", size=10.5, linespacing=1.1)

    bottom_note = axis.text(
        40,
        46,
        f"700 мм — путь товара во время накопления профилей, а не оптический FOV.\nFOV {layout.target_top_fov_mm:.0f} мм относится к направлению X на высоте Z=300 мм.",
        size=10.5,
        color="#455a64",
        linespacing=1.15,
    )
    _check_text_layout(
        figure,
        axis,
        diagram="side",
        independent_pairs=(
            ("title/subtitle", title, subtitle),
            ("subtitle/Gocator", subtitle, gocator),
            ("700/917 labels", window_label, height_label),
            ("WLF4FI/250 mm", wlf_label, trigger_dimension),
            ("DFS60/conveyor", dfs_label, conveyor_label),
            ("DFS60/note", dfs_label, bottom_note),
        ),
        vertical_clearances=(("917 label/right window boundary", height_label, 720),),
        forbidden_regions=(
            ("laser label/product", laser_label, product),
            ("700 label/product", window_label, product),
            ("DFS60 label/wheel", dfs_label, wheel),
        ),
    )
    _assert_text_inside_patch(figure, gocator, sensor_box, padding_px=8.0, description="Gocator text outside sensor body")
    _assert_text_inside_patch(figure, camera_text, sensor_box, padding_px=8.0, description="camera text outside sensor body")
    if camera_y + camera_radius >= sensor_y:
        raise RuntimeError("side geometry assertion failed: camera marker touches sensor body")
    for camera_x in camera_centers:
        camera_vertical_range = (camera_y - camera_radius, camera_y + camera_radius)
        laser_vertical_range = (390.0, laser_top_y)
        vertical_overlap = max(camera_vertical_range[0], laser_vertical_range[0]) <= min(camera_vertical_range[1], laser_vertical_range[1])
        if abs(laser_x - camera_x) <= camera_radius and vertical_overlap:
            raise RuntimeError("side geometry assertion failed: laser intersects camera marker")
    wheel_bottom = wheel_center_y - wheel_radius
    wheel_top = wheel_center_y + wheel_radius
    belt_line_y_coordinates = (190.0, 172.0)
    if wheel_top > conveyor_bottom_y + 0.1:
        raise RuntimeError("side geometry assertion failed: wheel penetrates conveyor underside")
    if any(wheel_bottom < line_y < wheel_top for line_y in belt_line_y_coordinates):
        raise RuntimeError("side geometry assertion failed: conveyor line crosses wheel")
    if abs(window_label.get_position()[0] - window_midpoint) > 0.1:
        raise RuntimeError("side geometry assertion failed: 700 mm label is not centered")
    _check_text_layout(
        figure,
        axis,
        diagram="side dimensions",
        vertical_clearances=(
            ("laser label/height dimension", laser_label, 805),
            ("917 label/dimension arrow", height_label, 805),
            ("917 label/right window boundary", height_label, 720),
        ),
    )
    _save_png(figure, path, tight=True)


def _top_png(path: Path) -> None:
    layout = calculate_linear_fov_layout(GOCATOR_2880, target_top_fov_mm=680.0)
    figure, axis = _png_axes(width=1100, compact=True)
    title = axis.text(40, 715, "Измерительная станция — вид сверху (X-Y)", size=21, weight="bold")
    subtitle = axis.text(40, 682, "Товар движется по Y; последовательные поперечные профили формируют 3D-облако.", size=11, color="#455a64")

    fov_title = axis.text(550, 640, f"FOV при Z=300 мм: {layout.target_top_fov_mm:.0f} мм", ha="center", size=13)
    fov_subtitle = axis.text(550, 615, f"по {layout.lateral_margin_per_side_mm:.0f} мм запаса относительно ленты", ha="center", size=10.5, color="#455a64")
    axis.annotate("", xy=(890, 590), xytext=(210, 590), arrowprops={"arrowstyle": "<->", "color": "#546e7a", "lw": 1.7})

    axis.add_patch(Rectangle((250, 185), 600, 390, facecolor="#eceff1", edgecolor="none"))
    axis.plot([250, 250], [185, 575], color="#263238", linewidth=2.8)
    axis.plot([850, 850], [185, 575], color="#263238", linewidth=2.8)
    axis.plot([210, 210], [185, 575], color="#607d8b", ls="--", lw=1.5)
    axis.plot([890, 890], [185, 575], color="#607d8b", ls="--", lw=1.5)

    axis.plot([235, 865], [520, 520], color="#90a4ae", ls=(0, (7, 3, 1.5, 3)), lw=1.5)
    axis.plot([235, 865], [230, 230], color="#90a4ae", ls=(0, (7, 3, 1.5, 3)), lw=1.5)
    axis.annotate(
        "",
        xy=(930, 520),
        xytext=(930, 230),
        arrowprops={"arrowstyle": "<->", "color": "#546e7a", "lw": 1.7},
    )
    window_label = axis.text(952, 376, "700 мм\nокно накопления", va="center", size=11, linespacing=1.15)

    axis.plot([210, 890], [370, 370], color="#d32f2f", linewidth=2.5)
    product = Rectangle((485, 320), 130, 100, angle=24, rotation_point="center", facecolor="#fff3e0", edgecolor="#ef6c00", lw=2)
    axis.add_patch(product)

    axis.annotate(
        "",
        xy=(850, 155),
        xytext=(250, 155),
        arrowprops={"arrowstyle": "<->", "color": "#546e7a", "lw": 1.7},
    )
    belt_label = axis.text(550, 122, "600 мм — ширина ленты", ha="center", size=13)

    axis.plot([40, 100], [94, 94], color="#d32f2f", linewidth=2.5)
    legend = axis.text(115, 94, "один профиль X-Z", va="center", size=10.5, color="#455a64")

    axis.add_patch(FancyArrowPatch((970, 110), (1060, 110), arrowstyle="->", mutation_scale=18, color="#1565c0", lw=2))
    axis.add_patch(FancyArrowPatch((970, 110), (970, 180), arrowstyle="->", mutation_scale=18, color="#1565c0", lw=2))
    axis_x = axis.text(1072, 110, "X", va="center", size=13)
    axis_y = axis.text(988, 180, "Y", va="center", size=13)

    bottom_note = axis.text(
        40,
        46,
        "Товар движется по Y через неподвижную лазерную линию.\nПоследовательные профили образуют 3D-облако.",
        size=10.5,
        color="#455a64",
        linespacing=1.15,
    )
    product_forbidden_texts = (
        fov_title,
        fov_subtitle,
        legend,
        window_label,
        belt_label,
        axis_x,
        axis_y,
        bottom_note,
    )
    _check_text_layout(
        figure,
        axis,
        diagram="top",
        independent_pairs=(
            ("title/subtitle", title, subtitle),
            ("FOV title/subtitle", fov_title, fov_subtitle),
            ("FOV/legend", fov_subtitle, legend),
            ("700/X axis", window_label, axis_x),
            ("700/Y axis", window_label, axis_y),
            ("X axis/note", axis_x, bottom_note),
            ("Y axis/note", axis_y, bottom_note),
        ),
        forbidden_regions=tuple(
            (f"annotation/product #{index}", text, product)
            for index, text in enumerate(product_forbidden_texts, start=1)
        ),
    )
    _save_png(figure, path, tight=True)


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
