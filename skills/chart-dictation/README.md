# chart-dictation

Convierte un cifrado **dictado por voz** (español o inglés) al formato de texto de [`slash-chart-musescore`](../slash-chart-musescore). Claude te muestra el texto y las dudas, y genera la partitura cuando lo apruebas.

## Qué entiende

- Notas en solfeo o letras: *do, re, mi… / C, D, E…*, con *bemol* y *sostenido*.
- Tipos de acorde: *menor, siete, mayor siete, menor siete, sus cuatro, disminuido, semidisminuido, aumentado, add nueve…*
- Bajos: *sol sobre si* → `G/B`.
- Estructura: *"cuatro compases de re"* → `| D | % | % | % |`, *"sol y re en el mismo compás"*, *"se repite tres veces"*, *"igual que el verso"*, *"doble barra"*.
- Encabezados: título, tempo (*"a 72, balada"*), tono (*"en re menor"*), compás (*"seis por ocho"*).
- Correcciones al vuelo: *"no, perdón, era mi menor"*.

## Ejemplo

> título grande es tu fidelidad tempo ochenta balada en re intro cuatro compases re sol sobre re re y la siete sus cuatro con la siete en el último compás…

```
Title: Grande Es Tu Fidelidad
Tempo: 80 Balada
Key: D
[Intro]
| D | G/D | D | A7sus4 A7 |
```

Requiere tener instalada también `slash-chart-musescore`.
