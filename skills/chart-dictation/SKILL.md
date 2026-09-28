---
name: chart-dictation
description: Convert a spoken or dictated description of a song (sections, bars, chords, in Spanish or English) into the pipe chord-chart text used by slash-chart-musescore.
---

# Chart dictation → chord-chart text

The user dictates songs for their band out loud (voice typing), usually in Spanish, sometimes in English or mixed. The transcript is messy: no punctuation, words instead of symbols, speech-to-text mistakes, self-corrections ("no, perdón, era Mi menor"). Your job is to turn it into the chart text format that the `slash-chart-musescore` skill converts into a MuseScore file.

This skill only produces the text. Always show it to the user and wait for their OK before making the score.

## Target format

```
Title: <título>
Tempo: <número> <texto opcional>
Key: <tono>
Time: <compás>
[Sección]
| Acorde | Acorde | Acorde Acorde | % |
```

- Header lines only for what was said. Never invent a tempo. Leave out `Key:` if it was not said (the converter infers it). Leave out `Time:` for 4/4.
- One `|` per barline. Each line is one system on the page.
- Two chords in a bar: `| A B |` (beats 1 and 3 in 4/4). Specific beats: `.` is a beat with no new chord, so "La dos tiempos, Si uno, Do uno" is `| A . B C |`.
- A bar that repeats the previous bar is `%` alone in the bar. "Cuatro compases de Sol" is `| G | % | % | % |`.
- `[Nombre]` before the first bar of each section.
- `|:` … `:|` for repeats; `:|x3` for three times.
- `||` at the end of a section that ends with a double bar.
- `N.C.` for no chord.

## Vocabulary

Note names:

| Dicho | Escrito |
|---|---|
| Do / ce | C |
| Re / de | D |
| Mi / e | E |
| Fa / efe | F |
| Sol / ge | G |
| La / a | A |
| Si / be | B |

- bemol / flat → `b`; sostenido / sharp → `#` ("Si bemol" → `Bb`, "Fa sostenido menor" → `F#m`).
- Speech-to-text often writes "sí" for Si, "mí" for Mi, "ré" or "de" for Re, and may turn "la" into an article or "sol" into "el sol". Read by context: inside a list of chords, these are note names.

Chord qualities (words or digits, both happen):

| Dicho | Escrito |
|---|---|
| mayor / major (or nothing) | (nothing) |
| menor / minor | `m` |
| siete / séptima / seven | `7` |
| mayor siete / séptima mayor / maj siete / major seven | `maj7` |
| menor siete | `m7` |
| sus cuatro / suspendido / cuatro (alone after the note) | `sus4` |
| sus dos / dos (alone after the note) | `sus2` |
| siete sus cuatro | `7sus4` |
| seis / sexta | `6` |
| nueve / novena | `9` |
| add nueve / agregado nueve / con novena | `add9` |
| once / trece | `11` / `13` |
| disminuido / disminuido siete | `dim` / `dim7` |
| semidisminuido / menor siete bemol cinco | `m7b5` |
| aumentado | `aug` |
| siete bemol nueve / siete sostenido nueve | `7b9` / `7#9` |

- Bass notes: "sobre", "con bajo en", "bajo", "barra", "slash", "over" → `/`. "Sol sobre Si" → `G/B`.
- "Sin acorde", "silencio", "corte", "en blanco" → `N.C.`

Structure phrases:

- Section names: Intro, Verso (Verso 1, Verso 2), Pre-coro, Coro, Puente, Interludio, Solo, Final / Outro, "Parte A" → `[A]`. Keep the user's wording and capitalize.
- "X compases de Y" → `Y` followed by X−1 bars of `%`.
- "Y y Z en el mismo compás", "medio y medio", "Y Z" said as one bar → `| Y Z |`.
- "un compás cada uno", "uno por compás", a plain list of chords → one chord per bar.
- "se repite", "dos veces" → `|:` … `:|`; "tres/cuatro veces" → `:|x3` / `:|x4`.
- "igual que el verso", "lo mismo que el coro" → copy that section's bars under the new section name.
- "doble barra", "cierra sección" → `||`.
- Headers: "título", "se llama" → Title. "tempo 72", "a 72", "72 BPM" → Tempo; words like balada, lenta, moderada, rápida, shuffle go after the number. "en Re", "tono de Re", "tonalidad" → Key ("Re menor" → `Dm`). "cuatro cuartos" → 4/4, "tres cuartos"/"tres por cuatro" → 3/4, "seis por ocho"/"seis octavos" → 6/8, "doce por ocho" → 12/8. "de", "autor", "artista" → Composer.
- Self-corrections ("no, perdón", "mejor dicho", "corrijo") replace what came right before.

## Layout

- Every section starts on a new line.
- Default 4 bars per line. A section of 8 bars is two lines of 4. For odd lengths (6, 10, 12…), use lines of 4 and put the remainder on the last line. If the user says "en una línea" or gives their own grouping, follow it.

## Steps

1. Read the whole dictation first, apply self-corrections, then build the chart section by section.
2. Check the counts: if the user said "ocho compases", the section must have exactly 8 bars (a `%` counts as a bar). If a repeat is inside a section, count the written bars, not the played ones.
3. Reply with:
   - The chart text in one code block, ready to copy.
   - "Dudas:" with a short bullet for each guess (a word that could be two notes, a bar count that did not match, an unclear section boundary). Leave this out if there were none.
   - One line asking whether to make the MuseScore file or what to fix.
4. The user may correct by voice ("el compás seis es Mi menor", "el coro son tres veces"). Apply the change, show the full updated chart again, and ask again.
5. When they approve ("ok", "dale", "sí", "hazlo", "pásalo a partitura"), use the `slash-chart-musescore` skill with the approved chart text.

## Example

Dictation:

> título grande es tu fidelidad tempo ochenta balada en re intro cuatro compases re sol sobre re re y la siete sus cuatro con la siete en el último compás verso dos compases de re mi menor siete la siete re re siete sobre fa sostenido sol sol menor re sobre la si menor mi siete la siete doble barra coro tres veces sol dos compases re sobre fa sostenido si menor siete mi menor siete la siete re dos compases

Chart:

```
Title: Grande Es Tu Fidelidad
Tempo: 80 Balada
Key: D
[Intro]
| D | G/D | D | A7sus4 A7 |
[Verso]
| D | % | Em7 | A7 |
| D | D7/F# | G | Gm |
| D/A | Bm | E7 | A7 ||
[Coro]
|: G | % | D/F# | Bm7 |
| Em7 | A7 | D | % :|x3
```
