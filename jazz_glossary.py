# -*- coding: utf-8 -*-
"""
Словарь джаз-терминов для пункта меню «Словарь» в боте.

Контент согласован со скиллом music-expert (аутентичная терминология, ученики-
духовики/джаз, работающие с лид-шитами и Hit Study Pack). Двуязычно (ru/en).

Структура: GLOSSARY[cat_key] = {"title": {ru,en}, "terms": [ {term:{ru,en},
def:{ru,en}} ... ]}. Порядок категорий — в CATEGORIES.
"""

CATEGORIES = ["harmony", "form", "rhythm", "improv", "sound"]

GLOSSARY = {
    "harmony": {
        "title": {"ru": "🎹 Гармония", "en": "🎹 Harmony"},
        "terms": [
            {
                "term": {"ru": "ii–V–I", "en": "ii–V–I"},
                "def": {
                    "ru": "Базовый гармонический оборот джаза: Dm7–G7–Cmaj7. Двигатель тональности; отрабатывается во всех 12 тональностях.",
                    "en": "The core jazz cadence: Dm7–G7–Cmaj7. The engine of tonal motion; practiced in all 12 keys.",
                },
            },
            {
                "term": {"ru": "Гайд-тоны (guide tones)", "en": "Guide tones"},
                "def": {
                    "ru": "3-я и 7-я ступени аккорда: определяют его качество и плавно ведут голос через смену аккордов (7→3).",
                    "en": "The 3rd and 7th of a chord — they define its quality and voice-lead smoothly between chords (7→3).",
                },
            },
            {
                "term": {"ru": "Voicing (голосоведение аккорда)", "en": "Voicing"},
                "def": {
                    "ru": "Конкретное расположение нот аккорда по голосам. От него зависит «цвет» гармонии.",
                    "en": "The specific vertical arrangement of a chord's notes. Determines the chord's color.",
                },
            },
            {
                "term": {"ru": "Rootless voicing", "en": "Rootless voicing"},
                "def": {
                    "ru": "Аккорд без основного тона (его берёт бас): освобождает руку компующего под тенсии (9, 11, 13).",
                    "en": "A chord voiced without its root (the bass covers it), freeing the comper to add tensions (9, 11, 13).",
                },
            },
            {
                "term": {"ru": "Turnaround (тёрнэраунд)", "en": "Turnaround"},
                "def": {
                    "ru": "Короткий оборот в конце формы (часто I–VI–ii–V), возвращающий к началу для нового хоруса.",
                    "en": "A short progression at the end of a form (often I–VI–ii–V) that loops back to the top for the next chorus.",
                },
            },
            {
                "term": {
                    "ru": "Тритоновая замена (tritone sub)",
                    "en": "Tritone substitution",
                },
                "def": {
                    "ru": "Замена доминанты на другую в тритоне (G7→D♭7): хроматический ход баса и свежие тенсии.",
                    "en": "Replacing a dominant with the one a tritone away (G7→D♭7): chromatic bass motion and fresh tensions.",
                },
            },
            {
                "term": {"ru": "Тенсии / надстройки", "en": "Tensions / extensions"},
                "def": {
                    "ru": "Ноты аккорда выше септимы: 9, 11, 13 (и альтерации ♭9/♯9/♯11/♭13). Источник джазовой краски.",
                    "en": "Notes above the 7th: 9, 11, 13 (and alterations ♭9/♯9/♯11/♭13). The source of jazz color.",
                },
            },
        ],
    },
    "form": {
        "title": {"ru": "🧩 Форма", "en": "🧩 Form"},
        "terms": [
            {
                "term": {"ru": "Lead sheet", "en": "Lead sheet"},
                "def": {
                    "ru": "Нотация темы: мелодия + буквенные аккорды (и текст). Основной формат стандартов (Real Book).",
                    "en": "Notation of a tune: melody + chord symbols (and lyrics). The standard format (Real Book).",
                },
            },
            {
                "term": {"ru": "Chart (нотная карта)", "en": "Chart"},
                "def": {
                    "ru": "Рабочая нотная «карта» пьесы для музыканта: сетка аккордов, форма, разметка секций.",
                    "en": "A working notation 'map' of a tune: chord grid, form, section markings.",
                },
            },
            {
                "term": {"ru": "Head (тема)", "en": "Head"},
                "def": {
                    "ru": "Изложение основной мелодии в начале и в конце пьесы («head in / head out»).",
                    "en": "The main melody, stated at the start and end of a performance ('head in / head out').",
                },
            },
            {
                "term": {"ru": "Chorus (хорус)", "en": "Chorus"},
                "def": {
                    "ru": "Один полный проход по форме пьесы. Длину соло измеряют в хорусах.",
                    "en": "One full pass through the tune's form. Solos are counted in choruses.",
                },
            },
            {
                "term": {"ru": "AABA", "en": "AABA"},
                "def": {
                    "ru": "Самая частая 32-тактовая песенная форма: два запева A, контрастный бридж B, реприза A.",
                    "en": "The most common 32-bar song form: two A sections, a contrasting bridge (B), then A.",
                },
            },
            {
                "term": {"ru": "Bridge (бридж)", "en": "Bridge"},
                "def": {
                    "ru": "Контрастная средняя секция (B) формы AABA; часто уходит в другую тональность.",
                    "en": "The contrasting middle section (B) of an AABA form; often modulates.",
                },
            },
            {
                "term": {"ru": "Blues form (блюз)", "en": "Blues form"},
                "def": {
                    "ru": "12-тактовая форма на трёх аккордах (I–IV–V) с характерным оборотом; фундамент джазового языка.",
                    "en": "The 12-bar form on three chords (I–IV–V) with its signature turnaround; bedrock of the language.",
                },
            },
            {
                "term": {"ru": "Rhythm changes", "en": "Rhythm changes"},
                "def": {
                    "ru": "Сетка «I Got Rhythm» Гершвина (B♭, AABA): после блюза — вторая по важности форма для практики.",
                    "en": "The chord changes of Gershwin's 'I Got Rhythm' (B♭, AABA): after the blues, the key form to know.",
                },
            },
            {
                "term": {"ru": "Контрафакт (contrafact)", "en": "Contrafact"},
                "def": {
                    "ru": "Новая тема на гармонии существующего стандарта (Donna Lee — на сетке Indiana). Сетка не охраняется, мелодия — да.",
                    "en": "A new melody written over an existing tune's changes (Donna Lee over the Indiana changes).",
                },
            },
        ],
    },
    "rhythm": {
        "title": {"ru": "🥁 Ритм и фраза", "en": "🥁 Rhythm & Phrasing"},
        "terms": [
            {
                "term": {"ru": "Swing feel", "en": "Swing feel"},
                "def": {
                    "ru": "Неровное деление восьмых (длинная–короткая, ближе к триольному) + акцент на off-beat. Суть джазового пульса.",
                    "en": "Uneven eighth notes (long–short, near-triplet) with off-beat accents. The heart of jazz time.",
                },
            },
            {
                "term": {"ru": "Comping", "en": "Comping"},
                "def": {
                    "ru": "Аккомпанемент аккордами (ф-но/гитара) под солиста: ритмически живо, но не мешая.",
                    "en": "Chordal accompaniment (piano/guitar) behind a soloist — rhythmically active but supportive.",
                },
            },
            {
                "term": {"ru": "Синкопа (syncopation)", "en": "Syncopation"},
                "def": {
                    "ru": "Акцент на слабую долю или между долями. Создаёт драйв и «качание».",
                    "en": "Accenting weak beats or off-beats. Creates drive and groove.",
                },
            },
            {
                "term": {
                    "ru": "Ритмический сдвиг (displacement)",
                    "en": "Rhythmic displacement",
                },
                "def": {
                    "ru": "Сдвиг мотива на другую долю: фраза «плывёт» против тактовой сетки и звучит свежо.",
                    "en": "Shifting a motif onto a different beat — the phrase floats against the barline and sounds fresh.",
                },
            },
            {
                "term": {"ru": "Count-in (отсчёт)", "en": "Count-in"},
                "def": {
                    "ru": "Затактовый щелчок/счёт перед началом, задающий темп (обычно 1–2 такта).",
                    "en": "A click/count before the start that sets the tempo (usually 1–2 bars).",
                },
            },
        ],
    },
    "improv": {
        "title": {"ru": "🎷 Импровизация", "en": "🎷 Improvisation"},
        "terms": [
            {
                "term": {"ru": "Enclosure (окружение)", "en": "Enclosure"},
                "def": {
                    "ru": "Подход к целевой ноте сверху и снизу (хроматически/диатонически) перед её взятием. Фирменный приём бибопа.",
                    "en": "Approaching a target note from above and below before landing on it. A signature bebop device.",
                },
            },
            {
                "term": {"ru": "Хроматический подход", "en": "Chromatic approach"},
                "def": {
                    "ru": "Хроматическая нота за полтона до аккордового тона на сильную долю.",
                    "en": "A chromatic note a half-step before a chord tone, landing on the strong beat.",
                },
            },
            {
                "term": {"ru": "Targeting", "en": "Targeting"},
                "def": {
                    "ru": "Осознанное ведение линии к важной ноте аккорда (3 или 7) на сильную долю.",
                    "en": "Deliberately aiming a line at a key chord tone (3rd or 7th) on a strong beat.",
                },
            },
            {
                "term": {"ru": "Chord-scale", "en": "Chord-scale"},
                "def": {
                    "ru": "Гамма, подходящая данному аккорду (Dm7→дорийский, G7→миксолидийский). Материал для линий.",
                    "en": "The scale that fits a given chord (Dm7→Dorian, G7→Mixolydian) — raw material for lines.",
                },
            },
            {
                "term": {"ru": "Lick (лик)", "en": "Lick"},
                "def": {
                    "ru": "Готовая короткая мелодическая фраза-заготовка, переносимая по аккордам и тональностям.",
                    "en": "A ready-made short melodic phrase, transposable across chords and keys.",
                },
            },
            {
                "term": {"ru": "Call & response", "en": "Call & response"},
                "def": {
                    "ru": "Диалог фраз: короткий «вопрос» и «ответ». Основа осмысленной фразировки.",
                    "en": "A dialogue of phrases — a short 'question' and 'answer.' The basis of meaningful phrasing.",
                },
            },
        ],
    },
    "sound": {
        "title": {"ru": "🎺 Sound & Feel", "en": "🎺 Sound & Feel"},
        "terms": [
            {
                "term": {"ru": "Артикуляция (articulation)", "en": "Articulation"},
                "def": {
                    "ru": "Как атакуются и связываются ноты (язык/легато/акцент). В джазе чаще legato с акцентами на off-beat.",
                    "en": "How notes are attacked and connected (tongue/legato/accent). Jazz often uses legato with off-beat accents.",
                },
            },
            {
                "term": {"ru": "Ghost note (гост-нота)", "en": "Ghost note"},
                "def": {
                    "ru": "Намеренно «съеденная», еле слышная нота — добавляет фразе ритмическую перкуссивность.",
                    "en": "A deliberately muted, barely-sounded note — adds rhythmic, percussive feel to a line.",
                },
            },
            {
                "term": {"ru": "Динамика (dynamics)", "en": "Dynamics"},
                "def": {
                    "ru": "Управление громкостью внутри фразы и формы: строит напряжение и арку соло.",
                    "en": "Shaping volume within a phrase and across the form — builds tension and the arc of a solo.",
                },
            },
        ],
    },
}


def category_title(cat, lang):
    c = GLOSSARY.get(cat)
    return c["title"].get(lang, c["title"]["ru"]) if c else cat


def terms_of(cat):
    c = GLOSSARY.get(cat)
    return c["terms"] if c else []


def term_at(cat, idx, lang):
    """Возвращает (term_str, def_str) для категории cat и индекса idx, или None."""
    terms = terms_of(cat)
    if not (0 <= idx < len(terms)):
        return None
    t = terms[idx]
    return (
        t["term"].get(lang, t["term"]["ru"]),
        t["def"].get(lang, t["def"]["ru"]),
    )
