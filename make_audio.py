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
DRUM_STICK = 37  # side stick — щелчок count-in

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
    root_midi — MIDI корня (для баса)."""
    from music21 import converter, harmony

    score = converter.parse(xml_path)
    chords = []
    for el in score.recurse().getElementsByClass(harmony.ChordSymbol):
        start = el.offset
        dur = el.quarterLength
        pitches = [p.midi for p in el.pitches] if el.pitches else []
        root = el.root().midi if el.root() else (pitches[0] if pitches else 60)
        chords.append((start, dur, pitches, root))
    return chords


# ... truncated for MCP size — PLACEHOLDER