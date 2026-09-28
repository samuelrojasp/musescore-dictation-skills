# choir-score-musescore

Convierte un arreglo de coro escrito en texto en una partitura de **MuseScore 4**: un pentagrama por voz con la letra debajo, acordes sobre la voz superior, reducción de piano, PDF y **audios de ensayo** (todas las voces, y uno por voz con esa voz destacada).

Voces: `S`, `S1`, `S2`, `A` (contralto), `A1`, `A2`, `T` (clave de sol octavada), `T1`, `T2`, `BAR`, `B`, `B1`, `B2`. Por defecto `S A T`.

## Formato

```
Title: Santo
Composer: …
Voices: S A T
Key: G
Time: 3/4
Tempo: 72 Solemne

[A]
S: D4:4 | mf G A B | C:2 B:4 | A G F# | G:2.^ ||
A: D4:4 | D D D | E:2 D:4 | C B C | B:2.^ ||
T: B3:4 | B C D | C:2 G:4 | A F# A | D':2.^ ||
Chords: | G . D | C . G | Am D7 . | G |
Lyrics: San-to, san-to, san-to~es el Se-ñor Dios
Lyrics 2: Glo-ria~a Dios en las al-tu-ras, a-mén
```

| Elemento | Sintaxis |
|---|---|
| Nota | letra mayúscula + alteración opcional (`#`, `b`, `n` becuadro); sin alteración se aplica la armadura |
| Octava | `C4` = do central. Sin número: la nota más cercana a la anterior; `'` la siguiente arriba, `,` la siguiente abajo |
| Duración | `:1 :2 :4 :8 :16`, puntillo `:4.`; se mantiene hasta que cambia |
| Silencio | `R`, `R:2` |
| Ligadura / calderón / legato | `~` / `^` / `(` … `)` |
| Dinámica | `p mf f…` antes de la nota |
| Anacrusa | primer compás más corto (automático) |
| Voz que descansa | se omite su línea en esa sección |
| Letra | `Lyrics:` (todas las voces), `Lyrics 2:` (2ª estrofa), `Lyrics T:` (solo tenor) |
| Melisma / sinalefa | `_` / `san-to~es` |

La letra se divide en sílabas automáticamente con reglas del español (diptongos, hiatos con tilde, grupos consonánticos). Puedes forzar la división con guiones.

El script revisa que cada compás sume lo correcto, que todas las voces tengan los mismos compases, que no sobren sílabas y avisa de notas fuera del registro normal de cada voz (casi siempre una octava equivocada).

## Uso directo

```bash
export MSCORE="/Applications/MuseScore 4.app/Contents/MacOS/mscore"   # macOS
python3 choir2mscz.py coro.txt salida --check   # solo revisar
python3 choir2mscz.py coro.txt salida           # .mscz, .pdf y .mp3
```

Ejemplo completo: [`ejemplos/coro`](../../ejemplos/coro).
