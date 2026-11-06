"""
format_validator.py – Kiểm tra thể thức văn bản & cấu trúc giáo án.

- Kiểm tra khổ giấy, căn lề (NĐ 30/2020)
- Kiểm tra font chữ, cỡ chữ
- Kiểm tra cấu trúc đề mục theo Công văn 5512
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from docx import Document
from docx.shared import Pt, Cm, Mm, Emu
from docx.oxml.ns import qn
from lxml import etree

from .constants import (
    ErrorType,
    PAPER_A4_WIDTH_MM, PAPER_A4_HEIGHT_MM,
    MARGIN_LEFT_MIN_CM, MARGIN_LEFT_MAX_CM,
    MARGIN_RIGHT_MIN_CM, MARGIN_RIGHT_MAX_CM,
    MARGIN_TOP_MIN_CM, MARGIN_TOP_MAX_CM,
    MARGIN_BOTTOM_MIN_CM, MARGIN_BOTTOM_MAX_CM,
    REQUIRED_FONT_NAME, REQUIRED_FONT_SIZES,
    CM_TO_EMU, PT_TO_EMU, MM_TO_EMU,
    CV5512_REQUIRED_SECTIONS,
)


# ──────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────

@dataclass
class FormatError:
    """Một lỗi về thể thức / cấu trúc."""
    error_type: ErrorType
    message: str
    detail: str = ""


@dataclass
class FormatReport:
    """Báo cáo tổng hợp kiểm tra thể thức."""
    errors: list[FormatError] = field(default_factory=list)
    paper_ok: bool = True
    margins_ok: bool = True
    font_ok: bool = True
    structure_ok: bool = True

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def total_errors(self) -> int:
        return len(self.errors)


# ──────────────────────────────────────────────
# Tiện ích chuyển đổi
# ──────────────────────────────────────────────

def emu_to_cm(emu: int) -> float:
    """Chuyển EMU sang cm."""
    return round(emu / CM_TO_EMU, 2) if emu else 0.0

def emu_to_mm(emu: int) -> float:
    """Chuyển EMU sang mm."""
    return round(emu / MM_TO_EMU, 1) if emu else 0.0

def emu_to_pt(emu: int) -> float:
    """Chuyển EMU sang pt."""
    return round(emu / PT_TO_EMU, 1) if emu else 0.0


# ──────────────────────────────────────────────
# Hàm lấy thông tin page setup từ XML
# ──────────────────────────────────────────────

def _get_page_setup(doc: Document) -> dict:
    """Trích thông tin page setup (khổ giấy, lề) từ section cuối cùng."""
    section = doc.sections[-1] if doc.sections else None
    if section is None:
        return {}

    info = {}
    # Khổ giấy
    info['page_width_mm'] = emu_to_mm(section.page_width) if section.page_width else None
    info['page_height_mm'] = emu_to_mm(section.page_height) if section.page_height else None

    # Căn lề
    info['left_cm'] = emu_to_cm(section.left_margin) if section.left_margin else None
    info['right_cm'] = emu_to_cm(section.right_margin) if section.right_margin else None
    info['top_cm'] = emu_to_cm(section.top_margin) if section.top_margin else None
    info['bottom_cm'] = emu_to_cm(section.bottom_margin) if section.bottom_margin else None

    return info


# ──────────────────────────────────────────────
# Kiểm tra khổ giấy & lề
# ──────────────────────────────────────────────

def check_page_setup(doc: Document) -> list[FormatError]:
    """Kiểm tra khổ giấy A4 và căn lề chuẩn."""
    errors: list[FormatError] = []
    info = _get_page_setup(doc)

    # Kiểm tra khổ giấy
    w = info.get('page_width_mm')
    h = info.get('page_height_mm')
    if w is not None and h is not None:
        # Cho phép sai số 2mm
        if not (abs(w - PAPER_A4_WIDTH_MM) <= 2 and abs(h - PAPER_A4_HEIGHT_MM) <= 2):
            # Kiểm tra chiều ngang (landscape)
            if not (abs(w - PAPER_A4_HEIGHT_MM) <= 2 and abs(h - PAPER_A4_WIDTH_MM) <= 2):
                errors.append(FormatError(
                    error_type=ErrorType.PAPER_SIZE,
                    message=f"Khổ giấy không phải A4 (hiện tại: {w}×{h} mm, chuẩn: {PAPER_A4_WIDTH_MM}×{PAPER_A4_HEIGHT_MM} mm)",
                ))

    # Kiểm tra lề trái
    left = info.get('left_cm')
    if left is not None:
        if not (MARGIN_LEFT_MIN_CM <= left <= MARGIN_LEFT_MAX_CM):
            errors.append(FormatError(
                error_type=ErrorType.MARGIN,
                message=f"Lề trái = {left} cm (chuẩn: {MARGIN_LEFT_MIN_CM} – {MARGIN_LEFT_MAX_CM} cm)",
                detail=f"Giá trị hiện tại: {left} cm",
            ))

    # Kiểm tra lề phải
    right = info.get('right_cm')
    if right is not None:
        if not (MARGIN_RIGHT_MIN_CM <= right <= MARGIN_RIGHT_MAX_CM):
            errors.append(FormatError(
                error_type=ErrorType.MARGIN,
                message=f"Lề phải = {right} cm (chuẩn: {MARGIN_RIGHT_MIN_CM} – {MARGIN_RIGHT_MAX_CM} cm)",
                detail=f"Giá trị hiện tại: {right} cm",
            ))

    # Kiểm tra lề trên
    top = info.get('top_cm')
    if top is not None:
        if not (MARGIN_TOP_MIN_CM <= top <= MARGIN_TOP_MAX_CM):
            errors.append(FormatError(
                error_type=ErrorType.MARGIN,
                message=f"Lề trên = {top} cm (chuẩn: {MARGIN_TOP_MIN_CM} – {MARGIN_TOP_MAX_CM} cm)",
                detail=f"Giá trị hiện tại: {top} cm",
            ))

    # Kiểm tra lề dưới
    bottom = info.get('bottom_cm')
    if bottom is not None:
        if not (MARGIN_BOTTOM_MIN_CM <= bottom <= MARGIN_BOTTOM_MAX_CM):
            errors.append(FormatError(
                error_type=ErrorType.MARGIN,
                message=f"Lề dưới = {bottom} cm (chuẩn: {MARGIN_BOTTOM_MIN_CM} – {MARGIN_BOTTOM_MAX_CM} cm)",
                detail=f"Giá trị hiện tại: {bottom} cm",
            ))

    return errors


# ──────────────────────────────────────────────
# Kiểm tra Font & Cỡ chữ
# ──────────────────────────────────────────────

def _get_effective_font_name(run) -> Optional[str]:
    """Lấy font name thực tế của một Run (kể cả kế thừa từ Style)."""
    # Kiểm tra trực tiếp trên run
    if run.font.name:
        return run.font.name

    # Kiểm tra trong run XML (rPr/rFonts)
    rpr = run._element.find(qn('w:rPr'))
    if rpr is not None:
        rfonts = rpr.find(qn('w:rFonts'))
        if rfonts is not None:
            for attr in ['w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia']:
                val = rfonts.get(qn(attr))
                if val:
                    return val

    # Kiểm tra style của paragraph
    try:
        style = run._element.getparent()
        if style is not None:
            ppr = style.find(qn('w:pPr'))
            if ppr is not None:
                rpr_style = ppr.find(qn('w:rPr'))
                if rpr_style is not None:
                    rfonts = rpr_style.find(qn('w:rFonts'))
                    if rfonts is not None:
                        for attr in ['w:ascii', 'w:hAnsi']:
                            val = rfonts.get(qn(attr))
                            if val:
                                return val
    except Exception:
        pass

    return None


def _get_effective_font_size_pt(run) -> Optional[float]:
    """Lấy cỡ chữ (pt) thực tế của một Run."""
    if run.font.size is not None:
        return emu_to_pt(run.font.size)

    # Kiểm tra trong XML
    rpr = run._element.find(qn('w:rPr'))
    if rpr is not None:
        sz = rpr.find(qn('w:sz'))
        if sz is not None:
            val = sz.get(qn('w:val'))
            if val:
                return int(val) / 2  # w:sz tính bằng half-point

    return None


def check_fonts(doc: Document) -> list[FormatError]:
    """Kiểm tra font chữ và cỡ chữ trong toàn bộ document."""
    errors: list[FormatError] = []
    wrong_font_count = 0
    wrong_size_count = 0
    wrong_font_samples: list[str] = []
    wrong_size_samples: list[str] = []

    def _check_runs_in_paragraphs(paragraphs, location_prefix: str = ""):
        nonlocal wrong_font_count, wrong_size_count
        for para in paragraphs:
            for run in para.runs:
                text = run.text.strip()
                if not text:
                    continue

                # Kiểm tra font
                font_name = _get_effective_font_name(run)
                if font_name and font_name != REQUIRED_FONT_NAME:
                    wrong_font_count += 1
                    if len(wrong_font_samples) < 5:
                        snippet = text[:30] + ('...' if len(text) > 30 else '')
                        wrong_font_samples.append(
                            f'"{snippet}" → font: {font_name}'
                        )

                # Kiểm tra cỡ chữ
                size_pt = _get_effective_font_size_pt(run)
                if size_pt is not None and size_pt not in REQUIRED_FONT_SIZES:
                    wrong_size_count += 1
                    if len(wrong_size_samples) < 5:
                        snippet = text[:30] + ('...' if len(text) > 30 else '')
                        wrong_size_samples.append(
                            f'"{snippet}" → cỡ: {size_pt}pt'
                        )

    # Kiểm tra paragraphs thường
    _check_runs_in_paragraphs(doc.paragraphs)

    # Kiểm tra trong tables (đệ quy)
    def _check_table(table):
        for row in table.rows:
            for cell in row.cells:
                _check_runs_in_paragraphs(cell.paragraphs, "bảng")
                # Bảng lồng nhau
                for nested_table in cell.tables:
                    _check_table(nested_table)

    for table in doc.tables:
        _check_table(table)

    # Tạo lỗi
    if wrong_font_count > 0:
        detail_lines = '\n'.join(f'  • {s}' for s in wrong_font_samples)
        errors.append(FormatError(
            error_type=ErrorType.FONT,
            message=f"Có {wrong_font_count} đoạn văn bản KHÔNG dùng font {REQUIRED_FONT_NAME}",
            detail=f"Ví dụ:\n{detail_lines}",
        ))

    if wrong_size_count > 0:
        sizes_str = ', '.join(str(s) for s in sorted(REQUIRED_FONT_SIZES))
        detail_lines = '\n'.join(f'  • {s}' for s in wrong_size_samples)
        errors.append(FormatError(
            error_type=ErrorType.FONT_SIZE,
            message=f"Có {wrong_size_count} đoạn văn bản KHÔNG dùng cỡ chữ {sizes_str}pt",
            detail=f"Ví dụ:\n{detail_lines}",
        ))

    return errors


# ──────────────────────────────────────────────
# Kiểm tra cấu trúc Giáo án (CV 5512)
# ──────────────────────────────────────────────

def _collect_all_text(doc: Document) -> list[str]:
    """Thu thập toàn bộ text từ paragraphs + tables (đệ quy)."""
    lines: list[str] = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)

    def _collect_from_table(table):
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    text = para.text.strip()
                    if text:
                        lines.append(text)
                for nested in cell.tables:
                    _collect_from_table(nested)

    for table in doc.tables:
        _collect_from_table(table)

    return lines


def check_structure_cv5512(doc: Document) -> list[FormatError]:
    """Kiểm tra sự tồn tại của các đề mục bắt buộc theo CV 5512."""
    errors: list[FormatError] = []
    all_text = _collect_all_text(doc)
    full_text = '\n'.join(all_text)

    def _section_exists(patterns: list[str]) -> bool:
        for pattern in patterns:
            if re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE):
                return True
        return False

    for section in CV5512_REQUIRED_SECTIONS:
        if not _section_exists(section['patterns']):
            errors.append(FormatError(
                error_type=ErrorType.STRUCTURE,
                message=f"Thiếu đề mục: {section['label']}",
                detail=f"Không tìm thấy đề mục «{section['label']}» trong giáo án. "
                        f"Theo Công văn 5512/BGDĐT-GDTrH, đây là đề mục bắt buộc.",
            ))
        else:
            # Kiểm tra các mục con
            for sub in section.get('subsections', []):
                if not _section_exists(sub['patterns']):
                    errors.append(FormatError(
                        error_type=ErrorType.STRUCTURE,
                        message=f"Thiếu đề mục con: {sub['label']} (thuộc {section['label']})",
                        detail=f"Không tìm thấy «{sub['label']}» bên trong mục «{section['label']}».",
                    ))

    return errors


# ──────────────────────────────────────────────
# API TỔNG HỢP
# ──────────────────────────────────────────────

class FormatValidator:
    """Kiểm tra toàn bộ thể thức & cấu trúc văn bản."""

    def __init__(self):
        pass

    def validate(self, doc: Document) -> FormatReport:
        """Chạy toàn bộ kiểm tra, trả về FormatReport."""
        report = FormatReport()

        # 1. Khổ giấy & Lề
        page_errors = check_page_setup(doc)
        if page_errors:
            report.paper_ok = False
            report.margins_ok = False
            report.errors.extend(page_errors)

        # 2. Font & Cỡ chữ
        font_errors = check_fonts(doc)
        if font_errors:
            report.font_ok = False
            report.errors.extend(font_errors)

        # 3. Cấu trúc CV 5512
        structure_errors = check_structure_cv5512(doc)
        if structure_errors:
            report.structure_ok = False
            report.errors.extend(structure_errors)

        return report

