"""Перегенерация PDF-партий 29 PDSA-работ (curated.json) с новым оформлением
(title/композитор/темп/характер, без ярлыка «Melody»). Сбрасывает file_id PDF
(новые байты → Telegram перельёт). Запуск на сервере. Бэкап notes.json авто.
"""

import json
import os
import shutil
import tempfile
import time
import urllib.request

import gen_parts
import parse_pdsa

DATAVERSE = "https://dataverse.lib.virginia.edu/api/access/datafile/"

cur = json.load(open("curated.json", encoding="utf-8"))
notes = json.load(open("notes.json", encoding="utf-8"))
by_title = {n.get("title"): n for n in notes}
shutil.copy("notes.json", f"notes.json.bak_rerender_{int(time.time())}")

done = 0
for c in cur:
    note = by_title.get(c["title"])
    if not note or not note.get("versions"):
        continue
    try:
        req = urllib.request.Request(
            DATAVERSE + str(c["id"]), headers={"User-Agent": "jazztone"}
        )
        data = urllib.request.urlopen(req, timeout=60).read()
        fd, p = tempfile.mkstemp(suffix=".xml")
        os.write(fd, data)
        os.close(fd)
        seq, fifths, _comp, _title = parse_pdsa.parse_melody(p)
        os.unlink(p)
        concert_notes = gen_parts.build_notes(seq, bpm=120)
        slug = gen_parts.slugify(c["title"])
        composer = note.get("composer")
        style = note.get("style") or note.get("genre")
        character = style.capitalize() if style else None

        # удалить старые PDF этой работы, чтобы render_part перерисовал
        for v in note["versions"]:
            ap = os.path.join(gen_parts.NOTES_FOLDER, v["file"])
            if os.path.exists(ap):
                os.remove(ap)
        cache = {}
        for v in note["versions"]:
            gen_parts.render_part(
                c["title"],
                slug,
                concert_notes,
                120,
                fifths,
                v["instrument"],
                cache,
                composer=composer,
                character=character,
            )
            v["file_id"] = None  # PDF пересоздан → старый file_id недействителен
        done += 1
        print(f"  ✓ id={note['id']:>3} {c['title']:42} версий={len(note['versions'])}")
    except Exception as e:
        print(f"  ✗ {c['title']}: {e!r}")

with open("notes.json", "w", encoding="utf-8") as f:
    json.dump(notes, f, ensure_ascii=False, indent=2)
print(f"\nГотово. Перегенерено работ: {done}.")
