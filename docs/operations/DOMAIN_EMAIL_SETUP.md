# Guía: Email Institucional + Dominio Propio
# Por qué es importante: gmail en formularios de grants es señal de baja seriedad.
# Tiempo estimado: 30 minutos. Costo: ~$12/año (dominio) + $0 (email con Proton).

---

## Opción recomendada: Porkbun + ProtonMail

### Paso 1 — Registrar dominio (10 minutos, ~$10/año)

1. Ir a https://porkbun.com
2. Buscar: `centinel.hn` o `centinelelectoral.org` o `centinel-audit.org`
3. Si `centinel.hn` no está disponible (TLD Honduras puede requerir trámite),
   usar `.org` — es el más creíble para proyectos cívicos.
4. Registrar con pago por tarjeta. NO activar privacidad de WHOIS si el proyecto
   eventualmente busca ser público (la transparencia es un activo).

**Dominios sugeridos (en orden de preferencia):**
- `centinelelectoral.org` (~$10/año)
- `centinel-audit.org` (~$10/año)
- `centinel.lat` (~$15/año, muy impactante para la narrativa LATAM)

### Paso 2 — Email con ProtonMail (gratis, cifrado, $0)

1. Ir a https://proton.me/mail
2. Crear cuenta con el dominio registrado
3. Email resultado: `contact@centinelelectoral.org`

O usar **Proton for Organizations** (gratis para 1 usuario con dominio propio):
https://proton.me/business/plans

### Paso 3 — Configurar DNS (5 minutos)

En Porkbun, agregar los registros MX que Proton te da.
Proton tiene una guía exacta paso a paso en:
https://proton.me/support/custom-domain

### Paso 4 — Actualizar los documentos

Una vez tengas el email, actualizar:
- `docs/grants/OTF_ConceptNote_IFF2026.md` — campo de contacto
- `docs/legal/MOU_UPNFM_DRAFT.md` — correo Parte A
- `docs/legal/EMAIL_DEVIS_DRAFT.md` — remitente
- README.md — email de contacto del proyecto

---

## Nota sobre el nombre del dominio

Para OTF en particular, un dominio `.org` con nombre descriptivo
es señal de organización seria. `centinel-audit.org` o
`centinelelectoral.org` comunican el propósito inmediatamente.

`centinel.lat` es la opción más impactante narrativamente
("auditoría electoral para toda Latinoamérica").

