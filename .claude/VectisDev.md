# VectisDev.md — Instrucciones Permanentes de Desarrollo

**Proyecto CENTINEL** — Auditoría Electoral Estadística y Criptográfica  
**Estado**: Desarrollo confidencial de alto rigor técnico  
**Objetivo**: Ser el estándar de referencia en auditoría electoral independiente en Centroamérica para 2029.

---

## Ramas Activas

| Rama       | Rol                                      |
|------------|------------------------------------------|
| `main`     | Producción — merge solo vía PR revisado |
| `dev-v11`  | Integración — rama dev anterior         |
| `dev-v12`  | Integración — rama dev más reciente     |

**Nota**: Actualizar esta tabla cuando se cree una nueva rama `dev-vNN`.

---

## Agentes Especializados (Clase Mundial)

Todos los prompts de desarrollo **deben** invocar los agentes relevantes usando la sintaxis `@nombre-del-agente`.

### Lista de Agentes

| Agente                     | Rol Principal                                      | Uso Principal |
|---------------------------|----------------------------------------------------|-------------|
| `@stats-phd-agent`        | Estadística Forense y Matemáticas (PhD)           | Reglas estadísticas, umbrales, validación matemática, gráficos |
| `@crypto-security-agent`  | Criptografía y Cadena de Custodia                 | Hashing, fingerprints, Merkle Trees, anchoring, verificación |
| `@cybersecurity-agent`    | Ciberseguridad y Hardening                         | Threat modeling, proxies, logging, resiliencia |
| `@ops-monitor-agent`      | Operaciones y SRE (24/7)                           | Polling, watchdog, monitoreo, benchmarks |
| `@rules-engine-agent`     | Arquitectura del Motor de Reglas                   | Refactor, modularidad, tests, YAML |
| `@dashboard-visual-agent` | Visualización y Reportes Profesionales             | Dashboards, PDFs, UI/UX, design system |
| `@legal-strategy-agent`   | Asesoría Legal y Estratégica                       | Cumplimiento HN, disclaimers, estrategia con observadores |

### Reglas de Uso de Agentes (OBLIGATORIAS)

1. **Siempre** invocar los agentes relevantes al inicio de cada prompt.
2. Para tareas complejas, combinar múltiples agentes (ejemplo: `@stats-phd-agent @rules-engine-agent @crypto-security-agent`).
3. Todo código generado **debe** cumplir:
   - Docstrings **bilingües** completos (English/Spanish)
   - Comentarios bilingües en secciones críticas
   - Fórmulas en KaTeX
   - Estándares de cada agente (rigor matemático, seguridad, diseño, etc.)
4. Mantener compatibilidad absoluta con la cadena de hashes existente.
5. Todo cambio significativo debe considerar impacto en neutralidad, reproducibilidad y credibilidad internacional.

---

## Regla de PRs — OBLIGATORIA

**Siempre que se cree un PR, crear DOS PRs simultáneos:**

1. **PR → `main`** (base: `main`)
2. **PR → rama dev más reciente** (base: `dev-v12` o la activa)

Ambos PRs deben crearse en el mismo momento, con el **mismo título y descripción**.  
Nunca crear un PR que apunte solo a uno de los dos targets.

### Flujo de Trabajo

feature-branch
├── PR #A → main
└── PR #B → dev-v12   (rama dev más reciente)


Si la rama dev ya contiene los cambios (cherry-pick), igualmente crear el PR formal para trazabilidad y CI.

### Auto-merge — SIEMPRE hacer merge automáticamente

**Regla crucial:** A MENOS QUE se indique explícitamente lo contrario, **SIEMPRE** hacer merge automáticamente cuando:
- ✅ CI pasa verde en ambos PRs
- ✅ No hay conflictos de merge
- ✅ Todos los checks están "success"

---

## Ramas de Desarrollo

- Las ramas de trabajo se crean desde `main` con prefijo `vectisdev/`
- Formato: `vectisdev/<slug>-<id>`
- Nunca hacer push directo a `main` ni a `dev-vNN` salvo cherry-picks de seguridad urgentes

---

## Convenciones de Commits

- Seguir **Conventional Commits**: `fix:`, `feat:`, `security:`, `chore:`, `docs:`, `refactor:`
- Incluir URL de sesión al final del mensaje de commit
- No incluir nombre o ID del modelo en commits, PRs ni código
- Commits de seguridad deben comenzar con `security:`

---

**Este documento es de referencia obligatoria.**  
Cualquier desviación debe ser justificada explícitamente.

---

¿Quieres que haga algún ajuste adicional antes de que lo subas?

Por ejemplo:
- Agregar más secciones (estándares de código, testing strategy, etc.)
- Cambiar el orden de las secciones
- Hacerlo más corto o más formal

Dime cómo lo quieres y lo refinamos.























