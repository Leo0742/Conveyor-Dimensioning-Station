import numpy as np
import pytest
from pydantic import ValidationError

from conveyor_dimensioning.types import AcquisitionBatch


def test_acquisition_batch_exposes_encoder_and_profile_quality_metadata() -> None:
    batch = AcquisitionBatch(
        points_mm=np.ones((20, 3)),
        encoder_position_mm=125.0,
        encoder_spacing_mm=1.0,
        profile_count=8,
        expected_profile_count=10,
        missing_profile_count=2,
        invalid_profile_count=1,
        sensor_status_flags=("saturation",),
        trigger_drop_detected=True,
        saturation_fraction=0.1,
    )

    assert batch.valid_profile_count == 7
    assert batch.valid_profile_fraction == pytest.approx(0.7)


def test_acquisition_batch_rejects_inconsistent_profile_counts() -> None:
    with pytest.raises(ValidationError, match="expected_profile_count"):
        AcquisitionBatch(
            points_mm=np.ones((20, 3)),
            encoder_position_mm=0.0,
            encoder_spacing_mm=1.0,
            profile_count=8,
            expected_profile_count=10,
            missing_profile_count=1,
            invalid_profile_count=0,
        )
