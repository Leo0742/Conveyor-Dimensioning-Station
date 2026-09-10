"""Classical point-cloud preprocessing with deterministic failure behavior."""

from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


def _plane_from_three(points: np.ndarray) -> np.ndarray | None:
    first, second, third = points
    normal = np.cross(second - first, third - first)
    norm = np.linalg.norm(normal)
    if norm < 1e-9:
        return None
    normal /= norm
    if normal[2] < 0:
        normal *= -1
    return np.append(normal, -normal @ first)


def fit_conveyor_plane_ransac(
    points_mm: np.ndarray,
    *,
    threshold_mm: float = 0.8,
    iterations: int = 300,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit the dominant plane and return normalized coefficients plus inlier mask."""
    points = np.asarray(points_mm, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 3:
        raise ValueError("points_mm must have shape (n, 3), n >= 3")
    if threshold_mm <= 0 or iterations < 1:
        raise ValueError("threshold_mm and iterations must be positive")

    rng = np.random.default_rng(seed)
    best_mask = np.zeros(len(points), dtype=bool)
    closest_supported_height = np.inf
    minimum_support = max(30, min(200, len(points) // 20))
    calibrated_band = points[
        np.abs(points[:, 2]) <= max(4.0 * threshold_mm, 2.0)
    ]
    if len(calibrated_band) >= 30:
        band_center = calibrated_band.mean(axis=0)
        _, _, band_vh = np.linalg.svd(
            calibrated_band - band_center, full_matrices=False
        )
        band_normal = band_vh[-1]
        if band_normal[2] < 0:
            band_normal *= -1
        calibrated_candidate = np.append(band_normal, -band_normal @ band_center)
        if calibrated_candidate[2] >= 0.7:
            calibrated_distances = np.abs(
                points @ calibrated_candidate[:3] + calibrated_candidate[3]
            )
            calibrated_mask = calibrated_distances <= threshold_mm
            if int(calibrated_mask.sum()) >= minimum_support:
                best_mask = calibrated_mask
                closest_supported_height = abs(
                    -calibrated_candidate[3] / calibrated_candidate[2]
                )
    for _ in range(iterations):
        candidate = _plane_from_three(points[rng.choice(len(points), 3, replace=False)])
        if candidate is None or candidate[2] < 0.7:
            continue
        distances = np.abs(points @ candidate[:3] + candidate[3])
        mask = distances <= threshold_mm
        support = int(mask.sum())
        candidate_height = -candidate[3] / candidate[2]
        if support >= minimum_support and abs(candidate_height) < closest_supported_height:
            closest_supported_height = abs(candidate_height)
            best_mask = mask

    if best_mask.sum() < 3:
        raise ValueError("dominant conveyor plane was not found")
    inlier_points = points[best_mask]
    center = inlier_points.mean(axis=0)
    _, _, vh = np.linalg.svd(inlier_points - center, full_matrices=False)
    normal = vh[-1]
    if normal[2] < 0:
        normal *= -1
    plane = np.append(normal, -normal @ center)
    refined_distances = np.abs(points @ plane[:3] + plane[3])
    return plane, refined_distances <= threshold_mm


def remove_plane(
    points_mm: np.ndarray,
    plane: np.ndarray,
    *,
    min_height_mm: float = 1.5,
) -> np.ndarray:
    """Keep points on the positive side of the conveyor by a minimum height."""
    points = np.asarray(points_mm, dtype=float)
    coefficients = np.asarray(plane, dtype=float)
    if coefficients.shape != (4,):
        raise ValueError("plane must have shape (4,)")
    normal_norm = np.linalg.norm(coefficients[:3])
    if normal_norm < 1e-12:
        raise ValueError("plane normal must be non-zero")
    signed_distance = (points @ coefficients[:3] + coefficients[3]) / normal_norm
    return points[signed_distance > min_height_mm]


def statistical_filter(
    points_mm: np.ndarray,
    *,
    neighbors: int = 12,
    std_ratio: float = 2.5,
) -> np.ndarray:
    """Remove points with unusually large mean k-neighbour distance."""
    points = np.asarray(points_mm, dtype=float)
    if len(points) <= neighbors or neighbors < 2 or std_ratio <= 0:
        return points.copy()
    distances, _ = cKDTree(points).query(points, k=neighbors + 1)
    mean_distances = distances[:, 1:].mean(axis=1)
    threshold = mean_distances.mean() + std_ratio * mean_distances.std()
    return points[mean_distances <= threshold]


def estimate_cluster_radius(
    points_mm: np.ndarray,
    *,
    multiplier: float = 3.0,
    minimum_mm: float = 2.0,
    maximum_mm: float = 12.0,
) -> float:
    """Estimate a connectivity radius from observed nearest-neighbour spacing."""
    points = np.asarray(points_mm, dtype=float)
    if multiplier <= 0 or minimum_mm <= 0 or maximum_mm < minimum_mm:
        raise ValueError("invalid radius estimation parameters")
    if len(points) < 2:
        return minimum_mm
    distances, _ = cKDTree(points).query(points, k=2)
    # A high quantile represents the sparsest still-observed surface better than
    # the median, which is often dominated by a densely sampled vertical face.
    spacing = float(np.quantile(distances[:, 1], 0.9))
    return float(np.clip(spacing * multiplier, minimum_mm, maximum_mm))


def connected_components(points_mm: np.ndarray, *, radius_mm: float) -> list[np.ndarray]:
    """Return every radius-connected component, including tiny noise groups."""
    points = np.asarray(points_mm, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("points_mm must have shape (n, 3)")
    if radius_mm <= 0:
        raise ValueError("radius_mm must be positive")
    if len(points) == 0:
        return []

    tree = cKDTree(points)
    visited = np.zeros(len(points), dtype=bool)
    components: list[np.ndarray] = []
    for start in range(len(points)):
        if visited[start]:
            continue
        stack = [start]
        visited[start] = True
        indices: list[int] = []
        while stack:
            current = stack.pop()
            indices.append(current)
            for neighbor in tree.query_ball_point(points[current], radius_mm):
                if not visited[neighbor]:
                    visited[neighbor] = True
                    stack.append(neighbor)
        components.append(points[np.asarray(indices)])
    return components


def merge_nearby_components(
    components: list[np.ndarray], *, maximum_gap_mm: float
) -> list[np.ndarray]:
    """Merge components whose axis-aligned bounding boxes are physically close."""
    if maximum_gap_mm < 0:
        raise ValueError("maximum_gap_mm must be non-negative")
    merged = [np.asarray(component, dtype=float) for component in components]
    changed = True
    while changed:
        changed = False
        for left_index in range(len(merged)):
            left = merged[left_index]
            left_min, left_max = left.min(axis=0), left.max(axis=0)
            for right_index in range(left_index + 1, len(merged)):
                right = merged[right_index]
                right_min, right_max = right.min(axis=0), right.max(axis=0)
                gap = np.maximum(0.0, np.maximum(left_min - right_max, right_min - left_max))
                if np.linalg.norm(gap) <= maximum_gap_mm:
                    merged[left_index] = np.vstack([left, right])
                    del merged[right_index]
                    changed = True
                    break
            if changed:
                break
    return merged


def largest_cluster(
    points_mm: np.ndarray,
    *,
    radius_mm: float = 4.0,
    min_points: int = 8,
) -> np.ndarray:
    """Return the largest radius-connected component meeting a size threshold."""
    points = np.asarray(points_mm, dtype=float)
    if len(points) == 0:
        return points.copy()
    if radius_mm <= 0 or min_points < 1:
        raise ValueError("radius_mm must be positive and min_points at least one")

    components = [
        component
        for component in connected_components(points, radius_mm=radius_mm)
        if len(component) >= min_points
    ]
    if not components:
        return np.empty((0, 3), dtype=float)
    return max(components, key=len)
