# 📝 Phần mềm Kiểm tra Giáo án (Kế hoạch bài dạy)

Phần mềm kiểm tra **chính tả**, **thể thức văn bản** và **cấu trúc Giáo án** trên file Microsoft Word (.docx) theo chuẩn **Công văn 5512/BGDĐT-GDTrH** và **Nghị định 30/2020/NĐ-CP**.

---

## ✨ Tính năng chính (Phiên bản 1.1.0)

### 1. Kiểm tra chính tả & đánh máy tiếng Việt nâng cao
- **Từ điển tiếng Việt chuẩn xác (20.000+ từ):** Xử lý đặc thù ngữ âm & chính tả tiếng Việt:
  + Chữ `gi` kết hợp với nguyên âm `i`/`iê`: chữ `i` được chập làm một theo luật chính tả (`gìn` trong *giữ gìn*, *gìn giữ*, `giếng`, `giết`, `gièm`, `giễu`, `gim`, `gíp`...).
  + Chữ `qu`: `quy`, `qui`, `quốc`, `quân`...
- **Bộ từ mượn tiếng Anh / công nghệ giáo dục phổ biến:** Tự động nhận diện không báo lỗi sai với:
  + Thiết bị: `tivi`, `rubik`, `video`, `clip`, `slide`, `laptop`, `smartphone`, `projector`, `micro`, `usb`, `wifi`, `robot`, `drone`...
  + Nền tảng dạy học: `powerpoint`, `word`, `excel`, `pdf`, `canva`, `padlet`, `kahoot`, `quizizz`, `azota`, `shub`, `olm`, `violet`, `teams`, `zoom`, `google meet`...
  + Thuật ngữ STEM / hoạt động: `stem`, `steam`, `coding`, `ai`, `game`, `team`, `group`, `feedback`, `quiz`, `rubric`, `mindmap`, `warm-up`, `wrap-up`...
- **Phát hiện lỗi cặp từ hay sai âm đầu / dấu thanh trong giáo án:**
  + `sử lý` ➔ `xử lý`, `sắp sếp` ➔ `sắp xếp`, `xắp xếp` ➔ `sắp xếp`
  + `chương chình` ➔ `chương trình`, `chực tiếp` ➔ `trực tiếp`, `chích xác` ➔ `chính xác`
  + `dáo viên` ➔ `giáo viên`, `dải thích` ➔ `giải thích`, `giữ dìn` ➔ `giữ gìn`
  + `lăng lực` ➔ `năng lực`, `lo lực` ➔ `nỗ lực`, `học xinh` ➔ `học sinh`
  + `kỉ năng` ➔ `kĩ năng`, `thăm quan` ➔ `tham quan`, `vô hình chung` ➔ `vô hình trung`
  + `sơ xuất` ➔ `sơ suất`, `suất sắc` ➔ `xuất sắc`, `sáng lạng` ➔ `xán lạn`...

### 2. Kiểm tra quy tắc dấu câu & khoảng trắng toàn diện
- **Hệ thống dấu ngoặc & dấu nháy:**
  + Ngoặc tròn `( )`, ngoặc vuông `[ ]`, ngoặc nhọn `{ }`.
  + Ngoặc kép cong tiếng Việt `“ ”`, ngoặc Pháp `« »`, ngoặc kép thẳng `" "`, nháy đơn `‘ ’`.
  + Bắt lỗi thừa khoảng trắng bên trong: `( abc )`, `“ thảo luận ”`, `« chuẩn bị »`.
  + Bắt lỗi dính chữ thiếu khoảng trắng bên ngoài: `học sinh(lớp 8)học bài`.
- **Dấu câu `.` `,` `;` `:` `!` `?` `…`:**
  + Thừa khoảng trắng trước dấu: `chữ ,`, `chữ .`, `chữ :`, `chữ ?`, `chữ !`.
  + Thiếu khoảng trắng sau dấu: `,văn`, `.Kiến thức`, `:toán`.
  + Lỗi kết hợp (thừa trước và thiếu sau): `chữ :nội dung` ➔ `: nội dung`.
  + Dấu ba chấm sai quy cách: `..` (2 dấu chấm) hoặc `....` (4+ dấu chấm) ➔ `...`.
  + Dấu câu lặp lại: `,,`, `;;`, `::`, `??`, `!!`.
  + Hai hoặc nhiều dấu cách liên tiếp (`  +`).

### 3. Vùng bảo vệ thông minh (Tránh bắt nhầm - No False Positives)
Phần mềm tự động nhận diện và **không bắt lỗi** các trường hợp:
- **Số thập phân & phân cách hàng nghìn:** `3,5`, `3.5`, `1.000.000`, `1,000,000`, `12,5%`.
- **Thời gian & tỉ số:** `7:30`, `14:00`, `1:1`, `16:9`.
- **Đường link website & email:** `https://moet.gov.vn`, `phong@edu.vn`.
- **Tên file & phần mở rộng:** `baocao.docx`, `tailieu.pdf`, `video.mp4`.
- **Viết tắt chuẩn có dấu chấm:** `v.v.`, `v.v`, `Th.S`, `PGS.TS`, `TS.`, `GS.TS`, `Đ/c`.
- **Công thức Toán / Hóa học:** `f(x)`, `sin(x)`, `Ca(OH)2`, `H2O`, `CO2`, `25°C`, `AB = 5cm`.

### 4. Kiểm tra Thể thức văn bản (NĐ 30/2020) & Cấu trúc CV 5512
- **Khổ giấy & Căn lề:** Khổ A4, lề trái (3.0 - 3.5cm), lề phải (1.5 - 2.0cm), trên (2.0 - 2.5cm), dưới (2.0 - 2.5cm).
- **Font chữ & Cỡ chữ:** Thống nhất `Times New Roman`, cỡ chữ `13` hoặc `14`.
- **Đề mục bắt buộc CV 5512:**
  + `I. MỤC TIÊU` (1. Kiến thức, 2. Năng lực, 3. Phẩm chất)
  + `II. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU`
  + `III. TIẾN TRÌNH DẠY HỌC` (Đủ 4 hoạt động: HĐ 1 Mở đầu, HĐ 2 Hình thành kiến thức, HĐ 3 Luyện tập, HĐ 4 Vận dụng).

### 5. Xuất file kết quả "Bôi đỏ trực tiếp trên file Word"
- Tách `Run` ở cấp XML (`lxml`), đổi màu đỏ `RGB(255, 0, 0)`, in đậm, gạch chân và kèm gợi ý sửa `[Sửa: ...]`.
- Giữ nguyên toàn bộ định dạng gốc (MathType, hình ảnh, bảng biểu lồng nhau, màu sắc xung quanh).
- Tự động chèn khung **BÁO CÁO TỔNG QUAN LỖI THỂ THỨC** viền đỏ ở đầu trang 1.

---

## 🛠 Cài đặt & Chạy ứng dụng

### Yêu cầu
- Python 3.10+

### Cài đặt thư viện
```bash
cd vn-lesson-checker
python -m venv venv
source venv/bin/activate  # Linux/Mac (hoặc venv\Scripts\activate trên Windows)
pip install -r requirements.txt
```

### Chạy ứng dụng Web (Streamlit)
```bash
streamlit run app.py
```
Mở trình duyệt tại: `http://localhost:8501`

### Chạy kiểm tra tự động (CLI)
```bash
python test_checker.py
```

---

## 📂 Cấu trúc thư mục

```
vn-lesson-checker/
├── app.py                      # Giao diện Web Streamlit
├── requirements.txt            # Danh sách thư viện Python
├── test_checker.py             # Script kiểm tra tự động end-to-end
├── README.md                   # Tài liệu hướng dẫn
├── core/
│   ├── __init__.py
│   ├── constants.py            # Hằng số, Whitelist GD, từ mượn tiếng Anh, CV 5512
│   ├── spell_checker.py        # Engine kiểm tra chính tả & dấu câu nâng cao
│   ├── format_validator.py     # Kiểm tra thể thức lề, font, cấu trúc đề mục
│   └── docx_processor.py       # Xử lý .docx: tách Run cấp XML, bôi đỏ, chèn báo cáo
├── data/
│   ├── viet_dict.txt           # Bộ từ điển tiếng Việt hoàn chỉnh (20.000+ từ)
│   └── generate_dict.py        # Script sinh từ điển tiếng Việt tự động
└── output/                     # Thư mục lưu file giáo án đã kiểm tra
```

## 📝 License
Phần mềm phát triển dành riêng cho giáo viên và các nhà trường tại Việt Nam theo chuẩn quy định hiện hành của Bộ GD&ĐT.
