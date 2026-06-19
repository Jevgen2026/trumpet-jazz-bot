import struct, sys

def _vlq(d, i):
    v = 0
    while True:
        b = d[i]; i += 1; v = (v << 7) | (b & 0x7f)
        if not (b & 0x80): break
    return v, i

def parse_midi(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'MThd'
    fmt, ntrk, div = struct.unpack('>HHH', d[8:14])
    i = 14
    tracks = []; tempo = 500000
    for _ in range(ntrk):
        assert d[i:i+4] == b'MTrk'
        ln = struct.unpack('>I', d[i+4:i+8])[0]; i += 8
        end = i + ln; t = 0; status = None; evs = []
        on = {}  # (chan,pitch)->start_tick
        while i < end:
            dt, i = _vlq(d, i); t += dt
            b = d[i]
            if b & 0x80: status = b; i += 1
            else: pass
            ev = status
            if ev == 0xFF:
                meta = d[i]; i += 1; ln2, i = _vlq(d, i); data = d[i:i+ln2]; i += ln2
                if meta == 0x51 and ln2 == 3: tempo = struct.unpack('>I', b'\x00'+data)[0]
            elif ev in (0xF0, 0xF7):
                ln2, i = _vlq(d, i); i += ln2
            else:
                hi = ev & 0xF0; chan = ev & 0x0F
                if hi in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    p = d[i]; v = d[i+1]; i += 2
                    if hi == 0x90 and v > 0:
                        on[(chan, p)] = t
                    elif hi == 0x80 or (hi == 0x90 and v == 0):
                        st = on.pop((chan, p), None)
                        if st is not None: evs.append((st, t, p))
                elif hi in (0xC0, 0xD0):
                    i += 1
        tracks.append(evs)
        i = end
    return fmt, div, tempo, tracks

def skyline_melody(path, beats_quant=0.25):
    fmt, div, tempo, tracks = parse_midi(path)
    # выбрать трек-мелодию = с наибольшей средней высотой (и непустой)
    best = max((tr for tr in tracks if tr), key=lambda tr: sum(p for _,_,p in tr)/len(tr))
    notes = sorted(best, key=lambda x: (x[0], -x[2]))
    # skyline: по онсетам берём верхнюю ноту, длительность до следующего онсета
    onsets = sorted(set(s for s,_,_ in notes))
    seq = []
    for k, st in enumerate(onsets):
        top = max(p for s,e,p in notes if s == st)
        nxt = onsets[k+1] if k+1 < len(onsets) else max(e for _,e,_ in notes)
        dur_ticks = nxt - st
        beats = dur_ticks / div
        seq.append((top, round(beats / beats_quant) * beats_quant or beats_quant))
    bpm = round(60_000_000 / tempo)
    return seq, bpm, div

if __name__ == '__main__':
    seq, bpm, div = skyline_melody(sys.argv[1])
    print(f"bpm={bpm} div={div} melody_notes={len(seq)}")
    # midi->name
    NN=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    print([f"{NN[p%12]}{p//12-1}:{b}" for p,b in seq[:30]])
