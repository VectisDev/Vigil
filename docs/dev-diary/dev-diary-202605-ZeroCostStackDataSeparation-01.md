# Dev Diary - 202605 - ZeroCostStackDataSeparation - 01

**Fecha aproximada / Approximate date:** 19-may-2026 / May 19, 2026  
**Fase / Phase:** Eliminar toda dependencia de pago y separar datos del código / Eliminating all paid dependencies and separating data from code  
**Versión interna / Internal version:** v0.1.x (ciclo dev-v11)  
**Rama / Branch:** dev-v11  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuación de `dev-diary-202605-AcademicoForensicSandbox-01.md`. Con el sandbox listo, la auditoría honesta del stack reveló deuda operativa: servicios de pago que podían cortar el sistema en cualquier momento. / With the sandbox ready, an honest audit of the stack revealed operational debt: paid services that could cut the system at any moment.

---

## [ES]

### 1) El Problema (Contexto)
El stack de CENTINEL dependía de Fly.io para hosting, Arbitrum para anclar hashes en blockchain (con gas fees), Telegram para alertas operacionales, y S3/Cloudflare para almacenamiento. Cada uno de estos servicios tiene costo recurrente, requiere una cuenta de tercero, y representa un punto único de fallo: si alguien no paga la factura, si el servicio cae, si la cuenta es suspendida — el sistema se detiene. En el contexto de un conteo disputado en Honduras o Venezuela, eso no es un riesgo operacional abstracto: es la diferencia entre evidencia registrada y evidencia ausente.

### 2) La Hipótesis
GitHub Actions, GitHub Pages, GitHub Releases y el RPC público de Base L2 cubren exactamente las mismas capacidades — recolección automatizada, publicación web, distribución de artifacts, y anclaje blockchain — a costo cero, sin cuentas de servicio adicionales, y con la misma garantía de uptime que cualquiera de las alternativas de pago. La separación de datos electorales en un repositorio `centinel-data` independiente del código resuelve además el problema de portabilidad entre ciclos electorales y países.

### 3) El Experimento / Implementación
Se eliminaron de todos los workflows y del código: Fly.io (hosting y deployment), Arbitrum (blockchain anchoring con fees), los bots de Telegram (alertas), y las referencias a S3/Cloudflare (almacenamiento de snapshots). El endpoint de Alchemy RPC fue reemplazado por el RPC público de Base L2 sin API key. Se diseñó el concepto arquitectural de `centinel-data` como repositorio separado donde van los datos electorales específicos de cada país y ciclo, desacoplados del motor de recolección y análisis.

### 4) El Resultado (La Lección)
Funcionó. El stack quedó operativo a costo cero con las mismas capacidades funcionales. La separación datos/código resultó ser más valiosa de lo anticipado: desvincula el motor de cualquier proceso electoral específico, lo que convierte a CENTINEL en un sistema genérico reutilizable — el motor es el mismo para Honduras 2025, Venezuela 2026, o cualquier elección futura; solo cambian los datos en `centinel-data`.

### 5) La Decisión Final (Takeaway)
Dependencia financiera es dependencia operativa. Un sistema que requiere pagar para correr solo puede ser operado por quienes tienen presupuesto para hacerlo — lo que contradice directamente el argumento de que cualquier organización de observación electoral puede desplegarlo. El stack debe ser gratuito por diseño desde el primer commit, no como optimización posterior cuando ya existe la deuda.

### 6) Qué cambió y por qué ahora
Los servicios de pago fueron removidos porque la promesa "cualquier organización puede replicar esto" era estructuralmente falsa mientras requiriera cuentas en Fly.io o Arbitrum con gas fees. No fue una decisión de ingeniería: fue una decisión de integridad argumental. Si el sistema no puede ser replicado por una organización con cero presupuesto de infraestructura, el argumento de accesibilidad es marketing, no una afirmación real.

### 7) Decisiones de implementación
- **GitHub como infraestructura primaria:** Actions para automatización, Pages para publicación web, Releases para distribución de artifacts. Todo dentro del ecosistema gratuito de GitHub.
- **Base L2 con RPC público:** el anclaje blockchain mantiene la garantía de inmutabilidad sin gas fees ni cuenta de Alchemy. El RPC público de Base tiene la misma garantía operacional para este caso de uso.
- **`centinel-data` como patrón arquitectural:** no es solo un repositorio — es el principio de que el motor y los datos electorales nunca deben vivir en el mismo lugar. Eso permite auditar uno sin exponer el otro y reutilizar el motor en cualquier elección.
- **Cero variables de entorno de pago:** la eliminación es total; no quedan secretos de Fly.io, Alchemy, o Cloudflare en `.env.example` ni en los workflows.

### 8) Impacto
Una organización electoral en Honduras, Venezuela, o cualquier país con recursos limitados puede hacer fork del repositorio y desplegarlo con una cuenta de GitHub gratuita, sin pagar ningún servicio adicional. Eso cierra el argumento de accesibilidad de forma estructural: la promesa es verificable, no solo anunciada.

### 9) Aprendizaje de ciclo
El stack de infraestructura es un argumento político antes de ser una decisión técnica. Si el sistema requiere dinero para correr, solo las organizaciones con dinero pueden usarlo — lo que significa que solo las organizaciones bien financiadas pueden fiscalizar elecciones. Eso reproduce exactamente el problema que CENTINEL intenta atacar. El costo cero no es una optimización de costos: es una afirmación sobre quién tiene derecho a desplegar vigilancia electoral.

---

## [EN]

### 1) The Problem (Context)
CENTINEL's stack depended on Fly.io for hosting, Arbitrum for blockchain hash anchoring (with gas fees), Telegram for operational alerts, and S3/Cloudflare for snapshot storage. Each of these services has recurring costs, requires a third-party account, and represents a single point of failure: if someone doesn't pay the bill, if the service goes down, if the account is suspended — the system stops. In the context of a disputed count in Honduras or Venezuela, that is not an abstract operational risk: it is the difference between recorded evidence and absent evidence.

### 2) The Hypothesis
GitHub Actions, GitHub Pages, GitHub Releases, and the Base L2 public RPC cover exactly the same capabilities — automated collection, web publication, artifact distribution, and blockchain anchoring — at zero cost, without additional service accounts, and with the same uptime guarantees as any of the paid alternatives. Separating electoral data into a `centinel-data` repository independent from the code also solves the portability problem across electoral cycles and countries.

### 3) The Experiment / Implementation
Removed from all workflows and code: Fly.io (hosting and deployment), Arbitrum (blockchain anchoring with fees), Telegram bots (alerts), and all S3/Cloudflare references (snapshot storage). The Alchemy RPC endpoint was replaced by the Base L2 public RPC with no API key. The architectural concept of `centinel-data` was designed as a separate repository to hold country- and cycle-specific electoral data, decoupled from the collection and analysis engine.

### 4) The Result (The Lesson)
It worked. The stack became operational at zero cost with the same functional capabilities. The data/code separation turned out to be more valuable than anticipated: it decouples the engine from any specific electoral process, making CENTINEL a generic reusable system — the engine is the same for Honduras 2025, Venezuela 2026, or any future election; only the data in `centinel-data` changes.

### 5) The Final Decision (Takeaway)
Financial dependency is operational dependency. A system that requires payment to run can only be operated by those with the budget to do so — which directly contradicts the claim that any electoral observation organization can deploy it. The stack must be free by design from the first commit, not as a later optimization once the debt already exists.

### 6) What changed and why now
Paid services were removed because the promise "any organization can replicate this" was structurally false while it required accounts on Fly.io or Arbitrum with gas fees. This was not an engineering decision: it was an argumentative integrity decision. If the system cannot be replicated by an organization with zero infrastructure budget, the accessibility argument is marketing, not a real claim.

### 7) Implementation choices
- **GitHub as primary infrastructure:** Actions for automation, Pages for web publication, Releases for artifact distribution. Everything within GitHub's free ecosystem.
- **Base L2 with public RPC:** blockchain anchoring maintains the immutability guarantee without gas fees or an Alchemy account. The Base public RPC provides the same operational guarantee for this use case.
- **`centinel-data` as architectural pattern:** not just a repository — it is the principle that the engine and electoral data should never live in the same place. This allows auditing one without exposing the other and reusing the engine in any election.
- **Zero paid environment variables:** the removal is total; no Fly.io, Alchemy, or Cloudflare secrets remain in `.env.example` or workflows.

### 8) Impact
An electoral organization in Honduras, Venezuela, or any resource-limited country can fork the repository and deploy it with a free GitHub account, paying for no additional services. That closes the accessibility argument structurally: the promise is verifiable, not just announced.

### 9) Cycle takeaway
The infrastructure stack is a political argument before it is a technical decision. If the system requires money to run, only organizations with money can use it — which means only well-funded organizations can conduct electoral monitoring. That reproduces exactly the problem CENTINEL is trying to address. Zero cost is not a cost optimization: it is a statement about who has the right to deploy electoral oversight.

---

## Cierre / Close
Un stack a costo cero no es una restricción de presupuesto: es una afirmación de que la vigilancia electoral no puede tener guardianes financieros. / A zero-cost stack is not a budget constraint: it is a statement that electoral oversight cannot have financial gatekeepers.
