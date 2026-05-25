"""
Generador de PDF de seeds de acceso administrativo.
Access seed PDF generator using WeasyPrint.

Los seeds se generan aquí en texto claro, se hashean con PBKDF2-SHA256
y solo los hashes se persisten en web/access.json.
El PDF es el único registro de los seeds reales.

Seeds are generated in plaintext here, hashed with PBKDF2-SHA256,
and only hashes are persisted in web/access.json.
The PDF is the only record of the real seeds.
"""

from __future__ import annotations

import hashlib
import secrets
import string
from datetime import datetime, timezone
from typing import Dict

SEED1_SALT = "centinel-admin-salt-v1"
SEED1_ITERS = 600_000
SEED1_LABELS = list("ABCDEFGHIJKL")
SEED_LENGTH = 24


def generate_seeds() -> Dict[str, str]:
    """Genera 12 seeds aleatorios de 24 caracteres con alta entropía."""
    alphabet = string.ascii_letters + string.digits
    return {
        f"S1-{label}": "".join(secrets.choice(alphabet) for _ in range(SEED_LENGTH))
        for label in SEED1_LABELS
    }


def hash_seeds(seeds: Dict[str, str]) -> Dict[str, str]:
    """Deriva hashes PBKDF2-SHA256 de los seeds. Solo los hashes se persisten."""
    return {
        key: hashlib.pbkdf2_hmac(
            "sha256", seed.encode(), SEED1_SALT.encode(), SEED1_ITERS
        ).hex()
        for key, seed in seeds.items()
    }


def _build_html(seeds: Dict[str, str], country_name: str, country_flag: str) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows = "".join(
        f"<tr><td class='label'>{key}</td><td class='seed'>{value}</td></tr>"
        for key, value in seeds.items()
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
  @page {{ size: A4; margin: 2cm; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    background: #fff; color: #111; font-size: 11pt; line-height: 1.6;
  }}
  .header {{
    border-bottom: 2px solid #111; padding-bottom: 16px; margin-bottom: 24px;
  }}
  .logo {{
    font-size: 9pt; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #555; margin-bottom: 4px;
  }}
  h1 {{ font-size: 20pt; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 4px; }}
  .country {{ font-size: 13pt; color: #333; margin-bottom: 2px; }}
  .meta {{ font-size: 9pt; color: #777; margin-top: 8px; }}
  .warning-box {{
    background: #fff8e1; border: 1.5px solid #f9a825; border-radius: 6px;
    padding: 14px 18px; margin-bottom: 24px; font-size: 10pt;
  }}
  .warning-box strong {{
    display: block; font-size: 10.5pt; margin-bottom: 6px; color: #e65100;
  }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 28px; }}
  thead tr {{ border-bottom: 1.5px solid #111; }}
  thead th {{
    font-size: 8pt; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; color: #555; padding: 6px 10px; text-align: left;
  }}
  tbody tr {{ border-bottom: 1px solid #e0e0e0; }}
  tbody tr:nth-child(even) {{ background: #f8f8f8; }}
  td {{ padding: 9px 10px; vertical-align: middle; }}
  td.label {{
    font-weight: 700; font-size: 10pt; width: 80px; color: #333; white-space: nowrap;
  }}
  td.seed {{
    font-family: 'Courier New', Courier, monospace;
    font-size: 12pt; letter-spacing: 0.04em; color: #111;
  }}
  .instructions {{ font-size: 10pt; color: #333; margin-bottom: 20px; }}
  .instructions h2 {{ font-size: 12pt; font-weight: 700; margin-bottom: 8px; }}
  .instructions li {{ margin-bottom: 5px; margin-left: 18px; }}
  .verify-box {{
    background: #f5f5f5; border: 1px solid #ddd; border-radius: 4px;
    padding: 10px 14px; margin-top: 20px; font-size: 8.5pt; color: #555;
  }}
  .footer {{
    border-top: 1px solid #ccc; padding-top: 10px; margin-top: 24px;
    font-size: 8pt; color: #999; display: flex; justify-content: space-between;
  }}
</style>
</head>
<body>
  <div class="header">
    <div class="logo">CENTINEL — Sistema de Auditoría Electoral</div>
    <h1>🔑 Seeds de Acceso Administrativo</h1>
    <div class="country">{country_flag} {country_name}</div>
    <div class="meta">
      Generado: {generated_at} &nbsp;·&nbsp;
      Algoritmo: PBKDF2-SHA256 &nbsp;·&nbsp;
      Iteraciones: 600,000 &nbsp;·&nbsp;
      Salt: {SEED1_SALT}
    </div>
  </div>

  <div class="warning-box">
    <strong>⚠ DOCUMENTO CONFIDENCIAL — GUARDA ESTE PDF EN LUGAR SEGURO</strong>
    Estos seeds son la <strong>única</strong> forma de acceder al panel de administración.
    El sistema <strong>no guarda</strong> los seeds — solo sus hashes criptográficos.
    Si pierdes este PDF, deberás regenerar nuevos seeds desde el panel OPS,
    lo que invalidará todos los seeds anteriores permanentemente.
  </div>

  <table>
    <thead>
      <tr>
        <th>Seed</th>
        <th>Valor (24 caracteres · alta entropía · uso único)</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>

  <div class="instructions">
    <h2>¿Cómo usar estos seeds?</h2>
    <ul>
      <li>Ingresa <strong>cualquiera</strong> de los 12 seeds en el panel OPS para autenticarte.</li>
      <li>Cada seed funciona independientemente — distribúyelos entre personas de confianza.</li>
      <li>Para regenerar: accede al panel OPS con un seed válido → sección §7 Acceso y Seeds.</li>
      <li>La regeneración invalida <strong>todos</strong> los seeds anteriores sin excepción.</li>
    </ul>
  </div>

  <div class="verify-box">
    <strong>Verificación:</strong> Los hashes PBKDF2-SHA256 de estos seeds están en
    <code>web/access.json</code>. El sistema nunca almacena seeds en texto claro.
    Este PDF es el único registro. Verificable offline con cualquier implementación PBKDF2.
  </div>

  <div class="footer">
    <span>CENTINEL · AGPL-3.0 · github.com/VectisDev/centinel</span>
    <span>Generado: {generated_at}</span>
  </div>
</body>
</html>"""


def generate_pdf(seeds: Dict[str, str], country_name: str, country_flag: str) -> bytes:
    """Convierte seeds a PDF usando WeasyPrint. Retorna bytes del PDF."""
    from weasyprint import HTML  # lazy import — WeasyPrint tiene deps pesadas

    html = _build_html(seeds, country_name, country_flag)
    return HTML(string=html).write_pdf()
