import pytest

from conveyor_dimensioning.hardware import (
    GOCATOR_2490,
    GOCATOR_2880,
    calculate_linear_fov_layout,
    fov_width_at_height_mm,
    profile_rate_scenarios,
    profile_spacing_mm,
)


def test_2880_layout_keeps_40mm_margin_per_belt_side() -> None:
    layout = calculate_linear_fov_layout(GOCATOR_2880, target_top_fov_mm=680.0)

    assert layout.lateral_margin_per_side_mm == pytest.approx(40.0)
    assert layout.mount_height_above_belt_mm == pytest.approx(916.667, abs=0.001)
    assert layout.belt_fov_mm == pytest.approx(1006.25)
    assert layout.belt_x_pitch_mm == pytest.approx(0.78613, abs=0.00001)
    assert layout.samples_per_10mm_at_belt == pytest.approx(12.7205, abs=0.0001)
    assert layout.remaining_range_beyond_belt_mm == pytest.approx(233.333, abs=0.001)


def test_selected_2880_fov_is_1006mm_at_belt_and_680mm_at_maximum_height() -> None:
    assert fov_width_at_height_mm(0.0) == pytest.approx(1006.25)
    assert fov_width_at_height_mm(300.0) == pytest.approx(680.0)


def test_2490_is_recalculated_with_the_same_top_margin() -> None:
    layout = calculate_linear_fov_layout(GOCATOR_2490, target_top_fov_mm=680.0)

    assert layout.mount_height_above_belt_mm == pytest.approx(924.689, abs=0.001)
    assert layout.belt_fov_mm == pytest.approx(996.721, abs=0.001)
    assert layout.samples_per_10mm_at_belt == pytest.approx(19.2632, abs=0.0001)
    assert layout.remaining_range_beyond_belt_mm == pytest.approx(950.311, abs=0.001)


def test_layout_rejects_zero_margin_or_out_of_range_target() -> None:
    with pytest.raises(ValueError, match="lateral margin"):
        calculate_linear_fov_layout(GOCATOR_2880, target_top_fov_mm=600.0)
    with pytest.raises(ValueError, match="outside sensor FOV"):
        calculate_linear_fov_layout(GOCATOR_2880, target_top_fov_mm=1400.0)


def test_profile_rate_operating_points_are_requirements_not_sensor_capability() -> None:
    expected = {
        1000.0: (1.0, 10.0),
        800.0: (1.25, 8.0),
        500.0: (2.0, 5.0),
        380.0: (1000.0 / 380.0, 3.8),
    }

    scenarios = profile_rate_scenarios(speed_mm_s=1000.0)

    assert {scenario.rate_hz for scenario in scenarios} == set(expected)
    for scenario in scenarios:
        y_pitch, profiles = expected[scenario.rate_hz]
        assert scenario.y_pitch_mm == pytest.approx(y_pitch)
        assert scenario.profiles_per_10mm == pytest.approx(profiles)
        assert scenario.capability_verified is False
    assert profile_spacing_mm(1000.0, 800.0) == pytest.approx(1.25)


def test_profile_spacing_rejects_non_positive_inputs() -> None:
    with pytest.raises(ValueError, match="positive"):
        profile_spacing_mm(1000.0, 0.0)
