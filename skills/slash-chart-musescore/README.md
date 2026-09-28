# slash-chart-musescore

Convierte un cifrado escrito con barras verticales en una partitura de **MuseScore 4** (`.mscz`) con barras rítmicas (*slashes*) y acordes, lista para la banda. Por defecto usa el estilo *Real Book* (fuente MuseJazz).

No necesita MuseScore instalado para generar el archivo: el script `chart2mscz.py` escribe el `.mscz` directamente.

## Formato

```
Title: Cuán Grande Es Él
Tempo: 72 Balada
Key: Bb
Time: 4/4
[Intro]
|: Bb | Eb/Bb | F7sus4 F7 | Bb :|
[Verso]
| Bb | Eb | Bb F/A | Gm7 . F . ||
[Coro]
|: Eb | % | Cm7 . F7 Ab | Bb :|x3
```

| Elemento | Sintaxis |
|---|---|
| Encabezados | `Title`/`Título`, `Subtitle`, `Composer`/`Compositor`, `Tempo` (número + texto), `Key`/`Tono`, `Time`/`Compás`, `Style: standard` para la fuente normal |
| Compases | `\|`; cada línea es un sistema |
| Dos acordes en un compás | `\| C G \|` (tiempos 1 y 3) |
| Tiempo sin acorde nuevo | `.` → `\| Cm7 . F7 Ab \|` |
| Compás solo con barras | `\| . \|` o `\|  \|` |
| Repetir compás anterior | `%` (signo de repetición) |
| Secciones | `[Verso]`, `[Coro]` |
| Repeticiones | `\|:` … `:\|`, `:\|x3` imprime "x3" |
| Doble barra | `\|\|` |
| Sin acorde | `N.C.` |

## Uso directo

```bash
python3 chart2mscz.py cifrado.txt "Mi Canción.mscz"
```

Ejemplo completo: [`ejemplos/banda`](../../ejemplos/banda).
