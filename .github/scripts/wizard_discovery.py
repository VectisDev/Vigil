#!/usr/bin/env python3
"""
CENTINEL — Endpoint Auto-Discovery
=====================================
Dado una URL base proporcionada por el usuario, descubre automáticamente
los endpoints reales de la API electoral para el país configurado.

Given a base URL provided by the user, automatically discovers the real
electoral API endpoints for the configured country.

Flujo / Flow:
  1. Lee ELECTION_URL y CENTINEL_COUNTRY del entorno
  2. Extrae el host base (ignora paths del usuario)
  3. Prueba patrones de API conocidos para ese país
  4. Confirma cuáles responden HTTP 200 con JSON válido
  5. Escribe los endpoints confirmados en command_center/config.yaml

El resultado es usado directamente por poller_async.py.
The result is used directly by poller_async.py.

Author: CENTINEL Team
License: AGPL-3.0
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse, urljoin

# ── Configuración desde entorno / Config from environment ─────────────────────
ELECTION_URL = os.environ.get("ELECTION_URL", "").strip()
COUNTRY      = os.environ.get("CENTINEL_COUNTRY", "HN").strip().upper()
YEAR         = os.environ.get("CENTINEL_YEAR", "2025").strip()
TIMEOUT      = int(os.environ.get("DISCOVERY_TIMEOUT", "15"))

# ── Cargar preset del país / Load country preset ───────────────────────────────
repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

preset = None
try:
    from vigil.countries import LATAM_COUNTRIES
    preset = LATAM_COUNTRIES.get(COUNTRY)
    if preset:
        print(f"✓ Preset cargado: {preset.name} ({len(preset.divisions)} divisiones)")
    else:
        print(f"⚠ Sin preset para {COUNTRY}")
except Exception as exc:
    print(f"⚠ countries.py no disponible: {exc}")


def _slugify(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")


def _extract_base(url: str) -> str:
    """
    Extrae solo scheme + host de una URL.
    Extract only scheme + host from a URL.

    https://resultados2029.cne.hn/presidencial/algo → https://resultados2029.cne.hn
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _probe(url: str, timeout: int = TIMEOUT) -> bool:
    """
    Verifica si una URL responde HTTP 200 con JSON válido.
    Check if a URL responds HTTP 200 with valid JSON.

    No lanza excepciones — retorna False en cualquier error.
    Never raises — returns False on any error.
    """
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "CENTINEL-Electoral-Auditor/1.0 (audit@vigil.app)",
                "Accept":     "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return False
            raw = resp.read(512)  # Solo cabecera — no descargar todo
            # Verificar que empieza como JSON
            stripped = raw.lstrip()
            return stripped.startswith(b"{") or stripped.startswith(b"[")
    except Exception:  # noqa: BLE001
        return False


def _build_candidate_patterns(base: str) -> list[dict]:
    """
    Genera patrones candidatos de URL para el país dado.
    Generate candidate URL patterns for the given country.

    Estrategia / Strategy:
      1. Patrones conocidos del país (de countries.py)
      2. Patrones genéricos comunes en APIs electorales de LATAM
      3. Variantes con/sin año, con/sin nivel electoral

    Returns:
        Lista de dicts con {national_pattern, dept_pattern, uses_code}
        List of dicts with {national_pattern, dept_pattern, uses_code}
    """
    candidates = []

    # ── Patrones desde countries.py (fuente primaria) ─────────────────────
    if preset and preset.url_pattern:
        # Reemplazar el host hardcodeado con el del usuario
        old_parsed  = urlparse(preset.url_pattern)
        old_base    = f"{old_parsed.scheme}://{old_parsed.netloc}"
        new_pattern = preset.url_pattern.replace(old_base, base)

        nat_url = None
        if preset.national_url:
            old_nat = urlparse(preset.national_url)
            old_nat_base = f"{old_nat.scheme}://{old_nat.netloc}"
            nat_url = preset.national_url.replace(old_nat_base, base)

        candidates.append({
            "name":             "preset_pattern",
            "national_url":     nat_url,
            "dept_pattern":     new_pattern,     # contiene {cne_code}
            "uses_cne_code":    True,
            "priority":         0,
        })

    # ── Patrones genéricos comunes en LATAM ───────────────────────────────
    # Basados en análisis de CNE-HN, TSE-GT, TSE-SV, INE-MX, Registraduría-CO
    # Based on analysis of CNE-HN, TSE-GT, TSE-SV, INE-MX, Registraduría-CO
    generic_patterns = [
        # Estilo CNE Honduras
        {
            "name":          "api_presidencial_nacional",
            "national_url":  f"{base}/api/presidencial/nacional",
            "dept_pattern":  f"{base}/api/presidencial/departamento/{{cne_code}}",
            "uses_cne_code": True,
            "priority":      1,
        },
        # Estilo con año en path
        {
            "name":          "api_year_presidencial",
            "national_url":  f"{base}/api/{YEAR}/presidencial/nacional",
            "dept_pattern":  f"{base}/api/{YEAR}/presidencial/departamento/{{cne_code}}",
            "uses_cne_code": True,
            "priority":      2,
        },
        # Estilo resultados directo
        {
            "name":          "resultados_presidencial",
            "national_url":  f"{base}/resultados/presidencial",
            "dept_pattern":  f"{base}/resultados/presidencial/{{cne_code}}",
            "uses_cne_code": True,
            "priority":      3,
        },
        # Estilo actas
        {
            "name":          "api_actas",
            "national_url":  f"{base}/api/actas/nacional",
            "dept_pattern":  f"{base}/api/actas/{{cne_code}}",
            "uses_cne_code": True,
            "priority":      4,
        },
        # Estilo con nombre de departamento en slug
        {
            "name":          "api_presidencial_slug",
            "national_url":  f"{base}/api/presidencial/nacional",
            "dept_pattern":  f"{base}/api/presidencial/{{slug}}",
            "uses_cne_code": False,  # usa slug en vez de código
            "priority":      5,
        },
        # Estilo PREP México
        {
            "name":          "prep_entidad",
            "national_url":  f"{base}/api/nacional",
            "dept_pattern":  f"{base}/api/entidad/{{cne_code}}",
            "uses_cne_code": True,
            "priority":      6,
        },
    ]
    candidates.extend(generic_patterns)

    return sorted(candidates, key=lambda c: c["priority"])


def discover_endpoints(base_url: str) -> dict | None:
    """
    Descubre los endpoints reales de la API electoral.
    Discover the real electoral API endpoints.

    Prueba patrones candidatos con el primer departamento del preset.
    Tests candidate patterns with the first department from the preset.

    Args:
        base_url: URL base extraída de la URL del usuario

    Returns:
        Dict con {national_url, dept_pattern, confirmed_endpoints} o None
        Dict with {national_url, dept_pattern, confirmed_endpoints} or None
    """
    if not preset:
        print("⚠ Sin preset — no se puede hacer discovery automático")
        return None

    candidates = _build_candidate_patterns(base_url)
    first_dept = preset.division_cne_codes[0] if preset.division_cne_codes else "01"
    first_slug = _slugify(preset.divisions[0]) if preset.divisions else "atlantida"

    print(f"\n🔍 Probando {len(candidates)} patrones contra {base_url}")
    print(f"   Usando primer departamento: código={first_dept} slug={first_slug}\n")

    for candidate in candidates:
        name        = candidate["name"]
        nat_url     = candidate["national_url"]
        dept_pat    = candidate["dept_pattern"]
        uses_code   = candidate["uses_cne_code"]

        # Construir URL de prueba para el primer departamento
        if uses_code:
            test_dept_url = dept_pat.replace("{cne_code}", first_dept)
        else:
            test_dept_url = dept_pat.replace("{slug}", first_slug)

        print(f"  [{name}]")
        print(f"    nacional: {nat_url}")

        # Probar nacional
        nat_ok = _probe(nat_url) if nat_url else False
        print(f"    nacional → {'✅ OK' if nat_ok else '❌ no responde'}")

        # Probar primer departamento
        dept_ok = _probe(test_dept_url)
        print(f"    dept/{first_dept} → {'✅ OK' if dept_ok else '❌ no responde'}")

        if nat_ok and dept_ok:
            print(f"\n✅ Patrón confirmado: {name}")

            # Confirmar TODOS los departamentos con el patrón encontrado
            confirmed = {}

            if nat_url:
                confirmed["00"] = nat_url

            if preset.division_cne_codes:
                codes_to_probe = preset.division_cne_codes
            else:
                codes_to_probe = [f"{i:02d}" for i in range(1, len(preset.divisions) + 1)]

            slugs = [_slugify(d) for d in preset.divisions]

            print(f"\n  Confirmando {len(codes_to_probe)} departamentos...")
            ok_count  = 0
            fail_count = 0

            for i, code in enumerate(codes_to_probe):
                slug = slugs[i] if i < len(slugs) else f"dept_{code}"
                if uses_code:
                    url = dept_pat.replace("{cne_code}", code)
                else:
                    url = dept_pat.replace("{slug}", slug)

                if _probe(url):
                    confirmed[code] = url
                    ok_count += 1
                    time.sleep(0.3)  # rate limiting / respeto al servidor
                else:
                    fail_count += 1
                    print(f"    ⚠ dept/{code} ({preset.divisions[i] if i < len(preset.divisions) else code}) no responde")

            print(f"\n  Confirmados: {ok_count} / {len(codes_to_probe)} departamentos")

            return {
                "pattern_name":  name,
                "national_url":  nat_url,
                "dept_pattern":  dept_pat,
                "uses_cne_code": uses_code,
                "confirmed":     confirmed,  # {code: url}
                "ok_count":      ok_count,
                "fail_count":    fail_count,
            }

        time.sleep(0.5)  # pausa entre candidatos

    print("\n❌ Ningún patrón respondió correctamente")
    return None


def write_config(discovery: dict, base_url: str) -> None:
    """
    Escribe los endpoints descubiertos en command_center/config.yaml.
    Write discovered endpoints to command_center/config.yaml.

    Preserva configuración existente, solo actualiza endpoints.
    Preserves existing config, only updates endpoints.
    """
    try:
        import yaml
        _use_yaml = True
    except ImportError:
        _use_yaml = False

    cfg_path = Path("command_center/config.yaml")
    if _use_yaml and cfg_path.exists():
        cfg = yaml.safe_load(cfg_path.read_text()) or {}
    else:
        cfg = {}

    # Actualizar metadata
    cfg.setdefault("centinel", {})
    cfg["centinel"]["country"]             = COUNTRY
    cfg["centinel"]["year"]                = YEAR
    cfg["centinel"]["election_url"]        = base_url
    cfg["centinel"]["discovery_pattern"]   = discovery["pattern_name"]
    cfg["centinel"]["endpoints_confirmed"] = discovery["ok_count"]

    # Escribir endpoints confirmados
    # Orden: nacional primero, luego departamentos por código
    endpoints = {}
    confirmed = discovery["confirmed"]

    if "00" in confirmed:
        endpoints["00"] = confirmed["00"]

    for code in sorted(k for k in confirmed if k != "00"):
        endpoints[code] = confirmed[code]

    cfg["endpoints"]  = endpoints
    cfg["base_url"]   = discovery.get("national_url", "")
    cfg["cne_domains"] = [urlparse(base_url).netloc]

    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if _use_yaml:
        cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
    else:
        # Fallback sin yaml: JSON-in-comment no es ideal pero funciona
        cfg_path.write_text(
            f"# CENTINEL config — generated by wizard_discovery.py\n"
            f"# country: {COUNTRY}\n"
            f"# base_url: {base_url}\n"
        )

    print(f"\n✓ command_center/config.yaml actualizado — {len(endpoints)} endpoints")

    # También actualizar config/prod/endpoints.yaml para el OPS panel
    ep_path = Path("config/prod/endpoints.yaml")
    if _use_yaml:
        ep_cfg = yaml.safe_load(ep_path.read_text()) if ep_path.exists() else {}
        ep_cfg = ep_cfg or {}
        ep_cfg.setdefault("cne", {})
        ep_cfg["cne"]["main_url"] = discovery.get("national_url", "")
        ep_cfg["cne"]["presidential_endpoints"] = [
            {"department_code": int(code) if code.isdigit() else code, "url": url}
            for code, url in confirmed.items()
            if code != "00"
        ]
        ep_path.parent.mkdir(parents=True, exist_ok=True)
        ep_path.write_text(yaml.safe_dump(ep_cfg, sort_keys=False, allow_unicode=True))
        print(f"✓ config/prod/endpoints.yaml actualizado")


def fallback_from_preset(base_url: str) -> None:
    """
    Fallback: si el discovery falla, usar el patrón del preset
    con el host del usuario (mejor que nada).
    Fallback: if discovery fails, use preset pattern with user's host.
    """
    if not preset:
        print("❌ Sin preset y sin discovery — no se puede configurar")
        sys.exit(1)

    try:
        import yaml
        _use_yaml = True
    except ImportError:
        _use_yaml = False

    print(f"\n⚠ Usando fallback: patrón preset con host {base_url}")

    old_base = ""
    if preset.national_url:
        p = urlparse(preset.national_url)
        old_base = f"{p.scheme}://{p.netloc}"

    endpoints = {}

    # Nacional
    if preset.national_url:
        nat = preset.national_url.replace(old_base, base_url) if old_base else preset.national_url
        endpoints["00"] = nat

    # Departamentos
    for i, code in enumerate(preset.division_cne_codes or []):
        if preset.url_pattern:
            url = preset.url_pattern.replace("{cne_code}", code)
            url = url.replace(old_base, base_url) if old_base else url
            endpoints[code] = url

    cfg_path = Path("command_center/config.yaml")
    if _use_yaml and cfg_path.exists():
        cfg = yaml.safe_load(cfg_path.read_text()) or {}
    else:
        cfg = {}

    cfg.setdefault("centinel", {})
    cfg["centinel"]["country"]      = COUNTRY
    cfg["centinel"]["year"]         = YEAR
    cfg["centinel"]["election_url"] = base_url
    cfg["centinel"]["discovery"]    = "fallback_preset_pattern"
    cfg["endpoints"]  = endpoints
    cfg["base_url"]   = endpoints.get("00", "")
    cfg["cne_domains"] = [urlparse(base_url).netloc]

    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if _use_yaml:
        cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))

    print(f"✓ Fallback: {len(endpoints)} endpoints escritos desde preset")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not ELECTION_URL:
        print("INFO: ELECTION_URL no proporcionada — usando patrón preset sin discovery")
        # Sin URL del usuario, wizard_config.py ya maneja esto
        sys.exit(0)

    print(f"CENTINEL Discovery — país={COUNTRY} año={YEAR}")
    print(f"URL del usuario: {ELECTION_URL}")

    base = _extract_base(ELECTION_URL)
    print(f"Base extraída:   {base}\n")

    # Intentar discovery automático
    result = discover_endpoints(base)

    if result:
        write_config(result, base)
        total = result["ok_count"] + (1 if result["confirmed"].get("00") else 0)
        print(f"\n✅ Discovery completado — {total} endpoints confirmados")
        print(f"   Patrón: {result['pattern_name']}")
    else:
        # Fallback al patrón del preset con el nuevo host
        fallback_from_preset(base)
        print("\n⚠ Discovery falló — usando patrón preset con nuevo host")
        print("   Los endpoints se confirmarán en el primer ciclo del poller")
