---
name: slash-chart-musescore
description: Turn a title, tempo, key and pipe-separated chord progression into a MuseScore 4 slash-notation band chart (.mscz). Use when the user pastes chords like '| G | D/F# | Em C |' for a band chart.
---

# Slash chart for MuseScore 4

The user writes chord charts for a band. They send a title, tempo and chords separated by pipes (typed, or produced from voice dictation by the `chart-dictation` skill). You produce a MuseScore 4 file with one treble staff filled with rhythmic slashes and the chord symbols placed on them, in a Real Book look (MuseJazz music font, MuseJazz Text for all text, jazz chord symbols). The user polishes the layout in MuseScore, so do not try to perfect the engraving and do not drive the MuseScore app with computer use unless asked.

The converter is `chart2mscz.py` in this skill's folder. It only needs Python 3 (no MuseScore installation).

## Input syntax

Header lines come first (English or Spanish keys work):

- `Title:` / `Título:`
- `Subtitle:` / `Subtítulo:` (optional)
- `Composer:` / `Compositor:` / `Artista:` (optional)
- `Tempo:` / `BPM:` → number plus optional text, e.g. `72 Balada`
- `Time:` / `Time Signature:` / `Compás:` → default 4/4. 6/8, 9/8, 12/8 use dotted-quarter slashes.
- `Key:` / `Tono:` → e.g. `Bb`, `F#m`. If missing, it is inferred from the first chord.
- `Style:` / `Estilo:` → default is the Real Book (MuseJazz) look. `Style: standard` gives MuseScore's default Leland engraving.

Body:

- `|` separates bars. Each input line becomes one system (line break).
- Several chords in a bar are spread evenly: `| C G |` = beats 1 and 3; `| C G D |` in 4/4 = 1, 3, 4.
- `.` or `/` is one beat with no new chord: `| Cm7 . F7 Ab |`. A bar of only `.` (or an empty `|  |`) is slashes with no chord.
- `%` alone in a bar → one-bar repeat sign (repeat the previous bar). It cannot be the first bar or share a bar with chords.
- `[Verso]`, `[A]`, `[Coro]` → rehearsal mark on the next bar.
- `|:` and `:|` → repeat barlines. `:|x3` → plays 3 times and prints "x3".
- `||` → double barline (hidden when the next bar starts a repeat). The last bar always gets a final barline.
- `N.C.` → no chord.
- Chord suffixes are passed to MuseScore as typed (m7, maj7, 7sus4, m7b5, add9, -7, etc.); slash chords like `D/F#` are supported.

## Steps

1. If the message is missing the title or the chords, ask once. Anything else uses the defaults above. Pasted text often loses or shifts line breaks (e.g. `Tempo: 72` then `Balada Key: Bb`, a header without a colon, or several `[Section]`s on one line). Normalize this yourself: tempo text belongs with the tempo, each `[Section]` starts a new line, and long sections keep the user's own breaks. Mention what you normalized in one short line. If the input is a spoken description rather than pipe text, use the `chart-dictation` skill first.
2. Write the normalized input to `chart.txt` in a working folder and run `python3 <this skill folder>/chart2mscz.py chart.txt "<Title>.mscz"`. Always output `.mscz`: the Real Book style lives in a `score_style.mss` inside the zip (MuseScore 4 ignores a `<Style>` block inside a bare .mscx). Error messages are in Spanish and name the bad chord or bar; fix obvious typos yourself, otherwise ask.
3. Give the `.mscz` to the user (save it where they can open it, e.g. their outputs folder or a folder they connected).
4. Reply in one or two sentences: bar count, key, and anything you had to interpret.

Optional check: to see the result, render it with MuseScore 4's command line (`mscore -o out.png file.mscz`; on Linux without a display set `QT_QPA_PLATFORM=offscreen`). Only do this when something looks risky (unusual meter, many split bars).
