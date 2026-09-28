import re
import sys
import zipfile
from fractions import Fraction
from xml.sax.saxutils import escape

STEP_TPC = {"F": 13, "C": 14, "G": 15, "D": 16, "A": 17, "E": 18, "B": 19}
MAJOR_FIFTHS = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7,
                "F": -1, "Bb": -2, "Eb": -3, "Ab": -4, "Db": -5, "Gb": -6, "Cb": -7}
MINOR_FIFTHS = {"A": 0, "E": 1, "B": 2, "F#": 3, "C#": 4, "G#": 5, "D#": 6, "A#": 7,
                "D": -1, "G": -2, "C": -3, "F": -4, "Bb": -5, "Eb": -6, "Ab": -7}
DUR_NAMES = {1: "whole", 2: "half", 4: "quarter", 8: "eighth", 16: "16th"}
PLACEHOLDERS = {".", "/"}
CHORD_RE = re.compile(r"^([A-G])([#b]?)(.*?)(?:/([A-G])([#b]?))?$")
JAZZ_TEXT_STYLES = ["default", "title", "subTitle", "composer", "lyricist", "translator", "tempo", "metronome",
                    "rehearsalMark", "staff", "system", "expression", "measureNumber", "repeatLeft", "repeatRight",
                    "frame", "header", "footer", "volta", "chordSymbolA", "chordSymbolB", "longInstrument",
                    "shortInstrument", "partInstrument", "tuplet", "textLine", "instrumentChange", "fingering",
                    "user1", "user2", "user3", "user4", "user5", "user6"]
JAZZ_EXTRA = {"musicalSymbolFont": "MuseJazz", "musicalTextFont": "MuseJazz Text", "chordStyle": "jazz",
              "chordDescriptionFile": "chords_jazz.xml", "chordSymbolAFontSize": "15", "chordSymbolBFontSize": "12",
              "titleFontSize": "28", "subTitleFontSize": "14", "tempoFontSize": "12", "tempoFontStyle": "1",
              "metronomeFontSize": "12", "rehearsalMarkFontSize": "14", "rehearsalMarkFontStyle": "1",
              "repeatLeftFontSize": "18"}
TOKEN_RE = re.compile(r"\|:|:\|(?:x\d+)?|\|\||\||\[[^\]]*\]|[^|\[\]:]+|:")


class ChartError(Exception):
    pass


def tpc(step, acc):
    return STEP_TPC[step] + (7 if acc == "#" else -7 if acc == "b" else 0)


def parse_chord(tok):
    if tok.upper() in ("N.C.", "NC", "N.C"):
        return {"nc": True}
    m = CHORD_RE.match(tok)
    if not m:
        raise ChartError(f"No entiendo el acorde '{tok}'")
    step, acc, name, bstep, bacc = m.groups()
    d = {"root": tpc(step, acc), "name": name}
    if bstep:
        d["base"] = tpc(bstep, bacc or "")
    return d


def key_fifths(key):
    key = key.strip()
    if not key:
        return 0
    m = re.match(r"^([A-G][#b]?)\s*(m|min|minor|menor)?$", key, re.I)
    if not m:
        raise ChartError(f"Tonalidad no reconocida: '{key}'")
    tonic = m.group(1)[0].upper() + m.group(1)[1:]
    table = MINOR_FIFTHS if m.group(2) else MAJOR_FIFTHS
    if tonic not in table:
        raise ChartError(f"Tonalidad no reconocida: '{key}'")
    return table[tonic]


def parse(text):
    meta = {"title": "", "subtitle": "", "composer": "", "tempo": "", "time": "4/4", "key": "", "style": "jazz"}
    aliases = {"titulo": "title", "título": "title", "subtitulo": "subtitle", "subtítulo": "subtitle",
               "compositor": "composer", "autor": "composer", "artist": "composer", "artista": "composer",
               "compas": "time", "compás": "time", "tono": "key", "tonalidad": "key", "bpm": "tempo",
               "estilo": "style", "fuente": "style", "font": "style", "time signature": "time"}
    lines = text.splitlines()
    body = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        hm = re.match(r"^([A-Za-zÁÉÍÓÚáéíóú ]+):\s*(.*)$", line)
        if hm and "|" not in line and not body:
            k = hm.group(1).strip().lower()
            k = aliases.get(k, k)
            if k in meta:
                meta[k] = hm.group(2).strip()
                continue
        body.append(line)

    bars = []
    pending_mark = None
    pending_start = False
    for li, line in enumerate(body):
        toks = [t for t in TOKEN_RE.findall(line)]
        prev_sep = None
        line_bars = []
        for i, t in enumerate(toks):
            if t.startswith("["):
                pending_mark = t[1:-1].strip()
                continue
            if t in ("|", "||", "|:") or t.startswith(":|"):
                if t.startswith(":|"):
                    if not line_bars:
                        if not bars:
                            raise ChartError("':|' sin compás antes")
                        target = bars[-1]
                    else:
                        target = line_bars[-1]
                    rm = re.match(r":\|x(\d+)", t)
                    target["end_repeat"] = int(rm.group(1)) if rm else 2
                elif t == "||":
                    tgt = line_bars[-1] if line_bars else (bars[-1] if bars else None)
                    if tgt is not None:
                        tgt["double"] = True
                elif t == "|:":
                    pending_start = True
                prev_sep = t
                continue
            if t == ":":
                raise ChartError(f"':' suelto en la línea: {line}")
            content = t.strip()
            if not content:
                nxt = toks[i + 1] if i + 1 < len(toks) else None
                if prev_sep == "|" and nxt == "|":
                    content = "."
                else:
                    continue
            bar = {"tokens": content.split(), "mark": pending_mark, "start_repeat": pending_start}
            pending_mark = None
            pending_start = False
            line_bars.append(bar)
            prev_sep = None
        if line_bars:
            line_bars[-1]["line_break"] = True
            bars.extend(line_bars)
    if not bars:
        raise ChartError("No encontré compases")
    bars[-1]["line_break"] = False
    if not meta["key"]:
        for bar in bars:
            first = next((t for t in bar["tokens"] if t not in PLACEHOLDERS and CHORD_RE.match(t)), None)
            if first:
                m = CHORD_RE.match(first)
                minor = m.group(3).startswith(("m", "-")) and not m.group(3).startswith("maj")
                guess = m.group(1) + m.group(2) + ("m" if minor else "")
                try:
                    key_fifths(guess)
                    meta["key"] = guess
                except ChartError:
                    pass
                break
    return meta, bars


def time_info(sig):
    m = re.match(r"^(\d+)\s*/\s*(\d+)$", sig.strip())
    if not m:
        raise ChartError(f"Compás no reconocido: '{sig}'")
    n, d = int(m.group(1)), int(m.group(2))
    if d == 8 and n % 3 == 0 and n > 3:
        return n, d, n // 3, Fraction(3, 8), DUR_NAMES[4], 1
    return n, d, n, Fraction(1, d), DUR_NAMES[d], 0


def place(tokens, beats):
    if any(t in PLACEHOLDERS for t in tokens) or len(tokens) == beats:
        if len(tokens) > beats:
            raise ChartError(f"Demasiados tiempos en el compás: {' '.join(tokens)}")
        return {i: t for i, t in enumerate(tokens) if t not in PLACEHOLDERS}
    n = len(tokens)
    if n > beats:
        raise ChartError(f"Demasiados acordes en el compás: {' '.join(tokens)}")
    base, extra = divmod(beats, n)
    out, pos = {}, 0
    for i, t in enumerate(tokens):
        out[pos] = t
        pos += base + (1 if i < extra else 0)
    return out


def harmony_xml(c, ind):
    if c.get("nc"):
        return f"{ind}<Harmony>\n{ind}  <name>N.C.</name>\n{ind}  </Harmony>\n"
    s = f"{ind}<Harmony>\n{ind}  <root>{c['root']}</root>\n"
    if c["name"]:
        s += f"{ind}  <name>{escape(c['name'])}</name>\n"
    if "base" in c:
        s += f"{ind}  <base>{c['base']}</base>\n"
    return s + f"{ind}  </Harmony>\n"


def style_mss(style):
    if style.strip().lower() in ("standard", "estandar", "estándar", "leland", "normal", "clasico", "clásico"):
        return ""
    lines = [f"    <{k}FontFace>MuseJazz Text</{k}FontFace>\n" for k in JAZZ_TEXT_STYLES]
    lines += [f"    <{k}>{v}</{k}>\n" for k, v in JAZZ_EXTRA.items()]
    return '<?xml version="1.0" encoding="UTF-8"?>\n<museScore version="4.40">\n  <Style>\n' + "".join(lines) + "    </Style>\n  </museScore>\n"


def build(meta, bars):
    n, d, beats, unit, dname, dots = time_info(meta["time"])
    fifths = key_fifths(meta["key"])
    pitch, ptpc = (70, 12) if fifths <= -1 else (72, 26) if fifths >= 7 else (71, 19)
    ind = "          "
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>\n<museScore version="4.40">\n  <Score>\n    <Division>480</Division>\n    <open>1</open>\n')
    out.append(f'    <metaTag name="workTitle">{escape(meta["title"])}</metaTag>\n')
    out.append(f'    <metaTag name="composer">{escape(meta["composer"])}</metaTag>\n')
    out.append('    <Part id="1">\n      <Staff id="1">\n        <StaffType group="pitched">\n          <name>stdNormal</name>\n          </StaffType>\n        </Staff>\n      <trackName></trackName>\n      <Instrument id="piano">\n        <longName></longName>\n        <shortName></shortName>\n        <trackName></trackName>\n        <instrumentId>keyboard.piano</instrumentId>\n        <Channel>\n          <program value="0"/>\n          <synti>Fluid</synti>\n          </Channel>\n        </Instrument>\n      </Part>\n')
    out.append('    <Staff id="1">\n')
    if meta["title"] or meta["subtitle"] or meta["composer"]:
        out.append('      <VBox>\n        <height>10</height>\n')
        for style, key in (("title", "title"), ("subtitle", "subtitle"), ("composer", "composer")):
            if meta[key]:
                out.append(f'        <Text>\n          <style>{style}</style>\n          <text>{escape(meta[key])}</text>\n          </Text>\n')
        out.append('        </VBox>\n')
    tempo_num = None
    tempo_text = ""
    if meta["tempo"]:
        tm = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(.*)$", meta["tempo"])
        if tm:
            tempo_num = float(tm.group(1))
            tempo_text = tm.group(2).strip()
        else:
            tempo_text = meta["tempo"]
    for bi, bar in enumerate(bars):
        out.append('      <Measure>\n')
        if bar.get("start_repeat"):
            out.append('        <startRepeat/>\n')
        if bar.get("end_repeat"):
            out.append(f'        <endRepeat>{bar["end_repeat"]}</endRepeat>\n')
        if bar.get("line_break"):
            out.append('        <LayoutBreak>\n          <subtype>line</subtype>\n          </LayoutBreak>\n')
        is_rep = bar["tokens"] == ["%"]
        if "%" in bar["tokens"] and not is_rep:
            raise ChartError(f"'%' debe ir solo en su compás: {' '.join(bar['tokens'])}")
        if is_rep and bi == 0:
            raise ChartError("El primer compás no puede ser '%'")
        if is_rep:
            out.append('        <measureRepeatCount>1</measureRepeatCount>\n')
        out.append('        <voice>\n')
        if is_rep:
            if bar.get("mark"):
                out.append(f'{ind}<RehearsalMark>\n{ind}  <text>{escape(bar["mark"])}</text>\n{ind}  </RehearsalMark>\n')
            if bar.get("end_repeat", 2) > 2:
                out.append(f'{ind}<StaffText>\n{ind}  <placement>above</placement>\n{ind}  <text>x{bar["end_repeat"]}</text>\n{ind}  </StaffText>\n')
            out.append(f'{ind}<MeasureRepeat>\n{ind}  <subtype>1</subtype>\n{ind}  <durationType>measure</durationType>\n{ind}  <duration>{n}/{d}</duration>\n{ind}  </MeasureRepeat>\n')
        if bi == 0:
            out.append(f'{ind}<Clef>\n{ind}  <concertClefType>G</concertClefType>\n{ind}  <transposingClefType>G</transposingClefType>\n{ind}  <isHeader>1</isHeader>\n{ind}  </Clef>\n')
            out.append(f'{ind}<KeySig>\n{ind}  <concertKey>{fifths}</concertKey>\n{ind}  </KeySig>\n')
            out.append(f'{ind}<TimeSig>\n{ind}  <sigN>{n}</sigN>\n{ind}  <sigD>{d}</sigD>\n{ind}  </TimeSig>\n')
        chords = {} if is_rep else {k: parse_chord(v) for k, v in place(bar["tokens"], beats).items()}
        for b in range(0 if is_rep else beats):
            if b == 0 and bar.get("mark"):
                out.append(f'{ind}<RehearsalMark>\n{ind}  <text>{escape(bar["mark"])}</text>\n{ind}  </RehearsalMark>\n')
            if b == 0 and bi == 0 and (tempo_num or tempo_text):
                if tempo_num:
                    qps = tempo_num * float(unit * 4) / 60
                    sym = "metNoteQuarterUp" if not dots else "metNoteQuarterUp</sym><sym>metAugmentationDot"
                    label = (f"{escape(tempo_text)} " if tempo_text else "") + f"<sym>{sym}</sym> = {int(tempo_num) if tempo_num.is_integer() else tempo_num}"
                    if d != 4 and not dots:
                        note_sym = {2: "metNoteHalfUp", 8: "metNote8thUp", 1: "metNoteWhole"}.get(d, "metNoteQuarterUp")
                        label = (f"{escape(tempo_text)} " if tempo_text else "") + f"<sym>{note_sym}</sym> = {int(tempo_num) if tempo_num.is_integer() else tempo_num}"
                    out.append(f'{ind}<Tempo>\n{ind}  <tempo>{float(qps):.6g}</tempo>\n{ind}  <followText>1</followText>\n{ind}  <text>{label}</text>\n{ind}  </Tempo>\n')
                else:
                    out.append(f'{ind}<Tempo>\n{ind}  <tempo>2</tempo>\n{ind}  <followText>0</followText>\n{ind}  <text>{escape(tempo_text)}</text>\n{ind}  </Tempo>\n')
            if b in chords:
                out.append(harmony_xml(chords[b], ind))
            if b == beats - 1 and bar.get("end_repeat", 2) > 2:
                out.append(f'{ind}<StaffText>\n{ind}  <placement>above</placement>\n{ind}  <text>x{bar["end_repeat"]}</text>\n{ind}  </StaffText>\n')
            out.append(f'{ind}<Chord>\n')
            if dots:
                out.append(f'{ind}  <dots>1</dots>\n')
            out.append(f'{ind}  <durationType>{dname}</durationType>\n{ind}  <noStem>1</noStem>\n')
            out.append(f'{ind}  <Note>\n{ind}    <pitch>{pitch}</pitch>\n{ind}    <tpc>{ptpc}</tpc>\n{ind}    <fixed>1</fixed>\n{ind}    <fixedLine>4</fixedLine>\n{ind}    <play>0</play>\n{ind}    <head>slash</head>\n{ind}    </Note>\n{ind}  </Chord>\n')
        if bi == len(bars) - 1:
            out.append(f'{ind}<BarLine>\n{ind}  <subtype>end</subtype>\n{ind}  </BarLine>\n')
        elif bar.get("double") and not bar.get("end_repeat") and not bars[bi + 1].get("start_repeat"):
            out.append(f'{ind}<BarLine>\n{ind}  <subtype>double</subtype>\n{ind}  </BarLine>\n')
        out.append('          </voice>\n        </Measure>\n')
    out.append('      </Staff>\n    </Score>\n  </museScore>\n')
    return "".join(out)


def write_mscz(mscx, mss, path):
    roots = ('    <rootfile full-path="score_style.mss"/>\n' if mss else "") + '    <rootfile full-path="score.mscx"/>\n'
    container = '<?xml version="1.0" encoding="UTF-8"?>\n<container>\n  <rootfiles>\n' + roots + '    </rootfiles>\n  </container>\n'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("META-INF/container.xml", container)
        if mss:
            z.writestr("score_style.mss", mss)
        z.writestr("score.mscx", mscx)


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: python3 chart2mscz.py entrada.txt salida.mscz")
    with open(sys.argv[1], encoding="utf-8") as f:
        text = f.read()
    try:
        meta, bars = parse(text)
        mscx = build(meta, bars)
    except ChartError as e:
        sys.exit(f"Error: {e}")
    write_mscz(mscx, style_mss(meta["style"]), sys.argv[2])
    print(f"{len(bars)} compases -> {sys.argv[2]}")


if __name__ == "__main__":
    main()
