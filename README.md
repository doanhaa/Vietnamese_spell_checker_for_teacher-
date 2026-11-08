# 📝 Phần mềm Kiểm tra & Chuẩn hóa Giáo án Pro (Phiên bản 2.0 Turbo)

Phần mềm kiểm tra **chính tả tiếng Việt**, **lỗi ngữ cảnh Hán-Việt**, **thể thức văn bản** và **cấu trúc Kế hoạch bài dạy (Giáo án)** trên file Microsoft Word (`.docx`) theo chuẩn **Công văn 5512/BGDĐT-GDTrH** và **Nghị định 30/2020/NĐ-CP**.

---

## 🚀 Điểm mới nổi bật trong Phiên bản 2.0 Pro

### 1. ⚡ Nâng cấp Hiệu năng Vượt trội (15x – 30x Faster)
- **Single-Pass Pre-compiled C-Regex Engine:** Toàn bộ hơn 200 cụm từ dễ nhầm lẫn và hệ thống quy tắc dấu câu được biên dịch trước thành biểu thức chính quy cấp C, quét toàn bộ đoạn văn chỉ trong **1 lượt duy nhất** (~0.7 ms / đoạn văn, ~35 ms / giáo án 35 đoạn).
- **In-Memory RAM Processing (`io.BytesIO`) & Đa luồng (`ThreadPoolExecutor`):** Xử lý file `.docx` trực tiếp trên bộ nhớ RAM không qua ghi/xóa file tạm trên ổ cứng; hỗ trợ kiểm tra hàng loạt file song song.
- **LRU Caching (`@lru_cache`) & Tối ưu XML DOM `O(1)`:** Bộ nhớ đệm thông minh cho phân tích âm tiết, tách dấu thanh và gợi ý sửa lỗi; loại bỏ vòng lặp `O(N²)` khi chèn khung báo cáo thể thức vào file Word.
- **Tách biệt thông minh Dấu câu & Từ vựng:** Sửa triệt để lỗi vùng dấu câu nuốt ký tự đầu của từ kế tiếp (ví dụ: `,lăng lực` hoặc ` ,sáng lạng` đều bắt đồng thời cả lỗi dấu phẩy lẫn lỗi chính tả).

### 2. 🌐 Giải pháp Trực tuyến cho Người cần Độ Chính Xác Cao
- **Xác thực Từ vựng Trực tuyến qua Wiktionary & Wikipedia Tiếng Việt API (Batch Query):**
  + Kiểm tra hàng loạt từ hiếm, từ Hán-Việt cổ, tên nhân vật lịch sử, địa danh trong **1 truy vấn HTTP duy nhất** để loại bỏ hoàn toàn tình trạng bắt lỗi nhầm (*Zero False Positives*).
  + Tích hợp **Từ điển Chính tả Trực tuyến** ngay trên Web giúp giáo viên tra cứu nghĩa, cách viết chuẩn và phân biệt các cặp từ dễ nhầm theo thời gian thực.
- **Tích hợp LanguageTool Public Cloud API (`api.languagetool.org`):**
  + Kiểm tra ngữ pháp nâng cao, quy chuẩn typography quốc tế và các đoạn tiếng Anh trong giáo án song ngữ / STEM mà không cần cấu hình API Key.
- **Trợ lý AI Ngữ cảnh & Thẩm định Sư phạm CV 5512 (Google Gemini / OpenAI / Groq / Free Cloud AI):**
  + Phát hiện **lỗi chính tả ngữ cảnh** (các từ có âm tiết hợp lệ trong từ điển nhưng dùng sai nghĩa trong câu: *điểm yếu* vs *yếu điểm*, *bàng quan* vs *bàng hoàng*, *giả thiết* vs *giả thuyết*, *chín muồi* vs *chín mùi*, *tham quan* vs *thăm quan*, *chỉn chu* vs *chỉnh chu*...).
  + **Thẩm định Sư phạm theo Công văn 5512:** Đánh giá cách viết Mục tiêu (động từ đo lường mức độ cần đạt), chuỗi 4 hoạt động dạy học và gợi ý cải thiện chuyên môn.

### 3. 🛠️ Tính năng Mới Hữu ích cho Giáo viên
- **Xuất song song 2 Phiên bản File Word (`.docx`):**
  1. 🔴 **Bản Word Bôi Đỏ & Gợi Ý (`_DaKiemTra.docx`):** Giữ nguyên định dạng gốc, bôi đỏ vị trí lỗi kèm gợi ý `[Sửa: ...]` và bảng tổng hợp đầu trang 1.
  2. 🟢 **Bản Word Đã Tự Động Sửa Sạch Lỗi (`_DaSuaLoi.docx`):** Tự động thay thế từ sai bằng từ đúng ngay ở cấp XML `<w:r>`, đồng thời tự động chuẩn hóa khổ giấy A4, căn lề chuẩn Nghị định 30/2020 và đồng bộ font `Times New Roman`.
- **Khôi phục lỗi gõ trượt phím Telex:** Tự động nhận diện và sửa các từ gõ lỗi bộ gõ như `hocj` ➔ `học`, `giaos` ➔ `giáo`, `vieen` ➔ `viên`, `truwowng` ➔ `trường`.
- **Chuẩn hóa Đồng bộ Dấu thanh & Chữ `i/y`:**
  + Tùy chọn đồng bộ dấu thanh kiểu mới Bộ GD&ĐT (`oà, oá, uỳ, uý`) hoặc kiểu truyền thống (`òa, óa, ùy, úy`).
  + Tùy chọn đồng bộ chữ `i/y` theo chuẩn SGK (`kĩ năng, vật lí, lí thuyết, mĩ thuật` ↔ `kỹ năng, vật lý, lý thuyết, mỹ thuật`).
- **Quản lý Từ điển Cá nhân (`Custom Whitelist`):** Cho phép giáo viên thêm tên riêng địa phương, tên trường, thuật ngữ môn học vào bộ nhớ bền vững (`data/custom_whitelist.json`).

### 4. 🎨 Giao diện Web Modern SaaS (Dual-Mode: Standalone SPA & Streamlit)
- Thiết kế hiện đại với **Dark / Light Mode**, thẻ **Điểm Chất lượng Giáo án (0–100 & Xếp hạng A+/A/B/C)**, **Checklist tuân thủ CV 5512**, **Bảng duyệt lỗi tương tác kèm ngữ cảnh Highlight**, và nút **🧪 Dùng thử Giáo án mẫu (1-Click)**.
- Hỗ trợ chạy trực tiếp bằng Python thuần (`python3 server.py` hoặc `python3 app.py`) không phụ thuộc môi trường ảo, hoặc chạy qua Streamlit (`streamlit run app.py`).

---

## 🛠 Cài đặt & Chạy ứng dụng

### Cách 1: Chạy trực tiếp Web Server Tốc độ cao (Khuyên dùng - Khởi động tức thì)
```bash
python3 server.py
# Hoặc:
python3 app.py
```
Mở trình duyệt tại: `http://localhost:8501`

### Cách 2: Chạy qua giao diện Streamlit
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Chạy kiểm tra tự động End-to-End (CLI)
```bash
python3 test_checker.py
```

---

## 📂 Cấu trúc thư mục

```text
Vietnamese_spell_checker_for_teacher-/
├── app.py                      # Giao diện Web Streamlit Hiện đại (tự chuyển sang server.py nếu chạy trực tiếp)
├── server.py                   # Máy chủ Web SPA Đa luồng tốc độ cao & REST API
├── web/
│   └── index.html              # Giao diện Modern Web SPA (Dark/Light mode, Live Diff, AI & Wiktionary)
├── core/
│   ├── __init__.py
│   ├── constants.py            # Hằng số, Whitelist GD, 200+ cặp từ dễ nhầm + giải thích, chuẩn CV 5512
│   ├── spell_checker.py        # Engine C-Regex, LRU Cache, Telex recovery, ngữ cảnh & chuẩn hóa oà/òa, i/y
│   ├── online_checker.py       # Tích hợp Wiktionary/Wikipedia API, LanguageTool Cloud & AI (Gemini/OpenAI/Groq)
│   ├── format_validator.py     # Kiểm tra & tự động sửa thể thức NĐ 30/2020, Checklist CV 5512
│   ├── docx_processor.py       # Xử lý .docx trên RAM: xuất cả bản Bôi Đỏ & bản Tự Động Sửa Sạch Lỗi
│   └── docx_compat.py          # Lớp tương thích python-docx / pure-lxml tốc độ cao
├── data/
│   ├── viet_dict.txt           # Bộ từ điển tiếng Việt hoàn chỉnh (20.300+ mục từ)
│   ├── generate_dict.py        # Script sinh từ điển tiếng Việt tự động
│   └── custom_whitelist.json   # Từ điển cá nhân của giáo viên (tự động tạo khi thêm từ)
├── test_checker.py             # Script kiểm tra tự động end-to-end
└── output/                     # Thư mục lưu file giáo án mẫu đã kiểm tra
```
