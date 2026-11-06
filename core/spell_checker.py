"""
spell_checker.py – Kiểm tra chính tả tiếng Việt & quy tắc dấu câu, thể thức văn bản.

Hỗ trợ:
  - Kiểm tra âm tiết tiếng Việt chuẩn, xử lý chính xác chữ 'gìn', 'giếng', 'quy'...
  - Từ điển ngoại lệ ngành Giáo dục (Whitelist) và từ mượn tiếng Anh phổ biến (tivi, rubik, video...)
  - Quy tắc dấu câu toàn diện: ngoặc đơn, ngoặc vuông, ngoặc nhọn, ngoặc kép cong “”, «», ""
  - Xử lý thông minh dấu ?, :, !, ., ,, ;… Tránh bắt nhầm dấu hỏi điền khuyết (x = ?, Sản phẩm: ?, [?])
  - Bảo vệ số thập phân, thời gian, tỉ số, URL, email, công thức Toán / Hóa
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .constants import (
    EDUCATION_WHITELIST,
    COMMON_LOANWORDS,
    PUNCTUATION_RULES,
    ErrorType,
)

# ──────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────

@dataclass
class SpellError:
    """Một lỗi chính tả / dấu câu được phát hiện."""
    start: int            # vị trí bắt đầu trong đoạn văn bản
    end: int              # vị trí kết thúc (exclusive)
    wrong_text: str       # chuỗi bị sai
    suggestion: str       # gợi ý sửa
    error_type: ErrorType # loại lỗi
    description: str = "" # mô tả thêm


# ──────────────────────────────────────────────
# Bảng dấu thanh tiếng Việt
# ──────────────────────────────────────────────

_TONE_CHARS: dict[tuple[str, int], str] = {}
_VOWEL_TO_BASE: dict[str, tuple[str, int]] = {}

def _build_tone_tables():
    """Xây dựng bảng ánh xạ nguyên âm có dấu ↔ nguyên âm gốc + thanh."""
    groups = [
        ('a', 'àáảãạ'),
        ('ă', 'ằắẳẵặ'),
        ('â', 'ầấẩẫậ'),
        ('e', 'èéẻẽẹ'),
        ('ê', 'ềếểễệ'),
        ('i', 'ìíỉĩị'),
        ('o', 'òóỏõọ'),
        ('ô', 'ồốổỗộ'),
        ('ơ', 'ờớởỡợ'),
        ('u', 'ùúủũụ'),
        ('ư', 'ừứửữự'),
        ('y', 'ỳýỷỹỵ'),
    ]
    for base, accented in groups:
        _VOWEL_TO_BASE[base] = (base, 0)
        for idx, ch in enumerate(accented, start=1):
            _VOWEL_TO_BASE[ch] = (base, idx)
            _TONE_CHARS[(base, idx)] = ch

_build_tone_tables()


def strip_tone(word: str) -> tuple[str, int]:
    """Bỏ dấu thanh, trả về (từ_không_dấu_thanh, mã_thanh).
    Mã thanh: 0=ngang, 1=huyền, 2=sắc, 3=hỏi, 4=ngã, 5=nặng.
    """
    tone = 0
    result = []
    for ch in word:
        if ch in _VOWEL_TO_BASE:
            base, t = _VOWEL_TO_BASE[ch]
            result.append(base)
            if t != 0:
                tone = t
        else:
            result.append(ch)
    return ''.join(result), tone


def remove_all_diacritics(word: str) -> str:
    """Bỏ HOÀN TOÀN dấu (cả dấu thanh lẫn dấu phụ ă→a, ô→o, đ→d …)."""
    word = word.replace('đ', 'd').replace('Đ', 'D')
    nfkd = unicodedata.normalize('NFD', word)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')


# ──────────────────────────────────────────────
# Bộ âm tiết hợp lệ tiếng Việt (sinh từ quy tắc ngữ âm học)
# ──────────────────────────────────────────────

_INITIALS = [
    '', 'b', 'c', 'ch', 'd', 'đ', 'g', 'gh', 'gi', 'h',
    'k', 'kh', 'l', 'm', 'n', 'ng', 'ngh', 'nh',
    'p', 'ph', 'qu', 'r', 's', 't', 'th', 'tr', 'v', 'x',
]

_RHYMES = [
    'a', 'ă', 'â', 'e', 'ê', 'i', 'o', 'ô', 'ơ', 'u', 'ư', 'y',
    'ac', 'ach', 'ai', 'am', 'an', 'ang', 'anh', 'ao', 'ap', 'at', 'au', 'ay',
    'ăc', 'ăm', 'ăn', 'ăng', 'ăp', 'ăt',
    'âc', 'âm', 'ân', 'âng', 'âp', 'ât', 'âu', 'ây',
    'ec', 'em', 'en', 'eng', 'eo', 'ep', 'et',
    'êch', 'êm', 'ên', 'ênh', 'êp', 'êt', 'êu',
    'ia', 'ich', 'im', 'in', 'inh', 'ip', 'it', 'iu',
    'iêc', 'iêm', 'iên', 'iêng', 'iêp', 'iêt', 'iêu',
    'oa', 'oac', 'oach', 'oai', 'oam', 'oan', 'oang', 'oanh', 'oap', 'oat', 'oay',
    'oă', 'oăc', 'oăm', 'oăn', 'oăng', 'oăt',
    'oc', 'oe', 'oem', 'oen', 'oeo', 'oet', 'oi', 'om', 'on', 'ong', 'op', 'ot',
    'ôc', 'ôi', 'ôm', 'ôn', 'ông', 'ôp', 'ôt',
    'ơi', 'ơm', 'ơn', 'ơp', 'ơt',
    'ua', 'uc', 'ui', 'um', 'un', 'ung', 'up', 'ut',
    'uê', 'uêch', 'uênh',
    'uâm', 'uân', 'uâng', 'uâp', 'uât',
    'uôc', 'uôi', 'uôm', 'uôn', 'uông', 'uôt',
    'uy', 'uya', 'uych', 'uyên', 'uyêt', 'uyn', 'uynh', 'uyt',
    'ưa', 'ưc', 'ưi', 'ưm', 'ưn', 'ưng', 'ưp', 'ưt', 'ưu',
    'ươc', 'ươi', 'ươm', 'ươn', 'ương', 'ươp', 'ươt',
    'yêm', 'yên', 'yêng', 'yêt', 'yêu',
]

_STOPPED_FINALS = {'c', 'ch', 'p', 't'}

def _get_final(rhyme: str) -> str:
    """Trích phụ âm cuối của một vần."""
    for ending in ('ng', 'nh', 'ch', 'c', 'm', 'n', 'p', 't'):
        if rhyme.endswith(ending) and len(rhyme) > len(ending):
            return ending
    return ''

_VALID_SYLLABLES: set[str] = set()

def _build_syllable_set():
    """Sinh tất cả âm tiết hợp lệ từ bảng phụ âm đầu × vần."""
    front_vowels = {'e', 'ê', 'i', 'y'}

    for initial in _INITIALS:
        for rhyme in _RHYMES:
            first_vowel = ''
            for ch in rhyme:
                if ch in {'a', 'ă', 'â', 'e', 'ê', 'i', 'o', 'ô', 'ơ', 'u', 'ư', 'y'}:
                    first_vowel = ch
                    break

            # k, gh, ngh chỉ đi với nguyên âm hàng trước (e, ê, i, y)
            if initial == 'k' and first_vowel not in front_vowels:
                continue
            if initial == 'gh' and first_vowel not in front_vowels:
                continue
            if initial == 'ngh' and first_vowel not in front_vowels:
                continue

            # c, g, ng KHÔNG đi với nguyên âm hàng trước
            if initial == 'c' and first_vowel in front_vowels:
                continue
            if initial == 'g' and first_vowel in front_vowels:
                continue
            if initial == 'ng' and first_vowel in front_vowels:
                continue

            # qu không kết hợp với vần bắt đầu bằng u, ư
            if initial == 'qu':
                if first_vowel in {'u', 'ư'}:
                    continue
                if rhyme.startswith('o') and len(rhyme) > 1:
                    continue

            # QUY TẮC CHÍNH TẢ: chữ "gi" kết hợp với vần bắt đầu bằng "i"
            # Ký tự "i" trong "gi" và "i" của vần chập lại (vd: gi + in -> gin, gi + iêng -> giêng)
            if initial == 'gi':
                if rhyme.startswith('i'):
                    syllable = 'g' + rhyme
                else:
                    syllable = initial + rhyme
            else:
                syllable = initial + rhyme

            if syllable:
                _VALID_SYLLABLES.add(syllable)

    # Thêm các trường hợp cơ sở đặc biệt của tiếng Việt
    special_bases = [
        # Nhóm gìn, giếng, giết, gièm, giễu
        'gin', 'gim', 'git', 'gip', 'gich', 'ginh', 'giu',
        'giêng', 'giên', 'giêt', 'giêc', 'giêm', 'giêu', 'giêp',
        # Nhóm quy, quí, quốc
        'pha', 'phai', 'phan', 'phang', 'phao',
        'gi', 'ra', 'răng', 'rât', 'rôi', 'ro', 'ru', 'rưng',
        'qua', 'qua', 'quan', 'quang', 'quanh', 'quân', 'quât', 'quay', 'quăng',
        'que', 'quen', 'quê', 'quên', 'qui', 'quy', 'quo', 'quô', 'quôc', 'quơ',
    ]
    for b in special_bases:
        base, _ = strip_tone(b)
        _VALID_SYLLABLES.add(base)

_build_syllable_set()


# ──────────────────────────────────────────────
# Tải từ điển bổ sung (viet_dict.txt / Viet74K.txt)
# ──────────────────────────────────────────────

_EXTRA_DICT: set[str] = set()
_DICT_LOADED = False

def _load_dictionary():
    """Tải từ điển bổ sung từ file data/viet_dict.txt (nếu có)."""
    global _EXTRA_DICT, _DICT_LOADED
    if _DICT_LOADED:
        return
    _DICT_LOADED = True

    dict_paths = [
        Path(__file__).parent.parent / 'data' / 'viet_dict.txt',
        Path(__file__).parent.parent / 'data' / 'Viet74K.txt',
    ]
    for p in dict_paths:
        if p.is_file():
            with open(p, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word:
                        _EXTRA_DICT.add(word)
                        # Thêm cả base không dấu thanh
                        base, _ = strip_tone(word)
                        if base:
                            _EXTRA_DICT.add(base)
            break


def _is_vietnamese_word(word: str) -> bool:
    """Kiểm tra một từ (đã lowercased) có phải âm tiết tiếng Việt hợp lệ không."""
    _load_dictionary()

    # 1. Kiểm tra từ mượn tiếng Anh phổ biến (tivi, rubik, video...)
    if word in COMMON_LOANWORDS:
        return True

    # 2. Kiểm tra từ viết tắt / thuật ngữ trong whitelist
    if word in EDUCATION_WHITELIST or word.upper() in EDUCATION_WHITELIST:
        return True

    # 3. Kiểm tra trong từ điển bổ sung
    base, tone = strip_tone(word)
    if word in _EXTRA_DICT or base in _EXTRA_DICT:
        return True

    # 4. Kiểm tra trong bộ âm tiết sinh từ quy tắc ngữ âm
    if base not in _VALID_SYLLABLES:
        return False

    # 5. Kiểm tra ràng buộc thanh điệu: vần tắc (-c, -ch, -p, -t) chỉ đi với sắc (2) hoặc nặng (5)
    final = _get_final(base)
    if final in _STOPPED_FINALS:
        if tone not in (0, 2, 5):
            return False

    return True


# ──────────────────────────────────────────────
# Từ và cụm từ sai chính tả phổ biến trong Giáo án
# ──────────────────────────────────────────────

_COMMON_TYPOS: dict[str, str] = {
    # Cặp chữ gìn / giữ gìn
    'giữ dìn': 'giữ gìn',
    'dữ dìn': 'giữ gìn',
    'gìn dĩ': 'gìn giữ',
    'dìn dĩ': 'gìn giữ',
    'gìn dũ': 'gìn giữ',

    # s / x
    'sử lý': 'xử lý',
    'sắp sếp': 'sắp xếp',
    'xắp xếp': 'sắp xếp',
    'sác nhận': 'xác nhận',
    'sác định': 'xác định',
    'bổ xung': 'bổ sung',
    'cọ sát': 'cọ xát',
    'suôn xẻ': 'suôn sẻ',
    'sơ xuất': 'sơ suất',
    'suất sắc': 'xuất sắc',
    'sáng lạng': 'xán lạn',
    'xúc tích': 'súc tích',
    'xơ đồ': 'sơ đồ',
    'chia xẻ': 'chia sẻ',

    # ch / tr
    'chương chình': 'chương trình',
    'chực tiếp': 'trực tiếp',
    'chích xác': 'chính xác',
    'chính sát': 'chính xác',
    'chúng chình': 'chương trình',
    'chăn chở': 'trăn trở',
    'tiến chình': 'tiến trình',
    'chình bày': 'trình bày',
    'thuyết chình': 'thuyết trình',
    'chi thức': 'tri thức',
    'tri tiết': 'chi tiết',
    'chọng tâm': 'trọng tâm',
    'cha cứu': 'tra cứu',
    'tiêu trí': 'tiêu chí',
    'đối triếu': 'đối chiếu',
    'chong đợi': 'trông đợi',

    # d / gi / r
    'dáo viên': 'giáo viên',
    'thầy dáo': 'thầy giáo',
    'cô dáo': 'cô giáo',
    'dải thích': 'giải thích',
    'giặn dò': 'dặn dò',
    'dẫn giắt': 'dẫn dắt',
    'giẫn dắt': 'dẫn dắt',
    'giẫn giắt': 'dẫn dắt',
    'giành riêng': 'dành riêng',
    'tranh dành': 'tranh giành',
    'để giành': 'để dành',
    'gián diệp': 'gián điệp',

    # l / n
    'lăng lực': 'năng lực',
    'lo lực': 'nỗ lực',
    'nổ lực': 'nỗ lực',
    'nuyện tập': 'luyện tập',
    'học niệu': 'học liệu',

    # hỏi / ngã
    'kỉ năng': 'kĩ năng',
    'kỷ năng': 'kỹ năng',
    'sỉ số': 'sĩ số',
    'nghỉ lực': 'nghị lực',

    # Lỗi đánh máy thường gặp khác
    'học xinh': 'học sinh',
    'thăm quan': 'tham quan',
    'vô hình chung': 'vô hình trung',
    'chín sửa': 'chỉnh sửa',
    'tựu chung': 'tựu trung',
    'phẩm trất': 'phẩm chất',
    'vận zụng': 'vận dụng',
}


# ──────────────────────────────────────────────
# CLASS CHÍNH: VietnameseSpellChecker
# ──────────────────────────────────────────────

class VietnameseSpellChecker:
    """Engine kiểm tra chính tả tiếng Việt & thể thức dấu câu (Offline & Rule-based)."""

    def __init__(self, extra_whitelist: set[str] | None = None):
        self.whitelist = EDUCATION_WHITELIST.copy()
        if extra_whitelist:
            self.whitelist.update(extra_whitelist)
        _load_dictionary()

    # ─── Vùng cần bảo vệ (không bắt lỗi dấu câu / chính tả) ───

    @staticmethod
    def _find_protected_spans(text: str) -> list[tuple[int, int]]:
        """Tìm các khoảng ký tự không được bắt lỗi (URL, email, số thập phân, giờ, file, công thức)."""
        spans: list[tuple[int, int]] = []

        patterns = [
            # URLs (http://, https://, www., domain.vn...)
            r'https?://[^\s<>"]+|www\.[^\s<>"]+',
            # Email addresses
            r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
            # Tên file kèm phần mở rộng
            r'\b[A-Za-z0-9_.-]+\.(docx|doc|pdf|pptx|ppt|xlsx|xls|mp4|mp3|png|jpg|jpeg|gif|txt|csv|zip|rar)\b',
            # Số thập phân / số phân cách hàng nghìn (vd: 3,5 hoặc 3.5 hoặc 1.000.000 hoặc 1,000,000)
            r'\b\d+([,\.]\d+)+\b',
            # Thời gian / tỉ số (vd: 14:30, 8:00, 1:1, 16:9)
            r'\b\d{1,2}:\d{2}\b',
            r'\b\d+:\d+\b',
            # Viết tắt có dấu chấm phổ biến
            r'\bv\.v\.(?:\.\.)?|\bv\.v\b|\bv/v\b',
            r'\bTh\.S\b|\bPGS\.TS\b|\bGS\.TS\b|\bTS\.\b|\bĐ/c\b|\bđ/c\b',
            # Dấu hỏi chấm dùng làm chỗ điền khuyết / ẩn số / bài tập trong giáo án (CV 5512)
            # Ví dụ: "x = ?", "2 + 3 = ?", "Sản phẩm: ?", "A -> ?", "[?]", "(?)"
            r'(?:=|\+|-|\*|/|:|\->|=>|→|⇒|\(|\/|\[)\s*\?',
            r'\[\?\]|\(\?\)',
            r'^\s*\?\s*$',
            # Công thức hóa học / toán học có ngoặc
            r'\b[A-Z][a-z]?\(OH\)[0-9]?\b',
            r'\b\(NH4\)2SO4\b',
            r'\b(sin|cos|tan|cot|log|ln|lim|sqrt)\([a-zA-Z0-9_+\-*/\s]+\)',
        ]

        for p in patterns:
            for m in re.finditer(p, text, re.IGNORECASE):
                spans.append((m.start(), m.end()))

        return spans

    @staticmethod
    def _is_in_spans(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
        """Kiểm tra một khoảng (start, end) có bị chồng lấn vào vùng bảo vệ hay không."""
        for p_start, p_end in spans:
            if not (end <= p_start or start >= p_end):
                return True
        return False

    # ─── Kiểm tra dấu câu & khoảng trắng ───

    def check_punctuation(self, text: str) -> list[SpellError]:
        """Phát hiện lỗi dấu câu, khoảng trắng, ngoặc đơn, ngoặc vuông, ngoặc kép."""
        errors: list[SpellError] = []
        protected = self._find_protected_spans(text)

        # 1. Lỗi kết hợp: Thừa khoảng trắng TRƯỚC VÀ thiếu khoảng trắng SAU dấu câu
        #    Áp dụng khi trước dấu câu là một từ ngữ (chữ cái / số): "chữ :nội dung" -> "chữ: nội dung", "hỏi ?bạn" -> "hỏi? bạn"
        combined_pattern = re.compile(r'([A-Za-zÀ-ỹ0-9]+) +([,\.;:!\?])([A-Za-zÀ-ỹ0-9])')
        for m in combined_pattern.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                word = m.group(1)
                mark = m.group(2)
                after = m.group(3)
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=f"{word}{mark} {after}",
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Thừa khoảng trắng trước và thiếu khoảng trắng sau dấu '{mark}'",
                ))

        # 2. Thừa khoảng trắng TRƯỚC dấu câu (.,;:!?…)
        #    CHỈ áp dụng khi trước dấu cách là một từ (chữ cái / chữ số): "không ?" -> "không?", "số :" -> "số:"
        #    KHÔNG bắt nhầm trường hợp "x = ?", "Sản phẩm: ?", "A -> ?" vì trước dấu cách là toán tử
        lead_punct_pattern = re.compile(r'([A-Za-zÀ-ỹ0-9]+) +([,\.;:!\?…])(?!\S)')
        for m in lead_punct_pattern.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                word = m.group(1)
                mark = m.group(2)
                # Kiểm tra thêm ngữ cảnh tiền tố (tránh trường hợp tiền tố là toán tử dạng "tên = ?")
                prefix = text[:m.start()]
                if mark == '?' and re.search(r'(=|:|\->|=>|→|⇒|\(|\/|\[)\s*$', prefix):
                    continue

                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=f"{word}{mark}",
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Thừa khoảng trắng trước dấu '{mark}' (viết liền '{word}{mark}')",
                ))

        # 3. Thiếu khoảng trắng SAU dấu câu
        #    Ví dụ: "Toán,văn" -> "Toán, văn", "lớp 8.Kiến thức" -> "lớp 8. Kiến thức", "hỏi?tôi" -> "hỏi? tôi"
        trail_punct_pattern = re.compile(r'([,\.;:!\?])([A-Za-zÀ-ỹ])')
        for m in trail_punct_pattern.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                mark = m.group(1)
                letter = m.group(2)
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=f"{mark} {letter}",
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Thiếu khoảng trắng sau dấu '{mark}'",
                ))

        # 4. Thừa khoảng trắng SAU dấu mở ngoặc / mở nháy
        #    Hỗ trợ: ( [ { “ « '
        open_bracket_space = re.compile(r'([(\[{“«]) +')
        for m in open_bracket_space.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                bracket = m.group(1)
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=bracket,
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Thừa khoảng trắng sau dấu mở '{bracket}'",
                ))

        # Đối với ASCII ", chỉ là mở nháy khi theo sau là khoảng trắng rồi đến chữ cái
        open_quote_ascii = re.compile(r'" +(?=[A-Za-zÀ-ỹ0-9])')
        for m in open_quote_ascii.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion='"',
                    error_type=ErrorType.PUNCTUATION,
                    description='Thừa khoảng trắng sau dấu mở nháy kép \'"\'',
                ))

        # 5. Thừa khoảng trắng TRƯỚC dấu đóng ngoặc / đóng nháy
        #    Hỗ trợ: ) ] } ” » ’
        close_bracket_space = re.compile(r' +([)\]}”»’])')
        for m in close_bracket_space.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                bracket = m.group(1)
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=bracket,
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Thừa khoảng trắng trước dấu đóng '{bracket}'",
                ))

        # Đối với ASCII ", chỉ là đóng nháy khi trước nó có khoảng trắng và trước khoảng trắng là từ/dấu câu
        close_quote_ascii = re.compile(r'(?<=[A-Za-zÀ-ỹ0-9,\.;:!\?]) +"(?=[,\.;:!\?\s]|$)')
        for m in close_quote_ascii.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion='"',
                    error_type=ErrorType.PUNCTUATION,
                    description='Thừa khoảng trắng trước dấu đóng nháy kép \'"\'',
                ))

        # 6. Thiếu khoảng trắng TRƯỚC dấu mở ngoặc
        #    Ví dụ: "học sinh(lớp 8)" -> "học sinh (lớp 8)"
        missing_space_before_open = re.compile(r'([A-Za-zÀ-ỹ0-9])([(\[{“«])')
        for m in missing_space_before_open.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                c = m.group(1)
                b = m.group(2)
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=f"{c} {b}",
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Thiếu khoảng trắng trước dấu mở '{b}'",
                ))

        # 7. Thiếu khoảng trắng SAU dấu đóng ngoặc
        #    Ví dụ: "(lớp 8)học bài" -> "(lớp 8) học bài", "“thảo luận”nhóm" -> "“thảo luận” nhóm"
        missing_space_after_close = re.compile(r'([)\]}”»])([A-Za-zÀ-ỹ0-9])')
        for m in missing_space_after_close.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                b = m.group(1)
                c = m.group(2)
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=f"{b} {c}",
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Thiếu khoảng trắng sau dấu đóng '{b}'",
                ))

        # 8. Hai dấu cách liên tiếp trở lên
        double_space = re.compile(r'  +')
        for m in double_space.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=' ',
                    error_type=ErrorType.PUNCTUATION,
                    description="Hai hoặc nhiều dấu cách liên tiếp",
                ))

        # 9. Dấu ba chấm gõ sai quy cách
        #    2 dấu chấm ".." -> "..."
        two_dots = re.compile(r'(?<!\.)\.\.(?!\.)')
        for m in two_dots.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion='...',
                    error_type=ErrorType.PUNCTUATION,
                    description="Dấu ba chấm chỉ có 2 dấu chấm (cần 3 dấu chấm '...')",
                ))

        #    4 dấu chấm trở lên "...." -> "..."
        many_dots = re.compile(r'\.{4,}')
        for m in many_dots.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion='...',
                    error_type=ErrorType.PUNCTUATION,
                    description="Thừa dấu chấm trong dấu ba chấm (chuẩn là '...')",
                ))

        # 10. Dấu câu bị lặp sai quy cách (,, hoặc ;; hoặc :: hoặc ?? hoặc !!)
        repeated_punct = re.compile(r'([,;:!?]){2,}')
        for m in repeated_punct.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                mark = m.group(1)
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=mark,
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Dấu câu '{mark}' bị lặp lại liên tiếp",
                ))

        return errors

    # ─── Kiểm tra chính tả từng từ & cụm từ ───

    def check_spelling(self, text: str) -> list[SpellError]:
        """Phát hiện lỗi chính tả từ đơn và cụm từ tiếng Việt."""
        errors: list[SpellError] = []
        protected = self._find_protected_spans(text)

        # 1. Kiểm tra các cụm từ sai phổ biến đã biết trong từ điển lỗi
        text_lower = text.lower()
        for wrong_phrase, correct_phrase in _COMMON_TYPOS.items():
            if wrong_phrase == correct_phrase:
                continue
            idx = 0
            while True:
                pos = text_lower.find(wrong_phrase, idx)
                if pos == -1:
                    break
                # Kiểm tra ranh giới từ (không nằm giữa một từ dài hơn)
                before_ok = (pos == 0 or not text[pos - 1].isalpha())
                after_pos = pos + len(wrong_phrase)
                after_ok = (after_pos >= len(text) or not text[after_pos].isalpha())
                if before_ok and after_ok:
                    if not self._is_in_spans(pos, after_pos, protected):
                        errors.append(SpellError(
                            start=pos,
                            end=after_pos,
                            wrong_text=text[pos:after_pos],
                            suggestion=correct_phrase,
                            error_type=ErrorType.SPELLING,
                            description=f"Sai chính tả cụm từ (sửa thành '{correct_phrase}')",
                        ))
                idx = pos + 1

        # Tập vị trí đã được đánh dấu lỗi cụm từ
        covered_positions = set()
        for err in errors:
            covered_positions.update(range(err.start, err.end))

        # 2. Kiểm tra từng từ / âm tiết đơn
        word_pattern = re.compile(r'[A-Za-zÀ-ỹĂăÂâĐđÊêÔôƠơƯư]+')
        for m in word_pattern.finditer(text):
            word = m.group(0)
            start = m.start()
            end = m.end()

            # Bỏ qua nếu thuộc vùng bảo vệ hoặc đã thuộc lỗi cụm từ
            if any(p in covered_positions for p in range(start, end)):
                continue
            if self._is_in_spans(start, end, protected):
                continue

            word_lower = word.lower()

            # Bỏ qua whitelist (viết tắt GD: GV, HS, SGK...)
            if word in self.whitelist or word.upper() in self.whitelist or word_lower in self.whitelist:
                continue

            # Bỏ qua từ mượn tiếng Anh phổ biến (tivi, rubik, video...)
            if word_lower in COMMON_LOANWORDS or word.upper() in COMMON_LOANWORDS:
                continue

            # Bỏ qua nếu toàn chữ HOA (tiêu đề, tên viết tắt <= 10 ký tự)
            if word.isupper() and len(word) <= 10:
                continue

            # Bỏ qua số La Mã
            if re.fullmatch(r'[IVXLCDM]+', word, re.IGNORECASE):
                continue

            # Bỏ qua nếu chỉ 1 ký tự chữ cái (vd: điểm A, cột B, hàm f)
            if len(word) <= 1:
                continue

            # Kiểm tra âm tiết tiếng Việt
            if not _is_vietnamese_word(word_lower):
                suggestion = self._suggest(word_lower)
                errors.append(SpellError(
                    start=start,
                    end=end,
                    wrong_text=word,
                    suggestion=suggestion,
                    error_type=ErrorType.SPELLING,
                    description="Từ không có trong từ điển tiếng Việt",
                ))

        # Sắp xếp và loại bỏ lỗi trùng lặp
        errors.sort(key=lambda e: e.start)
        deduped: list[SpellError] = []
        last_end = -1
        for err in errors:
            if err.start >= last_end:
                deduped.append(err)
                last_end = err.end

        return deduped

    # ─── Gợi ý sửa lỗi ───

    def _suggest(self, word_lower: str) -> str:
        """Sinh từ gợi ý sửa cho một từ bị sai. Trả về chuỗi rỗng nếu không có gợi ý phù hợp."""
        # Kiểm tra từ điển lỗi đã biết trước
        if word_lower in _COMMON_TYPOS:
            return _COMMON_TYPOS[word_lower]

        candidates: list[str] = []

        # 1. Nhầm l / n
        if word_lower.startswith('l'):
            alt = 'n' + word_lower[1:]
            if _is_vietnamese_word(alt):
                candidates.append(alt)
        elif word_lower.startswith('n'):
            alt = 'l' + word_lower[1:]
            if _is_vietnamese_word(alt):
                candidates.append(alt)

        # 2. Nhầm ch / tr
        if word_lower.startswith('ch'):
            alt = 'tr' + word_lower[2:]
            if _is_vietnamese_word(alt):
                candidates.append(alt)
        elif word_lower.startswith('tr'):
            alt = 'ch' + word_lower[2:]
            if _is_vietnamese_word(alt):
                candidates.append(alt)

        # 3. Nhầm s / x
        if word_lower.startswith('s'):
            alt = 'x' + word_lower[1:]
            if _is_vietnamese_word(alt):
                candidates.append(alt)
        elif word_lower.startswith('x'):
            alt = 's' + word_lower[1:]
            if _is_vietnamese_word(alt):
                candidates.append(alt)

        # 4. Nhầm d / gi / r
        for prefix_from, prefix_to_list in [
            ('d', ['gi', 'r']),
            ('gi', ['d', 'r']),
            ('r', ['d', 'gi']),
        ]:
            if word_lower.startswith(prefix_from):
                rest = word_lower[len(prefix_from):]
                for pt in prefix_to_list:
                    alt = pt + rest
                    if _is_vietnamese_word(alt):
                        candidates.append(alt)

        # 5. Nhầm hỏi / ngã
        tone_swapped = self._swap_hoi_nga(word_lower)
        if tone_swapped and tone_swapped != word_lower and _is_vietnamese_word(tone_swapped):
            candidates.append(tone_swapped)

        if candidates:
            return candidates[0]
        return ""

    @staticmethod
    def _swap_hoi_nga(word: str) -> Optional[str]:
        """Hoán đổi dấu hỏi ↔ ngã trong một từ."""
        result = list(word)
        changed = False
        for i, ch in enumerate(result):
            if ch in _VOWEL_TO_BASE:
                base, tone = _VOWEL_TO_BASE[ch]
                if tone == 3:  # hỏi → ngã
                    new_ch = _TONE_CHARS.get((base, 4))
                    if new_ch:
                        result[i] = new_ch
                        changed = True
                elif tone == 4:  # ngã → hỏi
                    new_ch = _TONE_CHARS.get((base, 3))
                    if new_ch:
                        result[i] = new_ch
                        changed = True
        return ''.join(result) if changed else None

    # ─── API tổng hợp ───

    def check_text(self, text: str) -> list[SpellError]:
        """Kiểm tra toàn diện một đoạn văn bản: dấu câu, khoảng trắng và chính tả."""
        errors: list[SpellError] = []
        errors.extend(self.check_punctuation(text))
        errors.extend(self.check_spelling(text))

        # Sắp xếp theo thứ tự vị trí xuất hiện trong đoạn văn
        errors.sort(key=lambda e: e.start)

        # Hợp nhất và loại bỏ lỗi chồng chéo (ưu tiên lỗi xuất hiện trước)
        deduped: list[SpellError] = []
        last_end = -1
        for err in errors:
            if err.start >= last_end:
                deduped.append(err)
                last_end = err.end
        return deduped
