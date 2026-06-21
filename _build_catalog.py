"""Пересобрать slim-каталог мини-аппы из чистого notes.json.
Схема item: {id,title,composer,type,style,instruments}. Запуск НА СЕРВЕРЕ.
Пишет /tmp/catalog.json.
"""

import json

notes = json.load(open("notes.json", encoding="utf-8"))
items = []
for w in notes:
    insts = []
    for v in w.get("versions") or []:
        i = v.get("instrument")
        if i and i not in insts:
            insts.append(i)
    if not insts:
        insts = ["trumpet"]  # legacy flat
    items.append(
        {
            "id": w.get("id"),
            "title": w.get("title"),
            "composer": w.get("composer"),
            "type": w.get("type"),
            "style": w.get("style") or w.get("genre"),
            "instruments": insts,
        }
    )

json.dump(
    {"items": items},
    open("/tmp/catalog.json", "w", encoding="utf-8"),
    ensure_ascii=False,
    indent=2,
)
print("catalog items: %d -> /tmp/catalog.json" % len(items))
