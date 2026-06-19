"""
Генератор партий под инструменты из ОДНОЙ концертной мелодии.
Берём мелодию в concert pitch (как звучит), транспонируем таблицей INSTRUMENTS
и рендерим PDF под каждый строй — НЕ скрапим N чужих файлов.

Источник мелодии должен быть ЧИСТЫМ и PD/собственным (Правило №1: не выдумывать).
Тут демо на public-domain теме «When the Saints Go Marching In» (traditional).

Запуск:  python gen_parts.py
Идемпотентно по title: если работа уже есть в notes.json — не дублирует.
"""

import json
import os
import transcribe

NOTES_JSON = "notes.json"
NOTES_FOLDER = "notes"

# Спецификация партий: инструмент -> (written-offset в полутонах, ключ, тег файла).
# written-offset = на сколько ПИШЕТСЯ партия относительно concert (для гитары/контрабаса
# = 0: они октавно-транспонирующие, пишутся в концертном строе, звучат октавой ниже).
# Один файл на каждый distinct тег (инструменты с одинаковыми нотами+ключом делят PDF).
PART_SPEC = {
    "trumpet": (2, "treble", "Bb"),
    "clarinet": (2, "treble", "Bb"),
    "tenorsax": (14, "treble", "Bb_tenor"),
    "altosax": (9, "treble", "Eb"),
    "trombone": (0, "treble", "concert"),
    "concert": (0, "treble", "concert"),
    "piano": (0, "treble", "concert"),
    "guitar": (0, "treble", "guitar"),
    "contrabass": (
        -12,
        "bass",
        "bass",
    ),  # на октаву ниже письма = читается в басовом ключе без лишних добавочных
}
TARGET_INSTRUMENTS = list(PART_SPEC)

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
# Число знаков (fifths) -> название мажорной тональности (для подписи версии).
FIFTHS_KEY = {
    -6: "G♭",
    -5: "D♭",
    -4: "A♭",
    -3: "E♭",
    -2: "B♭",
    -1: "F",
    0: "C",
    1: "G",
    2: "D",
    3: "A",
    4: "E",
    5: "B",
    6: "F♯",
}


def written_fifths(concert_fifths, offset):
    """Знаки при ключе ПИСАНОЙ партии. Транспозиция на n полутонов вверх
    сдвигает тональность на n*7 квинт; нормализуем в [-6, 5]."""
    return ((concert_fifths + offset * 7 + 6) % 12) - 6


def name_to_midi(tok):
    """'C4'->60, 'Bb3', 'F#5'. 'R'/'r' -> None (пауза)."""
    if tok in ("R", "r"):
        return None
    letter = tok[0].upper()
    i = 1
    semis = _PC[letter]
    while i < len(tok) and tok[i] in "#b♯♭":
        semis += 1 if tok[i] in "#♯" else -1
        i += 1
    octave = int(tok[i:])
    return semis + (octave + 1) * 12


def build_notes(seq, bpm=120):
    """seq = [(token, beats), ...] concert pitch -> список нот {midi,start,dur}.
    Паузы (R) сдвигают время, ноты не создают."""
    spb = 60.0 / bpm
    notes, t = [], 0.0
    for tok, beats in seq:
        dur = beats * spb
        m = name_to_midi(tok)
        if m is not None:
            notes.append({"midi": m, "start": t, "dur": dur, "conf": 1.0})
        t += dur
    return notes


def slugify(title):
    return "".join(c.lower() if c.isalnum() else "_" for c in title).strip("_")


def render_part(
    title,
    slug,
    concert_notes,
    bpm,
    concert_fifths,
    instr,
    _file_cache=None,
    composer=None,
    character=None,
):
    """Рендерит PDF одной партии (инструмента) и возвращает version-dict.
    _file_cache — общий dict тег->(rel,kw), чтобы инструменты с одинаковым тегом делили файл."""
    os.makedirs(NOTES_FOLDER, exist_ok=True)
    woffset, clef, tag = PART_SPEC[instr]
    rel = f"{slug}_{tag}.pdf"
    wf = written_fifths(concert_fifths, woffset)
    abspath = os.path.join(NOTES_FOLDER, rel)
    if not (_file_cache and tag in _file_cache) and not os.path.exists(abspath):
        xml = transcribe.render_musicxml(
            concert_notes,
            offset=woffset,
            tempo_bpm=bpm,
            fifths=wf,
            title=f"{title} — {transcribe.INSTRUMENTS[instr][0]}",
            clef=clef,
            composer=composer,
            character=character,
        )
        pdf = transcribe.render_pdf(xml)
        if not pdf:
            raise SystemExit("render_pdf вернул None — нет verovio/cairosvg?")
        with open(abspath, "wb") as f:
            f.write(pdf)
        print(
            f"  ✓ {rel}  ({len(pdf)} байт, woffset {woffset:+d}, {clef}, тон. {FIFTHS_KEY.get(wf, '?')})"
        )
    if _file_cache is not None:
        _file_cache[tag] = (rel, FIFTHS_KEY.get(wf, "?"))
    return {
        "instrument": instr,
        "transposition": woffset,
        "clef": clef,
        "key_written": FIFTHS_KEY.get(wf, "?"),
        "file": rel,
        "file_id": None,
    }


def generate_work(
    title,
    composer,
    concert_notes,
    bpm,
    key_concert,
    style,
    genre="jazz",
    typ="piece",
    concert_fifths=None,
    instruments=None,
):
    """Рендерит PDF под каждый distinct тег, собирает запись новой схемы.
    concert_fifths — реальные знаки концертной тональности (из MusicXML); если None — определяем.
    instruments — подмножество TARGET_INSTRUMENTS (по умолчанию все)."""
    slug = slugify(title)
    if concert_fifths is None:
        concert_fifths = (
            transcribe.detect_fifths([n["midi"] for n in concert_notes])
            if concert_notes
            else 0
        )
    cache = {}
    character = style.capitalize() if style else None  # видимая «особенность» на нотах
    versions = [
        render_part(
            title,
            slug,
            concert_notes,
            bpm,
            concert_fifths,
            instr,
            cache,
            composer=composer,
            character=character,
        )
        for instr in (instruments or TARGET_INSTRUMENTS)
    ]
    return {
        "title": title,
        "composer": composer,
        "genre": genre,
        "type": typ,
        "style": style,
        "key_concert": key_concert,
        "versions": versions,
    }


def add_to_catalog(entry):
    with open(NOTES_JSON, encoding="utf-8") as f:
        notes = json.load(f)
    if any(n.get("title") == entry["title"] and n.get("versions") for n in notes):
        print(f"  ⏭  «{entry['title']}» уже есть — пропускаю.")
        return
    entry["id"] = max(n["id"] for n in notes) + 1
    # порядок ключей: id первым для читаемости
    ordered = {"id": entry.pop("id"), **entry}
    notes.append(ordered)
    with open(NOTES_JSON, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)
    print(f"  ✓ добавлено id={ordered['id']} с {len(ordered['versions'])} версиями")


# ===== ДЕМО: When the Saints Go Marching In (traditional, public domain) =====
# Концертная мелодия (как звучит), key C, 4/4. Стандартная узнаваемая редакция.
SAINTS = [
    ("C4", 1),
    ("E4", 1),
    ("F4", 1),
    ("G4", 3),
    ("R", 1),
    ("C4", 1),
    ("E4", 1),
    ("F4", 1),
    ("G4", 3),
    ("R", 1),
    ("C4", 1),
    ("E4", 1),
    ("F4", 1),
    ("G4", 2),
    ("E4", 1),
    ("C4", 1),
    ("E4", 2),
    ("D4", 2),
    ("C4", 1),
    ("E4", 1),
    ("F4", 1),
    ("G4", 3),
    ("R", 1),
    ("G4", 1),
    ("E4", 1),
    ("C4", 1),
    ("D4", 1),
    ("C4", 4),
]

if __name__ == "__main__":
    print("Генерация партий…")
    notes = build_notes(SAINTS, bpm=120)
    entry = generate_work(
        title="When the Saints Go Marching In",
        composer="Traditional",
        concert_notes=notes,
        bpm=120,
        key_concert="C",
        style="dixieland",
        genre="dixieland",
    )
    add_to_catalog(entry)
    print("Готово.")
