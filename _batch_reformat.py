"""Полный реформат: перерисовать ВСЕ versioned-работы старого стиля (не curated)
в новом PDF-стиле (title/composer/character), сбросить file_id. Источник мелодии —
Dataverse через add_gb (source-map + OVERRIDE). Saints — хардкод gen_parts.SAINTS.
Пер-работный try/except: сбой одной не валит прогон. Бэкап notes.json в начале.
Запуск НА СЕРВЕРЕ через .venv/bin/python.
"""

import json
import os
import time

import add_gb
import gen_parts

notes = json.load(open("notes.json", encoding="utf-8"))
before = len(notes)
curated = {c["title"] for c in json.load(open("curated.json", encoding="utf-8"))}

targets = [n for n in notes if n.get("versions") and n["title"] not in curated]
print("кандидатов (versioned, не curated): %d" % len(targets), flush=True)

bak = "notes.json.bak_batch_%d" % int(time.time())
json.dump(notes, open(bak, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("бэкап:", bak, flush=True)

smap = add_gb.build_source_map()
SAINTS = add_gb.norm("When the Saints Go Marching In")

done, skipped = 0, []
for n in targets:
    title = n["title"]
    try:
        if add_gb.norm(title) == SAINTS:
            seq, fifths = gen_parts.SAINTS, 0
        else:
            fid = add_gb.OVERRIDE.get(title) or smap.get(add_gb.norm(title))
            if not fid:
                skipped.append((n["id"], title, "нет источника"))
                continue
            seq, fifths = add_gb.melody_from_anthology(fid)
        concert = gen_parts.build_notes(seq, bpm=120)
        slug = gen_parts.slugify(title)
        composer = n.get("composer")
        style = n.get("style") or n.get("genre")
        character = style.capitalize() if style else None

        for v in n["versions"]:
            ap = os.path.join(gen_parts.NOTES_FOLDER, v["file"])
            if os.path.exists(ap):
                os.remove(ap)
        cache = {}
        for v in n["versions"]:
            gen_parts.render_part(
                title,
                slug,
                concert,
                120,
                fifths,
                v["instrument"],
                cache,
                composer=composer,
                character=character,
            )
            v["file_id"] = None
        done += 1
        print(
            "  OK id=%-3s %s (версий %d)" % (n["id"], title[:40], len(n["versions"])),
            flush=True,
        )
    except Exception as e:
        skipped.append((n["id"], title, repr(e)[:80]))
        print("  СКИП id=%-3s %s :: %r" % (n["id"], title[:40], e), flush=True)

json.dump(
    notes, open("notes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2
)
print("\n=== ИТОГ ===", flush=True)
print("works: было %d -> стало %d" % (before, len(notes)), flush=True)
print("перерисовано: %d | пропущено: %d" % (done, len(skipped)), flush=True)
for i, t, why in skipped:
    print("  - id=%s %s :: %s" % (i, t, why), flush=True)
