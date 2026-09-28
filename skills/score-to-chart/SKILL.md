---
name: score-to-chart
description: Convert a full score, piano/vocal/guitar score or lead sheet (PDF or photos) into a compact slash chord chart for the band, via slash-chart-musescore.
---

# Score → slash chord chart

The user has a full score (piano/vocal/guitar songbook pages, a lead sheet, an orchestral score) and wants a band chart with only chord symbols over slashes. Read the score, write the chart text in the `slash-chart-musescore` format, and build the `.mscz` with that skill.

Defaults (ask only if the user wants something different):

- **Compact with repeats**: detect sections (Intro, Verso, Coro, Puente, Solo, Tag, Final…) and write each repeated 8/16-bar block once with `|:` … `:|` (or `:|x3`), in playing order. Sections that come back later are written again under their name (the converter has no D.S./Coda), so the chart reads top to bottom.
- **Anticipations on the next downbeat**: a chord printed over the last eighth (or last sixteenth) of a bar and tied over belongs to the next bar. Chords that clearly start mid-bar (beat 2, 3 or 4) keep their beat with `.` placeholders, e.g. `| Bb . C . |`.

## Reading the score

1. Render the pages to images. For a PDF: `pdftoppm -r 150 -png score.pdf page` (use `-r 200` if chord text is small). Look at a low-res overview of all pages first to see the layout, then read each page in halves (crop top/bottom) so the chord symbols are legible. Photos: read them directly; crop if needed.
2. For each system, list the bars and the chord symbols above the top staff. Place each chord by its x position between the barlines:
   - at or just after the barline → beat 1;
   - around the middle → beat 3 (in 4/4); quarter positions → beats 2 / 4;
   - over the last eighth / tied into the next bar → next bar's downbeat (see defaults).
   - A bar with no chord keeps the previous chord.
3. Use the printed bar numbers (boxed numbers every 5 bars, or at system starts) as checkpoints: after each page, confirm the running bar count matches them. If it doesn't, re-read that system.
4. Note the key signature, time signature, tempo marking, title and composer from page 1. Key: use the tonal center the chords point to (e.g. one flat + Dm/Gm/C/Bb progressions → `Key: Dm`).
5. Use lyrics and texture to find sections: where the verse text starts, where the chorus text starts, instrumental solos ("Sax", "Solo"), bars where everyone rests (`N.C.`).
6. Spell chords the way the chart format expects: `D(add9)` → `Dadd9`, `Gm7/D` stays, `B♭` → `Bb`, `C♯` → `C#`, `ø` → `m7b5`, `Δ` / `maj7` → `maj7`, minus sign → `m`.
7. If the score has no chord symbols (only notes), derive the harmony from the bass line and the accompaniment, and say clearly that it is an analysis, not printed chords. Mark uncertain bars under Dudas.

## Compacting

- Write the full bar-by-bar list first (internally), then find repeated blocks: two consecutive identical 8-bar blocks → one block with `|:` … `:|`; four → `:|x4`. Keep one-off bars (a 1-bar fill, a final hold, a rest before an a cappella pickup) as their own short line.
- Keep 4 bars per line. A bar that repeats the previous one inside a line can be `%`.
- Check: the number of played bars in the compact chart (counting repeats) must equal the original bar count. State both numbers.

## Steps

1. Read and transcribe as above.
2. Write the chart text to `chart.txt` and follow the `slash-chart-musescore` skill to build the `.mscz` (Real Book style by default). Render a PNG or PDF with MuseScore when available and look at it before delivering.
3. Deliver the `.mscz` (and PDF if rendered) plus the chart text.
4. Reply briefly: original bars → chart bars, structure found (e.g. Intro – Verso – Coro – Verso – Coro – Solo – Coro – Tag – Coro – Final), key, and any Dudas (unreadable chords, guessed beats, analysis instead of printed chords).

## Example

A 10-page piano/vocal/guitar scan, 120 bars, one flat, chords printed with guitar boxes:

```
Title: Al Que Está Sentado
Composer: Juan Salinas
Key: Dm
Time: 4/4
[Intro]
|: Gm7/D | Dadd9 :|
[Verso]
|: Gm7/D | Dadd9 | Gm7/D | Dadd9 |
| Bb | C | Am7 | Dm :|
[Coro]
|: Gm7 | C | Gm7 | C |
| Bb | C | Bb . C . | Dm :|
| Dm ||
[Verso 2]
|: Gm7/D | Dadd9 | Gm7/D | Dadd9 |
| Bb | C | Am7 | Dm :|
[Coro]
|: Gm7 | C | Gm7 | C |
| Bb | C | Bb . C . | Dm :|
[Solo Sax]
| Gm7/D | Dadd9 | Gm7/D | Dadd9 |
| Bb | C | Am7 . C . | Dm ||
[Coro]
|: Gm7 | C | Gm7 | C |
| Bb | C | Bb . C . | Dm :|
[Tag]
| Bb . C . | Dm | Bb . C . | Dm |
| % | N.C. | . ||
[Coro]
|: Gm7 | C | Gm7 | C |
| Bb | C | Bb . C . | Dm :|
[Final]
| Bb . C . | Dm | Bb . C . | Dm |
```

70 written bars, 120 played — matches the original.
