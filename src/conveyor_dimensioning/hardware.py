"""Preliminary FOV layout calculations kept separate from sensor accuracy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SensorFovSpec:
    """Manufacturer FOV endpoints used only for preliminary interpolation."""

    name: str
    points_per_profile: int
    clearance_mm: float
    measurement_range_mm: float
    fov_near_mm: float
    fov_far_mm: float


@dataclass(frozen=True)
class PreliminaryLayout:
    """Calculated mounting envelope, not a factory calibration result."""

    sensor_name: str
    target_top_fov_mm: float
    lateral_margin_per_side_mm: float
    top_position_in_range_mm: float
    belt_position_in_range_mm: float
    mount_height_above_belt_mm: float
    belt_fov_mm: float
    belt_x_pitch_mm: float
    samples_per_10mm_at_belt: float
    remaining_range_beyond_belt_mm: float


@dataclass(frozen=True)
class ProfileRateScenario:
    """Required sampling point; not proof that a sensor configuration can reach it."""

    rate_hz: float
    y_pitch_mm: float
    profiles_per_10mm: float
    capability_verified: bool = False


@dataclass(frozen=True)
class StationGeometry:
    """Shared production-layout assumptions used by calculations and simulation."""

    sensor: SensorFovSpec
    conveyor_width_mm: float
    maximum_object_height_mm: float
    measurement_zone_length_mm: float
    target_top_fov_mm: float
    conveyor_speed_mm_s: float
    target_profile_rate_hz: float


GOCATOR_2880 = SensorFovSpec(
    name="LMI Gocator 2880",
    points_per_profile=1280,
    clearance_mm=350.0,
    measurement_range_mm=800.0,
    fov_near_mm=390.0,
    fov_far_mm=1260.0,
)

GOCATOR_2490 = SensorFovSpec(
    name="LMI Gocator 2490",
    points_per_profile=1920,
    clearance_mm=350.0,
    measurement_range_mm=1525.0,
    fov_near_mm=390.0,
    fov_far_mm=2000.0,
)

SELECTED_STATION = StationGeometry(
    sensor=GOCATOR_2880,
    conveyor_width_mm=600.0,
    maximum_object_height_mm=300.0,
    measurement_zone_length_mm=700.0,
    target_top_fov_mm=680.0,
    conveyor_speed_mm_s=1000.0,
    target_profile_rate_hz=1000.0,
)


def profile_spacing_mm(speed_mm_s: float, profile_rate_hz: float) -> float:
    """Return longitudinal sample spacing from conveyor speed and profile rate."""
    if speed_mm_s <= 0 or profile_rate_hz <= 0:
        raise ValueError("speed and profile rate must be positive")
    return speed_mm_s / profile_rate_hz


def profile_rate_scenarios(
    *, speed_mm_s: float | None = None
) -> tuple[ProfileRateScenario, ...]:
    """Return the four requested operating points, all explicitly unverified."""
    selected_speed = SELECTED_STATION.conveyor_speed_mm_s if speed_mm_s is None else speed_mm_s
    scenarios = []
    for rate_hz in (1000.0, 800.0, 500.0, 380.0):
        y_pitch_mm = profile_spacing_mm(selected_speed, rate_hz)
        scenarios.append(
            ProfileRateScenario(
                rate_hz=rate_hz,
                y_pitch_mm=y_pitch_mm,
                profiles_per_10mm=10.0 / y_pitch_mm,
            )
        )
    return tuple(scenarios)


def calculate_linear_fov_layout(
    sensor: SensorFovSpec,
    *,
    target_top_fov_mm: float,
    conveyor_width_mm: float | None = None,
    maximum_object_height_mm: float | None = None,
) -> PreliminaryLayout:
    """Interpolate datasheet FOV endpoints for a preliminary mounting layout.

    Actual mounting coordinates must use the device's factory calibration model.
    """
    belt_width = (
        SELECTED_STATION.conveyor_width_mm
        if conveyor_width_mm is None
        else conveyor_width_mm
    )
    object_height = (
        SELECTED_STATION.maximum_object_height_mm
        if maximum_object_height_mm is None
        else maximum_object_height_mm
    )
    if target_top_fov_mm <= belt_width:
        raise ValueError("target FOV must provide a positive lateral margin")
    if not sensor.fov_near_mm <= target_top_fov_mm <= sensor.fov_far_mm:
        raise ValueError("target top FOV is outside sensor FOV endpoints")
    fov_span = sensor.fov_far_mm - sensor.fov_near_mm
    top_position = (
        (target_top_fov_mm - sensor.fov_near_mm)
        * sensor.measurement_range_mm
        / fov_span
    )
    belt_position = top_position + object_height
    if belt_position > sensor.measurement_range_mm:
        raise ValueError("maximum object and belt do not fit in the measurement range")
    belt_fov = sensor.fov_near_mm + fov_span * belt_position / sensor.measurement_range_mm
    pitch = belt_fov / sensor.points_per_profile
    return PreliminaryLayout(
        sensor_name=sensor.name,
        target_top_fov_mm=target_top_fov_mm,
        lateral_margin_per_side_mm=(target_top_fov_mm - belt_width) / 2,
        top_position_in_range_mm=top_position,
        belt_position_in_range_mm=belt_position,
        mount_height_above_belt_mm=sensor.clearance_mm + belt_position,
        belt_fov_mm=belt_fov,
        belt_x_pitch_mm=pitch,
        samples_per_10mm_at_belt=10.0 / pitch,
        remaining_range_beyond_belt_mm=sensor.measurement_range_mm - belt_position,
    )


SELECTED_LAYOUT = calculate_linear_fov_layout(
    SELECTED_STATION.sensor,
    target_top_fov_mm=SELECTED_STATION.target_top_fov_mm,
    conveyor_width_mm=SELECTED_STATION.conveyor_width_mm,
    maximum_object_height_mm=SELECTED_STATION.maximum_object_height_mm,
)


def fov_width_at_height_mm(
    height_above_belt_mm: float,
    *,
    sensor: SensorFovSpec = GOCATOR_2880,
    layout: PreliminaryLayout | None = None,
) -> float:
    """Interpolate preliminary FOV at an observed height above the belt.

    This is an installation-envelope calculation, not a substitute for the
    factory calibration model delivered by the physical sensor.
    """
    selected_layout = layout
    if selected_layout is None:
        selected_layout = (
            SELECTED_LAYOUT
            if sensor is SELECTED_STATION.sensor
            else calculate_linear_fov_layout(
                sensor, target_top_fov_mm=SELECTED_STATION.target_top_fov_mm
            )
        )
    position = selected_layout.belt_position_in_range_mm - height_above_belt_mm
    if not 0.0 <= position <= sensor.measurement_range_mm:
        raise ValueError("height is outside the preliminary measurement range")
    span = sensor.fov_far_mm - sensor.fov_near_mm
    return sensor.fov_near_mm + span * position / sensor.measurement_range_mm
