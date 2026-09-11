"""Static and animated visualizations generated from prototype data."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

from conveyor_dimensioning.geometry import BoundingBox3D
from conveyor_dimensioning.types import PointCloudFrame

BOX_EDGES = (
    (0, 1),
    (0, 2),
    (0, 4),
    (1, 3),
    (1, 5),
    (2, 3),
    (2, 6),
    (3, 7),
    (4, 5),
    (4, 6),
    (5, 7),
    (6, 7),
)


def plot_measurement(
    scene_points_mm: np.ndarray,
    object_points_mm: np.ndarray,
    box: BoundingBox3D,
    output_path: str | Path,
) -> None:
    """Render the conveyor, observed product points and measured OBB."""
    scene = np.asarray(scene_points_mm)
    product = np.asarray(object_points_mm)
    stride = max(1, len(scene) // 1800)

    figure = plt.figure(figsize=(10, 7), dpi=150)
    axis = figure.add_subplot(111, projection="3d")
    axis.scatter(
        scene[::stride, 0],
        scene[::stride, 1],
        scene[::stride, 2],
        s=1.5,
        c="#a6adb4",
        alpha=0.28,
        label="плоскость конвейера",
    )
    axis.scatter(
        product[:, 0],
        product[:, 1],
        product[:, 2],
        s=3,
        c="#1565c0",
        alpha=0.7,
        label="товар",
    )

    corners = box.corners_mm
    for first, second in BOX_EDGES:
        edge = corners[[first, second]]
        axis.plot(edge[:, 0], edge[:, 1], edge[:, 2], color="#d32f2f", linewidth=2)

    dimensions = np.sort(box.extents_mm)[::-1]
    axis.set_title(
        f"Результат симуляции: "
        f"{dimensions[0]:.1f} × {dimensions[1]:.1f} × {dimensions[2]:.1f} мм",
        pad=18,
    )
    axis.set_xlabel("X поперёк ленты, мм", labelpad=10)
    axis.set_ylabel("Y вдоль ленты, мм", labelpad=14)
    axis.set_zlabel("Z, мм", labelpad=8)
    axis.legend(loc="upper left", borderpad=0.8, handletextpad=0.8)
    axis.view_init(elev=27, azim=-58)
    axis.set_box_aspect((1.2, 1.4, 0.65))

    figure.subplots_adjust(left=0.03, right=0.96, bottom=0.07, top=0.90)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, bbox_inches="tight")
    plt.close(figure)


def save_motion_gif(
    frames: list[PointCloudFrame],
    output_path: str | Path,
    *,
    conveyor_width_mm: float = 600.0,
    zone_length_mm: float = 700.0,
) -> None:
    """Render a compact top-view animation from simulated frame coordinates."""
    images: list[Image.Image] = []
    width, height = 720, 460
    for frame in frames:
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        margin = 55
        draw.rectangle(
            (margin, 35, width - margin, height - 45),
            fill="#eceff1",
            outline="#455a64",
            width=3,
        )
        for arrow_x in range(margin + 80, width - margin, 120):
            draw.line(
                (arrow_x, height - 25, arrow_x + 45, height - 25),
                fill="#455a64",
                width=3,
            )
            arrow = [
                (arrow_x + 45, height - 25),
                (arrow_x + 34, height - 32),
                (arrow_x + 34, height - 18),
            ]
            draw.polygon(arrow, fill="#455a64")

        points = frame.points_mm
        x = (
            margin
            + (points[:, 0] + conveyor_width_mm / 2)
            / conveyor_width_mm
            * (width - 2 * margin)
        )
        y = 35 + (points[:, 1] + zone_length_mm / 2) / zone_length_mm * (height - 80)
        for px, py in zip(x[::3], y[::3], strict=False):
            if margin <= px <= width - margin and 35 <= py <= height - 45:
                draw.ellipse((px - 1, py - 1, px + 1, py + 1), fill="#1565c0")

        label = f"SIMULATED | encoder={frame.encoder_mm:.1f} mm | v=1.0 m/s"
        draw.text((margin, 8), label, fill="#263238")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        images.append(Image.open(buffer).copy())

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=120,
        loop=0,
    )


def plot_multiframe_summary(records, aggregate, output_path: str | Path) -> None:
    """Plot per-window dimensions and the median result sent to WMS."""
    valid = [record for record in records if record.result.status == "ok"]
    figure, axis = plt.subplots(figsize=(9, 5), dpi=150)
    for field, label, color in (
        ("length_mm", "L", "#1565c0"),
        ("width_mm", "W", "#2e7d32"),
        ("height_mm", "H", "#d84315"),
    ):
        axis.plot(
            [record.encoder_mm for record in valid],
            [getattr(record.result, field) for record in valid],
            "o-",
            label=f"окно: {label}",
            color=color,
        )
        axis.axhline(
            getattr(aggregate, field),
            linestyle="--",
            color=color,
            alpha=0.65,
        )

    axis.set_title("Синтетическая проверка: валидные окна и медиана")
    axis.set_xlabel("Позиция энкодера, мм")
    axis.set_ylabel("Размер, мм")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, bbox_inches="tight")
    plt.close(figure)
