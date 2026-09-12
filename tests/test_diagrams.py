import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from scripts.generate_diagrams import generate_all


def test_diagram_generator_writes_valid_consistent_svg_files(tmp_path) -> None:
    generated = generate_all(tmp_path)

    assert {path.name for path in generated} == {
        "layout_side.svg",
        "layout_top.svg",
        "system_block.svg",
        "layout_side.png",
        "layout_top.png",
        "system_block.png",
    }
    for path in [candidate for candidate in generated if candidate.suffix == ".svg"]:
        root = ET.parse(path).getroot()
        assert root.tag.endswith("svg")
        assert root.attrib["viewBox"]
    for path in [candidate for candidate in generated if candidate.suffix == ".png"]:
        with Image.open(path) as image:
            assert image.width >= 2000
            assert image.height >= 1200
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in generated
        if path.suffix == ".svg"
    )
    assert "Gocator 2880" in combined
    assert "917 мм" in combined
    assert "680 мм" in combined
    assert "40 мм" in combined
    assert "расчётная высота" in combined
    assert "843 мм" not in combined
    assert "600 мм на Z=300" not in combined
    assert "1 м/с" in combined

    side = (tmp_path / "layout_side.svg").read_text(encoding="utf-8")
    assert "Один фиксированный профиль X-Z" in side
    assert "700 мм — путь товара" in side
    assert "SICK WLF4FI" in side
    assert "250 мм" in side
    assert "SICK DFS60" in side


def test_report_embeds_portable_png_diagrams_only() -> None:
    report = (Path(__file__).parents[1] / "docs/report.md").read_text(encoding="utf-8")

    assert "assets/diagrams/layout_side.png" in report
    assert "assets/diagrams/layout_top.png" in report
    assert "assets/diagrams/system_block.png" in report
    assert ".svg" not in report
