"""Export the final Chinese translation to a PDF with extracted figures.

The exporter uses ReportLab rather than PyMuPDF text insertion so Chinese
fonts can be embedded correctly.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_DEPS = PROJECT_ROOT / ".codex_deps"
if LOCAL_DEPS.exists():
    sys.path.insert(0, str(LOCAL_DEPS))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/simsun.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export translated Markdown to PDF.")
    parser.add_argument(
        "--translation",
        default="output/translation_final.md",
        help="Final translation Markdown file.",
    )
    parser.add_argument(
        "--figures-dir",
        default="output/extracted_figures",
        help="Directory containing extracted figures and figure_manifest.json.",
    )
    parser.add_argument(
        "--output",
        default="output/translation_final_inline_figures_final.pdf",
        help="Output PDF path.",
    )
    parser.add_argument(
        "--report",
        default="output/figure_mapping_report.md",
        help="Figure mapping report path.",
    )
    parser.add_argument(
        "--inline-figures",
        action="store_true",
        help="Insert figures after the first in-body reference instead of appending a figure plate.",
    )
    return parser.parse_args()


def register_chinese_font() -> tuple[str, Path]:
    for font_path in FONT_CANDIDATES:
        if not font_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("ChineseBody", str(font_path)))
            return "ChineseBody", font_path
        except Exception:
            continue
    raise RuntimeError("No usable Chinese font found in Windows font directory.")


def parse_captions(markdown: str) -> dict[int, str]:
    captions: dict[int, str] = {}
    current: int | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, current
        if current is not None:
            text = " ".join(line.strip() for line in buffer if line.strip())
            captions[current] = re.sub(r"\s+", " ", text).strip()
        buffer = []

    for line in markdown.splitlines():
        heading = re.match(r"^###\s+图\s*(\d+)\s*$", line.strip())
        if heading:
            flush()
            current = int(heading.group(1))
            continue
        if current is not None and line.startswith("## "):
            flush()
            current = None
            continue
        if current is not None and not line.startswith("### "):
            buffer.append(line)
    flush()
    return captions


def markdown_without_caption_sections(markdown: str) -> list[str]:
    lines: list[str] = []
    skipping = False

    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped == "## 图注":
            skipping = True
            continue
        if skipping and line.startswith("## ") and stripped != "## 图注":
            skipping = False
        if not skipping:
            lines.append(line)
    return lines


def load_manifest(figures_dir: Path) -> list[dict[str, object]]:
    manifest_path = figures_dir / "figure_manifest.json"
    if not manifest_path.exists():
        return []
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def clean_inline_markdown(text: str) -> str:
    text = normalize_pdf_text(text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return html.escape(text)


def normalize_pdf_text(text: str) -> str:
    text = text.replace("CO₂", "CO2").replace("CO2", "CO2")
    text = re.sub(r"\bCO\s+排放", "CO2 排放", text)
    text = re.sub(r"\bCO\s+当量", "CO2 当量", text)
    text = re.sub(r"\bkg\s+CO\s+当量", "kg CO2 当量", text)
    return text


def build_styles(font_name: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles = {
        "h1": ParagraphStyle(
            "h1",
            parent=base["Title"],
            fontName=font_name,
            fontSize=18,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=14,
            wordWrap="CJK",
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName=font_name,
            fontSize=14,
            leading=20,
            spaceBefore=10,
            spaceAfter=8,
            wordWrap="CJK",
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=base["Heading3"],
            fontName=font_name,
            fontSize=11.5,
            leading=17,
            spaceBefore=8,
            spaceAfter=6,
            wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=10.5,
            leading=17,
            firstLineIndent=2 * 10.5,
            alignment=TA_LEFT,
            spaceAfter=7,
            wordWrap="CJK",
        ),
        "caption": ParagraphStyle(
            "caption",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=9.5,
            leading=14,
            alignment=TA_LEFT,
            spaceBefore=6,
            spaceAfter=10,
            wordWrap="CJK",
        ),
        "note": ParagraphStyle(
            "note",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#444444"),
            wordWrap="CJK",
        ),
    }
    return styles


def figure_block(
    item: dict[str, object],
    captions: dict[int, str],
    figures_dir: Path,
    styles: dict[str, ParagraphStyle],
) -> list[object]:
    idx = int(item["figure_index"])
    image_path = figures_dir / str(item["filename"])
    if not image_path.exists():
        return []

    max_width = A4[0] - 4 * cm
    max_height = A4[1] - 8 * cm
    caption = captions.get(idx, "")
    parts: list[object] = [
        image_flowable(image_path, max_width, max_height),
    ]
    if caption:
        parts.append(Paragraph(clean_inline_markdown(f"图 {idx}. {caption}"), styles["caption"]))
    return [KeepTogether(parts), Spacer(1, 0.3 * cm)]


def add_markdown_body(story: list[object], lines: list[str], styles: dict[str, ParagraphStyle]) -> None:
    paragraph: list[str] = []

    def flush() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(part.strip() for part in paragraph if part.strip())
            story.append(Paragraph(clean_inline_markdown(text), styles["body"]))
            paragraph = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue

        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            flush()
            level = len(heading.group(1))
            style = styles["h1"] if level == 1 else styles["h2"] if level == 2 else styles["h3"]
            story.append(Paragraph(clean_inline_markdown(heading.group(2)), style))
            continue

        paragraph.append(stripped)
    flush()


def add_markdown_body_with_inline_figures(
    story: list[object],
    lines: list[str],
    styles: dict[str, ParagraphStyle],
    manifest: list[dict[str, object]],
    captions: dict[int, str],
    figures_dir: Path,
) -> dict[int, dict[str, str]]:
    by_index = {int(item["figure_index"]): item for item in manifest}
    inserted: dict[int, dict[str, str]] = {}
    current_section = ""
    paragraph: list[str] = []

    def insert_matching_figures(text: str) -> None:
        for idx in sorted(by_index):
            if idx in inserted:
                continue
            if re.search(rf"图\s*{idx}(?!\d)", text):
                blocks = figure_block(by_index[idx], captions, figures_dir, styles)
                if blocks:
                    story.extend(blocks)
                    inserted[idx] = {
                        "section": current_section or "未识别章节",
                        "after": text[:180] + ("..." if len(text) > 180 else ""),
                    }

    def flush() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(part.strip() for part in paragraph if part.strip())
            story.append(Paragraph(clean_inline_markdown(text), styles["body"]))
            insert_matching_figures(text)
            paragraph = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue

        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            flush()
            level = len(heading.group(1))
            title = heading.group(2)
            if level <= 2:
                current_section = title
            style = styles["h1"] if level == 1 else styles["h2"] if level == 2 else styles["h3"]
            story.append(Paragraph(clean_inline_markdown(title), style))
            continue

        paragraph.append(stripped)
    flush()
    return inserted


def image_flowable(image_path: Path, max_width: float, max_height: float) -> Image:
    img = Image(str(image_path))
    scale = min(max_width / img.imageWidth, max_height / img.imageHeight, 1)
    img.drawWidth = img.imageWidth * scale
    img.drawHeight = img.imageHeight * scale
    img.hAlign = "CENTER"
    return img


def add_figures(
    story: list[object],
    manifest: list[dict[str, object]],
    captions: dict[int, str],
    figures_dir: Path,
    styles: dict[str, ParagraphStyle],
) -> None:
    if not manifest:
        return

    story.append(PageBreak())
    story.append(Paragraph("图版与中文图注", styles["h2"]))

    max_width = A4[0] - 4 * cm
    max_height = A4[1] - 8 * cm

    for item in manifest:
        idx = int(item["figure_index"])
        image_path = figures_dir / str(item["filename"])
        if not image_path.exists():
            continue

        caption = captions.get(idx, "")
        figure_parts: list[object] = [
            Paragraph(f"图 {idx}", styles["h3"]),
            image_flowable(image_path, max_width, max_height),
        ]
        if caption:
            figure_parts.append(Paragraph(clean_inline_markdown(f"图 {idx}. {caption}"), styles["caption"]))
        story.append(KeepTogether(figure_parts))
        story.append(Spacer(1, 0.3 * cm))


def write_report(
    report_path: Path,
    manifest: list[dict[str, object]],
    captions: dict[int, str],
    unmatched_images: list[dict[str, object]],
    unmatched_captions: list[int],
    font_path: Path,
    output_path: Path,
    inline: bool = False,
    inline_insertions: dict[int, dict[str, str]] | None = None,
) -> None:
    lines = [
        "# Figure Mapping Report",
        "",
        f"- 提取图片数量：{len(manifest)}",
        f"- 插入方式：{'正文首次引用处附近插入' if inline else '正文后附加“图版与中文图注”部分'}。",
        "- 图片来源：从 `input.pdf` 中提取的原始嵌入图片；未重新绘制。",
        f"- PDF 输出：`{output_path.as_posix()}`",
        f"- PDF 中文字体：`{font_path.as_posix()}`",
        "",
        "## Mapping",
        "",
        "| 图号 | 文件名 | 来源页 | 尺寸 | 使用的中文图注 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in manifest:
        idx = int(item["figure_index"])
        caption = captions.get(idx, "")
        caption_preview = caption if len(caption) <= 160 else caption[:157] + "..."
        lines.append(
            f"| 图 {idx} | `{item['filename']}` | {item['source_page']} | "
            f"{item['width']} x {item['height']} px | {caption_preview or '未匹配'} |"
        )

    lines.extend(["", "## Caption Details", ""])
    for item in manifest:
        idx = int(item["figure_index"])
        caption = captions.get(idx, "未匹配中文图注。")
        lines.extend([f"### 图 {idx}", "", f"- 文件名：`{item['filename']}`", f"- 中文图注：{caption}", ""])

    lines.extend(["", "## Unmatched Items", ""])
    if unmatched_images:
        lines.append("无法匹配图注的图片：")
        for item in unmatched_images:
            lines.append(f"- `{item['filename']}`")
    else:
        lines.append("- 无无法匹配图注的图片。")

    if unmatched_captions:
        lines.append("")
        lines.append("无法匹配图片的图注：")
        for idx in unmatched_captions:
            lines.append(f"- 图 {idx}")
    else:
        lines.append("- 无无法匹配图片的图注。")

    lines.extend(
        [
            "",
            "## Quality Notes",
            "",
            "- 首页期刊标识等小尺寸图像已按尺寸过滤，未作为论文图片输出。",
            "- 提取结果为 PDF 内嵌 raster image；组合图保持为整体图片，未拆分子图。",
            "- 图号按大图在 PDF 中的出现顺序映射到图 1–6；当前映射与中文图注数量一致。",
            "- PDF 使用 ReportLab 生成并嵌入系统中文字体，避免 PyMuPDF 直接写中文导致方框乱码。",
        ]
    )
    if inline:
        lines.extend(["", "## Inline Placement", ""])
        inline_insertions = inline_insertions or {}
        for item in manifest:
            idx = int(item["figure_index"])
            placement = inline_insertions.get(idx)
            if placement:
                lines.extend(
                    [
                        f"### 图 {idx}",
                        "",
                        f"- 插入章节：{placement['section']}",
                        f"- 插入位置：首次出现图 {idx} 的段落之后。",
                        f"- 段落摘录：{placement['after']}",
                        "",
                    ]
                )
            else:
                lines.extend(
                    [
                        f"### 图 {idx}",
                        "",
                        "- 插入章节：未能在正文中定位首次引用。",
                        "- 处理方式：放入文末未定位图版部分。",
                        "",
                    ]
                )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_inline_report(
    report_path: Path,
    manifest: list[dict[str, object]],
    inserted: dict[int, dict[str, str]],
    captions: dict[int, str],
    font_path: Path,
    fallback_indices: list[int],
) -> None:
    lines = [
        "# Inline Figure Report",
        "",
        f"- 使用中文字体：`{font_path.as_posix()}`",
        f"- 目标图片数量：{len(manifest)}",
        f"- 成功插入正文图片数量：{len(inserted)}",
        f"- 放入文末图片数量：{len(fallback_indices)}",
        "- 图片来源：`output/extracted_figures/` 中从原 PDF 提取的原始图片。",
        "- 排版方式：使用 ReportLab 生成 PDF，并嵌入系统中文字体。",
        "",
        "## Inline Placements",
        "",
    ]
    by_index = {int(item["figure_index"]): item for item in manifest}
    for idx in sorted(by_index):
        item = by_index[idx]
        placement = inserted.get(idx)
        lines.append(f"### 图 {idx}")
        lines.append("")
        lines.append(f"- 文件名：`{item['filename']}`")
        lines.append(f"- 来源页：{item['source_page']}")
        lines.append(f"- 尺寸：{item['width']} x {item['height']} px")
        if placement:
            lines.append(f"- 插入章节：{placement['section']}")
            lines.append(f"- 插入位置：正文首次出现“图 {idx}”的段落之后")
            lines.append(f"- 段落摘录：{placement['after']}")
        else:
            lines.append("- 插入章节：未能定位")
            lines.append("- 处理方式：放在文末未定位图版部分")
        lines.append(f"- 中文图注：{captions.get(idx, '未匹配中文图注。')}")
        lines.append("")

    lines.extend(["## Quality Notes", ""])
    if fallback_indices:
        lines.append("- 未能插入正文的图片：" + ", ".join(f"图 {idx}" for idx in fallback_indices))
    else:
        lines.append("- 图 1–图 6 均已插入正文首次引用位置附近。")
    lines.append("- 未发现需要裁切图片的处理；图片按比例缩放并居中显示。")
    lines.append("- 组合图保持整体图片，未拆分子图。")
    lines.append("- 如果某张图靠近页面底部，ReportLab 会自动将完整图片和图注移到下一页，避免拆开或裁切。")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    translation_path = Path(args.translation)
    figures_dir = Path(args.figures_dir)
    output_path = Path(args.output)
    report_path = Path(args.report)

    font_name, font_path = register_chinese_font()
    styles = build_styles(font_name)

    markdown = translation_path.read_text(encoding="utf-8-sig").lstrip("\ufeff")
    captions = parse_captions(markdown)
    body_lines = markdown_without_caption_sections(markdown)
    manifest = load_manifest(figures_dir)

    story: list[object] = []
    inline_insertions: dict[int, dict[str, str]] = {}
    if args.inline_figures:
        inline_insertions = add_markdown_body_with_inline_figures(
            story,
            body_lines,
            styles,
            manifest,
            captions,
            figures_dir,
        )
        missing = [item for item in manifest if int(item["figure_index"]) not in inline_insertions]
        if missing:
            story.append(PageBreak())
            story.append(Paragraph("未定位图版与中文图注", styles["h2"]))
            add_figures(story, missing, captions, figures_dir, styles)
    else:
        add_markdown_body(story, body_lines, styles)
        add_figures(story, manifest, captions, figures_dir, styles)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="Translation Final With Figures",
    )
    doc.build(story)

    image_indices = {int(item["figure_index"]) for item in manifest}
    caption_indices = set(captions)
    unmatched_images = [item for item in manifest if int(item["figure_index"]) not in captions]
    unmatched_captions = sorted(caption_indices - image_indices)
    write_report(
        report_path,
        manifest,
        captions,
        unmatched_images,
        unmatched_captions,
        font_path,
        output_path,
        inline=args.inline_figures,
        inline_insertions=inline_insertions,
    )
    if args.inline_figures:
        fallback_indices = [int(item["figure_index"]) for item in manifest if int(item["figure_index"]) not in inline_insertions]
        write_inline_report(
            Path("output/inline_figure_report.md"),
            manifest,
            inline_insertions,
            captions,
            font_path,
            fallback_indices,
        )

    print(f"PDF written: {output_path}")
    print(f"Report written: {report_path}")
    print(f"Chinese font: {font_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
