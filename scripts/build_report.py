"""Build the Russian engineering report from the Markdown source."""

from __future__ import annotations

import argparse
import html
import re
from collections.abc import Iterable
from pathlib import Path

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

PAGE_WIDTH, PAGE_HEIGHT = A4
AUTHOR = "Болбачан Леонид Анатольевич"
# Stable metadata timestamps and document IDs make committed PDFs reproducible.
rl_config.invariant = 1
LEFT = 18 * mm
RIGHT = 18 * mm
TOP = 18 * mm
BOTTOM = 17 * mm
CONTENT_WIDTH = PAGE_WIDTH - LEFT - RIGHT
CONTENT_HEIGHT = PAGE_HEIGHT - TOP - BOTTOM

_BREAK_BEFORE = {
    "1. Резюме решения",
    "4. Аппаратный trade study",
    "5. Финальная физическая компоновка",
    "7. Алгоритм production-контура",
    "9. Роль ML и план данных",
    "11. Ошибки и защитное поведение",
    "13. План физической валидации",
    "Источники",
}


def _first_existing(paths: Iterable[str]) -> Path:
    for path in paths:
        candidate = Path(path)
        if candidate.exists():
            return candidate
    raise RuntimeError("No Unicode TrueType font found")


def _register_fonts() -> None:
    regular = _first_existing(
        [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    bold = _first_existing(
        [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    italic = _first_existing(
        [
            "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
            str(regular),
        ]
    )
    bold_italic = _first_existing(
        [
            "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
            str(bold),
        ]
    )
    mono = _first_existing(
        [
            "/System/Library/Fonts/SFNSMono.ttf",
            "/System/Library/Fonts/Supplemental/Andale Mono.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            str(regular),
        ]
    )
    for name, path in (
        ("ReportSans", regular),
        ("ReportSans-Bold", bold),
        ("ReportSans-Italic", italic),
        ("ReportSans-BoldItalic", bold_italic),
        ("ReportMono", mono),
    ):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, path))
    pdfmetrics.registerFontFamily(
        "ReportSans",
        normal="ReportSans",
        bold="ReportSans-Bold",
        italic="ReportSans-Italic",
        boldItalic="ReportSans-BoldItalic",
    )


def _styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    navy = colors.HexColor("#17212b")
    blue = colors.HexColor("#145ea8")
    muted = colors.HexColor("#4f626d")
    return {
        "title": ParagraphStyle(
            "TitleRu",
            parent=sample["Title"],
            fontName="ReportSans-Bold",
            fontSize=22,
            leading=27,
            textColor=navy,
            alignment=TA_LEFT,
            spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "H2Ru",
            parent=sample["Heading2"],
            fontName="ReportSans-Bold",
            fontSize=15,
            leading=19,
            textColor=blue,
            spaceBefore=9,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3Ru",
            parent=sample["Heading3"],
            fontName="ReportSans-Bold",
            fontSize=11.5,
            leading=14,
            textColor=navy,
            spaceBefore=7,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "BodyRu",
            parent=sample["BodyText"],
            fontName="ReportSans",
            fontSize=8.8,
            leading=11.6,
            textColor=navy,
            alignment=TA_LEFT,
            spaceAfter=5,
            allowWidows=0,
            allowOrphans=0,
            wordWrap="CJK",
        ),
        "bullet": ParagraphStyle(
            "BulletRu",
            parent=sample["BodyText"],
            fontName="ReportSans",
            fontSize=8.6,
            leading=11.2,
            leftIndent=12,
            firstLineIndent=-7,
            spaceAfter=2.5,
            wordWrap="CJK",
        ),
        "quote": ParagraphStyle(
            "QuoteRu",
            parent=sample["BodyText"],
            fontName="ReportSans-Italic",
            fontSize=9.2,
            leading=12.5,
            leftIndent=12,
            rightIndent=8,
            borderColor=blue,
            borderWidth=0,
            borderLeft=3,
            borderPadding=7,
            backColor=colors.HexColor("#edf4fb"),
            textColor=navy,
            spaceBefore=4,
            spaceAfter=9,
            wordWrap="CJK",
        ),
        "code": ParagraphStyle(
            "Code",
            fontName="ReportMono",
            fontSize=7.2,
            leading=9.0,
            leftIndent=6,
            rightIndent=6,
            borderColor=colors.HexColor("#d7dde2"),
            borderWidth=0.5,
            borderPadding=6,
            backColor=colors.HexColor("#f6f8fa"),
            spaceBefore=4,
            spaceAfter=7,
        ),
        "caption": ParagraphStyle(
            "CaptionRu",
            parent=sample["BodyText"],
            fontName="ReportSans-Italic",
            fontSize=7.6,
            leading=9.2,
            textColor=muted,
            alignment=TA_CENTER,
            spaceAfter=7,
        ),
        "table": ParagraphStyle(
            "TableRu",
            parent=sample["BodyText"],
            fontName="ReportSans",
            fontSize=6.9,
            leading=8.4,
            wordWrap="CJK",
        ),
        "table_head": ParagraphStyle(
            "TableHeadRu",
            parent=sample["BodyText"],
            fontName="ReportSans-Bold",
            fontSize=6.9,
            leading=8.4,
            textColor=colors.white,
            wordWrap="CJK",
        ),
    }


def _inline(text: str) -> str:
    value = html.escape(text.strip())
    value = re.sub(r"`([^`]+)`", r'<font name="ReportMono">\1</font>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", value)
    value = re.sub(
        r"\[([^]]+)]\((https?://[^)]+)\)",
        r'<a href="\2" color="#145ea8">\1</a>',
        value,
    )
    return value


def _table(lines: list[str], styles: dict[str, ParagraphStyle]) -> Table:
    rows: list[list[Paragraph]] = []
    for row_index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if row_index == 1 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        style = styles["table_head"] if row_index == 0 else styles["table"]
        rows.append([Paragraph(_inline(cell), style) for cell in cells])
    column_count = max(len(row) for row in rows)
    widths = [CONTENT_WIDTH / column_count] * column_count
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#145ea8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8c3cb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7f9")]),
            ]
        )
    )
    return table


def _image_flowable(source: Path, alt: str, styles: dict[str, ParagraphStyle]):
    if source.suffix.lower() == ".svg":
        raise RuntimeError("SVG embedding is disabled; generate a portable PNG first")
    image = Image(str(source))
    scale = min(CONTENT_WIDTH / image.imageWidth, 100 * mm / image.imageHeight, 1.0)
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    return KeepTogether(
        [
            Spacer(1, 3),
            image,
            Paragraph(_inline(alt), styles["caption"]),
        ]
    )


def _parse_markdown(source: Path, styles: dict[str, ParagraphStyle]):
    lines = source.read_text(encoding="utf-8").splitlines()
    story = []
    paragraph: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if paragraph:
            story.append(Paragraph(_inline(" ".join(paragraph)), styles["body"]))
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            code: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code.append(lines[index])
                index += 1
            story.append(Preformatted("\n".join(code), styles["code"], maxLineLength=100))
            index += 1
            continue
        image_match = re.fullmatch(r"!\[([^]]*)]\(([^)]+)\)", stripped)
        if image_match:
            flush_paragraph()
            asset = (source.parent / image_match.group(2)).resolve()
            story.append(_image_flowable(asset, image_match.group(1), styles))
            index += 1
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            story.append(Paragraph(_inline(stripped[2:]), styles["title"]))
            index += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            heading = stripped[3:]
            if heading in _BREAK_BEFORE and story and not isinstance(story[-1], PageBreak):
                story.append(PageBreak())
            story.append(Paragraph(_inline(heading), styles["h2"]))
            index += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(_inline(stripped[4:]), styles["h3"]))
            index += 1
            continue
        if stripped.startswith(">"):
            flush_paragraph()
            quote: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote.append(lines[index].strip().lstrip(">").strip())
                index += 1
            story.append(Paragraph(_inline(" ".join(quote)), styles["quote"]))
            continue
        is_table = (
            stripped.startswith("|")
            and index + 1 < len(lines)
            and lines[index + 1].strip().startswith("|")
        )
        if is_table:
            flush_paragraph()
            table_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.append(_table(table_lines, styles))
            story.append(Spacer(1, 6))
            continue
        bullet_match = re.match(r"^[-*]\s+(.+)", stripped)
        number_match = re.match(r"^(\d+)\.\s+(.+)", stripped)
        if bullet_match or number_match:
            flush_paragraph()
            marker = "•" if bullet_match else f"{number_match.group(1)}."
            content = bullet_match.group(1) if bullet_match else number_match.group(2)
            story.append(Paragraph(_inline(content), styles["bullet"], bulletText=marker))
            index += 1
            continue
        paragraph.append(stripped)
        index += 1
    flush_paragraph()
    return story


def _page_decor(canvas, document) -> None:
    canvas.saveState()
    canvas.setTitle("Программно-аппаратный комплекс измерения габаритов товара")
    canvas.setAuthor(AUTHOR)
    canvas.setFont("ReportSans", 7.2)
    canvas.setFillColor(colors.HexColor("#667985"))
    canvas.drawString(LEFT, 9 * mm, "Ozon Tech × Университет Иннополис · инженерный отчёт")
    canvas.drawRightString(PAGE_WIDTH - RIGHT, 9 * mm, f"стр. {document.page}")
    canvas.setStrokeColor(colors.HexColor("#d7dde2"))
    canvas.line(LEFT, 12 * mm, PAGE_WIDTH - RIGHT, 12 * mm)
    canvas.restoreState()


def build_report(source: str | Path, output: str | Path) -> Path:
    """Render a supported Markdown subset to a selectable-text PDF."""
    _register_fonts()
    source_path = Path(source).resolve()
    output_path = Path(output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = Frame(LEFT, BOTTOM, CONTENT_WIDTH, CONTENT_HEIGHT, id="normal")
    document = BaseDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=LEFT,
        rightMargin=RIGHT,
        topMargin=TOP,
        bottomMargin=BOTTOM,
        title="Программно-аппаратный комплекс измерения габаритов товара",
        author=AUTHOR,
        subject="Ozon Tech computer vision assignment",
    )
    document.addPageTemplates(PageTemplate(id="report", frames=[frame], onPage=_page_decor))
    document.build(_parse_markdown(source_path, _styles()))
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Собрать docs/report.pdf из Markdown")
    parser.add_argument("--source", default="docs/report.md")
    parser.add_argument("--output", default="docs/report.pdf")
    args = parser.parse_args()
    build_report(args.source, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
