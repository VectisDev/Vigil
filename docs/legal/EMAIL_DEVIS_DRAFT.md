# Borrador de correo para Prof. Devis Alvarado

**Para:** [correo institucional Devis]  
**Asunto:** CENTINEL — Paquete de revisión académica + propuesta de co-autoría

---

Estimado Prof. Alvarado:

Le escribo para compartirle el paquete completo de revisión académica
del motor estadístico de CENTINEL, junto con una propuesta formal de
colaboración y co-autoría.

**Lo que le adjunto en este correo:**

1. **Working Paper WP-CENTINEL-2026-01** — Análisis de tasa de falsos
   positivos (500 ensayos Monte Carlo). Hallazgo principal: Benford de
   primer dígito produce 100% de FP en datos electorales hondureños;
   Benford 2do dígito (Mebane 2006) produce 1.2%.

2. **STATISTICAL_CONVENTIONS.md** — Convenciones unificadas de Z-score
   y Benford para las 23 reglas del motor.

3. **THRESHOLD_CALIBRATION_HN2025.md** — Calibración de umbrales contra
   63 snapshots reales del CNE (elecciones noviembre 2025).

4. **Preprint arXiv (borrador PDF)** — Listo para envío, pendiente su
   revisión y co-autoría con afiliación UPNFM.

5. **Dataset en Zenodo** — Los 64 archivos JSON del CNE están publicados
   con DOI permanente: https://doi.org/10.5281/zenodo.20598892

**Lo que le solicito:**

- Revisar la metodología estadística de las 23 reglas.
- Firmar el Working Paper WP-CENTINEL-2026-01 como co-autor.
- Aparecer como co-autor en el preprint arXiv con afiliación UPNFM.
- Revisar el borrador de MOU adjunto para formalizar la colaboración.

Su validación académica es el componente que falta para que CENTINEL
sea tomado en serio por organismos como la OEA y el Carter Center,
y para fortalecer la propuesta de financiamiento ante el Open Technology
Fund (OTF) de Washington.

Todo el código y datos son completamente reproducibles:

    git clone https://github.com/VectisDev/centinel.git
    PYTHONPATH=src python docs/research/run_fp_analysis.py

Quedo atento a sus comentarios y disponible para reunión en la
fecha que le sea conveniente.

Atentamente,
[Tu nombre]

---
*Archivos adjuntos:*
- WP-CENTINEL-2026-01.pdf
- STATISTICAL_CONVENTIONS.md
- THRESHOLD_CALIBRATION_HN2025.md
- CENTINEL_arXiv_preprint.pdf
- MOU_UPNFM_DRAFT.pdf
