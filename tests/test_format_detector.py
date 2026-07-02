"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `tests/test_format_detector.py`.
Tests del detector universal de formato (centinel.format_detector):
identifica JSON/CSV/XML/HTML/PDF por contenido, con Content-Type y
extensión de URL como desempate. Cubre las formas reales publicadas por
organismos electorales del continente (CNE-HN TREP JSON, INE-MX PREP CSV,
TSE-BR CSV latin-1).

Componentes detectados:
  - TestDetectByContent
  - TestDetectByHints
  - TestCsvDialect

======================== ENGLISH ========================
File: `tests/test_format_detector.py`.
Tests for the universal format detector (centinel.format_detector):
identifies JSON/CSV/XML/HTML/PDF from content, with Content-Type and URL
extension as tiebreakers. Covers real shapes published by electoral
authorities across the continent (CNE-HN TREP JSON, INE-MX PREP CSV,
TSE-BR latin-1 CSV).

Detected components:
  - TestDetectByContent
  - TestDetectByHints
  - TestCsvDialect
"""

import csv

import pytest

from centinel.format_detector import (
    DETECTED_ONLY_FORMATS,
    PARSEABLE_FORMATS,
    csv_dialect_for,
    detect_format,
)

# Forma TREP CNE Honduras (validada en producción 2025)
HN_TREP_JSON = (
    b'{"resultados":[{"partido":"PN","votos":"1,027,090"}],'
    b'"estadisticas":{"distribucion_votos":{"validos":"2,000,000"}}}'
)

# Forma PREP INE México: por casilla, delimitador ; y BOM UTF-8
MX_PREP_CSV = "﻿ID_ESTADO;CASILLA;PARTIDO;VOTOS\n1;001;MORENA;150\n1;002;PAN;100\n".encode("utf-8")

# Forma dados abertos TSE Brasil: latin-1
BR_TSE_CSV = "NR_ZONA;SG_PARTIDO;QT_VOTOS\n1;PT;5000\n1;PL;4000\n".encode("latin-1")


class TestDetectByContent:
    def test_hn_trep_json(self):
        assert detect_format(HN_TREP_JSON) == "json"

    def test_json_array(self):
        assert detect_format(b'[{"partido": "PN"}]') == "json"

    def test_json_with_bom_and_whitespace(self):
        assert detect_format("﻿  \n{}".encode("utf-8")) == "json"

    def test_truncated_json_still_json(self):
        # Payload cortado a media descarga sigue siendo hipótesis JSON
        assert detect_format(b'{"resultados":[{"partido":"PN"') == "json"

    def test_mx_prep_csv_semicolon_bom(self):
        assert detect_format(MX_PREP_CSV) == "csv"

    def test_br_tse_csv_latin1(self):
        assert detect_format(BR_TSE_CSV) == "csv"

    def test_csv_comma(self):
        assert detect_format(b"partido,votos\nPN,100\nPLH,90\n") == "csv"

    def test_csv_tab(self):
        assert detect_format(b"partido\tvotos\nPN\t100\nPLH\t90\n") == "csv"

    def test_xml(self):
        assert detect_format(b'<?xml version="1.0"?><resultados/>') == "xml"

    def test_html_doctype(self):
        assert detect_format(b"<!DOCTYPE html><html><body></body></html>") == "html"

    def test_xhtml_served_as_xml_is_html(self):
        payload = b'<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml"></html>'
        assert detect_format(payload) == "html"

    def test_pdf_magic(self):
        assert detect_format(b"%PDF-1.7 acta escaneada") == "pdf"

    def test_plain_text_unknown(self):
        assert detect_format(b"sin estructura reconocible") == "unknown"

    def test_empty_unknown(self):
        assert detect_format(b"") == "unknown"


class TestDetectByHints:
    def test_content_type_tiebreak(self):
        # Contenido ambiguo (una sola línea) → header decide
        assert detect_format(b"hola", "application/json") == "json"
        assert detect_format(b"hola", "text/csv; charset=utf-8") == "csv"
        assert detect_format(b"hola", "application/pdf") == "pdf"

    def test_url_extension_last_resort(self):
        assert detect_format(b"hola", None, "https://x.example/res.csv?v=1") == "csv"
        assert detect_format(b"hola", None, "https://x.example/res.json") == "json"

    def test_content_beats_wrong_header(self):
        # El contenido manda sobre un Content-Type equivocado
        assert detect_format(HN_TREP_JSON, "text/html") == "json"

    def test_format_sets_are_disjoint(self):
        assert not (PARSEABLE_FORMATS & DETECTED_ONLY_FORMATS)
        assert "json" in PARSEABLE_FORMATS and "csv" in PARSEABLE_FORMATS


class TestCsvDialect:
    def test_semicolon(self):
        assert csv_dialect_for(MX_PREP_CSV).delimiter == ";"

    def test_comma(self):
        assert csv_dialect_for(b"a,b\n1,2\n").delimiter == ","

    def test_not_csv_raises(self):
        with pytest.raises(csv.Error):
            csv_dialect_for(b"unasolapalabra")
