"""Deterministic synthetic point clouds for geometry-only validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from conveyor_dimensioning.types import PointCloudFrame

SENSOR_LIKE_EVIDENCE = "SIMPLIFIED LINE-PROFILER SYNTHETIC"
ShapeName = Literal["box", "l_prism", "cylinder", "composite"]


@dataclass(frozen=True)
class LineProfilerConfig:
    """Selected 2880 sampling geometry; not an optical or firmware emulator."""

    conveyor_speed_mm_s: float = 1000.0
    profile_rate_hz: float = 1000.0
    points_per_profile: int = 1280
    fov_near_mm: float = 390.0
    fov_far_mm: float = 1260.0
    measurement_range_mm: float = 800.0
    belt_position_in_range_mm: float = 566.6666666666666
    missing_profile_probability: float = 0.0

    def __post_init__(self) -> None:
        if self.conveyor_speed_mm_s <= 0 or self.profile_rate_hz <= 0:
            raise ValueError("speed and profile rate must be positive")
        if self.points_per_profile < 2 or self.measurement_range_mm <= 0:
            raise ValueError("profile geometry must be positive")
        if not 0 <= self.missing_profile_probability < 1:
            raise ValueError("missing_profile_probability is out of range")

    @property
    def y_pitch_mm(self) -> float:
        return self.conveyor_speed_mm_s / self.profile_rate_hz

    def fov_width_mm(self, height_above_belt_mm: float) -> float:
        """Preliminary linear FOV at a height above the conveyor plane."""
        position = self.belt_position_in_range_mm - float(height_above_belt_mm)
        position = float(np.clip(position, 0.0, self.measurement_range_mm))
        span = self.fov_far_mm - self.fov_near_mm
        return self.fov_near_mm + span * position / self.measurement_range_mm

    def x_pitch_mm(self, height_above_belt_mm: float) -> float:
        return self.fov_width_mm(height_above_belt_mm) / self.points_per_profile


@dataclass(frozen=True)
class SimulatedObject:
    """Observed points plus evaluation metadata kept outside the measurement API."""

    points_mm: np.ndarray
    surface_labels: np.ndarray
    reference_dimensions_mm: tuple[float, float, float]
    shape: ShapeName
    evidence_type: str = SENSOR_LIKE_EVIDENCE
    x_pitch_mm: float = float("nan")
    y_pitch_mm: float = float("nan")
    profile_rate_hz: float = float("nan")
    fov_clipped: bool = False
    missing_profile_count: int = 0


def rotation_matrix_xyz(rotation_deg: tuple[float, float, float]) -> np.ndarray:
    """Return a column-vector rotation matrix for roll, pitch and yaw."""
    roll, pitch, yaw = np.deg2rad(rotation_deg)
    cx, sx = np.cos(roll), np.sin(roll)
    cy, sy = np.cos(pitch), np.sin(pitch)
    cz, sz = np.cos(yaw), np.sin(yaw)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def sample_box_surface(
    dimensions_mm: tuple[float, float, float],
    *,
    points_per_face: int = 250,
    center_xy_mm: tuple[float, float] = (0.0, 0.0),
    rotation_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
    noise_std_mm: float = 0.0,
    dropout: float = 0.0,
    seed: int = 0,
) -> np.ndarray:
    """Sample a closed box surface whose unrotated bottom rests on z=0."""
    dimensions = np.asarray(dimensions_mm, dtype=float)
    if dimensions.shape != (3,) or np.any(dimensions <= 0):
        raise ValueError("dimensions_mm must contain three positive values")
    if points_per_face < 1:
        raise ValueError("points_per_face must be positive")
    if noise_std_mm < 0 or not 0 <= dropout < 1:
        raise ValueError("noise_std_mm and dropout are out of range")

    rng = np.random.default_rng(seed)
    half_x, half_y = dimensions[:2] / 2
    height = dimensions[2]
    bounds = np.array([[-half_x, half_x], [-half_y, half_y], [0.0, height]])
    faces: list[np.ndarray] = []
    for axis in range(3):
        free_axes = [candidate for candidate in range(3) if candidate != axis]
        for side in (0, 1):
            face = np.empty((points_per_face, 3), dtype=float)
            face[:, axis] = bounds[axis, side]
            for free_axis in free_axes:
                face[:, free_axis] = rng.uniform(
                    bounds[free_axis, 0], bounds[free_axis, 1], points_per_face
                )
            faces.append(face)

    corners = np.array(
        [
            [x, y, z]
            for x in (-half_x, half_x)
            for y in (-half_y, half_y)
            for z in (0.0, height)
        ],
        dtype=float,
    )
    points = np.vstack([*faces, corners])
    points -= np.array([0.0, 0.0, height / 2])
    points = points @ rotation_matrix_xyz(rotation_deg).T
    points += np.array([center_xy_mm[0], center_xy_mm[1], 0.0])
    points[:, 2] -= points[:, 2].min()

    if noise_std_mm:
        points += rng.normal(0.0, noise_std_mm, points.shape)
    if dropout:
        points = points[rng.random(len(points)) >= dropout]
    return points


def _axis_cell_centers(span_mm: float, pitch_mm: float) -> np.ndarray:
    count = max(1, int(np.ceil(span_mm / pitch_mm)))
    step = span_mm / count
    return -span_mm / 2 + step * (np.arange(count) + 0.5)


def _shape_top_mask(
    shape: ShapeName, x: np.ndarray, y: np.ndarray, dimensions: np.ndarray
) -> np.ndarray:
    length, width, _ = dimensions
    if shape == "box":
        return np.ones_like(x, dtype=bool)
    if shape == "l_prism":
        arm = min(length, width) * 0.35
        return (x <= -length / 2 + arm) | (y <= -width / 2 + arm)
    if shape == "composite":
        arm = min(length, width) * 0.32
        return (np.abs(y) <= arm / 2) | (np.abs(x) <= arm / 2)
    radius = min(length, width) / 2
    return x**2 + y**2 <= radius**2


def _polygon_for_shape(shape: ShapeName, dimensions: np.ndarray) -> np.ndarray:
    length, width, _ = dimensions
    if shape == "l_prism":
        arm = min(length, width) * 0.35
        return np.array(
            [
                [-length / 2, -width / 2],
                [length / 2, -width / 2],
                [length / 2, -width / 2 + arm],
                [-length / 2 + arm, -width / 2 + arm],
                [-length / 2 + arm, width / 2],
                [-length / 2, width / 2],
            ]
        )
    return np.array(
        [
            [-length / 2, -width / 2],
            [length / 2, -width / 2],
            [length / 2, width / 2],
            [-length / 2, width / 2],
        ]
    )


def _grounding_offset_z_mm(
    shape: ShapeName, dimensions: np.ndarray, rotation: np.ndarray
) -> float:
    """Return the Z translation that places the rotated physical shape on the belt."""
    length, width, height = dimensions
    if shape == "cylinder":
        radius = min(length, width) / 2
        radial_extent = radius * np.hypot(rotation[2, 0], rotation[2, 1])
        axial_extent = height / 2 * abs(rotation[2, 2])
        return float(radial_extent + axial_extent)

    polygons = [_polygon_for_shape(shape, dimensions)]
    if shape == "composite":
        arm = min(length, width) * 0.32
        polygons = [
            _polygon_for_shape("box", np.array([length, arm, height])),
            _polygon_for_shape("box", np.array([arm, width, height])),
        ]
    support_points = np.vstack(
        [
            np.column_stack([polygon, np.full(len(polygon), z)])
            for polygon in polygons
            for z in (-height / 2, height / 2)
        ]
    )
    return float(-(support_points @ rotation.T)[:, 2].min())


def _line_profiler_candidates(
    shape: ShapeName,
    dimensions: np.ndarray,
    *,
    x_pitch_mm: float,
    y_pitch_mm: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build deterministic area/edge lattices before visibility and z-buffering."""
    length, width, height = dimensions
    x_values = _axis_cell_centers(length, x_pitch_mm)
    y_values = _axis_cell_centers(width, y_pitch_mm)
    xx, yy = np.meshgrid(x_values, y_values, indexing="xy")
    mask = _shape_top_mask(shape, xx, yy, dimensions)
    top = np.column_stack([xx[mask], yy[mask], np.full(np.count_nonzero(mask), height)])
    top_normals = np.repeat([[0.0, 0.0, 1.0]], len(top), axis=0)
    top_labels = np.full(len(top), "top", dtype="U24")

    boundary_points: list[np.ndarray] = []
    boundary_normals: list[np.ndarray] = []
    boundary_labels: list[np.ndarray] = []
    edge_pitch = min(x_pitch_mm, y_pitch_mm)
    if shape == "cylinder":
        radius = min(length, width) / 2
        count = max(12, int(np.ceil(2 * np.pi * radius / edge_pitch)))
        angles = 2 * np.pi * (np.arange(count) + 0.5) / count
        xy = np.column_stack([radius * np.cos(angles), radius * np.sin(angles)])
        normals_xy = np.column_stack([np.cos(angles), np.sin(angles)])
        z = rng.uniform(0.08 * height, 0.92 * height, count)
        boundary_points.append(np.column_stack([xy, z]))
        boundary_normals.append(np.column_stack([normals_xy, np.zeros(count)]))
        boundary_labels.append(
            np.where(normals_xy[:, 0] >= 0, "side_x_positive", "side_x_negative").astype(
                "U24"
            )
        )
    else:
        polygons = [_polygon_for_shape(shape, dimensions)]
        if shape == "composite":
            arm = min(length, width) * 0.32
            polygons = [
                _polygon_for_shape("box", np.array([length, arm, height])),
                _polygon_for_shape("box", np.array([arm, width, height])),
            ]
        for polygon in polygons:
            for index, start in enumerate(polygon):
                end = polygon[(index + 1) % len(polygon)]
                edge = end - start
                edge_length = float(np.linalg.norm(edge))
                count = max(1, int(np.ceil(edge_length / edge_pitch)))
                fractions = (np.arange(count) + 0.5) / count
                xy = start + fractions[:, None] * edge
                normal_xy = np.array([edge[1], -edge[0]]) / edge_length
                normals_xy = np.repeat(normal_xy[None, :], count, axis=0)
                z = rng.uniform(0.08 * height, 0.92 * height, count)
                boundary_points.append(np.column_stack([xy, z]))
                boundary_normals.append(np.column_stack([normals_xy, np.zeros(count)]))
                if abs(normal_xy[0]) >= abs(normal_xy[1]):
                    label = "side_x_positive" if normal_xy[0] >= 0 else "side_x_negative"
                else:
                    label = "side_y_positive" if normal_xy[1] >= 0 else "side_y_negative"
                boundary_labels.append(np.full(count, label, dtype="U24"))

    return (
        np.vstack([top, *boundary_points]),
        np.vstack([top_normals, *boundary_normals]),
        np.concatenate([top_labels, *boundary_labels]),
    )


def _z_buffer_profile_cells(
    points: np.ndarray,
    labels: np.ndarray,
    *,
    x_pitch_mm: float,
    y_pitch_mm: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x_index = np.rint(points[:, 0] / x_pitch_mm).astype(np.int64)
    y_index = np.rint(points[:, 1] / y_pitch_mm).astype(np.int64)
    order = np.lexsort((-points[:, 2], y_index, x_index))
    ordered_cells = np.column_stack([x_index[order], y_index[order]])
    _, first = np.unique(ordered_cells, axis=0, return_index=True)
    selected = order[first]
    observed = points[selected].copy()
    observed[:, 0] = x_index[selected] * x_pitch_mm
    observed[:, 1] = y_index[selected] * y_pitch_mm
    return observed, labels[selected], y_index[selected]


def sample_line_profiler_shape(
    shape: ShapeName,
    dimensions_mm: tuple[float, float, float],
    *,
    config: LineProfilerConfig | None = None,
    center_xy_mm: tuple[float, float] = (0.0, 0.0),
    rotation_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
    dual_camera: bool = True,
    visible_completeness: float = 0.9,
    edge_shadow: float = 0.25,
    noise_std_mm: float = 0.15,
    dropout: float = 0.05,
    seed: int = 0,
) -> SimulatedObject:
    """Generate a simplified line-profiler observation, never a Gocator emulator."""
    dimensions = np.asarray(dimensions_mm, dtype=float)
    if dimensions.shape != (3,) or np.any(dimensions <= 0):
        raise ValueError("dimensions_mm must contain three positive values")
    if noise_std_mm < 0 or not 0 <= dropout < 1:
        raise ValueError("noise_std_mm and dropout are out of range")
    if not 0 < visible_completeness <= 1 or not 0 <= edge_shadow <= 1:
        raise ValueError("visibility controls are out of range")
    rng = np.random.default_rng(seed)
    if shape not in ("box", "l_prism", "cylinder", "composite"):
        raise ValueError(f"unsupported shape: {shape}")
    profiler = config or LineProfilerConfig()
    x_pitch_mm = profiler.x_pitch_mm(float(dimensions[2]))
    points, normals, labels = _line_profiler_candidates(
        shape,
        dimensions,
        x_pitch_mm=x_pitch_mm,
        y_pitch_mm=profiler.y_pitch_mm,
        rng=rng,
    )
    rotation = rotation_matrix_xyz(rotation_deg)
    centered = points - np.array([0.0, 0.0, dimensions[2] / 2])
    transformed = centered @ rotation.T
    transformed[:, 2] += _grounding_offset_z_mm(shape, dimensions, rotation)
    transformed += np.array([center_xy_mm[0], center_xy_mm[1], 0.0])
    transformed_normals = normals @ rotation.T

    views = [np.array([0.55, 0.0, 0.835])]
    if dual_camera:
        views.append(np.array([-0.55, 0.0, 0.835]))
    visible_score = np.max(transformed_normals @ np.column_stack(views), axis=1)
    visible = visible_score > 0.05
    half_fov = np.array(
        [profiler.fov_width_mm(float(height)) / 2 for height in transformed[:, 2]]
    )
    outside_fov = np.abs(transformed[:, 0]) > half_fov
    fov_clipped = bool(np.any(visible & outside_fov))
    visible &= ~outside_fov
    height_span = max(float(np.ptp(transformed[:, 2])), 1e-9)
    normalized_height = (transformed[:, 2] - transformed[:, 2].min()) / height_span
    side = labels != "top"
    keep_probability = visible_completeness * (
        1.0 - edge_shadow * (1.0 - normalized_height) * side
    )
    keep = visible & (rng.random(len(points)) <= keep_probability)
    transformed = transformed[keep]
    labels = labels[keep]
    observed, observed_labels, profile_index = _z_buffer_profile_cells(
        transformed,
        labels,
        x_pitch_mm=x_pitch_mm,
        y_pitch_mm=profiler.y_pitch_mm,
    )
    missing_rows: set[int] = set()
    if profiler.missing_profile_probability:
        for row in np.unique(profile_index):
            if rng.random() < profiler.missing_profile_probability:
                missing_rows.add(int(row))
        keep_rows = np.array([int(row) not in missing_rows for row in profile_index])
        observed = observed[keep_rows]
        observed_labels = observed_labels[keep_rows]
    if dropout:
        keep_points = rng.random(len(observed)) >= dropout
        observed = observed[keep_points]
        observed_labels = observed_labels[keep_points]
    if noise_std_mm:
        observed = observed + rng.normal(0.0, noise_std_mm, observed.shape)
    if shape == "cylinder":
        diameter = float(min(dimensions[0], dimensions[1]))
        reference = (diameter, diameter, float(dimensions[2]))
    else:
        reference = tuple(float(value) for value in dimensions)
    return SimulatedObject(
        points_mm=observed,
        surface_labels=observed_labels,
        reference_dimensions_mm=reference,
        shape=shape,
        x_pitch_mm=x_pitch_mm,
        y_pitch_mm=profiler.y_pitch_mm,
        profile_rate_hz=profiler.profile_rate_hz,
        fov_clipped=fov_clipped,
        missing_profile_count=len(missing_rows),
    )


def sample_line_profiler_box(
    dimensions_mm: tuple[float, float, float], **kwargs
) -> SimulatedObject:
    """Convenience wrapper for the selected simplified line-profiler model."""
    return sample_line_profiler_shape("box", dimensions_mm, **kwargs)


def make_scene(
    product_points_mm: np.ndarray,
    *,
    conveyor_width_mm: float = 600.0,
    zone_length_mm: float = 700.0,
    plane_point_count: int = 2500,
    plane_noise_std_mm: float = 0.15,
    seed: int = 0,
) -> np.ndarray:
    """Combine product points with a randomly sampled conveyor plane."""
    if plane_point_count < 3:
        raise ValueError("plane_point_count must be at least three")
    rng = np.random.default_rng(seed)
    plane = np.column_stack(
        [
            rng.uniform(-conveyor_width_mm / 2, conveyor_width_mm / 2, plane_point_count),
            rng.uniform(-zone_length_mm / 2, zone_length_mm / 2, plane_point_count),
            rng.normal(0.0, plane_noise_std_mm, plane_point_count),
        ]
    )
    return np.vstack([plane, np.asarray(product_points_mm, dtype=float)])


def simulate_sequence(
    product_points_mm: np.ndarray,
    *,
    frame_count: int = 12,
    fps: float = 30.0,
    speed_mm_s: float = 1000.0,
) -> list[PointCloudFrame]:
    """Translate an unchanged product along +Y using encoder-equivalent positions."""
    if frame_count < 1 or fps <= 0 or speed_mm_s < 0:
        raise ValueError("frame_count, fps and speed_mm_s are out of range")
    base = np.asarray(product_points_mm, dtype=float)
    distance_per_frame = speed_mm_s / fps
    frames = []
    for frame_index in range(frame_count):
        encoder_mm = frame_index * distance_per_frame
        translated = base + np.array([0.0, encoder_mm, 0.0])
        frames.append(
            PointCloudFrame(
                points_mm=translated,
                frame_index=frame_index,
                encoder_mm=encoder_mm,
            )
        )
    return frames
