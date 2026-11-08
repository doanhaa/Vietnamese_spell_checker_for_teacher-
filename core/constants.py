"""
constants.py – Hằng số, từ điển ngoại lệ, cặp từ dễ nhầm lẫn và chuẩn CV 5512 / NĐ 30/2020.
"""

from enum import Enum

# ──────────────────────────────────────────────
# 1. Whitelist – Viết tắt ngành Giáo dục & Đơn vị đo lường
# ──────────────────────────────────────────────
EDUCATION_WHITELIST: set[str] = {
    # Chức danh / vai trò
    "GV", "HS", "PH", "PHHS", "GVCN", "GVBM", "CBQL", "BGH", "HT", "PHT",
    "GS", "PGS", "TS", "THS", "ThS", "CN", "KS", "BS", "TPCM", "TTCM",
    "TTND", "NGND", "NGƯT", "Đ/c", "đ/c", "BTC", "BGK", "BCH",

    # Sách / tài liệu / chương trình
    "SGK", "SBT", "SGV", "TL", "TLTK", "KHDH", "KHBD", "KH", "PPCT", "TKB",
    "PHT", "CT", "GDPT", "CTGDPT", "CD", "CĐ",

    # Cấp học / trường
    "TH", "THCS", "THPT", "MN", "ĐH", "CĐ", "GDTX", "GDNN", "TC",
    "TH&THCS", "THCS&THPT", "PTDTNT", "PTDTBT",

    # Cơ quan quản lý / hành chính
    "BGDĐT", "SGDĐT", "PGDĐT", "UBND", "HĐND", "TW", "CP", "BGD", "SGD", "PGD",
    "CHXHCN", "XHCN", "VN", "QH", "NĐ", "TT", "CV", "QĐ", "CT", "NQ",

    # Đánh giá / kiểm tra (TT 22/2021, TT 26/2020, TT 27/2020)
    "ĐGTX", "ĐGĐK", "ĐGGK", "ĐGCK", "ĐG", "KT", "GK", "CK",
    "HKI", "HKII", "GKI", "GKII", "CKI", "CKII", "TN", "TL", "TNKQ",
    "NB", "TH", "VD", "VDC",

    # Công nghệ / phương pháp dạy học tích cực
    "CNTT", "STEM", "STEAM", "ICT", "AI", "LMS", "IoT", "VR", "AR",
    "PPDH", "KTDH", "PP", "KT", "DH", "KWL", "KWLH", "SWOT", "SMART", "PBL",

    # Hoạt động / mục / hồ sơ
    "HĐ", "NXB", "TPHCM", "HN", "ĐN", "HP", "CT",
    "VD", "BT", "TB", "TP", "CH", "TL", "Nxb",

    # Năng lực / phẩm chất (CV 5512, CT GDPT 2018)
    "NL", "PC", "NLTT", "NLĐC", "NLC", "NLĐT", "YCCĐ",

    # Phân môn / lĩnh vực
    "GDCD", "GDĐP", "KHTN", "KHXH", "TNXH", "HĐTN", "HĐTNHN",
    "GDTC", "GDKT&PL", "GDKTPL", "LS&ĐL", "LSĐL", "GDQP", "GDQPAN", "QPAN",

    # Nền tảng học tập phổ biến trong trường học
    "VIOLET", "OLM", "SHUB", "AZOTA", "KAHOOT", "PADLET",
    "QUIZIZZ", "CANVA", "ZOOM", "TEAMS", "VNEDU", "SMAS", "TEMIS", "K12ONLINE",

    # Số La Mã (thường dùng trong tiêu đề, mục lục)
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",

    # Đơn vị đo lường chuẩn (SI & thông dụng)
    "km", "m", "dm", "cm", "mm", "nm", "pm", "kg", "hg", "dag", "g", "mg",
    "l", "ml", "dl", "cl", "ha", "tấn", "tạ", "yến",
    "m2", "m3", "dm2", "dm3", "cm2", "cm3", "mm2", "mm3", "km2",
    "m²", "m³", "dm²", "dm³", "cm²", "cm³", "mm²", "mm³", "km²",
    "s", "ms", "min", "h", "kw", "kwh", "mw", "w", "v", "kv", "mv", "a", "ma",
    "hz", "khz", "mhz", "ghz", "mb", "gb", "tb", "kb", "pb",
    "byte", "bytes", "bit", "bits", "bps", "kbps", "mbps", "gbps",
    "dpi", "ppi", "px", "pixel", "pt", "emu", "rem", "em",
    "mol", "kcal", "cal", "j", "kj", "pa", "kpa", "mpa", "atm", "bar", "rad",
    "°C", "°F", "°K", "K", "%", "‰",

    # Ký hiệu hóa học / vật lý / toán học phổ biến
    "pH", "ADN", "ARN", "DNA", "RNA", "ATP", "ADP", "enzim", "enzyme",
    "sin", "cos", "tan", "cot", "arcsin", "arccos", "arctan", "log", "ln", "lim", "max", "min",

    # Viết tắt thông dụng khác
    "v.v.", "v.v", "vv", "v/v", "etc", "đ/v", "tr", "sgk", "sbt", "sgv", "gv", "hs",
}

# ──────────────────────────────────────────────
# 2. Từ mượn tiếng Anh phổ biến trong giáo dục & đời sống
# ──────────────────────────────────────────────
COMMON_LOANWORDS: set[str] = {
    # Thiết bị & phương tiện
    "tivi", "tv", "rubik", "video", "videos", "clip", "clips", "slide", "slides",
    "laptop", "smartphone", "projector", "micro", "mic", "loa", "radio", "camera", "cam",
    "webcam", "scanner", "printer", "usb", "wifi", "wi-fi", "bluetooth", "mouse", "keyboard",
    "pc", "card", "sim", "chip", "ram", "rom", "cpu", "gpu", "ssd", "hdd",
    "robot", "robots", "robotics", "drone", "tablet", "ipad", "iphone", "android",
    "headphone", "headset", "earphone", "monitor", "cable", "hdmi", "vga", "type-c",
    "adapter", "router", "modem", "server", "cloud", "data", "database", "drive", "folder", "file", "files",

    # Nền tảng, phần mềm, AI & ứng dụng EdTech
    "internet", "website", "web", "online", "offline", "link", "links", "url", "app", "apps", "qr",
    "code", "coding", "email", "mail", "gmail", "inbox", "chat", "chatbot", "message", "messenger", "sms",
    "hotline", "facebook", "fb", "zalo", "youtube", "tiktok", "instagram", "google", "bing",
    "meet", "form", "forms", "doc", "docs", "sheet", "sheets", "classroom", "teams", "zoom",
    "powerpoint", "ppt", "pptx", "word", "docx", "excel", "xlsx", "pdf", "html", "css",
    "canva", "padlet", "kahoot", "quizizz", "azota", "shub", "olm", "violet",
    "wordwall", "blooket", "mentimeter", "nearpod", "classpoint", "classdojo", "plickers",
    "geogebra", "scratch", "python", "pascal", "c++", "java", "javascript", "arduino", "microbit",
    "chatgpt", "openai", "gemini", "copilot", "claude", "deepseek", "perplexity", "ai", "prompt",
    "phet", "liveworksheets", "duolingo", "coursera", "udemy", "edmodo", "moodle", "scorm",
    "elearning", "e-learning", "blearning", "b-learning", "blended", "flipped",
    "lms", "portal", "fanpage", "admin", "post", "comment", "share", "like",
    "subscribe", "follow", "stream", "livestream", "podcast", "vlog", "blog",

    # Thuật ngữ dạy học / STEM / Hoạt động
    "stem", "steam", "game", "games", "minigame", "mini-game", "team", "teamwork", "group",
    "feedback", "check", "test", "tests", "quiz", "quizzes", "mini", "audio", "mc",
    "banner", "poster", "standee", "logo", "slogan", "rubric", "rubrics", "checklist", "kpi",
    "timeline", "deadline", "task", "tasks", "project", "projects", "workshop", "seminar", "webinar",
    "step", "part", "unit", "lesson", "topic", "theme", "skill", "skills", "reading",
    "writing", "speaking", "listening", "grammar", "vocabulary", "pronunciation", "phonics",
    "practice", "review", "exam", "homework", "warmup", "warm-up",
    "icebreaker", "ice-breaking", "brainstorm", "brainstorming", "mindmap", "mind-map",
    "mind", "map", "wrapup", "wrap-up", "pass", "fail", "score", "rank", "ranking",
    "level", "note", "notes", "copy", "paste", "save", "print", "scan", "click", "double-click",
    "drag", "drop", "view", "preview", "mode", "status", "setting", "settings",
    "layout", "setup", "menu", "option", "options", "font", "format", "size", "color",
    "style", "bullet", "table", "cell", "row", "column", "margin", "spacing",
    "align", "bold", "italic", "underline", "highlight", "template", "templates",
    "storyboard", "infographic", "flashcard", "flashcards", "handout", "handouts",
    "worksheet", "worksheets", "portfolio", "case", "study", "roleplay", "role-play",
    "key", "keyword", "keywords", "tag", "tags", "tip", "tips", "trick", "tricks",
    "target", "goal", "goals", "input", "output", "outcome", "outcomes", "process",
    "concept", "context", "logic", "critical", "thinking", "creative", "innovation",
    "mentor", "coach", "leader", "member", "partner", "pair", "solo", "station",

    # Tên môn học / học thuật tiếng Anh
    "english", "math", "maths", "science", "physics", "chemistry", "biology",
    "history", "geography", "literature", "music", "art", "arts", "informatics",
    "civics", "technology", "physical", "education", "pe", "ict",
    "acid", "axit", "base", "bazơ", "bazo", "oxide", "oxit", "salt", "ester", "este",
    "amine", "amin", "amino", "protein", "lipid", "lipit", "glucid", "gluxit",
    "glucose", "glucozơ", "fructose", "fructozơ", "saccharose", "saccarozơ",
    "cellulose", "xenlulozơ", "starch", "polymer", "polime", "monomer", "monome",
    "ion", "cation", "anion", "electron", "proton", "neutron", "notron", "atom", "molecule",
    "alkane", "ankan", "alkene", "anken", "alkyne", "ankin", "alkadiene", "ankadien",
    "benzene", "benzen", "phenol", "alcohol", "ancol", "aldehyde", "andehit", "ketone", "xeton",
    "carboxylic", "cacboxylic", "halogen", "metal", "nonmetal", "oxide",
    "vector", "vectơ", "vecto", "matrix", "integral", "derivative", "graph", "modulo",
    "vitamin", "hormone", "hocmon", "vaccine", "vacxin", "vắc-xin", "virus", "vi-rút", "bacteria",
    "gene", "gen", "chromosome", "mitosis", "meiosis", "ecosystem", "cell",

    # Từ mượn đời sống quen thuộc
    "cafe", "cà phê", "coffee", "pizza", "snack", "sandwich", "burger", "fastfood",
    "supermarket", "market", "mall", "bar", "club", "gym", "yoga", "fitness",
    "spa", "golf", "tennis", "football", "badminton", "basketball", "volleyball",
    "billiards", "bida", "bowling", "marathon", "aerobic", "aerobics",
    "checkin", "check-in", "checkout", "check-out", "homestay",
    "resort", "hotel", "motel", "villa", "voucher", "coupon", "sale", "freeship",
    "order", "shipper", "ship", "fan", "fans", "idol", "trend", "trending",
    "viral", "hot", "cool", "chill", "fashion", "model", "show", "talkshow", "gameshow",
    "event", "teaser", "trailer", "remix", "cover", "hit", "beat", "tune", "tour",
    "combo", "set", "top", "pro", "plus", "max", "ultra", "lite", "smart", "eco",
    "vip", "pr", "marketing", "brand", "startup", "ceo", "hr",
    "ok", "okay", "yes", "no", "hello", "hi", "bye", "thank", "thanks",
}

# ──────────────────────────────────────────────
# 3. Loại lỗi
# ──────────────────────────────────────────────
class ErrorType(str, Enum):
    SPELLING = "Lỗi chính tả"
    PUNCTUATION = "Lỗi dấu câu / khoảng trắng"
    ORTHOGRAPHY = "Chưa đồng nhất quy tắc chính tả (i/y, dấu thanh)"
    CONTEXT_ONLINE = "Lỗi ngữ cảnh / ngữ pháp (Trực tuyến)"
    FONT = "Lỗi font chữ"
    FONT_SIZE = "Lỗi cỡ chữ"
    LINE_SPACING = "Lỗi giãn dòng"
    MARGIN = "Lỗi căn lề"
    PAPER_SIZE = "Lỗi khổ giấy"
    STRUCTURE = "Thiếu đề mục CV 5512"


# ──────────────────────────────────────────────
# 4. Cặp từ dễ nhầm lẫn & giải thích chi tiết (Dành cho Giáo viên)
# ──────────────────────────────────────────────
# Cấu trúc: { "cụm_từ_sai": ("cụm_từ_đúng", "giải_thích_ngắn") }
CONFUSABLE_DETAILS: dict[str, tuple[str, str]] = {
    # Nhóm giữ gìn / gìn giữ
    "giữ dìn": ("giữ gìn", "Phụ âm đầu 'gi' kết hợp với vần 'in' lược bớt một chữ 'i' thành 'gìn'."),
    "dữ dìn": ("giữ gìn", "Sai cả hai âm đầu: viết đúng là 'giữ gìn'."),
    "dữ gìn": ("giữ gìn", "Từ 'giữ' có phụ âm đầu là 'gi', không phải 'd'."),
    "gìn dĩ": ("gìn giữ", "Viết đúng là 'gìn giữ'."),
    "dìn dĩ": ("gìn giữ", "Viết đúng là 'gìn giữ'."),
    "gìn dũ": ("gìn giữ", "Viết đúng là 'gìn giữ'."),
    "dìn giữ": ("gìn giữ", "'Gìn' viết với phụ âm 'g' (do 'gi' + 'in' -> 'gìn')."),

    # Nhóm s / x
    "sử lý": ("xử lý", "'Xử' (xử lý, xét xử, cư xử) viết với 'x'; 'sử' dùng cho lịch sử, sử dụng."),
    "sử lí": ("xử lí", "'Xử' (giải quyết, điều khiển) viết với 'x', không phải 's'."),
    "sử sự": ("xử sự", "'Xử sự' (cách ứng xử) viết với 'x'."),
    "sử trí": ("xử trí", "'Xử trí' (giải quyết tình huống) viết với 'x'."),
    "xử dụng": ("sử dụng", "'Sử dụng' (dùng vào việc gì) viết với 's'."),
    "sắp sếp": ("sắp xếp", "Viết đúng là 'sắp xếp' (sắp đặt và xếp thứ tự)."),
    "xắp xếp": ("sắp xếp", "Chữ đầu là 'sắp' (với 's'), chữ sau là 'xếp' (với 'x')."),
    "xắp sếp": ("sắp xếp", "Đúng chính tả là 'sắp xếp'."),
    "sác nhận": ("xác nhận", "'Xác' (chắc chắn, đúng thực: xác nhận, xác định, chính xác) viết với 'x'."),
    "sác định": ("xác định", "'Xác định' viết với 'x'."),
    "sác thực": ("xác thực", "'Xác thực' viết với 'x'."),
    "sác suất": ("xác suất", "'Xác suất' (toán học) viết là 'xác' (x) và 'suất' (s)."),
    "xác xuất": ("xác suất", "'Suất' (tỉ lệ, hiệu suất, xác suất) viết với 's'; 'xuất' là sản xuất, xuất hiện."),
    "năng xuất": ("năng suất", "'Suất' (hiệu quả tính theo đơn vị: năng suất, hiệu suất) viết với 's'."),
    "hiệu xuất": ("hiệu suất", "'Hiệu suất' viết với 's'."),
    "tần xuất": ("tần suất", "'Tần suất' viết với 's'."),
    "lãi xuất": ("lãi suất", "'Lãi suất' viết với 's'."),
    "sản suất": ("sản xuất", "'Sản xuất' (làm ra của cải) viết với 'x'."),
    "suất hiện": ("xuất hiện", "'Xuất' (ra ngoài: xuất hiện, xuất sắc, xuất phát) viết với 'x'."),
    "suất phát": ("xuất phát", "'Xuất phát' viết với 'x'."),
    "suất xứ": ("xuất xứ", "'Xuất xứ' (nguồn gốc ra đời) cả hai từ đều viết với 'x'."),
    "xuất sứ": ("xuất xứ", "'Xứ' (nơi chốn, quê xứ, xuất xứ) viết với 'x'; 'sứ' là sứ giả, đồ sứ."),
    "suất sắc": ("xuất sắc", "'Xuất' (vượt lên) viết với 'x', 'sắc' viết với 's'."),
    "xuất xắc": ("xuất sắc", "'Sắc' trong 'xuất sắc' viết với 's'."),
    "sơ xuất": ("sơ suất", "'Sơ suất' (thiếu cẩn thận, đại khái) cả hai âm tiết đều viết với 's'."),
    "xơ suất": ("sơ suất", "'Sơ suất' viết với 's'."),
    "xơ xuất": ("sơ suất", "'Sơ suất' viết với 's'."),
    "bổ xung": ("bổ sung", "'Sung' (thêm vào cho đầy: bổ sung, sung túc) viết với 's'."),
    "cọ sát": ("cọ xát", "'Cọ xát' (chà xát, thử thách thực tế) viết với 'x'; 'sát' là gần sát, quan sát."),
    "quan xát": ("quan sát", "'Quan sát' (nhìn xem kỹ) viết với 's'."),
    "khảo xát": ("khảo sát", "'Khảo sát' viết với 's'."),
    "suôn xẻ": ("suôn sẻ", "'Suôn sẻ' (trôi chảy, thuận lợi) cả hai từ đều viết với 's'."),
    "xuôn sẻ": ("suôn sẻ", "'Suôn sẻ' viết với 's'."),
    "sáng lạng": ("xán lạn", "Từ Hán-Việt chuẩn là 'xán lạn' (rực rỡ, tươi sáng), không phải 'sáng lạng'."),
    "xán lạng": ("xán lạn", "Viết đúng là 'xán lạn' (không có 'g' ở cuối)."),
    "sáng lạn": ("xán lạn", "Viết đúng là 'xán lạn' (âm đầu 'x')."),
    "xúc tích": ("súc tích", "'Súc' (chứa đựng, cô đọng: hàm súc, súc tích) viết với 's'."),
    "xơ đồ": ("sơ đồ", "'Sơ đồ' (bản vẽ quy ước) viết với 's'."),
    "xơ lược": ("sơ lược", "'Sơ lược' viết với 's'."),
    "chia xẻ": ("chia sẻ", "'Chia sẻ' (cùng san sẻ) viết với 's'; 'xẻ' là cưa xẻ gỗ."),
    "san xẻ": ("san sẻ", "'San sẻ' viết với 's'."),
    "xoay sở": ("xoay xở", "'Xoay xở' (tìm mọi cách giải quyết) cả hai từ đều viết với 'x'."),
    "soay xở": ("xoay xở", "'Xoay xở' viết với 'x'."),
    "xáng tạo": ("sáng tạo", "'Sáng tạo' viết với 's'."),
    "sâu xắc": ("sâu sắc", "'Sâu sắc' viết với 's'."),
    "xâu sắc": ("sâu sắc", "'Sâu sắc' viết với 's'."),
    "xuy nghĩ": ("suy nghĩ", "'Suy nghĩ' viết với 's'."),
    "suy xét": ("suy xét", ""),
    "xuy luận": ("suy luận", "'Suy luận' viết với 's'."),
    "soạn giả": ("soạn giả", ""),
    "xoạn thảo": ("soạn thảo", "'Soạn thảo' viết với 's'."),
    "kiểm xoát": ("kiểm soát", "'Kiểm soát' viết với 's'."),
    "soát xét": ("soát xét", ""),
    "xem sét": ("xem xét", "'Xem xét' cả hai từ đều viết với 'x'."),
    "nhận sét": ("nhận xét", "'Nhận xét' viết với 'x'."),

    # Nhóm ch / tr
    "chương chình": ("chương trình", "'Trình' (quá trình, chương trình, trình bày) viết với 'tr'."),
    "chúng chình": ("chương trình", "Viết đúng là 'chương trình'."),
    "tiến chình": ("tiến trình", "'Tiến trình' viết với 'tr'."),
    "quy chình": ("quy trình", "'Quy trình' viết với 'tr'."),
    "quá chình": ("quá trình", "'Quá trình' viết với 'tr'."),
    "chình bày": ("trình bày", "'Trình bày' viết với 'tr'."),
    "chình độ": ("trình độ", "'Trình độ' viết với 'tr'."),
    "thuyết chình": ("thuyết trình", "'Thuyết trình' viết với 'tr'."),
    "chực tiếp": ("trực tiếp", "'Trực tiếp' viết với 'tr'."),
    "chực quan": ("trực quan", "'Trực quan' viết với 'tr'."),
    "chích xác": ("chính xác", "Viết đúng là 'chính xác'."),
    "chính sát": ("chính xác", "'Xác' trong 'chính xác' viết với 'x' và vần 'ac'."),
    "trính xác": ("chính xác", "'Chính' trong 'chính xác' viết với 'ch'."),
    "đoạn chích": ("đoạn trích", "'Trích' (rút ra từ tác phẩm: đoạn trích, trích dẫn) viết với 'tr'."),
    "chích dẫn": ("trích dẫn", "'Trích dẫn' viết với 'tr'."),
    "chăn chở": ("trăn trở", "'Trăn trở' (suy nghĩ nhiều, băn khoăn) cả hai từ đều viết với 'tr'."),
    "chi thức": ("tri thức", "'Tri thức' (hiểu biết, kiến thức) viết với 'tr'."),
    "trí thức": ("trí thức", ""),
    "tri tiết": ("chi tiết", "'Chi tiết' (từng phần nhỏ) viết với 'ch'."),
    "chọng tâm": ("trọng tâm", "'Trọng tâm' (điểm chính yếu) viết với 'tr'."),
    "quan chọng": ("quan trọng", "'Quan trọng' viết với 'tr'."),
    "tôn chọng": ("tôn trọng", "'Tôn trọng' viết với 'tr'."),
    "cha cứu": ("tra cứu", "'Tra cứu' (tìm kiếm thông tin) viết với 'tr'."),
    "kiểm cha": ("kiểm tra", "'Kiểm tra' viết với 'tr'."),
    "tiêu trí": ("tiêu chí", "'Tiêu chí' (chuẩn mực để đánh giá) viết với 'ch'."),
    "vị trí": ("vị trí", ""),
    "đối triếu": ("đối chiếu", "'Đối chiếu' (so sánh hai bên) viết với 'ch'."),
    "chong đợi": ("trông đợi", "'Trông đợi' viết với 'tr' và nguyên âm 'ô'."),
    "trông chờ": ("trông chờ", ""),
    "tập chung": ("tập trung", "'Tập trung' (dồn vào một chỗ) viết với 'tr'; 'chung' là của chung."),
    "chung thành": ("trung thành", "'Trung thành' viết với 'tr'."),
    "chung thực": ("trung thực", "'Trung thực' (ngay thẳng, thật thà) viết với 'tr'."),
    "chung bình": ("trung bình", "'Trung bình' viết với 'tr'."),
    "trung tâm": ("trung tâm", ""),
    "chung tâm": ("trung tâm", "'Trung tâm' viết với 'tr'."),
    "vô hình chung": ("vô hình trung", "Thành ngữ Hán-Việt chuẩn là 'vô hình trung' (tự nhiên, không cố ý mà nên)."),
    "tựu chung": ("tựu trung", "Từ Hán-Việt chuẩn là 'tựu trung' (tóm lại, xét về đại thể)."),
    "chỉnh chu": ("chỉn chu", "Từ chuẩn trong từ điển tiếng Việt là 'chỉn chu' (chu đáo, cẩn thận), không có 'g'."),
    "trỉnh chu": ("chỉn chu", "Viết đúng là 'chỉn chu'."),
    "chẩn đoán": ("chẩn đoán", ""),
    "chuẩn đoán": ("chẩn đoán", "'Chẩn' (xem xét bệnh/tình trạng: chẩn đoán, chẩn mạch) không có 'u'."),
    "bắt trước": ("bắt chước", "'Bắt chước' (làm theo mẫu) viết với 'ch'."),
    "chau dồi": ("trau dồi", "'Trau dồi' (rèn luyện cho tốt đẹp hơn) viết với 'tr'."),
    "chau chuốt": ("trau chuốt", "'Trau chuốt' từ đầu viết với 'tr', từ sau viết với 'ch'."),
    "trau truốt": ("trau chuốt", "'Chuốt' trong 'trau chuốt' viết với 'ch'."),
    "chuyển biến": ("chuyển biến", ""),
    "triển biến": ("chuyển biến", "Viết đúng là 'chuyển biến' (hoặc 'diễn biến')."),
    "chiển khai": ("triển khai", "'Triển khai' (mở rộng, thực hiện) viết với 'tr'."),
    "phát chiển": ("phát triển", "'Phát triển' viết với 'tr'."),
    "chuyền thống": ("truyền thống", "'Truyền thống' viết với 'tr'."),
    "chuyền đạt": ("truyền đạt", "'Truyền đạt' (trao lại kiến thức) viết với 'tr'."),
    "chách nhiệm": ("trách nhiệm", "'Trách nhiệm' viết với 'tr'."),
    "phụ chách": ("phụ trách", "'Phụ trách' viết với 'tr'."),
    "phẩm trất": ("phẩm chất", "'Phẩm chất' viết với 'ch'."),
    "bản trất": ("bản chất", "'Bản chất' viết với 'ch'."),
    "vật trất": ("vật chất", "'Vật chất' viết với 'ch'."),
    "tổ chức": ("tổ chức", ""),
    "tổ trức": ("tổ chức", "'Tổ chức' viết với 'ch'."),
    "trức năng": ("chức năng", "'Chức năng' viết với 'ch'."),
    "chức lăng": ("chức năng", "'Chức năng' viết với 'n'."),
    "trủ động": ("chủ động", "'Chủ động' viết với 'ch'."),
    "trủ đề": ("chủ đề", "'Chủ đề' viết với 'ch'."),
    "chủ chương": ("chủ trương", "'Chủ trương' (đường lối, ý định) từ sau viết với 'tr'."),
    "trủ trương": ("chủ trương", "Viết đúng là 'chủ trương'."),
    "môi chường": ("môi trường", "'Môi trường' viết với 'tr'."),
    "hỗ chợ": ("hỗ trợ", "'Hỗ trợ' (giúp đỡ lẫn nhau) viết với 'tr'."),

    # Nhóm d / gi / r
    "dáo viên": ("giáo viên", "'Giáo' (dạy học: giáo viên, giáo dục, giáo án) viết với 'gi'."),
    "dáo dục": ("giáo dục", "'Giáo dục' viết với 'gi'."),
    "dáo án": ("giáo án", "'Giáo án' viết với 'gi'."),
    "thầy dáo": ("thầy giáo", "'Thầy giáo' viết với 'gi'."),
    "cô dáo": ("cô giáo", "'Cô giáo' viết với 'gi'."),
    "dải thích": ("giải thích", "'Giải' (giải thích, giải quyết, bài giải) viết với 'gi'."),
    "dải quyết": ("giải quyết", "'Giải quyết' viết với 'gi'."),
    "dải pháp": ("giải pháp", "'Giải pháp' viết với 'gi'."),
    "dải bài": ("giải bài", "'Giải bài' viết với 'gi'."),
    "giặn dò": ("dặn dò", "'Dặn dò' cả hai từ đều viết với 'd'."),
    "dặn giò": ("dặn dò", "'Dặn dò' cả hai từ đều viết với 'd'."),
    "dẫn giắt": ("dẫn dắt", "'Dẫn dắt' cả hai từ đều viết với 'd'."),
    "giẫn dắt": ("dẫn dắt", "'Dẫn dắt' cả hai từ đều viết với 'd'."),
    "giẫn giắt": ("dẫn dắt", "'Dẫn dắt' cả hai từ đều viết với 'd'."),
    "giành riêng": ("dành riêng", "'Dành' (để lại cho ai/việc gì: dành riêng, để dành, dành dụm) viết với 'd'."),
    "để giành": ("để dành", "'Để dành' (cất giữ lại) viết với 'd'; 'giành' là tranh giành, giành độc lập."),
    "giành dụm": ("dành dụm", "'Dành dụm' (tích góp lại) viết với 'd'."),
    "giành thời gian": ("dành thời gian", "'Dành thời gian' viết với 'd'; 'giành' chỉ dùng khi có sự nỗ lực/đấu tranh."),
    "tranh dành": ("tranh giành", "'Tranh giành' (cố lấy về mình) viết với 'gi'."),
    "dành giật": ("giành giật", "'Giành giật' viết với 'gi'."),
    "dành thắng lợi": ("giành thắng lợi", "'Giành thắng lợi' (nỗ lực đạt được) viết với 'gi'."),
    "dành độc lập": ("giành độc lập", "'Giành độc lập' viết với 'gi'."),
    "gián diệp": ("gián điệp", "'Gián điệp' viết với 'đ' ở âm tiết thứ hai."),
    "rèn rũa": ("rèn giũa", "'Rèn giũa' từ đầu viết 'r', từ sau viết 'gi'."),
    "dèn luyện": ("rèn luyện", "'Rèn luyện' viết với 'r'."),
    "gièn luyện": ("rèn luyện", "'Rèn luyện' viết với 'r'."),
    "rõ dàng": ("rõ ràng", "'Rõ ràng' cả hai từ đều viết với 'r'."),
    "dõ ràng": ("rõ ràng", "'Rõ ràng' viết với 'r'."),
    "dễ dàng": ("dễ dàng", ""),
    "dễ giàng": ("dễ dàng", "'Dễ dàng' cả hai từ đều viết với 'd'."),
    "giễ dàng": ("dễ dàng", "'Dễ dàng' viết với 'd'."),
    "tham gia": ("tham gia", ""),
    "tham da": ("tham gia", "'Tham gia' viết với 'gi'."),
    "đánh dá": ("đánh giá", "'Đánh giá' viết với 'gi'."),
    "giá chị": ("giá trị", "'Giá trị' viết với 'gi' và 'tr'."),
    "dá trị": ("giá trị", "'Giá trị' viết với 'gi'."),
    "vận zụng": ("vận dụng", "'Vận dụng' viết với 'd'."),
    "áp zụng": ("áp dụng", "'Áp dụng' viết với 'd'."),
    "sử zụng": ("sử dụng", "'Sử dụng' viết với 's' và 'd'."),

    # Nhóm l / n
    "lăng lực": ("năng lực", "'Năng lực' (khả năng thực hiện) viết với 'n'."),
    "năng nực": ("năng lực", "'Lực' trong 'năng lực' viết với 'l'."),
    "lăng nực": ("năng lực", "Viết đúng là 'năng lực'."),
    "lăng động": ("năng động", "'Năng động' viết với 'n'."),
    "lo lực": ("nỗ lực", "'Nỗ lực' (cố gắng hết sức) viết với 'n' và dấu ngã."),
    "nổ lực": ("nỗ lực", "'Nỗ lực' mang thanh ngã (~), không phải thanh hỏi."),
    "lỗ lực": ("nỗ lực", "'Nỗ lực' viết với 'n'."),
    "nuyện tập": ("luyện tập", "'Luyện tập' viết với 'l'."),
    "luyệnập": ("luyện tập", "Thiếu khoảng trắng giữa 'luyện' và 'tập'."),
    "học niệu": ("học liệu", "'Học liệu' (tài liệu học tập) viết với 'l'."),
    "tài niệu": ("tài liệu", "'Tài liệu' viết với 'l'."),
    "nội dung": ("nội dung", ""),
    "lội dung": ("nội dung", "'Nội dung' viết với 'n'."),
    "thảo nuận": ("thảo luận", "'Thảo luận' viết với 'l'."),
    "kết nuận": ("kết luận", "'Kết luận' viết với 'l'."),
    "lí nuận": ("lí luận", "'Lí luận' cả hai từ đều viết với 'l'."),
    "lý nuận": ("lý luận", "'Lý luận' cả hai từ đều viết với 'l'."),
    "khái liệm": ("khái niệm", "'Khái niệm' viết với 'n'."),
    "quan liệm": ("quan niệm", "'Quan niệm' viết với 'n'."),
    "kỉ liệm": ("kỉ niệm", "'Kỉ niệm' viết với 'n'."),
    "kỷ liệm": ("kỷ niệm", "'Kỷ niệm' viết với 'n'."),
    "nàm việc": ("làm việc", "'Làm việc' viết với 'l'."),
    "nàm bài": ("làm bài", "'Làm bài' viết với 'l'."),
    "nắng nghe": ("lắng nghe", "'Lắng nghe' viết với 'l'."),
    "liên kết": ("liên kết", ""),
    "niên kết": ("liên kết", "'Liên kết' viết với 'l'."),

    # Nhóm dấu hỏi / dấu ngã & thanh điệu
    "kỉ năng": ("kĩ năng", "'Kĩ' (khéo léo, chuyên môn: kĩ năng, kĩ thuật) mang thanh ngã (~); 'kỉ' (hỏi) dùng cho kỉ niệm, kỉ luật, thế kỉ."),
    "kỷ năng": ("kỹ năng", "'Kỹ' trong 'kỹ năng', 'kỹ thuật' mang thanh ngã (~)."),
    "kỉ thuật": ("kĩ thuật", "'Kĩ thuật' mang thanh ngã (~)."),
    "kỷ thuật": ("kỹ thuật", "'Kỹ thuật' mang thanh ngã (~)."),
    "kĩ niệm": ("kỉ niệm", "'Kỉ niệm' mang thanh hỏi (?); 'kĩ' (ngã) dùng cho kĩ năng, kĩ thuật."),
    "kỹ niệm": ("kỷ niệm", "'Kỷ niệm' mang thanh hỏi (?)."),
    "kĩ luật": ("kỉ luật", "'Kỉ luật' mang thanh hỏi (?)."),
    "kỹ luật": ("kỷ luật", "'Kỷ luật' mang thanh hỏi (?)."),
    "thế kĩ": ("thế kỉ", "'Thế kỉ' mang thanh hỏi (?)."),
    "thế kỹ": ("thế kỷ", "'Thế kỷ' mang thanh hỏi (?)."),
    "sỉ số": ("sĩ số", "'Sĩ số' (số lượng học sinh/quân nhân) mang thanh ngã (~)."),
    "nghỉ lực": ("nghị lực", "'Nghị lực' mang thanh nặng (.)."),
    "ngẫm nghĩ": ("ngẫm nghĩ", ""),
    "suy ngĩ": ("suy nghĩ", "'Nghĩ' đứng trước 'i' phải viết là 'ngh'."),
    "ngĩ ngợi": ("nghĩ ngợi", "Trước nguyên âm 'i', 'e', 'ê' phải dùng 'ngh'."),
    "nghe ngóng": ("nghe ngóng", ""),
    "lắng nge": ("lắng nghe", "Trước nguyên âm 'e' phải viết là 'ngh' ('nghe')."),
    "ghi nhớ": ("ghi nhớ", ""),
    "gi nhớ": ("ghi nhớ", "Trước nguyên âm 'i' phải viết là 'gh' ('ghi')."),
    "hỗn hợp": ("hỗn hợp", ""),
    "hổn hợp": ("hỗn hợp", "'Hỗn' (pha trộn: hỗn hợp, hỗn độn) mang thanh ngã (~)."),
    "mẫu giáo": ("mẫu giáo", ""),
    "mẩu giáo": ("mẫu giáo", "'Mẫu' (mẹ, khuôn mẫu: mẫu giáo, biểu mẫu) mang thanh ngã (~); 'mẩu' là mẩu chuyện, mẩu bánh."),
    "biểu mẩu": ("biểu mẫu", "'Biểu mẫu' mang thanh ngã (~)."),
    "nguyên mẩu": ("nguyên mẫu", "'Nguyên mẫu' mang thanh ngã (~)."),
    "chẩn bị": ("chuẩn bị", "Viết đúng là 'chuẩn bị'."),
    "chuẫn bị": ("chuẩn bị", "'Chuẩn' (chuẩn bị, tiêu chuẩn) mang thanh hỏi (?)."),
    "tiêu chuẫn": ("tiêu chuẩn", "'Tiêu chuẩn' mang thanh hỏi (?)."),
    "kiểm điễm": ("kiểm điểm", "'Điểm' mang thanh hỏi (?)."),
    "điễm số": ("điểm số", "'Điểm' mang thanh hỏi (?)."),
    "bão vệ": ("bảo vệ", "'Bảo vệ' mang thanh hỏi (?); 'bão' là cơn bão."),
    "đãm bảo": ("đảm bảo", "'Đảm bảo' cả hai từ đều mang thanh hỏi (?)."),
    "đảm bão": ("đảm bảo", "'Đảm bảo' mang thanh hỏi (?)."),
    "thão luận": ("thảo luận", "'Thảo luận' mang thanh hỏi (?)."),
    "biễu diễn": ("biểu diễn", "'Biểu' mang thanh hỏi (?), 'diễn' mang thanh ngã (~)."),
    "biểu diển": ("biểu diễn", "'Diễn' (biểu diễn, diễn đạt, diễn biến) mang thanh ngã (~)."),
    "diển đạt": ("diễn đạt", "'Diễn đạt' mang thanh ngã (~)."),
    "diển biến": ("diễn biến", "'Diễn biến' mang thanh ngã (~)."),
    "hướng dẩn": ("hướng dẫn", "'Dẫn' (hướng dẫn, dẫn dắt, hấp dẫn) mang thanh ngã (~)."),
    "hấp dẩn": ("hấp dẫn", "'Hấp dẫn' mang thanh ngã (~)."),
    "dẩn chứng": ("dẫn chứng", "'Dẫn chứng' mang thanh ngã (~)."),
    "mổi nhóm": ("mỗi nhóm", "'Mỗi' (từng đơn vị một: mỗi nhóm, mỗi em) mang thanh ngã (~); 'mỏi' là mệt mỏi."),
    "mổi học sinh": ("mỗi học sinh", "'Mỗi' mang thanh ngã (~)."),
    "mổi em": ("mỗi em", "'Mỗi' mang thanh ngã (~)."),
    "sẳn sàng": ("sẵn sàng", "'Sẵn' (có sẵn, sẵn sàng) mang thanh ngã (~)."),
    "có sẳn": ("có sẵn", "'Có sẵn' mang thanh ngã (~)."),
    "vẩn còn": ("vẫn còn", "'Vẫn' mang thanh ngã (~)."),
    "củng cố": ("củng cố", ""),
    "cũng cố": ("củng cố", "'Củng cố' (làm cho vững chắc thêm) mang thanh hỏi (?); 'cũng' là phó từ."),
    "bổn phận": ("bổn phận", ""),
    "nghiên cứu": ("nghiên cứu", ""),
    "ngiên cứu": ("nghiên cứu", "Trước 'iê' phải viết là 'ngh' ('nghiên')."),

    # Từ vựng dùng sai âm / nghĩa trong văn bản nhà trường
    "học xinh": ("học sinh", "'Học sinh' viết với 's'."),
    "thăm quan": ("tham quan", "Từ Hán-Việt chuẩn là 'tham quan' (tham: dự vào, quan: xem xét), không phải 'thăm quan'."),
    "chín sửa": ("chỉnh sửa", "Viết đúng là 'chỉnh sửa'."),
    "chín mùi": ("chín muồi", "Từ chuẩn là 'chín muồi' (đạt đến độ phát triển đầy đủ nhất), không phải 'chín mùi'."),
    "đọc giả": ("độc giả", "Từ Hán-Việt chuẩn là 'độc giả' (độc: đọc, giả: người), không viết là 'đọc giả'."),
    "khuôn khổ": ("khuôn khổ", ""),
    "khung khổ": ("khuôn khổ", "Viết đúng là 'khuôn khổ' (giới hạn, phạm vi quy định)."),
    "chắp vá": ("chắp vá", ""),
    "chấp vá": ("chắp vá", "Viết đúng là 'chắp vá' (ghép nối tạm bợ)."),
    "cổ võ": ("cổ vũ", "Từ thông dụng chuẩn hiện nay là 'cổ vũ' (động viên, khích lệ)."),
    "bàng quan": ("bàng quan", ""),
    "bàn quan": ("bàng quan", "Viết đúng là 'bàng quan' (đứng ngoài cuộc, thờ ơ)."),
    "xập xệ": ("xập xệ", ""),
    "sập sệ": ("xập xệ", "Viết đúng là 'xập xệ'."),
    "bác sỹ": ("bác sĩ", "Sau phụ âm 's' không dùng 'y' dài, viết chuẩn là 'bác sĩ'."),
    "ca sỹ": ("ca sĩ", "Viết chuẩn là 'ca sĩ'."),
    "họa sỹ": ("họa sĩ", "Viết chuẩn là 'họa sĩ'."),
    "hoạ sỹ": ("hoạ sĩ", "Viết chuẩn là 'hoạ sĩ'."),
    "nghệ sỹ": ("nghệ sĩ", "Viết chuẩn là 'nghệ sĩ'."),
    "tiến sỹ": ("tiến sĩ", "Viết chuẩn là 'tiến sĩ'."),
    "thạc sỹ": ("thạc sĩ", "Viết chuẩn là 'thạc sĩ'."),
    "chiến sỹ": ("chiến sĩ", "Viết chuẩn là 'chiến sĩ'."),
    "nhà sỹ": ("nha sĩ", "Viết chuẩn là 'nha sĩ'."),
}

# Tương thích ngược: ánh xạ wrong_phrase -> correct_phrase (chỉ giữ cặp thực sự khác nhau)
COMMON_TYPOS: dict[str, str] = {
    k: v[0] for k, v in CONFUSABLE_DETAILS.items() if k != v[0] and v[0]
}


# ──────────────────────────────────────────────
# 5. Cặp từ Ngữ cảnh (Cả hai từ đều có trong từ điển nhưng dùng sai ngữ cảnh)
# ──────────────────────────────────────────────
CONTEXTUAL_CONFUSION_RULES = [
    {
        "pattern": r"\b(?:khắc\s+phục|hạn\s+chế|sửa\s+chữa|những)\s+(yếu\s+điểm)\b",
        "wrong_group": 1,
        "suggestion": "điểm yếu",
        "description": "Sai ngữ nghĩa Hán-Việt: 'yếu điểm' là điểm quan trọng nhất (trọng điểm). Khi nói về thiếu sót cần khắc phục phải dùng 'điểm yếu' hoặc 'nhược điểm'.",
    },
    {
        "pattern": r"\b(bàng\s+hoàng)\s+(?:trước\s+nỗi\s+đau|đứng\s+ngoài|thờ\s+ơ|vô\s+cảm|không\s+quan\s+tâm)\b",
        "wrong_group": 1,
        "suggestion": "bàng quan",
        "description": "Nhầm từ gần âm: 'bàng hoàng' là sững sờ, choáng váng; 'bàng quan' mới có nghĩa là đứng ngoài cuộc, thờ ơ.",
    },
    {
        "pattern": r"\b(?:thái\s+độ)\s+(bàng\s+hoàng)\b",
        "wrong_group": 1,
        "suggestion": "bàng quan",
        "description": "'Thái độ bàng quan' (thờ ơ, đứng ngoài cuộc) mới đúng ngữ cảnh; 'bàng hoàng' là trạng thái cảm xúc sững sờ.",
    },
    {
        "pattern": r"\b(giả\s+thuyết)\s+(?:và\s+kết\s+luận|của\s+bài\s+toán|cho\s+biết|tam\s+giác|hình\s+học)\b",
        "wrong_group": 1,
        "suggestion": "giả thiết",
        "description": "Trong Toán học (điều kiện cho trước của bài toán/định lý, đi cặp với Kết luận) phải dùng 'giả thiết', không dùng 'giả thuyết'.",
    },
    {
        "pattern": r"\b(?:chuyển\s+đạt)\s+(?:kiến\s+thức|nội\s+dung|thông\s+điệp|ý\s+tưởng)\b",
        "wrong_group": 0,
        "suggestion": "truyền đạt",
        "description": "Kết hợp từ chuẩn là 'truyền đạt kiến thức / nội dung / thông điệp'.",
    },
]


# ──────────────────────────────────────────────
# 6. Quy tắc Chuẩn hóa Chính tả (i/y và vị trí dấu thanh oà/òa)
# ──────────────────────────────────────────────

# Các từ thông dụng có biến thể i / y (dùng để kiểm tra tính nhất quán hoặc chuẩn hóa theo SGK Bộ GD&ĐT)
IY_STANDARD_MAP: dict[str, str] = {
    # Từ chuẩn kiểu "i" (SGK hiện hành) ↔ từ kiểu "y"
    "kỹ năng": "kĩ năng",
    "kỹ thuật": "kĩ thuật",
    "kỹ thuật số": "kĩ thuật số",
    "kỹ sư": "kĩ sư",
    "kỹ lưỡng": "kĩ lưỡng",
    "kỷ niệm": "kỉ niệm",
    "kỷ luật": "kỉ luật",
    "kỷ lục": "kỉ lục",
    "kỷ nguyên": "kỉ nguyên",
    "thế kỷ": "thế kỉ",
    "thập kỷ": "thập kỉ",
    "ích kỷ": "ích kỉ",
    "tự kỷ": "tự kỉ",
    "lý thuyết": "lí thuyết",
    "lý luận": "lí luận",
    "lý tưởng": "lí tưởng",
    "lý do": "lí do",
    "lý thú": "lí thú",
    "lý giải": "lí giải",
    "vật lý": "vật lí",
    "địa lý": "địa lí",
    "sinh lý": "sinh lí",
    "tâm lý": "tâm lí",
    "quản lý": "quản lí",
    "xử lý": "xử lí",
    "hợp lý": "hợp lí",
    "định lý": "định lí",
    "nguyên lý": "nguyên lí",
    "chân lý": "chân lí",
    "đạo lý": "đạo lí",
    "triết lý": "triết lí",
    "mỹ thuật": "mĩ thuật",
    "thẩm mỹ": "thẩm mĩ",
    "hoàn mỹ": "hoàn mĩ",
    "mỹ quan": "mĩ quan",
}

# Ánh xạ dấu thanh trên oa, oe, uy: Kiểu cũ (òa, óa, ùy...) ↔ Kiểu mới (oà, oá, uỳ...)
TONE_OLD_TO_NEW: dict[str, str] = {
    "òa": "oà", "óa": "oá", "ỏa": "oả", "õa": "oã", "ọa": "oạ",
    "òe": "oè", "óe": "oé", "ỏe": "oẻ", "õe": "oẽ", "ọe": "oẹ",
    "ùy": "uỳ", "úy": "uý", "ủy": "uỷ", "ũy": "uỹ", "ụy": "uỵ",
    "Òa": "Oà", "Óa": "Oá", "Ỏa": "Oả", "Õa": "Oã", "Ọa": "Oạ",
    "Òe": "Oè", "Óe": "Oé", "Ỏe": "Oẻ", "Õe": "Oẽ", "Ọe": "Oẹ",
    "Ùy": "Uỳ", "Úy": "Uý", "Ủy": "Uỷ", "Ũy": "Uỹ", "Ụy": "Uỵ",
    "ÒA": "OÀ", "ÓA": "OÁ", "ỎA": "OẢ", "ÕA": "OÃ", "ỌA": "OẠ",
    "ÒE": "OÈ", "ÓE": "OÉ", "ỎE": "OẺ", "ÕE": "OẼ", "ỌE": "OẸ",
    "ÙY": "UỲ", "ÚY": "UÝ", "ỦY": "UỶ", "ŨY": "UỸ", "ỤY": "UỴ",
}

TONE_NEW_TO_OLD: dict[str, str] = {v: k for k, v in TONE_OLD_TO_NEW.items()}


# ──────────────────────────────────────────────
# 7. Cấu trúc Giáo án theo Công văn 5512
# ──────────────────────────────────────────────

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

# Các bước thành phần bên trong mỗi hoạt động theo CV 5512 (khuyến nghị / nâng cao)
CV5512_ACTIVITY_STEPS = [
    {"id": "step_a", "pattern": r"(?:a[\.\)]|[-•+])\s*Mục\s+tiêu", "label": "a) Mục tiêu"},
    {"id": "step_b", "pattern": r"(?:b[\.\)]|[-•+])\s*Nội\s+dung", "label": "b) Nội dung"},
    {"id": "step_c", "pattern": r"(?:c[\.\)]|[-•+])\s*Sản\s+phẩm", "label": "c) Sản phẩm"},
    {"id": "step_d", "pattern": r"(?:d[\.\)]|[-•+])\s*Tổ\s+chức\s+thực\s+hiện", "label": "d) Tổ chức thực hiện"},
]


# ──────────────────────────────────────────────
# 8. Thể thức văn bản (Nghị định 30/2020)
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
# 9. Các pattern quy tắc dấu câu / khoảng trắng
# ──────────────────────────────────────────────
PUNCTUATION_RULES = [
    (r' +([,\.;:!\?])', "Thừa khoảng trắng trước dấu câu"),
    (r'([,\.;:!\?])([A-Za-zÀ-ỹ])', "Thiếu khoảng trắng sau dấu câu"),
    (r'  +', "Hai dấu cách liên tiếp trở lên"),
    (r'(\() +', "Thừa khoảng trắng sau dấu mở ngoặc"),
    (r' +(\))', "Thừa khoảng trắng trước dấu đóng ngoặc"),
    (r'(\[) +', "Thừa khoảng trắng sau dấu mở ngoặc vuông"),
    (r' +(\])', "Thừa khoảng trắng trước dấu đóng ngoặc vuông"),
    (r'(\{) +', "Thừa khoảng trắng sau dấu mở ngoặc nhọn"),
    (r' +(\})', "Thừa khoảng trắng trước dấu đóng ngoặc nhọn"),
    (r'([“"«]) +', "Thừa khoảng trắng sau dấu mở nháy"),
    (r' +([”"»])', "Thừa khoảng trắng trước dấu đóng nháy"),
]
