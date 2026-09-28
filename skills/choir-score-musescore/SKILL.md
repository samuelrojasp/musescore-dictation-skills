---
name: choir-score-musescore
description: Turn choir text (SAT/SSA/SATB voices with notes, rhythms, lyrics, chords) into a MuseScore 4 score (.mscz + PDF), with a piano reduction and per-voice rehearsal MP3s.
---

# Choir score for MuseScore 4

The user arranges music for choir, often three-part SAT (Soprano, Contralto, Tenor). They give choir text (typed, or produced from dictation by the `choir-dictation` skill). You produce:

- `<Título>.mscz`: one staff per voice (tenor in treble-8 clef) with lyrics under each voice, chord symbols over the top voice, a bracket for the choir, and a piano reduction (upper voices in the right hand, lower voices in the left hand).
- `<Título>.pdf`
- Rehearsal MP3s: `<Título> - Todos.mp3` (everyone + piano) and one per voice (`<Título> - Soprano.mp3`…) where that voice is loud and the others soft.

The user polishes the engraving in MuseScore, so do not try to perfect the layout and do not drive the MuseScore app with computer use unless asked.

The converter is `choir2mscz.py` in this skill's folder (Python 3 + the MuseScore 4 command line).

## Text format

Header lines (English or Spanish keys):

- `Title:` / `Título:`, `Subtitle:` / `Subtítulo:`, `Composer:` / `Compositor:`, `Arranger:` / `Arreglo:`
- `Key:` / `Tono:` (`G`, `Bb`, `Em`…). `Time:` / `Compás:` (default 4/4). `Tempo:` number + optional words (`72 Solemne`).
- `Voices:` / `Voces:` default `S A T`. Codes: `S S1 S2 A A1 A2 T T1 T2 BAR B B1 B2` (A = Contralto, B = Bajo, BAR = Barítono).
- `Piano:` sí/no (default sí). `Audio:` sí/no (default sí).

Body, in blocks:

- `[Nombre]` starts a block and puts a rehearsal mark on its first bar. Text without a `[...]` line is one unnamed block.
- `S:`, `A:`, `T:` … voice lines. Repeating a label in the same block continues the line. A voice left out of a block gets rests there.
- `Chords:` / `Acordes:` bar by bar with the band-chart syntax (`| G . D | Am D7 . |`, `.` = beat with no new chord). It may skip a pickup bar.
- `Lyrics:` / `Letra:` words for every voice; `Lyrics 2:` second verse; `Lyrics T:` / `Lyrics T 2:` only for one voice.

Notes:

- Uppercase letter + optional accidental (`#`, `b`, `##`, `bb`, `n` = natural). Without an accidental the key signature applies (in G, `F` is F#).
- Optional octave digit right after it: `C4` = middle C, `D5`. Without it the note goes to the nearest octave from the previous note of that voice (within a 4th). `'` = the next one above, `,` = the next one below. Always give an octave on each voice's first note.
- Duration after a colon: `:1` `:2` `:4` `:8` `:16` `:32`, dots `:4.` `:2.`. It stays until changed; `:.` only changes the dots.
- `~` after a note ties it to the next note (same pitch). `^` fermata. `(` before and `)` after for a slur.
- Rests: `R`, `R:2`, `R:4.`, `R^`.
- Dynamics as separate tokens before a note: `ppp pp p mp mf f ff fff sfz fp`.
- Bars: `|`, `||` double bar, `|:` … `:|` repeat, `:|x3`.
- A short first bar is a pickup (anacrusa); the last bar may be short too. Every other bar must be complete, and all voices must have the same number of bars and the same length per bar.
- Not supported yet: tuplets, hairpins, time/key changes mid-piece, volta brackets.

Lyrics:

- Plain words are split into syllables with Spanish rules (diphthongs, hiatus with accents, consonant clusters). Write hyphens to force a split: `a-lé-lu-ya`.
- One syllable per note; rests and tied continuation notes take none.
- `_` = melisma: the previous syllable continues on the next note (one `_` per extra note).
- `~` = sinalefa: `san-to~es` puts "to‿es" on one note.
- Too many syllables is an error; too few leaves the last notes without text (warning).

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
   If none is available, the script still writes a `.musicxml` that MuseScore opens; deliver that and say so.
2. Write the choir text to `chart.txt` in a working folder.
3. Run `python3 <this skill folder>/choir2mscz.py chart.txt out --check`. Errors and `Aviso` lines are in Spanish and name the voice, section and bar. Fix clear slips yourself; otherwise ask. Pay attention to out-of-range warnings (usually a wrong octave) and the "empieza en" line.
4. Run `python3 <this skill folder>/choir2mscz.py chart.txt out` (about 5 seconds per MP3).
5. Give the user the `.mscz`, `.pdf` and MP3s (not the .musicxml), saved where they can open them.
6. Reply in one or two sentences: bars, voices, anything interpreted, and any remaining warnings.

To check the engraving yourself, render a PNG: `$MSCORE -o page.png out/<Título>.mscz` (on Linux without a display, prefix `QT_QPA_PLATFORM=offscreen`) and look at `page-1.png`.
