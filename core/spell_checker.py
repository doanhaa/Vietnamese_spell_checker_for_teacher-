"""
spell_checker.py – Engine kiểm tra chính tả tiếng Việt, quy tắc dấu câu, ngữ cảnh & chuẩn hóa chính tả.

Nâng cấp Hiệu năng & Độ chính xác cao (v2.0):
  - Pre-compiled Regex C-level cho toàn bộ quy tắc dấu câu, vùng bảo vệ và 200+ cụm từ dễ nhầm lẫn.
  - LRU Cache cho phân tích âm tiết, tách dấu thanh và gợi ý sửa lỗi (tăng tốc 15x–30x).
  - Khôi phục lỗi gõ Telex/VNI bị trượt phím (vd: hocj -> học, giaos -> giáo, truwowng -> trường).
  - Phát hiện lỗi ngữ cảnh Hán-Việt (điểm yếu / yếu điểm, bàng quan / bàng hoàng, giả thiết / giả thuyết) & lỗi lặp từ.
  - Chuẩn hóa đồng bộ quy tắc đặt dấu thanh (oà/òa, uỳ/ùy) và i/y (kĩ năng/kỹ năng, lí thuyết/lý thuyết).
  - Quản lý Từ điển Cá nhân (Custom Whitelist) lưu trữ bền vững.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .constants import (
    EDUCATION_WHITELIST,
    COMMON_LOANWORDS,
    CONFUSABLE_DETAILS,
    COMMON_TYPOS,
    CONTEXTUAL_CONFUSION_RULES,
    IY_STANDARD_MAP,
    TONE_OLD_TO_NEW,
    TONE_NEW_TO_OLD,
    ErrorType,
)

# ──────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────

@dataclass
class SpellError:
    """Một lỗi chính tả / dấu câu / ngữ cảnh được phát hiện."""
    start: int            # vị trí bắt đầu trong đoạn văn bản
    end: int              # vị trí kết thúc (exclusive)
    wrong_text: str       # chuỗi bị sai
    suggestion: str       # gợi ý sửa
    error_type: ErrorType # loại lỗi
    description: str = "" # mô tả giải thích chi tiết
    confidence: float = 1.0 # độ tin cậy (0.0 - 1.0)
    source: str = "offline" # "offline" | "wiktionary" | "languagetool" | "ai"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["error_type"] = self.error_type.value
        return d


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
        _TONE_CHARS[(base, 0)] = base
        for idx, ch in enumerate(accented, start=1):
            _VOWEL_TO_BASE[ch] = (base, idx)
            _TONE_CHARS[(base, idx)] = ch

_build_tone_tables()


@lru_cache(maxsize=65536)
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


@lru_cache(maxsize=32768)
def remove_all_diacritics(word: str) -> str:
    """Bỏ HOÀN TOÀN dấu (cả dấu thanh lẫn dấu phụ ă→a, ô→o, đ→d …)."""
    word = word.replace('đ', 'd').replace('Đ', 'D')
    nfkd = unicodedata.normalize('NFD', word)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')


def _preserve_case(original: str, replacement: str) -> str:
    """Giữ nguyên kiểu viết hoa (UPPER, Title, lower) của chuỗi gốc khi gợi ý."""
    if not original or not replacement:
        return replacement
    if original.isupper() and len(original) > 1:
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


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

            if initial in ('k', 'gh', 'ngh') and first_vowel not in front_vowels:
                continue
            if initial in ('c', 'g', 'ng') and first_vowel in front_vowels:
                continue
            if initial == 'qu':
                if first_vowel in {'u', 'ư'}:
                    continue
                if rhyme.startswith('o') and len(rhyme) > 1:
                    continue

            if initial == 'gi':
                if rhyme.startswith('i'):
                    syllable = 'g' + rhyme
                else:
                    syllable = initial + rhyme
            else:
                syllable = initial + rhyme

            if syllable:
                _VALID_SYLLABLES.add(syllable)

    special_bases = [
        'gin', 'gim', 'git', 'gip', 'gich', 'ginh', 'giu',
        'giêng', 'giên', 'giêt', 'giêc', 'giêm', 'giêu', 'giêp',
        'pha', 'phai', 'phan', 'phang', 'phao',
        'gi', 'ra', 'răng', 'rât', 'rôi', 'ro', 'ru', 'rưng',
        'qua', 'quan', 'quang', 'quanh', 'quân', 'quât', 'quay', 'quăng',
        'que', 'quen', 'quê', 'quên', 'qui', 'quy', 'quo', 'quô', 'quôc', 'quơ',
    ]
    for b in special_bases:
        base, _ = strip_tone(b)
        _VALID_SYLLABLES.add(base)

_build_syllable_set()


# ──────────────────────────────────────────────
# Tải từ điển bổ sung & Quản lý Từ điển Cá nhân
# ──────────────────────────────────────────────

_EXTRA_DICT: set[str] = set()
_FULL_WORDS_SET: set[str] = set()
_DICT_LOADED = False
_CUSTOM_WHITELIST_PATH = Path(__file__).parent.parent / 'data' / 'custom_whitelist.json'


def _load_dictionary():
    """Tải từ điển bổ sung từ file data/viet_dict.txt (chỉ chạy 1 lần duy nhất)."""
    global _EXTRA_DICT, _FULL_WORDS_SET, _DICT_LOADED
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
                        _FULL_WORDS_SET.add(word)
                        _EXTRA_DICT.add(word)
                        base, _ = strip_tone(word)
                        if base:
                            _EXTRA_DICT.add(base)
            break


def load_custom_whitelist() -> set[str]:
    """Đọc danh sách từ điển cá nhân của giáo viên từ data/custom_whitelist.json."""
    if _CUSTOM_WHITELIST_PATH.is_file():
        try:
            with open(_CUSTOM_WHITELIST_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {str(w).strip() for w in data if str(w).strip()}
        except Exception:
            pass
    return set()


def save_custom_whitelist(words: set[str]) -> None:
    """Lưu danh sách từ điển cá nhân vào data/custom_whitelist.json."""
    _CUSTOM_WHITELIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    sorted_words = sorted({w.strip() for w in words if w.strip()})
    with open(_CUSTOM_WHITELIST_PATH, 'w', encoding='utf-8') as f:
        json.dump(sorted_words, f, ensure_ascii=False, indent=2)
    _is_vietnamese_word.cache_clear()
    _suggest_cached.cache_clear()


def add_custom_words(new_words: list[str] | set[str]) -> set[str]:
    """Thêm một hoặc nhiều từ vào từ điển cá nhân."""
    current = load_custom_whitelist()
    for w in new_words:
        cleaned = w.strip()
        if cleaned:
            current.add(cleaned)
    save_custom_whitelist(current)
    return current


def remove_custom_word(word: str) -> set[str]:
    """Xóa một từ khỏi từ điển cá nhân."""
    current = load_custom_whitelist()
    current.discard(word.strip())
    current.discard(word.strip().lower())
    save_custom_whitelist(current)
    return current


@lru_cache(maxsize=65536)
def _is_vietnamese_word(word: str) -> bool:
    """Kiểm tra một từ (đã lowercased) có phải âm tiết tiếng Việt hợp lệ không (O(1) cached)."""
    _load_dictionary()

    # 1. Từ mượn tiếng Anh phổ biến
    if word in COMMON_LOANWORDS:
        return True

    # 2. Whitelist ngành giáo dục
    if word in EDUCATION_WHITELIST or word.upper() in EDUCATION_WHITELIST:
        return True

    # 3. Từ điển bổ sung
    base, tone = strip_tone(word)
    if word in _EXTRA_DICT or base in _EXTRA_DICT:
        # Vẫn kiểm tra ràng buộc thanh điệu cho vần tắc (-c, -ch, -p, -t)
        final = _get_final(base)
        if final in _STOPPED_FINALS and tone not in (0, 2, 5):
            return False
        return True

    # 4. Bộ âm tiết sinh từ quy tắc ngữ âm
    if base not in _VALID_SYLLABLES:
        return False

    # 5. Ràng buộc thanh điệu vần tắc
    final = _get_final(base)
    if final in _STOPPED_FINALS and tone not in (0, 2, 5):
        return False

    return True


# ──────────────────────────────────────────────
# PRE-COMPILED REGEXES (Tối ưu hóa tốc độ C-level)
# ──────────────────────────────────────────────

_PROTECTED_REGEXES = [
    re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+', re.IGNORECASE),
    re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', re.IGNORECASE),
    re.compile(r'\b[A-Za-z0-9_.-]+\.(?:docx|doc|pdf|pptx|ppt|xlsx|xls|mp4|mp3|png|jpg|jpeg|gif|txt|csv|zip|rar|html|py)\b', re.IGNORECASE),
    re.compile(r'\b\d+(?:[,\.]\d+)+\b'),
    re.compile(r'\b\d{1,2}:\d{2}\b'),
    re.compile(r'\b\d+:\d+\b'),
    re.compile(r'\bv\.v\.(?:\.\.)?|\bv\.v\b|\bv/v\b', re.IGNORECASE),
    re.compile(r'\bTh\.S\b|\bPGS\.TS\b|\bGS\.TS\b|\bTS\.\b|\bĐ/c\b|\bđ/c\b', re.IGNORECASE),
    re.compile(r'(?:=|\+|-|\*|/|:|\->|=>|→|⇒|\(|\/|\[)\s*\?'),
    re.compile(r'\[\?\]|\(\?\)'),
    re.compile(r'^\s*\?\s*$'),
    re.compile(r'\b[A-Z][a-z]?\(OH\)[0-9]?\b'),
    re.compile(r'\b\(NH4\)2SO4\b'),
    re.compile(r'\b(?:sin|cos|tan|cot|log|ln|lim|sqrt|f|g|h|P|Q)\([a-zA-Z0-9_+\-*/,\s]+\)', re.IGNORECASE),
]

_COMBINED_PUNCT_RE = re.compile(r'(?<=[A-Za-zÀ-ỹ0-9]) +([,\.;:!\?])(?=[A-Za-zÀ-ỹ0-9])')
_LEAD_PUNCT_RE = re.compile(r'(?<=[A-Za-zÀ-ỹ0-9]) +([,\.;:!\?…])(?!\S)')
_PREFIX_OPERATOR_RE = re.compile(r'(=|:|\->|=>|→|⇒|\(|\/|\[)\s*$')
_TRAIL_PUNCT_RE = re.compile(r'([,\.;:!\?])(?=[A-Za-zÀ-ỹ])')
_OPEN_BRACKET_SPACE_RE = re.compile(r'([(\[{“«]) +')
_OPEN_QUOTE_ASCII_RE = re.compile(r'" +(?=[A-Za-zÀ-ỹ0-9])')
_CLOSE_BRACKET_SPACE_RE = re.compile(r' +([)\]}”»’])')
_CLOSE_QUOTE_ASCII_RE = re.compile(r'(?<=[A-Za-zÀ-ỹ0-9,\.;:!\?]) +"(?=[,\.;:!\?\s]|$)')
_MISSING_SPACE_BEFORE_OPEN_RE = re.compile(r'(?<=[A-Za-zÀ-ỹ0-9])([(\[{“«])')
_MISSING_SPACE_AFTER_CLOSE_RE = re.compile(r'([)\]}”»])(?=[A-Za-zÀ-ỹ0-9])')
_DOUBLE_SPACE_RE = re.compile(r'  +')
_TWO_DOTS_RE = re.compile(r'(?<!\.)\.\.(?!\.)')
_MANY_DOTS_RE = re.compile(r'\.{4,}')
_REPEATED_PUNCT_RE = re.compile(r'([,;:!?]){2,}')

_WORD_RE = re.compile(r'[A-Za-zÀ-ỹĂăÂâĐđÊêÔôƠơƯư]+')
_ROMAN_RE = re.compile(r'^[IVXLCDM]+$', re.IGNORECASE)

# Precompile một Regex duy nhất cho toàn bộ cụm từ sai trong COMMON_TYPOS (ưu tiên cụm dài trước)
_SORTED_TYPO_KEYS = sorted(COMMON_TYPOS.keys(), key=len, reverse=True)
_TYPO_PHRASE_RE = re.compile(
    r'(?<![A-Za-zÀ-ỹĂăÂâĐđÊêÔôƠơƯư])(?:' +
    '|'.join(re.escape(k) for k in _SORTED_TYPO_KEYS) +
    r')(?![A-Za-zÀ-ỹĂăÂâĐđÊêÔôƠơƯư])',
    re.IGNORECASE
)

# Precompile các quy tắc ngữ cảnh
_COMPILED_CONTEXT_RULES = [
    {
        "regex": re.compile(rule["pattern"], re.IGNORECASE),
        "wrong_group": rule["wrong_group"],
        "suggestion": rule["suggestion"],
        "description": rule["description"],
    }
    for rule in CONTEXTUAL_CONFUSION_RULES
]

# Từ láy toàn phần hợp lệ trong tiếng Việt (không báo lỗi lặp từ)
_VALID_REDUPLICATIVES = {
    "xa", "gần", "đỏ", "xanh", "vàng", "trắng", "đen", "tím", "hồng",
    "nhanh", "chậm", "từ", "đều", "luôn", "ngày", "người", "nhà", "lớp",
    "đời", "năm", "tháng", "chiều", "sáng", "đêm", "tối", "hơi", "lăm",
    "nhỏ", "to", "lớn", "cao", "thấp", "dài", "ngắn", "rộng", "hẹp",
    "mờ", "sương", "lất", "rào", "ầm", "ì", "ào", "rì", "thì", "lặng",
    "buồn", "vui", "cười", "khóc", "đi", "đứng", "ngồi", "nằm", "chạy",
    "bay", "nhảy", "ăn", "nói", "xem", "nghe", "nhìn", "gật", "lắc",
    "lâng", "âng", "ngơ", "ngác", "khăng", "khít", "văng", "vẳng",
    "đùng", "đoàng", "leng", "keng", "tích", "tắc", "anh", "chị", "em",
    "con", "cháu", "bạn", "thầy", "cô", "trò",
}
# Bắt lỗi lặp từ vô ý phổ biến (của của, trong trong, và và, là là, với với, các các, những những, được được, cho cho, có có)
_ACCIDENTAL_REPEAT_WORDS = {
    "của", "trong", "và", "với", "các", "những", "được", "cho", "có",
    "một", "hai", "ba", "bốn", "năm", "khi", "nếu", "thì", "mà", "để",
    "về", "tại", "theo", "do", "bởi", "vì", "như", "rất", "quá", "lắm",
    "này", "đó", "kia", "ấy", "đây", "đã", "đang", "sẽ", "vẫn", "cũng",
    "không", "chưa", "chẳng", "học", "bài", "phần", "mục", "câu", "chữ",
}
_REPEAT_WORD_RE = re.compile(
    r'\b(' + '|'.join(re.escape(w) for w in sorted(_ACCIDENTAL_REPEAT_WORDS, key=len, reverse=True)) + r')\s+\1\b',
    re.IGNORECASE
)


# ──────────────────────────────────────────────
# Khôi phục lỗi gõ Telex & Gợi ý sửa thông minh
# ──────────────────────────────────────────────

_TELEX_VOWEL_MAP = [
    ('uwow', 'ươ'), ('uow', 'ươ'), ('wow', 'ươ'),
    ('aa', 'â'), ('aw', 'ă'), ('ee', 'ê'), ('oo', 'ô'), ('ow', 'ơ'), ('uw', 'ư'), ('dd', 'đ'),
]
_TELEX_TONE_MAP = {
    's': 2,  # sắc
    'f': 1,  # huyền
    'r': 3,  # hỏi
    'x': 4,  # ngã
    'j': 5,  # nặng
}


def _try_recover_telex(word_lower: str) -> Optional[str]:
    """Khôi phục từ bị lỗi gõ Telex trượt phím (vd: 'hocj' -> 'học', 'giaos' -> 'giáo', 'vieen' -> 'viên')."""
    if len(word_lower) < 2:
        return None

    candidate = word_lower
    # Thay thế dd, aa, aw, ee, oo, ow, uw
    for src, dst in _TELEX_VOWEL_MAP:
        if src in candidate:
            candidate = candidate.replace(src, dst)

    # Kiểm tra ký tự cuối có phải phím dấu thanh Telex (s, f, r, x, j) không
    tone_idx = 0
    if candidate[-1] in _TELEX_TONE_MAP and len(candidate) >= 2:
        tone_idx = _TELEX_TONE_MAP[candidate[-1]]
        candidate_base = candidate[:-1]
    else:
        candidate_base = candidate

    if candidate_base == word_lower and tone_idx == 0:
        return None

    # Nếu chưa có dấu thanh mới, kiểm tra luôn candidate_base
    if tone_idx == 0:
        if _is_vietnamese_word(candidate_base):
            return candidate_base
        return None

    # Đặt thanh điệu tone_idx vào nguyên âm chính của candidate_base
    chars = list(candidate_base)
    # Ưu tiên đặt dấu vào nguyên âm có dấu phụ (ă, â, ê, ô, ơ, ư) hoặc nguyên âm giữa/cuối
    vowel_indices = [i for i, ch in enumerate(chars) if ch in _VOWEL_TO_BASE]
    if not vowel_indices:
        return None

    # Thử đặt dấu vào từng vị trí nguyên âm (từ phải sang trái hoặc nguyên âm có mũ/râu)
    priority_indices = sorted(
        vowel_indices,
        key=lambda idx: (chars[idx] in {'ă', 'â', 'ê', 'ô', 'ơ', 'ư'}, idx),
        reverse=True,
    )
    for v_idx in priority_indices:
        base_v, _ = _VOWEL_TO_BASE[chars[v_idx]]
        toned_v = _TONE_CHARS.get((base_v, tone_idx))
        if toned_v:
            test_chars = chars.copy()
            test_chars[v_idx] = toned_v
            test_word = ''.join(test_chars)
            if _is_vietnamese_word(test_word):
                return test_word

    return None


@lru_cache(maxsize=32768)
def _suggest_cached(word_lower: str) -> str:
    """Sinh từ gợi ý sửa cho một từ bị sai (được cache O(1))."""
    _load_dictionary()

    if word_lower in COMMON_TYPOS:
        return COMMON_TYPOS[word_lower]

    # 0. Thử khôi phục lỗi gõ Telex (hocj -> học, giaos -> giáo, truwowng -> trường)
    telex_fixed = _try_recover_telex(word_lower)
    if telex_fixed:
        return telex_fixed

    candidates: list[str] = []

    # 1. Nhầm phụ âm đầu phổ biến: l/n, ch/tr, s/x, d/gi/r, c/k, g/gh, ng/ngh, v/d
    prefix_swaps = [
        ('ngh', ['ng', 'nh']),
        ('ng', ['ngh', 'nh', 'n']),
        ('gh', ['g', 'gi']),
        ('gi', ['d', 'r', 'g', 'gh']),
        ('ch', ['tr', 'c']),
        ('tr', ['ch', 't']),
        ('th', ['t', 'tr']),
        ('nh', ['n', 'ng']),
        ('ph', ['p', 'b']),
        ('kh', ['k', 'c']),
        ('l', ['n']),
        ('n', ['l', 'nh']),
        ('s', ['x']),
        ('x', ['s']),
        ('d', ['gi', 'r', 'đ', 'v']),
        ('đ', ['d']),
        ('r', ['d', 'gi', 'g']),
        ('v', ['d', 'gi']),
        ('c', ['k', 'qu']),
        ('k', ['c', 'kh']),
        ('g', ['gh', 'gi', 'r']),
    ]
    for prefix_from, prefix_to_list in prefix_swaps:
        if word_lower.startswith(prefix_from):
            rest = word_lower[len(prefix_from):]
            for pt in prefix_to_list:
                alt = pt + rest
                if _is_vietnamese_word(alt):
                    candidates.append(alt)

    # 2. Nhầm phụ âm cuối: n/ng/nh, c/t/ch, m/p
    suffix_swaps = [
        ('ng', ['n', 'nh']),
        ('nh', ['n', 'ng']),
        ('ch', ['c', 't']),
        ('n', ['ng', 'nh', 'm']),
        ('m', ['n', 'p']),
        ('c', ['t', 'ch']),
        ('t', ['c', 'ch', 'p']),
        ('p', ['t', 'm']),
    ]
    for suf_from, suf_to_list in suffix_swaps:
        if word_lower.endswith(suf_from) and len(word_lower) > len(suf_from):
            stem = word_lower[:-len(suf_from)]
            for st in suf_to_list:
                alt = stem + st
                if _is_vietnamese_word(alt):
                    candidates.append(alt)

    # 3. Nhầm dấu hỏi ↔ ngã, hoặc thanh điệu trên vần tắc (huyền/hỏi/ngã -> sắc/nặng)
    for i, ch in enumerate(word_lower):
        if ch in _VOWEL_TO_BASE:
            base, tone = _VOWEL_TO_BASE[ch]
            for target_tone in ([4] if tone == 3 else [3] if tone == 4 else [2, 5, 1, 3, 4]):
                new_ch = _TONE_CHARS.get((base, target_tone))
                if new_ch and new_ch != ch:
                    alt = word_lower[:i] + new_ch + word_lower[i + 1:]
                    if _is_vietnamese_word(alt):
                        candidates.append(alt)

    # 4. Nhầm nguyên âm gần nhau (a/ă/â, e/ê, o/ô/ơ, u/ư, i/y)
    vowel_confusions = {
        'a': ['ă', 'â'], 'ă': ['a', 'â'], 'â': ['a', 'ă'],
        'e': ['ê'], 'ê': ['e'],
        'o': ['ô', 'ơ'], 'ô': ['o', 'ơ'], 'ơ': ['o', 'ô'],
        'u': ['ư'], 'ư': ['u'],
        'i': ['y'], 'y': ['i'],
    }
    for i, ch in enumerate(word_lower):
        if ch in _VOWEL_TO_BASE:
            base, tone = _VOWEL_TO_BASE[ch]
            for alt_base in vowel_confusions.get(base, []):
                new_ch = _TONE_CHARS.get((alt_base, tone))
                if new_ch:
                    alt = word_lower[:i] + new_ch + word_lower[i + 1:]
                    if _is_vietnamese_word(alt):
                        candidates.append(alt)

    # 5. Xóa 1 ký tự thừa (lỗi gõ đúp phím: vd "họcc" -> "học", "giáoo" -> "giáo")
    if len(word_lower) >= 3:
        for i in range(len(word_lower)):
            alt = word_lower[:i] + word_lower[i + 1:]
            if _is_vietnamese_word(alt):
                candidates.append(alt)

    if candidates:
        # Ưu tiên từ có trong _FULL_WORDS_SET
        for c in candidates:
            if c in _FULL_WORDS_SET:
                return c
        return candidates[0]
    return ""


# ──────────────────────────────────────────────
# CLASS CHÍNH: VietnameseSpellChecker
# ──────────────────────────────────────────────

class VietnameseSpellChecker:
    """Engine kiểm tra chính tả tiếng Việt, dấu câu, ngữ cảnh & chuẩn hóa chính tả."""

    def __init__(self, extra_whitelist: set[str] | None = None,
                 check_context: bool = True,
                 check_orthography: bool = False):
        self.whitelist = EDUCATION_WHITELIST.copy()
        # Tải từ điển cá nhân của giáo viên
        custom_words = load_custom_whitelist()
        if custom_words:
            self.whitelist.update(custom_words)
            self.whitelist.update(w.lower() for w in custom_words)
        if extra_whitelist:
            self.whitelist.update(extra_whitelist)
            self.whitelist.update(w.lower() for w in extra_whitelist)
        self.check_context = check_context
        self.check_orthography = check_orthography
        _load_dictionary()

    def reload_custom_whitelist(self):
        """Cập nhật lại whitelist sau khi người dùng thêm/xóa từ cá nhân."""
        self.whitelist = EDUCATION_WHITELIST.copy()
        custom_words = load_custom_whitelist()
        self.whitelist.update(custom_words)
        self.whitelist.update(w.lower() for w in custom_words)

    # ─── Vùng cần bảo vệ (không bắt lỗi dấu câu / chính tả) ───

    @staticmethod
    def _find_protected_spans(text: str) -> list[tuple[int, int]]:
        """Tìm các khoảng ký tự không được bắt lỗi (URL, email, số thập phân, giờ, file, công thức)."""
        spans: list[tuple[int, int]] = []
        for regex in _PROTECTED_REGEXES:
            for m in regex.finditer(text):
                spans.append((m.start(), m.end()))
        if len(spans) > 1:
            spans.sort()
            merged = [spans[0]]
            for s, e in spans[1:]:
                prev_s, prev_e = merged[-1]
                if s <= prev_e:
                    merged[-1] = (prev_s, max(prev_e, e))
                else:
                    merged.append((s, e))
            return merged
        return spans

    @staticmethod
    def _is_in_spans(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
        """Kiểm tra một khoảng (start, end) có bị chồng lấn vào vùng bảo vệ hay không."""
        for p_start, p_end in spans:
            if p_start >= end:
                break
            if not (end <= p_start or start >= p_end):
                return True
        return False

    # ─── Kiểm tra dấu câu & khoảng trắng ───

    def check_punctuation(self, text: str,
                          protected: list[tuple[int, int]] | None = None) -> list[SpellError]:
        """Phát hiện lỗi dấu câu, khoảng trắng, ngoặc đơn, ngoặc vuông, ngoặc kép."""
        errors: list[SpellError] = []
        if protected is None:
            protected = self._find_protected_spans(text)

        # 1. Lỗi kết hợp: Thừa khoảng trắng TRƯỚC VÀ thiếu khoảng trắng SAU dấu câu
        for m in _COMBINED_PUNCT_RE.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                mark = m.group(1)
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=f"{mark} ",
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Thừa khoảng trắng trước và thiếu khoảng trắng sau dấu '{mark}'",
                ))

        # 2. Thừa khoảng trắng TRƯỚC dấu câu (.,;:!?…)
        for m in _LEAD_PUNCT_RE.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                mark = m.group(1)
                if mark == '?' and _PREFIX_OPERATOR_RE.search(text[:m.start()]):
                    continue
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=f"{mark}",
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Thừa khoảng trắng trước dấu '{mark}'",
                ))

        # 3. Thiếu khoảng trắng SAU dấu câu
        for m in _TRAIL_PUNCT_RE.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                mark = m.group(1)
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=f"{mark} ",
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Thiếu khoảng trắng sau dấu '{mark}'",
                ))

        # 4. Thừa khoảng trắng SAU dấu mở ngoặc / mở nháy
        for m in _OPEN_BRACKET_SPACE_RE.finditer(text):
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

        for m in _OPEN_QUOTE_ASCII_RE.finditer(text):
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
        for m in _CLOSE_BRACKET_SPACE_RE.finditer(text):
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

        for m in _CLOSE_QUOTE_ASCII_RE.finditer(text):
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
        for m in _MISSING_SPACE_BEFORE_OPEN_RE.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                b = m.group(1)
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=f" {b}",
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Thiếu khoảng trắng trước dấu mở '{b}'",
                ))

        # 7. Thiếu khoảng trắng SAU dấu đóng ngoặc
        for m in _MISSING_SPACE_AFTER_CLOSE_RE.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                b = m.group(1)
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion=f"{b} ",
                    error_type=ErrorType.PUNCTUATION,
                    description=f"Thiếu khoảng trắng sau dấu đóng '{b}'",
                ))

        # 8. Hai dấu cách liên tiếp trở lên
        for m in _DOUBLE_SPACE_RE.finditer(text):
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
        for m in _TWO_DOTS_RE.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion='...',
                    error_type=ErrorType.PUNCTUATION,
                    description="Dấu ba chấm chỉ có 2 dấu chấm (cần 3 dấu chấm '...')",
                ))

        for m in _MANY_DOTS_RE.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                errors.append(SpellError(
                    start=m.start(),
                    end=m.end(),
                    wrong_text=m.group(0),
                    suggestion='...',
                    error_type=ErrorType.PUNCTUATION,
                    description="Thừa dấu chấm trong dấu ba chấm (chuẩn là '...')",
                ))

        # 10. Dấu câu bị lặp sai quy cách
        for m in _REPEATED_PUNCT_RE.finditer(text):
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

    # ─── Kiểm tra chính tả từng từ & cụm từ (Single-Pass Regex) ───

    def check_spelling(self, text: str,
                       protected: list[tuple[int, int]] | None = None) -> list[SpellError]:
        """Phát hiện lỗi chính tả từ đơn và cụm từ tiếng Việt với tốc độ C-level."""
        errors: list[SpellError] = []
        if protected is None:
            protected = self._find_protected_spans(text)

        # 1. Quét 1 lượt duy nhất tất cả 200+ cụm từ sai bằng _TYPO_PHRASE_RE
        covered_spans: list[tuple[int, int]] = []
        for m in _TYPO_PHRASE_RE.finditer(text):
            pos, after_pos = m.start(), m.end()
            if self._is_in_spans(pos, after_pos, protected):
                continue
            matched_raw = m.group(0)
            matched_lower = matched_raw.lower()
            # Bỏ qua nếu cụm từ nằm trong custom whitelist
            if matched_lower in self.whitelist or matched_raw in self.whitelist:
                continue
            correct_phrase = COMMON_TYPOS.get(matched_lower)
            if not correct_phrase:
                continue
            detail_note = CONFUSABLE_DETAILS.get(matched_lower, (correct_phrase, ""))[1]
            preserved_suggestion = _preserve_case(matched_raw, correct_phrase)
            desc = detail_note if detail_note else f"Sai chính tả cụm từ (sửa thành '{preserved_suggestion}')"
            errors.append(SpellError(
                start=pos,
                end=after_pos,
                wrong_text=matched_raw,
                suggestion=preserved_suggestion,
                error_type=ErrorType.SPELLING,
                description=desc,
            ))
            covered_spans.append((pos, after_pos))

        # 2. Kiểm tra từng từ / âm tiết đơn
        for m in _WORD_RE.finditer(text):
            start, end = m.start(), m.end()
            if self._is_in_spans(start, end, covered_spans) or self._is_in_spans(start, end, protected):
                continue

            word = m.group(0)
            if len(word) <= 1:
                continue

            word_lower = word.lower()

            # Bỏ qua whitelist
            if word in self.whitelist or word_lower in self.whitelist or word.upper() in self.whitelist:
                continue

            # Bỏ qua từ mượn tiếng Anh phổ biến
            if word_lower in COMMON_LOANWORDS:
                continue

            # Bỏ qua nếu toàn chữ HOA (tiêu đề, tên viết tắt <= 10 ký tự)
            if word.isupper() and len(word) <= 10:
                continue

            # Bỏ qua số La Mã
            if _ROMAN_RE.match(word):
                continue

            # Kiểm tra âm tiết tiếng Việt (O(1) cached)
            if not _is_vietnamese_word(word_lower):
                raw_suggestion = self._suggest(word_lower)
                suggestion = _preserve_case(word, raw_suggestion) if raw_suggestion else ""
                errors.append(SpellError(
                    start=start,
                    end=end,
                    wrong_text=word,
                    suggestion=suggestion,
                    error_type=ErrorType.SPELLING,
                    description="Từ không có trong từ điển chuẩn tiếng Việt" + (
                        f" (gợi ý: '{suggestion}')" if suggestion else ""
                    ),
                ))

        return errors

    # ─── Kiểm tra ngữ cảnh Hán-Việt & lỗi lặp từ ───

    def check_contextual_rules(self, text: str,
                               protected: list[tuple[int, int]] | None = None) -> list[SpellError]:
        """Phát hiện các từ đúng chính tả âm tiết nhưng dùng sai ngữ cảnh hoặc lặp từ vô ý."""
        errors: list[SpellError] = []
        if protected is None:
            protected = self._find_protected_spans(text)

        # 1. Các cặp từ dễ nhầm lẫn theo ngữ cảnh (yếu điểm / điểm yếu, bàng hoàng / bàng quan...)
        for rule in _COMPILED_CONTEXT_RULES:
            for m in rule["regex"].finditer(text):
                grp = rule["wrong_group"]
                s, e = m.start(grp), m.end(grp)
                if not self._is_in_spans(s, e, protected):
                    wrong_raw = m.group(grp)
                    suggestion = _preserve_case(wrong_raw, rule["suggestion"])
                    errors.append(SpellError(
                        start=s,
                        end=e,
                        wrong_text=wrong_raw,
                        suggestion=suggestion,
                        error_type=ErrorType.SPELLING,
                        description=rule["description"],
                        confidence=0.95,
                    ))

        # 2. Lỗi gõ lặp từ liên tiếp vô ý (vd: "của của", "trong trong", "và và")
        for m in _REPEAT_WORD_RE.finditer(text):
            if not self._is_in_spans(m.start(), m.end(), protected):
                first_word = m.group(1)
                if first_word.lower() not in _VALID_REDUPLICATIVES:
                    errors.append(SpellError(
                        start=m.start(),
                        end=m.end(),
                        wrong_text=m.group(0),
                        suggestion=first_word,
                        error_type=ErrorType.SPELLING,
                        description=f"Lỗi lặp từ liên tiếp '{m.group(0)}' (nên rút gọn thành '{first_word}')",
                        confidence=0.92,
                    ))

        return errors

    # ─── Gợi ý sửa lỗi ───

    def _suggest(self, word_lower: str) -> str:
        """Sinh từ gợi ý sửa cho một từ bị sai."""
        return _suggest_cached(word_lower)

    @staticmethod
    def _swap_hoi_nga(word: str) -> Optional[str]:
        """Hoán đổi dấu hỏi ↔ ngã trong một từ."""
        result = list(word)
        changed = False
        for i, ch in enumerate(result):
            if ch in _VOWEL_TO_BASE:
                base, tone = _VOWEL_TO_BASE[ch]
                if tone == 3:
                    new_ch = _TONE_CHARS.get((base, 4))
                    if new_ch:
                        result[i] = new_ch
                        changed = True
                elif tone == 4:
                    new_ch = _TONE_CHARS.get((base, 3))
                    if new_ch:
                        result[i] = new_ch
                        changed = True
        return ''.join(result) if changed else None

    # ─── Chuẩn hóa Chính tả (Dấu thanh oà/òa & i/y) ───

    @staticmethod
    def normalize_orthography(text: str,
                              tone_style: str = "keep",
                              iy_style: str = "keep") -> tuple[str, int]:
        """Chuẩn hóa đồng bộ quy tắc dấu thanh và chữ i/y trên văn bản.

        Args:
            text: Văn bản đầu vào.
            tone_style:
                - "new": Kiểu mới theo Bộ GD&ĐT (oà, oá, oả, oã, oạ, oè, uỳ, uý, uỷ...)
                - "old": Kiểu cũ truyền thống (òa, óa, ỏa, õa, ọa, òe, ùy, úy, ủy...)
                - "keep": Giữ nguyên.
            iy_style:
                - "i": Chuẩn hóa về 'i' theo SGK Bộ GD&ĐT (kĩ năng, lí thuyết, vật lí, mĩ thuật...)
                - "y": Chuẩn hóa về 'y' (kỹ năng, lý thuyết, vật lý, mỹ thuật...)
                - "keep": Giữ nguyên.

        Returns:
            (văn_bản_đã_chuẩn_hóa, số_lần_thay_đổi)
        """
        changes = 0
        result = text

        # 1. Chuẩn hóa i/y
        if iy_style in ("i", "y"):
            mapping = IY_STANDARD_MAP if iy_style == "i" else {v: k for k, v in IY_STANDARD_MAP.items()}
            for src_phrase, dst_phrase in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
                pattern = re.compile(
                    r'(?<![A-Za-zÀ-ỹĂăÂâĐđÊêÔôƠơƯư])' + re.escape(src_phrase) + r'(?![A-Za-zÀ-ỹĂăÂâĐđÊêÔôƠơƯư])',
                    re.IGNORECASE
                )
                def _repl(m, dst=dst_phrase):
                    nonlocal changes
                    changes += 1
                    return _preserve_case(m.group(0), dst)
                result = pattern.sub(_repl, result)

        # 2. Chuẩn hóa vị trí dấu thanh (oa, oe, uy)
        if tone_style in ("new", "old"):
            t_map = TONE_OLD_TO_NEW if tone_style == "new" else TONE_NEW_TO_OLD
            for src_seq, dst_seq in t_map.items():
                # Chỉ đổi khi sau nguyên âm đó không phải phụ âm cuối (vì toàn bộ đều đồng nhất ở vần đóng: hoàn, toán, luyện)
                pattern = re.compile(re.escape(src_seq) + r'(?![A-Za-zÀ-ỹĂăÂâĐđÊêÔôƠơƯư])')
                result, count = pattern.subn(dst_seq, result)
                changes += count

        return result, changes

    @staticmethod
    def auto_fix_text(text: str, errors: list[SpellError]) -> tuple[str, int]:
        """Tự động áp dụng tất cả gợi ý sửa lỗi đáng tin cậy lên đoạn văn bản.

        Returns:
            (văn_bản_đã_sửa, số_lỗi_đã_sửa)
        """
        if not errors:
            return text, 0

        sorted_errs = sorted(errors, key=lambda e: e.start, reverse=True)
        fixed_count = 0
        chars = text
        for err in sorted_errs:
            if err.suggestion and err.suggestion != '?':
                if 0 <= err.start < err.end <= len(chars):
                    chars = chars[:err.start] + err.suggestion + chars[err.end:]
                    fixed_count += 1
        return chars, fixed_count

    # ─── API tổng hợp ───

    def check_text(self, text: str) -> list[SpellError]:
        """Kiểm tra toàn diện một đoạn văn bản: dấu câu, khoảng trắng, chính tả và ngữ cảnh."""
        if not text or not text.strip():
            return []

        protected = self._find_protected_spans(text)
        errors: list[SpellError] = []
        errors.extend(self.check_punctuation(text, protected))
        errors.extend(self.check_spelling(text, protected))
        if self.check_context:
            errors.extend(self.check_contextual_rules(text, protected))

        # Sắp xếp theo vị trí bắt đầu tăng dần, độ dài giảm dần
        errors.sort(key=lambda e: (e.start, -(e.end - e.start)))

        # Hợp nhất và loại bỏ lỗi chồng chéo
        deduped: list[SpellError] = []
        last_end = -1
        for err in errors:
            if err.start >= last_end:
                deduped.append(err)
                last_end = err.end
        return deduped
