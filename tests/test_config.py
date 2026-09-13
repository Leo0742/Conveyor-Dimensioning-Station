import numpy as np
import pytest
from pydantic import ValidationError

from conveyor_dimensioning.config import MeasurementConfig
from conveyor_dimensioning.hardware import SELECTED_LAYOUT, SELECTED_STATION
from conveyor_dimensioning.simulation import LineProfilerConfig
from conveyor_dimensioning.types import DimensionResult, PointCloudFrame


def test_config_rejects_non_positive_operating_values() -> None:
    with pytest.raises(ValidationError):
        MeasurementConfig(conveyor_speed_mm_s=0)


def test_point_cloud_frame_requires_n_by_three_points() -> None:
    with pytest.raises(ValueError, match="shape"):
        PointCloudFrame(points_mm=np.ones((4, 2)), frame_index=0, encoder_mm=0.0)


def test_dimension_result_orders_length_width_height() -> None:
    result = DimensionResult.from_extents(
        extents_mm=np.array([10.0, 40.0, 20.0]),
        confidence=0.9,
        status="ok",
        point_count=100,
    )

    assert result.length_mm == 40.0
    assert result.width_mm == 20.0
    assert result.height_mm == 10.0


def test_runtime_defaults_do_not_drift_from_selected_station_geometry() -> None:
    measurement = MeasurementConfig()
    profiler = LineProfilerConfig()

    assert measurement.conveyor_width_mm == SELECTED_STATION.conveyor_width_mm
    assert measurement.conveyor_speed_mm_s == SELECTED_STATION.conveyor_speed_mm_s
    assert profiler.conveyor_speed_mm_s == SELECTED_STATION.conveyor_speed_mm_s
    assert profiler.profile_rate_hz == SELECTED_STATION.target_profile_rate_hz
    assert profiler.points_per_profile == SELECTED_STATION.sensor.points_per_profile
    assert profiler.belt_position_in_range_mm == SELECTED_LAYOUT.belt_position_in_range_mm
