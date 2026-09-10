import numpy as np

from conveyor_dimensioning.config import MeasurementConfig
from conveyor_dimensioning.measurement import (
    aggregate_results,
    dimension_tolerance_mm,
    evaluate_result,
    measure_scene,
)
from conveyor_dimensioning.monte_carlo import DEVELOPMENT_SEED, generate_monte_carlo_cases
from conveyor_dimensioning.simulation import (
    LineProfilerConfig,
    make_scene,
    sample_box_surface,
    sample_line_profiler_box,
    sample_line_profiler_shape,
)
from conveyor_dimensioning.types import DimensionResult


def test_dimension_tolerance_uses_larger_of_five_percent_and_five_mm() -> None:
    assert np.array_equal(dimension_tolerance_mm([200.0, 100.0, 10.0]), [10.0, 5.0, 5.0])


def test_tolerance_evaluation_reports_each_axis() -> None:
    result = DimensionResult.from_extents(
        np.array([208.0, 96.0, 14.0]), confidence=0.9, status="ok", point_count=200
    )

    evaluation = evaluate_result(result, [200.0, 100.0, 10.0])

    assert np.array_equal(evaluation.absolute_error_mm, [8.0, 4.0, 4.0])
    assert np.all(evaluation.axis_passed)
    assert evaluation.passed


def test_measure_scene_handles_small_rotated_object_near_limit() -> None:
    product = sample_box_surface(
        (10.0, 10.0, 10.0),
        points_per_face=180,
        rotation_deg=(0.0, 0.0, 27.0),
        noise_std_mm=0.12,
        dropout=0.1,
        seed=11,
    )
    scene = make_scene(product, plane_point_count=1800, plane_noise_std_mm=0.1, seed=12)

    result = measure_scene(scene, MeasurementConfig(cluster_radius_mm=2.0), seed=13)

    assert result.status == "ok"
    assert evaluate_result(result, [10.0, 10.0, 10.0]).passed


def test_measure_scene_handles_large_noisy_object() -> None:
    product = sample_box_surface(
        (400.0, 300.0, 300.0),
        points_per_face=900,
        rotation_deg=(0.0, 0.0, 13.0),
        noise_std_mm=0.35,
        dropout=0.2,
        seed=21,
    )
    scene = make_scene(product, plane_point_count=3500, plane_noise_std_mm=0.15, seed=22)
    config = MeasurementConfig(cluster_radius_mm=24.0, cluster_min_points=12)

    result = measure_scene(scene, config, seed=23)

    assert result.status == "ok"
    assert evaluate_result(result, [400.0, 300.0, 300.0]).passed


def test_measure_scene_does_not_expand_a_box_resting_at_a_3d_tilt() -> None:
    product = sample_box_surface(
        (90.0, 55.0, 35.0),
        points_per_face=350,
        rotation_deg=(8.0, 5.0, 21.0),
        seed=31,
    )
    scene = make_scene(product, plane_point_count=1800, plane_noise_std_mm=0.1, seed=32)

    result = measure_scene(scene, MeasurementConfig(cluster_radius_mm=6.0), seed=33)

    assert evaluate_result(result, [90.0, 55.0, 35.0]).passed


def test_measure_scene_uses_dominant_top_frame_for_tilted_profile() -> None:
    """Development-seed fixture where unconstrained minimum volume selects a false frame."""
    product = sample_line_profiler_shape(
        "box",
        (252.2372346670138, 251.66219143235637, 120.50850207888323),
        config=LineProfilerConfig(
            profile_rate_hz=1000.0,
            missing_profile_probability=0.0015367689323179425,
        ),
        center_xy_mm=(21.498079349253214, 0.0),
        rotation_deg=(-4.3963559352667, 0.3574278082093081, 78.01916040183765),
        visible_completeness=0.8910224341094385,
        edge_shadow=0.14974194122879908,
        noise_std_mm=0.0639407105659346,
        dropout=0.13148729913684715,
        seed=1337 * 1009 + 25,
    )
    scene = make_scene(
        product.points_mm,
        plane_point_count=1200,
        plane_noise_std_mm=0.12,
        seed=1337 * 1013 + 25,
    )

    result = measure_scene(scene, seed=1337 + 25)

    assert result.status == "ok"
    assert evaluate_result(result, product.reference_dimensions_mm).passed


def test_measure_scene_marks_large_obb_frame_disagreement_low_confidence() -> None:
    case = generate_monte_carlo_cases(38, seed=DEVELOPMENT_SEED)[37]

    result = measure_scene(case.points_mm, seed=DEVELOPMENT_SEED + 37)

    assert result.status == "low_confidence"
    assert result.confidence < 0.75


def test_aggregate_results_uses_median_and_ignores_invalid_frames() -> None:
    results = [
        DimensionResult(
            length_mm=101, width_mm=51, height_mm=21,
            confidence=0.9, status="ok", point_count=100,
        ),
        DimensionResult(
            length_mm=99, width_mm=49, height_mm=19,
            confidence=0.8, status="ok", point_count=90,
        ),
        DimensionResult(
            length_mm=500, width_mm=1, height_mm=1,
            confidence=0.0, status="insufficient_depth_data", point_count=2,
        ),
    ]

    combined = aggregate_results(results)

    assert (combined.length_mm, combined.width_mm, combined.height_mm) == (100.0, 50.0, 20.0)
    assert combined.status == "ok"
    assert combined.point_count == 190


def test_two_meaningful_products_return_object_overlap() -> None:
    left = sample_line_profiler_box(
        (60.0, 40.0, 30.0), center_xy_mm=(-90.0, 0.0), seed=50
    )
    right = sample_line_profiler_box(
        (55.0, 35.0, 25.0), center_xy_mm=(90.0, 0.0), seed=51
    )
    scene = make_scene(
        np.vstack([left.points_mm, right.points_mm]), plane_point_count=1400, seed=52
    )

    result = measure_scene(scene, seed=53)

    assert result.status == "object_overlap"
    assert (result.length_mm, result.width_mm, result.height_mm) == (0.0, 0.0, 0.0)


def test_tiny_noise_cluster_does_not_trigger_overlap() -> None:
    product = sample_line_profiler_box(
        (70.0, 45.0, 25.0), edge_shadow=0.0, seed=54
    )
    rng = np.random.default_rng(55)
    tiny = rng.normal([180.0, 0.0, 12.0], 0.3, (6, 3))
    scene = make_scene(np.vstack([product.points_mm, tiny]), plane_point_count=1200, seed=56)

    result = measure_scene(scene, seed=57)

    assert result.status == "ok"


def test_small_dropout_gap_is_reconnected_as_one_object() -> None:
    product = sample_line_profiler_box(
        (80.0, 50.0, 30.0), edge_shadow=0.0, seed=58
    )
    fragments = product.points_mm[np.abs(product.points_mm[:, 0]) > 3.0]
    scene = make_scene(fragments, plane_point_count=1400, seed=59)

    result = measure_scene(scene, seed=60)

    assert result.status == "ok"
    assert evaluate_result(result, product.reference_dimensions_mm).passed


def test_measured_extent_beyond_assignment_range_is_rejected() -> None:
    product = sample_box_surface(
        (450.0, 100.0, 40.0), points_per_face=700, seed=61
    )
    scene = make_scene(product, plane_point_count=1600, seed=62)

    result = measure_scene(scene, seed=63)

    assert result.status == "measurement_out_of_range"


def test_sparse_but_measurable_object_returns_low_confidence() -> None:
    product = sample_line_profiler_box(
        (70.0, 45.0, 25.0),
        config=LineProfilerConfig(
            profile_rate_hz=380.0,
            missing_profile_probability=0.60,
        ),
        visible_completeness=0.15,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=64,
    )
    scene = make_scene(product.points_mm, plane_point_count=1000, seed=65)

    result = measure_scene(scene, seed=66)

    assert result.status == "low_confidence"


def test_observed_optical_boundary_returns_out_of_range_without_dimensions() -> None:
    product = sample_line_profiler_box(
        (200.0, 100.0, 300.0),
        center_xy_mm=(420.0, 0.0),
        visible_completeness=1.0,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=67,
    )
    scene = make_scene(product.points_mm, plane_point_count=1800, seed=68)

    result = measure_scene(scene, seed=69)

    assert result.status == "measurement_out_of_range"
    assert (result.length_mm, result.width_mm, result.height_mm) == (0.0, 0.0, 0.0)
