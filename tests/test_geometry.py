import numpy as np

from conveyor_dimensioning.geometry import (
    axis_aligned_box,
    minimum_volume_box,
    normalize_dimensions,
    pca_box,
)
from conveyor_dimensioning.simulation import sample_box_surface


def test_minimum_box_recovers_rotated_box_dimensions() -> None:
    points = sample_box_surface(
        (40.0, 20.0, 10.0), points_per_face=80, rotation_deg=(13.0, 7.0, 31.0), seed=2
    )

    measured = minimum_volume_box(points)

    assert np.allclose(normalize_dimensions(measured.extents_mm), [40.0, 20.0, 10.0], atol=0.15)
    assert np.isclose(measured.volume_mm3, 8000.0, rtol=0.01)


def test_axis_aligned_box_overestimates_yaw_rotated_box() -> None:
    points = sample_box_surface(
        (40.0, 20.0, 10.0), points_per_face=40, rotation_deg=(0.0, 0.0, 35.0), seed=3
    )

    aabb = axis_aligned_box(points)
    minimal = minimum_volume_box(points)

    assert aabb.volume_mm3 > minimal.volume_mm3 * 1.5


def test_minimum_box_is_smaller_than_pca_box_for_l_prism() -> None:
    footprint = np.array([[0, 0], [40, 0], [40, 10], [10, 10], [10, 40], [0, 40]])
    points = np.vstack(
        [
            np.column_stack([footprint, np.zeros(len(footprint))]),
            np.column_stack([footprint, np.full(len(footprint), 10.0)]),
        ]
    ).astype(float)

    minimal = minimum_volume_box(points)
    pca = pca_box(points)

    assert minimal.volume_mm3 <= 16000.0 + 1e-6
    assert minimal.volume_mm3 < pca.volume_mm3 * 0.9


def test_normalize_dimensions_is_permutation_invariant() -> None:
    expected = np.array([400.0, 300.0, 10.0])

    assert np.array_equal(normalize_dimensions([10.0, 400.0, 300.0]), expected)
    assert np.array_equal(normalize_dimensions([300.0, 10.0, 400.0]), expected)
