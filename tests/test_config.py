import numpy as np
import pytest
from pydantic import ValidationError

from conveyor_dimensioning.config import MeasurementConfig
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
