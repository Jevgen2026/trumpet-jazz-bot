"""
Каталог аккордовых СЕТОК для Hit Study Pack.

ЛЕГАЛЬНОСТЬ: аккордовая прогрессия (гармоническая сетка) НЕ охраняется авторским
правом — охраняется конкретная мелодия. Поэтому пакет строится на сетке, а мелодию
мы не цитируем и не нотируем. Все пьесы здесь — public domain в РФ:
  • Темы Чарли Паркера †1955 → его СОЛЬНЫЕ темы PD в РФ с 2026.
  • Музыка Гершвина †1937 → PD (без текста Иры Гершвина †1983).

Формат сетки: changes = список тактов; такт = список аккорд-символов (1, 2 или 4),
делящих такт поровну. Символы — в нотации, которую парсит music21.harmony.ChordSymbol.
'%' = повтор предыдущего такта (для аудио/гайд-тонов держим прошлый аккорд).
"""

# fmt: off
TUNES = {
    "nows_the_time": {
        "title": "Now's the Time",
        "composer": "Charlie Parker",
        "style": "bebop blues",
        "key": "F",
        "form": "12-тактовый блюз",
        "bpm": 160,
        "level": "easy",
        "pd_note": "Паркер †1955 → сольные темы PD в РФ с 2026",
        "changes": [
            ["F7"], ["Bb7"], ["F7"], ["F7"],
            ["Bb7"], ["Bb7"], ["F7"], ["D7"],
            ["Gm7"], ["C7"], ["F7", "D7"], ["Gm7", "C7"],
        ],
    },
    "blues_for_alice": {
        "title": "Blues for Alice",
        "composer": "Charlie Parker",
        "style": "bebop (Bird blues)",
        "key": "F",
        "form": "12 тактов, нисходящие ii–V",
        "bpm": 180,
        "level": "advanced",
        "pd_note": "Паркер †1955 → сольные темы PD в РФ с 2026",
        "changes": [
            ["Fmaj7"], ["Em7b5", "A7"], ["Dm7", "G7"], ["Cm7", "F7"],
            ["Bb7"], ["Bbm7", "Eb7"], ["Am7", "D7"], ["Abm7", "Db7"],
            ["Gm7"], ["C7"], ["Fmaj7", "D7"], ["Gm7", "C7"],
        ],
    },
    "confirmation": {
        "title": "Confirmation",
        "composer": "Charlie Parker",
        "style": "bebop",
        "key": "F",
        "form": "AABA, 32 такта",
        "bpm": 180,
        "level": "advanced",
        "pd_note": "Паркер †1955 → сольные темы PD в РФ с 2026",
        "changes": [
            # A1
            ["Fmaj7"], ["Em7b5", "A7"], ["Dm7", "G7"], ["Cm7", "F7"],
            ["Bbmaj7"], ["Bbm7", "Eb7"], ["Am7", "D7"], ["Gm7", "C7"],
            # A2
            ["Fmaj7"], ["Em7b5", "A7"], ["Dm7", "G7"], ["Cm7", "F7"],
            ["Bbmaj7"], ["Bbm7", "Eb7"], ["Fmaj7"], ["Gm7", "C7"],
            # B
            ["Cm7"], ["F7"], ["Bbmaj7"], ["Bbmaj7"],
            ["Am7"], ["D7"], ["Gm7"], ["C7"],
            # A3
            ["Fmaj7"], ["Em7b5", "A7"], ["Dm7", "G7"], ["Cm7", "F7"],
            ["Bbmaj7"], ["Bbm7", "Eb7"], ["Fmaj7"], ["Fmaj7"],
        ],
    },
    "i_got_rhythm": {
        "title": "I Got Rhythm",
        "composer": "George Gershwin",
        "style": "swing (rhythm changes)",
        "key": "Bb",
        "form": "AABA, 32 такта",
        "bpm": 200,
        "level": "medium",
        "pd_note": "Гершвин †1937 → музыка PD (без текста Иры Гершвина)",
        "changes": [
            # A1
            ["Bbmaj7", "G7"], ["Cm7", "F7"], ["Dm7", "G7"], ["Cm7", "F7"],
            ["Fm7", "Bb7"], ["Ebmaj7", "Edim7"], ["Dm7", "G7"], ["Cm7", "F7"],
            # A2
            ["Bbmaj7", "G7"], ["Cm7", "F7"], ["Dm7", "G7"], ["Cm7", "F7"],
            ["Fm7", "Bb7"], ["Ebmaj7", "Edim7"], ["Bbmaj7"], ["Bbmaj7"],
            # B (dominant cycle)
            ["D7"], ["D7"], ["G7"], ["G7"],
            ["C7"], ["C7"], ["F7"], ["F7"],
            # A3
            ["Bbmaj7", "G7"], ["Cm7", "F7"], ["Dm7", "G7"], ["Cm7", "F7"],
            ["Fm7", "Bb7"], ["Ebmaj7", "Edim7"], ["Bbmaj7"], ["Bbmaj7"],
        ],
    },
    "donna_lee": {
        "title": "Donna Lee",
        "composer": "Charlie Parker / Miles Davis",
        "style": "bebop (на сетке Indiana)",
        "key": "Ab",
        "form": "32 такта (Indiana changes)",
        "bpm": 210,
        "level": "advanced",
        "pd_note": "Контрафакт на «Indiana» (Hanley †1942, PD); используется только сетка, мелодия не цитируется",
        # Нотный лист первоисточника гармонии в библиотеке (PD). relation:
        # "contrafact" — другая мелодия, та же сетка; "same" — реальный лид-шит пьесы.
        "lead_sheet": {"note_id": 91, "relation": "contrafact", "title": "Indiana"},
        "changes": [
            ["Abmaj7"], ["F7"], ["Bb7"], ["Bb7"],
            ["Bbm7"], ["Eb7"], ["Abmaj7"], ["Ebm7", "Ab7"],
            ["Dbmaj7"], ["Gb7"], ["Abmaj7"], ["F7"],
            ["Bb7"], ["Bb7"], ["Bbm7"], ["Eb7"],
            ["Abmaj7"], ["F7"], ["Bb7"], ["Bb7"],
            ["C7b9"], ["Gm7b5", "C7b9"], ["Fm7"], ["Gm7b5", "C7b9"],
            ["Fm7"], ["Gm7b5", "C7b9"], ["Fm7"], ["Bdim7"],
            ["Abmaj7", "F7"], ["Bbm7", "Eb7"], ["Abmaj7"], ["Bbm7", "Eb7"],
        ],
    },
    "hot_house": {
        "title": "Hot House",
        "composer": "Tadd Dameron",
        "style": "bebop (на сетке What Is This Thing Called Love)",
        "key": "C",
        "form": "AABA, 32 такта",
        "bpm": 180,
        "level": "advanced",
        "pd_note": "Контрафакт на «What Is This Thing Called Love»; используется только сетка, мелодия не цитируется",
        "changes": [
            # A1
            ["Gm7b5"], ["C7"], ["Fm7"], ["Fm7"],
            ["Dm7b5"], ["G7"], ["Cmaj7"], ["Cmaj7"],
            # A2
            ["Gm7b5"], ["C7"], ["Fm7"], ["Fm7"],
            ["Dm7b5"], ["G7"], ["Cmaj7"], ["Cmaj7"],
            # B (модуляция в Bb)
            ["Cm7"], ["F7"], ["Bbmaj7"], ["Bbmaj7"],
            ["Dm7b5"], ["G7"], ["Cmaj7"], ["Cmaj7"],
            # A3
            ["Gm7b5"], ["C7"], ["Fm7"], ["Fm7"],
            ["Dm7b5"], ["G7"], ["Cmaj7"], ["Cmaj7"],
        ],
    },
    "oleo": {
        "title": "Oleo",
        "composer": "Sonny Rollins",
        "style": "bebop (rhythm changes)",
        "key": "Bb",
        "form": "AABA, 32 такта",
        "bpm": 220,
        "level": "advanced",
        "pd_note": "Контрафакт на rhythm changes (прогрессия Гершвина не охраняется); мелодия Роллинза не используется",
        "changes": [
            # A1
            ["Bbmaj7", "G7"], ["Cm7", "F7"], ["Dm7", "G7"], ["Cm7", "F7"],
            ["Fm7", "Bb7"], ["Ebmaj7", "Ab7"], ["Dm7", "G7"], ["Cm7", "F7"],
            # A2
            ["Bbmaj7", "G7"], ["Cm7", "F7"], ["Dm7", "G7"], ["Cm7", "F7"],
            ["Fm7", "Bb7"], ["Ebmaj7", "Ab7"], ["Bbmaj7"], ["Bbmaj7"],
            # B (dominant cycle)
            ["D7"], ["D7"], ["G7"], ["G7"],
            ["C7"], ["C7"], ["F7"], ["F7"],
            # A3
            ["Bbmaj7", "G7"], ["Cm7", "F7"], ["Dm7", "G7"], ["Cm7", "F7"],
            ["Fm7", "Bb7"], ["Ebmaj7", "Ab7"], ["Bbmaj7"], ["Bbmaj7"],
        ],
    },
}
# fmt: on


def get(slug):
    """Сетка пьесы по slug или None."""
    return TUNES.get(slug)


def list_tunes():
    """[(slug, title, style, level)] для меню — порядок по сложности."""
    order = {"easy": 0, "medium": 1, "advanced": 2}
    items = [
        (slug, t["title"], t["style"], t.get("level", "medium"))
        for slug, t in TUNES.items()
    ]
    items.sort(key=lambda x: order.get(x[3], 1))
    return items
