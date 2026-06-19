"""
Генерация аудио к произведению (concert pitch, на уровне работы):
  • audio   — мелодия (труба) ПОВЕРХ фона (полный плей-элонг, «как должно звучать»)
  • backing — тот же фон БЕЗ трубы (минусовка)

Мелодию берём через parse_pdsa.parse_melody (тот же источник, что и PDF-партии),
аккорды (chord-символы) — через music21 из того же MusicXML.

Джазовый движок (живое ощущение, не робот):
  • свинговые восьмые (swing-warp с лёгким джиттером ratio),
  • мелодия чуть «позади доли» (laid-back) + динам. акценты по метрике/фразе,
  • ходячий бас (walking) с хроматическим подходом к корню след. аккорда,
  • комп = электропиано Rhodes (мягкий клубный тембр), открытые rootless drop-2
    войсинги (без корня, +9-я, тёплый регистр G3..G4) — тихо/легато, балладный
    пэд раз в такт с лёгким арпеджио (мягкая атака), без резких акцентов,
  • свинговый ride + хэт-бэкбит 2/4 (акцент) + лёгкий kick,
  • микро-гуманизация тайминга и velocity (фикс. seed = воспроизводимо).

Рендер: pretty_midi → MIDI → fluidsynth (FluidR3_GM) → ffmpeg → mp3.

CLI:  python make_audio.py <musicxml> <slug> [bpm]
"""

import math
import os
import random
import subprocess
import tempfile

import pretty_midi

import gen_parts
import parse_pdsa

SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
AUDIO_DIR = os.path.join("notes", "audio")

PROG_TRUMPET = 56
PROG_PIANO = 4  # Rhodes EP — мягкий клубный комп, не бьёт по ушам (акуст. рояль резал)
PROG_BASS = 32  # Acoustic Bass
DRUM_KICK, DRUM_SNARE, DRUM_HAT_PEDAL, DRUM_RIDE = 36, 38, 44, 51

# мягкая шинная компрессия плей-элонга: подтягивает выпирающие куски трубы к фону
MIX_COMP = "acompressor=threshold=-16dB:ratio=3:attack=15:release=200"
SWING = 0.62  # позиция свингового «и» внутри доли (0.5 = прямо)
LAIDBACK = 0.02  # доля доли, на сколько мелодия «позади» (расслабленность)
_RND = random.Random(20260618)


def _swing_beat(beat_pos, ratio=SWING):
    """Свинг-варп позиции (в долях) с лёгким джиттером ratio (живой свинг)."""
    r = ratio + _RND.uniform(-0.02, 0.02)
    b = math.floor(beat_pos)
    f = beat_pos - b
    nf = f * (r / 0.5) if f <= 0.5 else r + (f - 0.5) * ((1 - r) / 0.5)
    return b + nf


def _accent(beat):
    """Прибавка velocity по метрике: сильная доля > синкопа > слабая."""
    f = beat - math.floor(beat)
    if f < 0.12:
        return 10  # доля (особенно сильная)
    if abs(f - 0.5) < 0.12:
        return 5  # «и» — джазовый офф-бит
    return 0


def _jit(sec=0.018):
    return _RND.uniform(-sec, sec)


def _vel(base, spread=9):
    return max(1, min(127, int(base + _RND.uniform(-spread, spread))))


# ---------- аккорды через music21 ----------
def parse_chords(xml_path, bpm):
    """[(start_beat, dur_beat, [midi_pitches], root_midi)] из chord-символов.
    Время — в долях (четвертях). Пусто, если нет <harmony>."""
    from music21 import converter, harmony

    score = converter.parse(xml_path)
    flat = score.flatten()
    syms = list(flat.getElementsByClass(harmony.ChordSymbol))
    if not syms:
        return []
    total = float(flat.highestTime)
    out = []
    for i, cs in enumerate(syms):
        s = float(cs.offset)
        e = float(syms[i + 1].offset) if i + 1 < len(syms) else total
        if e <= s:
            continue
        pitches = [p.midi for p in cs.pitches]
        if not pitches:
            continue
        root = cs.root().midi if cs.root() else pitches[0]
        out.append((s, e - s, pitches, root))
    return out


# ---------- голосоведение ----------
def jazz_voicing(pitches, root):
    """Мягкий открытый rootless-войсинг (drop-2) в ТЁПЛОМ регистре G3..G4.
    Корень убираем (его держит бас), +9-я для цвета, макс 4 ноты; верх ≤ G4 —
    подальше от 'звенящей' зоны 2–4 кГц, где рояль режет слух. Drop-2 разводит
    кластер на >октаву → открыто и тепло, без полутоновых тёрок."""
    rpc = root % 12
    pcs = [p % 12 for p in pitches if p % 12 != rpc]
    if not pcs:
        pcs = [p % 12 for p in pitches]
    ninth = (rpc + 2) % 12
    if ninth not in pcs and len(pcs) < 4:
        pcs.append(ninth)
    base = 55  # G3 — тёплый клубный регистр (раньше C4/A3 уезжало в 'звон')
    voiced = sorted({base + ((pc - base) % 12) for pc in pcs})[:4]  # G3..F#4, верх ≤ G4
    if len(voiced) >= 4 and voiced[-2] - 12 >= 48:
        voiced[-2] -= 12  # drop-2: вторую сверху — на октаву вниз (открытый войсинг)
        voiced.sort()
    return voiced


# ---------- инструменты ----------
def build_melody(concert_notes, spb):
    ins = pretty_midi.Instrument(program=PROG_TRUMPET, name="melody")
    prev_end = -1.0
    for n in concert_notes:
        sbeat = float(n["start"]) / spb
        sb = _swing_beat(sbeat)
        eb = _swing_beat((float(n["start"]) + float(n["dur"])) / spb)
        st = sb * spb + LAIDBACK * spb + _jit()  # чуть позади доли
        en = max(st + 0.06, eb * spb - 0.02)
        # лёгкий акцент по метрике/фразе (ослаблен → ровнее, куски не выбиваются)
        v = 72 + 0.4 * _accent(sbeat)  # труба тише: отступает за фон после loudnorm
        if st - prev_end > 0.18:
            v += 3
        ins.notes.append(
            pretty_midi.Note(
                velocity=_vel(v, 4), pitch=int(n["midi"]), start=max(0.0, st), end=en
            )  # узкий разброс velocity → ровная динамика, без скачков
        )
        prev_end = en
    return ins


def build_backing(chords, spb, piano_prog=PROG_PIANO):
    """Walking-бас + мягкий rootless-комп + свинговые барабаны. chords в долях.
    piano_prog задаёт тембр компа (0=Ac.Grand, 4=Rhodes EP)."""
    piano = pretty_midi.Instrument(program=piano_prog, name="comp")
    bass = pretty_midi.Instrument(program=PROG_BASS, name="bass")
    drums = pretty_midi.Instrument(program=0, is_drum=True, name="drums")
    if not chords:
        return [piano, bass, drums]

    def add(inst, pitch, beat, dur_beats, vel, swing=False):
        st = (_swing_beat(beat) if swing else beat) * spb + _jit()
        inst.notes.append(
            pretty_midi.Note(
                velocity=vel,
                pitch=int(pitch),
                start=max(0.0, st),
                end=max(0.0, st) + dur_beats * spb,
            )
        )

    total = int(round(chords[-1][0] + chords[-1][1]))

    def chord_at(beat):
        cur = chords[0]
        for c in chords:
            if c[0] <= beat + 1e-6:
                cur = c
            else:
                break
        return cur

    def is_at(beat):
        return any(abs(c[0] - beat) < 1e-6 for c in chords)

    # --- walking bass: акцент корня на смене, хром. подход к следующему ---
    for b in range(total):
        _, _, pitches, root = chord_at(b)
        rpc = root % 12 + 36
        tones = sorted({p % 12 + 36 for p in pitches} | {rpc, rpc + 7})
        if is_at(b):
            pitch, vel = rpc, _vel(80)  # смена аккорда — акцент (чуть тише)
        elif is_at(b + 1):
            tgt = chord_at(b + 1)[3] % 12 + 36  # хром. подход к след. корню
            pitch, vel = (tgt - 1 if _RND.random() < 0.5 else tgt + 1), _vel(70)
        else:
            pitch, vel = _RND.choice(tones), _vel(68)
        add(bass, pitch, b, 0.92, vel)

    # --- comp: балладный пэд — открытый войсинг, лёгкое арпеджио (мягкая атака),
    #     долгий сустейн, раз в такт; без офф-бит стэбов (раньше долбило каждые 2 доли) ---
    for c in chords:
        s, d, pitches, root = c
        voiced = jazz_voicing(pitches, root)
        t = s
        while t < s + d - 1e-6:
            seg = min(4.0, s + d - t)  # держим как пэд (до целой ноты)
            roll = 0.0
            for (
                p
            ) in voiced:  # арпеджио снизу вверх ~20мс/нота — мягкая, не ударная атака
                add(piano, p, t + roll, seg - roll, _vel(22, 3))  # очень тихо, легато
                roll += 0.04
            t += 4  # реже: один пэд на такт

    # --- swing ride + хэт-бэкбит 2/4 (акцент) + лёгкий kick ---
    for b in range(total):
        add(drums, DRUM_RIDE, b, 0.4, _vel(54 + _accent(b)))
        if b % 2 == 1:  # бэкбит на 2 и 4
            add(drums, DRUM_RIDE, b + 0.667, 0.3, _vel(46), swing=False)
            add(drums, DRUM_HAT_PEDAL, b, 0.3, _vel(70))  # акцент бэкбита
        if b % 2 == 0:
            add(drums, DRUM_KICK, b, 0.3, _vel(36))  # feathering, тихо

    return [piano, bass, drums]


# ---------- рендер ----------
def _write_midi(instruments, path):
    pm = pretty_midi.PrettyMIDI()
    for ins in instruments:
        pm.instruments.append(ins)
    pm.write(path)


def _render_mp3(midi_path, mp3_path, pre_af=""):
    """pre_af — доп. фильтры ДО loudnorm (напр. тёплый EQ для минусовки)."""
    wav = midi_path[:-4] + ".wav"
    subprocess.run(
        ["fluidsynth", "-ni", "-g", "0.8", "-F", wav, "-r", "44100", SF2, midi_path],
        check=True,
        capture_output=True,
    )
    af = "loudnorm=I=-15:TP=-1.5:LRA=11"
    if pre_af:
        af = pre_af + "," + af  # EQ до нормализации, чтобы громкость учла срез
    subprocess.run(
        ["ffmpeg", "-y", "-i", wav, "-ac", "2", "-af", af, "-b:a", "128k", mp3_path],
        check=True,
        capture_output=True,
    )
    os.remove(wav)
    return mp3_path


def make_audio_for_xml(
    xml_path,
    slug,
    bpm=120,
    outdir=AUDIO_DIR,
    piano_prog=PROG_PIANO,
    backing_af="",
    backing_only=False,
):
    """{'audio': мелодия+фон, 'backing': только фон|None} — пути относительно notes/.
    piano_prog — тембр компа; backing_af — тёплый EQ только для минусовки;
    backing_only — не рендерить полный микс (быстрее, для подбора звука минуса)."""
    os.makedirs(outdir, exist_ok=True)
    spb = 60.0 / bpm
    seq, _f, _c, _t = parse_pdsa.parse_melody(xml_path)
    concert_notes = gen_parts.build_notes(seq, bpm=bpm)
    if not concert_notes:
        return {"audio": None, "backing": None}

    chords = parse_chords(xml_path, bpm)
    melody = build_melody(concert_notes, spb)
    backing = build_backing(chords, spb, piano_prog=piano_prog)

    tmp = tempfile.mkdtemp()
    result = {"audio": None, "backing": None}
    if not backing_only:
        full_mid = os.path.join(tmp, "full.mid")
        _write_midi([melody] + backing, full_mid)
        audio_mp3 = os.path.join(outdir, f"{slug}.mp3")
        _render_mp3(full_mid, audio_mp3, pre_af=MIX_COMP)
        result["audio"] = os.path.relpath(audio_mp3, "notes")

    if chords:
        bk_mid = os.path.join(tmp, "bk.mid")
        _write_midi(backing, bk_mid)
        bk_mp3 = os.path.join(outdir, f"{slug}_minus.mp3")
        _render_mp3(bk_mid, bk_mp3, pre_af=backing_af)
        result["backing"] = os.path.relpath(bk_mp3, "notes")
    return result


if __name__ == "__main__":
    import sys

    xml = sys.argv[1]
    slug = sys.argv[2]
    bpm = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    r = make_audio_for_xml(xml, slug, bpm)
    print("audio   :", r["audio"])
    print("backing :", r["backing"])
