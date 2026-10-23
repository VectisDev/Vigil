[Español](#español) · [English](#english)

---

## Español

VIGIL lee los resultados **sin depender del formato**: al indicar la URL oficial, detecta si la publicación es JSON o CSV y aplica el analizador correcto. No hace falta código nuevo por país. Hay configuraciones listas para 21 países (`src/vigil/countries.py`).

### Nivel 1 — Validado de extremo a extremo

| País | Código | Autoridad | Formato | Estado |
|---|---|---|---|---|
| Honduras | `HN` | Consejo Nacional Electoral (CNE) | JSON | Piloto sobre la elección general de 2025, con datos reales anclados a Bitcoin |

### Nivel 2 — Configuración lista; el operador aporta la URL oficial

Las divisiones administrativas y la autoridad ya están mapeadas. Las URL incluidas son de referencia: hay que indicar la URL real de la elección; el formato se detecta en la primera captura.

| País | Código | Autoridad | Divisiones |
|---|---|---|---|
| Guatemala | `GT` | Tribunal Supremo Electoral | 22 |
| El Salvador | `SV` | Tribunal Supremo Electoral | 14 |
| Nicaragua | `NI` | Consejo Supremo Electoral | 17 |
| Costa Rica | `CR` | Tribunal Supremo de Elecciones | 7 |
| Panamá | `PA` | Tribunal Electoral | 13 |
| México | `MX` | Instituto Nacional Electoral (INE / PREP) | 32 |
| Colombia | `CO` | Registraduría Nacional | 33 |
| Venezuela | `VE` | Consejo Nacional Electoral | 24 |
| Perú | `PE` | JNE / ONPE | 25 |
| Ecuador | `EC` | Consejo Nacional Electoral | 24 |
| Bolivia | `BO` | Tribunal Supremo Electoral | 9 |
| Chile | `CL` | Servicio Electoral (SERVEL) | 16 |
| Argentina | `AR` | Cámara Nacional Electoral | 24 |
| Uruguay | `UY` | Corte Electoral | 19 |
| Paraguay | `PY` | Tribunal Superior de Justicia Electoral | 18 |
| Brasil | `BR` | Tribunal Superior Eleitoral | 27 |
| República Dominicana | `DO` | Junta Central Electoral | 32 |

### Nivel 3 — Configuración existente, sin portal público de resultados en tiempo real conocido

| País | Código | Nota |
|---|---|---|
| Cuba | `CU` | No hay un canal abierto de resultados |
| Haití | `HT` | No hay un portal público estable |
| Estados Unidos | `US` | Autoridad descentralizada: cada estado publica por su cuenta |

### Agregar o promover un país

1. Añade o ajusta el preset en [`src/vigil/countries.py`](https://github.com/VectisDev/Vigil/blob/main/src/vigil/countries.py).
2. Si el formato no es JSON ni CSV, registra un analizador en [`src/vigil/schema_adapter.py`](https://github.com/VectisDev/Vigil/blob/main/src/vigil/schema_adapter.py): XML y HTML ya se detectan; falta su analizador. Los PDF escaneados requieren OCR y hoy quedan fuera de alcance.
3. Ajusta los umbrales de dominio (participación, velocidad de escrutinio) al sistema electoral del país; ver la [guía de replicación](https://github.com/VectisDev/Vigil/blob/main/docs/operations/REPLICATION_GUIDE.md).

---

## English

VIGIL reads results **format-agnostically**: given the official URL, it detects whether the feed is JSON or CSV and applies the right parser. No new code is needed per country. Presets exist for 21 countries (`src/vigil/countries.py`).

### Tier 1 — Validated end to end

| Country | Code | Authority | Format | Status |
|---|---|---|---|---|
| Honduras | `HN` | National Electoral Council (CNE) | JSON | Piloted on the 2025 general election, with real data anchored to Bitcoin |

### Tier 2 — Preset ready; the operator supplies the official URL

Administrative divisions and the authority are already mapped. The bundled URLs are placeholders: supply the real URL for the election; the format is detected on the first capture.

| Country | Code | Authority | Divisions |
|---|---|---|---|
| Guatemala | `GT` | Supreme Electoral Tribunal | 22 |
| El Salvador | `SV` | Supreme Electoral Tribunal | 14 |
| Nicaragua | `NI` | Supreme Electoral Council | 17 |
| Costa Rica | `CR` | Supreme Electoral Tribunal | 7 |
| Panama | `PA` | Electoral Tribunal | 13 |
| Mexico | `MX` | National Electoral Institute (INE / PREP) | 32 |
| Colombia | `CO` | National Registry | 33 |
| Venezuela | `VE` | National Electoral Council | 24 |
| Peru | `PE` | JNE / ONPE | 25 |
| Ecuador | `EC` | National Electoral Council | 24 |
| Bolivia | `BO` | Supreme Electoral Tribunal | 9 |
| Chile | `CL` | Electoral Service (SERVEL) | 16 |
| Argentina | `AR` | National Electoral Chamber | 24 |
| Uruguay | `UY` | Electoral Court | 19 |
| Paraguay | `PY` | Superior Court of Electoral Justice | 18 |
| Brazil | `BR` | Superior Electoral Court | 27 |
| Dominican Republic | `DO` | Central Electoral Board | 32 |

### Tier 3 — Preset exists, no known real-time public results portal

| Country | Code | Note |
|---|---|---|
| Cuba | `CU` | No open results feed |
| Haiti | `HT` | No stable public portal |
| United States | `US` | Decentralized authority: each state publishes on its own |

### Adding or promoting a country

1. Add or adjust the preset in [`src/vigil/countries.py`](https://github.com/VectisDev/Vigil/blob/main/src/vigil/countries.py).
2. If the format is neither JSON nor CSV, register a parser in [`src/vigil/schema_adapter.py`](https://github.com/VectisDev/Vigil/blob/main/src/vigil/schema_adapter.py): XML and HTML are already detected; only their parser is missing. Scanned PDFs need OCR and are out of scope for now.
3. Tune the domain thresholds (turnout, counting speed) to the country's electoral system; see the [replication guide](https://github.com/VectisDev/Vigil/blob/main/docs/operations/REPLICATION_GUIDE.md).
