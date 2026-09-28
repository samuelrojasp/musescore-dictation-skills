# brass-score-musescore

Convierte líneas para sección de vientos escritas en **sonido real** en una partitura de **MuseScore 4** transpuesta para cada instrumento, con el **nombre de la nota dentro de la cabeza** (C, D, F♯…) para músicos que aún no leen con fluidez, y pentagramas más grandes.

| Código | Instrumento | Transposición |
|---|---|---|
| `TP` | Trompetas 1 y 2 (al unísono) | Si♭, suena una 2ª mayor abajo |
| `TP1`, `TP2` | Trompeta 1 / 2 | Si♭ |
| `AS` | Saxofón alto | Mi♭, suena una 6ª mayor abajo |
| `TS` | Saxofón tenor | Si♭, suena una 9ª mayor abajo |
| `BS` | Saxofón barítono | Mi♭, suena una 13ª mayor abajo |
| `TB` | Trombón | en Do, clave de fa |

Las armaduras se ajustan solas (por ejemplo, en Mi concierto el saxo alto queda en Re♭ en vez de Do♯).

## Formato

```
Title: Mambo de Prueba
Arranger: …
Instruments: TP AS TS TB
Key: Bb
Time: 4/4
Tempo: 110

[Intro]
TP: f F5:8! F! R:4 D:8> C Bb:4 | C:2 R:2 ||
AS: f D5:8! D! R:4 Bb:8> A F:4 | A:2 R:2 ||
TS: f Bb4:8! Bb! R:4 F:8> F D:4 | F:2 R:2 ||
TB: f Bb2:8! Bb! R:4 Bb:8> Bb Bb:4 | F:2 R:2 ||

[Verso]
TP: R*4
```

Misma sintaxis de notas que el coro (octavas, duraciones, ligaduras, dinámicas), más:

| Elemento | Sintaxis |
|---|---|
| Acento | `>` después de la nota |
| Staccato | `!` después de la nota |
| Varios compases de silencio | `R*8` |
| Instrumento que descansa | se omite su línea en esa sección |
| Tamaño | `Size: grande` (por defecto), `muy grande`, `normal` |

El script avisa de notas fuera del registro cómodo de cada instrumento y muestra con qué nota empieza cada uno (real y escrita).

## Uso directo

```bash
export MSCORE="/Applications/MuseScore 4.app/Contents/MacOS/mscore"   # macOS
python3 brass2mscz.py vientos.txt salida --check
python3 brass2mscz.py vientos.txt salida
```

Ejemplo completo: [`ejemplos/vientos`](../../ejemplos/vientos).
