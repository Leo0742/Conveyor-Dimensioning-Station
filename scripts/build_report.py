"""Build the Russian engineering report from the Markdown source."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from PIL import ImageChops
from reportlab import rl_config
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
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
    "9. Роль ML и план данных",
    "11. Ошибки и защитное поведение",
    "Источники",
    "Приложение. Код, воспроизведение и проверка",
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
    blue = colors.HexColor("#1f5d8f")
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
            fontSize=12,
            leading=14.5,
            textColor=navy,
            spaceBefore=7,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "h3_compact": ParagraphStyle(
            "H3CompactRu",
            parent=sample["Heading3"],
            fontName="ReportSans-Bold",
            fontSize=12,
            leading=14.5,
            textColor=navy,
            spaceBefore=5,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "BodyRu",
            parent=sample["BodyText"],
            fontName="ReportSans",
            fontSize=9.5,
            leading=12.7,
            textColor=navy,
            alignment=TA_LEFT,
            spaceAfter=5,
            allowWidows=0,
            allowOrphans=0,
            wordWrap="CJK",
        ),
        "body_compact": ParagraphStyle(
            "BodyCompactRu",
            parent=sample["BodyText"],
            fontName="ReportSans",
            fontSize=9.5,
            leading=12.7,
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
            fontSize=9.2,
            leading=12,
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
            textColor=navy,
        ),
        "figure_title": ParagraphStyle(
            "FigureTitleRu",
            parent=sample["BodyText"],
            fontName="ReportSans",
            fontSize=8.2,
            leading=10,
            textColor=navy,
            alignment=TA_CENTER,
            spaceAfter=2,
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
            textColor=navy,
            wordWrap="CJK",
        ),
    }


def _code_flowable(code: list[str], styles: dict[str, ParagraphStyle]) -> Table:
    block = Table(
        [[Preformatted("\n".join(code), styles["code"], maxLineLength=100)]],
        colWidths=[CONTENT_WIDTH],
        hAlign="CENTER",
    )
    block.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f3f5")),
                ("BOX", (0, 0), (-1, -1), 0.55, colors.HexColor("#bcc6ce")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    block.spaceBefore = 5
    block.spaceAfter = 8
    return block


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
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7edf2")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17212b")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#7790a1")),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#d2d9de")),
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


def _cover_flowable() -> Drawing:
    width = CONTENT_WIDTH
    height = CONTENT_HEIGHT
    navy = colors.HexColor("#17212b")
    blue = colors.HexColor("#1f5d8f")
    red = colors.HexColor("#cf3943")
    orange = colors.HexColor("#f2c48a")
    light = colors.HexColor("#e7edf2")
    drawing = Drawing(width, height)

    drawing.add(Rect(0, height - 57 * mm, 2.2 * mm, 40 * mm,
                     fillColor=blue, strokeColor=None))
    for offset, title_line in enumerate(
        ("Программно-аппаратный комплекс", "измерения габаритов товара", "на конвейере")
    ):
        drawing.add(String(8 * mm, height - (25 + 13 * offset) * mm, title_line,
                           fontName="ReportSans-Bold", fontSize=25, fillColor=navy))
    # Minimal engineering motif: sensor, laser, product and conveyor.
    center_x = width / 2
    y0 = 87 * mm
    drawing.add(Line(center_x - 45 * mm, y0, center_x + 45 * mm, y0,
                     strokeColor=colors.HexColor("#687983"), strokeWidth=2))
    drawing.add(Line(center_x - 40 * mm, y0 - 4 * mm, center_x + 40 * mm, y0 - 4 * mm,
                     strokeColor=light, strokeWidth=4))
    drawing.add(Rect(center_x - 14.5 * mm, y0, 29 * mm, 24 * mm,
                     fillColor=orange, strokeColor=colors.HexColor("#c38e53"), strokeWidth=0.8))
    drawing.add(Rect(center_x - 9.5 * mm, y0 + 65 * mm, 19 * mm, 12 * mm,
                     fillColor=blue, strokeColor=blue))
    drawing.add(Rect(center_x - 4.5 * mm, y0 + 61 * mm, 9 * mm, 4 * mm,
                     fillColor=blue, strokeColor=blue))
    drawing.add(Line(center_x, y0 + 61 * mm, center_x, y0,
                     strokeColor=red, strokeWidth=2.1))
    drawing.add(Line(center_x, y0 + 22 * mm, center_x, y0 + 24 * mm,
                     strokeColor=colors.white, strokeWidth=2.3))

    drawing.add(String(0, 30 * mm, AUTHOR, fontName="ReportSans-Bold",
                       fontSize=17, fillColor=navy))
    return drawing


def _add_arrow(drawing: Drawing, x1: float, y1: float, x2: float, y2: float) -> None:
    color = colors.HexColor("#687983")
    drawing.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1.1))
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 4
    drawing.add(
        Polygon(
            [
                x2,
                y2,
                x2 - size * math.cos(angle - 0.55),
                y2 - size * math.sin(angle - 0.55),
                x2 - size * math.cos(angle + 0.55),
                y2 - size * math.sin(angle + 0.55),
            ],
            fillColor=color,
            strokeColor=color,
        )
    )


def _system_diagram(styles: dict[str, ParagraphStyle], caption: str):
    width = CONTENT_WIDTH
    height = 72 * mm
    navy = colors.HexColor("#17212b")
    blue = colors.HexColor("#1f5d8f")
    light = colors.HexColor("#f1f4f6")
    drawing = Drawing(width, height)

    def box(x: float, y: float, w: float, h: float, lines: list[str], fill=colors.white) -> None:
        drawing.add(Rect(x, y, w, h, rx=3, ry=3, fillColor=fill,
                         strokeColor=blue, strokeWidth=0.9))
        total = (len(lines) - 1) * 10
        for idx, value in enumerate(lines):
            drawing.add(String(x + w / 2, y + h / 2 + total / 2 - idx * 10 - 3,
                               value, fontName="ReportSans-Bold" if idx == 0 else "ReportSans",
                               fontSize=7.8 if idx == 0 else 7.2, fillColor=navy,
                               textAnchor="middle"))

    src_x, src_w = 2 * mm, 30 * mm
    sensor_x, sensor_w = 42 * mm, 34 * mm
    edge_x, edge_w = 86 * mm, 54 * mm
    wms_x, wms_w = 150 * mm, 24 * mm
    box(src_x, 45 * mm, src_w, 12 * mm, ["WLF4FI", "событие товара"], light)
    box(src_x, 25 * mm, src_w, 12 * mm, ["DFS60", "координата Y"], light)
    box(sensor_x, 33 * mm, sensor_w, 16 * mm, ["Gocator 2880", "профили X–Z"])
    box(edge_x, 18 * mm, edge_w, 46 * mm,
        ["OnLogic K801", "калибровка", "удаление ленты", "кластеризация",
         "OBB", "проверка результата", "локальная очередь"], light)
    box(wms_x, 33 * mm, wms_w, 16 * mm, ["WMS", "JSON"])

    _add_arrow(drawing, src_x + src_w, 51 * mm, sensor_x, 44 * mm)
    _add_arrow(drawing, src_x + src_w, 31 * mm, sensor_x, 38 * mm)
    _add_arrow(drawing, sensor_x + sensor_w, 41 * mm, edge_x, 41 * mm)
    _add_arrow(drawing, edge_x + edge_w, 41 * mm, wms_x, 41 * mm)
    drawing.add(String(width / 2, 7 * mm,
                       "Измерение выполняется локально; сбой WMS не останавливает сбор профилей.",
                       fontName="ReportSans", fontSize=7.4,
                       fillColor=colors.HexColor("#5c6e78"), textAnchor="middle"))
    return KeepTogether([Spacer(1, 3), drawing, Paragraph(_inline(caption), styles["caption"])])


def _image_flowable(source: Path, alt: str, styles: dict[str, ParagraphStyle]):
    if source.name == "system_block.png":
        return _system_diagram(styles, alt)
    if source.suffix.lower() == ".svg":
        raise RuntimeError("SVG embedding is disabled; generate a portable PNG first")
    if source.name == "measurement.png":
        measurement = json.loads(
            source.with_name("example_measurement.json").read_text(encoding="utf-8")
        )
        dimensions = " × ".join(
            f"{float(measurement[field]):.1f}".replace(".", ",")
            for field in ("length_mm", "width_mm", "height_mm")
        )
        with PILImage.open(source).convert("RGB") as original:
            difference = ImageChops.difference(
                original, PILImage.new("RGB", original.size, "white")
            )
            left, _, right, bottom = difference.getbbox() or (0, 0, *original.size)
            crop_box = (
                max(0, left - 8),
                42,
                min(original.width, right + 8),
                min(original.height, bottom + 8),
            )
            cropped = original.crop(crop_box)
            buffer = BytesIO()
            cropped.save(buffer, format="PNG")
            buffer.seek(0)
        image = Image(buffer)
        scale = min(CONTENT_WIDTH / image.imageWidth, 96 * mm / image.imageHeight, 1.0)
        image.drawWidth = image.imageWidth * scale
        image.drawHeight = image.imageHeight * scale
        image.hAlign = "CENTER"
        return KeepTogether(
            [
                Spacer(1, 3),
                Paragraph(
                    f"Результат симуляции: {dimensions} мм",
                    styles["figure_title"],
                ),
                image,
                Paragraph(_inline(alt), styles["caption"]),
            ]
        )
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
    compact_section = False

    def flush_paragraph() -> None:
        if paragraph:
            style = styles["body_compact"] if compact_section else styles["body"]
            story.append(Paragraph(_inline(" ".join(paragraph)), style))
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped == "Псевдокод обработки одного товара":
            flush_paragraph()
            code_index = index + 1
            while code_index < len(lines) and not lines[code_index].strip():
                code_index += 1
            if code_index < len(lines) and lines[code_index].strip().startswith("```"):
                code: list[str] = []
                code_index += 1
                while (
                    code_index < len(lines)
                    and not lines[code_index].strip().startswith("```")
                ):
                    code.append(lines[code_index])
                    code_index += 1
                story.append(
                    KeepTogether(
                        [
                            Paragraph(_inline(stripped), styles["body"]),
                            _code_flowable(code, styles),
                        ]
                    )
                )
                index = code_index + 1
                continue
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
            story.append(_code_flowable(code, styles))
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
            story.append(_cover_flowable())
            story.append(PageBreak())
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("## "):
                index += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            heading = stripped[3:]
            if heading in _BREAK_BEFORE and story and not isinstance(story[-1], PageBreak):
                story.append(PageBreak())
            story.append(Paragraph(_inline(heading), styles["h2"]))
            compact_section = heading.startswith(("3. ", "4. "))
            index += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            style = styles["h3_compact"] if compact_section else styles["h3"]
            story.append(Paragraph(_inline(stripped[4:]), style))
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
            if number_match and number_match.group(1) == "22":
                index += 1
                while index < len(lines) and lines[index].startswith((" ", "\t")):
                    content += " " + lines[index].strip()
                    index += 1
                story.append(
                    KeepTogether(
                        [Paragraph(_inline(content), styles["bullet"], bulletText=marker)]
                    )
                )
                continue
            item = Paragraph(_inline(content), styles["bullet"], bulletText=marker)
            story.append(item)
            index += 1
            continue
        paragraph.append(stripped)
        index += 1
    flush_paragraph()
    return story


def _page_decor(canvas, document) -> None:
    canvas.saveState()
    canvas.setTitle("Программно-аппаратный комплекс измерения габаритов товара на конвейере")
    canvas.setAuthor(AUTHOR)
    if document.page == 1:
        canvas.restoreState()
        return
    canvas.setFont("ReportSans", 7.2)
    canvas.setFillColor(colors.HexColor("#667985"))
    canvas.drawString(LEFT, 9 * mm, "Ozon Tech × Университет Иннополис")
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
    frame = Frame(
        LEFT,
        BOTTOM,
        CONTENT_WIDTH,
        CONTENT_HEIGHT,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="normal",
    )
    document = BaseDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=LEFT,
        rightMargin=RIGHT,
        topMargin=TOP,
        bottomMargin=BOTTOM,
        title="Программно-аппаратный комплекс измерения габаритов товара на конвейере",
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
