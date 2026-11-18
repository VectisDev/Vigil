# VIGIL no se esconde

**Por qué este proyecto no tiene rotación de identidad, y por qué eso lo hace más fuerte.**

*English version below.*

---

## La premisa

VIGIL observa lo que una autoridad electoral publica, **sin pedirle permiso**. Esa es la
diferencia con las herramientas que trabajan desde dentro de la institución: no necesitamos
que nadie diga que sí, y por eso seguimos funcionando aunque la autoridad no coopere.

Pero no pedir permiso **no es lo mismo que esconderse**. VIGIL se identifica en cada
petición, respeta `robots.txt` y publica lo que ve. Un observador que se oculta pierde lo
único que lo hace valioso.

## Qué había antes

El árbol llegó a tener **cuatro motores de rotación de identidad** en paralelo:

| Dónde | Qué hacía |
|---|---|
| `defense/advanced_security.py` | 15 identidades y 8 proxies, rotando cada 10–30 peticiones |
| `vigil_engine/proxy_manager.py` | 5 identidades y 3 juegos de cabeceras, bajo el nombre «anti-fingerprinting» |
| `proxy_handler.py` | rotación de proxies con validación y vuelta a modo directo |
| `download_and_hash.py` | un perfil «low profile» con `User-Agent`, `Accept-Language` y **`Referer` falso** |

Más `_apply_stealth()`, que borraba del navegador la marca que delata la automatización,
declaraba el idioma como si el equipo estuviera en España y fabricaba cinco complementos
inexistentes. Y un contexto TLS que barajaba el orden de los cifradores en cada conexión
para que la huella del saludo no fuera siempre la misma.

La documentación presumía de todo ello. Un documento dirigido a financiadores lo listaba
entre los «controles activos» de madurez institucional.

## Por qué se fue

### 1. No defendía de nada

Era la razón original: *«el gobierno querrá bloquearme porque veo lo que no quieren que
vea»*. El miedo es razonable. La defensa no servía.

- Las quince identidades decían todas `Centinel-*` o `Vigil-*`. **Una sola regla con la
  cadena `Centinel` las tumbaba las quince a la vez.**
- Los proxies eran direcciones de centro de datos, que se bloquean por ASN en un minuto.
  Ocho de ellos, además, eran direcciones de documentación de la RFC 5737: no existen.
- Y quien quiere bloquearte no mira el `User-Agent`. Mira la IP, el ASN, o te pone un
  desafío delante.

Se pagaba todo el costo reputacional de parecer que uno se oculta, sin obtener protección.

### 2. Contradecía la premisa en el propio árbol

VIGIL existe para detectar sistemas que afirman una cosa y hacen otra. Tener, dentro del
repositorio, código que afirma transparencia y maquinaria construida para no ser perfilado
es exactamente ese defecto, cometido por nosotros.

Y había una versión peor, más silenciosa: durante meses la captura programada salió **sin
identificarse en absoluto** —con la cabecera por defecto de la librería— mientras le
preguntaba a `robots.txt` si `Vigil-Engine/1.0` podía entrar. Pedíamos permiso con un nombre
que no usábamos.

### 3. Un bloqueo es un hallazgo, no un fallo

Éste es el argumento que decide.

Si un portal público le niega el acceso a un observador que **se identifica, respeta
`robots.txt` y publica lo que ve**, esa negativa es un hecho documentable con fecha:

> *El portal del CNE bloqueó a un observador electoral identificado a las 19:43 de la noche
> de elecciones.*

Eso tiene costo político para quien lo hace.

La versión con máscaras no tiene titular: *«un raspador anónimo fue bloqueado»* no es nada,
y encima obliga a admitir que uno se estaba ocultando.

**Evadir convierte un hecho político en una partida técnica que se pierde en silencio.
Identificarse convierte un bloqueo técnico en un costo político para quien bloquea.**

Hay un corolario incómodo y lo asumimos: respetar `robots.txt` significa que una autoridad
puede cegarnos con un commit de una línea. Si lo hace, **paramos y lo publicamos**. Un
portal público que añade una regla para excluir específicamente a un auditor electoral
identificado acaba de documentar su propia intención.

### 4. La evidencia tiene que ser incuestionable

El valor de VIGIL es que un tercero puede verificar las capturas **sin confiar en quien las
tomó**. Rotar identidades y salidas le regala a cualquier adversario la pregunta más
cómoda: *«¿cómo sabemos que no fabricaron esto, si iban ocultos?»*.

La disciplina es la defensa.

## Qué sí da resistencia al bloqueo

**Muchos observadores honestos, no un observador con quince máscaras.**

Si cincuenta personas despliegan cada una su nodo desde su propia cuenta, bloquear uno no
sirve de nada, y bloquearlos a todos significa bloquear rangos enteros de GitHub Actions
—costoso y muy visible—. Misma resistencia, ética opuesta, y verificable.

Por eso el despliegue desde plantilla no es una comodidad: **es la defensa real contra el
bloqueo.**

## Lo único que se conserva: una salida opcional por Tor

Hay una distinción que importa y que no es un matiz:

- **Ocultar *quién* observa** al sitio observado → evasión. Se fue.
- **Proteger *dónde está físicamente* la persona** que opera el nodo → no es evasión.

Con `VIGIL_TOR_ENABLED=true` el tráfico sale por **un** circuito Tor —uno, no una rotación—
y la cabecera sigue diciendo `Vigil-Engine/1.0 (+https://github.com/VectisDev/Vigil)`. El
portal sabe perfectamente que quien consulta es VIGIL. Lo que no aprende es desde qué casa.

En un país donde operar esto puede costarle la seguridad a una persona, eso no es un lujo.
No engaña a nadie sobre qué es el tráfico; solo evita que la dirección de alguien quede en
un registro.

Configuración y verificación: `config/prod/proxies.yaml`.

## Cómo se impide que vuelva

`tests/test_identifies_itself.py` falla si en `src/`, `scripts/` o `vigil_engine/`
reaparece: un conjunto de identidades, una cabecera elegida al azar, un `User-Agent` que
finja un navegador, o la ocultación de la automatización del navegador.

Las mismas pruebas fijan que el nombre con el que se consulta `robots.txt` y el que viaja en
la petición son **la misma constante**, que un `Disallow` dirigido a VIGIL detiene la
captura, y que un `robots.txt` ausente no bloquea nada.

Si alguna vez hace falta discutir esta decisión, el sitio es un issue — no un parche
silencioso.

---

# VIGIL does not hide

**Why this project has no identity rotation, and why that makes it stronger.**

## The premise

VIGIL observes what an electoral authority publishes **without asking permission**. That is
the difference from tools that work from inside the institution: we do not need anyone to
say yes, so we keep working when the authority does not cooperate.

But not asking permission **is not the same as hiding**. VIGIL identifies itself on every
request, respects `robots.txt` and publishes what it sees. An observer that conceals itself
loses the only thing that makes it worth anything.

## What was here before

Four parallel identity-rotation engines: fifteen identities and eight proxies rotating every
10–30 requests; five identities and three header pools labelled "anti-fingerprinting";
proxy rotation with validation and direct-mode fallback; and a "low profile" builder with a
rotating `User-Agent`, `Accept-Language` and a **fake `Referer`**. Plus browser stealth that
erased the flag every automated browser exposes, claimed a European locale and fabricated
five non-existent plugins — and a TLS context that shuffled cipher order so the handshake
fingerprint would not stay constant. The documentation advertised all of it, including to
funders, as an active maturity control.

## Why it is gone

**It defended against nothing.** All fifteen identities said `Centinel-*` or `Vigil-*`, so
one rule matching `Centinel` dropped all fifteen at once. The proxies were datacenter
addresses, blocked by ASN in a minute; eight of them were RFC 5737 documentation addresses
that do not exist. And whoever wants to block you looks at the IP and the ASN, not the
`User-Agent`.

**It contradicted the premise inside our own tree.** VIGIL exists to detect systems that
claim one thing and do another. Worse and quieter: for months the scheduled capture went out
**with no identity at all** while asking `robots.txt` whether `Vigil-Engine/1.0` could
fetch. We asked permission under a name we never used.

**A block is a finding, not a failure.** If a public portal denies access to an observer
that identifies itself, respects `robots.txt` and publishes what it sees, that refusal is a
dated, publishable fact with a political cost. "An anonymous scraper was blocked" is not a
headline, and it forces you to admit you were hiding. Evasion turns a political fact into a
technical game you lose quietly; identifying yourself turns a technical block into a
political cost for whoever blocks you.

The uncomfortable corollary, which we accept: respecting `robots.txt` means an authority can
blind us with a one-line commit. If it does, **we stop and we publish it.** A public portal
that adds a rule to exclude an identified electoral auditor has just documented its own
intent.

**Evidence has to be unquestionable.** VIGIL's value is that a third party can verify the
captures without trusting whoever took them. Rotating identities hands any adversary the
easiest question: "how do we know this was not fabricated, if you were hiding?"

## What actually resists blocking

**Many honest observers, not one observer wearing fifteen masks.** Fifty people each running
their own node means blocking one achieves nothing, and blocking all of them means blocking
entire GitHub Actions ranges — expensive and highly visible. Same resilience, opposite
ethics, and verifiable. Template deployment is therefore not a convenience: it is the real
defence against blocking.

## The one thing kept: an optional Tor exit

Hiding **who** observes is evasion and it is gone. Protecting **where the operator
physically is** is not. With `VIGIL_TOR_ENABLED=true`, traffic leaves through **one** Tor
circuit — one, not a rotation — and the header still reads
`Vigil-Engine/1.0 (+https://github.com/VectisDev/Vigil)`. The portal knows exactly that
VIGIL is asking; it does not learn from which house. In a country where running this can
cost someone their safety, that is not a luxury. See `config/prod/proxies.yaml`.

## How it is kept out

`tests/test_identifies_itself.py` fails if an identity pool, a randomly chosen header, a
browser-impersonating `User-Agent`, or browser automation concealment reappears in `src/`,
`scripts/` or `vigil_engine/`. The same tests pin that the name asked about in `robots.txt`
and the name sent on the wire are the same constant, that a `Disallow` aimed at VIGIL stops
the capture, and that a missing `robots.txt` blocks nothing.

If this decision ever needs revisiting, the place is an issue — not a silent patch.
