import json

import numpy as np

from conveyor_dimensioning.cli import build_parser
from conveyor_dimensioning.monte_carlo import generate_monte_carlo_cases, run_monte_carlo


def test_monte_carlo_cases_are_deterministic_and_cover_required_subsets() -> None:
    first = generate_monte_carlo_cases(24, seed=901)
    second = generate_monte_carlo_cases(24, seed=901)

    assert {case.subset for case in first} == {
        "yaw_only",
        "tilted_irregular",
        "small_object",
        "noisy_incomplete",
    }
    assert [case.reference_dimensions_mm for case in first] == [
        case.reference_dimensions_mm for case in second
    ]
    assert all(
        np.array_equal(left.points_mm, right.points_mm)
        for left, right in zip(first, second, strict=True)
    )
    assert sum(max(case.reference_dimensions_mm) <= 40 for case in first) >= 6


def test_monte_carlo_writes_complete_metrics(tmp_path) -> None:
    rows, metrics = run_monte_carlo(tmp_path, count=16, seed=902)

    assert len(rows) == 16
    assert metrics["configuration"] == "FROZEN BEFORE FINAL SEED"
    assert set(metrics["subsets"]) == {
        "yaw_only",
        "tilted_irregular",
        "small_object",
        "noisy_incomplete",
    }
    assert set(metrics["overall"]) >= {
        "scenario_count",
        "expected_valid_count",
        "correct_ok_count",
        "wrong_ok_count",
        "rejected_expected_valid_count",
        "acceptance_rate",
        "precision_among_accepted",
        "correct_measurement_rate",
        "invalid_rate",
        "expected_reject_count",
        "correctly_rejected_expected_reject_count",
        "false_ok_count",
        "synthetic_rejection_stress_false_ok_rate",
        "absolute_error_mm",
        "relative_error_percent",
    }
    assert metrics["overall"]["expected_reject_count"] == sum(
        row.expected_reject for row in rows
    )
    assert metrics["overall"]["false_ok_count"] == sum(row.false_ok for row in rows)
    assert (tmp_path / "monte_carlo.csv").exists()
    loaded = json.loads((tmp_path / "monte_carlo_metrics.json").read_text())
    assert loaded["seed"] == 902
    markdown = (tmp_path / "monte_carlo.md").read_text(encoding="utf-8")
    assert "Correct OK" in markdown
    assert "Wrong OK" in markdown
    assert "Acceptance rate" in markdown
    assert "Precision among accepted" in markdown
    assert "Correct measurement rate" in markdown


def test_monte_carlo_cli_defaults_to_at_least_500_cases() -> None:
    args = build_parser().parse_args(["monte-carlo"])

    assert args.count >= 500
