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
