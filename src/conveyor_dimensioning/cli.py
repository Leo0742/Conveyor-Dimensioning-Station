"""Command-line interface for measurement, demo and synthetic benchmark."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from conveyor_dimensioning.measurement import measure_scene
from conveyor_dimensioning.wms import WMSMessage


def _measure(args: argparse.Namespace) -> int:
    source = Path(args.input)
    if source.suffix.lower() != ".npz":
        raise SystemExit("This lightweight build accepts .npz files with a points_mm array")
    with np.load(source) as archive:
        if "points_mm" not in archive:
            raise SystemExit("NPZ file must contain a points_mm array")
        result = measure_scene(archive["points_mm"], seed=args.seed)
    print(WMSMessage.from_result(args.item_id, result).model_dump_json(indent=2))
    return 0


def _demo(args: argparse.Namespace) -> int:
    from conveyor_dimensioning.demo import run_demo

    run_demo(Path(args.output_dir), seed=args.seed)
    return 0


def _benchmark(args: argparse.Namespace) -> int:
    from conveyor_dimensioning.benchmark import run_benchmark

    run_benchmark(Path(args.output_dir), seed=args.seed)
    return 0


def _sensor_benchmark(args: argparse.Namespace) -> int:
    from conveyor_dimensioning.benchmark import run_sensor_benchmark

    run_sensor_benchmark(Path(args.output_dir), seed=args.seed)
    return 0


def _monte_carlo(args: argparse.Namespace) -> int:
    from conveyor_dimensioning.monte_carlo import run_monte_carlo

    run_monte_carlo(Path(args.output_dir), count=args.count, seed=args.seed)
    return 0


def _multiframe_demo(args: argparse.Namespace) -> int:
    from conveyor_dimensioning.multiframe import run_multiframe_demo

    run_multiframe_demo(Path(args.output_dir), seed=args.seed)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Прототип измерения габаритов на конвейере")
    subparsers = parser.add_subparsers(dest="command", required=True)

    measure = subparsers.add_parser("measure", help="измерить облако points_mm из NPZ")
    measure.add_argument("input")
    measure.add_argument("--item-id", default="sample-item")
    measure.add_argument("--seed", type=int, default=0)
    measure.set_defaults(handler=_measure)

    demo = subparsers.add_parser("demo", help="создать PNG, GIF и пример WMS JSON")
    demo.add_argument("--output-dir", default="assets/demo")
    demo.add_argument("--seed", type=int, default=42)
    demo.set_defaults(handler=_demo)

    benchmark = subparsers.add_parser("benchmark", help="запустить synthetic benchmark")
    benchmark.add_argument("--output-dir", default="assets/demo")
    benchmark.add_argument("--seed", type=int, default=42)
    benchmark.set_defaults(handler=_benchmark)

    sensor = subparsers.add_parser("sensor-benchmark", help="sensor-like synthetic benchmark")
    sensor.add_argument("--output-dir", default="assets/demo")
    sensor.add_argument("--seed", type=int, default=42)
    sensor.set_defaults(handler=_sensor_benchmark)

    monte_carlo = subparsers.add_parser("monte-carlo", help="Monte Carlo synthetic benchmark")
    monte_carlo.add_argument("--output-dir", default="assets/demo")
    monte_carlo.add_argument("--count", type=int, default=500)
    monte_carlo.add_argument("--seed", type=int, default=20261017)
    monte_carlo.set_defaults(handler=_monte_carlo)

    multiframe = subparsers.add_parser("multiframe-demo", help="moving-object aggregate demo")
    multiframe.add_argument("--output-dir", default="assets/demo")
    multiframe.add_argument("--seed", type=int, default=42)
    multiframe.set_defaults(handler=_multiframe_demo)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))
