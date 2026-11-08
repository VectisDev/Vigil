"""
Generador de PDF de seeds de acceso administrativo.
Access seed PDF generator using WeasyPrint.

Los seeds se generan aquí en texto claro. El PDF es el único registro
de las claves. El repositorio guarda un hash con sal por clave en
config/ops_keys.yml. El sitio público no pide la clave.

Seeds are generated in plaintext here. The PDF is the only record of
the keys. The repository stores a per-key salted hash in
config/ops_keys.yml. The public site does not ask for the key.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

# Protocol constant: keeps the pre-rename name on purpose (see docs/architecture/LEGACY-NAMES.md).
SEED1_SALT = "centinel-admin-salt-v1"
SEED1_ITERS = 600_000
SEED1_LABELS = list("ABCDEFGHIJKL")
SEED_LENGTH = 12


def generate_seeds(count: int = 12) -> Dict[str, str]:
    """Genera claves de 12 caracteres. La clave del mapa es el id público, no un nombre."""
    from vigil.ops_keys import fingerprint, generate_key

    issued: Dict[str, str] = {}
    for _ in range(count):
        key = generate_key()
        issued[fingerprint(key)] = key
    return issued


def _build_html(seeds: Dict[str, str], country_name: str, country_flag: str) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows = "".join(
        f"<tr><td class='label'>{key}</td><td class='seed'>{value}</td></tr>" for key, value in seeds.items()
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
    <div class="logo">VIGIL — Sistema de Auditoría Electoral</div>
    <h1>🔑 Seeds de Acceso Administrativo</h1>
    <div class="country">{country_flag} {country_name}</div>
    <div class="meta">
      Generado: {generated_at} &nbsp;·&nbsp;
      Algoritmo: PBKDF2-SHA256 &nbsp;·&nbsp;
      Iteraciones: {SEED1_ITERS:,} &nbsp;·&nbsp;
      Sal: una por clave, no un valor fijo
    </div>
  </div>

  <div class="warning-box">
    <strong>⚠ DOCUMENTO CONFIDENCIAL — GUARDA ESTE PDF EN LUGAR SEGURO</strong>
    Cada clave tiene 12 caracteres. Es el secreto y, por su huella, el id anónimo.
    El sistema <strong>no guarda</strong> la clave — solo un hash con sal en
    <code>config/ops_keys.yml</code>. El sitio público no pide la clave.
    Si pierdes este PDF, rota la clave. La id anterior queda revocada.
  </div>

  <table>
    <thead>
      <tr>
        <th>Seed</th>
        <th>Clave (12 caracteres, alfabeto de 62, unos 71 bits)</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>

  <div class="instructions">
    <h2>¿Cómo usar estos seeds?</h2>
    <ul>
      <li>Quien hace el fork entrega cada clave a su equipo, fuera de este sitio.</li>
      <li>El sitio público no tiene un campo para la clave y no la comprueba.</li>
      <li>Un commit firmado que administre el panel nombra el id (la huella), no la clave.</li>
      <li>Rotar una clave revoca ese id. Los commits viejos siguen mostrando el id anterior.</li>
    </ul>
  </div>

  <div class="verify-box">
    <strong>Verificación:</strong> el hash con sal está en <code>config/ops_keys.yml</code>.
    La comparación se hace en un comando o en una Action, no en el JavaScript de la página.
    Este PDF es el único registro de la clave.
  </div>

  <div class="footer">
    <span>VIGIL · AGPL-3.0 · github.com/VectisDev/Vigil</span>
    <span>Generado: {generated_at}</span>
  </div>
</body>
</html>"""


def generate_pdf(seeds: Dict[str, str], country_name: str, country_flag: str) -> bytes:
    """Convierte seeds a PDF usando WeasyPrint. Retorna bytes del PDF."""
    from weasyprint import HTML  # lazy import — WeasyPrint tiene deps pesadas

    html = _build_html(seeds, country_name, country_flag)
    return HTML(string=html).write_pdf()
