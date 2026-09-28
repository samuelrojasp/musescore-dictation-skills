import os
import re
import shutil
import subprocess
import sys
from fractions import Fraction
from xml.sax.saxutils import escape

STRONG = set("aeoáéóíú")
WEAK = set("iuü")
VOWELS = STRONG | WEAK
CLUSTERS = {"pl", "pr", "bl", "br", "fl", "fr", "gl", "gr", "cl", "cr", "dr", "tr", "kl", "kr"}
DIGRAPHS = {"ch", "ll", "rr"}


def _is_vowel(word, i):
    c = word[i].lower()
    if c in VOWELS:
        if c == "u" and i > 0 and word[i - 1].lower() in "qg" and i + 1 < len(word) and word[i + 1].lower() in "eiéí":
            return False
        return True
    if c == "y" and (i == len(word) - 1 or not _is_vowel_char(word[i + 1])) and i > 0 and _is_vowel_char(word[i - 1]):
        return True
    return False


def _is_vowel_char(c):
    return c.lower() in VOWELS


def _hiatus(a, b):
    a, b = a.lower(), b.lower()
    if a in STRONG - set("íú") and b in STRONG - set("íú"):
        return True
    if a in "íú" or b in "íú":
        return True
    if a == b:
        return True
    return False


def _nuclei(word):
    kinds = []
    for i in range(len(word)):
        kinds.append("V" if _is_vowel(word, i) else "C")
    groups = []
    i = 0
    while i < len(word):
        if kinds[i] == "V":
            j = i + 1
            while j < len(word) and kinds[j] == "V" and not _hiatus(word[j - 1], word[j]):
                j += 1
            groups.append(("V", i, j))
            i = j
        else:
            j = i
            while j < len(word) and kinds[j] == "C":
                j += 1
            groups.append(("C", i, j))
            i = j
    return groups


def _split_consonants(cons):
    low = cons.lower()
    units = []
    i = 0
    while i < len(low):
        if low[i:i + 2] in DIGRAPHS:
            units.append(cons[i:i + 2])
            i += 2
        else:
            units.append(cons[i])
            i += 1
    n = len(units)
    if n == 0:
        return "", ""
    if n == 1:
        return "", units[0]
    last2 = (units[-2] + units[-1]).lower()
    if n == 2:
        return ("", cons) if last2 in CLUSTERS else (units[0], units[1])
    if last2 in CLUSTERS:
        return "".join(units[:-2]), "".join(units[-2:])
    return "".join(units[:-1]), units[-1]


def silabear(word):
    if "-" in word:
        return [p for p in word.split("-") if p]
    core = re.match(r"^([^\wáéíóúüñÁÉÍÓÚÜÑ]*)(.*?)([^\wáéíóúüñÁÉÍÓÚÜÑ]*)$", word)
    pre, body, post = core.groups()
    if not body or not any(_is_vowel_char(c) for c in body):
        return [word]
    groups = _nuclei(body)
    sylls = []
    current = ""
    for gi, (kind, a, b) in enumerate(groups):
        seg = body[a:b]
        if kind == "V":
            if gi > 0 and groups[gi - 1][0] == "V":
                sylls.append(current)
                current = ""
            current += seg
            continue
        if not sylls and not current:
            current = seg
            continue
        has_next_vowel = any(k == "V" for k, _, _ in groups[gi + 1:])
        if not has_next_vowel:
            current += seg
            continue
        left, right = _split_consonants(seg)
        current += left
        sylls.append(current)
        current = right
    if current:
        if sylls and not any(_is_vowel_char(c) for c in current):
            sylls[-1] += current
        else:
            sylls.append(current)
    sylls[0] = pre + sylls[0]
    sylls[-1] = sylls[-1] + post
    return sylls


DIV = 96
LETTERS = "CDEFGAB"
LETTER_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
SHARPS_ORDER = "FCGDAEB"
MAJOR_FIFTHS = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7,
                "F": -1, "Bb": -2, "Eb": -3, "Ab": -4, "Db": -5, "Gb": -6, "Cb": -7}
MINOR_FIFTHS = {"A": 0, "E": 1, "B": 2, "F#": 3, "C#": 4, "G#": 5, "D#": 6, "A#": 7,
                "D": -1, "G": -2, "C": -3, "F": -4, "Bb": -5, "Eb": -6, "Ab": -7}
VOICES = {
    "S": ("Soprano", "S.", "voice.soprano", "G", 0, ("B", 4)),
    "S1": ("Soprano I", "S. I", "voice.soprano", "G", 0, ("C", 5)),
    "S2": ("Soprano II", "S. II", "voice.soprano", "G", 0, ("A", 4)),
    "A": ("Contralto", "C.", "voice.alto", "G", 0, ("G", 4)),
    "A1": ("Contralto I", "C. I", "voice.alto", "G", 0, ("A", 4)),
    "A2": ("Contralto II", "C. II", "voice.alto", "G", 0, ("F", 4)),
    "T": ("Tenor", "T.", "voice.tenor", "G8", 0, ("G", 3)),
    "T1": ("Tenor I", "T. I", "voice.tenor", "G8", 0, ("A", 3)),
    "T2": ("Tenor II", "T. II", "voice.tenor", "G8", 0, ("F", 3)),
    "BAR": ("Barítono", "Bar.", "voice.baritone", "F", 0, ("D", 3)),
    "B": ("Bajo", "B.", "voice.bass", "F", 0, ("C", 3)),
    "B1": ("Bajo I", "B. I", "voice.bass", "F", 0, ("D", 3)),
    "B2": ("Bajo II", "B. II", "voice.bass", "F", 0, ("A", 2)),
}
RANGES = {"S": (60, 81), "S1": (62, 81), "S2": (60, 79), "A": (53, 74), "A1": (55, 74), "A2": (53, 72),
          "T": (48, 69), "T1": (50, 69), "T2": (48, 67), "BAR": (43, 65), "B": (40, 64), "B1": (43, 64), "B2": (40, 62)}
DYNAMICS = {"ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "sfz", "fp"}
NOTE_RE = re.compile(r"^(\(?)([A-G])(##|bb|#|b|n)?([0-8])?([',]*)(?::(\d+)?(\.{0,2}))?(~?)(\^?)(\)?)$")
REST_RE = re.compile(r"^R(?::(\d+)?(\.{0,2}))?(\^?)$")
CHORD_RE = re.compile(r"^([A-G])([#b]?)(.*?)(?:/([A-G])([#b]?))?$")
KINDS = {"": "major", "m": "minor", "-": "minor", "7": "dominant", "maj7": "major-seventh", "M7": "major-seventh",
         "m7": "minor-seventh", "-7": "minor-seventh", "dim": "diminished", "dim7": "diminished-seventh",
         "aug": "augmented", "+": "augmented", "m7b5": "half-diminished", "6": "major-sixth", "m6": "minor-sixth",
         "9": "dominant-ninth", "maj9": "major-ninth", "m9": "minor-ninth", "11": "dominant-11th",
         "13": "dominant-13th", "sus4": "suspended-fourth", "sus": "suspended-fourth", "sus2": "suspended-second",
         "5": "power"}
TYPE_NAMES = {1: "whole", 2: "half", 4: "quarter", 8: "eighth", 16: "16th", 32: "32nd"}


class ChoirError(Exception):
    pass


def key_info(key):
    key = key.strip()
    if not key:
        return 0, "major"
    m = re.match(r"^([A-G][#b]?)\s*(m|min|minor|menor)?$", key, re.I)
    if not m:
        raise ChoirError(f"Tonalidad no reconocida: '{key}'")
    tonic = m.group(1)[0].upper() + m.group(1)[1:]
    table = MINOR_FIFTHS if m.group(2) else MAJOR_FIFTHS
    if tonic not in table:
        raise ChoirError(f"Tonalidad no reconocida: '{key}'")
    return table[tonic], ("minor" if m.group(2) else "major")


def key_alters(fifths):
    alt = {l: 0 for l in LETTERS}
    if fifths > 0:
        for l in SHARPS_ORDER[:fifths]:
            alt[l] = 1
    elif fifths < 0:
        for l in SHARPS_ORDER[::-1][:-fifths]:
            alt[l] = -1
    return alt


def time_info(sig):
    m = re.match(r"^(\d+)\s*/\s*(\d+)$", sig.strip())
    if not m:
        raise ChoirError(f"Compás no reconocido: '{sig}'")
    n, d = int(m.group(1)), int(m.group(2))
    bar = DIV * 4 * n // d
    if d == 8 and n % 3 == 0 and n > 3:
        beat = DIV * 3 // 2
    else:
        beat = DIV * 4 // d
    return n, d, bar, beat


def dur_ticks(den, dots):
    if den not in TYPE_NAMES:
        raise ChoirError(f"Duración no válida: {den}")
    base = Fraction(DIV * 4, den)
    total = base * (2 - Fraction(1, 2 ** dots))
    if total.denominator != 1:
        raise ChoirError(f"Duración demasiado corta: {den}")
    return int(total)


def parse_text(text):
    meta = {"title": "", "subtitle": "", "composer": "", "arranger": "", "tempo": "", "time": "4/4", "key": "",
            "voices": "S A T", "piano": "si", "audio": "si"}
    aliases = {"titulo": "title", "título": "title", "subtitulo": "subtitle", "subtítulo": "subtitle",
               "compositor": "composer", "autor": "composer", "arreglo": "arranger", "arreglista": "arranger",
               "compas": "time", "compás": "time", "time signature": "time", "tono": "key", "tonalidad": "key",
               "bpm": "tempo", "voces": "voices", "voice": "voices", "piano reduction": "piano", "reduccion": "piano",
               "reducción": "piano", "audios": "audio"}
    blocks = []
    cur = None
    header_done = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        hm = re.match(r"^([A-Za-zÁÉÍÓÚáéíóú ]+):\s*(.*)$", line)
        if hm and not header_done:
            k = hm.group(1).strip().lower()
            k = aliases.get(k, k)
            if k in meta:
                meta[k] = hm.group(2).strip()
                continue
        header_done = True
        mm = re.match(r"^\[([^\]]*)\]\s*$", line)
        if mm:
            cur = {"mark": mm.group(1).strip(), "voices": {}, "chords": None, "lyrics": {}}
            blocks.append(cur)
            continue
        lm = re.match(r"^([A-Za-z0-9ÁÉÍÓÚáéíóú ]+?)\s*:\s*(.*)$", line)
        if not lm:
            raise ChoirError(f"No entiendo la línea: {line}")
        label, content = lm.group(1).strip(), lm.group(2)
        if cur is None:
            cur = {"mark": None, "voices": {}, "chords": None, "lyrics": {}}
            blocks.append(cur)
        low = label.lower()
        if low in ("chords", "acordes", "cifrado"):
            cur["chords"] = content
            continue
        lyr = re.match(r"^(lyrics|letra|texto)(?:\s+([A-Za-z]+\d?))?(?:\s+(\d+))?$", low)
        if lyr:
            v = lyr.group(2).upper() if lyr.group(2) else None
            verse = int(lyr.group(3)) if lyr.group(3) else 1
            cur["lyrics"][(v, verse)] = cur["lyrics"].get((v, verse), "") + " " + content
            continue
        code = label.upper()
        if code not in VOICES:
            raise ChoirError(f"Voz desconocida: '{label}'")
        cur["voices"][code] = cur["voices"].get(code, "") + " " + content
    voices = meta["voices"].replace(",", " ").upper().split()
    for v in voices:
        if v not in VOICES:
            raise ChoirError(f"Voz desconocida en Voices: '{v}'")
    if not blocks:
        raise ChoirError("No encontré música")
    return meta, voices, blocks


def split_bars(s):
    toks = re.findall(r"\|:|:\|(?:x\d+)?|\|\||\||[^\s|]+", s)
    bars = []
    cur = []
    start_rep = False
    pending_start = False
    for t in toks:
        if t in ("|", "||", "|:") or t.startswith(":|"):
            if cur:
                bars.append({"tokens": cur, "start_repeat": pending_start})
                pending_start = False
                cur = []
            if t == "||" and bars:
                bars[-1]["double"] = True
            elif t.startswith(":|") and bars:
                rm = re.match(r":\|x(\d+)", t)
                bars[-1]["end_repeat"] = int(rm.group(1)) if rm else 2
            elif t == "|:":
                pending_start = True
            continue
        cur.append(t)
    if cur:
        bars.append({"tokens": cur, "start_repeat": pending_start})
    return bars


class VoiceState:
    def __init__(self, code, alters):
        ref = VOICES[code][5]
        self.prev = LETTERS.index(ref[0]) + 7 * ref[1]
        self.dur = (4, 0)
        self.alters = alters
        self.tie_pending = None


def parse_note_bar(tokens, st, where):
    events = []
    dyn = None
    for tok in tokens:
        if tok in DYNAMICS:
            dyn = tok
            continue
        rm = REST_RE.match(tok)
        if rm:
            if rm.group(1):
                st.dur = (int(rm.group(1)), len(rm.group(2)))
            elif rm.group(2):
                st.dur = (st.dur[0], len(rm.group(2)))
            den, dots = st.dur
            events.append({"rest": True, "den": den, "dots": dots, "ticks": dur_ticks(den, dots),
                           "fermata": bool(rm.group(3)), "dyn": dyn})
            dyn = None
            st.tie_pending = None
            continue
        nm = NOTE_RE.match(tok)
        if not nm:
            raise ChoirError(f"No entiendo la nota '{tok}' ({where})")
        slur_start, letter, acc, octv, marks, den, dots, tie, ferm, slur_stop = nm.groups()
        dots = dots or ""
        if den:
            st.dur = (int(den), len(dots))
        elif dots:
            st.dur = (st.dur[0], len(dots))
        idx = LETTERS.index(letter)
        if octv is not None:
            best = idx + 7 * int(octv)
        else:
            ups, downs = marks.count("'"), marks.count(",")
            cands = [idx + 7 * o for o in range(0, 10)]
            if ups:
                best = min(c for c in cands if c > st.prev) + 7 * (ups - 1)
            elif downs:
                best = max(c for c in cands if c < st.prev) - 7 * (downs - 1)
            else:
                best = min(cands, key=lambda c: abs(c - st.prev))
        st.prev = best
        octave = best // 7
        if acc is None:
            alter = st.alters[letter]
        else:
            alter = {"#": 1, "##": 2, "b": -1, "bb": -2, "n": 0}[acc]
        midi = 12 * (octave + 1) + LETTER_PC[letter] + alter
        ev = {"rest": False, "step": letter, "alter": alter, "octave": octave, "midi": midi,
              "den": st.dur[0], "dots": st.dur[1], "ticks": dur_ticks(*st.dur), "tie_start": bool(tie),
              "tie_stop": False, "slur_start": bool(slur_start), "slur_stop": bool(slur_stop),
              "fermata": bool(ferm), "dyn": dyn}
        dyn = None
        if st.tie_pending is not None:
            if st.tie_pending != midi:
                raise ChoirError(f"Ligadura entre notas distintas ({where})")
            ev["tie_stop"] = True
        st.tie_pending = midi if tie else None
        events.append(ev)
    return events


def lyric_units(text):
    units = []
    for word in text.split():
        if word == "_":
            units.append({"melisma": True})
            continue
        pieces = word.split("~")
        sylls_per_piece = [silabear(p) for p in pieces]
        merged = []
        roles = []
        for pi, sy in enumerate(sylls_per_piece):
            for si, s in enumerate(sy):
                if pi > 0 and si == 0:
                    merged[-1] = merged[-1] + "‿" + s
                    roles[-1] = (roles[-1][0], si == len(sy) - 1)
                    continue
                merged.append(s)
                roles.append((si == 0 and pi == 0 or si == 0, si == len(sy) - 1))
        for s, (first, last) in zip(merged, roles):
            if first and last:
                syl = "single"
            elif first:
                syl = "begin"
            elif last:
                syl = "end"
            else:
                syl = "middle"
            units.append({"text": s, "syllabic": syl})
    return units


def assign_lyrics(events, units, verse, where, warnings):
    slots = [e for e in events if not e["rest"] and not e["tie_stop"]]
    ui = 0
    last = None
    for e in slots:
        if ui >= len(units):
            break
        u = units[ui]
        if u.get("melisma"):
            if last is not None and last["syllabic"] in ("single", "end"):
                last["extend"] = True
            ui += 1
            continue
        lyr = {"verse": verse, "text": u["text"], "syllabic": u["syllabic"]}
        e.setdefault("lyrics", []).append(lyr)
        last = lyr
        ui += 1
    rest_units = [u for u in units[ui:] if not u.get("melisma")]
    if rest_units:
        extra = " ".join(u["text"] for u in rest_units)
        raise ChoirError(f"Sobran sílabas en {where}: '{extra}' ({len(rest_units)} de más)")
    if ui < len(slots):
        warnings.append(f"{where}: {len(slots) - ui} nota(s) sin letra al final")


def parse_chords(line, nbars, beats_per_bar, beat_ticks, where):
    bars = [b for b in re.split(r"\|+:?|:?\|+", line) if b.strip()]
    if len(bars) != nbars:
        raise ChoirError(f"Acordes: {len(bars)} compases pero la música tiene {nbars} ({where})")
    out = []
    for b in bars:
        toks = b.split()
        if any(t in (".", "/") for t in toks) or len(toks) == beats_per_bar:
            pos = {i: t for i, t in enumerate(toks) if t not in (".", "/", "%")}
        else:
            base, extra = divmod(beats_per_bar, len(toks))
            pos, p = {}, 0
            for i, t in enumerate(toks):
                pos[p] = t
                p += base + (1 if i < extra else 0)
        chords = []
        for beat, t in pos.items():
            if t.upper() in ("N.C.", "NC"):
                chords.append((beat * beat_ticks, None))
                continue
            m = CHORD_RE.match(t)
            if not m:
                raise ChoirError(f"No entiendo el acorde '{t}' ({where})")
            chords.append((beat * beat_ticks, m.groups()))
        out.append(chords)
    return out


def build_model(meta, voices, blocks):
    fifths, mode = key_info(meta["key"])
    alters = key_alters(fifths)
    n, d, bar_ticks, beat_ticks = time_info(meta["time"])
    beats_per_bar = bar_ticks // beat_ticks
    states = {v: VoiceState(v, alters) for v in voices}
    measures = []
    warnings = []
    for bi, blk in enumerate(blocks):
        name = blk["mark"] or f"bloque {bi + 1}"
        parsed = {}
        counts = set()
        for v in voices:
            if v in blk["voices"]:
                parsed[v] = split_bars(blk["voices"][v])
                counts.add(len(parsed[v]))
        if not parsed:
            raise ChoirError(f"La sección '{name}' no tiene notas")
        if len(counts) != 1:
            detail = ", ".join(f"{v}={len(b)}" for v, b in parsed.items())
            raise ChoirError(f"Las voces no tienen la misma cantidad de compases en '{name}': {detail}")
        nb = counts.pop()
        chords = [[] for _ in range(nb)]
        if blk["chords"]:
            given = len([b for b in re.split(r"\|+:?|:?\|+", blk["chords"]) if b.strip()])
            if bi == 0 and given == nb - 1:
                chords = [[]] + parse_chords(blk["chords"], nb - 1, beats_per_bar, beat_ticks, name)
            else:
                chords = parse_chords(blk["chords"], nb, beats_per_bar, beat_ticks, name)
        voice_events = {}
        for v in voices:
            if v in parsed:
                evs = []
                for k, b in enumerate(parsed[v]):
                    evs.append(parse_note_bar(b["tokens"], states[v], f"{VOICES[v][0]}, '{name}', compás {k + 1}"))
                voice_events[v] = evs
            else:
                voice_events[v] = None
        for v in voices:
            if voice_events[v] is None:
                continue
            flat = [e for bar in voice_events[v] for e in bar]
            verses = sorted({verse for (lv, verse) in blk["lyrics"] if lv in (None, v)})
            for verse in verses:
                text = blk["lyrics"].get((v, verse)) or blk["lyrics"].get((None, verse))
                assign_lyrics(flat, lyric_units(text), verse, f"{VOICES[v][0]}, '{name}', estrofa {verse}", warnings)
        ref = next(v for v in voices if v in parsed)
        for k in range(nb):
            first_global = len(measures) == 0
            meas = {"voices": {}, "chords": chords[k], "mark": blk["mark"] if k == 0 else None,
                    "start_repeat": parsed[ref][k].get("start_repeat", False),
                    "end_repeat": parsed[ref][k].get("end_repeat"), "double": parsed[ref][k].get("double", False)}
            lengths = {}
            for v in voices:
                if voice_events[v] is None:
                    meas["voices"][v] = None
                    continue
                evs = voice_events[v][k]
                meas["voices"][v] = evs
                lengths[v] = sum(e["ticks"] for e in evs)
            if len(set(lengths.values())) != 1:
                detail = ", ".join(f"{VOICES[v][0]}={Fraction(t, beat_ticks)}" for v, t in lengths.items())
                raise ChoirError(f"Las voces no suman lo mismo en '{name}', compás {k + 1} (tiempos: {detail})")
            lengths = set(lengths.values())
            length = lengths.pop()
            is_last = bi == len(blocks) - 1 and k == nb - 1
            if length != bar_ticks:
                if first_global and length < bar_ticks:
                    meas["pickup"] = True
                elif is_last and length < bar_ticks:
                    meas["short"] = True
                else:
                    beats = Fraction(length, beat_ticks)
                    raise ChoirError(f"El compás {k + 1} de '{name}' dura {beats} tiempos y debería durar {beats_per_bar}")
            meas["length"] = length
            for v in voices:
                if meas["voices"][v] is None:
                    continue
                lo, hi = RANGES[v]
                for e in meas["voices"][v]:
                    if not e["rest"] and not (lo <= e["midi"] <= hi):
                        warnings.append(f"{VOICES[v][0]}, '{name}', compás {k + 1}: {e['step']}{e['octave']} está fuera del registro normal (¿octava equivocada?)")
            for v in voices:
                if meas["voices"][v] is None:
                    meas["voices"][v] = [{"rest": True, "whole": True, "ticks": length, "fermata": False, "dyn": None}]
            measures.append(meas)
    return {"fifths": fifths, "mode": mode, "n": n, "d": d, "bar": bar_ticks, "beat": beat_ticks,
            "measures": measures, "warnings": warnings}


def harmony_xml(ch, offset):
    off = f"<offset>{offset}</offset>" if offset else ""
    if ch is None:
        return f'<harmony print-frame="no"><root><root-step>C</root-step></root><kind text="N.C.">none</kind>{off}</harmony>'
    step, acc, suffix, bstep, bacc = ch
    alter = {"#": 1, "b": -1}.get(acc, 0)
    kind = KINDS.get(suffix, "other" if suffix else "major")
    s = f'<harmony print-frame="no"><root><root-step>{step}</root-step>'
    if alter:
        s += f"<root-alter>{alter}</root-alter>"
    s += f'</root><kind text="{escape(suffix, {chr(34): "&quot;"})}">{kind}</kind>'
    if bstep:
        s += f"<bass><bass-step>{bstep}</bass-step>"
        if bacc:
            s += f"<bass-alter>{ {'#': 1, 'b': -1}[bacc]}</bass-alter>"
        s += "</bass>"
    return s + off + "</harmony>"


def note_xml(e, voice_num, staff, with_lyrics, stem=None):
    if e.get("whole"):
        return f'<note><rest measure="yes"/><duration>{e["ticks"]}</duration><voice>{voice_num}</voice>' + (f"<staff>{staff}</staff>" if staff else "") + "</note>"
    s = "<note>"
    if e["rest"]:
        s += "<rest/>"
    else:
        s += f"<pitch><step>{e['step']}</step>" + (f"<alter>{e['alter']}</alter>" if e["alter"] else "") + f"<octave>{e['octave']}</octave></pitch>"
    s += f"<duration>{e['ticks']}</duration>"
    if not e["rest"]:
        if e["tie_stop"]:
            s += '<tie type="stop"/>'
        if e["tie_start"]:
            s += '<tie type="start"/>'
    s += f"<voice>{voice_num}</voice><type>{TYPE_NAMES[e['den']]}</type>" + "<dot/>" * e["dots"]
    if stem:
        s += f"<stem>{stem}</stem>"
    if staff:
        s += f"<staff>{staff}</staff>"
    nots = ""
    if not e["rest"]:
        if e["tie_stop"]:
            nots += '<tied type="stop"/>'
        if e["tie_start"]:
            nots += '<tied type="start"/>'
        if e["slur_start"]:
            nots += '<slur type="start" number="1"/>'
        if e["slur_stop"]:
            nots += '<slur type="stop" number="1"/>'
    if e.get("fermata"):
        nots += "<fermata/>"
    if nots:
        s += f"<notations>{nots}</notations>"
    if with_lyrics:
        for l in e.get("lyrics", []):
            s += f'<lyric number="{l["verse"]}"><syllabic>{l["syllabic"]}</syllabic><text>{escape(l["text"])}</text>'
            if l.get("extend"):
                s += "<extend/>"
            s += "</lyric>"
    return s + "</note>"


def dyn_xml(dyn, staff):
    st = f"<staff>{staff}</staff>" if staff else ""
    return f'<direction placement="below"><direction-type><dynamics><{dyn}/></dynamics></direction-type>{st}</direction>'


def voice_stream(events, voice_num, staff, with_lyrics, chords=None, stem=None, dyns=True):
    out = []
    t = 0
    pending = sorted(chords or [], key=lambda c: c[0])
    for e in events:
        end = t + e["ticks"]
        while pending and pending[0][0] < end:
            ct, ch = pending.pop(0)
            out.append(harmony_xml(ch, max(0, ct - t)))
        if dyns and e.get("dyn"):
            out.append(dyn_xml(e["dyn"], staff))
        out.append(note_xml(e, voice_num, staff, with_lyrics, stem))
        t = end
    return "".join(out), t


def clef_xml(kind, number=None):
    num = f' number="{number}"' if number else ""
    if kind == "G":
        return f"<clef{num}><sign>G</sign><line>2</line></clef>"
    if kind == "G8":
        return f"<clef{num}><sign>G</sign><line>2</line><clef-octave-change>-1</clef-octave-change></clef>"
    return f"<clef{num}><sign>F</sign><line>4</line></clef>"


def barline_xml(meas, is_last, location):
    if location == "left":
        if meas["start_repeat"]:
            return '<barline location="left"><bar-style>heavy-light</bar-style><repeat direction="forward"/></barline>'
        return ""
    if meas.get("end_repeat"):
        return f'<barline location="right"><bar-style>light-heavy</bar-style><repeat direction="backward" times="{meas["end_repeat"]}"/></barline>'
    if is_last:
        return '<barline location="right"><bar-style>light-heavy</bar-style></barline>'
    if meas["double"]:
        return '<barline location="right"><bar-style>light-light</bar-style></barline>'
    return ""


def tempo_direction(meta, model, staff=None):
    if not meta["tempo"]:
        return ""
    tm = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(.*)$", meta["tempo"])
    st = f"<staff>{staff}</staff>" if staff else ""
    compound = model["beat"] == DIV * 3 // 2
    unit = "quarter" if model["d"] <= 4 or compound else "eighth"
    if model["d"] == 2:
        unit = "half"
    dot = "<beat-unit-dot/>" if compound else ""
    if tm:
        bpm = float(tm.group(1))
        words = tm.group(2).strip()
        qpm = bpm * (1.5 if compound else {"half": 2, "quarter": 1, "eighth": 0.5}[unit])
        s = '<direction placement="above">'
        if words:
            s += f'<direction-type><words font-weight="bold">{escape(words)} </words></direction-type>'
        s += f"<direction-type><metronome><beat-unit>{unit}</beat-unit>{dot}<per-minute>{int(bpm) if bpm.is_integer() else bpm}</per-minute></metronome></direction-type>{st}<sound tempo=\"{qpm:g}\"/></direction>"
        return s
    return f'<direction placement="above"><direction-type><words font-weight="bold">{escape(meta["tempo"])}</words></direction-type>{st}</direction>'


def build_xml(meta, voices, model, piano=True, levels=None):
    parts = []
    plist = ['<part-group type="start" number="1"><group-symbol>bracket</group-symbol><group-barline>yes</group-barline></part-group>']
    for i, v in enumerate(voices):
        name, abbr, sound = VOICES[v][0], VOICES[v][1], VOICES[v][2]
        pid = f"P{i + 1}"
        plist.append(f'<score-part id="{pid}"><part-name>{escape(name)}</part-name><part-abbreviation>{escape(abbr)}</part-abbreviation>'
                     f'<score-instrument id="{pid}-I1"><instrument-name>{escape(name)}</instrument-name><instrument-sound>{sound}</instrument-sound></score-instrument>'
                     f'<midi-instrument id="{pid}-I1"><midi-channel>{i + 1}</midi-channel><midi-program>53</midi-program></midi-instrument></score-part>')
    plist.append('<part-group type="stop" number="1"/>')
    if piano:
        pid = f"P{len(voices) + 1}"
        plist.append(f'<score-part id="{pid}"><part-name>Piano</part-name><part-abbreviation>Pno.</part-abbreviation>'
                     f'<score-instrument id="{pid}-I1"><instrument-name>Piano</instrument-name><instrument-sound>keyboard.piano</instrument-sound></score-instrument>'
                     f'<midi-instrument id="{pid}-I1"><midi-channel>{len(voices) + 1}</midi-channel><midi-program>1</midi-program></midi-instrument></score-part>')
    ms = model["measures"]
    time_xml = f"<time><beats>{model['n']}</beats><beat-type>{model['d']}</beat-type></time>"
    key_xml = f"<key><fifths>{model['fifths']}</fifths><mode>{model['mode']}</mode></key>"
    for i, v in enumerate(voices):
        pid = f"P{i + 1}"
        body = []
        num = 0
        for mi, m in enumerate(ms):
            is_last = mi == len(ms) - 1
            implicit = ' implicit="yes"' if m.get("pickup") else ""
            mnum = 0 if m.get("pickup") else (num := num + 1)
            s = f'<measure number="{mnum}"{implicit}>' + barline_xml(m, is_last, "left")
            if mi == 0:
                s += f"<attributes><divisions>{DIV}</divisions>{key_xml}{time_xml}{clef_xml(VOICES[v][3])}</attributes>"
                if i == 0:
                    s += tempo_direction(meta, model)
            if mi == 0 and levels:
                s += f'<direction placement="below"><direction-type><dynamics><{levels[v]}/></dynamics></direction-type></direction>'
            if i == 0 and m["mark"]:
                s += f'<direction placement="above"><direction-type><rehearsal>{escape(m["mark"])}</rehearsal></direction-type></direction>'
            stream, _ = voice_stream(m["voices"][v], 1, None, True, m["chords"] if i == 0 else None, dyns=not levels)
            s += stream + barline_xml(m, is_last, "right") + "</measure>"
            body.append(s)
        parts.append(f'<part id="{pid}">' + "".join(body) + "</part>")
    if piano:
        pid = f"P{len(voices) + 1}"
        order = list(voices)
        split = (len(order) + 1) // 2
        upper, lower = order[:split], order[split:]
        low_clef = "F" if any(VOICES[v][3] in ("F", "G8") for v in lower) else "G"
        body = []
        num = 0
        for mi, m in enumerate(ms):
            is_last = mi == len(ms) - 1
            implicit = ' implicit="yes"' if m.get("pickup") else ""
            mnum = 0 if m.get("pickup") else (num := num + 1)
            s = f'<measure number="{mnum}"{implicit}>' + barline_xml(m, is_last, "left")
            if mi == 0:
                s += f"<attributes><divisions>{DIV}</divisions>{key_xml}{time_xml}<staves>2</staves>{clef_xml('G', 1)}{clef_xml(low_clef, 2)}</attributes>"
            vn = 1
            first = True
            for staff, group in ((1, upper), (2, lower)):
                for gi, v in enumerate(group):
                    if not first:
                        s += f"<backup><duration>{m['length']}</duration></backup>"
                    first = False
                    stem = None
                    if len(group) > 1:
                        stem = "up" if gi == 0 else "down"
                    evs = []
                    for e in m["voices"][v]:
                        if gi > 0 and e.get("fermata"):
                            e = dict(e, fermata=False)
                        evs.append(e)
                    stream, _ = voice_stream(evs, vn, staff, False, m["chords"] if (staff == 1 and gi == 0) else None, stem, dyns=False)
                    s += stream
                    vn += 1
            s += barline_xml(m, is_last, "right") + "</measure>"
            body.append(s)
        parts.append(f'<part id="{pid}">' + "".join(body) + "</part>")
    ident = ""
    creators = ""
    if meta["composer"]:
        creators += f'<creator type="composer">{escape(meta["composer"])}</creator>'
    if meta["arranger"]:
        creators += f'<creator type="arranger">{escape(meta["arranger"])}</creator>'
    if creators:
        ident = f"<identification>{creators}</identification>"
    credits = ""
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n'
            f'<score-partwise version="4.0"><work><work-title>{escape(meta["title"])}</work-title></work>{ident}{credits}'
            f'<part-list>{"".join(plist)}</part-list>{"".join(parts)}</score-partwise>\n')


def title_vbox(meta):
    texts = []
    if meta["title"]:
        texts.append(("title", meta["title"]))
    if meta["subtitle"]:
        texts.append(("subtitle", meta["subtitle"]))
    right = [x for x in (meta["composer"], f"Arr. {meta['arranger']}" if meta["arranger"] else "") if x]
    if right:
        texts.append(("composer", "\n".join(right)))
    if not texts:
        return ""
    body = "".join(f"        <Text>\n          <style>{st}</style>\n          <text>{escape(tx)}</text>\n          </Text>\n" for st, tx in texts)
    return "      <VBox>\n        <height>10</height>\n" + body + "        </VBox>\n"


def patch_mscz(path, meta):
    import zipfile
    with zipfile.ZipFile(path) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    out = []
    for info, data in items:
        if info.filename.endswith(".mscx"):
            x = data.decode("utf-8")
            x = re.sub(r"<metaTag name=\"workTitle\">.*?</metaTag>", f'<metaTag name="workTitle">{escape(meta["title"])}</metaTag>', x)
            x = re.sub(r"<metaTag name=\"composer\">.*?</metaTag>", f'<metaTag name="composer">{escape(meta["composer"])}</metaTag>', x)
            vbox = title_vbox(meta)
            first_staff = re.search(r"\n    <Staff id=\"1\">\n", x)
            m = re.search(r"      <VBox>.*?</VBox>\n", x[first_staff.end():], re.S)
            if m and m.start() == 0:
                x = x[:first_staff.end()] + vbox + x[first_staff.end() + m.end():]
            else:
                x = x[:first_staff.end()] + vbox + x[first_staff.end():]
            data = x.encode("utf-8")
        out.append((info, data))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in out:
            z.writestr(info.filename, data)


def find_mscore():
    for c in (os.environ.get("MSCORE"), shutil.which("mscore4portable"), shutil.which("mscore"), shutil.which("musescore")):
        if c and os.path.exists(c):
            return c
    return None


def run_mscore(mscore, src, dst):
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    r = subprocess.run([mscore, "-o", dst, src], env=env, capture_output=True, text=True, timeout=300)
    if not os.path.exists(dst) and not any(f.startswith(os.path.splitext(os.path.basename(dst))[0]) for f in os.listdir(os.path.dirname(dst) or ".")):
        raise ChoirError(f"MuseScore no pudo exportar {dst}")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("salida_dir")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    with open(a.entrada, encoding="utf-8") as f:
        text = f.read()
    try:
        meta, voices, blocks = parse_text(text)
        model = build_model(meta, voices, blocks)
    except ChoirError as e:
        sys.exit(f"Error: {e}")
    piano = meta["piano"].strip().lower() not in ("no", "false", "0", "sin")
    audio = meta["audio"].strip().lower() not in ("no", "false", "0", "sin")
    firsts = []
    for v in voices:
        for m in model["measures"]:
            evs = [e for e in m["voices"][v] if not e["rest"]]
            if evs:
                e = evs[0]
                firsts.append(f"{VOICES[v][0]} empieza en {e['step']}{({1: '#', 2: '##', -1: 'b', -2: 'bb'}).get(e['alter'], '')}{e['octave']}")
                break
    print(f"{len(model['measures'])} compases; " + "; ".join(firsts))
    for w in model["warnings"]:
        print(f"Aviso: {w}")
    if a.check:
        return
    os.makedirs(a.salida_dir, exist_ok=True)
    title = re.sub(r'[\\/:*?"<>|]', "", meta["title"] or "Coro").strip() or "Coro"
    base = os.path.join(a.salida_dir, title)
    with open(base + ".musicxml", "w", encoding="utf-8") as f:
        f.write(build_xml(meta, voices, model, piano=piano))
    mscore = find_mscore()
    if not mscore:
        print(f"MuseScore no disponible: entrego {base}.musicxml")
        return
    run_mscore(mscore, base + ".musicxml", base + ".mscz")
    patch_mscz(base + ".mscz", meta)
    run_mscore(mscore, base + ".mscz", base + ".pdf")
    print(f"-> {base}.mscz, {base}.pdf")
    if audio:
        tmp = os.path.join(a.salida_dir, ".audio")
        os.makedirs(tmp, exist_ok=True)
        variants = [("Todos", None, piano)]
        for v in voices:
            lv = {w: "p" for w in voices}
            lv[v] = "ff"
            variants.append((VOICES[v][0], lv, False))
        for label, lv, with_piano in variants:
            src = os.path.join(tmp, f"{label}.musicxml")
            with open(src, "w", encoding="utf-8") as f:
                f.write(build_xml(meta, voices, model, piano=with_piano, levels=lv))
            run_mscore(mscore, src, f"{base} - {label}.mp3")
        shutil.rmtree(tmp, ignore_errors=True)
        print("-> audios: " + ", ".join(f"{title} - {l}.mp3" for l, *_ in variants))


if __name__ == "__main__":
    main()
