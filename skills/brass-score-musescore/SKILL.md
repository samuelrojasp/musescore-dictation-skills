---
name: brass-score-musescore
description: Turn horn-section text in concert pitch (trumpets, alto sax, tenor sax, baritone sax, trombone) into a transposed MuseScore 4 score (.mscz + PDF) with the letter names printed inside the noteheads.
---

# Horn-section score for MuseScore 4

A typical horn section: two trumpets in unison (B♭), alto sax (E♭), tenor sax (B♭) and trombone. The players are not strong sight readers, so every note shows its letter name inside the notehead (C, D, F♯…). The user writes in concert pitch; the script transposes each part to its written pitch and key, so the names in the heads are the notes each player reads and fingers.

You produce `<Título>.mscz` and `<Título>.pdf`: a full score in transposed view, bigger staff size, note names in the heads, title and "Arr." credit. The user polishes it in MuseScore and can extract parts there. Do not drive the MuseScore app with computer use unless asked.

The converter is `brass2mscz.py` in this skill's folder (Python 3 + the MuseScore 4 command line).

## Text format

Header lines (English or Spanish keys):

- `Title:` / `Título:`, `Subtitle:`, `Composer:` / `Compositor:`, `Arranger:` / `Arreglo:`
- `Key:` / `Tono:` concert key (`Bb`, `Eb`, `Gm`…). `Time:` / `Compás:` (default 4/4). `Tempo:` number + optional words.
- `Instruments:` / `Instrumentos:` default `TP AS TS TB`. Codes: `TP` Trompetas 1 y 2 (unison), `TP1`, `TP2`, `AS` Saxofón alto, `TS` Saxofón tenor, `BS` Saxofón barítono, `TB` Trombón.
- `Size:` / `Tamaño:` `grande` (default), `muy grande`, or `normal`.

Body, in blocks:

- `[Nombre]` starts a block with a rehearsal mark. Lines `TP:`, `AS:`, `TS:`, `TB:` (repeat a label to continue). An instrument left out of a block gets rests.

Notes, always in concert pitch:

- Uppercase letter + optional accidental (`#`, `b`, `##`, `bb`, `n`). Without an accidental the concert key signature applies.
- Optional octave digit (`C4` = middle C). Without it: nearest octave to the previous note (within a 4th); `'` = next one above, `,` = next one below. Always give an octave on each instrument's first note.
- Duration after a colon: `:1 :2 :4 :8 :16 :32`, dots `:4.`. It stays until changed.
- After the note: `~` tie to the next (same pitch), `>` accent, `!` staccato, `^` fermata. `(` before and `)` after for a slur. `F5:8>!` works, as does `(D5:4` … `G)`.
- Rests: `R`, `R:2`, `R:4.`; `R*8` alone between barlines = 8 bars of rest.
- Dynamics as separate tokens before a note: `ppp pp p mp mf f ff fff sfz fp`.
- Bars: `|`, `||`, `|:` … `:|`, `:|x3`. A short first bar is a pickup; the last bar may be short. All instruments need the same number of bars and the same length per bar.
- Not supported yet: tuplets, glissandos, falls, hairpins, mid-piece key or time changes, volta brackets.

## Steps

1. Find the MuseScore 4 command line and export it as `MSCORE`:
   - macOS: `/Applications/MuseScore 4.app/Contents/MacOS/mscore`
   - Windows: `C:\Program Files\MuseScore 4\bin\MuseScore4.exe`
   - Linux: `mscore` / `musescore` on PATH. In a Linux sandbox without it:
     ```
     curl -sSL -o ms.AppImage https://github.com/musescore/MuseScore/releases/download/v4.4.4/MuseScore-Studio-4.4.4.243461245-x86_64.AppImage && chmod +x ms.AppImage && ./ms.AppImage --appimage-extract >/dev/null
     apt-get install -y -qq libopengl0 libegl1 libgl1 libxkbcommon0 libfontconfig1 libdbus-1-3 libnss3 >/dev/null
     export MSCORE=$PWD/squashfs-root/bin/mscore4portable
     ```
   Without MuseScore the script only writes a `.musicxml` (no note names in the heads); deliver it and say so.
2. Write the text to `chart.txt` in a working folder.
3. Run `python3 <this skill folder>/brass2mscz.py chart.txt out --check`. It prints each instrument's first note in real and written pitch. Errors and `Aviso` lines (notes outside the comfortable range, usually a wrong octave) are in Spanish and name the instrument, section and bar. Fix clear slips; otherwise ask.
4. Run `python3 <this skill folder>/brass2mscz.py chart.txt out`.
5. Give the user the `.mscz` and `.pdf`, saved where they can open them.
6. Reply in one or two sentences: bars, instruments, written keys if useful, anything interpreted, remaining warnings.

To check the result yourself: `$MSCORE -o page.png out/<Título>.mscz` (on Linux without a display, prefix `QT_QPA_PLATFORM=offscreen`) and look at `page-1.png`.

How it works: the script writes MusicXML with written pitches and a `<transpose>` per instrument (keys moved to the nearest enharmonic, e.g. C♯ → D♭, with notes respelled), MuseScore converts it, and the script patches the .mscz to add `<noteheadScheme>name-pitch</noteheadScheme>` to every staff, the title frame, and a larger `<Spatium>`.
