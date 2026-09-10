"""Write AABB/PCA/custom/Open3D volume comparisons for representative shapes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from conveyor_dimensioning.geometry import (
    axis_aligned_box,
    minimum_volume_box,
    normalize_dimensions,
    open3d_reference_box,
    pca_box,
)
from conveyor_dimensioning.simulation import (
    rotation_matrix_xyz,
    sample_box_surface,
    sample_line_profiler_shape,
)


def _convex_irregular_fixture() -> np.ndarray:
    """Return a fixed, non-symmetric convex 3D fixture for offline comparison."""
    points = np.array(
        [
            [-48.0, -27.0, 0.0],
            [51.0, -22.0, 3.0],
            [43.0, 31.0, 1.0],
            [-38.0, 35.0, 4.0],
            [-31.0, -19.0, 37.0],
            [35.0, -25.0, 42.0],
            [47.0, 18.0, 34.0],
            [4.0, 39.0, 46.0],
            [-44.0, 17.0, 31.0],
        ]
    )
    return points @ rotation_matrix_xyz((7.0, -4.0, 29.0)).T


def _fixture(shape: str, index: int) -> np.ndarray:
    if shape == "box":
        return sample_box_surface(
            (100.0, 65.0, 35.0), points_per_face=180, seed=700 + index
        )
    if shape == "rotated_box":
        return sample_box_surface(
            (100.0, 65.0, 35.0),
            points_per_face=180,
            rotation_deg=(5.0, 3.0, 31.0),
            seed=700 + index,
        )
    if shape == "convex_irregular":
        return _convex_irregular_fixture()
    return sample_line_profiler_shape(
        shape,
        (100.0, 65.0, 35.0),
        rotation_deg=(3.0, 2.0, 31.0),
        edge_shadow=0.0,
        dropout=0.0,
        noise_std_mm=0.0,
        seed=700 + index,
    ).points_mm


def compare(output_path: str | Path) -> list[dict[str, object]]:
    rows = []
    shapes = ("box", "rotated_box", "l_prism", "cylinder", "composite", "convex_irregular")
    for index, shape in enumerate(shapes):
        points = _fixture(shape, index)
        reference = open3d_reference_box(points)
        aabb = axis_aligned_box(points)
        pca = pca_box(points)
        custom = minimum_volume_box(points)
        reference_volume = reference.box.volume_mm3
        custom_dimensions = normalize_dimensions(custom.extents_mm)
        reference_dimensions = normalize_dimensions(reference.box.extents_mm)
        difference = custom_dimensions - reference_dimensions
        if reference.method == "MINIMAL_JYLANKI":
            availability = "MINIMAL_JYLANKI available in frozen runtime"
        else:
            availability = (
                f"MINIMAL_JYLANKI unavailable in frozen Open3D "
                f"{reference.open3d_version} runtime; using "
                "create_from_points_minimal (minimal-approx)"
            )
        rows.append(
            {
                "shape": shape,
                "aabb_volume_mm3": aabb.volume_mm3,
                "pca_volume_mm3": pca.volume_mm3,
                "custom_volume_mm3": custom.volume_mm3,
                "reference_volume_mm3": reference_volume,
                "aabb_dimensions_mm": normalize_dimensions(aabb.extents_mm).tolist(),
                "pca_dimensions_mm": normalize_dimensions(pca.extents_mm).tolist(),
                "custom_dimensions_mm": custom_dimensions.tolist(),
                "reference_dimensions_mm": reference_dimensions.tolist(),
                "custom_reference_dimension_difference_mm": difference.tolist(),
                "custom_reference_dimension_abs_diff_mm": np.abs(difference).tolist(),
                "custom_gap_percent": (custom.volume_mm3 / reference_volume - 1.0) * 100.0,
                "reference_method": reference.method,
                "reference_availability": availability,
                "open3d_version": reference.open3d_version,
            }
        )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="assets/demo/obb_comparison.json")
    args = parser.parse_args()
    compare(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
