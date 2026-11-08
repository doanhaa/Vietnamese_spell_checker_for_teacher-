"""
docx_compat.py – Lớp tương thích xử lý .docx tốc độ cao.

Tự động sử dụng `python-docx` nếu đã cài đặt trong môi trường;
Nếu chưa cài đặt `python-docx`, tự động chuyển sang Engine XML thuần (`zipfile` + `lxml.etree`)
giúp phần mềm hoạt động 100% độc lập không phụ thuộc thư viện ngoài.
"""

from __future__ import annotations

import copy
import io
import zipfile
from pathlib import Path
from typing import Optional, Union

from lxml import etree

try:
    from docx import Document as _DocxDocument
    from docx.shared import Pt, Cm, Mm, Inches, Emu, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn, nsmap
    HAS_PYTHON_DOCX = True
    Document = _DocxDocument
except ImportError:
    HAS_PYTHON_DOCX = False

    WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    XML_NS = "http://www.w3.org/XML/1998/namespace"
    R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

    nsmap = {
        "w": WORD_NS,
        "xml": XML_NS,
        "r": R_NS,
    }

    def qn(tag: str) -> str:
        """Chuyển đổi tiền tố namespace kiểu 'w:p' sang '{http://...}p'."""
        if ":" in tag:
            prefix, local = tag.split(":", 1)
            uri = nsmap.get(prefix, WORD_NS)
            return f"{{{uri}}}{local}"
        return tag

    class _BaseOxmlElement(etree.ElementBase):
        """Lớp Element mở rộng có hỗ trợ các helper giống python-docx."""

        def get_or_add_pPr(self):
            pPr = self.find(qn("w:pPr"))
            if pPr is None:
                pPr = OxmlElement("w:pPr")
                self.insert(0, pPr)
            return pPr

        def get_or_add_rPr(self):
            rPr = self.find(qn("w:rPr"))
            if rPr is None:
                rPr = OxmlElement("w:rPr")
                self.insert(0, rPr)
            return rPr

    _PARSER_LOOKUP = etree.ElementDefaultClassLookup(element=_BaseOxmlElement)
    _XML_PARSER = etree.XMLParser(remove_blank_text=False)
    _XML_PARSER.set_element_class_lookup(_PARSER_LOOKUP)

    def OxmlElement(tag: str) -> _BaseOxmlElement:
        """Tạo một XML element với namespace WordprocessingML."""
        elem = _XML_PARSER.makeelement(qn(tag), nsmap={"w": WORD_NS})
        return elem

    # ─── Đơn vị đo lường (qui đổi ra EMU) ───
    class Emu(int):
        def __new__(cls, val: float | int):
            return super().__new__(cls, int(round(val)))

    def Pt(val: float) -> Emu:
        return Emu(val * 12700)

    def Cm(val: float) -> Emu:
        return Emu(val * 360000)

    def Mm(val: float) -> Emu:
        return Emu(val * 36000)

    def Inches(val: float) -> Emu:
        return Emu(val * 914400)

    class RGBColor:
        def __init__(self, r: int, g: int, b: int):
            self.r = r
            self.g = g
            self.b = b

        def __str__(self) -> str:
            return f"{self.r:02X}{self.g:02X}{self.b:02X}"

    class WD_ALIGN_PARAGRAPH:
        LEFT = "left"
        CENTER = "center"
        RIGHT = "right"
        JUSTIFY = "both"

    class WD_COLOR_INDEX:
        YELLOW = "yellow"
        RED = "red"

    # ─── Các lớp đối tượng Document / Paragraph / Run / Table / Section ───

    class _ColorFormat:
        def __init__(self, run_elem):
            self._r = run_elem

        @property
        def rgb(self) -> Optional[RGBColor]:
            rPr = self._r.find(qn("w:rPr"))
            if rPr is not None:
                c = rPr.find(qn("w:color"))
                if c is not None:
                    val = c.get(qn("w:val"), "")
                    if len(val) == 6:
                        try:
                            return RGBColor(int(val[0:2], 16), int(val[2:4], 16), int(val[4:6], 16))
                        except ValueError:
                            pass
            return None

        @rgb.setter
        def rgb(self, value: Optional[RGBColor]):
            rPr = self._r.get_or_add_rPr()
            c = rPr.find(qn("w:color"))
            if c is None:
                c = OxmlElement("w:color")
                rPr.append(c)
            if value is not None:
                c.set(qn("w:val"), str(value))

    class _Font:
        def __init__(self, run_elem):
            self._r = run_elem
            self.color = _ColorFormat(run_elem)

        @property
        def name(self) -> Optional[str]:
            rPr = self._r.find(qn("w:rPr"))
            if rPr is not None:
                rf = rPr.find(qn("w:rFonts"))
                if rf is not None:
                    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                        v = rf.get(qn(attr))
                        if v:
                            return v
            return None

        @name.setter
        def name(self, val: Optional[str]):
            rPr = self._r.get_or_add_rPr()
            rf = rPr.find(qn("w:rFonts"))
            if rf is None:
                rf = OxmlElement("w:rFonts")
                rPr.append(rf)
            if val:
                for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                    rf.set(qn(attr), val)

        @property
        def size(self) -> Optional[int]:
            rPr = self._r.find(qn("w:rPr"))
            if rPr is not None:
                sz = rPr.find(qn("w:sz"))
                if sz is not None:
                    val = sz.get(qn("w:val"))
                    if val and val.isdigit():
                        return int(val) * 6350  # half-pt -> EMU (1pt = 12700 EMU)
            return None

        @size.setter
        def size(self, emu_val: Optional[int]):
            rPr = self._r.get_or_add_rPr()
            for tag in ("w:sz", "w:szCs"):
                old = rPr.find(qn(tag))
                if old is not None:
                    rPr.remove(old)
                if emu_val is not None:
                    half_pt = int(round(int(emu_val) / 6350))
                    el = OxmlElement(tag)
                    el.set(qn("w:val"), str(half_pt))
                    rPr.append(el)

    class Run:
        def __init__(self, r_elem):
            self._r = r_elem
            self._element = r_elem
            self.font = _Font(r_elem)

        @property
        def text(self) -> str:
            parts = []
            for t in self._r.findall(qn("w:t")):
                if t.text:
                    parts.append(t.text)
            return "".join(parts)

        @text.setter
        def text(self, val: str):
            t_elems = self._r.findall(qn("w:t"))
            if t_elems:
                t_elems[0].text = val
                t_elems[0].set(qn("xml:space"), "preserve")
                for extra in t_elems[1:]:
                    self._r.remove(extra)
            else:
                t = OxmlElement("w:t")
                t.text = val
                t.set(qn("xml:space"), "preserve")
                self._r.append(t)

        @property
        def bold(self) -> bool:
            rPr = self._r.find(qn("w:rPr"))
            return rPr is not None and rPr.find(qn("w:b")) is not None

        @bold.setter
        def bold(self, val: bool):
            rPr = self._r.get_or_add_rPr()
            b = rPr.find(qn("w:b"))
            if val and b is None:
                rPr.append(OxmlElement("w:b"))
            elif not val and b is not None:
                rPr.remove(b)

        @property
        def italic(self) -> bool:
            rPr = self._r.find(qn("w:rPr"))
            return rPr is not None and rPr.find(qn("w:i")) is not None

        @italic.setter
        def italic(self, val: bool):
            rPr = self._r.get_or_add_rPr()
            i_el = rPr.find(qn("w:i"))
            if val and i_el is None:
                rPr.append(OxmlElement("w:i"))
            elif not val and i_el is not None:
                rPr.remove(i_el)

    class Paragraph:
        def __init__(self, p_elem):
            self._p = p_elem
            self._element = p_elem

        @property
        def runs(self) -> list[Run]:
            return [Run(r) for r in self._p.findall(qn("w:r"))]

        @property
        def text(self) -> str:
            return "".join(r.text for r in self.runs)

        @property
        def alignment(self) -> Optional[str]:
            pPr = self._p.find(qn("w:pPr"))
            if pPr is not None:
                jc = pPr.find(qn("w:jc"))
                if jc is not None:
                    return jc.get(qn("w:val"))
            return None

        @alignment.setter
        def alignment(self, val: str):
            pPr = self._p.get_or_add_pPr()
            jc = pPr.find(qn("w:jc"))
            if jc is None:
                jc = OxmlElement("w:jc")
                pPr.append(jc)
            jc.set(qn("w:val"), str(val))

        def add_run(self, text: str = "") -> Run:
            r = OxmlElement("w:r")
            t = OxmlElement("w:t")
            t.text = text
            t.set(qn("xml:space"), "preserve")
            r.append(t)
            self._p.append(r)
            return Run(r)

    class _Cell:
        def __init__(self, tc_elem):
            self._tc = tc_elem

        @property
        def paragraphs(self) -> list[Paragraph]:
            return [Paragraph(p) for p in self._tc.findall(qn("w:p"))]

        @property
        def tables(self) -> list[Table]:
            return [Table(tbl) for tbl in self._tc.findall(qn("w:tbl"))]

        def add_paragraph(self, text: str = "") -> Paragraph:
            p = OxmlElement("w:p")
            self._tc.append(p)
            para = Paragraph(p)
            if text:
                para.add_run(text)
            return para

    class _Row:
        def __init__(self, tr_elem):
            self._tr = tr_elem

        @property
        def cells(self) -> list[_Cell]:
            return [_Cell(tc) for tc in self._tr.findall(qn("w:tc"))]

    class Table:
        def __init__(self, tbl_elem):
            self._tbl = tbl_elem
            self.style = None

        @property
        def rows(self) -> list[_Row]:
            return [_Row(tr) for tr in self._tbl.findall(qn("w:tr"))]

        def add_row(self) -> _Row:
            num_cols = len(self.rows[0].cells) if self.rows else 1
            tr = OxmlElement("w:tr")
            for _ in range(num_cols):
                tc = OxmlElement("w:tc")
                tc.append(OxmlElement("w:p"))
                tr.append(tc)
            self._tbl.append(tr)
            return _Row(tr)

    class Section:
        """ Đại diện cho <w:sectPr> (quy đổi twips <-> EMU: 1 twip = 635 EMU)."""

        def __init__(self, sect_elem):
            self._sectPr = sect_elem

        def _get_pgSz(self):
            pgSz = self._sectPr.find(qn("w:pgSz"))
            if pgSz is None:
                pgSz = OxmlElement("w:pgSz")
                self._sectPr.append(pgSz)
            return pgSz

        def _get_pgMar(self):
            pgMar = self._sectPr.find(qn("w:pgMar"))
            if pgMar is None:
                pgMar = OxmlElement("w:pgMar")
                self._sectPr.append(pgMar)
            return pgMar

        @property
        def page_width(self) -> Optional[int]:
            val = self._get_pgSz().get(qn("w:w"))
            return int(val) * 635 if val and val.lstrip("-").isdigit() else None

        @page_width.setter
        def page_width(self, emu: int):
            self._get_pgSz().set(qn("w:w"), str(int(round(emu / 635))))

        @property
        def page_height(self) -> Optional[int]:
            val = self._get_pgSz().get(qn("w:h"))
            return int(val) * 635 if val and val.lstrip("-").isdigit() else None

        @page_height.setter
        def page_height(self, emu: int):
            self._get_pgSz().set(qn("w:h"), str(int(round(emu / 635))))

        def _get_margin(self, attr: str) -> Optional[int]:
            val = self._get_pgMar().get(qn(attr))
            return int(val) * 635 if val and val.lstrip("-").isdigit() else None

        def _set_margin(self, attr: str, emu: int):
            self._get_pgMar().set(qn(attr), str(int(round(emu / 635))))

        @property
        def left_margin(self) -> Optional[int]:
            return self._get_margin("w:left")

        @left_margin.setter
        def left_margin(self, emu: int):
            self._set_margin("w:left", emu)

        @property
        def right_margin(self) -> Optional[int]:
            return self._get_margin("w:right")

        @right_margin.setter
        def right_margin(self, emu: int):
            self._set_margin("w:right", emu)

        @property
        def top_margin(self) -> Optional[int]:
            return self._get_margin("w:top")

        @top_margin.setter
        def top_margin(self, emu: int):
            self._set_margin("w:top", emu)

        @property
        def bottom_margin(self) -> Optional[int]:
            return self._get_margin("w:bottom")

        @bottom_margin.setter
        def bottom_margin(self, emu: int):
            self._set_margin("w:bottom", emu)

    class _DocElementWrapper:
        def __init__(self, root_elem):
            self._root = root_elem

        @property
        def body(self):
            return self._root.find(qn("w:body"))

    _MINIMAL_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

    _MINIMAL_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    _MINIMAL_DOCUMENT_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{WORD_NS}">
  <w:body>
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1134" w:right="850" w:bottom="1134" w:left="1701"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    class Document:
        """Lớp Document tương thích hoàn toàn với python-docx trên nền zipfile + lxml."""

        def __init__(self, docx_source: Union[str, Path, io.BytesIO, None] = None):
            self._zip_parts: dict[str, bytes] = {}
            if docx_source is None:
                self._zip_parts["[Content_Types].xml"] = _MINIMAL_CONTENT_TYPES.encode("utf-8")
                self._zip_parts["_rels/.rels"] = _MINIMAL_RELS.encode("utf-8")
                self._root = etree.fromstring(_MINIMAL_DOCUMENT_XML.encode("utf-8"), parser=_XML_PARSER)
            else:
                if isinstance(docx_source, (str, Path)):
                    with zipfile.ZipFile(str(docx_source), "r") as zf:
                        for name in zf.namelist():
                            self._zip_parts[name] = zf.read(name)
                else:
                    docx_source.seek(0)
                    with zipfile.ZipFile(docx_source, "r") as zf:
                        for name in zf.namelist():
                            self._zip_parts[name] = zf.read(name)

                doc_xml = self._zip_parts.get("word/document.xml")
                if not doc_xml:
                    raise ValueError("File .docx không hợp lệ (thiếu word/document.xml)")
                self._root = etree.fromstring(doc_xml, parser=_XML_PARSER)

            self.element = _DocElementWrapper(self._root)

        @property
        def paragraphs(self) -> list[Paragraph]:
            body = self.element.body
            if body is None:
                return []
            return [Paragraph(p) for p in body.findall(qn("w:p"))]

        @property
        def tables(self) -> list[Table]:
            body = self.element.body
            if body is None:
                return []
            return [Table(tbl) for tbl in body.findall(qn("w:tbl"))]

        @property
        def sections(self) -> list[Section]:
            body = self.element.body
            if body is None:
                return []
            sects = body.findall(f".//{qn('w:sectPr')}")
            if not sects:
                sect = OxmlElement("w:sectPr")
                body.append(sect)
                sects = [sect]
            return [Section(s) for s in sects]

        def _insert_into_body(self, elem):
            body = self.element.body
            sectPr = body.find(qn("w:sectPr"))
            if sectPr is not None:
                body.insert(list(body).index(sectPr), elem)
            else:
                body.append(elem)

        def add_paragraph(self, text: str = "") -> Paragraph:
            p = OxmlElement("w:p")
            self._insert_into_body(p)
            para = Paragraph(p)
            if text:
                para.add_run(text)
            return para

        def add_table(self, rows: int, cols: int) -> Table:
            tbl = OxmlElement("w:tbl")
            for _ in range(rows):
                tr = OxmlElement("w:tr")
                for _ in range(cols):
                    tc = OxmlElement("w:tc")
                    tc.append(OxmlElement("w:p"))
                    tr.append(tc)
                tbl.append(tr)
            self._insert_into_body(tbl)
            return Table(tbl)

        def save(self, target: Union[str, Path, io.BytesIO]):
            xml_bytes = etree.tostring(
                self._root,
                xml_declaration=True,
                encoding="UTF-8",
                standalone="yes",
            )
            self._zip_parts["word/document.xml"] = xml_bytes
            target_arg = str(target) if isinstance(target, Path) else target
            with zipfile.ZipFile(target_arg, "w", zipfile.ZIP_DEFLATED) as zf:
                for name, data in self._zip_parts.items():
                    zf.writestr(name, data)
