"""Validated operating parameters for the synthetic measurement pipeline."""

from pydantic import BaseModel, ConfigDict, Field

from conveyor_dimensioning.hardware import SELECTED_STATION


class MeasurementConfig(BaseModel):
    """Pipeline values expressed in millimetres and seconds."""

    model_config = ConfigDict(frozen=True)

    conveyor_width_mm: float = Field(default=SELECTED_STATION.conveyor_width_mm, gt=0)
    conveyor_speed_mm_s: float = Field(
        default=SELECTED_STATION.conveyor_speed_mm_s, gt=0
    )
    plane_distance_threshold_mm: float = Field(default=0.8, gt=0)
    object_min_height_mm: float = Field(default=1.5, gt=0)
    ransac_iterations: int = Field(default=300, ge=10)
    outlier_neighbors: int = Field(default=12, ge=3)
    outlier_std_ratio: float = Field(default=2.5, gt=0)
    cluster_radius_mm: float | None = Field(default=None, gt=0)
    cluster_radius_multiplier: float = Field(default=3.0, gt=0)
    cluster_radius_min_mm: float = Field(default=2.0, gt=0)
    cluster_radius_max_mm: float = Field(default=20.0, gt=0)
    cluster_min_points: int = Field(default=8, ge=2)
    min_object_points: int = Field(default=30, ge=8)
    min_confident_points: int = Field(default=80, ge=8)
    significant_cluster_ratio: float = Field(default=0.2, gt=0, le=1)
    fragment_merge_gap_mm: float = Field(default=8.0, ge=0)
    fragment_merge_max_size_ratio: float = Field(default=0.2, gt=0, lt=1)
    optical_boundary_guard_samples: float = Field(default=2.0, gt=0)
    optical_boundary_min_points: int = Field(default=3, ge=1)
    min_valid_windows: int = Field(default=3, ge=1)
    minimum_valid_window_fraction: float | None = Field(default=0.5, gt=0, le=1)
    aggregate_mad_floor_mm: float = Field(default=2.5, gt=0)
    aggregate_mad_fraction: float = Field(default=0.025, gt=0)
    maximum_dimensions_mm: tuple[float, float, float] = (400.0, 300.0, 300.0)
