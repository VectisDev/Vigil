# VIGIL · Guía de marca (v1)

Principios: **elegancia, simplicidad, limpieza, funcionalidad.**

## Idea
**«Visto bueno».** La V de VIGIL es una marca de verificación (✓). El punto rojo, siempre equidistante de ambos brazos, es el voto que la verificación sostiene. Se entiende sin explicación: *comprobado*.

## Logo
- `logo/vigil-horizontal.svg` — principal (con lema).
- `logo/vigil-horizontal-corto.svg` — cabeceras y navegación (sin lema).
- `logo/vigil-vertical.svg` — portadas, redes, documentos cuadrados.
- `logo/vigil-marca.svg` — solo símbolo. Versiones `-oscuro` para fondos negros; `-mono-negro` / `-mono-blanco` para una sola tinta.
- Favicon: `favicon/favicon.svg` (se adapta a modo oscuro), PNG 16/32/180/512 (`favicon-tile`, fondo negro).

## Espacio libre y tamaño mínimo
- Espacio libre alrededor = diámetro del punto rojo × 2 (≈ ¼ de la altura del símbolo).
- Mínimo: símbolo 16 px; logo horizontal con lema 140 px de ancho; sin lema 96 px.
- Por debajo de 24 px el lema se omite.

## Color (solo tres)
| Token | Hex | Uso |
|---|---|---|
| Negro | `#0A0A0A` | texto, símbolo |
| Blanco | `#FFFFFF` | fondo |
| Rojo | `#D7262E` | un solo acento por pieza (punto, «alterados.», alertas) |
| Rojo en fondo oscuro | `#FF4D55` | mismo rojo, ajustado para contraste |
Grises neutros solo para líneas finas (`#E5E5E5`) y banda (`#F5F5F5`). Sin azul, amarillo ni degradados.

## Tipografía (licencia OFL, igual que Pages)
- **Inter** 600, espaciado amplio: nombre VIGIL. Inter 400–500 para titulares y texto.
- **JetBrains Mono** 500, versalitas espaciadas: etiquetas y lema.
El logo está convertido a trazos: no depende de fuentes instaladas.

## No hacer
Cambiar colores, girar, añadir sombras o contornos, poner el rojo en más de un elemento, estirar, usar el logo antiguo.

## README (claro/oscuro)
Ver `README-banner-snippet.md` (`<picture>` con `prefers-color-scheme`).
