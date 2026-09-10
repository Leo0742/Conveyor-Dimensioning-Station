import numpy as np
import pytest

import conveyor_dimensioning.simulation as simulation
from conveyor_dimensioning.simulation import (
    SENSOR_LIKE_EVIDENCE,
    LineProfilerConfig,
    make_scene,
    sample_box_surface,
    sample_line_profiler_box,
    sample_line_profiler_shape,
    simulate_sequence,
)


def test_sample_box_surface_preserves_ground_truth_extents() -> None:
    points = sample_box_surface((40.0, 20.0, 10.0), points_per_face=30, seed=7)

    assert np.allclose(np.ptp(points, axis=0), [40.0, 20.0, 10.0], atol=1e-9)
    assert points[:, 2].min() == 0.0


def test_sample_box_surface_is_reproducible_with_noise_and_dropout() -> None:
    first = sample_box_surface(
        (40.0, 20.0, 10.0), points_per_face=30, noise_std_mm=0.2, dropout=0.15, seed=17
    )
    second = sample_box_surface(
        (40.0, 20.0, 10.0), points_per_face=30, noise_std_mm=0.2, dropout=0.15, seed=17
    )

    assert np.array_equal(first, second)
    assert len(first) < 6 * 30 + 8


def test_make_scene_adds_conveyor_plane_below_product() -> None:
    product = sample_box_surface((30.0, 20.0, 10.0), points_per_face=20, seed=2)
    scene = make_scene(product, plane_point_count=200, plane_noise_std_mm=0.0, seed=3)

    assert len(scene) == len(product) + 200
    assert np.count_nonzero(scene[:, 2] == 0.0) >= 200
    assert scene[:, 0].min() >= -300.0
    assert scene[:, 0].max() <= 300.0


def test_simulation_moves_object_according_to_speed_and_frame_rate() -> None:
    product = sample_box_surface((30.0, 20.0, 10.0), points_per_face=10, seed=4)
    frames = simulate_sequence(product, frame_count=3, fps=30.0, speed_mm_s=1000.0)

    assert [frame.frame_index for frame in frames] == [0, 1, 2]
    assert np.isclose(frames[1].encoder_mm, 1000.0 / 30.0)
    assert np.allclose(frames[1].points_mm[:, 1] - frames[0].points_mm[:, 1], 1000.0 / 30.0)


def test_rotated_box_is_lifted_onto_conveyor_instead_of_crossing_it() -> None:
    product = sample_box_surface(
        (90.0, 55.0, 35.0), points_per_face=50, rotation_deg=(8.0, 5.0, 21.0), seed=6
    )

    assert np.isclose(product[:, 2].min(), 0.0, atol=1e-9)


@pytest.mark.parametrize(
    ("shape", "rotation_deg", "physical_min_z"),
    [
        ("box", (6.0, -4.0, 23.0), -20.79996341554126),
        ("l_prism", (-7.0, 5.0, 30.0), -17.225117574211914),
        ("cylinder", (-7.0, -7.0, 30.0), -19.928462357809217),
        ("composite", (-7.0, -5.0, 30.0), -19.483261618150337),
    ],
)
def test_tilted_physical_shape_is_grounded_on_conveyor(
    shape: str,
    rotation_deg: tuple[float, float, float],
    physical_min_z: float,
) -> None:
    dimensions = np.array([80.0, 60.0, 30.0])
    rotation = simulation.rotation_matrix_xyz(rotation_deg)
    offset = simulation._grounding_offset_z_mm(shape, dimensions, rotation)

    assert physical_min_z + offset == pytest.approx(0.0, abs=1e-9)

    observed = sample_line_profiler_shape(
        shape,
        tuple(dimensions),
        rotation_deg=rotation_deg,
        visible_completeness=1.0,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=43,
    )
    expected = (60.0, 60.0, 30.0) if shape == "cylinder" else (80.0, 60.0, 30.0)
    assert observed.reference_dimensions_mm == expected


def test_sensor_like_box_excludes_hidden_bottom_and_keeps_dual_x_views() -> None:
    observed = sample_line_profiler_box((60.0, 40.0, 30.0), edge_shadow=0.0, seed=40)

    assert observed.evidence_type == SENSOR_LIKE_EVIDENCE
    assert "bottom" not in set(observed.surface_labels)
    assert {"side_x_negative", "side_x_positive"} <= set(observed.surface_labels)
    assert "top" in set(observed.surface_labels)


def test_single_view_loses_one_opposing_side_that_dual_view_keeps() -> None:
    single = sample_line_profiler_box(
        (60.0, 40.0, 30.0), dual_camera=False, seed=41
    )
    dual = sample_line_profiler_box((60.0, 40.0, 30.0), dual_camera=True, seed=41)

    assert len(set(single.surface_labels) & {"side_x_negative", "side_x_positive"}) == 1
    assert {"side_x_negative", "side_x_positive"} <= set(dual.surface_labels)


def test_sensor_like_noise_dropout_and_shadow_are_reproducible() -> None:
    kwargs = dict(
        noise_std_mm=0.25,
        dropout=0.2,
        visible_completeness=0.75,
        edge_shadow=0.35,
        rotation_deg=(4.0, 3.0, 27.0),
        seed=42,
    )

    first = sample_line_profiler_box((80.0, 50.0, 35.0), **kwargs)
    second = sample_line_profiler_box((80.0, 50.0, 35.0), **kwargs)

    assert np.array_equal(first.points_mm, second.points_mm)
    assert np.array_equal(first.surface_labels, second.surface_labels)
    assert len(first.points_mm) < 0.8 * 80.0 * 50.0 / (first.x_pitch_mm * first.y_pitch_mm)


@pytest.mark.parametrize("shape", ["l_prism", "cylinder", "composite"])
def test_sensor_like_irregular_shapes_have_known_reference_box(shape: str) -> None:
    observed = sample_line_profiler_shape(
        shape,
        (80.0, 60.0, 30.0),
        edge_shadow=0.0,
        seed=43,
    )

    assert observed.shape == shape
    expected = (60.0, 60.0, 30.0) if shape == "cylinder" else (80.0, 60.0, 30.0)
    assert observed.reference_dimensions_mm == expected
    assert "bottom" not in set(observed.surface_labels)
    assert len(observed.points_mm) >= 100


def test_line_profiler_density_scales_with_observed_surface_area() -> None:
    config = LineProfilerConfig(profile_rate_hz=1000.0)
    small = sample_line_profiler_box(
        (20.0, 20.0, 10.0),
        config=config,
        visible_completeness=1.0,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=80,
    )
    large = sample_line_profiler_box(
        (40.0, 40.0, 10.0),
        config=config,
        visible_completeness=1.0,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=80,
    )

    assert len(large.points_mm) > len(small.points_mm) * 2.5
    assert small.x_pitch_mm == pytest.approx(config.x_pitch_mm(10.0))
    assert small.y_pitch_mm == pytest.approx(1.0)


def test_line_profiler_outputs_one_depth_per_xy_sample() -> None:
    config = LineProfilerConfig(profile_rate_hz=800.0)
    observed = sample_line_profiler_box(
        (30.0, 25.0, 12.0),
        config=config,
        visible_completeness=1.0,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=81,
    )
    x_index = np.rint(observed.points_mm[:, 0] / observed.x_pitch_mm).astype(int)
    y_index = np.rint(observed.points_mm[:, 1] / observed.y_pitch_mm).astype(int)
    cells = np.column_stack([x_index, y_index])

    assert len(np.unique(cells, axis=0)) == len(cells)
    assert observed.y_pitch_mm == pytest.approx(1.25)
    assert "bottom" not in set(observed.surface_labels)
    assert {"side_x_negative", "side_x_positive"} <= set(observed.surface_labels)


def test_missing_profile_strips_remove_complete_y_rows() -> None:
    complete = sample_line_profiler_box(
        (50.0, 60.0, 20.0),
        config=LineProfilerConfig(missing_profile_probability=0.0),
        visible_completeness=1.0,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=82,
    )
    stripped = sample_line_profiler_box(
        (50.0, 60.0, 20.0),
        config=LineProfilerConfig(missing_profile_probability=0.35),
        visible_completeness=1.0,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=82,
    )
    complete_rows = set(np.rint(complete.points_mm[:, 1] / complete.y_pitch_mm).astype(int))
    stripped_rows = set(np.rint(stripped.points_mm[:, 1] / stripped.y_pitch_mm).astype(int))

    assert stripped.missing_profile_count > 0
    assert stripped_rows < complete_rows


@pytest.mark.parametrize("center_x", [0.0, -290.0, 290.0])
def test_full_conveyor_positions_remain_inside_preliminary_fov(center_x: float) -> None:
    observed = sample_line_profiler_box(
        (20.0, 20.0, 20.0),
        center_xy_mm=(center_x, 0.0),
        visible_completeness=1.0,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=83,
    )

    assert observed.fov_clipped is False


def test_high_large_object_within_conveyor_remains_inside_fov() -> None:
    observed = sample_line_profiler_box(
        (400.0, 300.0, 300.0),
        center_xy_mm=(100.0, 0.0),
        visible_completeness=1.0,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=84,
    )

    assert observed.fov_clipped is False


@pytest.mark.parametrize("center_x", [-420.0, 420.0])
def test_points_outside_height_dependent_fov_are_clipped(center_x: float) -> None:
    observed = sample_line_profiler_box(
        (200.0, 100.0, 300.0),
        center_xy_mm=(center_x, 0.0),
        visible_completeness=1.0,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=85,
    )
    half_width = np.array(
        [LineProfilerConfig().fov_width_mm(z) / 2 for z in observed.points_mm[:, 2]]
    )

    assert observed.fov_clipped is True
    assert np.all(np.abs(observed.points_mm[:, 0]) <= half_width + 1e-9)
