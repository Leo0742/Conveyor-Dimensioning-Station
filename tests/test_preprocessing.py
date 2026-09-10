import numpy as np

from conveyor_dimensioning.preprocessing import (
    connected_components,
    estimate_cluster_radius,
    fit_conveyor_plane_ransac,
    largest_cluster,
    remove_plane,
    statistical_filter,
)
from conveyor_dimensioning.simulation import (
    make_scene,
    sample_box_surface,
    sample_line_profiler_box,
)


def test_ransac_recovers_noisy_conveyor_plane() -> None:
    product = sample_box_surface((40.0, 30.0, 20.0), points_per_face=30, seed=1)
    scene = make_scene(product, plane_point_count=900, plane_noise_std_mm=0.15, seed=2)

    plane, inliers = fit_conveyor_plane_ransac(scene, threshold_mm=0.6, iterations=250, seed=3)

    assert plane[2] > 0.999
    assert abs(plane[3]) < 0.1
    assert inliers.sum() >= 850


def test_ransac_selects_belt_below_a_more_densely_sampled_product_top() -> None:
    product = sample_line_profiler_box(
        (70.0, 45.0, 25.0),
        visible_completeness=1.0,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=54,
    )
    scene = make_scene(
        product.points_mm,
        plane_point_count=1200,
        plane_noise_std_mm=0.1,
        seed=56,
    )

    plane, inliers = fit_conveyor_plane_ransac(
        scene, threshold_mm=0.8, iterations=300, seed=57
    )

    assert abs(plane[3]) < 0.1
    assert inliers.sum() >= 1100


def test_calibrated_belt_fit_survives_forty_times_more_object_samples() -> None:
    product = sample_line_profiler_box(
        (300.0, 200.0, 200.0),
        visible_completeness=1.0,
        edge_shadow=0.0,
        noise_std_mm=0.0,
        dropout=0.0,
        seed=58,
    )
    scene = make_scene(
        product.points_mm,
        plane_point_count=1200,
        plane_noise_std_mm=0.1,
        seed=59,
    )

    plane, inliers = fit_conveyor_plane_ransac(
        scene, threshold_mm=0.8, iterations=300, seed=60
    )

    assert plane[2] > 0.999
    assert abs(plane[3]) < 0.1
    assert inliers.sum() >= 1100


def test_remove_plane_keeps_product_above_height_threshold() -> None:
    product = sample_box_surface((40.0, 30.0, 20.0), points_per_face=30, seed=4)
    scene = make_scene(product, plane_point_count=500, plane_noise_std_mm=0.0, seed=5)

    isolated = remove_plane(scene, np.array([0.0, 0.0, 1.0, 0.0]), min_height_mm=1.0)

    assert isolated[:, 2].min() > 1.0
    assert isolated[:, 2].max() == 20.0
    assert len(isolated) < len(product)


def test_statistical_filter_removes_distant_outlier() -> None:
    rng = np.random.default_rng(8)
    cluster = rng.normal(0.0, 0.2, (80, 3))
    points = np.vstack([cluster, [100.0, 100.0, 100.0]])

    filtered = statistical_filter(points, neighbors=8, std_ratio=2.0)

    assert len(filtered) == 80
    assert filtered[:, 0].max() < 2.0


def test_largest_cluster_discards_smaller_object() -> None:
    rng = np.random.default_rng(9)
    large = rng.normal([0.0, 0.0, 10.0], 0.4, (60, 3))
    small = rng.normal([30.0, 0.0, 10.0], 0.4, (20, 3))

    selected = largest_cluster(np.vstack([small, large]), radius_mm=2.0, min_points=5)

    assert len(selected) == 60
    assert abs(selected[:, 0].mean()) < 0.2


def test_cluster_radius_comes_from_observed_spacing_with_physical_bounds() -> None:
    grid = np.array([[x, y, 10.0] for x in range(5) for y in range(5)], dtype=float)

    radius = estimate_cluster_radius(grid, multiplier=3.0, minimum_mm=2.0, maximum_mm=8.0)

    assert radius == 3.0


def test_connected_components_keeps_tiny_noise_separate() -> None:
    rng = np.random.default_rng(50)
    product = rng.normal([0.0, 0.0, 10.0], 0.5, (80, 3))
    noise = rng.normal([50.0, 0.0, 10.0], 0.2, (5, 3))

    components = connected_components(np.vstack([product, noise]), radius_mm=2.0)

    assert sorted(map(len, components), reverse=True) == [80, 5]
