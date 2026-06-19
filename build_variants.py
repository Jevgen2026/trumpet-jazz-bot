"""Сборка двух минусовок одного произведения для A/B-сравнения тембра компа:
  • rhodes — электропиано (Rhodes EP), натуральный звук
  • grand  — акустический рояль + тёплый EQ (срез 'звенящего' верха)
Качает MusicXML с UVA Dataverse. Использование:
    python build_variants.py <dataverse_file_id> [bpm]
Пишет в notes/audio/: rhodes_minus.mp3, grand_minus.mp3
"""

import sys
import tempfile
import urllib.request

import make_audio

DATAVERSE = "https://dataverse.lib.virginia.edu/api/access/datafile/"

# тёплый EQ для рояля: срез presence-зоны (бит по ушам) + лёгкий low-pass от сизла
GRAND_AF = "highshelf=f=2800:g=-6,lowpass=f=8500"


def main():
    fid = sys.argv[1]
    bpm = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    req = urllib.request.Request(
        DATAVERSE + str(fid), headers={"User-Agent": "jazztone-ingest"}
    )
    data = urllib.request.urlopen(req, timeout=60).read()
    fd, path = tempfile.mkstemp(suffix=".xml")
    with open(path, "wb") as f:
        f.write(data)

    # Rhodes EP (program 4) — натурально, без EQ
    make_audio.make_audio_for_xml(
        path, "rhodes", bpm=bpm, piano_prog=4, backing_only=True
    )
    # Acoustic Grand (program 0) — приглушённый тёплым EQ
    make_audio.make_audio_for_xml(
        path, "grand", bpm=bpm, piano_prog=0, backing_af=GRAND_AF, backing_only=True
    )
    print("ok: rhodes_minus.mp3, grand_minus.mp3")


if __name__ == "__main__":
    main()
