"""
Транскрипция монофонической записи → ноты → MIDI + MusicXML + транспозиция.
Чистый numpy + stdlib, БЕЗ librosa/ML. Демо на чистом моно (см. §9c ТЗ).
Переиспользует низкоуровневый pitch-трекинг из analysis.py.
"""

import io
import struct
import numpy as np

from analysis import _read_wav, _acf_pitch_conf, _hz_to_midi_cents

# Транспозиция: сколько полутонов прибавить к КОНЦЕРТНОЙ (звучащей) высоте,
# чтобы получить ПИСАНУЮ ноту для инструмента. Зеркалит логику тюнера.
# key -> (подпись, полутонов)
INSTRUMENTS = {
    "trumpet": ("Труба B♭", 2),
    "concert": ("Concert (как звучит)", 0),
    "trombone": ("Тромбон", 0),
    "tenorsax": ("Тенор-сакс B♭", 14),
    "altosax": ("Альт-сакс E♭", 9),
    "clarinet": ("Кларнет B♭", 2),
    "contrabass": ("Контрабас", 12),  # звучит на октаву ниже письма
    "guitar": ("Гитара", 12),  # звучит на октаву ниже письма
    "piano": ("Фортепиано", 0),
}

NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"]


def note_name(midi):
    return NOTE_NAMES[midi % 12] + str(midi // 12 - 1)


# ================== ТРАНСКРИПЦИЯ ==================
def transcribe(wav_path, fmin=70.0, fmax=1500.0, min_ms=55):
    """WAV → список нот {midi, start, dur, conf} + общая уверенность.
    min_ms низкий, чтобы ловить короткие украшающие ноты (форшлаги)."""
    data, sr = _read_wav(wav_path)
    win, hop = 2048, 512
    if len(data) < win:
        return {"ok": False, "reason": "too_short", "notes": []}

    frames = []  # (midi|None, strength)
    for start in range(0, len(data) - win, hop):
        f0, st = _acf_pitch_conf(data[start : start + win], sr, fmin, fmax)
        frames.append((_hz_to_midi_cents(f0)[0] if f0 > 0 else None, st))

    sec_per_hop = hop / sr
    min_frames = max(2, int((min_ms / 1000.0) / sec_per_hop))

    notes = []
    cur_m, cur_st, cur_start = None, [], 0

    def flush():
        if cur_m is not None and len(cur_st) >= min_frames:
            notes.append(
                {
                    "midi": cur_m,
                    "start": cur_start * sec_per_hop,
                    "dur": len(cur_st) * sec_per_hop,
                    "conf": float(np.mean(cur_st)),
                }
            )

    for i, (m, st) in enumerate(frames):
        if m is not None and m == cur_m:
            cur_st.append(st)
        else:
            flush()
            cur_m = m
            cur_st = [st] if m is not None else []
            cur_start = i
    flush()

    if not notes:
        return {"ok": False, "reason": "no_pitch", "notes": []}

    # Коррекция октавных ошибок трекера: одиночная нота на ±12 полутонов от
    # обоих близких соседей → снапим в их октаву.
    for i in range(1, len(notes) - 1):
        m, pm, nm = notes[i]["midi"], notes[i - 1]["midi"], notes[i + 1]["midi"]
        if abs(pm - nm) <= 2 and abs(m - pm) >= 11:
            for cand in (m - 12, m + 12):
                if abs(cand - pm) <= 2 and abs(cand - nm) <= 2:
                    notes[i]["midi"] = cand
                    break

    # Честная «уверенность»: средняя сила тона по распознанным нотам.
    confidence = int(round(100 * float(np.mean([n["conf"] for n in notes]))))
    confidence = max(1, min(99, confidence))
    return {"ok": True, "notes": notes, "count": len(notes), "confidence": confidence}


# ================== MIDI ==================
def _vlq(n):
    """Variable-length quantity (MIDI delta-time)."""
    if n == 0:
        return b"\x00"
    out = bytearray()
    while n:
        out.insert(0, n & 0x7F)
        n >>= 7
    for i in range(len(out) - 1):
        out[i] |= 0x80
    return bytes(out)


def render_midi(notes, offset=0, tempo_bpm=None, tpq=480):
    """Список нот → байты SMF type-0. Тайминг сохраняется точно (не квантуется)."""
    if tempo_bpm is None:
        tempo_bpm = estimate_tempo(notes)
    spb = 60.0 / tempo_bpm

    def ticks(sec):
        return int(round(sec / spb * tpq))

    events = []  # (tick, status, note, vel)
    for n in notes:
        m = max(0, min(127, n["midi"] + offset))
        on = ticks(n["start"])
        off = max(on + 1, ticks(n["start"] + n["dur"]))
        events.append((on, 0x90, m, 80))
        events.append((off, 0x80, m, 0))
    # При равном тике note-off раньше note-on
    events.sort(key=lambda e: (e[0], 1 if e[1] == 0x90 else 0))

    track = bytearray()
    mpqn = int(60_000_000 / tempo_bpm)
    track += b"\x00\xff\x51\x03" + mpqn.to_bytes(3, "big")  # set tempo
    last = 0
    for tick, status, note, vel in events:
        track += _vlq(tick - last) + bytes([status, note & 0x7F, vel])
        last = tick
    track += b"\x00\xff\x2f\x00"  # end of track

    header = (
        b"MThd"
        + (6).to_bytes(4, "big")
        + (0).to_bytes(2, "big")
        + (1).to_bytes(2, "big")
        + tpq.to_bytes(2, "big")
    )
    chunk = b"MTrk" + len(track).to_bytes(4, "big") + bytes(track)
    return header + chunk


# ================== MusicXML ==================
# Канонические длительности в делениях (divisions=4 → четверть=4, шестнадцатая=1).
_CANON = [
    (16, "whole", 0),
    (12, "half", 1),
    (8, "half", 0),
    (6, "quarter", 1),
    (4, "quarter", 0),
    (3, "eighth", 1),
    (2, "eighth", 0),
    (1, "16th", 0),
]
# Энгармоническое написание по классу высоты: диезное и бемольное.
_SHARP_STEP = [
    ("C", 0),
    ("C", 1),
    ("D", 0),
    ("D", 1),
    ("E", 0),
    ("F", 0),
    ("F", 1),
    ("G", 0),
    ("G", 1),
    ("A", 0),
    ("A", 1),
    ("B", 0),
]
_FLAT_STEP = [
    ("C", 0),
    ("D", -1),
    ("D", 0),
    ("E", -1),
    ("E", 0),
    ("F", 0),
    ("G", -1),
    ("G", 0),
    ("A", -1),
    ("A", 0),
    ("B", -1),
    ("B", 0),
]

_DIV = 4  # делений на четверть
_MEASURE_DIV = 4 * _DIV  # 4/4 такт = 16 делений


def detect_fifths(midis):
    """Подбирает тональность (мажор): число знаков fifths (-6..+6),
    минимизируя ноты вне диатоники."""
    from collections import Counter

    cnt = Counter(m % 12 for m in midis)
    best = None
    for f in range(-6, 7):
        tonic = (f * 7) % 12
        scale = {(tonic + i) % 12 for i in (0, 2, 4, 5, 7, 9, 11)}
        out = sum(c for pc, c in cnt.items() if pc not in scale)
        key = (out, abs(f))
        if best is None or key < best[0]:
            best = (key, f)
    return best[1]


def _key_alters(fifths):
    """Знаки при ключе: {шаг: alter}."""
    sharps = "FCGDAEB"
    flats = "BEADGCF"
    d = {}
    if fifths > 0:
        for s in sharps[:fifths]:
            d[s] = 1
    elif fifths < 0:
        for s in flats[:-fifths]:
            d[s] = -1
    return d


def _spell(midi, fifths):
    """(step, alter, octave) — написание ноты с учётом тональности (диез/бемоль)."""
    table = _FLAT_STEP if fifths < 0 else _SHARP_STEP
    step, alter = table[midi % 12]
    # октава по реальному звуку (для бемольной записи Cb/B-граница не сдвигаем — редкий край)
    return step, alter, midi // 12 - 1


def estimate_tempo(notes):
    """Оценка темпа: медианная длительность ноты ≈ четверть."""
    durs = sorted(n["dur"] for n in notes if n["dur"] > 0)
    if not durs:
        return 120
    med = durs[len(durs) // 2]
    bpm = 60.0 / med if med > 0 else 120
    return int(max(50, min(200, round(bpm))))


def _decompose(d):
    """Длительность (в делениях) → список (dur, type, dots) канонич. нот."""
    out = []
    for val, t, dots in _CANON:
        while d >= val:
            out.append((val, t, dots))
            d -= val
    return out


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class _MeasureWriter:
    """Раскладывает поток нот/пауз по тактам 4/4, разрывая на барлайнах с лигами."""

    def __init__(self):
        self.measures = [[]]
        self.rem = _MEASURE_DIV

    def _new_measure(self):
        self.measures.append([])
        self.rem = _MEASURE_DIV

    def add(self, pitch, dur, is_rest, graces=None):
        """pitch = dict {step,alter,octave,accidental} или None (для паузы).
        graces = список pitch-dict — украшающие форшлаги перед нотой (без длительности)."""
        if graces:
            if self.rem == 0:
                self._new_measure()
            for gp in graces:
                self.measures[-1].append(
                    {
                        "pitch": gp,
                        "dur": 0,
                        "type": "eighth",
                        "dots": 0,
                        "rest": False,
                        "tie": None,
                        "show_acc": True,
                        "grace": True,
                    }
                )
        pieces = []
        r = dur
        while r > 0:
            if self.rem == 0:
                self._new_measure()
            take = min(self.rem, r)
            for d, t, dots in _decompose(take):
                el = {
                    "pitch": pitch,
                    "dur": d,
                    "type": t,
                    "dots": dots,
                    "rest": is_rest,
                    "tie": None,
                    "show_acc": False,
                }
                self.measures[-1].append(el)
                pieces.append(el)
            self.rem -= take
            r -= take
        if not is_rest and pieces:
            pieces[0]["show_acc"] = (
                True  # знак альтерации — только на первой части ноты
            )
            if len(pieces) > 1:  # лиги между частями одной ноты
                for k, el in enumerate(pieces):
                    el["tie"] = (
                        "start"
                        if k == 0
                        else ("stop" if k == len(pieces) - 1 else "both")
                    )

    def pad_last(self):
        if 0 < self.rem < _MEASURE_DIV:
            self.add(None, self.rem, True)


def _note_xml(el):
    is_grace = el.get("grace")
    out = ["<note>"]
    if is_grace:
        out.append('<grace slash="yes"/>')
    p = el["pitch"]
    if el["rest"] or p is None:
        out.append("<rest/>")
    else:
        out.append("<pitch><step>%s</step>" % p["step"])
        if p["alter"]:
            out.append("<alter>%d</alter>" % p["alter"])
        out.append("<octave>%d</octave></pitch>" % p["octave"])
    if not is_grace:  # у грейс-ноты нет длительности
        out.append("<duration>%d</duration>" % el["dur"])
    tied = []
    if not is_grace:
        if el["tie"] in ("start", "both"):
            out.append('<tie type="start"/>')
            tied.append('<tied type="start"/>')
        if el["tie"] in ("stop", "both"):
            out.append('<tie type="stop"/>')
            tied.append('<tied type="stop"/>')
    out.append("<type>%s</type>" % el["type"])
    out.append("<dot/>" * el["dots"])
    # знак альтерации (визуальный) — только на первой части ноты
    if (not el["rest"]) and p is not None and el["show_acc"] and p.get("accidental"):
        out.append("<accidental>%s</accidental>" % p["accidental"])
    if tied:
        out.append("<notations>%s</notations>" % "".join(tied))
    out.append("</note>")
    return "".join(out)


_CLEFS = {"treble": ("G", 2), "bass": ("F", 4)}


def render_musicxml(
    notes,
    offset=0,
    tempo_bpm=None,
    title="Транскрипция",
    fifths=None,
    clef="treble",
    composer=None,
    character=None,
):
    midis = [n["midi"] + offset for n in notes]
    if (
        fifths is None
    ):  # автоопределение (для транскрипции); генератор партий задаёт явно
        fifths = detect_fifths(midis) if midis else 0
    if tempo_bpm is None:
        tempo_bpm = estimate_tempo(notes)
    spb = 60.0 / tempo_bpm
    ka = _key_alters(fifths)

    def to_div(sec):
        return int(round(sec / spb * _DIV))

    def make_pitch(midi):
        step, alter, octave = _spell(midi, fifths)
        acc = None
        if alter != ka.get(step, 0):  # нота вне знаков при ключе → рисуем знак
            acc = {1: "sharp", 0: "natural", -1: "flat"}[alter]
        return {"step": step, "alter": alter, "octave": octave, "accidental": acc}

    # Классификация форшлагов: короткая нота перед явно более длинной = украшение.
    GRACE_SEC, MAIN_MIN = 0.13, 0.18
    items, pend = [], []
    for idx, n in enumerate(notes):
        is_grace = (
            n["dur"] < GRACE_SEC
            and idx < len(notes) - 1
            and notes[idx + 1]["dur"] >= MAIN_MIN
        )
        if is_grace:
            pend.append(n)
        else:
            items.append({"note": n, "graces": pend})
            pend = []
    for g in pend:  # хвостовые форшлаги без основной ноты → как обычные
        items.append({"note": g, "graces": []})

    w = _MeasureWriter()
    prev_end = 0.0
    for it in items:
        n, graces = it["note"], it["graces"]
        gstart = graces[0]["start"] if graces else n["start"]
        gap = to_div(gstart - prev_end)
        if gap > 0:
            w.add(None, gap, True)
        gp = [make_pitch(g["midi"] + offset) for g in graces]
        w.add(
            make_pitch(n["midi"] + offset), max(1, to_div(n["dur"])), False, graces=gp
        )
        prev_end = n["start"] + n["dur"]
    w.pad_last()

    measures = [m for m in w.measures if m]
    parts = []
    for i, mz in enumerate(measures, 1):
        attrs = ""
        if i == 1:
            csign, cline = _CLEFS.get(clef, _CLEFS["treble"])
            attrs = (
                "<attributes><divisions>%d</divisions>"
                "<key><fifths>%d</fifths></key>"
                "<time><beats>4</beats><beat-type>4</beat-type></time>"
                "<clef><sign>%s</sign><line>%d</line></clef></attributes>"
                % (_DIV, fifths, csign, cline)
            )
            # видимая «особенность» (характер/стиль), напр. Ballad
            if character:
                attrs += (
                    '<direction placement="above"><direction-type>'
                    '<words font-weight="bold" font-size="11">%s</words>'
                    "</direction-type></direction>" % _esc(character)
                )
            # видимая отметка темпа ♩=NN (текст DejaVu Sans — в нём есть символ ноты)
            attrs += (
                '<direction placement="above"><direction-type>'
                '<words font-family="DejaVu Sans" font-size="11">♩ = %d</words>'
                "</direction-type>"
                '<sound tempo="%d"/></direction>' % (tempo_bpm, tempo_bpm)
            )
        parts.append(
            '<measure number="%d">%s%s</measure>'
            % (i, attrs, "".join(_note_xml(el) for el in mz))
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" '
        '"http://www.musicxml.org/dtds/partwise.dtd">'
        '<score-partwise version="3.1">'
        "<work><work-title>%s</work-title></work>%s%s"
        '<part-list><score-part id="P1">'
        '<part-name print-object="no">Melody</part-name>'
        "</score-part></part-list>"
        '<part id="P1">%s</part></score-partwise>'
        % (
            _esc(title),
            (
                '<identification><creator type="composer">%s</creator></identification>'
                % _esc(composer)
            )
            if composer
            else "",
            _credits(title, composer),
            "".join(parts),
        )
    )


def _credits(title, composer):
    """MusicXML <credit> для шапки страницы: название по центру + автор справа.
    Рисуются при verovio header='encoded'. Автор — только если задан."""
    c = (
        '<credit page="1"><credit-type>title</credit-type>'
        '<credit-words justify="center" valign="top" font-size="15" '
        'font-weight="bold">%s</credit-words></credit>' % _esc(title)
    )
    if composer:
        c += (
            '<credit page="1"><credit-type>composer</credit-type>'
            '<credit-words justify="right" valign="top" font-size="11">'
            "%s</credit-words></credit>" % _esc(composer)
        )
    return c


# ================== РЕНДЕР НОТАЦИИ В КАРТИНКУ ==================
def render_png(musicxml, scale=40):
    """MusicXML → PNG с нотацией (verovio + cairosvg).
    Возвращает bytes или None, если движки не установлены / рендер не удался."""
    try:
        import verovio
        import cairosvg
    except Exception:
        return None
    try:
        tk = verovio.toolkit()
        tk.setOptions(
            {
                "pageWidth": 2100,
                "pageHeight": 2970,
                "scale": scale,
                "adjustPageHeight": True,
                "header": "encoded",
                "footer": "none",
                "smuflTextFont": "none",
                "pageMarginTop": 60,
                "pageMarginBottom": 60,
                "pageMarginLeft": 60,
                "pageMarginRight": 60,
            }
        )
        if not tk.loadData(musicxml):
            return None
        svg = tk.renderToSVG(1)
        return cairosvg.svg2png(
            bytestring=svg.encode("utf-8"), background_color="white"
        )
    except Exception:
        return None


def render_pdf(musicxml, scale=40):
    """MusicXML → PDF с нотацией (verovio + cairosvg). bytes или None."""
    try:
        import verovio
        import cairosvg
    except Exception:
        return None
    try:
        tk = verovio.toolkit()
        tk.setOptions(
            {
                "pageWidth": 2100,
                "pageHeight": 2970,
                "scale": scale,
                "adjustPageHeight": True,
                "header": "encoded",
                "footer": "none",
                "smuflTextFont": "none",
                "pageMarginTop": 60,
                "pageMarginBottom": 60,
                "pageMarginLeft": 60,
                "pageMarginRight": 60,
            }
        )
        if not tk.loadData(musicxml):
            return None
        svg = tk.renderToSVG(1)
        return cairosvg.svg2pdf(
            bytestring=svg.encode("utf-8"), background_color="white"
        )
    except Exception:
        return None
