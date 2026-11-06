"""
test_checker.py – Tạo file giáo án mẫu có lỗi cố ý, rồi chạy kiểm tra.

Chạy: python test_checker.py
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os
import sys

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_sample_giao_an(output_path: str):
    """Tạo file giáo án mẫu với các lỗi cố ý để test."""
    doc = Document()

    # ── Cấu hình trang (cố ý sai lề) ──
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.5)    # SAI: phải 3.0-3.5
    section.right_margin = Cm(1.5)   # Đúng
    section.top_margin = Cm(2.0)     # Đúng
    section.bottom_margin = Cm(2.0)  # Đúng

    # ── Tiêu đề ──
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run('KẾ HOẠCH BÀI DẠY')
    run.bold = True
    run.font.size = Pt(14)
    run.font.name = 'Times New Roman'

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run('Môn: Ngữ văn – Lớp 8')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    info = doc.add_paragraph()
    run = info.add_run('Bài: Tức nước vỡ bờ (Trích Tắt đèn – Ngô Tất Tố)')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    time_p = doc.add_paragraph()
    run = time_p.add_run('Thời gian thực hiện: 2 tiết')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    # ── I. MỤC TIÊU ──
    h1 = doc.add_paragraph()
    run = h1.add_run('I. MỤC TIÊU')
    run.bold = True
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    # 1. Kiến thức (có lỗi chính tả cố ý)
    h2 = doc.add_paragraph()
    run = h2.add_run('1. Kiến thức')
    run.bold = True
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p1 = doc.add_paragraph()
    # Lỗi: "sử lý" → "xử lý", thừa 2 dấu cách
    run = p1.add_run('- HS nắm được nội dung và nghệ thuật  của đoạn chích. GV hướng dẫn HS sử lý văn bản.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    # 2. Năng lực
    h2b = doc.add_paragraph()
    run = h2b.add_run('2. Năng lực')
    run.bold = True
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p2 = doc.add_paragraph()
    # Lỗi: "lăng lực" → "năng lực", thiếu dấu cách sau dấu chấm
    run = p2.add_run('- Phát chiển lăng lực tự học,lăng lực giao tiếp và hợp tác.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    # 3. Phẩm chất
    h2c = doc.add_paragraph()
    run = h2c.add_run('3. Phẩm chất')
    run.bold = True
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p3 = doc.add_paragraph()
    # Lỗi: thừa khoảng trắng trước dấu phẩy
    run = p3.add_run('- Giáo dục HS lòng yêu thương , sự đồng cảm với nhân vật.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    # ── II. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU ──
    h1b = doc.add_paragraph()
    run = h1b.add_run('II. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU')
    run.bold = True
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p4 = doc.add_paragraph()
    run = p4.add_run('- GV: SGK, SGV, máy chiếu, bảng phụ.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p5 = doc.add_paragraph()
    # Lỗi font: dùng Arial thay vì Times New Roman
    run = p5.add_run('- HS: SGK, SBT, vở ghi, bút màu.')
    run.font.size = Pt(13)
    run.font.name = 'Arial'  # SAI FONT

    # ── III. TIẾN TRÌNH DẠY HỌC ──
    h1c = doc.add_paragraph()
    run = h1c.add_run('III. TIẾN TRÌNH DẠY HỌC')
    run.bold = True
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    # Bảng hoạt động (mô phỏng giáo án thực tế)
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'

    # Header
    hdr = table.rows[0]
    for i, text in enumerate(['HOẠT ĐỘNG CỦA GV', 'HOẠT ĐỘNG CỦA HS', 'SẢN PHẨM DỰ KIẾN']):
        run = hdr.cells[i].paragraphs[0].add_run(text)
        run.bold = True
        run.font.size = Pt(13)
        run.font.name = 'Times New Roman'

    # HĐ 1: Mở đầu
    row1 = table.add_row()
    # GV
    p = row1.cells[0].paragraphs[0]
    run = p.add_run('Hoạt động 1: Mở đầu (5 phút)')
    run.bold = True
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p = row1.cells[0].add_paragraph()
    # Lỗi trong bảng: "chương chình" → "chương trình"
    run = p.add_run('GV giới thiệu chương chình bài học. Yêu cầu HS nhớ lại kiến thức bài trước.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    # HS
    p = row1.cells[1].paragraphs[0]
    run = p.add_run('HS lắng nghe và chuẩn bị sách vở.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    # Sản phẩm
    p = row1.cells[2].paragraphs[0]
    run = p.add_run('HS sẵn sàng vào bài mới.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    # HĐ 2: Hình thành kiến thức
    row2 = table.add_row()
    p = row2.cells[0].paragraphs[0]
    run = p.add_run('Hoạt động 2: Hình thành kiến thức mới (25 phút)')
    run.bold = True
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p = row2.cells[0].add_paragraph()
    # Lỗi: "sắp sếp" → "sắp xếp", "chực tiếp" → "trực tiếp"
    run = p.add_run('GV yêu cầu HS đọc văn bản và sắp sếp các sự kiện. GV hướng dẫn chực tiếp HS phân tích nhân vật.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p = row2.cells[1].paragraphs[0]
    run = p.add_run('HS đọc văn bản, thảo luận nhóm.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p = row2.cells[2].paragraphs[0]
    # Lỗi: "dải thích" → "giải thích"
    run = p.add_run('HS dải thích được ý nghĩa đoạn trích.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    # HĐ 3: Luyện tập
    row3 = table.add_row()
    p = row3.cells[0].paragraphs[0]
    run = p.add_run('Hoạt động 3: Luyện tập (10 phút)')
    run.bold = True
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p = row3.cells[0].add_paragraph()
    run = p.add_run('GV yêu cầu HS làm bài tập trong SGK.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p = row3.cells[1].paragraphs[0]
    run = p.add_run('HS làm bài tập cá nhân.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p = row3.cells[2].paragraphs[0]
    run = p.add_run('Bài tập hoàn chỉnh.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    # HĐ 4: Vận dụng
    row4 = table.add_row()
    p = row4.cells[0].paragraphs[0]
    run = p.add_run('Hoạt động 4: Vận dụng (5 phút)')
    run.bold = True
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p = row4.cells[0].add_paragraph()
    # Lỗi: "thăm quan" → "tham quan"
    run = p.add_run('GV giao nhiệm vụ về nhà: Viết đoạn văn cảm nhận. HS có thể thăm quan thư viện để tìm tài liệu.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p = row4.cells[1].paragraphs[0]
    run = p.add_run('HS ghi nhận nhiệm vụ.')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    p = row4.cells[2].paragraphs[0]
    run = p.add_run('Đoạn văn cảm nhận (300 từ).')
    run.font.size = Pt(13)
    run.font.name = 'Times New Roman'

    # Lưu file
    doc.save(output_path)
    print(f"✅ Đã tạo file giáo án mẫu: {output_path}")


def test_checker(input_path: str):
    """Chạy kiểm tra trên file giáo án mẫu."""
    from core.docx_processor import DocxProcessor

    processor = DocxProcessor(
        show_suggestion=True,
        check_spelling=True,
        check_format=True,
    )

    output_path = input_path.replace('.docx', '_DaKiemTra.docx')
    result_path, stats = processor.process(input_path, output_path)

    print(f"\n{'='*60}")
    print(f"📊 KẾT QUẢ KIỂM TRA")
    print(f"{'='*60}")
    print(f"  📄 File gốc:      {input_path}")
    print(f"  📝 File kết quả:  {result_path}")
    print(f"  {'─'*56}")
    print(f"  📝 Số đoạn kiểm tra: {stats.paragraphs_checked}")
    print(f"  📊 Số bảng kiểm tra: {stats.tables_checked}")
    print(f"  {'─'*56}")
    print(f"  🔴 Lỗi chính tả:    {stats.total_spelling_errors}")
    print(f"  🟡 Lỗi dấu câu:     {stats.total_punctuation_errors}")
    print(f"  🔵 Lỗi thể thức:    {stats.total_format_errors}")
    print(f"  📋 Thiếu đề mục:    {stats.total_structure_errors}")
    print(f"  {'─'*56}")
    print(f"  ❌ TỔNG LỖI:        {stats.total_errors}")
    print(f"{'='*60}")

    if stats.total_errors > 0:
        print(f"\n✅ Mở file {result_path} trong Microsoft Word để xem kết quả bôi đỏ.")
    else:
        print(f"\n🎉 Không phát hiện lỗi nào!")


if __name__ == '__main__':
    sample_path = os.path.join(os.path.dirname(__file__), 'output', 'giao_an_mau.docx')
    os.makedirs(os.path.dirname(sample_path), exist_ok=True)

    print("📝 Tạo file giáo án mẫu có lỗi cố ý...")
    create_sample_giao_an(sample_path)

    print("\n🔍 Bắt đầu kiểm tra...")
    test_checker(sample_path)

