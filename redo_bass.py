"""Перерендер ТОЛЬКО партий контрабаса (на октаву ниже, см. PART_SPEC['contrabass']).
Перезаписывает существующие slug_bass.pdf и обновляет transposition в version-dict.
Источник мелодий — тот же, что в add_gb (антология + Saints). file_id контрабаса сбрасываем (PDF сменился).
Запуск НА СЕРВЕРЕ: python redo_bass.py
"""
import json
import add_gb, gen_parts


def main():
    notes = json.load(open(add_gb.NOTES_JSON, encoding="utf-8"))
    srcmap = add_gb.build_source_map()
    redone = 0
    for n in notes:
        vers = n.get("versions") or []
        cbv = next((v for v in vers if v["instrument"] == "contrabass"), None)
        if not cbv:
            continue
        title = n["title"]
        if add_gb.norm(title) == add_gb.norm("When the Saints Go Marching In"):
            seq, fifths = gen_parts.SAINTS, None
        else:
            fid = add_gb.OVERRIDE.get(title) or srcmap.get(add_gb.norm(title))
            if not fid:
                print(f"  ✗ нет источника: {title}"); continue
            seq, fifths = add_gb.melody_from_anthology(fid)
        cnotes = gen_parts.build_notes(seq, bpm=120)
        cf = fifths if fifths is not None else gen_parts.transcribe.detect_fifths([x["midi"] for x in cnotes])
        slug = gen_parts.slugify(title)
        # удалить старый файл, чтобы render_part перерендерил
        import os
        path = os.path.join(gen_parts.NOTES_FOLDER, f"{slug}_bass.pdf")
        if os.path.exists(path):
            os.remove(path)
        newv = gen_parts.render_part(title, slug, cnotes, 120, cf, "contrabass")
        cbv.update(newv)  # file тот же, transposition -> -12, file_id -> None
        print(f"  ↻ {title}")
        redone += 1
    json.dump(notes, open(add_gb.NOTES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nГотово. Перерендерено контрабасов: {redone}.")


if __name__ == "__main__":
    main()
