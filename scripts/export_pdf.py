"""Export the final Chinese translation to a PDF with extracted figures.

The exporter uses ReportLab rather than PyMuPDF text insertion so Chinese
fonts can be embedded correctly.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
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

WINDOWS_FILENAME_REPLACEMENTS = str.maketrans({
    "\\": "_",
    "/": "_",
    ":": "_",
    "*": "_",
    "?": "_",
    '"': "",
    "<": "_",
    ">": "_",
    "|": "_",
    "：": "_",
    "—": "_",
    "–": "_",
    "-": "_",
    "／": "_",
})


def contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def clean_title_candidate(text: str) -> str:
    text = html.unescape(text).strip()
    text = re.sub(r"^#{1,6}\s*", "", text)
    text = re.sub(r"^[-*+\d.)、\s]+", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(
        r"^(?:中文)?(?:文章|论文)?(?:题目|标题)(?:翻译结果)?\s*[:：]\s*",
        "",
        text,
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip(" \t\r\n-—–_：:;；。")


def extract_chinese_title(markdown: str) -> str | None:
    lines = markdown.splitlines()

    for index, line in enumerate(lines):
        heading = clean_title_candidate(line)
        if "题目与作者" not in heading:
            continue
        for candidate_line in lines[index + 1 :]:
            if candidate_line.strip().startswith("#"):
                break
            candidate = clean_title_candidate(candidate_line)
            if not candidate:
                continue
            if contains_chinese(candidate) and "作者" not in candidate:
                return candidate
        break

    for index, line in enumerate(lines):
        candidate = clean_title_candidate(line)
        if not candidate:
            continue
        if "文章标题翻译结果" in candidate or ("标题" in candidate and "翻译" in candidate):
            if contains_chinese(candidate) and not candidate.endswith(("标题翻译", "翻译结果")):
                return candidate
            for following_line in lines[index + 1 : index + 5]:
                following = clean_title_candidate(following_line)
                if following and contains_chinese(following):
                    return following

    for line in lines:
        candidate = clean_title_candidate(line)
        if candidate.startswith("#"):
            candidate = clean_title_candidate(candidate)
        if contains_chinese(candidate) and len(candidate) >= 6 and not candidate.startswith("图"):
            return candidate

    return None


def make_safe_chinese_filename_stem(title: str) -> str:
    safe = clean_title_candidate(title).translate(WINDOWS_FILENAME_REPLACEMENTS)
    safe = re.sub(r"\s+", "", safe)
    safe = re.sub(r"_+", "_", safe)
    return safe.strip(" ._")


def make_safe_chinese_filename(title: str) -> str:
    safe_stem = make_safe_chinese_filename_stem(title)
    if not safe_stem:
        return ""
    return f"{safe_stem[:60]}.pdf"


def make_unique_output_path(output_dir: Path, filename: str, fixed_output_path: Path) -> Path:
    base = Path(filename).stem
    suffix = Path(filename).suffix or ".pdf"
    candidate = output_dir / f"{base}{suffix}"
    fixed_resolved = fixed_output_path.resolve()
    counter = 1
    while candidate.exists() or candidate.resolve() == fixed_resolved:
        candidate = output_dir / f"{base}_{counter}{suffix}"
        counter += 1
    return candidate


def create_title_named_pdf(
    translation_path: Path,
    markdown: str,
    fixed_output_path: Path,
) -> dict[str, object]:
    info: dict[str, object] = {
        "path": None,
        "filename": None,
        "title": None,
        "truncated": False,
        "error": None,
    }
    try:
        title = extract_chinese_title(markdown)
        if not title:
            info["error"] = "未能从 translation_final.md 中识别中文标题。"
            return info

        filename = make_safe_chinese_filename(title)
        if not filename:
            info["error"] = "中文标题无法转换为有效的 Windows 文件名。"
            info["title"] = title
            return info

        safe_title = make_safe_chinese_filename_stem(title)
        info["title"] = title
        info["filename"] = filename
        info["truncated"] = len(safe_title) > 60

        title_output_path = make_unique_output_path(fixed_output_path.parent, filename, fixed_output_path)
        shutil.copy2(fixed_output_path, title_output_path)
        info["path"] = title_output_path
        info["filename"] = title_output_path.name
    except Exception as exc:
        info["error"] = f"生成中文标题 PDF 文件名失败：{exc}"
    return info


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
