"""
docx_processor.py – Xử lý file .docx tốc độ cao: bôi đỏ lỗi, tự động sửa sạch lỗi & chèn báo cáo.

Kỹ thuật cốt lõi (v2.0):
  - Split Run ở cấp XML (lxml) để giữ nguyên 100% định dạng gốc (công thức Toán, hình ảnh, bảng biểu).
  - Hỗ trợ song song 2 chế độ xuất file Word:
      1. Bản Bôi Đỏ & Gợi Ý (_DaKiemTra.docx)
      2. Bản Tự Động Sửa Sạch Lỗi & Chuẩn Hóa Thể Thức (_DaSuaLoi.docx)
  - Xử lý trực tiếp trên RAM (io.BytesIO) giúp tăng tốc độ Web gấp nhiều lần, không cần ghi file tạm.
  - Tích hợp giải pháp Trực tuyến độ chính xác cao (Wiktionary Batch Verifier, LanguageTool, Cloud AI).
"""

from __future__ import annotations

import copy
import html
import io
import os
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from .docx_compat import (
    Document,
    Pt,
    RGBColor,
    Cm,
    Inches,
    WD_COLOR_INDEX,
    OxmlElement,
    qn,
    nsmap,
)
from .spell_checker import VietnameseSpellChecker, SpellError
from .format_validator import FormatValidator, FormatReport, auto_fix_document_format
from .online_checker import OnlineHighPrecisionChecker
from .constants import ErrorType


# ──────────────────────────────────────────────
# Tiện ích XML
# ──────────────────────────────────────────────

def _make_rpr_element() -> OxmlElement:
    return OxmlElement("w:rPr")


def _clone_rpr(source_run_element) -> Optional[OxmlElement]:
    rpr = source_run_element.find(qn("w:rPr"))
    if rpr is not None:
        return copy.deepcopy(rpr)
    return None


def _make_run_element(text: str, rpr: Optional[OxmlElement] = None,
                      preserve_space: bool = True) -> OxmlElement:
    r = OxmlElement("w:r")
    if rpr is not None:
        r.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    if preserve_space:
        t.set(qn("xml:space"), "preserve")
    r.append(t)
    return r


def _get_run_text(run_elem) -> str:
    parts = []
    for t_elem in run_elem.findall(qn("w:t")):
        if t_elem.text:
            parts.append(t_elem.text)
    return "".join(parts)


def _set_run_text(run_elem, text: str):
    t_elems = run_elem.findall(qn("w:t"))
    if t_elems:
        t_elems[0].text = text
        t_elems[0].set(qn("xml:space"), "preserve")
        for extra in t_elems[1:]:
            run_elem.remove(extra)
    else:
        t = OxmlElement("w:t")
        t.text = text
        t.set(qn("xml:space"), "preserve")
        run_elem.append(t)


# ──────────────────────────────────────────────
# Split Run – THUẬT TOÁN CỐT LÕI
# ──────────────────────────────────────────────

def split_run_at(run_elem, char_pos: int):
    """Tách một <w:r> element thành 2 element tại vị trí ký tự char_pos."""
    text = _get_run_text(run_elem)
    if char_pos <= 0 or char_pos >= len(text):
        return run_elem, None

    left_text = text[:char_pos]
    right_text = text[char_pos:]

    _set_run_text(run_elem, left_text)

    rpr_copy = _clone_rpr(run_elem)
    right_elem = _make_run_element(right_text, rpr_copy)

    parent = run_elem.getparent()
    if parent is not None:
        idx = list(parent).index(run_elem)
        parent.insert(idx + 1, right_elem)

    return run_elem, right_elem


def _apply_error_formatting(run_elem, color_red: bool = True,
                            bold: bool = True, underline: bool = True,
                            highlight_yellow: bool = False):
    """Áp dụng định dạng lỗi (đỏ, đậm, gạch chân) lên một <w:r>."""
    rpr = run_elem.find(qn("w:rPr"))
    if rpr is None:
        rpr = _make_rpr_element()
        run_elem.insert(0, rpr)

    if color_red:
        old_color = rpr.find(qn("w:color"))
        if old_color is not None:
            rpr.remove(old_color)
        color_elem = OxmlElement("w:color")
        color_elem.set(qn("w:val"), "FF0000")
        rpr.append(color_elem)

    if bold:
        old_b = rpr.find(qn("w:b"))
        if old_b is None:
            rpr.append(OxmlElement("w:b"))

    if underline:
        old_u = rpr.find(qn("w:u"))
        if old_u is not None:
            rpr.remove(old_u)
        u_elem = OxmlElement("w:u")
        u_elem.set(qn("w:val"), "single")
        rpr.append(u_elem)

    if highlight_yellow:
        old_hl = rpr.find(qn("w:highlight"))
        if old_hl is not None:
            rpr.remove(old_hl)
        hl_elem = OxmlElement("w:highlight")
        hl_elem.set(qn("w:val"), "yellow")
        rpr.append(hl_elem)


def _make_suggestion_run(suggestion: str) -> OxmlElement:
    """Tạo run gợi ý sửa: [Sửa: ...] màu xanh dương, in nghiêng."""
    rpr = _make_rpr_element()

    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0052CC")
    rpr.append(color)

    rpr.append(OxmlElement("w:i"))

    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "20")
    rpr.append(sz)
    sz_cs = OxmlElement("w:szCs")
    sz_cs.set(qn("w:val"), "20")
    rpr.append(sz_cs)

    text = f" [Sửa: {suggestion}]"
    return _make_run_element(text, rpr)


# ──────────────────────────────────────────────
# Đánh dấu lỗi & Tự động sửa lỗi trong Paragraph
# ──────────────────────────────────────────────

@dataclass
class _RunSpan:
    run_elem: object
    start: int
    end: int


def _build_run_map(para_elem) -> list[_RunSpan]:
    spans = []
    pos = 0
    for r_elem in para_elem.findall(qn("w:r")):
        text = _get_run_text(r_elem)
        if text:
            spans.append(_RunSpan(run_elem=r_elem, start=pos, end=pos + len(text)))
            pos += len(text)
    return spans


def _isolate_error_runs(para_elem, err_start: int, err_end: int) -> list[_RunSpan]:
    """Tách các <w:r> tại biên [err_start, err_end) và trả về danh sách _RunSpan nằm trọn trong vùng lỗi."""
    run_map = _build_run_map(para_elem)
    if not run_map:
        return []

    affected_runs = [
        span for span in run_map
        if span.start < err_end and span.end > err_start
    ]
    if not affected_runs:
        return []

    # Bước 1: Split run đầu tiên
    first_span = affected_runs[0]
    if err_start > first_span.start:
        offset = err_start - first_span.start
        _, right_elem = split_run_at(first_span.run_elem, offset)
        if right_elem is not None:
            affected_runs[0] = _RunSpan(
                run_elem=right_elem,
                start=err_start,
                end=first_span.end,
            )

    # Bước 2: Split run cuối cùng
    last_span = affected_runs[-1]
    if err_end < last_span.end:
        current_run = last_span.run_elem
        current_text = _get_run_text(current_run)
        actual_offset = err_end - last_span.start
        if 0 < actual_offset < len(current_text):
            left_elem, _ = split_run_at(current_run, actual_offset)
            affected_runs[-1] = _RunSpan(
                run_elem=left_elem,
                start=last_span.start,
                end=err_end,
            )

    return affected_runs


def mark_errors_in_paragraph(para_elem, errors: list[SpellError],
                             show_suggestion: bool = True):
    """Bôi đỏ các lỗi trong một paragraph element (<w:p>)."""
    if not errors:
        return

    sorted_errors = sorted(errors, key=lambda e: e.start, reverse=True)

    for error in sorted_errors:
        affected_runs = _isolate_error_runs(para_elem, error.start, error.end)
        if not affected_runs:
            continue

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

        if (
            show_suggestion
            and last_error_run is not None
            and error.suggestion
            and error.suggestion.strip()
            and error.suggestion.strip() != "?"
        ):
            suggestion_run = _make_suggestion_run(error.suggestion)
            parent = last_error_run.getparent()
            if parent is not None:
                idx = list(parent).index(last_error_run)
                parent.insert(idx + 1, suggestion_run)


def apply_fixes_in_paragraph(para_elem, errors: list[SpellError]) -> int:
    """Tự động thay thế trực tiếp văn bản sai bằng gợi ý sửa ngay trong <w:r> (giữ nguyên định dạng gốc)."""
    if not errors:
        return 0

    sorted_errors = sorted(errors, key=lambda e: e.start, reverse=True)
    fixed_count = 0

    for error in sorted_errors:
        if not error.suggestion or error.suggestion == "?":
            continue

        affected_runs = _isolate_error_runs(para_elem, error.start, error.end)
        if not affected_runs:
            continue

        # Đặt toàn bộ chuỗi sửa vào run đầu tiên của vùng lỗi, xóa các run thừa còn lại trong vùng lỗi
        first_run = affected_runs[0].run_elem
        _set_run_text(first_run, error.suggestion)
        for extra_span in affected_runs[1:]:
            parent = extra_span.run_elem.getparent()
            if parent is not None:
                parent.remove(extra_span.run_elem)
        fixed_count += 1

    return fixed_count


# ──────────────────────────────────────────────
# Chèn Báo cáo Tổng quan Lỗi Thể thức (Tối ưu O(1) XML)
# ──────────────────────────────────────────────

def _style_report_p_elem(p_elem, fill_color: str = "FFF2CC"):
    """Đóng khung viền đỏ và tô nền vàng nhạt trực tiếp trên <w:p> element."""
    pPr = p_elem.find(qn("w:pPr"))
    if pPr is None:
        pPr = OxmlElement("w:pPr")
        p_elem.insert(0, pPr)

    pBdr = OxmlElement("w:pBdr")
    for side in ("top", "left", "bottom", "right"):
        border = OxmlElement(f"w:{side}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "12")
        border.set(qn("w:space"), "4")
        border.set(qn("w:color"), "FF0000")
        pBdr.append(border)
    pPr.append(pBdr)

    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_color)
    pPr.append(shd)


def _add_styled_run_to_p(p_elem, text: str, color_hex: str = "C80000",
                         size_pt: int = 11, bold: bool = False, italic: bool = False):
    """Thêm một <w:r> có định dạng font Times New Roman vào <w:p>."""
    rpr = OxmlElement("w:rPr")
    rfonts = OxmlElement("w:rFonts")
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), "Times New Roman")
    rpr.append(rfonts)

    if bold:
        rpr.append(OxmlElement("w:b"))
    if italic:
        rpr.append(OxmlElement("w:i"))

    color = OxmlElement("w:color")
    color.set(qn("w:val"), color_hex)
    rpr.append(color)

    half_pt = str(size_pt * 2)
    for tag in ("w:sz", "w:szCs"):
        sz = OxmlElement(tag)
        sz.set(qn("w:val"), half_pt)
        rpr.append(sz)

    r_elem = _make_run_element(text, rpr)
    p_elem.append(r_elem)


def insert_format_report(doc: Document, report: FormatReport):
    """Chèn khung BÁO CÁO LỖI THỂ THỨC ở đầu trang 1 với độ phức tạp O(1)."""
    if not report.has_errors:
        return

    body = doc.element.body
    if body is None:
        return

    elements_to_insert = []

    # 1. Tiêu đề
    title_p = OxmlElement("w:p")
    _style_report_p_elem(title_p, "FFF2CC")
    _add_styled_run_to_p(
        title_p,
        "⚠ BÁO CÁO TỔNG QUAN LỖI THỂ THỨC & CẤU TRÚC (CV 5512 & NĐ 30/2020)",
        color_hex="FF0000",
        size_pt=13,
        bold=True,
    )
    elements_to_insert.append(title_p)

    # 2. Danh sách lỗi
    icon_map = {
        ErrorType.PAPER_SIZE: "📄",
        ErrorType.MARGIN: "📐",
        ErrorType.FONT: "🔤",
        ErrorType.FONT_SIZE: "🔢",
        ErrorType.STRUCTURE: "📋",
    }
    for error in report.errors:
        err_p = OxmlElement("w:p")
        _style_report_p_elem(err_p, "FFF2CC")
        icon = icon_map.get(error.error_type, "❌")
        _add_styled_run_to_p(
            err_p,
            f"  {icon} [{error.error_type.value}] {error.message}",
            color_hex="C80000",
            size_pt=11,
            bold=False,
        )
        if error.detail:
            _add_styled_run_to_p(
                err_p,
                f" — {error.detail.replace(chr(10), '; ')}",
                color_hex="555555",
                size_pt=10,
                italic=True,
            )
        elements_to_insert.append(err_p)

    # 3. Dòng phân cách
    sep_p = OxmlElement("w:p")
    _add_styled_run_to_p(sep_p, "─" * 65, color_hex="CCCCCC", size_pt=8)
    elements_to_insert.append(sep_p)

    # Chèn toàn bộ lên đầu body
    for idx, el in enumerate(elements_to_insert):
        body.insert(idx, el)


# ──────────────────────────────────────────────
# Dữ liệu Thống kê & Chi tiết Lỗi
# ──────────────────────────────────────────────

@dataclass
class ErrorDetail:
    """Chi tiết một lỗi kèm vị trí và ngữ cảnh đoạn văn để hiển thị trên Web UI."""
    id: int
    location: str
    error_type: str
    wrong_text: str
    suggestion: str
    description: str
    context_snippet: str
    context_html: str
    source: str = "offline"

    def to_dict(self) -> dict:
        return asdict(self)


def format_visible_token(token: str) -> str:
    """Hiển thị rõ ràng các ký tự khoảng trắng để không bị chìm hoặc vô hình trên giao diện."""
    if not token:
        return ""
    if token.strip() == "":
        n = len(token)
        if n == 1:
            return "␣ (1 dấu cách)"
        return f"{'␣' * min(n, 4)} ({n} dấu cách)"
    if token.startswith(" ") or token.endswith(" "):
        return token.replace(" ", "␣")
    return token


def _build_context_html(full_text: str, err: SpellError, window: int = 55) -> tuple[str, str]:
    """Tạo đoạn trích ngắn và HTML highlight độ tương phản cao cho lỗi trong câu."""
    start_ctx = max(0, err.start - window)
    end_ctx = min(len(full_text), err.end + window)
    prefix = ("..." if start_ctx > 0 else "") + full_text[start_ctx:err.start]
    wrong = full_text[err.start:err.end]
    suffix = full_text[err.end:end_ctx] + ("..." if end_ctx < len(full_text) else "")

    vis_wrong = format_visible_token(wrong)
    vis_sug = format_visible_token(err.suggestion) if (err.suggestion and err.suggestion != "?") else "?"
    plain_snippet = f"{prefix}[{vis_wrong} -> {vis_sug}]{suffix}"

    esc_prefix = html.escape(prefix)
    esc_wrong = html.escape(vis_wrong)
    esc_suffix = html.escape(suffix)
    if err.suggestion and err.suggestion != "?":
        esc_sug = html.escape(format_visible_token(err.suggestion))
        sug_badge = f'<span class="sug-inline">➜ {esc_sug}</span>'
    else:
        sug_badge = ""

    html_snippet = (
        f'<span class="ctx-text">{esc_prefix}</span>'
        f'<span class="err-inline">{esc_wrong}</span>'
        f'{sug_badge}'
        f'<span class="ctx-text">{esc_suffix}</span>'
    )
    return plain_snippet, html_snippet


@dataclass
class ProcessingStats:
    """Thống kê kết quả xử lý toàn diện."""
    total_spelling_errors: int = 0
    total_punctuation_errors: int = 0
    total_context_errors: int = 0
    total_format_errors: int = 0
    total_structure_errors: int = 0
    paragraphs_checked: int = 0
    tables_checked: int = 0
    total_words: int = 0
    auto_fixed_count: int = 0
    processing_time_ms: float = 0.0
    error_details: list[ErrorDetail] = field(default_factory=list)
    format_report: Optional[FormatReport] = None
    verified_online_words: list[str] = field(default_factory=list)

    @property
    def total_errors(self) -> int:
        return (
            self.total_spelling_errors
            + self.total_punctuation_errors
            + self.total_context_errors
            + self.total_format_errors
            + self.total_structure_errors
        )

    @property
    def quality_score(self) -> int:
        """Điểm chất lượng Giáo án trên thang 100."""
        penalty = (
            self.total_spelling_errors * 2.5
            + self.total_context_errors * 2.5
            + self.total_punctuation_errors * 1.2
            + self.total_format_errors * 4.0
            + self.total_structure_errors * 6.0
        )
        return max(0, min(100, int(round(100 - penalty))))

    @property
    def quality_grade(self) -> str:
        s = self.quality_score
        if s >= 95:
            return "A+ (Xuất sắc)"
        if s >= 85:
            return "A (Tốt)"
        if s >= 70:
            return "B (Khá)"
        if s >= 55:
            return "C (Cần chỉnh sửa)"
        return "D (Nhiều lỗi cần khắc phục)"


# ──────────────────────────────────────────────
# CLASS CHÍNH: DocxProcessor
# ──────────────────────────────────────────────

class DocxProcessor:
    """Bộ xử lý tổng hợp: kiểm tra chính tả + thể thức + trực tuyến + bôi đỏ + tự động sửa lỗi."""

    def __init__(self,
                 show_suggestion: bool = True,
                 check_spelling: bool = True,
                 check_format: bool = True,
                 check_context: bool = True,
                 online_verify_wiktionary: bool = False,
                 online_languagetool: bool = False,
                 online_ai_check: bool = False,
                 ai_provider: str = "free_cloud",
                 ai_api_key: str = "",
                 ai_model: str = "",
                 normalize_tone: str = "keep",
                 normalize_iy: str = "keep"):
        self.show_suggestion = show_suggestion
        self.check_spelling_flag = check_spelling
        self.check_format_flag = check_format
        self.check_context_flag = check_context
        self.online_verify_wiktionary = online_verify_wiktionary
        self.online_languagetool = online_languagetool
        self.online_ai_check = online_ai_check
        self.ai_provider = ai_provider
        self.ai_api_key = ai_api_key
        self.ai_model = ai_model
        self.normalize_tone = normalize_tone
        self.normalize_iy = normalize_iy

        self.spell_checker = VietnameseSpellChecker(check_context=check_context)
        self.format_validator = FormatValidator()
        self.online_checker = OnlineHighPrecisionChecker(self.spell_checker)

    def _collect_paragraph_targets(self, doc: Document) -> list[tuple[object, str]]:
        """Thu thập danh sách (para_elem, nhãn_vị_trí) trong toàn bộ Document."""
        targets: list[tuple[object, str]] = []
        for idx, para in enumerate(doc.paragraphs, start=1):
            targets.append((para._p, f"Đoạn {idx}"))

        def _walk_table(table, tbl_label: str):
            for r_idx, row in enumerate(table.rows, start=1):
                for c_idx, cell in enumerate(row.cells, start=1):
                    for p_idx, para in enumerate(cell.paragraphs, start=1):
                        loc = f"{tbl_label} (Hàng {r_idx}, Cột {c_idx})"
                        targets.append((para._p, loc))
                    for n_idx, nested in enumerate(cell.tables, start=1):
                        _walk_table(nested, f"{tbl_label}.{n_idx}")

        for t_idx, table in enumerate(doc.tables, start=1):
            _walk_table(table, f"Bảng {t_idx}")

        return targets

    def _count_tables_recursive(self, doc: Document) -> int:
        count = 0
        def _walk(tbl):
            nonlocal count
            count += 1
            for r in tbl.rows:
                for c in r.cells:
                    for nt in c.tables:
                        _walk(nt)
        for t in doc.tables:
            _walk(t)
        return count

    def _analyze_document(self, doc: Document) -> tuple[ProcessingStats, list[tuple[int, list[SpellError]]]]:
        """Phân tích toàn bộ document, trả về (stats, danh_sách_(target_index, errors))."""
        t0 = time.perf_counter()
        stats = ProcessingStats()
        stats.tables_checked = self._count_tables_recursive(doc)

        # 1. Kiểm tra thể thức & cấu trúc CV 5512
        format_report = FormatReport()
        if self.check_format_flag:
            format_report = self.format_validator.validate(doc)
            stats.format_report = format_report
            stats.total_format_errors = sum(
                1 for e in format_report.errors
                if e.error_type in (ErrorType.FONT, ErrorType.FONT_SIZE, ErrorType.MARGIN, ErrorType.PAPER_SIZE)
            )
            stats.total_structure_errors = sum(
                1 for e in format_report.errors
                if e.error_type == ErrorType.STRUCTURE
            )

        para_errors_list: list[tuple[int, str, str, list[SpellError]]] = []

        if self.check_spelling_flag:
            targets = self._collect_paragraph_targets(doc)
            all_unknown_words: set[str] = set()

            for target_idx, (para_elem, loc_label) in enumerate(targets):
                run_map = _build_run_map(para_elem)
                if not run_map:
                    continue
                full_text = "".join(_get_run_text(span.run_elem) for span in run_map)
                if not full_text.strip():
                    continue

                stats.paragraphs_checked += 1
                stats.total_words += len(full_text.split())

                errors = self.spell_checker.check_text(full_text)

                # Nếu bật LanguageTool Online (cho đoạn có lỗi hoặc tiếng Anh)
                if self.online_languagetool and len(full_text.strip()) > 10:
                    lt_errs = self.online_checker.check_with_languagetool(full_text)
                    if lt_errs:
                        errors.extend(lt_errs)

                if errors:
                    for e in errors:
                        if e.error_type == ErrorType.SPELLING and "không có trong từ điển" in e.description:
                            all_unknown_words.add(e.wrong_text)
                    para_errors_list.append((target_idx, loc_label, full_text, errors))

            # Nếu bật Xác thực Wiktionary/Wikipedia Trực tuyến -> Gửi 1 batch query duy nhất cho toàn bộ file!
            verified_map: dict[str, bool] = {}
            if self.online_verify_wiktionary and all_unknown_words:
                verified_map = self.online_checker.verify_words_batch(list(all_unknown_words))
                stats.verified_online_words = sorted([w for w, ok in verified_map.items() if ok])

            # Nếu bật AI Ngữ cảnh -> Gộp các đoạn văn có nội dung để kiểm tra ngữ cảnh nhanh
            ai_errors_by_target: dict[int, list[SpellError]] = {}
            if self.online_ai_check:
                # Lấy tối đa 25 đoạn văn dài nhất để kiểm tra ngữ cảnh sâu bằng AI
                non_empty_targets = []
                for t_idx, (p_elem, loc_lbl) in enumerate(targets):
                    rmap = _build_run_map(p_elem)
                    txt = "".join(_get_run_text(s.run_elem) for s in rmap).strip()
                    if len(txt) >= 25:
                        non_empty_targets.append((t_idx, loc_lbl, txt))

                combined_sample = "\n".join(f"[{i}] {t[2]}" for i, t in enumerate(non_empty_targets[:25]))
                if combined_sample:
                    ai_errs, _ = self.online_checker.check_contextual_ai(
                        combined_sample,
                        provider=self.ai_provider,
                        api_key=self.ai_api_key,
                        model=self.ai_model,
                    )
                    # Ánh xạ lỗi AI về từng đoạn tương ứng
                    for ai_e in ai_errs:
                        for t_idx, loc_lbl, orig_txt in non_empty_targets[:25]:
                            pos = orig_txt.find(ai_e.wrong_text)
                            if pos != -1:
                                ai_errors_by_target.setdefault(t_idx, []).append(SpellError(
                                    start=pos,
                                    end=pos + len(ai_e.wrong_text),
                                    wrong_text=ai_e.wrong_text,
                                    suggestion=ai_e.suggestion,
                                    error_type=ErrorType.CONTEXT_ONLINE,
                                    description=ai_e.description,
                                    confidence=ai_e.confidence,
                                    source="ai",
                                ))
                                break

                # Hợp nhất ai_errors_by_target vào para_errors_list
                existing_t_indices = {item[0] for item in para_errors_list}
                for t_idx, extra_ai_errs in ai_errors_by_target.items():
                    if t_idx not in existing_t_indices:
                        p_elem, loc_lbl = targets[t_idx]
                        full_t = "".join(_get_run_text(s.run_elem) for s in _build_run_map(p_elem))
                        para_errors_list.append((t_idx, loc_lbl, full_t, extra_ai_errs))
                    else:
                        for idx_p, (ti, ll, ft, elist) in enumerate(para_errors_list):
                            if ti == t_idx:
                                elist.extend(extra_ai_errs)
                                break

            # Lọc kết quả cuối cùng, khử trùng lặp và ghi vào stats.error_details
            final_Indexed_errors: list[tuple[int, list[SpellError]]] = []
            err_counter = 1

            for target_idx, loc_label, full_text, raw_errs in sorted(para_errors_list, key=lambda x: x[0]):
                filtered: list[SpellError] = []
                for e in raw_errs:
                    if (
                        self.online_verify_wiktionary
                        and e.error_type == ErrorType.SPELLING
                        and "không có trong từ điển" in e.description
                        and verified_map.get(e.wrong_text.lower(), False)
                    ):
                        continue
                    filtered.append(e)

                if not filtered:
                    continue

                # Sắp xếp và khử chồng lấn
                filtered.sort(key=lambda e: (e.start, -(e.end - e.start)))
                dedup: list[SpellError] = []
                last_end = -1
                for e in filtered:
                    if e.start >= last_end:
                        dedup.append(e)
                        last_end = e.end

                for err in dedup:
                    if err.error_type == ErrorType.SPELLING:
                        stats.total_spelling_errors += 1
                    elif err.error_type == ErrorType.PUNCTUATION:
                        stats.total_punctuation_errors += 1
                    elif err.error_type in (ErrorType.CONTEXT_ONLINE, ErrorType.ORTHOGRAPHY):
                        stats.total_context_errors += 1

                    plain_snip, html_snip = _build_context_html(full_text, err)
                    stats.error_details.append(ErrorDetail(
                        id=err_counter,
                        location=loc_label,
                        error_type=err.error_type.value,
                        wrong_text=err.wrong_text,
                        suggestion=err.suggestion or "",
                        description=err.description,
                        context_snippet=plain_snip,
                        context_html=html_snip,
                        source=err.source,
                    ))
                    err_counter += 1

                final_Indexed_errors.append((target_idx, dedup))
        else:
            final_Indexed_errors = []

        stats.processing_time_ms = round((time.perf_counter() - t0) * 1000, 2)
        return stats, final_Indexed_errors

    def process(self, input_path: str | Path,
                output_path: str | Path | None = None) -> tuple[str, ProcessingStats]:
        """Xử lý file .docx trên ổ đĩa (tương thích 100% với CLI & test_checker.py)."""
        input_path = Path(input_path)
        if output_path is None:
            stem = input_path.stem
            output_path = input_path.parent / f"{stem}_DaKiemTra.docx"
        output_path = Path(output_path)

        doc = Document(str(input_path))
        stats, indexed_errors = self._analyze_document(doc)

        if self.check_spelling_flag and indexed_errors:
            targets = self._collect_paragraph_targets(doc)
            for target_idx, errs in indexed_errors:
                para_elem, _ = targets[target_idx]
                mark_errors_in_paragraph(para_elem, errs, self.show_suggestion)

        if self.check_format_flag and stats.format_report and stats.format_report.has_errors:
            insert_format_report(doc, stats.format_report)

        doc.save(str(output_path))
        return str(output_path), stats

    def process_bytes(self, docx_bytes: bytes,
                      generate_auto_fixed: bool = True,
                      auto_fix_format: bool = True) -> dict:
        """Xử lý file .docx hoàn toàn trên bộ nhớ RAM (BytesIO), trả về cả bản Bôi Đỏ và bản Tự Động Sửa."""
        t0 = time.perf_counter()

        # 1. Mở Document cho bản Bôi Đỏ
        stream_marked = io.BytesIO(docx_bytes)
        doc_marked = Document(stream_marked)
        stats, indexed_errors = self._analyze_document(doc_marked)

        if self.check_spelling_flag and indexed_errors:
            targets_marked = self._collect_paragraph_targets(doc_marked)
            for target_idx, errs in indexed_errors:
                para_elem, _ = targets_marked[target_idx]
                mark_errors_in_paragraph(para_elem, errs, self.show_suggestion)

        if self.check_format_flag and stats.format_report and stats.format_report.has_errors:
            insert_format_report(doc_marked, stats.format_report)

        out_marked = io.BytesIO()
        doc_marked.save(out_marked)
        marked_bytes = out_marked.getvalue()

        # 2. Tạo bản Tự Động Sửa Lỗi (_DaSuaLoi.docx) nếu được yêu cầu
        fixed_bytes = b""
        if generate_auto_fixed:
            stream_fixed = io.BytesIO(docx_bytes)
            doc_fixed = Document(stream_fixed)
            targets_fixed = self._collect_paragraph_targets(doc_fixed)

            fixed_cnt = 0
            for target_idx, errs in indexed_errors:
                para_elem, _ = targets_fixed[target_idx]
                fixed_cnt += apply_fixes_in_paragraph(para_elem, errs)

            # Nếu người dùng chọn chuẩn hóa dấu thanh (oà/òa) hoặc i/y trên bản sạch
            if self.normalize_tone in ("new", "old") or self.normalize_iy in ("i", "y"):
                for para_elem, _ in targets_fixed:
                    for r_elem in para_elem.findall(qn("w:r")):
                        r_txt = _get_run_text(r_elem)
                        if r_txt:
                            norm_txt, c_norm = VietnameseSpellChecker.normalize_orthography(
                                r_txt,
                                tone_style=self.normalize_tone,
                                iy_style=self.normalize_iy,
                            )
                            if c_norm > 0:
                                _set_run_text(r_elem, norm_txt)
                                fixed_cnt += c_norm

            if auto_fix_format and self.check_format_flag:
                fixed_cnt += auto_fix_document_format(doc_fixed)

            stats.auto_fixed_count = fixed_cnt
            out_fixed = io.BytesIO()
            doc_fixed.save(out_fixed)
            fixed_bytes = out_fixed.getvalue()

        stats.processing_time_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "stats": stats,
            "marked_bytes": marked_bytes,
            "fixed_bytes": fixed_bytes,
        }
