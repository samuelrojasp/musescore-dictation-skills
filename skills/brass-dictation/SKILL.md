---
name: brass-dictation
description: Convert dictated or handwritten (photo) horn-section lines in concert pitch into the text format used by brass-score-musescore.
---

# Horn-section dictation → brass text

The user writes lines for a horn section (for example two trumpets in unison, alto sax, tenor sax and trombone). The music comes either by voice (voice typing, usually Spanish) or as a photo of note names written by hand or in a notes app ("sol negra, la corchea…" or "G4 A8…"). The user thinks in concert pitch (real sound, as on the piano). Turn it into the text format of the `brass-score-musescore` skill, show it, and only build the score after the user approves.

Read the `brass-score-musescore` skill first: its "Text format" section is the exact target syntax.

## Reading a photo

- Read the image carefully, line by line. Keep the order of instruments and bars.
- If a word or number is unreadable, write your best guess and list it under Dudas with where it is ("trombón, compás 3, tercera nota").
- Treat the handwriting exactly like dictation: same vocabulary and shortcuts below.

## Vocabulary

Instruments → line labels: trompetas / trompeta → `TP` (both play it in unison), saxo alto → `AS`, saxo tenor → `TS`, trombón → `TB`. If the trumpets split: `TP1`, `TP2` (and set `Instruments:`). Saxo barítono → `BS`.

Notes (concert pitch):

| Dicho | Escrito |
|---|---|
| do | C |
| re | D |
| mi | E |
| fa | F |
| sol | G |
| la | A |
| si | B |

- sostenido `#`, bemol `b`, becuadro `n`. Plain names follow the concert key signature (in Si bemol, "mi" is Eb), so write `E`; write `En` only for "mi natural/becuadro".
- Speech-to-text may write "sí", "mí", "el sol", "la" as an article: in a list of notes they are note names.

Octaves (concert):

- Give an octave number on each instrument's first note (C4 = do central). If it was not said, use the usual concert octave (trumpets around G4–D5, alto around D4–A4, tenor around G3–D4, trombone around Bb2–F3) and list it under Dudas.
- Then each note goes to the nearest octave. "sube" / "arriba" → `'`; "baja" / "abajo" → `,`; a named octave ("fa cinco") → `F5`.

Rhythm (stays until it changes):

| Dicho | Escrito |
|---|---|
| redonda | `:1` |
| blanca | `:2` |
| negra | `:4` |
| corchea | `:8` |
| semicorchea | `:16` |
| con puntillo | `.` (`:4.`) |
| silencio de negra… | `R:4`… |
| descansa N compases / N compases de silencio | `R*N` |
| ligada a la siguiente | `~` after the note |
| calderón | `^` |
| acento | `>` after the note |
| staccato / picado / corto | `!` after the note |
| legato de X a Y | `(` before X, `)` after Y |

Dynamics as separate tokens before the note: `pp p mp mf f ff fp sfz`.

Not supported yet: tresillos, glissandos, caídas (falls/doits), crescendos, cambios de compás o tono, casillas 1 y 2. List them under Dudas so the user adds them in MuseScore.

Shortcuts:

- "los saxos hacen lo mismo que las trompetas" → copy the notes; "una octava abajo" → same notes one octave lower.
- "el alto hace la trompeta una tercera abajo" (or sexta, cuarta…) → move each note that many scale steps down inside the concert key, same rhythm. Mark it under Dudas as generated harmony to review.
- "mismo ritmo que la trompeta: fa, sol, la…" → copy the rhythm bar by bar with the new pitches.
- "el trombón descansa en el verso" → leave that instrument out of the block (rests are filled in automatically).
- Sections ("intro", "mambo", "puente", "final") → `[Nombre]` blocks. "se repite" → `|:` … `:|`, "tres veces" → `:|x3`.

Headers: título, arreglo, tono (concert: "en Si bemol" → `Key: Bb`), compás, tempo. Never invent a tempo.

## Steps

1. The user may send the whole arrangement or one instrument/section at a time. Keep a running text and always rebuild the full version.
2. Apply self-corrections ("no, perdón", "mejor dicho").
3. Validate before showing: run `python3 <brass-score-musescore folder>/brass2mscz.py chart.txt out --check`. Fix clear slips. Turn errors and every `Aviso` into Dudas.
4. Reply with:
   - The full text in one code block.
   - The check line (bars and each instrument's first note, real and written).
   - "Dudas:" with one short bullet per guess or warning. Leave it out if there were none.
   - One line asking whether to make the score or what to fix.
5. Apply corrections, show the full text again, ask again.
6. When the user approves, follow `brass-score-musescore` with the approved text.

## Example

Dictation:

> título mambo en si bemol cuatro cuartos tempo 110 intro trompetas forte fa cinco corchea picado fa picado silencio de negra re corchea con acento do si bemol negra, segundo compás do blanca silencio de blanca doble barra. saxo alto igual una tercera abajo.

Text:

```
Title: Mambo
Key: Bb
Time: 4/4
Tempo: 110

[Intro]
TP: f F5:8! F! R:4 D:8> C Bb:4 | C:2 R:2 ||
AS: f D5:8! D! R:4 Bb:8> A G:4 | A:2 R:2 ||
```
