"""
constants.py – Hằng số dùng chung cho toàn bộ dự án.
"""

from enum import Enum

# ──────────────────────────────────────────────
# 1. Whitelist – Viết tắt ngành Giáo dục & Đơn vị đo lường
# ──────────────────────────────────────────────
EDUCATION_WHITELIST: set[str] = {
    # Chức danh / vai trò
    "GV", "HS", "PH", "GVCN", "CBQL", "BGH", "HT", "PHT",
    "GS", "PGS", "TS", "THS", "ThS", "CN", "KS", "BS",
    "TTND", "NGND", "NGƯT", "Đ/c", "đ/c",

    # Sách / tài liệu / chương trình
    "SGK", "SBT", "SGV", "TL", "TLTK", "KHDH", "KHBD", "KH", "PPCT", "TKB",

    # Cấp học / trường
    "TH", "THCS", "THPT", "MN", "ĐH", "CĐ", "GDTX",
    "TH&THCS", "THCS&THPT",

    # Cơ quan quản lý / hành chính
    "BGDĐT", "SGDĐT", "PGDĐT", "UBND", "HĐND", "TW", "CP",

    # Đánh giá / kiểm tra
    "ĐGTX", "ĐGĐK", "ĐGGK", "ĐG", "KT", "GK", "CK",
    "HKI", "HKII", "GKI", "GKII",

    # Công nghệ / phương pháp
    "CNTT", "STEM", "STEAM", "ICT", "AI", "LMS",
    "PPDH", "KTDH", "PP",

    # Hoạt động / mục / hồ sơ
    "HĐ", "NXB", "TPHCM", "HN", "CV", "QĐ", "TT", "KH",
    "VD", "BT", "TB", "TP",

    # Năng lực / phẩm chất (CV 5512, CT GDPT 2018)
    "NL", "PC", "NLTT", "NLĐC",

    # Phân môn / lĩnh vực
    "GDCD", "GDĐP", "KHTN", "KHXH", "TNXH", "HĐTN", "HĐTNHN",

    # Nền tảng học tập phổ biến trong trường học
    "VIOLET", "OLM", "SHUB", "AZOTA", "KAHOOT", "PADLET",
    "QUIZIZZ", "CANVA", "ZOOM", "TEAMS",

    # Số La Mã (thường dùng trong tiêu đề, mục lục)
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII",

    # Đơn vị đo lường chuẩn
    "km", "m", "cm", "mm", "nm", "kg", "g", "mg", "l", "ml", "ha",
    "m2", "m3", "cm2", "cm3", "km2", "m²", "m³", "cm²", "cm³", "km²",
    "s", "ms", "min", "h", "kw", "kwh", "w", "v", "a",
    "hz", "khz", "mhz", "ghz", "mb", "gb", "tb", "kb",
    "byte", "bit", "dpi", "px", "pixel", "pt", "emu",
    "°C", "°F", "K", "%",

    # Viết tắt thông dụng khác
    "v.v.", "v.v", "vv", "v/v", "etc",
}

# ──────────────────────────────────────────────
# 2. Từ mượn tiếng Anh phổ biến trong giáo dục & đời sống
# ──────────────────────────────────────────────
COMMON_LOANWORDS: set[str] = {
    # Thiết bị & phương tiện
    "tivi", "tv", "rubik", "video", "clip", "slide", "laptop", "smartphone",
    "projector", "micro", "mic", "loa", "radio", "camera", "cam",
    "scanner", "printer", "usb", "wifi", "bluetooth", "mouse", "keyboard",
    "pc", "card", "sim", "chip", "ram", "cpu", "robot", "drone", "tablet",
    "ipad", "headphone", "headset", "monitor", "cable", "adapter", "router",
    "modem", "server", "cloud", "data", "drive", "folder", "file",

    # Nền tảng, phần mềm & ứng dụng
    "internet", "website", "web", "online", "offline", "link", "app", "qr",
    "code", "email", "mail", "gmail", "inbox", "chat", "message", "sms",
    "hotline", "facebook", "fb", "zalo", "youtube", "tiktok", "google",
    "meet", "form", "forms", "doc", "docs", "sheet", "sheets", "slides",
    "classroom", "teams", "zoom", "powerpoint", "word", "excel", "pdf",
    "canva", "padlet", "kahoot", "quizizz", "azota", "shub", "olm", "violet",
    "lms", "portal", "fanpage", "admin", "post", "comment", "share", "like",
    "subscribe", "follow", "stream", "livestream", "podcast", "vlog", "blog",

    # Thuật ngữ dạy học / STEM / Hoạt động
    "stem", "steam", "coding", "ai", "game", "games", "team", "group",
    "feedback", "check", "test", "tests", "quiz", "mini", "audio", "mc",
    "banner", "poster", "standee", "logo", "rubric", "checklist", "kpi",
    "timeline", "deadline", "task", "project", "workshop", "seminar", "webinar",
    "step", "part", "unit", "lesson", "topic", "theme", "skill", "reading",
    "writing", "speaking", "listening", "grammar", "vocabulary", "pronunciation",
    "practice", "review", "exam", "homework", "warmup", "warm-up",
    "icebreaker", "ice-breaking", "brainstorming", "mindmap", "mind-map",
    "mind", "map", "wrapup", "wrap-up", "pass", "fail", "score", "rank",
    "level", "note", "copy", "paste", "save", "print", "scan", "click",
    "drag", "drop", "view", "mode", "status", "setting", "settings",
    "layout", "setup", "menu", "option", "font", "format", "size", "color",
    "style", "bullet", "table", "cell", "row", "column", "margin", "spacing",
    "align", "bold", "italic", "underline",

    # Tên môn học tiếng Anh
    "english", "math", "maths", "science", "physics", "chemistry", "biology",
    "history", "geography", "literature", "music", "art", "arts", "informatics",
    "civics", "technology", "physical", "education", "pe", "ict",

    # Từ mượn đời sống quen thuộc
    "cafe", "cà phê", "pizza", "snack", "sandwich", "burger", "fastfood",
    "supermarket", "market", "mall", "bar", "club", "gym", "yoga", "fitness",
    "spa", "golf", "tennis", "football", "billiards", "bida", "bowling",
    "marathon", "checkin", "check-in", "checkout", "check-out", "homestay",
    "resort", "hotel", "motel", "voucher", "coupon", "sale", "freeship",
    "order", "shipper", "ship", "fan", "fans", "idol", "trend", "trending",
    "viral", "hot", "cool", "fashion", "model", "show", "event", "teaser",
    "trailer", "remix", "cover", "hit", "beat", "tune", "tour", "combo",
    "set", "top", "pro", "plus", "max", "ultra", "lite", "smart", "eco",
    "vip", "pr",
}

# ──────────────────────────────────────────────
# 3. Loại lỗi
# ──────────────────────────────────────────────
class ErrorType(str, Enum):
    SPELLING = "Lỗi chính tả"
    PUNCTUATION = "Lỗi dấu câu / khoảng trắng"
    FONT = "Lỗi font chữ"
    FONT_SIZE = "Lỗi cỡ chữ"
    MARGIN = "Lỗi căn lề"
    PAPER_SIZE = "Lỗi khổ giấy"
    STRUCTURE = "Thiếu đề mục CV 5512"

# ──────────────────────────────────────────────
# 4. Cấu trúc Giáo án theo Công văn 5512
# ──────────────────────────────────────────────

# Các đề mục BẮT BUỘC (level 1)
CV5512_REQUIRED_SECTIONS = [
    {
        "id": "I",
        "patterns": [
            r"I\s*[\.\)]\s*MỤC\s*TIÊU",
            r"MỤC\s*TIÊU",
        ],
        "label": "I. MỤC TIÊU",
        "subsections": [
            {
                "id": "I.1",
                "patterns": [
                    r"1\s*[\.\)]\s*(?:Về\s+)?[Kk]iến\s+thức",
                    r"[Kk]iến\s+thức",
                ],
                "label": "1. Kiến thức",
            },
            {
                "id": "I.2",
                "patterns": [
                    r"2\s*[\.\)]\s*(?:Về\s+)?[Nn]ăng\s+lực",
                    r"[Nn]ăng\s+lực",
                ],
                "label": "2. Năng lực",
            },
            {
                "id": "I.3",
                "patterns": [
                    r"3\s*[\.\)]\s*(?:Về\s+)?[Pp]hẩm\s+chất",
                    r"[Pp]hẩm\s+chất",
                ],
                "label": "3. Phẩm chất",
            },
        ],
    },
    {
        "id": "II",
        "patterns": [
            r"II\s*[\.\)]\s*THIẾT\s+BỊ\s+DẠY\s+HỌC\s+VÀ\s+HỌC\s+LIỆU",
            r"THIẾT\s+BỊ\s+DẠY\s+HỌC",
            r"II\s*[\.\)]\s*THIẾT\s+BỊ",
            r"II\s*[\.\)]\s*CHUẨN\s+BỊ",
        ],
        "label": "II. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU",
        "subsections": [],
    },
    {
        "id": "III",
        "patterns": [
            r"III\s*[\.\)]\s*TIẾN\s+TRÌNH\s+DẠY\s+HỌC",
            r"TIẾN\s+TRÌNH\s+DẠY\s+HỌC",
            r"III\s*[\.\)]\s*TỔ\s+CHỨC\s+CÁC\s+HOẠT\s+ĐỘNG",
        ],
        "label": "III. TIẾN TRÌNH DẠY HỌC",
        "subsections": [
            {
                "id": "III.HĐ1",
                "patterns": [
                    r"[Hh]oạt\s+động\s+1\s*[:\.]?\s*(?:[MmXx]ở\s+đầu|[Xx]ác\s+định\s+vấn\s+đề|[Kk]hởi\s+động)",
                    r"HĐ\s*1\s*[:\.]",
                    r"[Hh]oạt\s+động\s+1",
                ],
                "label": "Hoạt động 1: Mở đầu / Xác định vấn đề",
            },
            {
                "id": "III.HĐ2",
                "patterns": [
                    r"[Hh]oạt\s+động\s+2\s*[:\.]?\s*(?:[Hh]ình\s+thành\s+kiến\s+thức|[Kk]hám\s+phá)",
                    r"HĐ\s*2\s*[:\.]",
                    r"[Hh]oạt\s+động\s+2",
                ],
                "label": "Hoạt động 2: Hình thành kiến thức mới",
            },
            {
                "id": "III.HĐ3",
                "patterns": [
                    r"[Hh]oạt\s+động\s+3\s*[:\.]?\s*[Ll]uyện\s+tập",
                    r"HĐ\s*3\s*[:\.]",
                    r"[Hh]oạt\s+động\s+3",
                ],
                "label": "Hoạt động 3: Luyện tập",
            },
            {
                "id": "III.HĐ4",
                "patterns": [
                    r"[Hh]oạt\s+động\s+4\s*[:\.]?\s*[Vv]ận\s+dụng",
                    r"HĐ\s*4\s*[:\.]",
                    r"[Hh]oạt\s+động\s+4",
                ],
                "label": "Hoạt động 4: Vận dụng",
            },
        ],
    },
]

# ──────────────────────────────────────────────
# 5. Thể thức văn bản (Nghị định 30/2020)
# ──────────────────────────────────────────────

# Khổ giấy A4: 210 × 297 mm
PAPER_A4_WIDTH_MM = 210
PAPER_A4_HEIGHT_MM = 297

# Căn lề (đơn vị cm)
MARGIN_LEFT_MIN_CM = 3.0
MARGIN_LEFT_MAX_CM = 3.5
MARGIN_RIGHT_MIN_CM = 1.5
MARGIN_RIGHT_MAX_CM = 2.0
MARGIN_TOP_MIN_CM = 2.0
MARGIN_TOP_MAX_CM = 2.5
MARGIN_BOTTOM_MIN_CM = 2.0
MARGIN_BOTTOM_MAX_CM = 2.5

# Font
REQUIRED_FONT_NAME = "Times New Roman"
REQUIRED_FONT_SIZES = {13, 14}  # Pt

# Hệ số chuyển đổi
CM_TO_EMU = 360000  # 1 cm ≈ 360 000 EMU
PT_TO_HALF_PT = 2    # python-docx font.size đo bằng EMU, 1pt = 12700 EMU
PT_TO_EMU = 12700
MM_TO_EMU = 36000

# ──────────────────────────────────────────────
# 6. Các pattern quy tắc dấu câu / khoảng trắng
# ──────────────────────────────────────────────
PUNCTUATION_RULES = [
    # Thừa khoảng trắng trước dấu câu
    (r' +([,\.;:!\?])', "Thừa khoảng trắng trước dấu câu"),
    # Thiếu khoảng trắng sau dấu câu
    (r'([,\.;:!\?])([A-Za-zÀ-ỹ])', "Thiếu khoảng trắng sau dấu câu"),
    # Hai dấu cách liên tiếp trở lên
    (r'  +', "Hai dấu cách liên tiếp trở lên"),
    # Ngoặc tròn
    (r'(\() +', "Thừa khoảng trắng sau dấu mở ngoặc"),
    (r' +(\))', "Thừa khoảng trắng trước dấu đóng ngoặc"),
    # Ngoặc vuông
    (r'(\[) +', "Thừa khoảng trắng sau dấu mở ngoặc vuông"),
    (r' +(\])', "Thừa khoảng trắng trước dấu đóng ngoặc vuông"),
    # Ngoặc nhọn
    (r'(\{) +', "Thừa khoảng trắng sau dấu mở ngoặc nhọn"),
    (r' +(\})', "Thừa khoảng trắng trước dấu đóng ngoặc nhọn"),
    # Ngoặc kép (ASCII và cong và Pháp)
    (r'([“"«]) +', "Thừa khoảng trắng sau dấu mở nháy"),
    (r' +([”"»])', "Thừa khoảng trắng trước dấu đóng nháy"),
]
