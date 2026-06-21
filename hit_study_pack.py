"""
Hit Study Pack — генератор учебного пакета по одной пьесе (за Telegram Stars).
Состав (см. дизайн): аккордовая сетка + гарм. разбор + минус (полная длина) +
гайд-тоны + chord-scale карта + оригинальные лики + targeting-упражнения +
план освоения + чек-лист + стилевая справка.

ЛЕГАЛЬНОСТЬ: аккордовая прогрессия (сетка) не охраняется → пакет строится на
СЕТКЕ (входные изменения), а не на копирайтной мелодии. Гайд-тоны считаются
детерминированно из сетки (без галлюцинаций). Текстовые разделы — Claude с
Authentic Jazz Filter, ГРОУНДЯТСЯ на переданной сетке.

Вход: changes = список тактов, каждый такт = список аккорд-символов, напр.
    [["Dm7"], ["G7"], ["Cmaj7"], ["Cmaj7"]]  (один такт = одна строка сетки-бара)
"""

import os
import re


def norm_symbol(sym):
    """Нормализация аккорд-символа под music21.harmony.ChordSymbol.
    music21 жадно режет корень и ломается на flat-корне перед maj7/m7
    ('Bbmaj7' → пытается abbrev 'bmaj7'). Лечим: flat-корень 'Xb' → 'X-'
    (только акциденталь сразу после буквы ноты; 'b5'/'b9' не трогаем).
    Отображаем юзеру всегда ОРИГИНАЛ — это только для разбора пьес."""
    return re.sub(r"^([A-G])b", r"\1-", sym.strip())


def chord_symbol(sym):
    """music21 ChordSymbol из символа с нормализацией корня (или бросает)."""
    from music21 import harmony

    return harmony.ChordSymbol(norm_symbol(sym))


# ---------- ДЕТЕРМИНИРОВАННЫЕ КАРТЫ: лад под аккорд + форма ----------
_SCALES = {
    "Ionian": [0, 2, 4, 5, 7, 9, 11],
    "Lydian": [0, 2, 4, 6, 7, 9, 11],
    "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "Dorian": [0, 2, 3, 5, 7, 9, 10],
    "Aeolian": [0, 2, 3, 5, 7, 8, 10],
    "Locrian": [0, 1, 3, 5, 6, 8, 10],
    "Melodic minor": [0, 2, 3, 5, 7, 9, 11],
    "Whole-half dim": [0, 2, 3, 5, 6, 8, 9, 11],
    "Altered": [0, 1, 3, 4, 6, 8, 10],
    "Whole tone": [0, 2, 4, 6, 8, 10],
}


def chord_scale(chord):
    """Аккорд → (название лада, корень pitch-class, интервалы). Детерминированно:
    корень/спец-качества из строки, остальное (3/5/7) — из music21. (None,…) если нет корня."""
    import re

    from transcribe import _parse_chord

    root, _suffix = _parse_chord(
        (chord or "").split("/")[0]
    )  # _parse_chord сам ест 'b'
    if root is None:
        return None, None, None
    figure = (chord or "").lower()
    if "alt" in figure or "7#5" in figure or "7b9" in figure or "7#9" in figure:
        name = "Altered"
    elif "dim" in figure or "°" in (chord or ""):
        name = "Whole-half dim"
    elif "aug" in figure or "+" in (chord or ""):
        name = "Whole tone"
    elif re.search(r"m\(?(maj7|ma7|M7|\^7|#7|∆)", chord or ""):
        name = "Melodic minor"
    else:
        third = fifth = seventh = None
        try:
            cs = chord_symbol(chord)

            def iv(tone):
                return (tone.pitchClass - root) % 12 if tone is not None else None

            third, fifth, seventh = iv(cs.third), iv(cs.fifth), iv(cs.seventh)
        except Exception:
            pass
        if third == 3 and seventh == 11:
            name = "Melodic minor"
        elif third == 3 and fifth == 6:
            name = "Locrian"
        elif third == 3:
            name = "Dorian"
        elif third == 4 and seventh == 10:
            name = "Mixolydian"
        elif third == 4:
            name = "Ionian"
        else:
            name = "Dorian" if ("m" in figure and "maj" not in figure) else "Ionian"
    return name, root, _SCALES[name]


def chord_scale_map(changes):
    """[(такт, аккорд, лад)] — детерминированная карта лад-гамм по сетке."""
    out = []
    for i, bar in enumerate(changes, 1):
        for ch in bar or []:
            if not ch:
                continue
            name, _root, _iv = chord_scale(ch)
            out.append({"bar": i, "chord": ch, "scale": name or "?"})
    return out


def detect_form(changes, section_len=8):
    """Маркировка формы: секции по section_len тактов, одинаковые → одна буква (AABA)."""

    def norm(bar):
        return tuple(c.strip() for c in (bar or []))

    sections, seen = [], {}
    for i in range(0, len(changes), section_len):
        key = tuple(norm(b) for b in changes[i : i + section_len])
        if key not in seen:
            seen[key] = chr(ord("A") + len(seen))
        sections.append((seen[key], i + 1, changes[i : i + section_len]))
    return sections


def form_string(changes, section_len=8):
    """Краткая форма строкой: 'AABA (32 такта, секции по 8)'."""
    sec = detect_form(changes, section_len)
    if not sec:
        return ""
    return (
        f"{''.join(s[0] for s in sec)} ({len(changes)} тактов, секции по {section_len})"
    )


# ---------- РОЛЬ ИНСТРУМЕНТА (соло / комп / бас) ----------
_COMP_INSTR = {"piano", "guitar"}
_BASS_INSTR = {"contrabass"}


def instrument_role(instrument):
    """Роль в ансамбле → тип учебного контента: comp (пиано/гитара), bass, иначе solo."""
    if instrument in _COMP_INSTR:
        return "comp"
    if instrument in _BASS_INSTR:
        return "bass"
    return "solo"


_ROLE_FOCUS = {
    ("ru", "solo"): (
        "однолинейная импровизация: enclosures и хром. подходы к аккордовым тонам, "
        "targeting на сильную долю, ритм. смещение, фразировка с дыханием"
    ),
    ("ru", "comp"): (
        "АККОМПАНЕМЕНТ (не соло!): shell-войсинги (3 и 7), rootless A/B войсинги "
        "(3-5-7-9 / 7-9-3-5), comping-ритмы (Charleston, антиципации), голосоведение "
        "верхних голосов по форме. НЕ давай одноголосные соло-лики"
    ),
    ("ru", "bass"): (
        "WALKING BASS (не соло!): корни на сильную долю, обводка аккордовых тонов, "
        "хром./диатон. подходы к корню следующего аккорда, two-feel vs walking, "
        "построение линии по форме. НЕ давай соло-лики верхнего регистра"
    ),
    ("en", "solo"): (
        "single-line improvisation: enclosures & chromatic approaches to chord tones, "
        "targeting strong-beat chord tones, rhythmic displacement, phrasing"
    ),
    ("en", "comp"): (
        "COMPING (not soloing!): shell voicings (3 & 7), rootless A/B voicings "
        "(3-5-7-9 / 7-9-3-5), comping rhythms (Charleston, anticipations), upper-voice "
        "voice leading through the form. Do NOT give single-line solo licks"
    ),
    ("en", "bass"): (
        "WALKING BASS (not soloing!): roots on strong beats, chord-tone outlines, "
        "chromatic/diatonic approaches to the next root, two-feel vs walking, "
        "building the line through the form. Do NOT give high-register solo licks"
    ),
}
_ROLE_SECTIONS = {
    ("ru", "solo"): (
        "## Гармонический разбор\n## Chord–scale карта\n"
        "## 5 оригинальных ликов (имена нот, над ключевым ii-V-I)\n"
        "## Targeting-упражнения\n## План на неделю\n## Чек-лист мастерства\n"
        "## Стиль и что слушать (только легальные ссылки)"
    ),
    ("ru", "comp"): (
        "## Гармонический разбор\n## Chord–scale карта\n"
        "## Войсинги (shell 3-7 + rootless A/B, имена нот по аккордам)\n"
        "## Comping-ритмы (нотные паттерны, антиципации)\n"
        "## Голосоведение верхних голосов по форме\n## План на неделю\n"
        "## Чек-лист мастерства\n## Стиль и что слушать (только легальные ссылки)"
    ),
    ("ru", "bass"): (
        "## Гармонический разбор\n## Root motion по форме\n"
        "## Walking-линия (имена нот, 4 такта над ключевым ii-V-I)\n"
        "## Подходные тоны к корням (упражнения)\n## План на неделю\n"
        "## Чек-лист мастерства\n## Стиль и что слушать (только легальные ссылки)"
    ),
    ("en", "solo"): (
        "## Harmonic analysis\n## Chord–scale map\n"
        "## 5 original licks (note names, over the key ii-V-I)\n"
        "## Targeting exercises\n## Study plan (1 week)\n## Mastery checklist\n"
        "## Style & listening (legal links only)"
    ),
    ("en", "comp"): (
        "## Harmonic analysis\n## Chord–scale map\n"
        "## Voicings (shell 3-7 + rootless A/B, note names per chord)\n"
        "## Comping rhythms (notated patterns, anticipations)\n"
        "## Upper-voice voice leading through the form\n## Study plan (1 week)\n"
        "## Mastery checklist\n## Style & listening (legal links only)"
    ),
    ("en", "bass"): (
        "## Harmonic analysis\n## Root motion through the form\n"
        "## Walking line (note names, 4 bars over the key ii-V-I)\n"
        "## Approach tones to roots (exercises)\n## Study plan (1 week)\n"
        "## Mastery checklist\n## Style & listening (legal links only)"
    ),
}


# ---------- ГАЙД-ТОНЫ (детерминированно, music21) ----------
def guide_tones(changes):
    """Для каждого аккорда сетки → его 3-я и 7-я ступени (основа голосоведения).
    Возвращает [{bar, chord, third, seventh}]. music21 берёт реальные тоны аккорда,
    без выдумывания. Незнакомый символ → пропуск с пометкой."""
    out = []
    for bar_idx, bar in enumerate(changes, 1):
        for ch in bar:
            try:
                cs = chord_symbol(ch)
                third = cs.third.name if cs.third else None
                seventh = cs.seventh.name if cs.seventh else None
            except Exception:
                out.append(
                    {
                        "bar": bar_idx,
                        "chord": ch,
                        "third": None,
                        "seventh": None,
                        "err": True,
                    }
                )
                continue
            out.append(
                {"bar": bar_idx, "chord": ch, "third": third, "seventh": seventh}
            )
    return out


def changes_to_chart(changes, per_line=4):
    """Сетка в текст: '| Dm7 | G7 | Cmaj7 | Cmaj7 |' по per_line тактов в строке."""
    bars = ["  ".join(bar) if bar else "%" for bar in changes]
    lines = []
    for i in range(0, len(bars), per_line):
        lines.append("| " + " | ".join(bars[i : i + per_line]) + " |")
    return "\n".join(lines)


# ---------- ТЕКСТОВЫЕ РАЗДЕЛЫ (Claude + Authentic Jazz Filter) ----------
def _llm(client, system, user, max_tokens=1500):
    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(
        b.text for b in resp.content if getattr(b, "type", None) == "text"
    ).strip()


def generate_sections(
    title, changes, instrument="trumpet", level="medium", lang="ru", style=None
):
    """Разборные разделы пакета (markdown) через Claude, грундятся на сетке.
    None если ANTHROPIC_API_KEY не задан. Прогоняет Authentic Jazz Filter."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except Exception:
        return None

    chart = changes_to_chart(changes)
    gts = guide_tones(changes)
    gt_str = "; ".join(
        f"{g['chord']}: 3={g['third']} 7={g['seventh']}"
        for g in gts
        if not g.get("err")
    )

    role = instrument_role(instrument)
    lang_key = "en" if lang == "en" else "ru"
    focus = _ROLE_FOCUS[(lang_key, role)]
    role_sections = _ROLE_SECTIONS[(lang_key, role)]

    if lang_key == "en":
        sys = (
            "You are a Berklee jazz professor + Real Book editor building a serious, practical "
            f"study pack for ONE tune for a {instrument} student (level: {level}). "
            f"This instrument's role is '{role}'. FOCUS: {focus}. "
            "Use ONLY the chord changes provided — never quote or notate the copyrighted melody. "
            "Be concrete and playable: real note names, chord tones, scales, named exercises. "
            "Correct jazz terminology. Apply the Authentic Jazz Filter (enclosures & chromatic "
            "approaches to chord tones, targeting strong beats, rhythmic displacement, correct "
            "dominant tensions b9/#9/#11/b13). Output clean markdown EXACTLY with these sections:\n"
            f"{role_sections}"
        )
    else:
        sys = (
            "Ты профессор джаза Berklee + редактор Real Book, собираешь СЕРЬЁЗНЫЙ практический "
            f"учебный пакет по ОДНОЙ пьесе для ученика на {instrument} (уровень: {level}). "
            f"Роль инструмента — '{role}'. ФОКУС: {focus}. "
            "Используй ТОЛЬКО переданную аккордовую сетку — НЕ цитируй и НЕ нотируй копирайтную "
            "мелодию. Конкретно и играбельно: реальные ноты, аккордовые тоны, гаммы, названные "
            "упражнения. Верная джазовая терминология. Прогони Authentic Jazz Filter (enclosures "
            "и хром. подходы, targeting на сильную долю, ритм. смещение, тензии b9/#9/#11/b13). "
            "Выдай чистый markdown РОВНО с разделами:\n"
            f"{role_sections}"
        )
    # Детерминированные данные → отдаём LLM как ИСТИНУ (лады/форму не галлюцинирует).
    cs_str = "; ".join(f"{d['chord']}→{d['scale']}" for d in chord_scale_map(changes))
    user = (
        f"Пьеса: {title}\nСтиль: {style or 'jazz'}\nИнструмент: {instrument}\n"
        f"Форма (ДЕТЕРМИНИРОВАННО): {form_string(changes)}\n\n"
        f"Аккордовая сетка:\n{chart}\n\nГайд-тоны (3/7 по аккордам): {gt_str}\n\n"
        f"Лад-гаммы (ДЕТЕРМИНИРОВАННО, используй их в Chord–scale карте): {cs_str}"
    )
    client = anthropic.Anthropic()
    try:
        return _llm(client, sys, user)
    except Exception:
        return None


def build_pack(
    title, changes, instrument="trumpet", level="medium", lang="ru", style=None
):
    """Собрать данные пакета (без PDF/аудио — это следующие кирпичи).
    Возвращает dict: chart, guide_tones, sections(markdown)."""
    return {
        "title": title,
        "instrument": instrument,
        "chart": changes_to_chart(changes),
        "guide_tones": guide_tones(changes),
        "sections": generate_sections(title, changes, instrument, level, lang, style),
    }
