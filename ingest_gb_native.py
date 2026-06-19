"""Залив РОДНОГО PD-репертуара под гитару и контрабас (не транспонированные мелодии, а
настоящие пьесы/этюды для инструмента).

Гитара — чистые граверы Mutopia (PD-композиторы: Sor †1839, Carcassi †1853, Giuliani †1829,
Aguado †1849, Tárrega †1909). URL: <composer>/<path>/<last>-a4.pdf.
Контрабас — IMSLP-зеркала на archive.org (Bottesini †1889, Fröhlich †1836).

Все композиторы музыки умерли ≤1955 → PD в ЕС (сервер в Финляндии, life+70). Идемпотентно по title.
Запуск НА СЕРВЕРЕ (инет; туннель не нужен): python ingest_gb_native.py
"""
import json, os, urllib.parse, urllib.request

NOTES_JSON = "notes.json"
NOTES_FOLDER = "notes"
MUTOPIA = "https://www.mutopiaproject.org/ftp/"
ARCHIVE = "https://archive.org/download/"

# гитара: (mutopia-path, title, composer, type, style)
GUITAR = [
    ("TarregaF/recuerdos",                 "Recuerdos de la Alhambra",   "Francisco Tárrega",  "piece", "romantic"),
    ("TarregaF/capricho-arabe",            "Capricho Árabe",             "Francisco Tárrega",  "piece", "romantic"),
    ("TarregaF/adelita",                   "Adelita (Mazurka)",          "Francisco Tárrega",  "piece", "romantic"),
    ("TarregaF/claro-de-luna",             "Claro de Luna",              "Francisco Tárrega",  "piece", "romantic"),
    ("SorF/O6/sorf-op6n01",                "Étude Op.6 No.1",            "Fernando Sor",       "etude", "classical"),
    ("SorF/O6/sorf-op6n08",                "Étude Op.6 No.8",            "Fernando Sor",       "etude", "classical"),
    ("SorF/O6/sorf-op6n12",                "Étude Op.6 No.12",           "Fernando Sor",       "etude", "classical"),
    ("SorF/O35/sorf_op35_no1",             "Étude Op.35 No.1",           "Fernando Sor",       "etude", "classical"),
    ("SorF/O35/sorf_op35_no22",            "Étude Op.35 No.22",          "Fernando Sor",       "etude", "classical"),
    ("GiulianiM/O50/giuliani-op50n01",     "Le Papillon Op.50 No.1",     "Mauro Giuliani",     "etude", "classical"),
    ("GiulianiM/O50/giuliani-op50n05",     "Le Papillon Op.50 No.5",     "Mauro Giuliani",     "etude", "classical"),
    ("GiulianiM/O50/giuliani-op50n19",     "Le Papillon Op.50 No.19",    "Mauro Giuliani",     "etude", "classical"),
    ("AguadoD/O3/aguado-op03n01",          "Étude Op.3 No.1",            "Dionisio Aguado",    "etude", "classical"),
    ("AguadoD/O3/aguado-op03n06",          "Étude Op.3 No.6",            "Dionisio Aguado",    "etude", "classical"),
]

# Carcassi Op.60 — полный набор из 25 мелодических этюдов (все есть на Mutopia, проверено).
GUITAR += [(f"CarcassiM/O60/carcassi-op60-{i:02d}", f"Étude Op.60 No.{i}",
            "Matteo Carcassi", "etude", "classical") for i in range(1, 26)]

# контрабас: (archive-id, filename, title, composer, type, style)
BASS = [
    ("imslp-bottesini-giovanni", "PMLP60690-Bottesini,_Giovanni_-_Elegia_in_D_-Double_bass_and_piano-.pdf",
     "Elegy in D", "Giovanni Bottesini", "piece", "romantic"),
    ("imslp-bottesini-giovanni", "PMLP60692-Bottesini_-Reverie.pdf",
     "Rêverie", "Giovanni Bottesini", "piece", "romantic"),
    ("imslp-frhlich-friedrich-theodor", "PMLP73170-Froehlich_Contrabass_schule_1830.pdf",
     "Contrabass-Schule (1830)", "Friedrich Theodor Fröhlich", "book", "method"),
    ("imslp-op136-michaelis-theodor", "PMLP319528-Michalils_D_Bass_tutor.pdf",
     "Contrabass-Schule, Op.136 (1891)", "Theodor Michaelis", "book", "method"),
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "jazztone-ingest"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def slug(s):
    return "".join(c.lower() if c.isalnum() else "_" for c in s).strip("_")


def main():
    os.makedirs(NOTES_FOLDER, exist_ok=True)
    notes = json.load(open(NOTES_JSON, encoding="utf-8"))
    have = {n.get("title") for n in notes}
    nid = max(n["id"] for n in notes)
    added = 0

    jobs = []
    for path, title, comp, typ, style in GUITAR:
        stem = path.rsplit("/", 1)[-1]
        url = f"{MUTOPIA}{path}/{stem}-a4.pdf"
        jobs.append(("guitar", url, f"guitar_{slug(title)}.pdf", title, comp, typ, style, "treble", 0))
    for aid, fn, title, comp, typ, style in BASS:
        url = ARCHIVE + aid + "/" + urllib.parse.quote(fn)
        jobs.append(("contrabass", url, f"bass_{slug(title)}.pdf", title, comp, typ, style, "bass", -12))

    for instr, url, rel, title, comp, typ, style, clef, transp in jobs:
        if title in have:
            print(f"  ⏭ {title} уже есть"); continue
        try:
            data = fetch(url)
        except Exception as e:
            print(f"  ✗ {title}: {e}"); continue
        if not data[:4] == b"%PDF":
            print(f"  ✗ {title}: не PDF ({len(data)} б)"); continue
        with open(os.path.join(NOTES_FOLDER, rel), "wb") as f:
            f.write(data)
        nid += 1
        notes.append({
            "id": nid, "title": title, "composer": comp, "genre": style,
            "type": typ, "style": style, "key_concert": "—",
            "versions": [{"instrument": instr, "transposition": transp, "clef": clef,
                          "key_written": "—", "file": rel, "file_id": None}],
        })
        print(f"  ✓ id={nid} [{instr}] {title}  ({len(data)//1024} KB)")
        added += 1

    json.dump(notes, open(NOTES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nГотово. Добавлено {added}, всего {len(notes)}.")


if __name__ == "__main__":
    main()
