"""Ингест EU-PD мелодий из Public Domain Song Anthology (UVA, MusicXML lead sheets)
→ gen_parts → партии под инструменты → notes.json. Источник верифицированный (не выдумка,
не OCR). Только композиторы †≤1955 / традиционные (EU life+70). Идемпотентно по title.
"""

import json, sys, tempfile, os, urllib.request
import parse_pdsa, gen_parts, make_audio

DATAVERSE = "https://dataverse.lib.virginia.edu/api/access/datafile/"
CURATED = json.load(
    open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "curated.json"),
        encoding="utf-8",
    )
)
DRY = "--dry" in sys.argv


def fetch(fid):
    req = urllib.request.Request(
        DATAVERSE + str(fid), headers={"User-Agent": "jazztone-ingest"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main():
    added = 0
    for c in CURATED:
        try:
            data = fetch(c["id"])
            fd, path = tempfile.mkstemp(suffix=".xml")
            os.write(fd, data)
            os.close(fd)
            seq, fifths, xml_comp, xml_title = parse_pdsa.parse_melody(path)
            if len(seq) < 6:
                os.unlink(path)
                print(f"  ⚠ {c['title']}: мало нот ({len(seq)}) — пропуск")
                continue
            keyname = gen_parts.FIFTHS_KEY.get(fifths, "?")
            print(
                f"  {c['title']:42} нот={len(seq):3} тон.={keyname:3} ({c['composer']})"
            )
            if DRY:
                os.unlink(path)
                continue
            notes = gen_parts.build_notes(seq, bpm=120)
            entry = gen_parts.generate_work(
                title=c["title"],
                composer=c["composer"],
                concert_notes=notes,
                bpm=120,
                key_concert=keyname,
                style=c["style"],
                genre=c["genre"],
                concert_fifths=fifths,
            )
            # авто-аудио: плей-элонг+минус из того же MusicXML (если есть аккорды)
            try:
                r = make_audio.make_audio_for_xml(
                    path, gen_parts.slugify(c["title"]), bpm=120
                )
                if r.get("backing"):
                    entry["audio"] = {
                        "play": r["audio"],
                        "minus": r["backing"],
                        "play_file_id": None,
                        "minus_file_id": None,
                    }
            except Exception as ae:
                print(f"    ⚠ аудио не собралось: {ae}")
            finally:
                try:
                    os.unlink(path)
                except OSError:
                    pass
            gen_parts.add_to_catalog(entry)
            added += 1
        except Exception as e:
            print(f"  ✗ {c['title']}: {e}")
    print(f"\nГотово. Обработано {len(CURATED)}, добавлено {added}.")


if __name__ == "__main__":
    main()
