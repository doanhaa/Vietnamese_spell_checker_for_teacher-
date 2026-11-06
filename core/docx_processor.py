"""
docx_processor.py – Xử lý file .docx: bôi đỏ lỗi & chèn báo cáo.

Kỹ thuật cốt lõi:
  - Split Run ở cấp XML (lxml) để giữ nguyên định dạng gốc.
  - Duyệt đệ quy paragraphs + tables (kể cả bảng lồng nhau).
  - Chèn khung báo cáo lỗi thể thức ở đầu trang 1.

KHÔNG BAO GIỜ gán lại paragraph.text = ... 
"""

from __future__ import annotations

import copy
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from docx import Document
from docx.shared import Pt, RGBColor, Cm, Inches
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn, nsmap
from lxml import etree

from .spell_checker import VietnameseSpellChecker, SpellError
from .format_validator import FormatValidator, FormatReport
from .constants import ErrorType


# ──────────────────────────────────────────────
# Tiện ích XML
# ──────────────────────────────────────────────

WORD_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def _make_rpr_element() -> OxmlElement:
    """Tạo element <w:rPr> rỗng."""
    return OxmlElement('w:rPr')


def _clone_rpr(source_run_element) -> Optional[OxmlElement]:
    """Clone <w:rPr> từ một <w:r> element. Trả về None nếu không có."""
    rpr = source_run_element.find(qn('w:rPr'))
    if rpr is not None:
        return copy.deepcopy(rpr)
    return None


def _make_run_element(text: str, rpr: Optional[OxmlElement] = None,
                      preserve_space: bool = True) -> OxmlElement:
    """Tạo một <w:r> element mới với text và rPr cho trước."""
    r = OxmlElement('w:r')
    if rpr is not None:
        r.append(rpr)
    t = OxmlElement('w:t')
    t.text = text
    if preserve_space:
        t.set(qn('xml:space'), 'preserve')
    r.append(t)
    return r


def _get_run_text(run_elem) -> str:
    """Lấy toàn bộ text của một <w:r> (gồm nhiều <w:t> nếu có)."""
    parts = []
    for t_elem in run_elem.findall(qn('w:t')):
        if t_elem.text:
            parts.append(t_elem.text)
    return ''.join(parts)


def _set_run_text(run_elem, text: str):
    """Đặt lại text cho <w:r>, giữ <w:t> đầu tiên, xoá các <w:t> thừa."""
    t_elems = run_elem.findall(qn('w:t'))
    if t_elems:
        t_elems[0].text = text
        t_elems[0].set(qn('xml:space'), 'preserve')
        for extra in t_elems[1:]:
            run_elem.remove(extra)
    else:
        t = OxmlElement('w:t')
        t.text = text
        t.set(qn('xml:space'), 'preserve')
        run_elem.append(t)


# ──────────────────────────────────────────────
# Split Run – THUẬT TOÁN CỐT LÕI
# ──────────────────────────────────────────────

def split_run_at(run_elem, char_pos: int):
    """Tách một <w:r> element thành 2 element tại vị trí ký tự char_pos.

    Trả về (left_elem, right_elem). left_elem giữ nguyên vị trí trong
    parent; right_elem được chèn ngay sau left_elem.

    VÍ DỤ: split_run_at(<w:r>"Hello World">, 5) →
        <w:r>"Hello">, <w:r>" World">
    """
    text = _get_run_text(run_elem)
    if char_pos <= 0 or char_pos >= len(text):
        return run_elem, None  # Không cần tách

    left_text = text[:char_pos]
    right_text = text[char_pos:]

    # Sửa run gốc → chỉ giữ phần trái
    _set_run_text(run_elem, left_text)

    # Tạo run mới cho phần phải (clone rPr)
    rpr_copy = _clone_rpr(run_elem)
    right_elem = _make_run_element(right_text, rpr_copy)

    # Chèn right_elem ngay sau run_elem trong parent
    parent = run_elem.getparent()
    if parent is not None:
        idx = list(parent).index(run_elem)
        parent.insert(idx + 1, right_elem)

    return run_elem, right_elem


def _apply_error_formatting(run_elem, color_red: bool = True,
                             bold: bool = True, underline: bool = True,
                             highlight_yellow: bool = False):
    """Áp dụng định dạng lỗi (đỏ, đậm, gạch chân) lên một <w:r>."""
    rpr = run_elem.find(qn('w:rPr'))
    if rpr is None:
        rpr = _make_rpr_element()
        run_elem.insert(0, rpr)

    if color_red:
        # Xóa color cũ nếu có
        old_color = rpr.find(qn('w:color'))
        if old_color is not None:
            rpr.remove(old_color)
        color_elem = OxmlElement('w:color')
        color_elem.set(qn('w:val'), 'FF0000')
        rpr.append(color_elem)

    if bold:
        old_b = rpr.find(qn('w:b'))
        if old_b is None:
            b_elem = OxmlElement('w:b')
            rpr.append(b_elem)

    if underline:
        old_u = rpr.find(qn('w:u'))
        if old_u is not None:
            rpr.remove(old_u)
        u_elem = OxmlElement('w:u')
        u_elem.set(qn('w:val'), 'single')
        rpr.append(u_elem)

    if highlight_yellow:
        old_hl = rpr.find(qn('w:highlight'))
        if old_hl is not None:
            rpr.remove(old_hl)
        hl_elem = OxmlElement('w:highlight')
        hl_elem.set(qn('w:val'), 'yellow')
        rpr.append(hl_elem)


def _make_suggestion_run(suggestion: str) -> OxmlElement:
    """Tạo run gợi ý sửa: [Sửa: ...] màu xanh dương, in nghiêng."""
    rpr = _make_rpr_element()

    # Màu xanh dương
    color = OxmlElement('w:color')
    color.set(qn('w:val'), '0000FF')
    rpr.append(color)

    # In nghiêng
    i_elem = OxmlElement('w:i')
    rpr.append(i_elem)

    # Cỡ chữ nhỏ hơn (20 half-pt = 10pt)
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), '20')
    rpr.append(sz)
    sz_cs = OxmlElement('w:szCs')
    sz_cs.set(qn('w:val'), '20')
    rpr.append(sz_cs)

    text = f' [Sửa: {suggestion}]'
    return _make_run_element(text, rpr)


# ──────────────────────────────────────────────
# Đánh dấu lỗi trong Paragraph
# ──────────────────────────────────────────────

@dataclass
class _RunSpan:
    """Ánh xạ một run element tới vị trí ký tự trong paragraph."""
    run_elem: object  # lxml Element
    start: int
    end: int


def _build_run_map(para_elem) -> list[_RunSpan]:
    """Xây bản đồ (run_element, start, end) cho paragraph."""
    spans = []
    pos = 0
    for r_elem in para_elem.findall(qn('w:r')):
        text = _get_run_text(r_elem)
        if text:
            spans.append(_RunSpan(run_elem=r_elem, start=pos, end=pos + len(text)))
            pos += len(text)
    return spans


def mark_errors_in_paragraph(para_elem, errors: list[SpellError],
                             show_suggestion: bool = True):
    """Bôi đỏ các lỗi trong một paragraph element (<w:p>).

    Thuật toán:
    1. Xây run map (text position → run element).
    2. Với mỗi lỗi, xác định run(s) chứa lỗi.
    3. Split run tại ranh giới lỗi (nếu cần).
    4. Áp dụng định dạng đỏ lên phần lỗi.
    5. Chèn run gợi ý sau phần lỗi.

    LƯU Ý: Xử lý lỗi từ CUỐI paragraph về ĐẦU để tránh lệch vị trí.
    """
    if not errors:
        return

    # Sắp xếp lỗi theo vị trí giảm dần (xử lý từ cuối)
    sorted_errors = sorted(errors, key=lambda e: e.start, reverse=True)

    for error in sorted_errors:
        err_start = error.start
        err_end = error.end

        # Xây lại run map mỗi lần (vì split thay đổi cấu trúc)
        run_map = _build_run_map(para_elem)
        if not run_map:
            continue

        # Tìm các run bị ảnh hưởng
        affected_runs = []
        for span in run_map:
            if span.start < err_end and span.end > err_start:
                affected_runs.append(span)

        if not affected_runs:
            continue

        # ── Bước 1: Split run đầu tiên (nếu lỗi bắt đầu giữa run) ──
        first_span = affected_runs[0]
        if err_start > first_span.start:
            offset = err_start - first_span.start
            left_elem, right_elem = split_run_at(first_span.run_elem, offset)
            if right_elem is not None:
                # Cập nhật: run ảnh hưởng bây giờ là right_elem
                affected_runs[0] = _RunSpan(
                    run_elem=right_elem,
                    start=err_start,
                    end=first_span.end,
                )

        # ── Bước 2: Split run cuối cùng (nếu lỗi kết thúc giữa run) ──
        last_span = affected_runs[-1]
        if err_end < last_span.end:
            offset = err_end - last_span.start
            # Nếu bước 1 đã thay đổi last_span, dùng run mới
            current_run = last_span.run_elem
            # Đọc lại text hiện tại
            current_text = _get_run_text(current_run)
            # Tính offset trong run hiện tại
            actual_offset = err_end - last_span.start
            if 0 < actual_offset < len(current_text):
                left_elem, right_elem = split_run_at(current_run, actual_offset)
                # left_elem chứa phần lỗi, right_elem là phần sau lỗi
                affected_runs[-1] = _RunSpan(
                    run_elem=left_elem,
                    start=last_span.start,
                    end=err_end,
                )

        # ── Bước 3: Áp dụng định dạng đỏ lên tất cả run bị ảnh hưởng ──
        last_error_run = None
        for span in affected_runs:
            _apply_error_formatting(
                span.run_elem,
                color_red=True,
                bold=True,
                underline=True,
                highlight_yellow=False,
            )
            last_error_run = span.run_elem

        # ── Bước 4: Chèn gợi ý sửa ──
        if show_suggestion and last_error_run is not None and error.suggestion and error.suggestion.strip() and error.suggestion.strip() != '?':
            suggestion_run = _make_suggestion_run(error.suggestion)
            parent = last_error_run.getparent()
            if parent is not None:
                idx = list(parent).index(last_error_run)
                parent.insert(idx + 1, suggestion_run)


# ──────────────────────────────────────────────
# Chèn Báo cáo Tổng quan Lỗi Thể thức
# ──────────────────────────────────────────────

def _add_border_to_paragraph(para):
    """Thêm viền đóng khung cho paragraph (qua XML)."""
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    for side in ['top', 'left', 'bottom', 'right']:
        border = OxmlElement(f'w:{side}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '12')       # 1.5pt
        border.set(qn('w:space'), '4')
        border.set(qn('w:color'), 'FF0000')
        pBdr.append(border)
    pPr.append(pBdr)


def _add_shading_to_paragraph(para, color: str = 'FFF2CC'):
    """Thêm nền màu cho paragraph."""
    pPr = para._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color)
    pPr.append(shd)


def insert_format_report(doc: Document, report: FormatReport):
    """Chèn khung BÁO CÁO LỖI THỂ THỨC ở đầu trang 1."""
    if not report.has_errors:
        return

    body = doc.element.body

    # Tìm paragraph đầu tiên
    first_para = body.find(qn('w:p'))

    # ── Tiêu đề ──
    title_p = OxmlElement('w:p')
    _insert_before(body, title_p, first_para)

    title_para = doc.paragraphs[0]  # paragraph vừa chèn
    _add_border_to_paragraph(title_para)
    _add_shading_to_paragraph(title_para, 'FFF2CC')

    # Thêm run tiêu đề
    title_run = title_para.add_run('⚠ BÁO CÁO TỔNG QUAN LỖI THỂ THỨC')
    title_run.bold = True
    title_run.font.color.rgb = RGBColor(255, 0, 0)
    title_run.font.size = Pt(14)
    title_run.font.name = 'Times New Roman'

    # ── Danh sách lỗi ──
    for i, error in enumerate(report.errors):
        err_p_elem = OxmlElement('w:p')
        # Chèn sau title
        ref = title_para._p.getnext()
        if ref is not None:
            body.insert(list(body).index(ref), err_p_elem)
        else:
            body.append(err_p_elem)

        # Tìm paragraph object tương ứng
        err_para = None
        for p in doc.paragraphs:
            if p._p is err_p_elem:
                err_para = p
                break
        if err_para is None:
            continue

        _add_border_to_paragraph(err_para)
        _add_shading_to_paragraph(err_para, 'FFF2CC')

        # Icon theo loại lỗi
        icon = {
            ErrorType.PAPER_SIZE: '📄',
            ErrorType.MARGIN: '📐',
            ErrorType.FONT: '🔤',
            ErrorType.FONT_SIZE: '🔢',
            ErrorType.STRUCTURE: '📋',
        }.get(error.error_type, '❌')

        run = err_para.add_run(f'  {icon} [{error.error_type.value}] {error.message}')
        run.font.color.rgb = RGBColor(200, 0, 0)
        run.font.size = Pt(11)
        run.font.name = 'Times New Roman'

        if error.detail:
            detail_run = err_para.add_run(f'\n      ↳ {error.detail}')
            detail_run.font.color.rgb = RGBColor(100, 100, 100)
            detail_run.font.size = Pt(10)
            detail_run.font.name = 'Times New Roman'
            detail_run.italic = True

    # ── Dòng phân cách ──
    sep_p_elem = OxmlElement('w:p')
    # Chèn sau tất cả lỗi
    last_error_p = doc.paragraphs[len(report.errors)]._p
    next_sibling = last_error_p.getnext()
    if next_sibling is not None:
        body.insert(list(body).index(next_sibling), sep_p_elem)
    else:
        body.append(sep_p_elem)

    for p in doc.paragraphs:
        if p._p is sep_p_elem:
            sep_run = p.add_run('─' * 60)
            sep_run.font.color.rgb = RGBColor(200, 200, 200)
            sep_run.font.size = Pt(8)
            break


def _insert_before(parent, new_elem, ref_elem):
    """Chèn new_elem trước ref_elem trong parent."""
    if ref_elem is not None:
        parent.insert(list(parent).index(ref_elem), new_elem)
    else:
        parent.append(new_elem)


# ──────────────────────────────────────────────
# XỬ LÝ TOÀN BỘ DOCUMENT
# ──────────────────────────────────────────────

@dataclass
class ProcessingStats:
    """Thống kê kết quả xử lý."""
    total_spelling_errors: int = 0
    total_punctuation_errors: int = 0
    total_format_errors: int = 0
    total_structure_errors: int = 0
    paragraphs_checked: int = 0
    tables_checked: int = 0

    @property
    def total_errors(self) -> int:
        return (self.total_spelling_errors + self.total_punctuation_errors +
                self.total_format_errors + self.total_structure_errors)


class DocxProcessor:
    """Bộ xử lý tổng hợp: kiểm tra chính tả + thể thức + bôi đỏ."""

    def __init__(self, show_suggestion: bool = True,
                 check_spelling: bool = True,
                 check_format: bool = True):
        self.show_suggestion = show_suggestion
        self.check_spelling_flag = check_spelling
        self.check_format_flag = check_format
        self.spell_checker = VietnameseSpellChecker()
        self.format_validator = FormatValidator()

    def process(self, input_path: str | Path, output_path: str | Path | None = None) -> tuple[str, ProcessingStats]:
        """Xử lý file .docx, trả về (đường dẫn file kết quả, thống kê).

        Args:
            input_path: Đường dẫn file .docx gốc.
            output_path: Đường dẫn file kết quả. Nếu None, tự sinh.

        Returns:
            (output_path, stats)
        """
        input_path = Path(input_path)
        if output_path is None:
            stem = input_path.stem
            output_path = input_path.parent / f"{stem}_DaKiemTra.docx"
        output_path = Path(output_path)

        # Mở document
        doc = Document(str(input_path))
        stats = ProcessingStats()

        # ── 1. Kiểm tra thể thức ──
        format_report = FormatReport()
        if self.check_format_flag:
            format_report = self.format_validator.validate(doc)
            stats.total_format_errors = sum(
                1 for e in format_report.errors
                if e.error_type in (ErrorType.FONT, ErrorType.FONT_SIZE,
                                    ErrorType.MARGIN, ErrorType.PAPER_SIZE)
            )
            stats.total_structure_errors = sum(
                1 for e in format_report.errors
                if e.error_type == ErrorType.STRUCTURE
            )

        # ── 2. Kiểm tra chính tả & bôi đỏ ──
        if self.check_spelling_flag:
            # 2a. Xử lý paragraphs thường
            for para in doc.paragraphs:
                self._process_paragraph(para._p, stats)

            # 2b. Xử lý tables (đệ quy)
            for table in doc.tables:
                self._process_table(table, stats)

        # ── 3. Chèn báo cáo thể thức ──
        if self.check_format_flag and format_report.has_errors:
            insert_format_report(doc, format_report)

        # ── 4. Lưu file ──
        doc.save(str(output_path))

        return str(output_path), stats

    def _process_paragraph(self, para_elem, stats: ProcessingStats):
        """Kiểm tra & bôi đỏ lỗi trong một paragraph element."""
        # Lấy text từ runs
        run_map = _build_run_map(para_elem)
        if not run_map:
            return

        full_text = ''.join(_get_run_text(span.run_elem) for span in run_map)
        if not full_text.strip():
            return

        stats.paragraphs_checked += 1

        # Chạy kiểm tra chính tả
        errors = self.spell_checker.check_text(full_text)
        if not errors:
            return

        # Đếm thống kê
        for err in errors:
            if err.error_type == ErrorType.SPELLING:
                stats.total_spelling_errors += 1
            elif err.error_type == ErrorType.PUNCTUATION:
                stats.total_punctuation_errors += 1

        # Bôi đỏ
        mark_errors_in_paragraph(para_elem, errors, self.show_suggestion)

    def _process_table(self, table, stats: ProcessingStats):
        """Duyệt đệ quy table → cell → paragraph (kể cả nested tables)."""
        stats.tables_checked += 1
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    self._process_paragraph(para._p, stats)
                # Bảng lồng nhau
                for nested_table in cell.tables:
                    self._process_table(nested_table, stats)

