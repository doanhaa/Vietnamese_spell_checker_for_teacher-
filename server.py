#!/usr/bin/env python3
"""
server.py – Máy chủ Web Tốc Độ Cao (Multi-threaded SPA Server) cho Phần mềm Kiểm tra Giáo án v2.0.

Chạy độc lập cực nhanh:
    python3 server.py [--port 8501]
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

WEB_DIR = Path(__file__).parent / "web"

# Singleton instances giữ trên RAM để phản hồi tức thì (< 5ms cho văn bản, ~30ms cho file .docx)
_GLOBAL_SPELL_CHECKER = VietnameseSpellChecker(check_context=True)
_GLOBAL_ONLINE_CHECKER = OnlineHighPrecisionChecker(_GLOBAL_SPELL_CHECKER)


def _render_highlighted_text_html(text: str, errors: list[SpellError]) -> str:
    """Chuyển đoạn văn bản và danh sách lỗi thành chuỗi HTML có highlight trực quan."""
    if not errors:
        return html.escape(text)

    parts: list[str] = []
    cursor = 0
    for err in sorted(errors, key=lambda e: e.start):
        if err.start < cursor:
            continue
        parts.append(f'<span class="ctx-text">{html.escape(text[cursor:err.start])}</span>')
        wrong_esc = html.escape(format_visible_token(text[err.start:err.end]))
        sug_esc = html.escape(format_visible_token(err.suggestion)) if err.suggestion else ""
        sug_span = f'<span class="sug-inline">➜ {sug_esc}</span>' if sug_esc else ""
        parts.append(
            f'<span class="err-inline" title="{html.escape(err.description)}">{wrong_esc}</span>{sug_span}'
        )
        cursor = err.end
    parts.append(f'<span class="ctx-text">{html.escape(text[cursor:])}</span>')
    return "".join(parts)


def _serialize_docx_result(filename: str, res: dict) -> dict:
    """Đóng gói kết quả xử lý .docx thành JSON trả về cho Web UI."""
    stats: ProcessingStats = res["stats"]
    stem = Path(filename).stem

    format_errors = []
    section_checklist = []
    if stats.format_report:
        format_errors = [fe.to_dict() for fe in stats.format_report.errors]
        section_checklist = stats.format_report.section_checklist

    return {
        "success": True,
        "filename": filename,
        "marked_filename": f"{stem}_DaKiemTra.docx",
        "fixed_filename": f"{stem}_DaSuaLoi.docx",
        "marked_b64": base64.b64encode(res["marked_bytes"]).decode("ascii"),
        "fixed_b64": base64.b64encode(res["fixed_bytes"]).decode("ascii"),
        "stats": {
            "total_errors": stats.total_errors,
            "total_spelling_errors": stats.total_spelling_errors + stats.total_context_errors,
            "total_punctuation_errors": stats.total_punctuation_errors,
            "total_format_errors": stats.total_format_errors,
            "total_structure_errors": stats.total_structure_errors,
            "paragraphs_checked": stats.paragraphs_checked,
            "tables_checked": stats.tables_checked,
            "total_words": stats.total_words,
            "auto_fixed_count": stats.auto_fixed_count,
            "processing_time_ms": stats.processing_time_ms,
            "quality_score": stats.quality_score,
            "quality_grade": stats.quality_grade,
            "verified_online_words": stats.verified_online_words,
            "error_details": [ed.to_dict() for ed in stats.error_details],
            "format_errors": format_errors,
            "section_checklist": section_checklist,
        },
    }


class LessonCheckerRequestHandler(BaseHTTPRequestHandler):
    """Xử lý HTTP Request cho giao diện Web SPA và REST API."""

    def log_message(self, format: str, *args):
        # Giữ log gọn gàng
        pass

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            index_file = WEB_DIR / "index.html"
            data = index_file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if self.path == "/api/custom-whitelist":
            custom_words = sorted(load_custom_whitelist())
            confusables = [
                {"wrong": k, "right": v[0], "explanation": v[1]}
                for k, v in CONFUSABLE_DETAILS.items()
                if k != v[0] and v[0]
            ]
            self._send_json({
                "custom_words": custom_words,
                "confusables": confusables,
            })
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        try:
            body = self._read_json_body()
        except Exception as e:
            self._send_json({"success": False, "error": f"Invalid JSON: {e}"}, status=400)
            return

        if self.path == "/api/check-docx":
            filename = body.get("filename", "Giao_an.docx")
            content_b64 = body.get("content_b64", "")
            cfg = body.get("config", {})
            try:
                docx_bytes = base64.b64decode(content_b64)
                processor = DocxProcessor(
                    show_suggestion=cfg.get("show_suggestion", True),
                    check_spelling=cfg.get("check_spelling", True),
                    check_format=cfg.get("check_format", True),
                    check_context=cfg.get("check_context", True),
                    online_verify_wiktionary=cfg.get("online_verify_wiktionary", False),
                    online_languagetool=cfg.get("online_languagetool", False),
                    online_ai_check=cfg.get("online_ai_check", False),
                    ai_provider=cfg.get("ai_provider", "free_cloud"),
                    ai_api_key=cfg.get("ai_api_key", ""),
                    normalize_tone=cfg.get("normalize_tone", "keep"),
                    normalize_iy=cfg.get("normalize_iy", "keep"),
                )
                res = processor.process_bytes(docx_bytes, generate_auto_fixed=True, auto_fix_format=True)
                self._send_json(_serialize_docx_result(filename, res))
            except Exception as e:
                self._send_json({"success": False, "filename": filename, "error": str(e)}, status=500)
            return

        if self.path == "/api/sample-docx":
            cfg = body.get("config", {})
            try:
                sample_bytes = build_sample_giao_an_bytes()
                processor = DocxProcessor(
                    show_suggestion=cfg.get("show_suggestion", True),
                    check_spelling=cfg.get("check_spelling", True),
                    check_format=cfg.get("check_format", True),
                    check_context=cfg.get("check_context", True),
                    online_verify_wiktionary=cfg.get("online_verify_wiktionary", False),
                    online_languagetool=cfg.get("online_languagetool", False),
                    online_ai_check=cfg.get("online_ai_check", False),
                    ai_provider=cfg.get("ai_provider", "free_cloud"),
                    ai_api_key=cfg.get("ai_api_key", ""),
                    normalize_tone=cfg.get("normalize_tone", "keep"),
                    normalize_iy=cfg.get("normalize_iy", "keep"),
                )
                res = processor.process_bytes(sample_bytes, generate_auto_fixed=True, auto_fix_format=True)
                self._send_json(_serialize_docx_result("Giao_an_Mau_Ngu_Van_8.docx", res))
            except Exception as e:
                self._send_json({"success": False, "filename": "Giao_an_Mau.docx", "error": str(e)}, status=500)
            return

        if self.path == "/api/check-text":
            text = body.get("text", "")
            cfg = body.get("config", {})
            t0 = time.perf_counter()

            _GLOBAL_SPELL_CHECKER.reload_custom_whitelist()
            _GLOBAL_SPELL_CHECKER.check_context = cfg.get("check_context", True)
            errors = _GLOBAL_SPELL_CHECKER.check_text(text)

            if cfg.get("online_verify_wiktionary", False) and errors:
                errors, _ = _GLOBAL_ONLINE_CHECKER.filter_false_positives_online(errors)

            if cfg.get("online_languagetool", False):
                lt_errs = _GLOBAL_ONLINE_CHECKER.check_with_languagetool(text)
                errors.extend(lt_errs)

            if cfg.get("online_ai_check", False):
                ai_errs, _ = _GLOBAL_ONLINE_CHECKER.check_contextual_ai(
                    text,
                    provider=cfg.get("ai_provider", "free_cloud"),
                    api_key=cfg.get("ai_api_key", ""),
                )
                errors.extend(ai_errs)

            # Khử chồng lấn
            errors.sort(key=lambda e: (e.start, -(e.end - e.start)))
            dedup: list[SpellError] = []
            last_end = -1
            for e in errors:
                if e.start >= last_end:
                    dedup.append(e)
                    last_end = e.end

            fixed_text, _ = VietnameseSpellChecker.auto_fix_text(text, dedup)
            fixed_text, _ = VietnameseSpellChecker.normalize_orthography(
                fixed_text,
                tone_style=cfg.get("normalize_tone", "keep"),
                iy_style=cfg.get("normalize_iy", "keep"),
            )
            highlighted_html = _render_highlighted_text_html(text, dedup)
            dt_ms = round((time.perf_counter() - t0) * 1000, 2)

            self._send_json({
                "success": True,
                "processing_time_ms": dt_ms,
                "errors": [e.to_dict() for e in dedup],
                "fixed_text": fixed_text,
                "highlighted_html": highlighted_html,
            })
            return

        if self.path == "/api/lookup-word":
            query = body.get("query", "")
            res = _GLOBAL_ONLINE_CHECKER.lookup_word(query)
            self._send_json({
                "query": res.query,
                "is_valid_offline": res.is_valid_offline,
                "is_verified_online": res.is_verified_online,
                "recommended_form": res.recommended_form,
                "explanation": res.explanation,
                "wiktionary_extract": res.wiktionary_extract,
                "wikipedia_summary": res.wikipedia_summary,
                "iy_variant": res.iy_variant,
                "related_confusables": res.related_confusables,
                "suggestions": res.suggestions,
                "online_source_url": res.online_source_url,
            })
            return

        if self.path == "/api/pedagogy-review":
            text = body.get("text", "")
            cfg = body.get("config", {})
            review = _GLOBAL_ONLINE_CHECKER.review_pedagogy_cv5512(
                text,
                provider=cfg.get("ai_provider", "free_cloud"),
                api_key=cfg.get("ai_api_key", ""),
            )
            self._send_json(review)
            return

        if self.path == "/api/custom-whitelist":
            action = body.get("action", "")
            if action == "add":
                words = body.get("words", [])
                updated = sorted(add_custom_words(words))
            elif action == "remove":
                word = body.get("word", "")
                updated = sorted(remove_custom_word(word))
            else:
                updated = sorted(load_custom_whitelist())
            _GLOBAL_SPELL_CHECKER.reload_custom_whitelist()
            self._send_json({"custom_words": updated})
            return

        self.send_error(404, "Endpoint Not Found")


def run_server(host: str = "0.0.0.0", port: int = 8501, open_browser: bool = False):
    server = ThreadingHTTPServer((host, port), LessonCheckerRequestHandler)
    url = f"http://localhost:{port}"
    print(f"\n{'='*65}")
    print(f"🚀 VN Lesson Checker Pro v2.0 – Web Server đang chạy tại:")
    print(f"👉 {url}")
    print(f"{'='*65}\n")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Đã dừng máy chủ Web.")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy Web Server Kiểm tra Giáo án Pro v2.0")
    parser.add_argument("--host", default="0.0.0.0", help="Địa chỉ host (mặc định: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8501, help="Cổng lắng nghe (mặc định: 8501)")
    parser.add_argument("--open", action="store_true", help="Tự động mở trình duyệt")
    args = parser.parse_args()
    run_server(host=args.host, port=args.port, open_browser=args.open)
