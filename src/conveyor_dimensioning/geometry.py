"""Axis-aligned, PCA and hull-frame minimum-volume bounding boxes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import ConvexHull, QhullError


@dataclass(frozen=True)
class BoundingBox3D:
    """A rectangular box represented by center, orthonormal axes and extents."""

    center_mm: np.ndarray
    rotation: np.ndarray
    extents_mm: np.ndarray

    @property
    def volume_mm3(self) -> float:
        return float(np.prod(self.extents_mm))

    @property
    def corners_mm(self) -> np.ndarray:
        signs = np.array(
            [[x, y, z] for x in (-0.5, 0.5) for y in (-0.5, 0.5) for z in (-0.5, 0.5)]
        )
        return self.center_mm + (signs * self.extents_mm) @ self.rotation.T


@dataclass(frozen=True)
class ReferenceBoundingBox:
    """Optional Open3D result with its exact algorithm label and version."""

    box: BoundingBox3D
    method: str
    open3d_version: str


def _validate_points(points_mm: np.ndarray) -> np.ndarray:
    points = np.asarray(points_mm, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 4:
        raise ValueError("points_mm must have shape (n, 3), n >= 4")
    if not np.isfinite(points).all():
        raise ValueError("points_mm must contain finite values")
    return points


def _box_in_frame(points: np.ndarray, rotation: np.ndarray) -> BoundingBox3D:
    local = points @ rotation
    lower = local.min(axis=0)
    upper = local.max(axis=0)
    return BoundingBox3D(
        center_mm=((lower + upper) / 2) @ rotation.T,
        rotation=rotation,
        extents_mm=upper - lower,
    )


def normalize_dimensions(extents_mm: np.ndarray | list[float]) -> np.ndarray:
    """Return dimensions as length >= width >= height."""
    extents = np.asarray(extents_mm, dtype=float)
    if extents.shape != (3,) or np.any(extents < 0):
        raise ValueError("extents_mm must contain three non-negative values")
    return np.sort(extents)[::-1]


def axis_aligned_box(points_mm: np.ndarray) -> BoundingBox3D:
    """Return an AABB in the conveyor coordinate frame."""
    return _box_in_frame(_validate_points(points_mm), np.eye(3))


def pca_box(points_mm: np.ndarray) -> BoundingBox3D:
    """Return the oriented box aligned with principal components."""
    points = _validate_points(points_mm)
    covariance = np.cov(points - points.mean(axis=0), rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    rotation = eigenvectors[:, np.argsort(eigenvalues)[::-1]]
    if np.linalg.det(rotation) < 0:
        rotation[:, -1] *= -1
    return _box_in_frame(points, rotation)


def minimum_volume_box(points_mm: np.ndarray) -> BoundingBox3D:
    """Approximate the global minimum OBB by evaluating convex-hull face-edge frames.

    The method is stronger than PCA and matches Open3D's documented minimal-approx
    family: every triangular hull face supplies its normal and each edge supplies an
    in-plane axis. It is exact for rectangular boxes and many engineering shapes, but
    is not presented as the exhaustive O'Rourke algorithm for every convex polyhedron.
    """
    points = _validate_points(points_mm)
    try:
        hull = ConvexHull(points)
    except QhullError:
        return pca_box(points)

    hull_points = points[hull.vertices]
    best: BoundingBox3D | None = None
    seen: set[tuple[float, ...]] = set()
    for simplex in hull.simplices:
        triangle = points[simplex]
        normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
        normal_norm = np.linalg.norm(normal)
        if normal_norm < 1e-10:
            continue
        z_axis = normal / normal_norm
        for start, end in ((0, 1), (1, 2), (2, 0)):
            edge = triangle[end] - triangle[start]
            edge -= z_axis * (edge @ z_axis)
            edge_norm = np.linalg.norm(edge)
            if edge_norm < 1e-10:
                continue
            x_axis = edge / edge_norm
            y_axis = np.cross(z_axis, x_axis)
            y_axis /= np.linalg.norm(y_axis)
            rotation = np.column_stack([x_axis, y_axis, z_axis])
            key = tuple(np.round(np.abs(rotation), 7).ravel())
            if key in seen:
                continue
            seen.add(key)
            candidate = _box_in_frame(hull_points, rotation)
            if best is None or candidate.volume_mm3 < best.volume_mm3:
                best = candidate
    if best is None:
        return pca_box(points)
    return best


def dominant_top_plane_box(points_mm: np.ndarray, *, seed: int = 0) -> BoundingBox3D:
    """Fit the dominant top surface, then minimize the footprint in that plane.

    Line-profiler clouds contain a dense upper surface and sparse side/support
    evidence. An unconstrained 3D minimum-volume box can align with the artificial
    support wedge instead of the physical top frame. The fallback preserves the
    general OBB behavior when a sufficiently supported upward-facing plane is absent.
    """
    points = _validate_points(points_mm)
    rng = np.random.default_rng(seed)
    sample = points
    if len(sample) > 4000:
        sample = sample[rng.choice(len(sample), 4000, replace=False)]

    best_mask = np.zeros(len(sample), dtype=bool)
    for _ in range(300):
        triangle = sample[rng.choice(len(sample), 3, replace=False)]
        normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
        normal_norm = np.linalg.norm(normal)
        if normal_norm < 1e-9:
            continue
        normal /= normal_norm
        if normal[2] < 0:
            normal *= -1
        if normal[2] < 0.95:
            continue
        offset = -normal @ triangle[0]
        mask = np.abs(sample @ normal + offset) <= 0.8
        if mask.sum() > best_mask.sum():
            best_mask = mask
    if best_mask.sum() < 30:
        return minimum_volume_box(points)

    center = sample[best_mask].mean(axis=0)
    _, _, vh = np.linalg.svd(sample[best_mask] - center, full_matrices=False)
    normal = vh[-1]
    if normal[2] < 0:
        normal *= -1
    x_basis = np.array([1.0, 0.0, 0.0])
    x_basis -= normal * (x_basis @ normal)
    x_basis /= np.linalg.norm(x_basis)
    y_basis = np.cross(normal, x_basis)

    projected = points @ np.column_stack([x_basis, y_basis])
    try:
        hull = ConvexHull(projected)
    except QhullError:
        return minimum_volume_box(points)
    hull_points = projected[hull.vertices]
    best: BoundingBox3D | None = None
    for index, start in enumerate(hull_points):
        edge = hull_points[(index + 1) % len(hull_points)] - start
        if np.linalg.norm(edge) < 1e-9:
            continue
        angle = np.arctan2(edge[1], edge[0])
        x_axis = np.cos(angle) * x_basis + np.sin(angle) * y_basis
        y_axis = np.cross(normal, x_axis)
        rotation = np.column_stack([x_axis, y_axis, normal])
        candidate = _box_in_frame(points, rotation)
        if best is None or candidate.volume_mm3 < best.volume_mm3:
            best = candidate
    return best if best is not None else minimum_volume_box(points)


def open3d_reference_box(points_mm: np.ndarray) -> ReferenceBoundingBox:
    """Use Jylänki when exposed by Open3D, else stable 0.19 minimal-approx.

    Open3D stays an optional validation dependency and is not imported by the main
    measurement path.
    """
    points = _validate_points(points_mm)
    try:
        import open3d as o3d
    except ImportError as error:
        raise RuntimeError("Open3D optional dependency is not installed") from error

    method_enum = getattr(o3d.t.geometry, "MethodOBBCreate", None)
    jylanki = getattr(method_enum, "MINIMAL_JYLANKI", None)
    if jylanki is not None:
        tensor = o3d.core.Tensor(points, dtype=o3d.core.Dtype.Float64)
        result = o3d.t.geometry.OrientedBoundingBox.create_from_points(
            tensor, robust=False, method=jylanki
        )
        box = BoundingBox3D(
            center_mm=np.asarray(result.center.numpy()),
            rotation=np.asarray(result.rotation.numpy()),
            extents_mm=np.asarray(result.extent.numpy()),
        )
        method = "MINIMAL_JYLANKI"
    else:
        result = o3d.geometry.OrientedBoundingBox.create_from_points_minimal(
            o3d.utility.Vector3dVector(points), robust=False
        )
        box = BoundingBox3D(
            center_mm=np.asarray(result.center),
            rotation=np.asarray(result.R),
            extents_mm=np.asarray(result.extent),
        )
        method = "create_from_points_minimal (minimal-approx)"
    return ReferenceBoundingBox(box=box, method=method, open3d_version=o3d.__version__)
