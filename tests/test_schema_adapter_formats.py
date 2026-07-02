"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `tests/test_schema_adapter_formats.py`.
Tests del registry de parsers por formato (parse_payload) y de los
adaptadores universales JSON/CSV de centinel.schema_adapter: auto-mapeo
de columnas del continente, field_map explícito, agregación por
mesa/casilla, errores explícitos (nunca datos inventados) y regresión
del adaptador HN existente.

Componentes detectados:
  - TestParseJsonPayload
  - TestParseCsvPayload
  - TestParsePayloadDispatch
  - TestHnRegressionUnchanged

======================== ENGLISH ========================
File: `tests/test_schema_adapter_formats.py`.
Tests for the per-format parser registry (parse_payload) and the
universal JSON/CSV adapters in centinel.schema_adapter: continent-wide
column auto-mapping, explicit field_map, per-polling-station aggregation,
explicit errors (never invented data) and regression of the existing HN
adapter.

Detected components:
  - TestParseJsonPayload
  - TestParseCsvPayload
  - TestParsePayloadDispatch
  - TestHnRegressionUnchanged
"""

import json
from pathlib import Path

import pytest

from centinel.schema_adapter import (
    FORMAT_PARSERS,
    UnsupportedFormatError,
    adapt_hn_json,
    parse_payload,
    suggest_csv_field_map,
)

FIXTURES = Path(__file__).parent / "fixtures" / "hnd_2025"

HN_JSON = (
    b'{"resultados":['
    b'{"partido":"PN","candidato":"ANA GARCIA","votos":"1,027,090","porcentaje":"38.2"},'
    b'{"partido":"LIBRE","candidato":"RIXI MONCADA","votos":"900,123","porcentaje":"33.5"}],'
    b'"estadisticas":{'
    b'"distribucion_votos":{"validos":"2,000,000","nulos":"50,000","blancos":"30,000"},'
    b'"totalizacion_actas":{"actas_totales":"19,167","actas_divulgadas":"18,000"},'
    b'"estado_actas_divulgadas":{"actas_correctas":"17,500","actas_inconsistentes":"500"}},'
    b'"timestamp":"2025-12-01T20:00:00Z"}'
)

MX_PREP_CSV = (
    "﻿ID_ESTADO;CASILLA;PARTIDO;CANDIDATO;VOTOS;VOTOS_NULOS\n"
    "1;001;MORENA;CLAUDIA;150;3\n"
    "1;002;MORENA;CLAUDIA;200;2\n"
    "1;001;PAN;XOCHITL;100;0\n"
).encode("utf-8")

BR_TSE_CSV = (
    "NR_ZONA;SG_PARTIDO;NM_VOTAVEL;QT_VOTOS\n"
    "1;PT;LULA;5000\n"
    "2;PT;LULA;2500\n"
    "1;PL;JAIR;4000\n"
).encode("latin-1")


class TestParseJsonPayload:
    def test_hn_trep_shape_defaults(self):
        snap = parse_payload(HN_JSON, "json", country_code="HN")
        assert snap.votos_validos == 2_000_000
        assert snap.votos_nulos == 50_000
        assert snap.votos_blancos == 30_000
        assert snap.actas_total == 19_167
        assert snap.actas_inconsistentes == 500
        assert [c["party"] for c in snap.candidates] == ["PN", "LIBRE"]
        assert snap.candidates[0]["votes"] == 1_027_090
        # Timestamp embebido del payload, no wall clock
        assert snap.timestamp_utc == "2025-12-01T20:00:00Z"

    def test_custom_field_map_paths(self):
        payload = (
            b'{"data":{"totales":{"ok":"5,000"}},'
            b'"partidos":[{"agrupacion":"X","sufragios":"3,000"}]}'
        )
        fmap = {
            "totals": {"valid_votes": ["data.totales.ok"]},
            "candidate_roots": ["partidos"],
        }
        snap = parse_payload(payload, "json", field_map=fmap, country_code="EC")
        assert snap.votos_validos == 5_000
        assert snap.candidates[0]["party"] == "X"
        assert snap.candidates[0]["votes"] == 3_000

    def test_list_wrapped_payload(self):
        wrapped = b"[" + HN_JSON + b"]"
        snap = parse_payload(wrapped, "json")
        assert snap.votos_validos == 2_000_000

    def test_to_core_snapshot_roundtrip(self):
        core = parse_payload(HN_JSON, "json", country_code="HN").to_core_snapshot()
        assert core.totals.valid_votes == 2_000_000
        assert len(core.candidates) == 2
        assert core.candidates[0].party == "PN"


class TestParseCsvPayload:
    def test_mx_prep_aggregates_by_casilla(self):
        snap = parse_payload(MX_PREP_CSV, "csv", country_code="MX",
                             timestamp_utc="2024-06-02T22:00:00Z")
        by_party = {c["party"]: c["votes"] for c in snap.candidates}
        assert by_party == {"MORENA": 350, "PAN": 100}
        assert snap.votos_nulos == 5
        assert snap.votos_validos == 450  # suma de candidatos sin columna validos

    def test_br_tse_latin1_auto_map(self):
        snap = parse_payload(BR_TSE_CSV, "csv", country_code="BR",
                             timestamp_utc="2022-10-02T20:00:00Z")
        by_party = {c["party"]: c["votes"] for c in snap.candidates}
        assert by_party == {"PT": 7500, "PL": 4000}

    def test_explicit_csv_field_map_wins(self):
        raw = b"col_a,col_b\nPN,100\nPLH,90\n"
        fmap = {"csv": {"party_column": "col_a", "votes_column": "col_b"}}
        snap = parse_payload(raw, "csv", field_map=fmap)
        assert {c["party"]: c["votes"] for c in snap.candidates} == {"PN": 100, "PLH": 90}

    def test_unrecognized_columns_explicit_error(self):
        with pytest.raises(ValueError, match="csv_columns_unrecognized"):
            parse_payload(b"foo,bar\n1,2\n3,4\n", "csv")

    def test_empty_csv_explicit_error(self):
        with pytest.raises(ValueError):
            parse_payload(b"PARTIDO,VOTOS\n", "csv")

    def test_suggest_csv_field_map(self):
        suggestion = suggest_csv_field_map(MX_PREP_CSV)
        assert suggestion["party_column"] == "PARTIDO"
        assert suggestion["votes_column"] == "VOTOS"
        assert suggestion["null_column"] == "VOTOS_NULOS"
        assert suggestion["valid_column"] is None


class TestParsePayloadDispatch:
    def test_registry_has_json_and_csv(self):
        assert "json" in FORMAT_PARSERS
        assert "csv" in FORMAT_PARSERS

    def test_auto_detection_json(self):
        snap = parse_payload(HN_JSON)  # sin fmt → detecta
        assert snap.votos_validos == 2_000_000

    def test_auto_detection_csv(self):
        snap = parse_payload(MX_PREP_CSV, timestamp_utc="2024-06-02T22:00:00Z")
        assert snap.votos_nulos == 5

    def test_detected_format_overrides_wrong_hint(self):
        # Hint dice csv pero el contenido es JSON → gana lo detectado
        snap = parse_payload(HN_JSON, "csv")
        assert snap.votos_validos == 2_000_000

    @pytest.mark.parametrize("payload,name", [
        (b"<!DOCTYPE html><html></html>", "html"),
        (b'<?xml version="1.0"?><r/>', "xml"),
        (b"%PDF-1.4", "pdf"),
    ])
    def test_unsupported_formats_raise(self, payload, name):
        with pytest.raises(UnsupportedFormatError, match=name):
            parse_payload(payload)


class TestHnRegressionUnchanged:
    """El camino HN existente no cambia: mismo AdaptedSnapshot que antes.
    The existing HN path is unchanged: same AdaptedSnapshot as before."""

    def test_adapt_hn_json_fixture(self):
        fixture = sorted(FIXTURES.glob("HN.PRESIDENTE.00-TODOS*.json"))[0]
        snap = adapt_hn_json(fixture)
        raw = json.loads(fixture.read_text(encoding="utf-8"))
        dist = raw["estadisticas"]["distribucion_votos"]

        def _int(v):
            return int(str(v).replace(",", "").strip() or 0)

        assert snap.votos_validos == _int(dist["validos"])
        assert snap.votos_nulos == _int(dist["nulos"])
        assert snap.country_code == "HN"
        # Timestamp del nombre de archivo, nunca wall clock
        assert snap.timestamp_utc.startswith(fixture.name.split(" ")[1][:10])
        assert len(snap.candidates) == len(raw["resultados"])

    def test_generic_json_parser_matches_hn_adapter_totals(self):
        """El parser genérico con field_map default produce los mismos
        totales que el adaptador HN dedicado sobre el mismo fixture."""
        fixture = sorted(FIXTURES.glob("HN.PRESIDENTE.00-TODOS*.json"))[0]
        dedicated = adapt_hn_json(fixture)
        generic = parse_payload(fixture.read_bytes(), "json", country_code="HN")
        assert generic.votos_validos == dedicated.votos_validos
        assert generic.votos_nulos == dedicated.votos_nulos
        assert generic.votos_blancos == dedicated.votos_blancos
        assert generic.actas_total == dedicated.actas_total
        assert [c["party"] for c in generic.candidates] == \
            [c["party"] for c in dedicated.candidates]
