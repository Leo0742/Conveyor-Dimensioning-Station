from pathlib import Path

from pypdf import PdfReader

from scripts.build_report import build_report


def test_report_builds_as_selectable_russian_pdf(tmp_path: Path) -> None:
    source = tmp_path / "report.md"
    source.write_text(
        "# Проверка отчёта\n\n## Раздел\n\nРусский `z_top≈267 мм` выбираемый текст.\n",
        encoding="utf-8",
    )
    output = tmp_path / "report.pdf"

    build_report(source, output)

    assert output.read_bytes().startswith(b"%PDF")
    reader = PdfReader(output)
    assert len(reader.pages) == 2
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "z_top≈267 мм" in extracted
    assert not {"■", "�"} & set(extracted)
    assert reader.metadata.title == (
        "Программно-аппаратный комплекс измерения габаритов товара на конвейере"
    )
    assert reader.metadata.author == "Болбачан Леонид Анатольевич"


def test_full_report_has_expected_title_and_page_range(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    output = tmp_path / "full.pdf"

    build_report(root / "docs/report.md", output)

    reader = PdfReader(output)
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    normalized = " ".join(extracted.split())
    assert 12 <= len(reader.pages) <= 18
    assert "Gocator 2880" in extracted
    assert "Результат симуляции" in extracted
    assert "120,8 × 80,7 × 46,0 мм" in extracted
    assert "не устанавливают абсолютную точность физической станции" in normalized
    assert "Болбачан Леонид Анатольевич" in extracted
    assert "2026" in extracted
    assert not {"■", "�"} & set(extracted)
    assert reader.metadata.author == "Болбачан Леонид Анатольевич"


def test_report_build_is_byte_for_byte_reproducible(tmp_path: Path) -> None:
    source = tmp_path / "report.md"
    source.write_text("# Детерминированный отчёт\n", encoding="utf-8")
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"

    build_report(source, first)
    build_report(source, second)

    assert first.read_bytes() == second.read_bytes()
