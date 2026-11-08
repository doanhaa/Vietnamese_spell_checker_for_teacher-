"""
core – Bộ xử lý trung tâm của Phần mềm Kiểm tra & Chuẩn hóa Giáo án Pro v2.0.
"""

from .constants import ErrorType, EDUCATION_WHITELIST, COMMON_LOANWORDS, CONFUSABLE_DETAILS, COMMON_TYPOS
from .spell_checker import VietnameseSpellChecker, SpellError
from .format_validator import FormatValidator, FormatReport, FormatError, auto_fix_document_format
from .docx_processor import DocxProcessor, ProcessingStats, ErrorDetail
from .online_checker import OnlineHighPrecisionChecker, WordLookupResult

__all__ = [
    "ErrorType",
    "EDUCATION_WHITELIST",
    "COMMON_LOANWORDS",
    "CONFUSABLE_DETAILS",
    "COMMON_TYPOS",
    "VietnameseSpellChecker",
    "SpellError",
    "FormatValidator",
    "FormatReport",
    "FormatError",
    "auto_fix_document_format",
    "DocxProcessor",
    "ProcessingStats",
    "ErrorDetail",
    "OnlineHighPrecisionChecker",
    "WordLookupResult",
]
