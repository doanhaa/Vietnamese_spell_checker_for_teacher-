"""
app.py – Giao diện Streamlit cho phần mềm kiểm tra Giáo án.

Chạy: streamlit run app.py
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import streamlit as st

from core.docx_processor import DocxProcessor, ProcessingStats
from core.format_validator import FormatReport

# ──────────────────────────────────────────────
# Cấu hình trang
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Kiểm tra Giáo án",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a5276;
        text-align: center;
        padding: 0.5rem 0;
        border-bottom: 3px solid #2e86c1;
        margin-bottom: 1.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        text-align: center;
        margin-top: -1rem;
        margin-bottom: 2rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: 800;
        line-height: 1.2;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #555;
        margin-top: 0.3rem;
    }
    .error-stat { color: #e74c3c; }
    .warn-stat { color: #f39c12; }
    .ok-stat { color: #27ae60; }
    .info-stat { color: #2e86c1; }
    .stDownloadButton > button {
        background-color: #27ae60 !important;
        color: white !important;
        font-size: 1.1rem !important;
        padding: 0.6rem 2rem !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────

st.markdown('<div class="main-header">📝 Kiểm tra Giáo án (Kế hoạch bài dạy)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Kiểm tra chính tả, thể thức & cấu trúc theo Công văn 5512/BGDĐT-GDTrH</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Sidebar – Cấu hình
# ──────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Cấu hình kiểm tra")
    st.markdown("---")

    check_spelling = st.checkbox("✅ Kiểm tra chính tả & dấu câu", value=True,
                                  help="Bắt lỗi chính tả tiếng Việt, lỗi dấu câu, khoảng trắng")
    check_format = st.checkbox("✅ Kiểm tra thể thức văn bản", value=True,
                                help="Kiểm tra khổ giấy, căn lề, font chữ, cỡ chữ")
    check_structure = st.checkbox("✅ Kiểm tra cấu trúc CV 5512", value=True,
                                   help="Kiểm tra đề mục bắt buộc theo Công văn 5512")
    show_suggestion = st.checkbox("💡 Hiển thị gợi ý sửa [Sửa: ...]", value=True,
                                   help="Chèn gợi ý sửa ngay bên cạnh từ sai")

    st.markdown("---")
    st.markdown("### 📖 Hướng dẫn")
    st.markdown("""
    1. Tải lên file `.docx` (giáo án)
    2. Chọn các tuỳ chọn kiểm tra
    3. Nhấn **Bắt đầu kiểm tra**
    4. Tải về file đã bôi đỏ lỗi
    """)

    st.markdown("---")
    st.markdown("### ℹ️ Thông tin")
    st.markdown("""
    - **Engine:** Rule-based + Từ điển 20.000+ từ
    - **Chuẩn:** NĐ 30/2020, CV 5512/BGDĐT
    - **Bảo vệ:** URL, email, số thập phân, thời gian, tỉ số, công thức
    - **Phiên bản:** 1.1.0
    - **Author: Thai Ha - Computer Science - UIT**
    """)


# ──────────────────────────────────────────────
# Khu vực chính – Upload & Xử lý
# ──────────────────────────────────────────────

uploaded_files = st.file_uploader(
    "📂 Kéo thả file giáo án vào đây (hỗ trợ nhiều file cùng lúc)",
    type=['docx'],
    accept_multiple_files=True,
    help="Chỉ hỗ trợ file .docx (Microsoft Word)",
)

if uploaded_files:
    st.info(f"📋 Đã tải lên **{len(uploaded_files)}** file.")

    # Hiển thị danh sách file
    with st.expander("📄 Danh sách file", expanded=False):
        for f in uploaded_files:
            size_kb = f.size / 1024
            st.write(f"- **{f.name}** ({size_kb:.1f} KB)")

    # Nút xử lý
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        start_button = st.button("🚀 Bắt đầu kiểm tra", type="primary", use_container_width=True)

    if start_button:
        st.markdown("---")

        # Xử lý từng file
        results = []
        progress_bar = st.progress(0, text="Đang xử lý...")

        for file_idx, uploaded_file in enumerate(uploaded_files):
            progress_text = f"Đang xử lý: **{uploaded_file.name}** ({file_idx + 1}/{len(uploaded_files)})"
            progress_bar.progress((file_idx) / len(uploaded_files), text=progress_text)

            # Lưu file tạm
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_in:
                tmp_in.write(uploaded_file.getvalue())
                tmp_input_path = tmp_in.name

            # Tạo đường dẫn output
            stem = Path(uploaded_file.name).stem
            tmp_output_path = os.path.join(tempfile.gettempdir(), f"{stem}_DaKiemTra.docx")

            try:
                # Khởi tạo processor
                processor = DocxProcessor(
                    show_suggestion=show_suggestion,
                    check_spelling=check_spelling,
                    check_format=(check_format or check_structure),
                )

                # Xử lý
                output_path, stats = processor.process(tmp_input_path, tmp_output_path)

                # Đọc file kết quả
                with open(output_path, 'rb') as f:
                    result_bytes = f.read()

                results.append({
                    'name': uploaded_file.name,
                    'output_name': f"{stem}_DaKiemTra.docx",
                    'stats': stats,
                    'bytes': result_bytes,
                    'success': True,
                    'error': None,
                })

            except Exception as e:
                results.append({
                    'name': uploaded_file.name,
                    'output_name': None,
                    'stats': None,
                    'bytes': None,
                    'success': False,
                    'error': str(e),
                })

            finally:
                # Dọn file tạm
                try:
                    os.unlink(tmp_input_path)
                except OSError:
                    pass
                try:
                    if os.path.exists(tmp_output_path):
                        os.unlink(tmp_output_path)
                except OSError:
                    pass

        progress_bar.progress(1.0, text="✅ Hoàn tất!")
        time.sleep(0.5)

        # ── Hiển thị kết quả ──
        st.markdown("## 📊 Kết quả kiểm tra")

        for result in results:
            with st.container():
                st.markdown(f"### 📄 {result['name']}")

                if not result['success']:
                    st.error(f"❌ Lỗi xử lý: {result['error']}")
                    continue

                stats: ProcessingStats = result['stats']

                # Thẻ thống kê
                c1, c2, c3, c4, c5 = st.columns(5)

                with c1:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number error-stat">{stats.total_errors}</div>
                        <div class="stat-label">Tổng lỗi</div>
                    </div>
                    """, unsafe_allow_html=True)

                with c2:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number warn-stat">{stats.total_spelling_errors}</div>
                        <div class="stat-label">Lỗi chính tả</div>
                    </div>
                    """, unsafe_allow_html=True)

                with c3:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number warn-stat">{stats.total_punctuation_errors}</div>
                        <div class="stat-label">Lỗi dấu câu</div>
                    </div>
                    """, unsafe_allow_html=True)

                with c4:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number info-stat">{stats.total_format_errors}</div>
                        <div class="stat-label">Lỗi thể thức</div>
                    </div>
                    """, unsafe_allow_html=True)

                with c5:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number info-stat">{stats.total_structure_errors}</div>
                        <div class="stat-label">Thiếu đề mục</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Chi tiết
                with st.expander("📋 Chi tiết kiểm tra", expanded=False):
                    st.write(f"- Số đoạn văn đã kiểm tra: **{stats.paragraphs_checked}**")
                    st.write(f"- Số bảng đã kiểm tra: **{stats.tables_checked}**")
                    if stats.total_errors == 0:
                        st.success("🎉 Không phát hiện lỗi nào! Giáo án đạt chuẩn.")

                # Nút tải về
                if result['bytes']:
                    st.download_button(
                        label=f"⬇️ Tải về: {result['output_name']}",
                        data=result['bytes'],
                        file_name=result['output_name'],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"download_{result['name']}",
                    )

                st.markdown("---")

        # Tổng kết
        total_all = sum(r['stats'].total_errors for r in results if r['success'])
        success_count = sum(1 for r in results if r['success'])
        st.markdown(f"""
        ### 📈 Tổng kết
        - **{success_count}/{len(results)}** file xử lý thành công
        - **{total_all}** lỗi được phát hiện tổng cộng
        """)

else:
    # Placeholder khi chưa upload
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem; background: #f8f9fa; border-radius: 16px;
                border: 2px dashed #ccc; margin: 2rem 0;">
        <span style="font-size: 4rem;">📂</span>
        <h3 style="color: #888; margin-top: 1rem;">Kéo thả file .docx vào đây để bắt đầu</h3>
        <p style="color: #aaa;">Hỗ trợ nhiều file cùng lúc</p>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.85rem; padding: 1rem;">
    📝 Phần mềm Kiểm tra Giáo án v1.0 | Chuẩn CV 5512/BGDĐT-GDTrH & NĐ 30/2020/NĐ-CP<br>
    Sử dụng engine kiểm tra chính tả tiếng Việt offline (Rule-based + Từ điển)
</div>
""", unsafe_allow_html=True)

