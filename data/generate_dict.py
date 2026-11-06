#!/usr/bin/env python3
"""
Generate a comprehensive Vietnamese syllable dictionary.
Produces all valid Vietnamese syllable combinations from initials, rhymes, and tones,
accounting for orthographic merging (e.g. gi + in -> gìn, gi + iêng -> giếng, qu + y -> quy)
and includes common English loanwords used in schools and daily life.
"""

import os
import sys

# Thêm đường dẫn project
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.constants import COMMON_LOANWORDS, EDUCATION_WHITELIST

# All Vietnamese initial consonants (including zero-initial "")
INITIALS = [
    "", "b", "c", "ch", "d", "đ", "g", "gh", "gi", "h",
    "k", "kh", "l", "m", "n", "ng", "ngh", "nh", "p", "ph",
    "qu", "r", "s", "t", "th", "tr", "v", "x"
]

# Tone marks applied to the main vowel
# (ngang, sắc, huyền, hỏi, ngã, nặng)
TONE_MAP = {
    'a':  ('a', 'á', 'à', 'ả', 'ã', 'ạ'),
    'ă':  ('ă', 'ắ', 'ằ', 'ẳ', 'ẵ', 'ặ'),
    'â':  ('â', 'ấ', 'ầ', 'ẩ', 'ẫ', 'ậ'),
    'e':  ('e', 'é', 'è', 'ẻ', 'ẽ', 'ẹ'),
    'ê':  ('ê', 'ế', 'ề', 'ể', 'ễ', 'ệ'),
    'i':  ('i', 'í', 'ì', 'ỉ', 'ĩ', 'ị'),
    'o':  ('o', 'ó', 'ò', 'ỏ', 'õ', 'ọ'),
    'ô':  ('ô', 'ố', 'ồ', 'ổ', 'ỗ', 'ộ'),
    'ơ':  ('ơ', 'ớ', 'ờ', 'ở', 'ỡ', 'ợ'),
    'u':  ('u', 'ú', 'ù', 'ủ', 'ũ', 'ụ'),
    'ư':  ('ư', 'ứ', 'ừ', 'ử', 'ữ', 'ự'),
    'y':  ('y', 'ý', 'ỳ', 'ỷ', 'ỹ', 'ỵ'),
}

def apply_tone(rhyme_template: str, tone_index: int) -> str:
    """
    Apply a tone to a rhyme template.
    The template uses uppercase for the tone-bearing vowel.
    e.g., "A" -> tone on 'a', "OAn" -> tone on 'a' in "oan"
    """
    result = []
    for ch in rhyme_template:
        if ch.isupper():
            base = ch.lower()
            if base in TONE_MAP:
                result.append(TONE_MAP[base][tone_index])
            else:
                result.append(base)
        else:
            result.append(ch)
    return ''.join(result)


# Define rhyme templates. Uppercase letter = tone-bearing vowel.
OPEN_RHYMES = [
    # Simple vowels
    "A", "Ă", "Â", "E", "Ê", "I", "O", "Ô", "Ơ", "U", "Ư", "Y",
    # Diphthongs / combinations
    "Ai", "Ao", "Au", "Âu", "Ay", "Ây",
    "Eo", "Êu",
    "Ia", "Iu", "Iê", "IÊu",
    "Oa", "Oe", "Oi", "Ôi", "Ơi",
    "Ua", "Uê", "Ui", "Uo", "Uô", "Ưa", "Ưi", "Ươ", "Ươi", "Ưu",
    # with u- medial
    "uA", "uÂ", "uE", "uÊ", "uI", "uY",
    "uAi", "uAy", "uÂy", "uYa",
]

# Nasal/liquid final rhymes (all 6 tones)
NASAL_FINAL_RHYMES = [
    # -m finals
    "Am", "Ăm", "Âm", "Em", "Êm", "Im", "Om", "Ôm", "Ơm", "Um", "Ưm",
    "Iam", "Iêm", "uAm", "uÂm",
    # -n finals
    "An", "Ăn", "Ân", "En", "Ên", "In", "On", "Ôn", "Ơn", "Un", "Ưn", "Yn",
    "Ian", "Iên", "Oan", "Oăn", "Oen", "uAn", "uÂn", "uÊn", "uIn", "uYn",
    "Ươn", "Uôn", "uYên",
    # -ng finals
    "Ang", "Ăng", "Âng", "Eng", "Ong", "Ông", "Ung", "Ưng",
    "Iang", "Iêng", "Oang", "Oăng", "uAng", "uÂng",
    "Ương", "Uông",
    # -nh finals
    "Anh", "Ênh", "Inh", "Ynh",
    "Oanh", "uÊnh", "uYnh",
]

# Stop final rhymes (only sắc=1 and nặng=5)
STOP_FINAL_RHYMES = [
    # -p finals
    "Ap", "Ăp", "Âp", "Ep", "Êp", "Ip", "Op", "Ôp", "Ơp", "Up", "Ưp",
    "Iêp", "Oap", "uAp", "uÂp", "uYp",
    # -t finals
    "At", "Ăt", "Ât", "Et", "Êt", "It", "Ot", "Ôt", "Ơt", "Ut", "Ưt",
    "Iêt", "Oat", "Oăt", "Oet", "uAt", "uÂt", "uÊt", "uYt",
    "Ươt", "Uôt", "uYêt",
    # -c finals
    "Ac", "Ăc", "Âc", "Oc", "Ôc", "Uc", "Ưc",
    "Iêc", "Oac", "Oăc", "uAc", "uÂc",
    "Ươc", "Uôc",
    # -ch finals
    "Ach", "Êch", "Ich",
    "Oach", "uÊch", "uYch",
]


def is_valid_combination(initial: str, rhyme_template: str) -> bool:
    """Kiểm tra sự kết hợp phụ âm đầu và khuôn vần có hợp lệ theo ngữ âm tiếng Việt."""
    rhyme_lower = rhyme_template.lower()

    # Xác định nguyên âm đầu tiên của vần
    first_vowel = ''
    for ch in rhyme_lower:
        if ch in 'aeêioyăâôơưu':
            first_vowel = ch
            break

    # "gh" và "ngh" CHỈ đi với i, e, ê (và iê, ia)
    if initial in ("gh", "ngh"):
        if first_vowel not in ('i', 'e', 'ê'):
            return False

    # "k" CHỈ đi với i, e, ê, y
    if initial == "k":
        if first_vowel not in ('i', 'e', 'ê', 'y'):
            return False

    # "c", "g", "ng" KHÔNG đi với i, e, ê (thay bằng k, gh, ngh)
    if initial in ("c", "g", "ng"):
        if first_vowel in ('i', 'e', 'ê'):
            return False

    # "qu" không kết hợp với vần bắt đầu bằng u, ư
    if initial == "qu":
        if rhyme_lower.startswith(('u', 'ư')):
            return False

    return True


def merge_initial_and_rhyme(initial: str, rhyme_realized: str) -> str:
    """
    Ghép phụ âm đầu và vần đã điền thanh theo đúng luật chính tả tiếng Việt:
    - gi + i... -> g + i... (gi + ìn -> gìn, gi + iếng -> giếng, gi + iết -> giết)
    - gi + ia -> gia
    - qu + y... / u... -> quy...
    """
    if not initial:
        return rhyme_realized

    rhyme_lower = rhyme_realized.lower()

    # Quy tắc chữ "gi":
    # Khi phụ âm đầu là "gi" và vần bắt đầu bằng nguyên âm "i" hoặc biến thể có dấu của "i":
    # Ký tự "i" trong "gi" và "i" của vần chập làm một.
    if initial == "gi":
        first_char = rhyme_lower[0] if rhyme_lower else ''
        if first_char in ('i', 'í', 'ì', 'ỉ', 'ĩ', 'ị'):
            return "g" + rhyme_realized

    return initial + rhyme_realized


def generate_syllables() -> set[str]:
    """Sinh tất cả các âm tiết hợp lệ tiếng Việt."""
    syllables = set()

    # 1. Vần mở (6 thanh: 0=ngang, 1=sắc, 2=huyền, 3=hỏi, 4=ngã, 5=nặng)
    for rhyme in OPEN_RHYMES:
        for tone in range(6):
            r = apply_tone(rhyme, tone)
            for init in INITIALS:
                if not is_valid_combination(init, rhyme):
                    continue
                s = merge_initial_and_rhyme(init, r)
                if s:
                    syllables.add(s.lower())

    # 2. Vần khép vang (-m, -n, -ng, -nh) (6 thanh)
    for rhyme in NASAL_FINAL_RHYMES:
        for tone in range(6):
            r = apply_tone(rhyme, tone)
            for init in INITIALS:
                if not is_valid_combination(init, rhyme):
                    continue
                s = merge_initial_and_rhyme(init, r)
                if s:
                    syllables.add(s.lower())

    # 3. Vần khép tắc (-p, -t, -c, -ch) (chỉ thanh sắc=1 và nặng=5)
    for rhyme in STOP_FINAL_RHYMES:
        for tone in [1, 5]:
            r = apply_tone(rhyme, tone)
            for init in INITIALS:
                if not is_valid_combination(init, rhyme):
                    continue
                s = merge_initial_and_rhyme(init, r)
                if s:
                    syllables.add(s.lower())

    # 4. Các âm tiết đặc biệt có quy cách chính tả riêng
    special_syllables = [
        # Nhóm "gìn", "giữ gìn", "gìn giữ"
        "gin", "gìn", "gín", "gỉn", "gĩn", "gịn",
        "gim", "gìm", "gím", "gỉm", "gĩm", "gịm",
        "git", "gít", "gịt",
        "gip", "gíp", "gịp",
        "gich", "gích", "gịch",
        "ginh", "gình", "gính", "gỉnh", "gĩnh", "gịnh",
        "giu", "gìu", "gíu", "gỉu", "gĩu", "gịu",
        "giêng", "giềng", "giếng", "giểng", "giễng", "giệng",
        "giên", "giền", "giến", "giển", "giễn", "giện",
        "giêt", "giết", "giệt",
        "giêc", "giếc", "giệc",
        "giêm", "giềm", "giếm", "giểm", "giễm", "giệm",
        "giêu", "giều", "giếu", "giểu", "giễu", "giệu",
        # Nhóm "quy", "qui", "quốc"
        "quy", "quý", "quỳ", "quỷ", "quỹ", "quỵ",
        "qui", "quí", "quì", "quỉ", "quĩ", "quị",
        "quoc", "quốc", "quộc",
        "quo", "quơ", "quở", "quợ", "quớ", "quờ",
        # Từ cảm thán / khẩu ngữ
        "à", "á", "ạ", "ả", "ã", "ơi", "ơi", "ờ", "ớ", "ợ", "ở", "ỡ",
        "ừ", "ứ", "ự", "ử", "ữ", "ừm", "hử", "hở", "ủa", "hả", "úi", "ối",
        "chao", "eo", "ôi", "kìa", "kia", "nọ", "ấy",
    ]
    for sp in special_syllables:
        syllables.add(sp.lower())

    return syllables


# Common Vietnamese words (education, curriculum, everyday)
COMMON_WORDS = [
    # Giáo dục & Hoạt động dạy học
    "giáo dục", "học sinh", "giáo viên", "thầy giáo", "cô giáo", "học tập",
    "kiến thức", "năng lực", "phẩm chất", "kế hoạch bài dạy", "giáo án",
    "chương trình", "mục tiêu", "thiết bị", "học liệu", "tiến trình",
    "phương pháp", "kỹ thuật", "hình thức", "tổ chức", "dạy học", "hoạt động",
    "khởi động", "mở đầu", "xác định vấn đề", "hình thành kiến thức", "khám phá",
    "luyện tập", "thực hành", "vận dụng", "mở rộng", "tìm tòi",
    "đánh giá", "kiểm tra", "thường xuyên", "định kỳ", "giữa kỳ", "cuối kỳ",
    "kết quả", "sản phẩm", "nhiệm vụ", "giao nhiệm vụ", "thực hiện",
    "báo cáo", "thảo luận", "kết luận", "nhận định", "hướng dẫn",
    "phiếu học tập", "sơ đồ tư duy", "bảng kiểm", "thang đo", "rubric",
    "chuẩn bị", "dặn dò", "ghi chép", "quan sát", "lắng nghe", "tích cực",
    "chủ động", "sáng tạo", "tự học", "giao tiếp", "hợp tác", "giải quyết vấn đề",
    "ngôn ngữ", "tính toán", "tin học", "thẩm mỹ", "thể chất",
    "yêu nước", "nhân ái", "chăm chỉ", "trung thực", "trách nhiệm",
    "giữ gìn", "gìn giữ", "rèn luyện", "trau dồi", "bồi dưỡng", "phát triển",
    "liên hệ", "thực tế", "thực tiễn", "đời sống", "môi trường",
    "tham quan", "trải nghiệm", "ngoại khóa", "câu lạc bộ",
    "sách giáo khoa", "sách bài tập", "sách giáo viên", "tài liệu tham khảo",
    "máy chiếu", "bảng phụ", "bút dạ", "thước kẻ", "com pa", "ê ke",

    # Môn học
    "toán học", "ngữ văn", "tiếng việt", "tiếng anh", "ngoại ngữ",
    "lịch sử", "địa lý", "lịch sử và địa lý", "khoa học tự nhiên", "khoa học xã hội",
    "vật lý", "hóa học", "sinh học", "tin học", "công nghệ",
    "giáo dục công dân", "giáo dục kinh tế và pháp luật", "hoạt động trải nghiệm",
    "âm nhạc", "mỹ thuật", "nghệ thuật", "giáo dục thể chất", "quốc phòng an ninh",

    # Cấp học & Quản lý
    "mầm non", "tiểu học", "trung học cơ sở", "trung học phổ thông",
    "đại học", "cao đẳng", "trung cấp", "giáo dục thường xuyên",
    "bộ giáo dục và đào tạo", "sở giáo dục và đào tạo", "phòng giáo dục và đào tạo",
    "ủy ban nhân dân", "ban giám hiệu", "hiệu trưởng", "phó hiệu trưởng",
    "tổ trưởng chuyên môn", "giáo viên chủ nhiệm", "hội đồng sư phạm",

    # Tác giả & Tác phẩm SGK phổ biến
    "ngô tất tố", "nam cao", "vũ trọng phụng", "thạch lam", "tô hoài",
    "nguyễn tuân", "xuân diệu", "huy cận", "hàn mặc tử", "chế lan viên",
    "tố hữu", "nguyễn du", "nguyễn trãi", "hồ xuân hương", "đoàn thị điểm",
    "bà huyện thanh quan", "nguyễn đình chiểu", "nguyễn khuyến", "trần tế xương",
    "hồ chí minh", "võ nguyên giáp", "trần hưng đạo", "lý thường kiệt",
    "quang trung", "nguyễn huệ", "an dương vương", "phù đổng thiên vương",
    "tức nước vỡ bờ", "tắt đèn", "lão hạc", "chí phèo", "dế mèn phiêu lưu ký",
    "truyện kiều", "bình ngô đại cáo", "hịch tướng sĩ", "nam quốc sơn hà",

    # Nhà khoa học kinh điển
    "newton", "niu-tơn", "einstein", "anh-xtanh", "pythagoras", "pi-ta-go",
    "thales", "ta-lét", "archimedes", "ác-si-mét", "pascal", "men-đen",
    "mendeleev", "đác-uyn", "darwin", "galileo",
]


def main():
    print("🔄 Đang sinh bộ từ điển tiếng Việt hoàn chỉnh...")

    syllables = generate_syllables()
    print(f"  ✓ Đã sinh {len(syllables)} âm tiết cơ sở (gồm xử lý chính xác 'gìn', 'giếng', 'quy'...).")

    # Thêm từ tiếng Việt phổ biến & cụm từ
    for phrase in COMMON_WORDS:
        for word in phrase.split():
            syllables.add(word.lower())
        syllables.add(phrase.lower())

    # Thêm từ mượn tiếng Anh phổ biến
    for loanword in COMMON_LOANWORDS:
        # Nếu là cụm từ (ví dụ: "mind map", "check in"), thêm cả cụm lẫn từng từ
        for w in loanword.replace('-', ' ').split():
            syllables.add(w.lower())
        syllables.add(loanword.lower())
        # Thêm biến thể không dấu gạch nối
        if '-' in loanword:
            syllables.add(loanword.replace('-', '').lower())

    # Thêm whitelist ngành giáo dục
    for item in EDUCATION_WHITELIST:
        syllables.add(item.lower())

    sorted_syllables = sorted(syllables)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viet_dict.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for s in sorted_syllables:
            f.write(s + "\n")

    print(f"  ✓ Tổng số mục trong từ điển: {len(sorted_syllables)}")
    print(f"  ✓ Đã lưu file: {output_path}")

    # Kiểm tra nhanh các từ khoá quan trọng
    check_keys = ["gìn", "giữ gìn", "giếng", "giết", "tivi", "rubik", "video", "slide", "kahoot", "stem"]
    print("\n🔍 Kiểm tra từ điển:")
    for k in check_keys:
        found = k in syllables
        print(f"  • {k}: {'✅ CÓ' if found else '❌ THIẾU'}")


if __name__ == "__main__":
    main()
