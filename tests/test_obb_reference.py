import pytest

from conveyor_dimensioning.geometry import (
    axis_aligned_box,
    minimum_volume_box,
    open3d_reference_box,
    pca_box,
)
from conveyor_dimensioning.simulation import sample_box_surface, sample_line_profiler_shape
from scripts.compare_obb import compare

open3d = pytest.importorskip("open3d")


@pytest.mark.parametrize("shape", ["box", "l_prism", "cylinder", "composite"])
def test_custom_obb_is_compared_with_explicit_open3d_reference(shape: str) -> None:
    if shape == "box":
        points = sample_box_surface(
            (80.0, 55.0, 30.0), points_per_face=120, rotation_deg=(5.0, 3.0, 29.0), seed=5
        )
    else:
        points = sample_line_profiler_shape(
            shape,
            (80.0, 55.0, 30.0),
            rotation_deg=(3.0, 2.0, 29.0),
            edge_shadow=0.0,
            dropout=0.0,
            noise_std_mm=0.0,
            seed=5,
        ).points_mm

    aabb = axis_aligned_box(points)
    pca = pca_box(points)
    custom = minimum_volume_box(points)
    reference = open3d_reference_box(points)

    assert reference.method in {
        "MINIMAL_JYLANKI",
        "create_from_points_minimal (minimal-approx)",
    }
    # Stable 0.19 exposes another face-frame approximation, not Jylänki. Its
    # implementation can differ slightly from ours in either direction, so the
    # numerical allowance is explicit and reported. A real Jylänki result gets a
    # tight one-sided minimum-volume check.
    tolerance = 1e-5 if reference.method == "MINIMAL_JYLANKI" else reference.box.volume_mm3 * 0.01
    assert aabb.volume_mm3 >= reference.box.volume_mm3 - tolerance
    assert pca.volume_mm3 >= reference.box.volume_mm3 - tolerance
    assert custom.volume_mm3 >= reference.box.volume_mm3 - tolerance


def test_obb_comparison_has_six_shapes_dimensions_and_method_evidence(tmp_path) -> None:
    rows = compare(tmp_path / "obb.json")

    assert {row["shape"] for row in rows} == {
        "box",
        "rotated_box",
        "l_prism",
        "cylinder",
        "composite",
        "convex_irregular",
    }
    for row in rows:
        assert set(row) >= {
            "aabb_dimensions_mm",
            "pca_dimensions_mm",
            "custom_dimensions_mm",
            "reference_dimensions_mm",
            "custom_reference_dimension_difference_mm",
            "custom_reference_dimension_abs_diff_mm",
            "reference_method",
            "reference_availability",
            "open3d_version",
        }
        assert len(row["custom_reference_dimension_abs_diff_mm"]) == 3
        assert row["reference_method"] in {
            "MINIMAL_JYLANKI",
            "create_from_points_minimal (minimal-approx)",
        }
