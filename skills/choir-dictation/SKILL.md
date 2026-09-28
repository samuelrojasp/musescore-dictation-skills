---
name: choir-dictation
description: Convert spoken or dictated choir music (voices, notes, rhythms, lyrics, sections, in Spanish or English) into the choir text format used by choir-score-musescore.
---

# Choir dictation → choir text

The user dictates choir arrangements out loud (voice typing), usually in Spanish, often for three-part SAT choir (Soprano, Contralto, Tenor). The transcript is messy: no punctuation, words instead of symbols, speech-to-text mistakes, self-corrections. Turn it into the text format of the `choir-score-musescore` skill, show it, and only build the score after the user approves.

Read the `choir-score-musescore` skill first: its "Text format" section is the exact target syntax.

## Vocabulary

Notes (solfège or letters):

| Dicho | Escrito |
|---|---|
| do | C |
| re | D |
| mi | E |
| fa | F |
| sol | G |
| la | A |
| si | B |

- sostenido → `#`, bemol → `b`, becuadro / natural → `n`. Plain names follow the key signature (in Sol mayor, "fa" is F#), so write `F`; write `Fn` only for "fa natural/becuadro".
- Speech-to-text often writes "sí" for si, "mí" for mi, "el sol", "la" as an article. Inside a list of notes they are note names.

Octaves:

- Always write an octave number on the first note of each voice (C4 = do central). "Do central" = `C4`; "el la de arriba del do central" = `A4`. If it was not said, pick the natural octave for the voice (Soprano around C5, Contralto around G4, Tenor around A3 sounding) and list it under Dudas.
- After that, each note goes to the nearest octave (a 4th or less). "sube a" / "arriba" → `'` (next one above); "baja a" / "abajo" → `,` (next one below); "una octava arriba" of the same note → `'` too. A named octave ("sol cinco") → `G5`.

Rhythm (the duration stays until it changes, so write it only when it changes):

| Dicho | Escrito |
|---|---|
| redonda | `:1` |
| blanca | `:2` |
| negra | `:4` |
| corchea | `:8` |
| semicorchea | `:16` |
| con puntillo | add `.` (`:4.`, `:2.`) |
| silencio de negra / blanca… | `R:4`, `R:2`… |
| silencio de compás (in 4/4) | `R:1` |
| ligada a la siguiente / ligadura | `~` after the first note (same pitch) |
| calderón | `^` after the note |
| legato / ligadura de expresión de X a Y | `(` before X, `)` after Y |

Dynamics, as separate tokens before the note: pianissimo `pp`, piano `p`, mezzo piano `mp`, mezzo forte `mf`, forte `f`, fortissimo `ff`.

Not supported yet: tresillos, crescendos, cambios de compás o tonalidad a mitad de canción, primera y segunda casilla. If one is dictated, list it under Dudas so the user adds it in MuseScore.

Structure and shortcuts:

- "Soprano, compás uno: …" → voice lines `S:`, `A:` (contralto), `T:`. Other voicings: `S1 S2 A` (SSA), `S A T B` (SATB), `T1 T2 B` (TTB); set `Voices:`.
- "Sección A", "verso", "coro", "puente" → `[Nombre]` starting a block.
- "la contralto descansa" / "el tenor no canta en esta parte" → leave that voice out of the block (the converter fills rests).
- "mismo ritmo que la soprano: re, re, mi…" → copy the soprano's durations bar by bar and put the new pitches in order. If the number of pitches does not match, list it under Dudas.
- "la contralto hace la soprano una tercera abajo" (or sexta, octava…) → move each soprano note that many scale steps down inside the key, same rhythm. List it under Dudas as generated harmony to review.
- "igual que el verso" → copy that block's voice lines. If only the words change, prefer `Lyrics 2:` in the original block.
- "se repite" → `|:` … `:|`; "tres veces" → `:|x3`.

Lyrics:

- Write the dictated words as plain text on a `Lyrics:` line under the block (they apply to every voice). Add syllable hyphens only where automatic Spanish splitting would be wrong. Different words for one voice: `Lyrics T:`. Second verse: `Lyrics 2:`.
- "se alarga", "melisma", "en dos notas" → `_` after the syllable, one `_` per extra note.
- Sinalefa: when a word ends in a vowel and the next starts with a vowel and they share one note, join them with `~` (`san-to~es`). Apply it when the note count says so, and mention it.
- Accents and punctuation as they would be written (Señor, Él, amén).

Headers: título, subtítulo, compositor, arreglo, tono ("en Sol" → `Key: G`, "Re menor" → `Key: Dm`), compás ("tres cuartos" → 3/4, "seis por ocho" → 6/8), tempo ("negra a 72, solemne" → `Tempo: 72 Solemne`), acordes ("cifrado: Sol, Do, Re…" → a `Chords:` line per block, band-chart syntax). Defaults: `Voices: S A T`, `Piano: sí`, `Audio: sí`. Never invent a tempo or chords.

## Steps

1. The user may dictate a whole song or one piece at a time (one voice, one section). Keep a running chart across messages and always rebuild the full text.
2. Apply self-corrections ("no, perdón", "mejor dicho") to what came right before.
3. Validate before showing: run `python3 <choir-score-musescore folder>/choir2mscz.py chart.txt out --check`. Fix anything that is clearly a transcription slip. Turn remaining errors and every `Aviso` (notes outside the normal range, notes without lyrics) into Dudas.
4. Reply with:
   - The full choir text in one code block.
   - The check line (bars, and the starting note of each voice, e.g. "Soprano empieza en D4").
   - "Dudas:" with one short bullet per guess or warning. Leave it out if there were none.
   - One line asking whether to make the score or what to fix.
5. The user corrects by voice ("soprano compás 3, la segunda nota es mi"). Apply it, show the full text again, ask again.
6. When they approve ("ok", "dale", "sí", "hazlo", "pásalo a partitura"), follow the `choir-score-musescore` skill with the approved text.

## Example

Dictation:

> título santo en sol tres cuartos negra a 72 solemne sección A soprano empieza en re cuatro anacrusa de negra re luego sol la si do blanca si negra la sol fa sostenido sol blanca con puntillo con calderón doble barra contralto mismo ritmo re re re re re mi re do si do si con calderón tenor si tres si do re do sol la fa sostenido la re arriba con calderón letra santo santo santo es el señor dios cifrado sol y re, do y sol, la menor re siete, sol

Choir text:

```
Title: Santo
Voices: S A T
Key: G
Time: 3/4
Tempo: 72 Solemne

[A]
S: D4:4 | G A B | C:2 B:4 | A G F | G:2.^ ||
A: D4:4 | D D D | E:2 D:4 | C B C | B:2.^ ||
T: B3:4 | B C D | C:2 G:4 | A F A | D':2.^ ||
Chords: | G . D | C . G | Am D7 . | G |
Lyrics: San-to, san-to, san-to~es el Se-ñor Dios
```

Dudas: sinalefa "to~es" so that 10 syllables fit 10 notes.
