import pytest

from conveyor_dimensioning.config import MeasurementConfig
from conveyor_dimensioning.measurement import evaluate_result, measure_scene
from conveyor_dimensioning.simulation import make_scene, sample_line_profiler_shape


@pytest.mark.parametrize("shape", ["l_prism", "cylinder", "composite"])
def test_irregular_shape_runs_through_full_measurement_pipeline(shape: str) -> None:
    simulated = sample_line_profiler_shape(
        shape,
        (80.0, 60.0, 30.0),
        edge_shadow=0.05,
        visible_completeness=0.95,
        seed=100,
    )
    scene = make_scene(
        simulated.points_mm,
        plane_point_count=1200,
        plane_noise_std_mm=0.08,
        seed=101,
    )

    result = measure_scene(scene, MeasurementConfig(cluster_radius_mm=8.0), seed=102)

    assert result.status == "ok"
    assert evaluate_result(result, simulated.reference_dimensions_mm).passed
