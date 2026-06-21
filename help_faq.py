# -*- coding: utf-8 -*-
"""
FAQ / пошаговая помощь для раздела «❓ Помощь» в боте.

Единый источник контента — переиспользуется в боте; те же тексты портируются
в мини-аппу (Worker) и на сайт. Двуязычно (ru/en). Формат: список вопрос→ответ,
ответы практичные, где уместно — пошаговые.
"""

FAQ = [
    {
        "q": {"ru": "🚀 С чего начать?", "en": "🚀 How do I start?"},
        "a": {
            "ru": (
                "1. Нажми «🎼 Открыть приложение» — это библиотека нот.\n"
                "2. Выбери раздел: 🎵 Пьесы, 📚 Этюды или 📖 Книги.\n"
                "3. Открой ноту — придёт PDF. У многих пьес есть версии под твой "
                "инструмент и плей-элонг.\n"
                "4. Хочешь учиться по конкретному стандарту — загляни в «🎓 Hit Study Pack»."
            ),
            "en": (
                "1. Tap “🎼 Open app” — that's the sheet-music library.\n"
                "2. Pick a section: 🎵 Pieces, 📚 Etudes or 📖 Books.\n"
                "3. Open a piece — you'll get a PDF. Many tunes have versions for your "
                "instrument and a play-along.\n"
                "4. To study a specific standard, check “🎓 Hit Study Pack”."
            ),
        },
    },
    {
        "q": {"ru": "🎵 Где найти ноты?", "en": "🎵 Where do I find sheet music?"},
        "a": {
            "ru": (
                "В разделах 🎵 Пьесы / 📚 Этюды / 📖 Книги, или через 🔍 Поиск (по "
                "названию, композитору, стилю). Открыв пьесу, выбери версию под свой "
                "инструмент (труба, сакс, тромбон, гитара, ф-но и др.) — нота придёт "
                "в правильной транспозиции."
            ),
            "en": (
                "In 🎵 Pieces / 📚 Etudes / 📖 Books, or via 🔍 Search (by title, "
                "composer, style). Inside a piece, pick the version for your instrument "
                "(trumpet, sax, trombone, guitar, piano, etc.) — it arrives in the right "
                "transposition."
            ),
        },
    },
    {
        "q": {
            "ru": "🎓 Что такое Hit Study Pack?",
            "en": "🎓 What is a Hit Study Pack?",
        },
        "a": {
            "ru": (
                "Учебный пакет по конкретной пьесе: аккордовая сетка, разбор гармонии, "
                "гайд-тоны, лики, упражнения, план на неделю + минусовка (play-along). "
                "Где возможно — кнопка нотного листа первоисточника. Выбираешь пьесу → "
                "инструмент → получаешь PDF и аудио."
            ),
            "en": (
                "A study pack for one tune: the chord chart, harmonic analysis, guide "
                "tones, licks, exercises, a week plan + a backing track. Where available, "
                "a button for the source lead sheet. Pick a tune → instrument → get the "
                "PDF and audio."
            ),
        },
    },
    {
        "q": {"ru": "⭐️ Как оплатить пакет?", "en": "⭐️ How do I pay for a pack?"},
        "a": {
            "ru": (
                "Оплата идёт за Telegram Stars (⭐️) — прямо в Telegram, картой/через "
                "оплату Telegram. Купленный пакет остаётся у тебя навсегда: его можно "
                "пере-скачать в «🎓 Мои паки». Есть бандл из 5 пакетов выгоднее."
            ),
            "en": (
                "Payment is in Telegram Stars (⭐️) — right inside Telegram. A purchased "
                "pack is yours forever: re-download it any time from “🎓 My packs”. A "
                "bundle of 5 packs is cheaper per pack."
            ),
        },
    },
    {
        "q": {
            "ru": "🎚 Как замедлить минусовку?",
            "en": "🎚 How do I slow down the backing track?",
        },
        "a": {
            "ru": (
                "После выдачи пакета (или в «🎓 Мои паки») нажми «🎚 Темп минусовки» и "
                "выбери темп: 🎯 выступление (100%), 🚶 рабочий (75%), 🐢 медленно (50%) "
                "или ✏️ свой BPM. Минус идёт с отсчётом (count-in), высота нот не меняется. "
                "Учись медленно → постепенно разгоняйся."
            ),
            "en": (
                "After you get a pack (or in “🎓 My packs”) tap “🎚 Backing tempo” and pick "
                "a tempo: 🎯 performance (100%), 🚶 working (75%), 🐢 slow (50%) or ✏️ your "
                "own BPM. The backing has a count-in and keeps the pitch. Learn slow → "
                "speed up gradually."
            ),
        },
    },
    {
        "q": {
            "ru": "🎤 Как получить разбор моей игры?",
            "en": "🎤 How do I get my playing analyzed?",
        },
        "a": {
            "ru": (
                "Запиши себя и пришли голосовое/аудио в бот — он разберёт интонацию "
                "(отклонения в центах) по нотам. Можно привязать разбор к конкретной "
                "пьесе. Это работает для духовых и контрабаса (непрерывная высота). "
                "Совет: играй чисто и не слишком быстро для точного анализа."
            ),
            "en": (
                "Record yourself and send a voice/audio message to the bot — it analyzes "
                "your intonation (deviation in cents) note by note. You can tie the "
                "analysis to a specific piece. Works for winds and double bass (continuous "
                "pitch). Tip: play cleanly and not too fast for accurate results."
            ),
        },
    },
    {
        "q": {
            "ru": "🎶 Можно сделать ноты из записи?",
            "en": "🎶 Can I turn a recording into notation?",
        },
        "a": {
            "ru": (
                "Да — пришли запись, и бот снимет её в ноты (транскрипция). Для "
                "фортепиано и гитары распознаются аккорды (полифония), для духовых — "
                "одноголосная мелодия. Результат — нотный файл."
            ),
            "en": (
                "Yes — send a recording and the bot transcribes it into notation. For "
                "piano and guitar it detects chords (polyphony); for winds, a single-line "
                "melody. You get a notation file."
            ),
        },
    },
    {
        "q": {
            "ru": "📝 Что за «Мои ноты» и «Мои паки»?",
            "en": "📝 What are “My notes” and “My packs”?",
        },
        "a": {
            "ru": (
                "📝 «Мои ноты» — личные заметки/закладки к пьесам. 🎓 «Мои паки» — все "
                "купленные Hit Study Pack: оттуда можно мгновенно пере-скачать PDF и "
                "минус, а также менять темп минусовки."
            ),
            "en": (
                "📝 “My notes” — your personal notes/bookmarks for pieces. 🎓 “My packs” — "
                "all your purchased Hit Study Packs: re-download the PDF and backing "
                "instantly, and change the backing tempo."
            ),
        },
    },
    {
        "q": {"ru": "🎯 Метроном и тюнер?", "en": "🎯 Metronome and tuner?"},
        "a": {
            "ru": (
                "🎚 Метроном — задай темп (BPM) и размер, получишь щёлкающий трек. "
                "🎯 Тюнер — открывается как приложение, показывает высоту ноты и "
                "отклонение, помогает строить инструмент и слышать интонацию."
            ),
            "en": (
                "🎚 Metronome — set the tempo (BPM) and time signature, get a click "
                "track. 🎯 Tuner — opens as an app, shows the note pitch and deviation, "
                "helps you tune up and hear your intonation."
            ),
        },
    },
    {
        "q": {
            "ru": "📖 Не понимаю термин (ii–V–I и т.п.)",
            "en": "📖 I don't get a term (ii–V–I etc.)",
        },
        "a": {
            "ru": (
                "Открой 📖 Словарь — там коротко разобраны термины из лид-шитов и "
                "учебных пакетов (гармония, форма, ритм, импровизация, звук): ii–V–I, "
                "гайд-тоны, comping, enclosure, swing feel и другие."
            ),
            "en": (
                "Open the 📖 Glossary — it briefly explains the terms you meet in lead "
                "sheets and study packs (harmony, form, rhythm, improvisation, sound): "
                "ii–V–I, guide tones, comping, enclosure, swing feel and more."
            ),
        },
    },
    {
        "q": {"ru": "🌐 Как сменить язык?", "en": "🌐 How do I change the language?"},
        "a": {
            "ru": "Команда /language или кнопка языка в меню — переключение между русским и английским.",
            "en": "Use /language or the language button in the menu — switch between Russian and English.",
        },
    },
    {
        "q": {
            "ru": "💡 Нашёл ошибку / есть идея",
            "en": "💡 Found a bug / have an idea",
        },
        "a": {
            "ru": (
                "Нажми «💡 Предложить» в меню (или /feedback) и напиши — пожелания, "
                "ошибки, какие ноты добавить. Мы читаем всё."
            ),
            "en": (
                "Tap “💡 Suggest” in the menu (or /feedback) and write to us — requests, "
                "bugs, which sheet music to add. We read everything."
            ),
        },
    },
]


def question(idx, lang):
    if 0 <= idx < len(FAQ):
        q = FAQ[idx]["q"]
        return q.get(lang, q["ru"])
    return None


def answer(idx, lang):
    if 0 <= idx < len(FAQ):
        a = FAQ[idx]["a"]
        return a.get(lang, a["ru"])
    return None
