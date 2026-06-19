"""Миграция: добавить партии ГИТАРЫ (скрипичный ключ, концертный строй) и
КОНТРАБАСА (басовый ключ) ко ВСЕМ мелодическим работам (у кого есть версия trumpet).

Мелодии берём из того же верифицированного источника, что и оригинальные партии —
Public Domain Song Anthology (Dataverse), сопоставляя по нормализованному названию;
«Saints» — из хардкод-мелодии gen_parts.SAINTS. Существующие версии/файлы/file_id НЕ трогаем,
только дописываем guitar+contrabass. Идемпотентно.

Запуск НА СЕРВЕРЕ (там verovio+cairosvg+инет):  python add_gb.py
"""
import json, os, re, sys, tempfile, urllib.request
import parse_pdsa, gen_parts

NOTES_JSON = "notes.json"
DOI = "doi:10.18130/V3/C4RD06"
DATASET = "https://dataverse.lib.virginia.edu/api/datasets/:persistentId/?persistentId=" + DOI
DATAFILE = "https://dataverse.lib.virginia.edu/api/access/datafile/"
NEW = ["guitar", "contrabass"]

# Наши названия, отличающиеся от ярлыка антологии -> Dataverse file id (выверено вручную).
OVERRIDE = {
    "A Good Man Is Hard to Find": 4060,
    "Second Line (Joe Avery Blues)": 3747,
    "Indiana (Back Home Again in Indiana)": 4116,
    "Chicago (That Toddlin' Town)": 3877,
    "Go Down, Moses": 4042,
    "Daisy Bell (Bicycle Built for Two)": 4069,
    "Streets of Laredo": 3866,
}


def norm(s):
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "jazztone-ingest"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def build_source_map():
    """нормализованное название -> Dataverse file id (только .xml)."""
    data = json.loads(fetch(DATASET))
    m = {}
    for f in data["data"]["latestVersion"]["files"]:
        fn = f["dataFile"]["filename"]
        if fn.lower().endswith(".xml"):
            m[norm(fn[:-4])] = f["dataFile"]["id"]
    return m


def melody_from_anthology(fid):
    raw = fetch(DATAFILE + str(fid))
    fd, path = tempfile.mkstemp(suffix=".xml"); os.write(fd, raw); os.close(fd)
    try:
        seq, fifths, _comp, _title = parse_pdsa.parse_melody(path)
    finally:
        os.unlink(path)
    return seq, fifths


def main():
    notes = json.load(open(NOTES_JSON, encoding="utf-8"))
    srcmap = build_source_map()
    print(f"Источник: {len(srcmap)} XML в антологии.")

    done = skipped = nomatch = 0
    for n in notes:
        vers = n.get("versions")
        if not vers:
            continue
        have = {v["instrument"] for v in vers}
        if "trumpet" not in have:          # не мелодическая работа (напр. Joplin piano) — пропуск
            continue
        if all(i in have for i in NEW):    # уже есть — идемпотентно
            skipped += 1
            continue

        title = n["title"]
        # источник мелодии
        if norm(title) == norm("When the Saints Go Marching In"):
            seq = gen_parts.SAINTS
            fifths = None  # detect (C)
        else:
            fid = OVERRIDE.get(title) or srcmap.get(norm(title))
            if not fid:
                print(f"  ✗ нет источника: {title}")
                nomatch += 1
                continue
            seq, fifths = melody_from_anthology(fid)
            if len(seq) < 6:
                print(f"  ✗ мало нот: {title}")
                nomatch += 1
                continue

        cnotes = gen_parts.build_notes(seq, bpm=120)
        cf = fifths if fifths is not None else gen_parts.transcribe.detect_fifths([x["midi"] for x in cnotes])
        slug = gen_parts.slugify(title)
        print(f"  + {title}")
        for instr in NEW:
            if instr in have:
                continue
            v = gen_parts.render_part(title, slug, cnotes, 120, cf, instr)
            n["versions"].append(v)
        done += 1

    json.dump(notes, open(NOTES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nГотово. Дополнено {done}, уже было {skipped}, без источника {nomatch}.")


if __name__ == "__main__":
    main()
