"""
online_checker.py – Giải pháp kiểm tra độ chính xác cao trực tuyến (Online High-Precision Suite).

Tích hợp 4 tầng giải pháp trực tuyến & ngữ cảnh:
  1. Wiktionary & Wikipedia Tiếng Việt API (Batch Query):
     - Xác thực từ hiếm, từ Hán-Việt cổ, địa danh, nhân vật lịch sử để triệt tiêu bắt nhầm (Zero False Positives).
     - Tra cứu từ điển chính tả & giải nghĩa trực tuyến theo thời gian thực.
  2. LanguageTool Public Cloud API (https://api.languagetool.org/v2/check):
     - Kiểm tra ngữ pháp, quy chuẩn typography quốc tế và đoạn văn bản song ngữ Anh - Việt (không cần API key).
  3. Cloud AI Deep Contextual Proofreader (Google Gemini / OpenAI / Groq / Free Cloud Endpoint):
     - Phát hiện lỗi chính tả ngữ cảnh (từ đồng âm/gần âm đúng âm tiết nhưng sai nghĩa trong câu).
     - Thẩm định sư phạm Kế hoạch bài dạy theo chuẩn Công văn 5512/BGDĐT-GDTrH.
  4. Hybrid Offline-Online Fallback:
     - Hoạt động mượt mà, tự động fallback an toàn khi mất kết nối mạng.
"""

from __future__ import annotations

import html
import json
import os
import re
import urllib.parse
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

import requests

from .constants import CONFUSABLE_DETAILS, COMMON_TYPOS, IY_STANDARD_MAP, ErrorType
from .spell_checker import SpellError, VietnameseSpellChecker, _is_vietnamese_word

USER_AGENT = "VNLessonSpellChecker/2.0 (Educational Software for Teachers; contact: education@vn)"


@dataclass
class WordLookupResult:
    """Kết quả tra cứu chi tiết một từ hoặc cụm từ."""
    query: str
    is_valid_offline: bool
    is_verified_online: bool = False
    recommended_form: str = ""
    explanation: str = ""
    wiktionary_extract: str = ""
    wikipedia_summary: str = ""
    iy_variant: str = ""
    related_confusables: list[tuple[str, str, str]] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    online_source_url: str = ""


class OnlineHighPrecisionChecker:
    """Bộ kiểm tra độ chính xác cao kết hợp Wiktionary, LanguageTool và Cloud AI."""

    def __init__(self, spell_checker: Optional[VietnameseSpellChecker] = None):
        self.spell_checker = spell_checker or VietnameseSpellChecker()
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})

    # ──────────────────────────────────────────────
    # 1. Wiktionary & Wikipedia Tiếng Việt Batch Verifier
    # ──────────────────────────────────────────────

    @lru_cache(maxsize=4096)
    def _check_single_word_mediawiki(self, word: str, timeout: float = 2.5) -> bool:
        """Kiểm tra một từ có mục từ trên Wiktionary hoặc Wikipedia Tiếng Việt không."""
        res = self.verify_words_batch((word,), timeout=timeout)
        return res.get(word.lower(), False)

    def verify_words_batch(self, words: tuple[str, ...] | list[str],
                           timeout: float = 3.0) -> dict[str, bool]:
        """Kiểm tra hàng loạt từ (tối đa 50 từ/lượt) trên Wiktionary & Wikipedia Tiếng Việt."""
        unique_words = list({w.strip() for w in words if w and w.strip()})
        if not unique_words:
            return {}

        verified: dict[str, bool] = {w.lower(): False for w in unique_words}

        # Gửi truy vấn batch tới vi.wiktionary.org và vi.wikipedia.org
        endpoints = [
            "https://vi.wiktionary.org/w/api.php",
            "https://vi.wikipedia.org/w/api.php",
        ]

        # Chia batch mỗi 40 từ
        for i in range(0, len(unique_words), 40):
            batch = unique_words[i:i + 40]
            # Thử cả dạng chữ thường và viết hoa chữ đầu
            titles_to_check = set()
            for w in batch:
                titles_to_check.add(w.lower())
                titles_to_check.add(w.capitalize())

            titles_param = "|".join(list(titles_to_check)[:50])

            for api_url in endpoints:
                try:
                    resp = self._session.get(
                        api_url,
                        params={
                            "action": "query",
                            "titles": titles_param,
                            "format": "json",
                            "redirects": 1,
                        },
                        timeout=timeout,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        pages = data.get("query", {}).get("pages", {})
                        for page_id, page_info in pages.items():
                            if str(page_id) != "-1" and "missing" not in page_info:
                                title = page_info.get("title", "").lower()
                                if title in verified:
                                    verified[title] = True
                except Exception:
                    continue

        return verified

    def filter_false_positives_online(self, errors: list[SpellError],
                                      timeout: float = 3.0) -> tuple[list[SpellError], list[str]]:
        """Lọc bỏ các từ bị báo lỗi 'không có trong từ điển' nhưng thực chất là thuật ngữ/tên riêng
        hợp lệ trên Wiktionary/Wikipedia Tiếng Việt.

        Returns:
            (danh_sách_lỗi_đã_lọc, danh_sách_từ_được_xác_thực_online)
        """
        unknown_candidates = [
            e.wrong_text for e in errors
            if e.error_type == ErrorType.SPELLING
            and "không có trong từ điển" in e.description
            and e.wrong_text.lower() not in COMMON_TYPOS
        ]
        if not unknown_candidates:
            return errors, []

        verified_map = self.verify_words_batch(unknown_candidates, timeout=timeout)
        verified_words = [w for w, ok in verified_map.items() if ok]
        if not verified_words:
            return errors, []

        filtered_errors = [
            e for e in errors
            if not (
                e.error_type == ErrorType.SPELLING
                and "không có trong từ điển" in e.description
                and verified_map.get(e.wrong_text.lower(), False)
            )
        ]
        return filtered_errors, verified_words

    # ──────────────────────────────────────────────
    # 2. Tra cứu Từ điển Chính tả Trực tuyến (Live Dictionary)
    # ──────────────────────────────────────────────

    def lookup_word(self, query: str, timeout: float = 3.5) -> WordLookupResult:
        """Tra cứu toàn diện một từ hoặc cụm từ (Offline + Cặp từ dễ nhầm + Wiktionary + Wikipedia)."""
        q_clean = query.strip()
        q_lower = q_clean.lower()

        # 1. Kiểm tra tính hợp lệ của từng âm tiết trong cụm từ
        tokens = re.findall(r'[A-Za-zÀ-ỹĂăÂâĐđÊêÔôƠơƯư]+', q_lower)
        is_valid_offline = bool(tokens) and all(_is_vietnamese_word(t) for t in tokens)
        if q_lower in COMMON_TYPOS:
            is_valid_offline = False

        res = WordLookupResult(
            query=q_clean,
            is_valid_offline=is_valid_offline,
            recommended_form=q_clean if is_valid_offline else "",
        )

        # 2. Kiểm tra trong từ điển cặp từ dễ nhầm (CONFUSABLE_DETAILS)
        if q_lower in CONFUSABLE_DETAILS:
            correct_form, expl = CONFUSABLE_DETAILS[q_lower]
            res.recommended_form = correct_form
            res.explanation = expl or f"Cách viết chuẩn là «{correct_form}»."
            if q_lower != correct_form:
                res.is_valid_offline = False

        # Tìm các cặp từ liên quan chứa từ khóa
        for wrong_k, (right_v, expl) in CONFUSABLE_DETAILS.items():
            if q_lower in wrong_k or q_lower in right_v:
                if wrong_k != right_v:
                    res.related_confusables.append((wrong_k, right_v, expl))
        res.related_confusables = res.related_confusables[:8]

        # 3. Kiểm tra biến thể i / y
        if q_lower in IY_STANDARD_MAP:
            res.iy_variant = f"Biến thể chữ i/y: «{q_lower}» (thông dụng) ↔ «{IY_STANDARD_MAP[q_lower]}» (chuẩn SGK Bộ GD&ĐT)."
        else:
            rev_iy = {v: k for k, v in IY_STANDARD_MAP.items()}
            if q_lower in rev_iy:
                res.iy_variant = f"Biến thể chữ i/y: «{q_lower}» (chuẩn SGK Bộ GD&ĐT) ↔ «{rev_iy[q_lower]}» (thông dụng)."

        # 4. Sinh gợi ý nếu từ sai
        if not res.is_valid_offline and len(tokens) == 1:
            sug = self.spell_checker._suggest(tokens[0])
            if sug:
                res.suggestions.append(sug)
                if not res.recommended_form:
                    res.recommended_form = sug

        # 5. Tra cứu trực tuyến trên Wiktionary Tiếng Việt
        target_lookup = res.recommended_form or q_clean
        try:
            resp = self._session.get(
                "https://vi.wiktionary.org/w/api.php",
                params={
                    "action": "query",
                    "prop": "extracts",
                    "explaintext": 1,
                    "titles": target_lookup.lower(),
                    "format": "json",
                    "redirects": 1,
                },
                timeout=timeout,
            )
            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                for page_id, page_info in pages.items():
                    if str(page_id) != "-1" and page_info.get("extract"):
                        extract_text = page_info["extract"].strip()
                        # Lấy tối đa 600 ký tự đầu tiên cho gọn đẹp
                        res.wiktionary_extract = extract_text[:700] + ("..." if len(extract_text) > 700 else "")
                        res.is_verified_online = True
                        res.online_source_url = f"https://vi.wiktionary.org/wiki/{urllib.parse.quote(target_lookup.lower())}"
                        break
        except Exception:
            pass

        # 6. Tra cứu bổ sung trên Wikipedia Tiếng Việt nếu chưa có trên Wiktionary
        if not res.wiktionary_extract:
            try:
                wiki_url = f"https://vi.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(target_lookup)}"
                resp = self._session.get(wiki_url, timeout=timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("extract"):
                        res.wikipedia_summary = data["extract"][:600]
                        res.is_verified_online = True
                        res.online_source_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
            except Exception:
                pass

        return res

    # ──────────────────────────────────────────────
    # 3. LanguageTool Public Cloud API
    # ──────────────────────────────────────────────

    def check_with_languagetool(self, text: str,
                                language: str = "auto",
                                timeout: float = 5.0) -> list[SpellError]:
        """Kiểm tra văn bản qua LanguageTool Cloud API (https://api.languagetool.org/v2/check).
        Hữu ích cho các đoạn tiếng Anh trong giáo án song ngữ / tiếng Anh và lỗi khoảng trắng/dấu câu nâng cao.
        """
        if not text or not text.strip():
            return []

        errors: list[SpellError] = []
        try:
            resp = self._session.post(
                "https://api.languagetool.org/v2/check",
                data={
                    "text": text[:8000],
                    "language": language,
                },
                timeout=timeout,
            )
            if resp.status_code != 200:
                return []

            data = resp.json()
            for match in data.get("matches", []):
                offset = match.get("offset", 0)
                length = match.get("length", 0)
                if length <= 0 or offset + length > len(text):
                    continue

                wrong_str = text[offset:offset + length]
                replacements = match.get("replacements", [])
                suggestion = replacements[0].get("value", "") if replacements else ""
                message = match.get("message", "Lỗi ngữ pháp / chính tả phát hiện qua LanguageTool")
                rule_id = match.get("rule", {}).get("id", "")

                # Bỏ qua nếu rule_id chỉ là báo lỗi từ tiếng Việt khi language auto nhận nhầm sang tiếng Anh
                if "MORFOLOGIK_RULE" in rule_id or "HUNSPELL" in rule_id:
                    tokens = re.findall(r'[A-Za-zÀ-ỹĂăÂâĐđÊêÔôƠơƯư]+', wrong_str.lower())
                    if tokens and all(_is_vietnamese_word(t) for t in tokens):
                        continue

                errors.append(SpellError(
                    start=offset,
                    end=offset + length,
                    wrong_text=wrong_str,
                    suggestion=suggestion,
                    error_type=ErrorType.CONTEXT_ONLINE,
                    description=f"[LanguageTool Online] {message}",
                    confidence=0.88,
                    source="languagetool",
                ))
        except Exception:
            pass

        return errors

    # ──────────────────────────────────────────────
    # 4. Cloud AI Deep Contextual Proofreader & CV 5512 Reviewer
    # ──────────────────────────────────────────────

    def _call_llm_json(self, system_prompt: str, user_prompt: str,
                       provider: str = "free_cloud",
                       api_key: str = "",
                       model: str = "",
                       timeout: float = 18.0) -> Optional[str]:
        """Gọi Cloud LLM (Gemini / OpenAI / Groq / Pollinations Free Cloud) và trả về chuỗi phản hồi."""
        provider_norm = provider.lower().strip()

        # 1. Google Gemini API
        if "gemini" in provider_norm:
            key = api_key.strip() or os.environ.get("GEMINI_API_KEY", "")
            if not key:
                raise ValueError("Vui lòng nhập Google Gemini API Key (miễn phí tại aistudio.google.com) hoặc chuyển sang chế độ Free Cloud AI.")
            model_name = model.strip() or "gemini-2.0-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json",
                },
            }
            resp = self._session.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return None

        # 2. OpenAI / Groq / DeepSeek / OpenRouter
        if provider_norm in ("openai", "groq", "deepseek", "openrouter"):
            key = api_key.strip() or os.environ.get("OPENAI_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")
            if not key:
                raise ValueError(f"Vui lòng nhập API Key cho {provider} hoặc chuyển sang chế độ Free Cloud AI.")

            if provider_norm == "groq":
                base_url = "https://api.groq.com/openai/v1/chat/completions"
                default_model = "llama-3.3-70b-versatile"
            elif provider_norm == "deepseek":
                base_url = "https://api.deepseek.com/v1/chat/completions"
                default_model = "deepseek-chat"
            elif provider_norm == "openrouter":
                base_url = "https://openrouter.ai/api/v1/chat/completions"
                default_model = "google/gemini-2.0-flash-001"
            else:
                base_url = "https://api.openai.com/v1/chat/completions"
                default_model = "gpt-4o-mini"

            model_name = model.strip() or default_model
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
            }
            resp = self._session.post(base_url, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

        # 3. Free Cloud AI (Pollinations OpenAI-compatible endpoint - không cần API Key)
        url = "https://text.pollinations.ai/openai"
        payload = {
            "model": model.strip() or "openai",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "jsonMode": True,
        }
        resp = self._session.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "choices" in data:
            return data["choices"][0]["message"]["content"]
        return resp.text

    @staticmethod
    def _extract_json_from_text(raw: str) -> Optional[dict | list]:
        """Trích xuất JSON an toàn từ chuỗi phản hồi của LLM."""
        if not raw:
            return None
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except Exception:
            match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
        return None

    def check_contextual_ai(self, text: str,
                            provider: str = "free_cloud",
                            api_key: str = "",
                            model: str = "",
                            timeout: float = 18.0) -> tuple[list[SpellError], Optional[str]]:
        """Dùng AI kiểm tra chính tả ngữ cảnh tiếng Việt (từ đồng âm khác nghĩa, dùng sai từ Hán-Việt, lỗi ngữ pháp).

        Returns:
            (danh_sách_SpellError, thông_báo_lỗi_nếu_có)
        """
        if not text or not text.strip():
            return [], None

        system_prompt = (
            "Bạn là chuyên gia hiệu đính ngôn ngữ tiếng Việt và thẩm định giáo án theo chuẩn Bộ GD&ĐT. "
            "Nhiệm vụ: Phát hiện các lỗi chính tả tiếng Việt, đặc biệt là LỖI CHÍNH TẢ NGỮ CẢNH "
            "(các từ có âm tiết hợp lệ nhưng viết sai trong ngữ cảnh câu, ví dụ: 'bàng quan' vs 'bàng hoàng', "
            "'yếu điểm' vs 'điểm yếu', 'chín muồi' vs 'chín mùi', 'tham quan' vs 'thăm quan', "
            "'súc tích' vs 'xúc tích', 'chỉn chu' vs 'chỉnh chu', 'giả thiết' vs 'giả thuyết', "
            "'dành' vs 'giành', sai dấu hỏi/ngã, sai s/x, ch/tr, l/n, hoặc câu lủng củng). "
            "Trả về ĐÚNG định dạng JSON: "
            '{"errors": [{"wrong_text": "chuỗi sai nguyên văn trong bài", "suggestion": "từ sửa đúng", "description": "giải thích ngắn gọn lý do sai"}]}'
        )
        user_prompt = f"Hãy kiểm tra đoạn văn bản giáo án sau và chỉ liệt kê các lỗi thực sự:\n\n{text[:4500]}"

        try:
            raw_resp = self._call_llm_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                provider=provider,
                api_key=api_key,
                model=model,
                timeout=timeout,
            )
            parsed = self._extract_json_from_text(raw_resp or "")
            if not parsed:
                return [], None

            items = parsed.get("errors", []) if isinstance(parsed, dict) else (parsed if isinstance(parsed, list) else [])
            found_errors: list[SpellError] = []
            search_from = 0

            for item in items:
                if not isinstance(item, dict):
                    continue
                wrong_str = str(item.get("wrong_text", "")).strip()
                suggestion = str(item.get("suggestion", "")).strip()
                desc = str(item.get("description", "Phát hiện bởi AI Ngữ cảnh")).strip()

                if not wrong_str or wrong_str == suggestion:
                    continue

                pos = text.find(wrong_str, search_from)
                if pos == -1:
                    pos = text.find(wrong_str)
                if pos != -1:
                    found_errors.append(SpellError(
                        start=pos,
                        end=pos + len(wrong_str),
                        wrong_text=wrong_str,
                        suggestion=suggestion,
                        error_type=ErrorType.CONTEXT_ONLINE,
                        description=f"[AI Ngữ cảnh] {desc}",
                        confidence=0.95,
                        source="ai",
                    ))
                    search_from = pos + len(wrong_str)

            return found_errors, None

        except Exception as e:
            return [], str(e)

    def review_pedagogy_cv5512(self, text: str,
                               provider: str = "free_cloud",
                               api_key: str = "",
                               model: str = "",
                               timeout: float = 22.0) -> dict:
        """Phân tích & góp ý chuyên môn sư phạm cho Kế hoạch bài dạy theo Công văn 5512/BGDĐT-GDTrH."""
        system_prompt = (
            "Bạn là Chuyên gia Thẩm định Kế hoạch bài dạy (Giáo án) theo Công văn 5512/BGDĐT-GDTrH của Bộ Giáo dục và Đào tạo Việt Nam. "
            "Hãy đánh giá văn bản giáo án được cung cấp và trả về JSON có cấu trúc: "
            '{"score": 85, "summary": "Nhận xét tổng quan ngắn gọn", '
            '"objectives_review": "Đánh giá mục I. Mục tiêu (Kiến thức, Năng lực chung, Năng lực đặc thù, Phẩm chất - có viết theo động từ đo lường được không)", '
            '"activities_review": "Đánh giá mục III. Tiến trình dạy học (4 hoạt động: Mở đầu, Hình thành kiến thức, Luyện tập, Vận dụng và 4 bước a,b,c,d)", '
            '"style_and_language": "Nhận xét về văn phong sư phạm, tính rõ ràng, chính xác thuật ngữ", '
            '"recommendations": ["Gợi ý cải thiện 1", "Gợi ý cải thiện 2", "Gợi ý cải thiện 3"]}'
        )
        user_prompt = f"Nội dung Kế hoạch bài dạy cần thẩm định:\n\n{text[:6000]}"

        try:
            raw_resp = self._call_llm_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                provider=provider,
                api_key=api_key,
                model=model,
                timeout=timeout,
            )
            parsed = self._extract_json_from_text(raw_resp or "")
            if isinstance(parsed, dict) and ("summary" in parsed or "recommendations" in parsed):
                return {
                    "success": True,
                    "mode": f"Cloud AI ({provider})",
                    "score": parsed.get("score", 85),
                    "summary": parsed.get("summary", ""),
                    "objectives_review": parsed.get("objectives_review", ""),
                    "activities_review": parsed.get("activities_review", ""),
                    "style_and_language": parsed.get("style_and_language", ""),
                    "recommendations": parsed.get("recommendations", []),
                }
        except Exception as e:
            err_msg = str(e)
            # Fallback phân tích sư phạm thông minh tại chỗ nếu mạng/API bị gián đoạn
            fallback = self._local_pedagogy_analysis(text)
            fallback["note"] = f"Đã sử dụng bộ phân tích cấu trúc sư phạm CV 5512 nội bộ (Lý do không gọi Cloud AI: {err_msg})"
            return fallback

        return self._local_pedagogy_analysis(text)

    @staticmethod
    def _local_pedagogy_analysis(text: str) -> dict:
        """Bộ phân tích chuyên môn CV 5512 dự phòng (hoạt động tức thì ngay cả khi không có mạng)."""
        has_muc_tieu = bool(re.search(r"MỤC\s+TIÊU", text, re.IGNORECASE))
        has_nang_luc = bool(re.search(r"Năng\s+lực", text, re.IGNORECASE))
        has_pham_chat = bool(re.search(r"Phẩm\s+chất", text, re.IGNORECASE))
        has_thiet_bi = bool(re.search(r"THIẾT\s+BỊ|HỌC\s+LIỆU", text, re.IGNORECASE))
        has_tien_trinh = bool(re.search(r"TIẾN\s+TRÌNH", text, re.IGNORECASE))
        has_4_steps = sum(
            1 for p in [r"Mục\s+tiêu", r"Nội\s+dung", r"Sản\s+phẩm", r"Tổ\s+chức\s+thực\s+hiện"]
            if re.search(p, text, re.IGNORECASE)
        )
        measurable_verbs = re.findall(
            r"\b(nêu\s+được|trình\s+bày\s+được|phân\s+tích\s+được|vận\s+dụng\s+được|giải\s+thích\s+được|xác\s+định\s+được|so\s+sánh\s+được|thực\s+hiện\s+được)\b",
            text,
            re.IGNORECASE,
        )

        score = 60
        if has_muc_tieu and has_nang_luc and has_pham_chat:
            score += 15
        if has_thiet_bi and has_tien_trinh:
            score += 10
        if has_4_steps >= 3:
            score += 10
        if len(measurable_verbs) >= 2:
            score += 5

        recs = []
        if len(measurable_verbs) < 2:
            recs.append(
                "Trong phần I. Mục tiêu, theo CV 5512 nên sử dụng các động từ hành vi đo lường được mức độ cần đạt của HS (ví dụ: 'Nêu được...', 'Trình bày được...', 'Phân tích được...', 'Vận dụng được...') thay vì 'Nắm được' hay 'Hiểu được'."
            )
        if has_4_steps < 4:
            recs.append(
                "Mỗi hoạt động học trong phần III. Tiến trình dạy học nên thể hiện rõ đủ 4 mục thành phần: a) Mục tiêu, b) Nội dung, c) Sản phẩm, d) Tổ chức thực hiện."
            )
        recs.append(
            "Ở bước d) Tổ chức thực hiện, nên làm rõ 4 bước chuyển giao: (1) Chuyển giao nhiệm vụ -> (2) Thực hiện nhiệm vụ -> (3) Báo cáo, thảo luận -> (4) Kết luận, nhận định."
        )

        return {
            "success": True,
            "mode": "Engine Phân tích Sư phạm CV 5512",
            "score": min(100, score),
            "summary": "Giáo án đáp ứng khung cấu trúc cơ bản của Công văn 5512/BGDĐT-GDTrH.",
            "objectives_review": (
                f"Đã phát hiện {len(measurable_verbs)} cụm động từ chỉ mức độ cần đạt. "
                + ("Đầy đủ 3 thành tố Kiến thức - Năng lực - Phẩm chất." if (has_nang_luc and has_pham_chat) else "Cần bổ sung đủ các mục Năng lực chung, Năng lực đặc thù và Phẩm chất.")
            ),
            "activities_review": (
                f"Phát hiện {has_4_steps}/4 thành phần chuẩn (Mục tiêu, Nội dung, Sản phẩm, Tổ chức thực hiện) trong các hoạt động."
            ),
            "style_and_language": "Ngôn ngữ hành chính - sư phạm rõ ràng. Khuyến nghị rà soát đồng nhất cách viết tắt GV, HS và chuẩn hóa dấu câu.",
            "recommendations": recs,
        }
