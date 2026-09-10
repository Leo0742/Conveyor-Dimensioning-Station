import pytest

from conveyor_dimensioning.cli import build_parser


def test_cli_help_exposes_measure_demo_and_benchmark(capsys) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as error:
        parser.parse_args(["--help"])

    assert error.value.code == 0
    help_text = capsys.readouterr().out
    assert "measure" in help_text
    assert "demo" in help_text
    assert "benchmark" in help_text
    assert "multiframe-demo" in help_text
