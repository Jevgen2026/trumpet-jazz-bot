"""Скан: у каких PDSA-работ (curated.json) есть аккорды → аудио-способны.
Сопоставляет с id в notes.json по title. Запуск на сервере."""

import json
import tempfile
import urllib.request

import make_audio
import parse_pdsa

DATAVERSE = "https://dataverse.lib.virginia.edu/api/access/datafile/"
cur = json.load(open("curated.json", encoding="utf-8"))
notes = json.load(open("notes.json", encoding="utf-8"))
title_to_id = {n.get("title"): n["id"] for n in notes}

ok = []
for c in cur:
    try:
        req = urllib.request.Request(
            DATAVERSE + str(c["id"]), headers={"User-Agent": "x"}
        )
        data = urllib.request.urlopen(req, timeout=60).read()
        fd, p = tempfile.mkstemp(suffix=".xml")
        open(p, "wb").write(data)
        seq, _, _, _ = parse_pdsa.parse_melody(p)
        ch = make_audio.parse_chords(p, 120)
        cid = title_to_id.get(c["title"])
        nnotes = len([s for s in seq if s[0] != "R"])
        has = len(ch) >= 4 and nnotes >= 6
        print(
            f"{'AUDIO' if has else 'skip '} id={str(cid):>4} fid={c['id']} ch={len(ch):3} notes={nnotes:3}  {c['title']}"
        )
        if has and cid:
            ok.append({"id": cid, "fid": c["id"], "title": c["title"]})
    except Exception as e:
        print("ERR", c["title"], repr(e))

print("\nAUDIO-CAPABLE:", len(ok), "из", len(cur))
print(json.dumps(ok, ensure_ascii=False))
