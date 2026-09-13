"""Shared data contracts for frames and dimension results."""

from __future__ import annotations

from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MeasurementStatus = Literal[
    "ok",
    "insufficient_depth_data",
    "object_overlap",
    "calibration_error",
    "measurement_out_of_range",
    "low_confidence",
    "wms_unavailable",
]


class PointCloudFrame(BaseModel):
    """One point-cloud frame in the conveyor coordinate system."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    points_mm: np.ndarray
    frame_index: int = Field(ge=0)
    encoder_mm: float

    @field_validator("points_mm")
    @classmethod
    def validate_points(cls, value: np.ndarray) -> np.ndarray:
        points = np.asarray(value, dtype=float)
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("points_mm must have shape (n, 3)")
        if not np.isfinite(points).all():
            raise ValueError("points_mm must contain finite values")
        return points


class AcquisitionBatch(BaseModel):
    """Acquisition-boundary batch with encoder and profile-quality metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    points_mm: np.ndarray
    encoder_position_mm: float
    encoder_spacing_mm: float = Field(gt=0)
    profile_count: int = Field(ge=0)
    expected_profile_count: int = Field(ge=1)
    missing_profile_count: int = Field(ge=0)
    invalid_profile_count: int = Field(ge=0)
    sensor_status_flags: tuple[str, ...] = ()
    trigger_drop_detected: bool = False
    saturation_fraction: float | None = Field(default=None, ge=0, le=1)

    @field_validator("points_mm")
    @classmethod
    def validate_points(cls, value: np.ndarray) -> np.ndarray:
        return PointCloudFrame.validate_points(value)

    @model_validator(mode="after")
    def validate_profile_counts(self) -> AcquisitionBatch:
        if self.profile_count + self.missing_profile_count != self.expected_profile_count:
            raise ValueError(
                "profile_count plus missing_profile_count must equal expected_profile_count"
            )
        if self.invalid_profile_count > self.profile_count:
            raise ValueError("invalid_profile_count cannot exceed profile_count")
        return self

    @property
    def valid_profile_count(self) -> int:
        return self.profile_count - self.invalid_profile_count

    @property
    def valid_profile_fraction(self) -> float:
        return self.valid_profile_count / self.expected_profile_count


class DimensionResult(BaseModel):
    """Sorted OBB edges L>=W>=H and an uncalibrated heuristic quality score.

    These names are size ordering, not conveyor axes. The installation's vertical
    envelope is the separate physical Z limit in the selected station geometry.
    """

    model_config = ConfigDict(frozen=True)

    length_mm: float = Field(ge=0)
    width_mm: float = Field(ge=0)
    height_mm: float = Field(ge=0)
    confidence: float = Field(
        ge=0, le=1, description="Uncalibrated heuristic quality score"
    )
    status: MeasurementStatus
    point_count: int = Field(ge=0)

    @classmethod
    def from_extents(
        cls,
        extents_mm: np.ndarray,
        *,
        confidence: float,
        status: MeasurementStatus,
        point_count: int,
    ) -> DimensionResult:
        ordered = np.sort(np.asarray(extents_mm, dtype=float))[::-1]
        if ordered.shape != (3,):
            raise ValueError("extents_mm must have shape (3,)")
        return cls(
            length_mm=float(ordered[0]),
            width_mm=float(ordered[1]),
            height_mm=float(ordered[2]),
            confidence=confidence,
            status=status,
            point_count=point_count,
        )
