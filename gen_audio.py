"""Рендер плей-элонг+минус для PDSA-работ (curated.json) и запись полей audio
в notes.json. Запуск на сервере (нужны fluidsynth+FluidR3+ffmpeg):
    ./.venv/bin/python gen_audio.py
Идемпотентно перезаписывает mp3 (движок заморожен) и сбрасывает file_id (новые байты).
Бэкап notes.json делается автоматически.
"""

import json
import os
import shutil
import tempfile
import time
import urllib.request

import gen_parts
import make_audio

DATAVERSE = "https://dataverse.lib.virginia.edu/api/access/datafile/"

cur = json.load(open("curated.json", encoding="utf-8"))
notes = json.load(open("notes.json", encoding="utf-8"))
by_title = {n.get("title"): n for n in notes}

bak = f"notes.json.bak_audio_{int(time.time())}"
shutil.copy("notes.json", bak)
print(f"бэкап: {bak}")

done = 0
for c in cur:
    note = by_title.get(c["title"])
    if not note:
        print(f"  ⏭  нет в каталоге: {c['title']}")
        continue
    try:
        req = urllib.request.Request(
            DATAVERSE + str(c["id"]), headers={"User-Agent": "jazztone"}
        )
        data = urllib.request.urlopen(req, timeout=60).read()
        fd, path = tempfile.mkstemp(suffix=".xml")
        os.write(fd, data)
        os.close(fd)
        slug = gen_parts.slugify(c["title"])
        r = make_audio.make_audio_for_xml(path, slug, bpm=120)
        os.unlink(path)
        if not r.get("backing"):
            print(f"  ⏭  нет аккордов: {c['title']}")
            continue
        note["audio"] = {
            "play": r["audio"],
            "minus": r["backing"],
            "play_file_id": None,
            "minus_file_id": None,
        }
        done += 1
        print(f"  ✓ id={note['id']:>3} {c['title']:42} {r['audio']} | {r['backing']}")
    except Exception as e:
        print(f"  ✗ {c['title']}: {e!r}")

with open("notes.json", "w", encoding="utf-8") as f:
    json.dump(notes, f, ensure_ascii=False, indent=2)
print(f"\nГотово. Аудио добавлено к {done} работам.")
