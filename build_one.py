"""Ad-hoc сборщик одного произведения: качает MusicXML с UVA Dataverse по file-id
и рендерит audio+minus через make_audio. Использование:
    python build_one.py <dataverse_file_id> <slug> [bpm]
"""

import sys
import tempfile
import urllib.request

import make_audio

DATAVERSE = "https://dataverse.lib.virginia.edu/api/access/datafile/"


def main():
    fid = sys.argv[1]
    slug = sys.argv[2]
    bpm = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    req = urllib.request.Request(
        DATAVERSE + str(fid), headers={"User-Agent": "jazztone-ingest"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    fd, path = tempfile.mkstemp(suffix=".xml")
    with open(path, "wb") as f:
        f.write(data)
    r = make_audio.make_audio_for_xml(path, slug, bpm=bpm)
    print("bpm     :", bpm)
    print("audio   :", r["audio"])
    print("backing :", r["backing"])


if __name__ == "__main__":
    main()
