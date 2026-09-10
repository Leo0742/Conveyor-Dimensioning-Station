"""End-to-end geometry measurement, aggregation and tolerance evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from conveyor_dimensioning.config import MeasurementConfig
from conveyor_dimensioning.geometry import (
    dominant_top_plane_box,
    minimum_volume_box,
    normalize_dimensions,
)
from conveyor_dimensioning.hardware import GOCATOR_2880, fov_width_at_height_mm
from conveyor_dimensioning.preprocessing import (
    connected_components,
    estimate_cluster_radius,
    fit_conveyor_plane_ransac,
    merge_nearby_components,
    remove_plane,
    statistical_filter,
)
from conveyor_dimensioning.types import DimensionResult

MAX_TRUSTED_OBB_DISAGREEMENT_RATIO = 0.25


@dataclass(frozen=True)
class MeasurementEvaluation:
    """Errors relative to known synthetic ground truth."""

    absolute_error_mm: np.ndarray
    relative_error_percent: np.ndarray
    tolerance_mm: np.ndarray
    axis_passed: np.ndarray

    @property
    def passed(self) -> bool:
        return bool(np.all(self.axis_passed))


def dimension_tolerance_mm(dimensions_mm: Sequence[float]) -> np.ndarray:
    """Return the assignment tolerance ±max(5%, 5 mm) per sorted axis."""
    dimensions = normalize_dimensions(np.asarray(dimensions_mm, dtype=float))
    return np.maximum(dimensions * 0.05, 5.0)


def evaluate_result(
    result: DimensionResult, ground_truth_mm: Sequence[float]
) -> MeasurementEvaluation:
    """Compare a result with known dimensions without hiding invalid statuses."""
    truth = normalize_dimensions(np.asarray(ground_truth_mm, dtype=float))
    measured = np.array([result.length_mm, result.width_mm, result.height_mm])
    absolute = np.abs(measured - truth)
    relative = np.divide(absolute * 100.0, truth, out=np.full(3, np.inf), where=truth > 0)
    tolerance = dimension_tolerance_mm(truth)
    passed = (absolute <= tolerance) & (result.status == "ok")
    return MeasurementEvaluation(absolute, relative, tolerance, passed)


def estimate_support_contact_completion(
    points: np.ndarray, plane: np.ndarray, *, fraction: float = 0.01
) -> np.ndarray:
    """Apply a box-friendly support-plane completion heuristic to the lowest band.

    The projected points are an explicit geometric assumption, not observed depth and
    not a reconstruction of an arbitrary hidden underside.
    """
    normal = plane[:3] / np.linalg.norm(plane[:3])
    signed = (points @ plane[:3] + plane[3]) / np.linalg.norm(plane[:3])
    cutoff = np.quantile(signed, fraction)
    contact = points[signed <= cutoff]
    contact_distance = signed[signed <= cutoff]
    projected = contact - contact_distance[:, None] * normal
    return np.vstack([points, projected])


def reaches_optical_fov_boundary(
    points_mm: np.ndarray,
    *,
    guard_samples: float,
    minimum_points: int,
) -> bool:
    """Detect observed samples at the selected 2880 preliminary FOV boundary."""
    points = np.asarray(points_mm, dtype=float)
    if len(points) < minimum_points:
        return False
    widths = np.array(
        [fov_width_at_height_mm(max(0.0, float(height))) for height in points[:, 2]]
    )
    pitch = widths / GOCATOR_2880.points_per_profile
    margin = widths / 2 - np.abs(points[:, 0])
    return int(np.count_nonzero(margin <= guard_samples * pitch)) >= minimum_points


def add_support_contact_points(
    points: np.ndarray, plane: np.ndarray, *, fraction: float = 0.01
) -> np.ndarray:
    """Backward-compatible alias for :func:`estimate_support_contact_completion`."""
    return estimate_support_contact_completion(points, plane, fraction=fraction)


def measure_scene(
    points_mm: np.ndarray,
    config: MeasurementConfig | None = None,
    *,
    seed: int = 0,
) -> DimensionResult:
    """Measure one scene containing a dominant conveyor plane and one product."""
    settings = config or MeasurementConfig()
    try:
        plane, _ = fit_conveyor_plane_ransac(
            points_mm,
            threshold_mm=settings.plane_distance_threshold_mm,
            iterations=settings.ransac_iterations,
            seed=seed,
        )
    except ValueError:
        return DimensionResult.from_extents(
            np.zeros(3), confidence=0.0, status="calibration_error", point_count=0
        )
    object_points = remove_plane(
        points_mm,
        plane,
        min_height_mm=settings.object_min_height_mm,
    )
    object_points = statistical_filter(
        object_points,
        neighbors=settings.outlier_neighbors,
        std_ratio=settings.outlier_std_ratio,
    )
    radius_mm = settings.cluster_radius_mm or estimate_cluster_radius(
        object_points,
        multiplier=settings.cluster_radius_multiplier,
        minimum_mm=settings.cluster_radius_min_mm,
        maximum_mm=settings.cluster_radius_max_mm,
    )
    components = connected_components(object_points, radius_mm=radius_mm)
    candidates = [
        component for component in components if len(component) >= settings.cluster_min_points
    ]
    candidates = merge_nearby_components(
        candidates, maximum_gap_mm=settings.fragment_merge_gap_mm
    )
    if not candidates:
        return DimensionResult.from_extents(
            np.zeros(3),
            confidence=0.0,
            status="insufficient_depth_data",
            point_count=0,
        )
    candidates.sort(key=len, reverse=True)
    significant_limit = max(
        settings.cluster_min_points,
        int(np.ceil(len(candidates[0]) * settings.significant_cluster_ratio)),
    )
    significant = [component for component in candidates if len(component) >= significant_limit]
    if len(significant) > 1:
        return DimensionResult.from_extents(
            np.zeros(3),
            confidence=0.0,
            status="object_overlap",
            point_count=sum(map(len, significant)),
        )
    object_points = candidates[0]
    if len(object_points) < settings.min_object_points:
        return DimensionResult.from_extents(
            np.zeros(3),
            confidence=0.0,
            status="insufficient_depth_data",
            point_count=len(object_points),
        )
    if reaches_optical_fov_boundary(
        object_points,
        guard_samples=settings.optical_boundary_guard_samples,
        minimum_points=settings.optical_boundary_min_points,
    ):
        return DimensionResult.from_extents(
            np.zeros(3),
            confidence=0.0,
            status="measurement_out_of_range",
            point_count=len(object_points),
        )

    # The calibrated belt plane supplies a support constraint. Projecting only the
    # observed lowest band is an explicit box-oriented completion assumption.
    augmented = estimate_support_contact_completion(object_points, plane)
    box = dominant_top_plane_box(augmented, seed=seed)
    minimal_box = minimum_volume_box(augmented)
    dimensions = normalize_dimensions(box.extents_mm)
    minimal_dimensions = normalize_dimensions(minimal_box.extents_mm)
    obb_disagreement_ratio = float(
        np.max(np.abs(dimensions - minimal_dimensions) / np.maximum(dimensions, 1.0))
    )
    point_quality = float(min(0.99, 0.65 + 0.08 * np.log10(len(object_points))))
    obb_agreement_quality = float(max(0.0, 1.0 - obb_disagreement_ratio))
    confidence = min(point_quality, obb_agreement_quality)
    maximum = normalize_dimensions(np.asarray(settings.maximum_dimensions_mm, dtype=float))
    if np.any(dimensions > maximum + dimension_tolerance_mm(maximum)):
        return DimensionResult.from_extents(
            np.zeros(3),
            confidence=0.0,
            status="measurement_out_of_range",
            point_count=len(object_points),
        )
    trusted = (
        len(object_points) >= settings.min_confident_points
        and obb_disagreement_ratio <= MAX_TRUSTED_OBB_DISAGREEMENT_RATIO
    )
    status = "ok" if trusted else "low_confidence"
    return DimensionResult.from_extents(
        box.extents_mm,
        confidence=confidence,
        status=status,
        point_count=len(object_points),
    )


def aggregate_results(results: Sequence[DimensionResult]) -> DimensionResult:
    """Median-aggregate valid frames and retain their combined evidence count."""
    valid = [result for result in results if result.status == "ok"]
    if not valid:
        return DimensionResult.from_extents(
            np.zeros(3), confidence=0.0, status="insufficient_depth_data", point_count=0
        )
    dimensions = np.array(
        [[result.length_mm, result.width_mm, result.height_mm] for result in valid]
    )
    return DimensionResult(
        length_mm=float(np.median(dimensions[:, 0])),
        width_mm=float(np.median(dimensions[:, 1])),
        height_mm=float(np.median(dimensions[:, 2])),
        confidence=float(np.median([result.confidence for result in valid])),
        status="ok",
        point_count=sum(result.point_count for result in valid),
    )
