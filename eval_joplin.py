import urllib.request, midi_melody, gen_parts, transcribe
url="https://www.mutopiaproject.org/ftp/JoplinS/maple/maple.mid"
open("/tmp/maple.mid","wb").write(urllib.request.urlopen(url, timeout=60).read())
seq, bpm, div = midi_melody.skyline_melody("/tmp/maple.mid")
print("notes", len(seq), "bpm", bpm)
NN=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
tokens=[(f"{NN[p%12]}{p//12-1}".replace('#','#'), b) for p,b in seq]
notes=[{"midi":p,"start":0,"dur":b,"conf":1.0} for p,b in seq]  # not used; build via build_notes
nl=gen_parts.build_notes([(f"{['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][p%12]}{p//12-1}", b) for p,b in seq], bpm=bpm)
xml=transcribe.render_musicxml(nl, offset=2, tempo_bpm=bpm, title="Maple Leaf Rag — труба B♭ (skyline)")
png=transcribe.render_png(xml)
open("/tmp/maple_tpt.png","wb").write(png); print("png bytes", len(png))
