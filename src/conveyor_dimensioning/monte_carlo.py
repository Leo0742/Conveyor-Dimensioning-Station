"""Frozen, deterministic Monte Carlo evaluation on sensor-like synthetic clouds."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from conveyor_dimensioning.benchmark import (
    BenchmarkCase,
    BenchmarkRow,
    _evaluate_case,
    summarize_rows,
)
from conveyor_dimensioning.simulation import (
    LineProfilerConfig,
    make_scene,
    sample_line_profiler_shape,
)

DEVELOPMENT_SEED = 1337
FINAL_EVALUATION_SEED = 20261017
FROZEN_CONFIGURATION_LABEL = "FROZEN BEFORE FINAL SEED"
SUBSETS = ("yaw_only", "tilted_irregular", "small_object", "noisy_incomplete")


def _sample_dimensions(rng: np.random.Generator, *, small: bool) -> tuple[float, float, float]:
    if small:
        values = rng.uniform(10.0, 40.0, 3)
    else:
        values = np.array(
            [rng.uniform(40.0, 400.0), rng.uniform(30.0, 300.0), rng.uniform(10.0, 300.0)]
        )
    ordered = np.sort(values)[::-1]
    ordered[0] = min(ordered[0], 400.0)
    ordered[1:] = np.minimum(ordered[1:], 300.0)
    return tuple(float(value) for value in ordered)


def generate_monte_carlo_cases(count: int, *, seed: int) -> list[BenchmarkCase]:
    """Generate cases without exposing reference metadata to runtime configuration."""
    if count < 1:
        raise ValueError("count must be positive")
    rng = np.random.default_rng(seed)
    cases: list[BenchmarkCase] = []
    shape_options = np.array(["box", "l_prism", "cylinder", "composite"])
    for index in range(count):
        subset = SUBSETS[index % len(SUBSETS)]
        small = subset == "small_object"
        dimensions = _sample_dimensions(rng, small=small)
        shape = "box" if subset in {"yaw_only", "small_object"} else str(rng.choice(shape_options))
        yaw = float(rng.uniform(0.0, 90.0))
        if subset == "tilted_irregular":
            rotation = (float(rng.uniform(-7.0, 7.0)), float(rng.uniform(-7.0, 7.0)), yaw)
        else:
            rotation = (0.0, 0.0, yaw)
        noisy = subset == "noisy_incomplete"
        noise = float(rng.uniform(0.25, 0.7) if noisy else rng.uniform(0.05, 0.25))
        dropout = float(rng.uniform(0.20, 0.55) if noisy else rng.uniform(0.0, 0.15))
        completeness = float(rng.uniform(0.35, 0.75) if noisy else rng.uniform(0.80, 1.0))
        edge_shadow = float(rng.uniform(0.35, 0.75) if noisy else rng.uniform(0.05, 0.35))
        expected_reject = noisy and index % 20 == 3
        if expected_reject:
            completeness = 0.05
            dropout = 0.95
        missing_profile_probability = float(
            0.97
            if expected_reject
            else (rng.uniform(0.12, 0.35) if noisy else rng.uniform(0.0, 0.04))
        )
        footprint = max(dimensions[:2]) / 2
        lateral_limit = max(0.0, 300.0 - min(footprint, 290.0))
        center_x = float(rng.uniform(-lateral_limit, lateral_limit))
        product = sample_line_profiler_shape(
            shape,
            dimensions,
            config=LineProfilerConfig(
                profile_rate_hz=1000.0,
                missing_profile_probability=missing_profile_probability,
            ),
            center_xy_mm=(center_x, 0.0),
            rotation_deg=rotation,
            visible_completeness=completeness,
            edge_shadow=edge_shadow,
            noise_std_mm=noise,
            dropout=dropout,
            seed=seed * 1009 + index,
        )
        scene = make_scene(
            product.points_mm,
            plane_point_count=1200,
            plane_noise_std_mm=0.12,
            seed=seed * 1013 + index,
        )
        cases.append(
            BenchmarkCase(
                scenario=f"mc_{index:04d}_{shape}",
                points_mm=scene,
                reference_dimensions_mm=product.reference_dimensions_mm,
                subset=subset,
                expected_reject=expected_reject,
            )
        )
    return cases


def run_monte_carlo(
    output_dir: str | Path, *, count: int = 500, seed: int = FINAL_EVALUATION_SEED
) -> tuple[list[BenchmarkRow], dict[str, object]]:
    """Run the frozen evaluation and save rows plus overall/subset metrics."""
    cases = generate_monte_carlo_cases(count, seed=seed)
    rows = [
        _evaluate_case(
            case,
            evidence_type=f"MONTE CARLO SYNTHETIC | {case.subset}",
            seed=seed + index,
        )
        for index, case in enumerate(cases)
    ]
    metrics: dict[str, object] = {
        "seed": seed,
        "development_seed": DEVELOPMENT_SEED,
        "configuration": FROZEN_CONFIGURATION_LABEL,
        "overall": summarize_rows(rows),
        "subsets": {
            subset: summarize_rows([row for row in rows if row.subset == subset])
            for subset in SUBSETS
        },
    }
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / "monte_carlo.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(asdict(rows[0])), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    (destination / "monte_carlo_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# MONTE CARLO SYNTHETIC",
        "",
        "> Проверяет геометрию на упрощённых синтетических данных линейного "
        "профилометра; не измеряет "
        "абсолютную точность физической станции.",
        "",
        f"Seed: {seed}; cases: {count}; configuration: {FROZEN_CONFIGURATION_LABEL}.",
        "",
        "| Поднабор | Total | Expected-valid | Expected-reject | Correct OK | Wrong OK | "
        "Rejected valid | Acceptance rate | Precision among accepted | "
        "Correct measurement rate | Reject correct / false accepted |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for subset in SUBSETS:
        summary = metrics["subsets"][subset]
        lines.append(
            f"| {subset} | {summary['scenario_count']} | {summary['expected_valid_count']} | "
            f"{summary['expected_reject_count']} | {summary['correct_ok_count']} | "
            f"{summary['wrong_ok_count']} | {summary['rejected_expected_valid_count']} | "
            f"{summary['acceptance_rate']:.1%} | "
            f"{summary['precision_among_accepted']:.1%} | "
            f"{summary['correct_measurement_rate']:.1%} | "
            f"{summary['correctly_rejected_expected_reject_count']} / "
            f"{summary['false_ok_count']} |"
        )
    overall = metrics["overall"]
    lines.append(
        f"| **Итого** | **{overall['scenario_count']}** | "
        f"**{overall['expected_valid_count']}** | **{overall['expected_reject_count']}** | "
        f"**{overall['correct_ok_count']}** | **{overall['wrong_ok_count']}** | "
        f"**{overall['rejected_expected_valid_count']}** | "
        f"**{overall['acceptance_rate']:.1%}** | "
        f"**{overall['precision_among_accepted']:.1%}** | "
        f"**{overall['correct_measurement_rate']:.1%}** | "
        f"**{overall['correctly_rejected_expected_reject_count']} / "
        f"{overall['false_ok_count']}** |"
    )
    lines.extend(
        [
            "",
            "Reject stress — искусственный тест защитной отбраковки, а не оценка "
            "частоты ошибок физической станции.",
        ]
    )
    (destination / "monte_carlo.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows, metrics
