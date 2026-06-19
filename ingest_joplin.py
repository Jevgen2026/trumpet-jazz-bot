"""Joplin-рэгтаймы: чистые PD-граверы Mutopia (фортепиано) → ragtime-пьесы.
Только НОВЫЕ (которых нет в каталоге). Идемпотентно по title."""
import json, os, urllib.request
NOTES_JSON="notes.json"; NOTES_FOLDER="notes"
BASE="https://www.mutopiaproject.org/ftp/JoplinS/"
JOPLIN=[  # (folder, title, key_concert)
 ("entertainer","The Entertainer","C"),
 ("magnetic","Magnetic Rag","—"),
 ("peacherine","Peacherine Rag","—"),
 ("search","Searchlight Rag","—"),
 ("bethena","Bethena (A Concert Waltz)","—"),
]
def main():
    os.makedirs(NOTES_FOLDER, exist_ok=True)
    notes=json.load(open(NOTES_JSON, encoding="utf-8"))
    have={n.get("title") for n in notes}
    nid=max(n["id"] for n in notes)
    added=0
    for folder,title,key in JOPLIN:
        if title in have:
            print(f"  ⏭ {title} уже есть"); continue
        url=f"{BASE}{folder}/{folder}-a4.pdf"
        rel=f"joplin_{folder}.pdf"
        try:
            data=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"jazztone"}),timeout=60).read()
        except Exception as e:
            print(f"  ✗ {title}: {e}"); continue
        open(os.path.join(NOTES_FOLDER,rel),"wb").write(data)
        nid+=1
        notes.append({"id":nid,"title":title,"composer":"Scott Joplin","genre":"ragtime",
            "type":"piece","style":"ragtime","key_concert":key,
            "versions":[{"instrument":"piano","transposition":0,"clef":"treble",
                         "key_written":key,"file":rel,"file_id":None}]})
        print(f"  ✓ id={nid} {title}  ({len(data)} байт)")
        added+=1
    json.dump(notes,open(NOTES_JSON,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    print(f"добавлено {added}, всего {len(notes)}")
if __name__=="__main__": main()
