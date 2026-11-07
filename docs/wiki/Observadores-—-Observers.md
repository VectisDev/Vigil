[Español](#español) · [English](#english)

---

## Español

Esta página es para quien quiere comprobar los bytes sin instalar el motor. Los pasos canónicos, con el código de salida esperado, están en [`docs/VERIFY.md`](https://github.com/VectisDev/Vigil/blob/main/docs/VERIFY.md). La muestra de 2025 no es una cadena: el verificador sale en 1.

### Verificar un directorio de snapshots

Solo necesitas Python 3.6 o superior; el verificador usa únicamente la biblioteca estándar.

```bash
curl -O https://raw.githubusercontent.com/VectisDev/Vigil/main/verify/verify_chain.py
python3 verify_chain.py /ruta/a/los/snapshots/
```

- `-v` muestra el hash de cada archivo.
- `-o informe.txt` guarda el informe en un archivo.
- `--json` produce el resultado en JSON.

Si la cadena está íntegra, el script lo indica. Si un archivo fue modificado, señala el punto exacto donde se rompe la cadena.

### Reproducir el análisis completo

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make reproduce-2025-audit
```

Esto vuelve a ejecutar el análisis forense del [piloto Honduras 2025](Piloto-Honduras-2025-—-Honduras-2025-pilot) sobre los mismos 64 archivos oficiales.

### Qué hace y qué no hace

| VIGIL sí | VIGIL no |
|---|---|
| Captura los datos que la autoridad publica en línea | Analiza actas físicas ni papeletas |
| Encadena cada captura con SHA-256 y la ancla a Bitcoin | Accede a sistemas internos de la autoridad |
| Señala deltas en la serie guardada | Acusa a una parte o decide una elección |
| Permite que cualquiera verifique sin conexión | Reemplaza la observación en las mesas de votación |
| | Constituye por sí mismo prueba jurídica: es evidencia técnica para evaluación experta |

### Documentación completa

- [Guía técnica para observadores internacionales](https://github.com/VectisDev/Vigil/blob/main/docs/international_observers/OBSERVER_GUIDE.md)
- [Límites legales y operativos](https://github.com/VectisDev/Vigil/blob/main/docs/legal/LEGAL-AND-OPERATIONAL-BOUNDARIES.md)
- [Panel público de verificación](https://vectisdev.github.io/Vigil/)

---

## English

This page is for election observers, journalists and citizens who want to **check for themselves** that the data VIGIL captured was not altered — without installing the system or trusting its operators.

### Verify the chain in 2 minutes

You only need Python 3.6 or newer; the verifier uses the standard library only.

```bash
curl -O https://raw.githubusercontent.com/VectisDev/Vigil/main/verify/verify_chain.py
python3 verify_chain.py /path/to/snapshots/
```

- `-v` prints the hash of every file.
- `-o report.txt` writes the report to a file.
- `--json` outputs the result as JSON.

If the chain is intact, the script says so. If any file was modified, it points to the exact place where the chain breaks.

### Reproduce the full analysis

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make reproduce-2025-audit
```

This re-runs the forensic analysis of the [Honduras 2025 pilot](Piloto-Honduras-2025-—-Honduras-2025-pilot) on the same 64 official files.

### What it does and does not do

| VIGIL does | VIGIL does not |
|---|---|
| Capture the data the authority publishes online | Analyze physical tally sheets or ballots |
| Chain every capture with SHA-256 and anchor it to Bitcoin | Access the authority's internal systems |
| Points at deltas in the stored series | Accuses a party or decides an election |
| Let anyone verify offline | Replace observation at polling stations |
| | Constitute legal proof by itself: it is technical evidence for expert evaluation |

### Full documentation

- [Technical guide for international observers](https://github.com/VectisDev/Vigil/blob/main/docs/international_observers/OBSERVER_GUIDE.md)
- [Legal and operational boundaries](https://github.com/VectisDev/Vigil/blob/main/docs/legal/LEGAL-AND-OPERATIONAL-BOUNDARIES.md)
- [Public verification panel](https://vectisdev.github.io/Vigil/)
