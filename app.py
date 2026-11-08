"""
app.py – Giao diện Web Hiện đại (Streamlit & Standalone Dual-Mode) cho Phần mềm Kiểm tra Giáo án Pro v2.0.

Cách chạy:
  1. Chạy qua Streamlit:  streamlit run app.py
  2. Chạy trực tiếp:      python3 app.py  (hoặc python3 server.py)
"""

from __future__ import annotations

import csv
import html
import io
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Nếu người dùng chạy `python3 app.py` trực tiếp hoặc môi trường chưa cài streamlit -> Chạy Standalone Web Server
try:
    import streamlit as st
    from streamlit.runtime import exists as _st_runtime_exists
    _IS_STREAMLIT_RUN = _st_runtime_exists()
except ImportError:
    st = None
    _IS_STREAMLIT_RUN = False

if not _IS_STREAMLIT_RUN:
    if __name__ == "__main__":
        from server import run_server
        run_server(port=8501)
    sys.exit(0)

# ──────────────────────────────────────────────
# STREAMLIT MODERN WEB UI (Khi chạy `streamlit run app.py`)
# ──────────────────────────────────────────────

from core.constants import CONFUSABLE_DETAILS, ErrorType
from core.docx_processor import DocxProcessor, ProcessingStats, format_visible_token
from core.online_checker import OnlineHighPrecisionChecker
from core.spell_checker import (
    VietnameseSpellChecker,
    SpellError,
    load_custom_whitelist,
    add_custom_words,
    remove_custom_word,
)
from test_checker import build_sample_giao_an_bytes

st.set_page_config(
    page_title="Kiểm tra & Chuẩn hóa Giáo án Pro v2.0",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_cached_engines() -> tuple[VietnameseSpellChecker, OnlineHighPrecisionChecker]:
    """Khởi tạo và giữ bộ kiểm tra chính tả + từ điển 20.000+ từ trên RAM xuyên suốt phiên làm việc."""
    checker = VietnameseSpellChecker(check_context=True)
    online = OnlineHighPrecisionChecker(checker)
    return checker, online


spell_engine, online_engine = get_cached_engines()

# ──────────────────────────────────────────────
# Modern SaaS Custom CSS
# ──────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Be Vietnam Pro', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .hero-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 55%, #4f46e5 100%);
        color: #ffffff;
        padding: 1.75rem 2.2rem;
        border-radius: 18px;
        margin-bottom: 1.5rem;
        box-shadow: 0 12px 30px rgba(37, 99, 235, 0.22);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        opacity: 0.9;
        margin-top: 0.3rem;
    }
    .hero-badge {
        background: rgba(255, 255, 255, 0.18);
        backdrop-filter: blur(8px);
        padding: 0.45rem 1rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
        border: 1px solid rgba(255,255,255,0.28);
    }

    .metric-card {
        background: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 14px;
        padding: 1.15rem 1rem;
        text-align: center;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
        transition: transform 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-val {
        font-size: 2.1rem;
        font-weight: 800;
        line-height: 1.15;
    }
    .metric-lbl {
        font-size: 0.82rem;
        color: #334155 !important;
        font-weight: 700;
        margin-top: 0.3rem;
    }

    .context-box {
        background: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
        border-left: 5px solid #2563eb !important;
        border-radius: 12px;
        padding: 0.95rem 1.2rem;
        margin-bottom: 0.8rem;
        font-size: 0.94rem;
        line-height: 1.75;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
    }
    .ctx-header {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 0.55rem;
        padding-bottom: 0.45rem;
        border-bottom: 1px dashed #cbd5e1;
    }
    .ctx-loc-badge {
        background: #0f172a !important;
        color: #ffffff !important;
        padding: 0.18rem 0.65rem;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 700;
    }
    .ctx-type-badge {
        background: #dbeafe !important;
        color: #1e3a8a !important;
        border: 1px solid #93c5fd;
        padding: 0.18rem 0.65rem;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 700;
    }
    .ctx-desc {
        color: #1e293b !important;
        font-weight: 600;
        font-size: 0.88rem;
    }
    .ctx-quote {
        background: #f1f5f9 !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 0.65rem 0.95rem;
        font-size: 0.95rem;
        line-height: 1.8;
    }
    .ctx-text {
        color: #0f172a !important;
        font-weight: 500;
    }
    .err-inline {
        background: #fee2e2 !important;
        color: #991b1b !important;
        border: 1.5px solid #ef4444 !important;
        font-weight: 800 !important;
        padding: 0.12rem 0.5rem;
        border-radius: 6px;
        margin: 0 0.15rem;
        display: inline-block;
    }
    .sug-inline {
        background: #d1fae5 !important;
        color: #065f46 !important;
        border: 1.5px solid #10b981 !important;
        font-weight: 800 !important;
        padding: 0.12rem 0.55rem;
        border-radius: 6px;
        margin: 0 0.2rem;
        display: inline-block;
        font-size: 0.9em;
    }
    .check-badge-ok {
        display: inline-block;
        background: #d1fae5 !important;
        color: #065f46 !important;
        border: 1px solid #34d399;
        padding: 0.28rem 0.65rem;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
        margin: 0.2rem;
    }
    .check-badge-fail {
        display: inline-block;
        background: #fee2e2 !important;
        color: #991b1b !important;
        border: 1px solid #f87171;
        padding: 0.28rem 0.65rem;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Hero Banner
# ──────────────────────────────────────────────

st.markdown("""
<div class="hero-banner">
    <div>
        <div class="hero-title">📝 Kiểm tra & Chuẩn hóa Giáo án Pro v2.0</div>
        <div class="hero-subtitle">Kiểm tra Chính tả, Ngữ cảnh Hán-Việt, Thể thức NĐ 30/2020 & Cấu trúc Công văn 5512 • Tích hợp Wiktionary, LanguageTool & AI</div>
    </div>
    <div class="hero-badge">⚡ Engine C-Regex + RAM Turbo • Độ chính xác cao</div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Sidebar – Cấu hình Toàn diện
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Cấu hình Kiểm tra")
    check_spelling = st.checkbox("✅ Chính tả & Dấu câu", value=True,
                                 help="Từ điển 20.000+ âm tiết, 200+ cặp từ dễ nhầm, khôi phục lỗi gõ Telex")
    check_context = st.checkbox("✅ Ngữ cảnh Hán-Việt & Lặp từ", value=True,
                                help="Bắt lỗi yếu điểm/điểm yếu, bàng quan/bàng hoàng, giả thiết/giả thuyết, lặp từ...")
    check_format = st.checkbox("✅ Thể thức NĐ 30 & Cấu trúc CV 5512", value=True,
                               help="Kiểm tra khổ A4, căn lề, font Times New Roman 13-14pt, đủ 4 hoạt động")
    show_suggestion = st.checkbox("💡 Chèn gợi ý [Sửa: ...] vào file Word", value=True)

    st.markdown("---")
    st.markdown("### 🌐 Giải pháp Độ Chính Xác Cao (Online)")
    online_wiktionary = st.checkbox(
        "🌐 Xác thực từ hiếm qua Wiktionary/Wikipedia",
        value=True,
        help="Tự động kiểm tra các từ hiếm, tên riêng lịch sử/địa lý trên Wiktionary & Wikipedia Tiếng Việt để chống bắt lỗi nhầm",
    )
    online_languagetool = st.checkbox(
        "🌍 LanguageTool Cloud API",
        value=False,
        help="Kiểm tra ngữ pháp & quy tắc khoảng trắng quốc tế / đoạn tiếng Anh song ngữ (Không cần API key)",
    )
    online_ai = st.checkbox(
        "🤖 Kiểm tra Ngữ cảnh Sâu bằng AI",
        value=False,
        help="Sử dụng mô hình ngôn ngữ lớn để phát hiện lỗi từ đồng âm khác nghĩa & lỗi câu",
    )

    ai_provider_label = st.selectbox(
        "Nhà cung cấp Cloud AI",
        options=[
            "free_cloud (Miễn phí - Không cần Key)",
            "gemini (Google Gemini API)",
            "openai (OpenAI GPT-4o-mini)",
            "groq (Groq Llama-3.3-70B)",
            "deepseek (DeepSeek API)",
        ],
        index=0,
    )
    ai_provider = ai_provider_label.split()[0]
    ai_api_key = st.text_input("🔑 API Key (Tùy chọn)", type="password", placeholder="Nhập nếu dùng Gemini/OpenAI/Groq...")

    st.markdown("---")
    st.markdown("### 🔄 Chuẩn hóa Đồng bộ Chính tả")
    tone_opt = st.selectbox(
        "Quy tắc dấu thanh (oa, oe, uy)",
        options=[
            ("keep", "Giữ nguyên theo bản gốc"),
            ("new", "Kiểu mới Bộ GD&ĐT (oà, oá, uỳ)"),
            ("old", "Kiểu truyền thống (òa, óa, ùy)"),
        ],
        format_func=lambda x: x[1],
    )[0]
    iy_opt = st.selectbox(
        "Đồng bộ chữ i / y (kĩ/kỹ, lí/lý)",
        options=[
            ("keep", "Giữ nguyên theo bản gốc"),
            ("i", "Chuẩn SGK hiện hành (kĩ năng, vật lí)"),
            ("y", "Chuẩn chữ y dài (kỹ năng, vật lý)"),
        ],
        format_func=lambda x: x[1],
    )[0]

    st.markdown("---")
    st.caption("Developed by **Thai Ha - Computer Science - UIT** | Phiên bản **2.0 Pro**")


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _build_csv_report(filename: str, stats: ProcessingStats) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["STT", "File", "Vị trí", "Loại lỗi", "Từ / Cụm sai", "Gợi ý sửa", "Giải thích", "Ngữ cảnh"])
    for ed in stats.error_details:
        writer.writerow([
            ed.id,
            filename,
            ed.location,
            ed.error_type,
            ed.wrong_text,
            ed.suggestion,
            ed.description,
            ed.context_snippet,
        ])
    return buf.getvalue().encode("utf-8-sig")


def _process_single_file_task(item: tuple[str, bytes], cfg: dict) -> dict:
    fname, raw_bytes = item
    stem = Path(fname).stem
    try:
        processor = DocxProcessor(
            show_suggestion=cfg["show_suggestion"],
            check_spelling=cfg["check_spelling"],
            check_format=cfg["check_format"],
            check_context=cfg["check_context"],
            online_verify_wiktionary=cfg["online_wiktionary"],
            online_languagetool=cfg["online_languagetool"],
            online_ai_check=cfg["online_ai"],
            ai_provider=cfg["ai_provider"],
            ai_api_key=cfg["ai_api_key"],
            normalize_tone=cfg["tone_opt"],
            normalize_iy=cfg["iy_opt"],
        )
        res = processor.process_bytes(raw_bytes, generate_auto_fixed=True, auto_fix_format=True)
        return {
            "name": fname,
            "marked_name": f"{stem}_DaKiemTra.docx",
            "fixed_name": f"{stem}_DaSuaLoi.docx",
            "stats": res["stats"],
            "marked_bytes": res["marked_bytes"],
            "fixed_bytes": res["fixed_bytes"],
            "success": True,
            "error": None,
        }
    except Exception as e:
        return {
            "name": fname,
            "success": False,
            "error": str(e),
        }


# ──────────────────────────────────────────────
# 4 Main Workspace Tabs
# ──────────────────────────────────────────────

tab_docx, tab_live, tab_online, tab_dict = st.tabs([
    "📂 1. Kiểm tra File Giáo án (.docx)",
    "✍️ 2. Kiểm tra & Chuẩn hóa Văn bản Trực tiếp",
    "🌐 3. Tra cứu Chính tả & Thẩm định Sư phạm AI",
    "⚙️ 4. Từ điển Cá nhân & Quy chuẩn",
])

# ══════════════════════════════════════════════
# TAB 1: KIỂM TRA FILE GIÁO ÁN (.DOCX)
# ══════════════════════════════════════════════
with tab_docx:
    col_up, col_sample = st.columns([3, 1])
    with col_up:
        uploaded_files = st.file_uploader(
            "📂 Kéo thả một hoặc nhiều file Giáo án (.docx) vào đây",
            type=["docx"],
            accept_multiple_files=True,
        )
    with col_sample:
        st.markdown("<div style='height: 1.7rem'></div>", unsafe_allow_html=True)
        run_sample_btn = st.button("🧪 Dùng thử Giáo án mẫu (1-Click)", width="stretch")

    current_cfg = {
        "show_suggestion": show_suggestion,
        "check_spelling": check_spelling,
        "check_format": check_format,
        "check_context": check_context,
        "online_wiktionary": online_wiktionary,
        "online_languagetool": online_languagetool,
        "online_ai": online_ai,
        "ai_provider": ai_provider,
        "ai_api_key": ai_api_key,
        "tone_opt": tone_opt,
        "iy_opt": iy_opt,
    }

    files_to_process: list[tuple[str, bytes]] = []
    if run_sample_btn:
        files_to_process = [("Giao_an_Mau_Ngu_Van_8.docx", build_sample_giao_an_bytes())]
    elif uploaded_files:
        if st.button("🚀 Bắt đầu Kiểm tra & Tạo Bản Tự Động Sửa Lỗi", type="primary", width="stretch"):
            files_to_process = [(f.name, f.getvalue()) for f in uploaded_files]

    if files_to_process:
        with st.spinner(f"Đang xử lý {len(files_to_process)} file giáo án trên RAM..."):
            with ThreadPoolExecutor(max_workers=min(4, len(files_to_process))) as pool:
                st.session_state["docx_results"] = list(
                    pool.map(lambda item: _process_single_file_task(item, current_cfg), files_to_process)
                )

    results = st.session_state.get("docx_results", [])
    for idx, res in enumerate(results):
        st.markdown(f"### 📄 {res['name']}")
        if not res["success"]:
            st.error(f"❌ Lỗi xử lý: {res['error']}")
            continue

        stats: ProcessingStats = res["stats"]
        score_color = "#059669" if stats.quality_score >= 85 else ("#d97706" if stats.quality_score >= 65 else "#dc2626")

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:{score_color}">{stats.quality_score}/100</div><div class="metric-lbl">Điểm ({stats.quality_grade})</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#dc2626">{stats.total_errors}</div><div class="metric-lbl">Tổng số lỗi</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#e11d48">{stats.total_spelling_errors + stats.total_context_errors}</div><div class="metric-lbl">Lỗi Chính tả / Ngữ cảnh</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#d97706">{stats.total_punctuation_errors}</div><div class="metric-lbl">Lỗi Dấu câu</div></div>', unsafe_allow_html=True)
        with m5:
            st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#2563eb">{stats.total_format_errors + stats.total_structure_errors}</div><div class="metric-lbl">Lỗi Thể thức & CV 5512</div></div>', unsafe_allow_html=True)
        with m6:
            st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#475569">{stats.processing_time_ms}ms</div><div class="metric-lbl">{stats.paragraphs_checked} đoạn • {stats.total_words} từ</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

        # 3 Nút tải về: Bản Bôi Đỏ, Bản Tự Động Sửa Sạch, Báo cáo CSV
        dl1, dl2, dl3 = st.columns(3)
        with dl1:
            st.download_button(
                label=f"🔴 Tải Bản Word Bôi Đỏ ({res['marked_name']})",
                data=res["marked_bytes"],
                file_name=res["marked_name"],
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"dl_marked_{idx}_{res['name']}",
                width="stretch",
            )
        with dl2:
            st.download_button(
                label=f"🟢 Tải Bản Đã Tự Động Sửa Sạch ({res['fixed_name']})",
                data=res["fixed_bytes"],
                file_name=res["fixed_name"],
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"dl_fixed_{idx}_{res['name']}",
                width="stretch",
            )
        with dl3:
            csv_bytes = _build_csv_report(res["name"], stats)
            st.download_button(
                label="📊 Tải Báo cáo Chi tiết (.CSV / Excel)",
                data=csv_bytes,
                file_name=f"{Path(res['name']).stem}_BaoCaoLoi.csv",
                mime="text/csv",
                key=f"dl_csv_{idx}_{res['name']}",
                width="stretch",
            )

        if stats.verified_online_words:
            st.info(
                f"🌐 **Đã xác thực trực tuyến trên Wiktionary/Wikipedia ({len(stats.verified_online_words)} từ):** "
                + ", ".join(stats.verified_online_words)
                + " — Đã tự động bảo vệ không báo lỗi nhầm."
            )

        # Checklist cấu trúc CV 5512 & Thể thức
        if stats.format_report:
            with st.expander("📋 Xem Checklist Cấu trúc Công văn 5512 & Thể thức Nghị định 30/2020", expanded=stats.format_report.has_errors):
                if stats.format_report.errors:
                    for fe in stats.format_report.errors:
                        st.warning(f"**[{fe.error_type.value}]** {fe.message}" + (f" — *{fe.detail}*" if fe.detail else ""))
                if stats.format_report.section_checklist:
                    badges_html = "".join(
                        f'<span class="{"check-badge-ok" if c["found"] else "check-badge-fail"}">'
                        f'{"✅" if c["found"] else "❌"} {html.escape(c["label"])}</span>'
                        for c in stats.format_report.section_checklist
                    )
                    st.markdown(f"<div><strong>Đề mục chuẩn CV 5512:</strong><br/>{badges_html}</div>", unsafe_allow_html=True)

        # Danh sách chi tiết từng lỗi kèm ngữ cảnh
        if stats.error_details:
            with st.expander(f"🔍 Duyệt chi tiết {len(stats.error_details)} lỗi trong ngữ cảnh đoạn văn", expanded=True):
                search_kw = st.text_input("Lọc nhanh theo từ khóa hoặc vị trí:", key=f"filter_err_{idx}")
                for ed in stats.error_details:
                    if search_kw and search_kw.lower() not in (ed.wrong_text + ed.suggestion + ed.description + ed.location).lower():
                        continue
                    st.markdown(
                        f'<div class="context-box">'
                        f'<div class="ctx-header">'
                        f'<span class="ctx-loc-badge">#{ed.id} • {html.escape(ed.location)}</span>'
                        f'<span class="ctx-type-badge">{html.escape(ed.error_type)}</span>'
                        f'<span class="ctx-desc">— {html.escape(ed.description)}</span>'
                        f'</div>'
                        f'<div class="ctx-quote">{ed.context_html}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.success("🎉 Không phát hiện lỗi chính tả hay dấu câu nào! Giáo án đạt chuẩn xuất sắc.")

        st.markdown("---")


# ══════════════════════════════════════════════
# TAB 2: KIỂM TRA VĂN BẢN TRỰC TIẾP (LIVE PROOFREADER)
# ══════════════════════════════════════════════
with tab_live:
    st.markdown("#### ✍️ Kiểm tra & Tự động Sửa Văn bản Tức thì")
    default_sample_text = (
        "I. MỤC TIÊU:\n"
        "- Phát chiển lăng lực tự học ,lăng lực giao tiếp và hợp tác cho học xinh.\n"
        "- GV hướng dẫn HS sử lý văn bản  một cách xúc tích, khắc phục những yếu điểm khi thuyết chình.\n"
        "- Giáo dục HS không có thái độ bàng hoàng trước nỗi đau của của người khác, biết giữ dìn văn hóa dân tộc và chuẩn bị bài chỉnh chu trước khi đi thăm quan bảo tàng."
    )
    live_input = st.text_area("Nhập hoặc dán đoạn văn bản giáo án cần kiểm tra:", value=default_sample_text, height=160)

    if st.button("🔍 Kiểm tra & Tự động Chuẩn hóa Văn bản", type="primary"):
        t0 = time.perf_counter()
        spell_engine.reload_custom_whitelist()
        spell_engine.check_context = check_context
        errs = spell_engine.check_text(live_input)

        if online_wiktionary and errs:
            errs, verified_list = online_engine.filter_false_positives_online(errs)
        else:
            verified_list = []

        if online_languagetool:
            errs.extend(online_engine.check_with_languagetool(live_input))

        if online_ai:
            ai_errs, ai_err_msg = online_engine.check_contextual_ai(
                live_input, provider=ai_provider, api_key=ai_api_key
            )
            errs.extend(ai_errs)

        errs.sort(key=lambda e: (e.start, -(e.end - e.start)))
        dedup_errs: list[SpellError] = []
        last_e = -1
        for e in errs:
            if e.start >= last_e:
                dedup_errs.append(e)
                last_e = e.end

        fixed_txt, fixed_cnt = VietnameseSpellChecker.auto_fix_text(live_input, dedup_errs)
        fixed_txt, norm_cnt = VietnameseSpellChecker.normalize_orthography(
            fixed_txt, tone_style=tone_opt, iy_style=iy_opt
        )
        dt_ms = round((time.perf_counter() - t0) * 1000, 2)

        # Render highlighted HTML
        parts_html = []
        cur = 0
        for e in dedup_errs:
            parts_html.append(f'<span class="ctx-text">{html.escape(live_input[cur:e.start])}</span>')
            w_esc = html.escape(format_visible_token(live_input[e.start:e.end]))
            s_esc = html.escape(format_visible_token(e.suggestion)) if e.suggestion else ""
            s_badge = f'<span class="sug-inline">➜ {s_esc}</span>' if s_esc else ""
            parts_html.append(f'<span class="err-inline" title="{html.escape(e.description)}">{w_esc}</span>{s_badge}')
            cur = e.end
        parts_html.append(f'<span class="ctx-text">{html.escape(live_input[cur:])}</span>')
        hl_html = "".join(parts_html).replace("\n", "<br/>")

        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown(f"**🔴 Bản Đánh Dấu Lỗi Trực Quan ({len(dedup_errs)} lỗi • {dt_ms} ms)**")
            st.markdown(f'<div class="context-box"><div class="ctx-quote">{hl_html}</div></div>', unsafe_allow_html=True)
        with c_right:
            st.markdown(f"**🟢 Bản Đã Tự Động Sửa Sạch ({fixed_cnt + norm_cnt} vị trí đã chuẩn hóa)**")
            st.code(fixed_txt, language=None)


# ══════════════════════════════════════════════
# TAB 3: TRA CỨU CHÍNH TẢ TRỰC TUYẾN & THẨM ĐỊNH AI
# ══════════════════════════════════════════════
with tab_online:
    col_dict, col_ai = st.columns(2)

    with col_dict:
        st.markdown("#### 📖 Tra cứu Từ điển Chính tả Trực tuyến (Wiktionary + Wikipedia)")
        lookup_q = st.text_input(
            "Nhập từ hoặc cụm từ dễ nhầm lẫn cần tra cứu:",
            value="chỉnh chu",
            help="Ví dụ: chỉn chu, súc tích, xán lạn, tham quan, vô hình trung, yếu điểm...",
        )
        if st.button("🌐 Tra cứu Chính tả & Giải nghĩa"):
            res_lookup = online_engine.lookup_word(lookup_q)
            if res_lookup.is_valid_offline:
                st.success(f"✅ **«{res_lookup.query}»** là từ viết ĐÚNG chính tả chuẩn tiếng Việt.")
            else:
                st.error(
                    f"❌ **«{res_lookup.query}»** chưa chuẩn chính tả."
                    + (f" Cách viết đúng: **«{res_lookup.recommended_form}»**" if res_lookup.recommended_form else "")
                )
            if res_lookup.explanation:
                st.info(f"💡 **Giải thích:** {res_lookup.explanation}")
            if res_lookup.iy_variant:
                st.caption(f"🔄 {res_lookup.iy_variant}")
            if res_lookup.wiktionary_extract:
                st.markdown("**🌐 Trích dẫn Wiktionary Tiếng Việt:**")
                st.code(res_lookup.wiktionary_extract, language=None)
            elif res_lookup.wikipedia_summary:
                st.markdown("**🌐 Tóm tắt Wikipedia Tiếng Việt:**")
                st.write(res_lookup.wikipedia_summary)

    with col_ai:
        st.markdown("#### 🤖 Thẩm định Chuyên môn Giáo án theo Công văn 5512 (AI)")
        pedagogy_input = st.text_area(
            "Dán nội dung Kế hoạch bài dạy để AI thẩm định cấu trúc & mục tiêu:",
            value=(
                "I. MỤC TIÊU\n"
                "1. Kiến thức: HS nêu được nội dung và nghệ thuật của đoạn trích Tức nước vỡ bờ.\n"
                "2. Năng lực: Phát triển năng lực tự học, giao tiếp và hợp tác.\n"
                "3. Phẩm chất: Nhân ái, đồng cảm với người lao động.\n"
                "II. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU: SGK, máy chiếu, phiếu học tập.\n"
                "III. TIẾN TRÌNH DẠY HỌC\n"
                "Hoạt động 1: Mở đầu\nHoạt động 2: Hình thành kiến thức\nHoạt động 3: Luyện tập\nHoạt động 4: Vận dụng"
            ),
            height=155,
        )
        if st.button("✨ Phân tích Sư phạm CV 5512"):
            with st.spinner("Đang phân tích cấu trúc sư phạm theo Công văn 5512..."):
                rev = online_engine.review_pedagogy_cv5512(
                    pedagogy_input, provider=ai_provider, api_key=ai_api_key
                )
            st.metric("Điểm Cấu trúc Sư phạm CV 5512", f"{rev.get('score', 85)}/100", rev.get("mode", ""))
            st.write(f"**📌 Tổng quan:** {rev.get('summary', '')}")
            st.write(f"**🎯 Đánh giá Mục tiêu (I):** {rev.get('objectives_review', '')}")
            st.write(f"**🔄 Đánh giá Tiến trình (III):** {rev.get('activities_review', '')}")
            st.markdown("**💡 Khuyến nghị cải thiện:**")
            for r_item in rev.get("recommendations", []):
                st.markdown(f"- {r_item}")


# ══════════════════════════════════════════════
# TAB 4: TỪ ĐIỂN CÁ NHÂN & CẨM NANG 200+ CẶP TỪ
# ══════════════════════════════════════════════
with tab_dict:
    st.markdown("#### 🛡️ Quản lý Từ điển Cá nhân (Custom Whitelist)")
    st.caption("Các từ được thêm vào đây sẽ được lưu trữ bền vững và không bao giờ bị báo lỗi chính tả nhầm.")

    c_add1, c_add2 = st.columns([3, 1])
    with c_add1:
        new_words_str = st.text_input("Nhập từ mới (cách nhau bởi dấu phẩy):", placeholder="Ví dụ: Pác Bó, Côn Sơn, GeoGebra")
    with c_add2:
        st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
        if st.button("➕ Thêm vào Từ điển", width="stretch") and new_words_str.strip():
            items = [w.strip() for w in new_words_str.split(",") if w.strip()]
            add_custom_words(items)
            spell_engine.reload_custom_whitelist()
            st.success(f"Đã thêm {len(items)} từ vào Từ điển Cá nhân!")

    custom_list = sorted(load_custom_whitelist())
    if custom_list:
        st.write("**Danh sách từ cá nhân hiện tại:**", ", ".join(f"`{w}`" for w in custom_list))
        del_word = st.selectbox("Chọn từ muốn xóa:", options=[""] + custom_list)
        if del_word and st.button("🗑️ Xóa từ đã chọn"):
            remove_custom_word(del_word)
            spell_engine.reload_custom_whitelist()
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📚 Cẩm nang 200+ Cặp từ hay nhầm lẫn trong Giáo án")
    search_conf = st.text_input("🔍 Tìm kiếm cặp từ:", placeholder="Nhập từ cần tra (vd: xử lý, năng suất, dành, kĩ năng)...")
    conf_rows = [
        {"Cách viết SAI": k, "Cách viết ĐÚNG": v[0], "Giải thích quy tắc": v[1]}
        for k, v in CONFUSABLE_DETAILS.items()
        if k != v[0] and v[0] and (not search_conf or search_conf.lower() in (k + v[0] + v[1]).lower())
    ]
    st.dataframe(conf_rows, width="stretch", hide_index=True)
