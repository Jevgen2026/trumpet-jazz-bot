"""
Анализ интонации записанной игры (монофония, без librosa — только numpy).
Вход: путь к WAV (моно/стерео, 16/8/32-bit). Выход: список нот + сводка.
"""
import wave
import numpy as np

NOTE_NAMES = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B']
A4 = 440.0


def _read_wav(path):
    with wave.open(path, 'rb') as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if sw == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sw == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    else:  # 32-bit
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    return data, sr


def _acf_pitch_conf(frame, sr, fmin, fmax):
    """Высота кадра через нормированную автокорреляцию (FFT).
    Возвращает (freq, strength): strength = высота ACF-пика 0..1 (уверенность).
    (0.0, 0.0) = нет устойчивого тона."""
    frame = frame - frame.mean()
    rms = float(np.sqrt(np.mean(frame ** 2)))
    if rms < 0.01:
        return 0.0, 0.0
    n = len(frame)
    spec = np.fft.rfft(frame, 2 * n)
    acf = np.fft.irfft(spec * np.conj(spec))[:n]
    if acf[0] <= 0:
        return 0.0, 0.0
    acf = acf / acf[0]
    lag_min = max(1, int(sr / fmax))
    lag_max = min(int(sr / fmin), n - 1)
    if lag_max <= lag_min:
        return 0.0, 0.0
    seg = acf[lag_min:lag_max]
    peak = lag_min + int(np.argmax(seg))
    strength = float(acf[peak])
    if strength < 0.3:  # слабая периодичность → нет ноты
        return 0.0, 0.0
    if 0 < peak < n - 1:  # параболическая интерполяция вершины
        a, b, c = acf[peak - 1], acf[peak], acf[peak + 1]
        denom = a - 2 * b + c
        if denom != 0:
            peak = peak + 0.5 * (a - c) / denom
    return (sr / peak if peak > 0 else 0.0), strength


def _acf_pitch(frame, sr, fmin, fmax):
    """Высота кадра (без уверенности). 0 = нет устойчивого тона."""
    return _acf_pitch_conf(frame, sr, fmin, fmax)[0]


def _hz_to_midi_cents(freq):
    midi_f = 69.0 + 12.0 * np.log2(freq / A4)
    m = int(round(midi_f))
    cents = int(round((midi_f - m) * 100))
    return m, cents


def analyze_performance(path, fmin=70.0, fmax=1500.0):
    """Разбирает запись: возвращает ноты с отклонением в центах и сводку."""
    data, sr = _read_wav(path)
    win, hop = 2048, 512
    if len(data) < win:
        return {'ok': False, 'reason': 'too_short', 'notes': []}

    frames = []
    for start in range(0, len(data) - win, hop):
        f0 = _acf_pitch(data[start:start + win], sr, fmin, fmax)
        frames.append(_hz_to_midi_cents(f0) if f0 > 0 else (None, None))

    # Сегментация в ноты: подряд идущие кадры с одинаковым MIDI-номером.
    notes = []
    cur_m, cur_cents = None, []
    min_frames = max(3, int(0.12 * sr / hop))  # нота >= ~120 мс

    def flush():
        if cur_m is not None and len(cur_cents) >= min_frames:
            med = int(np.median(cur_cents))
            name = NOTE_NAMES[cur_m % 12] + str(cur_m // 12 - 1)
            # Отклонение в герцах от ближайшей ноты (для отображения вместо центов).
            f_target = A4 * 2.0 ** ((cur_m - 69) / 12.0)
            hz = f_target * (2.0 ** (med / 1200.0) - 1.0)
            notes.append({'note': name, 'cents': med, 'hz': round(hz, 1)})

    for m, c in frames:
        if m is None:
            flush(); cur_m, cur_cents = None, []
            continue
        if m == cur_m:
            cur_cents.append(c)
        else:
            flush(); cur_m, cur_cents = m, [c]
    flush()

    if not notes:
        return {'ok': False, 'reason': 'no_pitch', 'notes': []}

    cents = [n['cents'] for n in notes]
    abs_c = [abs(c) for c in cents]
    abs_hz = [abs(n['hz']) for n in notes]
    in_tune = sum(1 for a in abs_c if a <= 10)
    return {
        'ok': True,
        'notes': notes,
        'count': len(notes),
        'in_tune': in_tune,
        'accuracy': round(100 * in_tune / len(notes)),
        'mean_abs_hz': round(float(np.mean(abs_hz)), 1),
        'mean_signed_cents': int(round(float(np.mean(cents)))),  # >0 высит, <0 низит
        'spread_cents': int(round(float(np.std(cents)))),        # «гуляние» высоты
    }
