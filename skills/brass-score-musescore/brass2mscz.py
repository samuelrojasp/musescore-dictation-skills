import os
import re
import shutil
import subprocess
import sys
import zipfile
from fractions import Fraction
from xml.sax.saxutils import escape

DIV = 96
LETTERS = "CDEFGAB"
LETTER_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
SHARPS_ORDER = "FCGDAEB"
MAJOR_FIFTHS = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7,
                "F": -1, "Bb": -2, "Eb": -3, "Ab": -4, "Db": -5, "Gb": -6, "Cb": -7}
MINOR_FIFTHS = {"A": 0, "E": 1, "B": 2, "F#": 3, "C#": 4, "G#": 5, "D#": 6, "A#": 7,
                "D": -1, "G": -2, "C": -3, "F": -4, "Bb": -5, "Eb": -6, "Ab": -7}
INSTR = {
    "TP": ("Trompetas 1 y 2", "Tpts.", "brass.trumpet.bflat", "G", (-1, -2, 0), ("G", 4), (52, 82)),
    "TP1": ("Trompeta 1", "Tpt. 1", "brass.trumpet.bflat", "G", (-1, -2, 0), ("A", 4), (52, 82)),
    "TP2": ("Trompeta 2", "Tpt. 2", "brass.trumpet.bflat", "G", (-1, -2, 0), ("F", 4), (52, 80)),
    "AS": ("Saxofón alto", "Sax. A.", "wind.reed.saxophone.alto", "G", (-5, -9, 0), ("E", 4), (49, 80)),
    "TS": ("Saxofón tenor", "Sax. T.", "wind.reed.saxophone.tenor", "G", (-1, -2, -1), ("B", 3), (44, 75)),
    "BS": ("Saxofón barítono", "Sax. B.", "wind.reed.saxophone.baritone", "G", (-5, -9, -1), ("E", 3), (37, 68)),
    "TB": ("Trombón", "Tbn.", "brass.trombone", "F", (0, 0, 0), ("D", 3), (40, 77)),
}
DYNAMICS = {"ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "sfz", "fp"}
NOTE_RE = re.compile(r"^(\(?)([A-G])(##|bb|#|b|n)?([0-8])?([',]*)(?::(\d+)?(\.{0,2}))?(~?)([>!]*)(\^?)(\)?)$")
REST_RE = re.compile(r"^R(?::(\d+)?(\.{0,2}))?(\^?)$")
MULTI_RE = re.compile(r"^R\*(\d+)$")
TYPE_NAMES = {1: "whole", 2: "half", 4: "quarter", 8: "eighth", 16: "16th", 32: "32nd"}


class BrassError(Exception):
    pass


def key_info(key):
    key = key.strip()
    if not key:
        return 0, "major"
    m = re.match(r"^([A-G][#b]?)\s*(m|min|minor|menor)?$", key, re.I)
    if not m:
        raise BrassError(f"Tonalidad no reconocida: '{key}'")
    tonic = m.group(1)[0].upper() + m.group(1)[1:]
    table = MINOR_FIFTHS if m.group(2) else MAJOR_FIFTHS
    if tonic not in table:
        raise BrassError(f"Tonalidad no reconocida: '{key}'")
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
        raise BrassError(f"Compás no reconocido: '{sig}'")
    n, d = int(m.group(1)), int(m.group(2))
    bar = DIV * 4 * n // d
    beat = DIV * 3 // 2 if d == 8 and n % 3 == 0 and n > 3 else DIV * 4 // d
    return n, d, bar, beat


def dur_ticks(den, dots):
    if den not in TYPE_NAMES:
        raise BrassError(f"Duración no válida: {den}")
    total = Fraction(DIV * 4, den) * (2 - Fraction(1, 2 ** dots))
    if total.denominator != 1:
        raise BrassError(f"Duración demasiado corta: {den}")
    return int(total)


def written_key(fifths, code):
    dia, chrom, octv = INSTR[code][4]
    s = -chrom - 12 * octv
    d = -dia - 7 * octv
    f = fifths + 7 * s - 12 * d
    shift = 0
    if f > 6:
        f -= 12
        shift = 1
    elif f < -6:
        f += 12
        shift = -1
    return f, shift


def to_written(e, code, shift):
    dia, chrom, octv = INSTR[code][4]
    cd = LETTERS.index(e["step"]) + 7 * e["octave"]
    wd = cd - dia - 7 * octv + shift
    wm = e["midi"] - chrom - 12 * octv
    letter = LETTERS[wd % 7]
    octave = wd // 7
    alter = wm - (12 * (octave + 1) + LETTER_PC[letter])
    return letter, alter, octave


def parse_text(text):
    meta = {"title": "", "subtitle": "", "composer": "", "arranger": "", "tempo": "", "time": "4/4", "key": "",
            "instruments": "TP AS TS TB", "size": "grande"}
    aliases = {"titulo": "title", "título": "title", "subtitulo": "subtitle", "subtítulo": "subtitle",
               "compositor": "composer", "autor": "composer", "arreglo": "arranger", "arreglista": "arranger",
               "compas": "time", "compás": "time", "time signature": "time", "tono": "key", "tonalidad": "key",
               "bpm": "tempo", "instrumentos": "instruments", "tamaño": "size", "tamano": "size"}
    blocks = []
    cur = None
    header_done = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        hm = re.match(r"^([A-Za-zÁÉÍÓÚáéíóúñ ]+):\s*(.*)$", line)
        if hm and not header_done:
            k = aliases.get(hm.group(1).strip().lower(), hm.group(1).strip().lower())
            if k in meta:
                meta[k] = hm.group(2).strip()
                continue
        header_done = True
        mm = re.match(r"^\[([^\]]*)\]\s*$", line)
        if mm:
            cur = {"mark": mm.group(1).strip(), "parts": {}}
            blocks.append(cur)
            continue
        lm = re.match(r"^([A-Za-z0-9]+)\s*:\s*(.*)$", line)
        if not lm:
            raise BrassError(f"No entiendo la línea: {line}")
        code = lm.group(1).upper()
        if code not in INSTR:
            raise BrassError(f"Instrumento desconocido: '{lm.group(1)}'")
        if cur is None:
            cur = {"mark": None, "parts": {}}
            blocks.append(cur)
        cur["parts"][code] = cur["parts"].get(code, "") + " " + lm.group(2)
    instruments = meta["instruments"].replace(",", " ").upper().split()
    for c in instruments:
        if c not in INSTR:
            raise BrassError(f"Instrumento desconocido en Instruments: '{c}'")
    if not blocks:
        raise BrassError("No encontré música")
    return meta, instruments, blocks


def split_bars(s):
    toks = re.findall(r"\|:|:\|(?:x\d+)?|\|\||\||[^\s|]+", s)
    bars = []
    cur = []
    pending_start = False
    for t in toks:
        if t in ("|", "||", "|:") or t.startswith(":|"):
            if cur:
                mm = MULTI_RE.match(cur[0]) if len(cur) == 1 else None
                if mm:
                    for i in range(int(mm.group(1))):
                        bars.append({"tokens": [], "multi": True, "start_repeat": pending_start and i == 0})
                else:
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
        mm = MULTI_RE.match(cur[0]) if len(cur) == 1 else None
        if mm:
            for i in range(int(mm.group(1))):
                bars.append({"tokens": [], "multi": True, "start_repeat": pending_start and i == 0})
        else:
            bars.append({"tokens": cur, "start_repeat": pending_start})
    return bars


class PartState:
    def __init__(self, code, alters):
        ref = INSTR[code][5]
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
            raise BrassError(f"No entiendo la nota '{tok}' ({where})")
        slur_start, letter, acc, octv, marks, den, dots, tie, arts, ferm, slur_stop = nm.groups()
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
        alter = st.alters[letter] if acc is None else {"#": 1, "##": 2, "b": -1, "bb": -2, "n": 0}[acc]
        midi = 12 * (octave + 1) + LETTER_PC[letter] + alter
        ev = {"rest": False, "step": letter, "alter": alter, "octave": octave, "midi": midi,
              "den": st.dur[0], "dots": st.dur[1], "ticks": dur_ticks(*st.dur), "tie_start": bool(tie),
              "tie_stop": False, "slur_start": bool(slur_start), "slur_stop": bool(slur_stop),
              "fermata": bool(ferm), "accent": ">" in arts, "staccato": "!" in arts, "dyn": dyn}
        dyn = None
        if st.tie_pending is not None:
            if st.tie_pending != midi:
                raise BrassError(f"Ligadura entre notas distintas ({where})")
            ev["tie_stop"] = True
        st.tie_pending = midi if tie else None
        events.append(ev)
    return events


def build_model(meta, instruments, blocks):
    fifths, mode = key_info(meta["key"])
    alters = key_alters(fifths)
    n, d, bar_ticks, beat_ticks = time_info(meta["time"])
    beats_per_bar = bar_ticks // beat_ticks
    states = {c: PartState(c, alters) for c in instruments}
    measures = []
    warnings = []
    for bi, blk in enumerate(blocks):
        name = blk["mark"] or f"bloque {bi + 1}"
        parsed = {c: split_bars(blk["parts"][c]) for c in instruments if c in blk["parts"]}
        for c in blk["parts"]:
            if c not in instruments:
                raise BrassError(f"'{c}' aparece en '{name}' pero no está en Instruments")
        if not parsed:
            raise BrassError(f"La sección '{name}' no tiene notas")
        counts = {c: len(b) for c, b in parsed.items()}
        if len(set(counts.values())) != 1:
            detail = ", ".join(f"{INSTR[c][0]}={k}" for c, k in counts.items())
            raise BrassError(f"Los instrumentos no tienen la misma cantidad de compases en '{name}': {detail}")
        nb = next(iter(counts.values()))
        events = {}
        for c in instruments:
            if c in parsed:
                events[c] = [None if b.get("multi") else parse_note_bar(b["tokens"], states[c], f"{INSTR[c][0]}, '{name}', compás {k + 1}")
                             for k, b in enumerate(parsed[c])]
            else:
                events[c] = None
        ref = next(c for c in instruments if c in parsed)
        for k in range(nb):
            first_global = len(measures) == 0
            rb = parsed[ref][k]
            meas = {"parts": {}, "mark": blk["mark"] if k == 0 else None, "start_repeat": rb.get("start_repeat", False),
                    "end_repeat": rb.get("end_repeat"), "double": rb.get("double", False)}
            lengths = {}
            for c in instruments:
                evs = events[c][k] if events[c] is not None else None
                meas["parts"][c] = evs
                if evs is not None:
                    lengths[c] = sum(e["ticks"] for e in evs)
            if len(set(lengths.values())) > 1:
                detail = ", ".join(f"{INSTR[c][0]}={Fraction(t, beat_ticks)}" for c, t in lengths.items())
                raise BrassError(f"Los instrumentos no suman lo mismo en '{name}', compás {k + 1} (tiempos: {detail})")
            length = next(iter(lengths.values())) if lengths else bar_ticks
            is_last = bi == len(blocks) - 1 and k == nb - 1
            if length != bar_ticks:
                if first_global and length < bar_ticks:
                    meas["pickup"] = True
                elif is_last and length < bar_ticks:
                    meas["short"] = True
                else:
                    raise BrassError(f"El compás {k + 1} de '{name}' dura {Fraction(length, beat_ticks)} tiempos y debería durar {beats_per_bar}")
            meas["length"] = length
            for c in instruments:
                evs = meas["parts"][c]
                if evs is None:
                    meas["parts"][c] = [{"rest": True, "whole": True, "ticks": length, "fermata": False, "dyn": None}]
                    continue
                lo, hi = INSTR[c][6]
                for e in evs:
                    if not e["rest"] and not (lo <= e["midi"] <= hi):
                        warnings.append(f"{INSTR[c][0]}, '{name}', compás {k + 1}: {e['step']}{ {1: '#', 2: '##', -1: 'b', -2: 'bb'}.get(e['alter'], '')}{e['octave']} (sonido real) está fuera del registro cómodo (¿octava equivocada?)")
            measures.append(meas)
    return {"fifths": fifths, "mode": mode, "n": n, "d": d, "bar": bar_ticks, "beat": beat_ticks,
            "measures": measures, "warnings": warnings}


def note_xml(e, code, shift):
    if e.get("whole"):
        return f'<note><rest measure="yes"/><duration>{e["ticks"]}</duration><voice>1</voice></note>'
    s = "<note>"
    if e["rest"]:
        s += "<rest/>"
    else:
        letter, alter, octave = to_written(e, code, shift)
        s += f"<pitch><step>{letter}</step>" + (f"<alter>{alter}</alter>" if alter else "") + f"<octave>{octave}</octave></pitch>"
    s += f"<duration>{e['ticks']}</duration>"
    if not e["rest"]:
        if e["tie_stop"]:
            s += '<tie type="stop"/>'
        if e["tie_start"]:
            s += '<tie type="start"/>'
    s += f"<voice>1</voice><type>{TYPE_NAMES[e['den']]}</type>" + "<dot/>" * e["dots"]
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
        arts = ("<accent/>" if e.get("accent") else "") + ("<staccato/>" if e.get("staccato") else "")
        if arts:
            nots += f"<articulations>{arts}</articulations>"
    if e.get("fermata"):
        nots += "<fermata/>"
    if nots:
        s += f"<notations>{nots}</notations>"
    return s + "</note>"


def clef_xml(kind):
    if kind == "G":
        return "<clef><sign>G</sign><line>2</line></clef>"
    return "<clef><sign>F</sign><line>4</line></clef>"


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


def tempo_direction(meta, model):
    if not meta["tempo"]:
        return ""
    tm = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(.*)$", meta["tempo"])
    compound = model["beat"] == DIV * 3 // 2
    unit = "half" if model["d"] == 2 else ("quarter" if model["d"] <= 4 or compound else "eighth")
    dot = "<beat-unit-dot/>" if compound else ""
    if tm:
        bpm = float(tm.group(1))
        words = tm.group(2).strip()
        qpm = bpm * (1.5 if compound else {"half": 2, "quarter": 1, "eighth": 0.5}[unit])
        s = '<direction placement="above">'
        if words:
            s += f'<direction-type><words font-weight="bold">{escape(words)} </words></direction-type>'
        return s + f'<direction-type><metronome><beat-unit>{unit}</beat-unit>{dot}<per-minute>{int(bpm) if bpm.is_integer() else bpm}</per-minute></metronome></direction-type><sound tempo="{qpm:g}"/></direction>'
    return f'<direction placement="above"><direction-type><words font-weight="bold">{escape(meta["tempo"])}</words></direction-type></direction>'


def build_xml(meta, instruments, model):
    plist = []
    parts = []
    for i, c in enumerate(instruments):
        name, abbr, sound = INSTR[c][0], INSTR[c][1], INSTR[c][2]
        pid = f"P{i + 1}"
        plist.append(f'<score-part id="{pid}"><part-name>{escape(name)}</part-name><part-abbreviation>{escape(abbr)}</part-abbreviation>'
                     f'<score-instrument id="{pid}-I1"><instrument-name>{escape(name)}</instrument-name><instrument-sound>{sound}</instrument-sound></score-instrument></score-part>')
        wf, shift = written_key(model["fifths"], c)
        dia, chrom, octv = INSTR[c][4]
        tr = ""
        if dia or chrom or octv:
            tr = f"<transpose><diatonic>{dia}</diatonic><chromatic>{chrom}</chromatic>" + (f"<octave-change>{octv}</octave-change>" if octv else "") + "</transpose>"
        body = []
        num = 0
        ms = model["measures"]
        for mi, m in enumerate(ms):
            is_last = mi == len(ms) - 1
            implicit = ' implicit="yes"' if m.get("pickup") else ""
            mnum = 0 if m.get("pickup") else (num := num + 1)
            s = f'<measure number="{mnum}"{implicit}>' + barline_xml(m, is_last, "left")
            if mi == 0:
                s += (f"<attributes><divisions>{DIV}</divisions><key><fifths>{wf}</fifths><mode>{model['mode']}</mode></key>"
                      f"<time><beats>{model['n']}</beats><beat-type>{model['d']}</beat-type></time>{clef_xml(INSTR[c][3])}{tr}</attributes>")
                if i == 0:
                    s += tempo_direction(meta, model)
            if i == 0 and m["mark"]:
                s += f'<direction placement="above"><direction-type><rehearsal>{escape(m["mark"])}</rehearsal></direction-type></direction>'
            for e in m["parts"][c]:
                if e.get("dyn"):
                    s += f'<direction placement="below"><direction-type><dynamics><{e["dyn"]}/></dynamics></direction-type></direction>'
                s += note_xml(e, c, shift)
            s += barline_xml(m, is_last, "right") + "</measure>"
            body.append(s)
        parts.append(f'<part id="{pid}">' + "".join(body) + "</part>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n'
            f'<score-partwise version="4.0"><work><work-title>{escape(meta["title"])}</work-title></work>'
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
    sizes = {"normal": None, "grande": "2.1", "muy grande": "2.5", "extra grande": "2.5"}
    spatium = sizes.get(meta["size"].strip().lower(), "2.1")
    with zipfile.ZipFile(path) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    out = []
    for info, data in items:
        if info.filename.endswith(".mscx"):
            x = data.decode("utf-8")
            x = re.sub(r"<metaTag name=\"workTitle\">.*?</metaTag>", f'<metaTag name="workTitle">{escape(meta["title"])}</metaTag>', x)
            x = re.sub(r"<metaTag name=\"composer\">.*?</metaTag>", f'<metaTag name="composer">{escape(meta["composer"])}</metaTag>', x)
            x = re.sub(r"(<StaffType group=\"pitched\">\s*<name>stdNormal</name>)", r"\1\n          <noteheadScheme>name-pitch</noteheadScheme>", x)
            vbox = title_vbox(meta)
            first_staff = re.search(r"\n    <Staff id=\"1\">\n", x)
            m = re.search(r"      <VBox>.*?</VBox>\n", x[first_staff.end():], re.S)
            if m and m.start() == 0:
                x = x[:first_staff.end()] + vbox + x[first_staff.end() + m.end():]
            else:
                x = x[:first_staff.end()] + vbox + x[first_staff.end():]
            data = x.encode("utf-8")
        elif info.filename.endswith(".mss") and spatium:
            data = re.sub(r"<Spatium>[^<]*</Spatium>", f"<Spatium>{spatium}</Spatium>", data.decode("utf-8")).encode("utf-8")
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
    subprocess.run([mscore, "-o", dst, src], env=env, capture_output=True, text=True, timeout=300)
    if not os.path.exists(dst):
        raise BrassError(f"MuseScore no pudo exportar {dst}")


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
        meta, instruments, blocks = parse_text(text)
        model = build_model(meta, instruments, blocks)
    except BrassError as e:
        sys.exit(f"Error: {e}")
    firsts = []
    for c in instruments:
        for m in model["measures"]:
            evs = [e for e in m["parts"][c] if not e["rest"]]
            if evs:
                e = evs[0]
                acc = {1: "#", 2: "##", -1: "b", -2: "bb"}
                wl, wa, wo = to_written(e, c, written_key(model["fifths"], c)[1])
                firsts.append(f"{INSTR[c][0]} empieza en {e['step']}{acc.get(e['alter'], '')}{e['octave']} real ({wl}{acc.get(wa, '')}{wo} escrito)")
                break
    print(f"{len(model['measures'])} compases; " + "; ".join(firsts))
    for w in model["warnings"]:
        print(f"Aviso: {w}")
    if a.check:
        return
    os.makedirs(a.salida_dir, exist_ok=True)
    title = re.sub(r'[\\/:*?"<>|]', "", meta["title"] or "Vientos").strip() or "Vientos"
    base = os.path.join(a.salida_dir, title)
    with open(base + ".musicxml", "w", encoding="utf-8") as f:
        f.write(build_xml(meta, instruments, model))
    mscore = find_mscore()
    if not mscore:
        print(f"MuseScore no disponible: entrego {base}.musicxml (sin nombres en las cabezas)")
        return
    run_mscore(mscore, base + ".musicxml", base + ".mscz")
    patch_mscz(base + ".mscz", meta)
    run_mscore(mscore, base + ".mscz", base + ".pdf")
    print(f"-> {base}.mscz, {base}.pdf")


if __name__ == "__main__":
    main()
