import json
import os
import random
import logging
import io
import math
import struct
import wave
import asyncio
import shutil
import tempfile
import subprocess
import datetime
import mynotes
import billing
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    BotCommand,
    MenuButtonWebApp,
    LabeledPrice,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    ContextTypes,
)

# ================== НАСТРОЙКИ ==================
# Токен ТОЛЬКО из переменной окружения (env-файл systemd). НЕ хардкодить и НЕ коммитить!
TOKEN = os.environ.get("TOKEN")
YOUR_USER_ID = 848061458  # Ваш Telegram ID (узнать у @userinfobot)
NOTES_JSON = "notes.json"
NOTES_FOLDER = "notes"
LANG_FILE = "user_lang.json"  # выбор языка пользователя (переживает рестарт)
ITEMS_PER_PAGE = 15  # Количество кнопок на одной странице
TUNER_URL = "https://jazztone.app/tuner/?v=7"  # ?v= = cache-bust для Telegram-вебвью (бампать при каждом обновлении тюнера!)
HOME_URL = "https://jazztone.app/app/?v=8"  # мини-аппа «домашний экран»; ?v= = cache-bust Telegram-вебвью (бампать при обновлении app/)
# Монетизация (MVP, council: платно ТОЛЬКО глубокий AI-разбор, через Stars-кредиты).
# ⚠️ ВКЛЮЧАТЬ только после настройки вывода Stars (Fragment) на ВЗРОСЛОГО + налоги/учёт.
# При False поведение бота не меняется (разбор бесплатен и без лимита).
BILLING_ENABLED = True
# ===============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# httpx логирует полный URL запроса (вместе с токеном!) на INFO — глушим, чтобы токен не утекал в логи
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def load_notes():
    with open(NOTES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def save_notes(notes):
    with open(NOTES_JSON, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


# ================== ЯЗЫК / I18N ==================
LANGS = ("ru", "en")


def _load_lang_store():
    try:
        with open(LANG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


USER_LANG = _load_lang_store()


def set_lang(context, uid, lang):
    if lang not in LANGS:
        lang = "ru"
    if context is not None:
        context.user_data["lang"] = lang
    USER_LANG[str(uid)] = lang
    try:
        with open(LANG_FILE, "w", encoding="utf-8") as f:
            json.dump(USER_LANG, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Не удалось сохранить язык: {e}")


def user_lang(context, user=None):
    """Язык пользователя: кэш user_data → файл → язык Telegram-клиента → ru."""
    l = context.user_data.get("lang") if context is not None else None
    if l in LANGS:
        return l
    if user is not None:
        l = USER_LANG.get(str(user.id))
        if l not in LANGS:
            code = (getattr(user, "language_code", None) or "")[:2]
            l = "en" if (code and code != "ru") else "ru"
        if context is not None:
            context.user_data["lang"] = l
        return l
    return "ru"


# Английские подписи инструментов (русские берём из transcribe.INSTRUMENTS)
INSTRUMENT_LABELS_EN = {
    "trumpet": "Trumpet B♭",
    "concert": "Concert (as sounds)",
    "trombone": "Trombone",
    "tenorsax": "Tenor sax B♭",
    "altosax": "Alto sax E♭",
    "clarinet": "Clarinet B♭",
    "contrabass": "Double bass",
    "guitar": "Guitar",
    "piano": "Piano",
}

TR = {
    "ru": {
        "welcome": (
            "🎺 **Добро пожаловать в JazzTone — библиотеку джазовых нот!**\n\n"
            "Используй кнопки ниже для навигации.\n\n"
            "Все ноты **кликабельны** — просто нажми на название."
        ),
        "lang_prompt": "🌐 Выбери язык / Choose your language",
        "lang_done": "✅ Язык установлен: Русский 🇷🇺",
        "btn_lang": "🌐 Язык / Language",
        "btn_open_app": "✨ Открыть JazzTone",
        "btn_pieces": "🎵 Произведения",
        "btn_etudes": "📖 Этюды",
        "btn_books": "📚 Книги",
        "btn_search": "🔍 Умный поиск",
        "btn_metro": "🎼 Метроном",
        "btn_tuner": "🎺 Тюнер",
        "btn_perf": "🎤 Анализ игры (бета)",
        "btn_trans": "🎼 Ноты из записи (бета)",
        "btn_mynotes": "🎤 Пользовательские ноты",
        "btn_suggest": "📝 Предложить произведение",
        "btn_buy": "⭐️ Купить разборы игры",
        "btn_home": "🏠 На главную",
        "btn_back": "⬅️ Назад",
        "btn_next": "Вперёд ➡️",
        "btn_other_instr": "🎷 Другой инструмент",
        "btn_to_instruments": "⬅️ К инструментам",
        "btn_delete": "🗑 Удалить",
        "btn_to_letters": "🔙 К буквам",
        "btn_to_composers": "🔙 К композиторам",
        "btn_my_tempo": "↩️ Мой темп ({n})",
        "btn_custom_tempo": "✏️ Свой темп",
        "btn_to_tempo": "⬅️ К выбору темпа",
        "cat_piece": "Произведения",
        "cat_etude": "Этюды",
        "cat_book": "Книги",
        "picker_title": "🎷 **{cat} — выбери инструмент**\n\nПокажу то, для чего есть партия в твоём строе.",
        "picker_empty": "📭 В разделе «{cat}» пока ничего нет.",
        "pieces_empty": "📭 Под «{instr}» здесь пока пусто.",
        "pieces_title": "🎷 **{instr}** · {cat} ({a}-{b} из {total}):\n\nНажми на название — пришлю в твоём строе.",
        "cap_key": "тон.",
        "hz": "Гц",
        "note_file_missing": "❌ Файл для ноты «{title}» не найден.",
        "note_not_found": "❌ Нота не найдена.",
        "btn_playalong": "🎧 Плей-элонг",
        "btn_minus": "🎵 Минусовка",
        "cap_playalong": "🎧 Плей-элонг (труба + фон) — {title}",
        "cap_minus": "🎵 Минусовка (фон без трубы) — {title}",
        "audio_missing": "❌ Аудио для этой вещи пока не готово.",
        "btn_perf_piece": "🎯 Разобрать мою игру",
        "perfpiece_prompt": "🎯 Разбор пьесы «{title}».\nЗапиши или пришли, как ты её играешь (голосовое или MP3) — оценю интонацию именно по этой вещи.",
        "btn_ask_coach": "❓ Спросить / посоветоваться",
        "askq_prompt": "💬 Напиши свой вопрос по пьесе «{title}» и своей игре — отвечу и подскажу, как заниматься.",
        "coach_thinking": "💬 Думаю над ответом…",
        "coach_unavailable": "❓ Консультация пока в настройке — загляни позже.",
        "coach_error": "😕 Не получилось ответить. Попробуй переформулировать вопрос.",
        "random_empty": "📭 Библиотека пока пуста.",
        "feedback": "📬 По всем вопросам пишите: trumpet_library@example.com",
        "credits": "📚 **Источники нот:**\n• Личная коллекция\n• Открытые интернет-архивы",
        "metro_text": (
            "🎼 **Метроном**\n\nВыбери темп (BPM) из списка или задай свой.\n"
            "Дальше выберешь размер — число долей в такте; акцент придётся на первую долю."
        ),
        "beats_n": "{n} доли",
        "metro_size_prompt": "🎼 Темп {bpm} BPM. Теперь выбери размер — число долей в такте (акцент на 1-ю):",
        "metro_custom_prompt": "✏️ Напиши свой темп числом — BPM от {min} до {max} (например, 132).",
        "metro_bad_bpm": "❌ Нужно число от {min} до {max}. Открой 🎼 Метроном и попробуй ещё раз.",
        "metro_caption": "🎼 Метроном {bpm} BPM · {beats} доли в такте · ~30 c",
        "metro_title": "Метроном {bpm} BPM ({beats} доли)",
        "perf_text": (
            "🎤 **Анализ игры (бета)**\n\n"
            "Запиши **голосовое сообщение**, играя на трубе (или другом духовом) — "
            "лучше всего ровную гамму или короткую фразу, по одной ноте за раз.\n\n"
            "Я разберу запись и покажу, насколько чисто звучит каждая нота "
            "(отклонение в центах от равномерного строя, A4 = 440 Гц).\n\n"
            "⚠️ Бета: работает по монофонии (одна нота за раз), "
            "real-time настройку лучше делать через 🎺 Тюнер."
        ),
        "paywall_text": (
            "🎺 **Бесплатные разборы на этот месяц закончились.**\n\n"
            "Тюнер, метроном и библиотека остаются бесплатными всегда. "
            "Глубокий AI-разбор игры — это сервис: можно докупить пакет разборов "
            "за Telegram Stars ⭐️."
        ),
        "buy_pack": "⭐️ {n} разборов — {stars} Stars",
        "invoice_title": "JazzTone · {n} разборов игры",
        "invoice_desc": "{n} глубоких AI-разборов твоей игры (интонация в центах + советы). Не ноты — сервис.",
        "invoice_label": "{n} разборов игры",
        "pay_thanks": "✅ Спасибо! Начислено **{n}** разборов. Доступно сейчас: **{bal}**.\nЗапиши голосовое — разберу.",
        "buy_status": (
            "🎺 **Глубокий разбор игры**\n\nБесплатно осталось в этом месяце: **{free}**.\n"
            "Купленных разборов: **{bal}**.\n\nДокупить пакет за Telegram Stars ⭐️:"
        ),
        "no_ffmpeg": "⚙️ На сервере нет ffmpeg для декодирования аудио. Попробуй позже.",
        "dl_too_big": "⚠️ Файл слишком большой для бота (лимит ~20 МБ). Пришли кусок покороче или сожми в MP3.",
        "dl_decode_fail": "❌ Не удалось декодировать аудио. Пришли голосовое ещё раз.",
        "perf_listening": "🎧 Слушаю запись…",
        "analysis_missing": "⚙️ Модуль анализа пока не установлен на сервере. Попробуй позже.",
        "perf_error": "❌ Что-то пошло не так при разборе записи. Попробуй ещё раз.",
        "perf_fail_short": "Запись слишком короткая — сыграй хотя бы пару секунд.",
        "perf_fail_nopitch": "Не удалось распознать устойчивый тон. Запиши поближе к микрофону и играй ноты подольше.",
        "fail_generic": "Не удалось разобрать запись.",
        "verdict_good": "🟢 Отличная интонация!",
        "verdict_mid": "🟡 Неплохо, но есть что подтянуть.",
        "verdict_bad": "🟠 Над интонацией стоит поработать.",
        "report_header": "🎤 **Разбор записи**",
        "report_count": "Нот распознано: **{n}**",
        "report_clean": "Чисто: **{a}/{b}** ({acc}%)",
        "report_meandev": "Средн. отклонение: **{hz} Гц**",
        "report_bynote": "_По нотам (отклонение в Гц):_",
        "report_more": "…и ещё {n}.",
        "report_howto": "**Как поработать:**",
        "fix_lo_soft": " · возьми чуть ниже 🔽",
        "fix_hi_soft": " · возьми чуть выше 🔼",
        "fix_lo": " · возьми ниже 🔽",
        "fix_hi": " · возьми выше 🔼",
        "adv_great": "🎯 Отлично — звук ровный и в строе. Так держать!",
        "adv_sharp": (
            "Ты в среднем **высишь**. Попробуй чуть **опустить настройку** инструмента "
            "(выдвинуть крон) и направить воздух теплее, не «поджимай» губами."
        ),
        "adv_flat": (
            "Ты в среднем **низишь**. Чуть **подними настройку** (задвинь крон), "
            "добавь опоры и скорости воздуха, держи амбушюр собраннее."
        ),
        "adv_spread": (
            "Высота **гуляет** (разброс большой) — это про стабильность звука. "
            "Поучи **длинные ноты** под тюнер: ровный выдох, опора, держи центр."
        ),
        "adv_worst": "Больше всего мимо: **{names}** — поучи их отдельно длинными нотами на тюнер.",
        "adv_almost": "Почти в строю — отдельные ноты подтяни длинными нотами на тюнер.",
        "trans_text": (
            "🎼 **Ноты из записи (бета)**\n\n"
            "Пришли запись **одной мелодии** (монофония — одна нота за раз): "
            "**аудиофайл MP3** (удобнее всего), FLAC/M4A/WAV или голосовое. "
            "Я распознаю ноты и пришлю **картинку с нотами** + файлы **MIDI** и **MusicXML**.\n\n"
            "⚠️ Это работает для **сольной мелодии**. Целая песня с аккомпанементом "
            "(или ссылка на YouTube) — полифония, это отдельный тяжёлый этап (будет позже).\n\n"
            "Сначала выбери, **под какой инструмент** транспонировать ноты:"
        ),
        "trans_pick_prompt": (
            "🎼 Инструмент: **{label}**\n\n"
            "Теперь пришли запись мелодии: **MP3** (удобнее всего), FLAC/M4A/WAV или голосовое — "
            "одна нота за раз. Я пришлю **картинку с нотами** + MIDI и MusicXML."
        ),
        "trans_missing": "⚙️ Модуль транскрипции пока не установлен на сервере. Попробуй позже.",
        "trans_recognizing": "🎧 Распознаю ноты…",
        "trans_fail_short": "Запись слишком короткая — сыграй хотя бы пару нот.",
        "trans_fail_nopitch": "Не удалось распознать ноты. Играй по одной ноте, поближе к микрофону, в тишине.",
        "trans_report_header": "🎼 **Готово — ноты распознаны**",
        "trans_instrument": "Инструмент: **{label}**",
        "trans_notes": "Нот: **{n}**",
        "trans_conf": "Уверенность: **{c}%** ({mark})",
        "conf_high": "🟢 высокая",
        "conf_mid": "🟡 средняя",
        "conf_low": "🟠 низкая",
        "trans_foot1": "_Ниже: картинка с нотами + файлы MIDI и MusicXML._",
        "trans_foot2": "_Это черновик с записи; на спорных местах сверься на слух._",
        "trans_title_prefix": "Запись {dt}",
        "midi_caption": "🎵 MIDI",
        "xml_caption": "📄 MusicXML (для MuseScore)",
        "trans_saved": "💾 Сохранено в «🎤 Пользовательские ноты» (#{nid}).",
        "trans_error": "❌ Что-то пошло не так при распознавании. Попробуй ещё раз.",
        "mynotes_empty": (
            "🎤 **Пользовательские ноты**\n\nПока пусто. Пришли мелодию через "
            "«🎼 Ноты из записи» — она появится здесь."
        ),
        "mynotes_title": "🎤 **Пользовательские ноты**\n\nНажми, чтобы получить файлы:",
        "mynote_btn": "{title} · {instr} · {n} нот ({c}%)",
        "mynote_caption": "🎼 {title} · {instr} · {n} нот · уверенность {c}%",
        "mynote_notfound": "❌ Ноты не найдены (возможно, удалены).",
        "mynote_nofiles": "❌ Файлы не найдены на сервере.",
        "mynote_manage": "Управление:",
        "deleted": "🗑 Удалено.",
        "notfound_generic": "❌ Не найдено.",
        "search_title": "🔍 **Умный поиск**\n\nВыберите первую букву фамилии композитора:",
        "no_composers_letter": "❌ Нет композиторов на букву {l}.",
        "composers_letter_title": "🎵 **Композиторы на букву {l}:**",
        "no_pieces_composer": "❌ У композитора {c} пока нет нот.",
        "pieces_composer_title": "🎺 **Произведения {c}:**",
        "suggest_prompt": (
            "📝 **Предложите произведение**\n\nНапишите название и композитора или пришлите PDF.\n\n"
            "Ваше предложение будет отправлено куратору."
        ),
        "suggest_sent": "✅ Спасибо! Предложение отправлено.",
        "suggest_sent_curator": "✅ Спасибо! Предложение отправлено куратору.",
        "suggest_fail": "❌ Не удалось отправить предложение. Попробуйте позже.",
        "suggest_need_pdf": "❌ Пришлите файл в формате **PDF**.",
        "trans_link_warn": (
            "🔗 Ссылки (YouTube и т.п.) и целые песни с аккомпанементом — "
            "это **полифония**, отдельный тяжёлый этап, будет позже.\n\n"
            "Сейчас пришли **аудиофайл MP3/FLAC** с **одной мелодией** (соло)."
        ),
        "trans_send_audio": "🎧 Пришли **аудиофайл** (MP3 удобнее всего) или голосовое с мелодией.",
        "doc_send_audio": "🎧 Пришли **аудиофайл** (MP3, FLAC, M4A, WAV) или голосовое.",
        "search_none": "❌ **Ничего не найдено.** Попробуйте другое слово или проверьте написание.",
        "search_results": "🔍 **Результаты поиска «{q}»:**\n\nНажмите на название:",
    },
    "en": {
        "welcome": (
            "🎺 **Welcome to JazzTone — the jazz sheet-music library!**\n\n"
            "Use the buttons below to navigate.\n\n"
            "Every piece is **clickable** — just tap a title."
        ),
        "lang_prompt": "🌐 Choose your language / Выбери язык",
        "lang_done": "✅ Language set: English 🇬🇧",
        "btn_lang": "🌐 Language / Язык",
        "btn_open_app": "✨ Open JazzTone",
        "btn_pieces": "🎵 Pieces",
        "btn_etudes": "📖 Études",
        "btn_books": "📚 Books",
        "btn_search": "🔍 Smart search",
        "btn_metro": "🎼 Metronome",
        "btn_tuner": "🎺 Tuner",
        "btn_perf": "🎤 Playing analysis (beta)",
        "btn_trans": "🎼 Notation from recording (beta)",
        "btn_mynotes": "🎤 Your notation",
        "btn_suggest": "📝 Suggest a piece",
        "btn_buy": "⭐️ Buy playing analyses",
        "btn_home": "🏠 Home",
        "btn_back": "⬅️ Back",
        "btn_next": "Next ➡️",
        "btn_other_instr": "🎷 Another instrument",
        "btn_to_instruments": "⬅️ To instruments",
        "btn_delete": "🗑 Delete",
        "btn_to_letters": "🔙 To letters",
        "btn_to_composers": "🔙 To composers",
        "btn_my_tempo": "↩️ My tempo ({n})",
        "btn_custom_tempo": "✏️ Custom tempo",
        "btn_to_tempo": "⬅️ To tempo",
        "cat_piece": "Pieces",
        "cat_etude": "Études",
        "cat_book": "Books",
        "picker_title": "🎷 **{cat} — choose your instrument**\n\nI'll show what has a part in your key.",
        "picker_empty": "📭 Nothing in “{cat}” yet.",
        "pieces_empty": "📭 Nothing for “{instr}” here yet.",
        "pieces_title": "🎷 **{instr}** · {cat} ({a}-{b} of {total}):\n\nTap a title — I'll send it in your key.",
        "cap_key": "key",
        "hz": "Hz",
        "note_file_missing": "❌ File for “{title}” not found.",
        "note_not_found": "❌ Piece not found.",
        "btn_playalong": "🎧 Play-along",
        "btn_minus": "🎵 Backing track",
        "cap_playalong": "🎧 Play-along (trumpet + backing) — {title}",
        "cap_minus": "🎵 Backing track (no trumpet) — {title}",
        "audio_missing": "❌ Audio for this piece isn’t ready yet.",
        "btn_perf_piece": "🎯 Analyze my playing",
        "perfpiece_prompt": "🎯 Analysis of “{title}”.\nRecord or send how you play it (voice message or MP3) — I'll check your intonation on this piece.",
        "btn_ask_coach": "❓ Ask / get advice",
        "askq_prompt": "💬 Ask your question about “{title}” and your playing — I'll answer and suggest how to practice.",
        "coach_thinking": "💬 Thinking…",
        "coach_unavailable": "❓ The Q&A feature isn't set up yet — check back later.",
        "coach_error": "😕 Couldn't answer. Try rephrasing your question.",
        "random_empty": "📭 The library is empty for now.",
        "feedback": "📬 Questions? Write to: trumpet_library@example.com",
        "credits": "📚 **Sources:**\n• Personal collection\n• Open internet archives",
        "metro_text": (
            "🎼 **Metronome**\n\nPick a tempo (BPM) from the list or set your own.\n"
            "Then choose the time signature — beats per bar; the accent lands on beat 1."
        ),
        "beats_n": "{n} beats",
        "metro_size_prompt": "🎼 Tempo {bpm} BPM. Now choose the time signature — beats per bar (accent on beat 1):",
        "metro_custom_prompt": "✏️ Type your tempo as a number — BPM from {min} to {max} (e.g. 132).",
        "metro_bad_bpm": "❌ Need a number from {min} to {max}. Open 🎼 Metronome and try again.",
        "metro_caption": "🎼 Metronome {bpm} BPM · {beats} beats/bar · ~30 s",
        "metro_title": "Metronome {bpm} BPM ({beats} beats)",
        "perf_text": (
            "🎤 **Playing analysis (beta)**\n\n"
            "Record a **voice message** while playing your trumpet (or another wind) — "
            "ideally an even scale or a short phrase, one note at a time.\n\n"
            "I'll analyse it and show how cleanly each note sounds "
            "(deviation in cents from equal temperament, A4 = 440 Hz).\n\n"
            "⚠️ Beta: works on monophony (one note at a time); "
            "for real-time tuning use the 🎺 Tuner."
        ),
        "paywall_text": (
            "🎺 **You've used your free analyses for this month.**\n\n"
            "The tuner, metronome and library stay free forever. The deep AI "
            "playing analysis is a service — you can top up a pack of analyses "
            "with Telegram Stars ⭐️."
        ),
        "buy_pack": "⭐️ {n} analyses — {stars} Stars",
        "invoice_title": "JazzTone · {n} playing analyses",
        "invoice_desc": "{n} deep AI analyses of your playing (intonation in cents + advice). A service, not sheet music.",
        "invoice_label": "{n} playing analyses",
        "pay_thanks": "✅ Thanks! Added **{n}** analyses. Available now: **{bal}**.\nSend a voice message — I'll analyse it.",
        "buy_status": (
            "🎺 **Deep playing analysis**\n\nFree left this month: **{free}**.\n"
            "Purchased analyses: **{bal}**.\n\nTop up a pack with Telegram Stars ⭐️:"
        ),
        "no_ffmpeg": "⚙️ The server has no ffmpeg to decode audio. Try later.",
        "dl_too_big": "⚠️ File too large for the bot (~20 MB limit). Send a shorter clip or compress to MP3.",
        "dl_decode_fail": "❌ Couldn't decode the audio. Send the voice message again.",
        "perf_listening": "🎧 Listening…",
        "analysis_missing": "⚙️ The analysis module isn't installed on the server yet. Try later.",
        "perf_error": "❌ Something went wrong analysing the recording. Try again.",
        "perf_fail_short": "Recording too short — play at least a couple of seconds.",
        "perf_fail_nopitch": "Couldn't detect a steady pitch. Record closer to the mic and hold notes longer.",
        "fail_generic": "Couldn't analyse the recording.",
        "verdict_good": "🟢 Excellent intonation!",
        "verdict_mid": "🟡 Not bad, but room to improve.",
        "verdict_bad": "🟠 Intonation needs some work.",
        "report_header": "🎤 **Recording analysis**",
        "report_count": "Notes detected: **{n}**",
        "report_clean": "In tune: **{a}/{b}** ({acc}%)",
        "report_meandev": "Avg. deviation: **{hz} Hz**",
        "report_bynote": "_By note (deviation in Hz):_",
        "report_more": "…and {n} more.",
        "report_howto": "**How to work on it:**",
        "fix_lo_soft": " · ease down a touch 🔽",
        "fix_hi_soft": " · lift a touch 🔼",
        "fix_lo": " · ease down 🔽",
        "fix_hi": " · lift up 🔼",
        "adv_great": "🎯 Excellent — steady and in tune. Keep it up!",
        "adv_sharp": (
            "On average you're **sharp**. Try **tuning down** a little (pull the slide out), "
            "use warmer air, and don't pinch with the lips."
        ),
        "adv_flat": (
            "On average you're **flat**. **Tune up** a little (push the slide in), "
            "add support and air speed, keep the embouchure firm."
        ),
        "adv_spread": (
            "Your pitch **drifts** (high spread) — that's about steadiness. "
            "Practise **long tones** with the tuner: even airflow, support, hold the center."
        ),
        "adv_worst": "Most off: **{names}** — drill them separately as long tones with the tuner.",
        "adv_almost": "Almost in tune — clean up individual notes with long tones on the tuner.",
        "trans_text": (
            "🎼 **Notation from recording (beta)**\n\n"
            "Send a recording of **a single melody** (monophony — one note at a time): "
            "an **MP3 audio file** (best), FLAC/M4A/WAV or a voice message. "
            "I'll recognise the notes and send a **notation image** + **MIDI** and **MusicXML** files.\n\n"
            "⚠️ This works for a **solo melody**. A full song with accompaniment "
            "(or a YouTube link) is polyphony — a separate heavy stage (coming later).\n\n"
            "First, choose **which instrument** to transpose the notes for:"
        ),
        "trans_pick_prompt": (
            "🎼 Instrument: **{label}**\n\n"
            "Now send a melody recording: **MP3** (best), FLAC/M4A/WAV or a voice message — "
            "one note at a time. I'll send a **notation image** + MIDI and MusicXML."
        ),
        "trans_missing": "⚙️ The transcription module isn't installed on the server yet. Try later.",
        "trans_recognizing": "🎧 Recognising notes…",
        "trans_fail_short": "Recording too short — play at least a couple of notes.",
        "trans_fail_nopitch": "Couldn't recognise notes. Play one note at a time, close to the mic, in a quiet room.",
        "trans_report_header": "🎼 **Done — notes recognised**",
        "trans_instrument": "Instrument: **{label}**",
        "trans_notes": "Notes: **{n}**",
        "trans_conf": "Confidence: **{c}%** ({mark})",
        "conf_high": "🟢 high",
        "conf_mid": "🟡 medium",
        "conf_low": "🟠 low",
        "trans_foot1": "_Below: a notation image + MIDI and MusicXML files._",
        "trans_foot2": "_It's a draft from the recording; double-check tricky spots by ear._",
        "trans_title_prefix": "Recording {dt}",
        "midi_caption": "🎵 MIDI",
        "xml_caption": "📄 MusicXML (for MuseScore)",
        "trans_saved": "💾 Saved to “🎤 Your notation” (#{nid}).",
        "trans_error": "❌ Something went wrong recognising. Try again.",
        "mynotes_empty": (
            "🎤 **Your notation**\n\nEmpty for now. Send a melody via "
            "“🎼 Notation from recording” — it'll show up here."
        ),
        "mynotes_title": "🎤 **Your notation**\n\nTap to get the files:",
        "mynote_btn": "{title} · {instr} · {n} notes ({c}%)",
        "mynote_caption": "🎼 {title} · {instr} · {n} notes · confidence {c}%",
        "mynote_notfound": "❌ Notation not found (maybe deleted).",
        "mynote_nofiles": "❌ Files not found on the server.",
        "mynote_manage": "Manage:",
        "deleted": "🗑 Deleted.",
        "notfound_generic": "❌ Not found.",
        "search_title": "🔍 **Smart search**\n\nChoose the first letter of the composer's surname:",
        "no_composers_letter": "❌ No composers starting with {l}.",
        "composers_letter_title": "🎵 **Composers starting with {l}:**",
        "no_pieces_composer": "❌ {c} has no pieces yet.",
        "pieces_composer_title": "🎺 **Pieces by {c}:**",
        "suggest_prompt": (
            "📝 **Suggest a piece**\n\nWrite the title and composer, or send a PDF.\n\n"
            "Your suggestion goes to the curator."
        ),
        "suggest_sent": "✅ Thanks! Your suggestion was sent.",
        "suggest_sent_curator": "✅ Thanks! Sent to the curator.",
        "suggest_fail": "❌ Couldn't send the suggestion. Try later.",
        "suggest_need_pdf": "❌ Please send a **PDF** file.",
        "trans_link_warn": (
            "🔗 Links (YouTube etc.) and full songs with accompaniment are "
            "**polyphony** — a separate heavy stage, coming later.\n\n"
            "For now send an **MP3/FLAC** file with **a single melody** (solo)."
        ),
        "trans_send_audio": "🎧 Send an **audio file** (MP3 is easiest) or a voice message with the melody.",
        "doc_send_audio": "🎧 Send an **audio file** (MP3, FLAC, M4A, WAV) or a voice message.",
        "search_none": "❌ **Nothing found.** Try another word or check the spelling.",
        "search_results": "🔍 **Search results for “{q}”:**\n\nTap a title:",
    },
}


def t(lang, key, **kw):
    s = TR.get(lang, TR["ru"]).get(key)
    if s is None:
        s = TR["ru"].get(key, key)
    return s.format(**kw) if kw else s


# ================== ВЕРСИИ ПОД ИНСТРУМЕНТ ==================
# Порядок показа инструментов в библиотеке (джазовый состав).
LIBRARY_INSTRUMENTS = [
    "trumpet",
    "trombone",
    "tenorsax",
    "altosax",
    "clarinet",
    "contrabass",
    "guitar",
    "piano",
]


def instrument_label(key, lang="ru"):
    if lang == "en":
        return INSTRUMENT_LABELS_EN.get(key, key)
    from transcribe import INSTRUMENTS

    return INSTRUMENTS.get(key, (key,))[0]


def versions_of(note):
    """Список версий ноты под инструменты.
    Новые записи держат versions[]; старые (legacy) PDF — это партия для трубы (B♭),
    её и отдаём как единственную версию, не трогая file_path/file_id."""
    if note.get("versions"):
        return note["versions"]
    return [
        {
            "instrument": note.get("instrument", "trumpet"),
            "file": note["file_path"],
            "legacy": True,
        }
    ]


def version_for(note, instrument):
    """Версия ноты под конкретный инструмент, либо None."""
    for v in versions_of(note):
        if v.get("instrument") == instrument:
            return v
    return None


def notes_for_instrument(notes, instrument, category="piece"):
    """Произведения категории, у которых есть партия под данный инструмент."""
    return [
        n for n in notes if n.get("type") == category and version_for(n, instrument)
    ]


# ================== МЕТРОНОМ ==================
METRO_TEMPOS = [50, 60, 70, 80, 90, 100, 110, 120, 140, 160, 180, 200]
METRO_BEATS = [2, 3, 4, 5, 6, 7]  # число долей в такте (акцент на 1-ю)
METRO_BPM_MIN, METRO_BPM_MAX = 30, 300


def metronome_keyboard(context, lang):
    """Меню выбора темпа: пресеты + свой BPM + (если есть) запомненный."""
    keyboard, row = [], []
    for tempo in METRO_TEMPOS:
        row.append(InlineKeyboardButton(str(tempo), callback_data=f"metro_bpm_{tempo}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    bottom = []
    last = context.user_data.get("metro_bpm") if context else None
    if last:
        bottom.append(
            InlineKeyboardButton(
                t(lang, "btn_my_tempo", n=last), callback_data=f"metro_bpm_{last}"
            )
        )
    bottom.append(
        InlineKeyboardButton(t(lang, "btn_custom_tempo"), callback_data="metro_custom")
    )
    keyboard.append(bottom)
    keyboard.append([InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")])
    return InlineKeyboardMarkup(keyboard)


def metronome_size_keyboard(lang):
    """Меню выбора размера (доли в такте)."""
    keyboard, row = [], []
    for b in METRO_BEATS:
        text = t(lang, "beats_n", n=b) if b < 5 else str(b)
        row.append(InlineKeyboardButton(text, callback_data=f"metro_size_{b}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append(
        [InlineKeyboardButton(t(lang, "btn_to_tempo"), callback_data="metro")]
    )
    keyboard.append([InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")])
    return InlineKeyboardMarkup(keyboard)


def make_metronome_wav(bpm, beats_per_bar=4, total_seconds=30, sample_rate=44100):
    """Синтезирует WAV-клик метронома в памяти (без внешних зависимостей)."""
    beat_interval = 60.0 / bpm
    beat_samples = int(round(beat_interval * sample_rate))
    click_samples = min(int(0.04 * sample_rate), beat_samples)
    n_beats = max(1, int(total_seconds / beat_interval))

    def click_block(freq, amp):
        out = bytearray()
        for s in range(beat_samples):
            if s < click_samples:
                env = math.exp(-5.0 * s / click_samples)
                val = int(
                    amp * env * math.sin(2 * math.pi * freq * s / sample_rate) * 32767
                )
            else:
                val = 0
            out += struct.pack("<h", val)
        return bytes(out)

    accent = click_block(1320.0, 0.9)  # сильная доля
    normal = click_block(880.0, 0.55)  # слабые доли

    buf = io.BytesIO()
    w = wave.open(buf, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sample_rate)
    for i in range(n_beats):
        w.writeframes(accent if i % beats_per_bar == 0 else normal)
    w.close()
    buf.seek(0)
    buf.name = f"metronome_{bpm}bpm.wav"
    return buf


async def send_metronome(update_or_query, bpm, beats, lang):
    buf = make_metronome_wav(bpm, beats_per_bar=beats)
    caption = t(lang, "metro_caption", bpm=bpm, beats=beats)
    fname = f"metronome_{bpm}bpm_{beats}-{'4' if beats < 5 else '8'}.wav"
    try:
        await update_or_query.message.reply_audio(
            buf,
            title=t(lang, "metro_title", bpm=bpm, beats=beats),
            performer="JazzTone",
            caption=caption,
        )
    except Exception:
        buf.seek(0)
        await update_or_query.message.reply_document(
            buf, filename=fname, caption=caption
        )


async def metronome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(context, update.effective_user)
    context.user_data["awaiting_metro_bpm"] = False
    await update.message.reply_text(
        t(lang, "metro_text"),
        parse_mode="Markdown",
        reply_markup=metronome_keyboard(context, lang),
    )


def audio_keyboard(note, lang):
    """Клавиатура под нотой: плей-элонг/минус (если собрано аудио) +
    «разобрать мою игру» (для пьес — анализ привязан к этому произведению)."""
    nid = note["id"]
    rows = []
    if note.get("audio"):
        rows.append(
            [
                InlineKeyboardButton(
                    t(lang, "btn_playalong"), callback_data=f"aud_play_{nid}"
                ),
                InlineKeyboardButton(
                    t(lang, "btn_minus"), callback_data=f"aud_minus_{nid}"
                ),
            ]
        )
    if note.get("type", "piece") == "piece":
        rows.append(
            [
                InlineKeyboardButton(
                    t(lang, "btn_perf_piece"), callback_data=f"perfpiece_{nid}"
                )
            ]
        )
    return InlineKeyboardMarkup(rows) if rows else None


async def send_audio_track(update_or_query, note, kind, lang):
    """Шлёт mp3 (kind='play'|'minus') как audio с кэшем file_id на уровне work-записи."""
    audio = note.get("audio") or {}
    rel = audio.get("play") if kind == "play" else audio.get("minus")
    if not rel:
        await update_or_query.message.reply_text(t(lang, "audio_missing"))
        return
    fid_key = "play_file_id" if kind == "play" else "minus_file_id"
    cap_key = "cap_playalong" if kind == "play" else "cap_minus"
    caption = t(lang, cap_key, title=note["title"])
    performer = note.get("composer") or "JazzTone"
    suffix = " — play-along" if kind == "play" else " — backing"
    title = note["title"] + suffix

    cached = audio.get(fid_key)
    if cached:
        try:
            await update_or_query.message.reply_audio(
                cached, caption=caption, title=title, performer=performer
            )
            return
        except Exception:
            pass

    path = os.path.join(NOTES_FOLDER, rel)
    if not os.path.exists(path):
        await update_or_query.message.reply_text(t(lang, "audio_missing"))
        return
    with open(path, "rb") as f:
        sent = await update_or_query.message.reply_audio(
            f, caption=caption, title=title, performer=performer
        )
    fid = sent.audio.file_id if sent and sent.audio else None
    if fid:
        notes = load_notes()
        for n in notes:
            if n["id"] == note["id"] and n.get("audio"):
                n["audio"][fid_key] = fid
                break
        save_notes(notes)


async def send_note(update_or_query, note, instrument=None, lang="ru"):
    """Отправляет PDF-файл ноты. instrument — какую версию (партию) отдать;
    None → первая/legacy-версия (труба). Под PDF — кнопки аудио, если оно есть."""
    vers = versions_of(note)
    v = (
        next((x for x in vers if x.get("instrument") == instrument), None)
        if instrument
        else None
    )
    if v is None:
        v = vers[0]
    instr_key = v.get("instrument")
    is_legacy = v.get("legacy", False)
    file_path = os.path.join(NOTES_FOLDER, v["file"])
    cached_id = note.get("file_id") if is_legacy else v.get("file_id")

    cap = [f"🎺 {note['title']}", f"👤 {note.get('composer', '—')}"]
    style = note.get("style") or note.get("genre")
    if style:
        cap.append(f"🎵 {style}")
    if instr_key:
        kw = v.get("key_written")
        line = f"🎷 {instrument_label(instr_key, lang)}"
        if kw:
            line += f" · {t(lang, 'cap_key')} {kw}"
        cap.append(line)
    caption = "\n".join(cap)
    fname = f"{note['title']} - {note.get('composer', '')}.pdf"
    akb = audio_keyboard(note, lang)  # кнопки плей-элонг/минус, если аудио собрано

    if cached_id:
        try:
            await update_or_query.message.reply_document(
                cached_id, caption=caption, reply_markup=akb
            )
            return
        except Exception:
            pass

    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            sent = await update_or_query.message.reply_document(
                f, filename=fname, caption=caption, reply_markup=akb
            )
        # кэшируем file_id: legacy → на уровне ноты, версия → в самой версии
        notes = load_notes()
        for n in notes:
            if n["id"] == note["id"]:
                if is_legacy:
                    n["file_id"] = sent.document.file_id
                else:
                    for nv in n.get("versions", []):
                        if nv.get("instrument") == instr_key:
                            nv["file_id"] = sent.document.file_id
                            break
                break
        save_notes(notes)
    else:
        await update_or_query.message.reply_text(
            t(lang, "note_file_missing", title=note["title"])
        )


# ================== АНАЛИЗ ИГРЫ (БЕТА) ==================
def _ffmpeg_available():
    return shutil.which("ffmpeg") is not None


def _intonation_advice(res, lang):
    """Подробный совет «как именно работать» по сводке (голосовые 1 и 3)."""
    acc = res["accuracy"]
    signed = res["mean_signed_cents"]  # >0 высит, <0 низит
    spread = res["spread_cents"]  # разброс высоты
    if acc >= 80 and spread <= 12:
        return t(lang, "adv_great")

    tips = []
    if signed >= 8:
        tips.append(t(lang, "adv_sharp"))
    elif signed <= -8:
        tips.append(t(lang, "adv_flat"))
    if spread > 18:
        tips.append(t(lang, "adv_spread"))
    worst = sorted(res["notes"], key=lambda n: abs(n["hz"]), reverse=True)
    worst = [n for n in worst if abs(n["cents"]) > 15][:3]
    if worst:
        names = ", ".join(n["note"] for n in worst)
        tips.append(t(lang, "adv_worst", names=names))
    if not tips:
        tips.append(t(lang, "adv_almost"))
    return "\n".join("• " + tip for tip in tips)


def _format_perf_report(res, lang):
    """Человекочитаемый отчёт по результату analyze_performance()."""
    if not res.get("ok"):
        reasons = {
            "too_short": t(lang, "perf_fail_short"),
            "no_pitch": t(lang, "perf_fail_nopitch"),
        }
        return "🤔 " + reasons.get(res.get("reason"), t(lang, "fail_generic"))

    acc = res["accuracy"]
    if acc >= 80:
        verdict = t(lang, "verdict_good")
    elif acc >= 50:
        verdict = t(lang, "verdict_mid")
    else:
        verdict = t(lang, "verdict_bad")

    lines = [
        t(lang, "report_header") + "\n",
        verdict,
        t(lang, "report_count", n=res["count"]),
        t(lang, "report_clean", a=res["in_tune"], b=res["count"], acc=acc),
        t(lang, "report_meandev", hz=res["mean_abs_hz"]) + "\n",
        t(lang, "report_bynote"),
    ]
    unit = t(lang, "hz")
    for n in res["notes"][:30]:
        c, hz = n["cents"], n["hz"]
        if abs(c) <= 10:
            mark, fix = "🟢", ""
        elif abs(c) <= 25:
            mark = "🟡"
            fix = t(lang, "fix_lo_soft") if c > 0 else t(lang, "fix_hi_soft")
        else:
            mark = "🟠"
            fix = t(lang, "fix_lo") if c > 0 else t(lang, "fix_hi")
        sign = f"+{hz}" if hz > 0 else str(hz)
        lines.append(f"{mark} `{n['note']:<4}` {sign} {unit}{fix}")
    if res["count"] > 30:
        lines.append(t(lang, "report_more", n=res["count"] - 30))

    lines.append("\n" + t(lang, "report_howto"))
    lines.append(_intonation_advice(res, lang))
    return "\n".join(lines)


async def _download_and_decode(update, context, status, lang):
    """Скачивает голосовое/аудио и декодирует в WAV 22050 mono.
    Возвращает (wav_path, tmpdir) или (None, None) с сообщением об ошибке в status."""
    if not _ffmpeg_available():
        logger.error("ffmpeg не найден в PATH")
        await status.edit_text(t(lang, "no_ffmpeg"))
        return None, None
    media = update.message.voice or update.message.audio or update.message.document
    if media is None:
        return None, None

    tmpdir = tempfile.mkdtemp(prefix="aud_")
    oga = os.path.join(
        tmpdir, "in.audio"
    )  # ffmpeg определяет формат по содержимому (oga/mp3/flac/m4a)
    wav = os.path.join(tmpdir, "out.wav")
    try:
        tg_file = await context.bot.get_file(media.file_id)
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        await status.edit_text(t(lang, "dl_too_big"))
        return None, None
    await tg_file.download_to_drive(oga)
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-i",
        oga,
        "-ac",
        "1",
        "-ar",
        "22050",
        "-y",
        wav,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    await proc.wait()
    if proc.returncode != 0 or not os.path.exists(wav):
        shutil.rmtree(tmpdir, ignore_errors=True)
        await status.edit_text(t(lang, "dl_decode_fail"))
        return None, None
    return wav, tmpdir


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Диспетчер голосовых: разбор интонации или транскрипция в ноты."""
    if context.user_data.get("awaiting_trans"):
        await _handle_transcribe(update, context)
    elif context.user_data.get("awaiting_perf"):
        await _handle_perf(update, context)
    # голос вне режимов игнорируем


async def _handle_perf(update, context):
    """Разбор интонации записанной игры (центы)."""
    lang = user_lang(context, update.effective_user)
    user_id = update.effective_user.id
    # Платный гейт (council: дорогой AI). Бесплатный лимит → потом Stars-кредиты.
    if BILLING_ENABLED and not billing.can_analyze(user_id):
        await update.message.reply_text(
            t(lang, "paywall_text"),
            parse_mode="Markdown",
            reply_markup=paywall_keyboard(lang),
        )
        return
    try:
        from analysis import analyze_performance
    except Exception as e:
        logger.error(f"analysis не импортируется: {e}")
        await update.message.reply_text(t(lang, "analysis_missing"))
        return

    await update.message.chat.send_action("typing")
    status = await update.message.reply_text(t(lang, "perf_listening"))
    wav, tmpdir = await _download_and_decode(update, context, status, lang)
    if wav is None:
        return
    try:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, analyze_performance, wav)
        piece = context.user_data.get("perf_piece")
        report = _format_perf_report(res, lang)
        ask_kb = None
        if piece:  # разбор привязан к произведению (ГС2)
            report = f"🎯 «{piece['title']}»\n" + report
            if res.get("ok"):
                context.user_data["perf_summary"] = _perf_summary_text(res)
                ask_kb = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                t(lang, "btn_ask_coach"),
                                callback_data=f"askq_{piece['id']}",
                            )
                        ]
                    ]
                )
        await status.edit_text(report, parse_mode="Markdown", reply_markup=ask_kb)
        if BILLING_ENABLED:
            billing.consume(user_id)  # списываем разбор ТОЛЬКО при успешном результате
    except Exception as e:
        logger.error(f"Ошибка анализа игры: {e}")
        try:
            await status.edit_text(t(lang, "perf_error"))
        except Exception:
            pass
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _perf_summary_text(res):
    """Компактная фактическая сводка разбора для контекста ИИ-консультации."""
    worst = [n for n in res.get("notes", []) if abs(n.get("cents", 0)) > 15][:5]
    worst_s = (
        ", ".join(f"{n['note']} {int(round(n['cents'])):+d}c" for n in worst) or "—"
    )
    return (
        f"accuracy={res.get('accuracy')}%, нот={res.get('count')}, "
        f"в строе={res.get('in_tune')}, ср.отклонение={res.get('mean_signed_cents')}c "
        f"(>0 высит, <0 низит), разброс={res.get('spread_cents')}c, "
        f"хуже всего: {worst_s}"
    )


def _coach_answer(piece_title, perf_summary, question, lang):
    """Ответ ИИ-наставника (Claude API) по пьесе + игре ученика. None если не настроено."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except Exception:
        return None
    if lang == "en":
        sys = (
            "You are an experienced jazz trumpet teacher. Answer the student's question about "
            "the given piece and their own playing. Be concrete, warm and brief: 1–3 short "
            "paragraphs with practical practice advice. Reply with the final answer only, no preamble."
        )
    else:
        sys = (
            "Ты опытный преподаватель джазовой трубы. Отвечай на вопрос ученика по конкретной "
            "пьесе и его собственной игре. Конкретно, по-доброму и КРАТКО: 1–3 коротких абзаца с "
            "практическими советами как заниматься. Только финальный ответ, без вступлений."
        )
    user = (
        f"Пьеса: {piece_title}\n"
        f"Сводка разбора игры ученика: {perf_summary or 'нет данных'}\n"
        f"Вопрос: {question}"
    )
    client = anthropic.Anthropic()  # ключ из env ANTHROPIC_API_KEY
    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=900,
        system=sys,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(
        b.text for b in resp.content if getattr(b, "type", None) == "text"
    ).strip()


# ================== БИЛЛИНГ (Telegram Stars) ==================
def paywall_keyboard(lang):
    rows = []
    for payload, (cred, stars) in billing.PACKS.items():
        rows.append(
            [
                InlineKeyboardButton(
                    t(lang, "buy_pack", n=cred, stars=stars),
                    callback_data=f"buy_{payload}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")])
    return InlineKeyboardMarkup(rows)


async def send_analysis_invoice(update, context, payload):
    lang = user_lang(context, update.effective_user)
    pack = billing.PACKS.get(payload)
    if not pack:
        return
    cred, stars = pack
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title=t(lang, "invoice_title", n=cred),
        description=t(lang, "invoice_desc", n=cred),
        payload=payload,
        provider_token="",  # пусто = оплата Telegram Stars
        currency="XTR",
        prices=[LabeledPrice(t(lang, "invoice_label", n=cred), stars)],
    )


async def buy_command(update, context):
    """/buy — показать баланс разборов и предложить докупить (можно в любой момент)."""
    lang = user_lang(context, update.effective_user)
    free_left, bal = billing.status(update.effective_user.id)
    await update.message.reply_text(
        t(lang, "buy_status", free=free_left, bal=bal),
        parse_mode="Markdown",
        reply_markup=paywall_keyboard(lang),
    )


async def precheckout(update, context):
    # Ответить надо в 10 сек, иначе Telegram отменит платёж.
    q = update.pre_checkout_query
    await q.answer(
        ok=q.invoice_payload in billing.PACKS, error_message="Unknown product"
    )


async def on_successful_payment(update, context):
    sp = update.message.successful_payment
    lang = user_lang(context, update.effective_user)
    pack = billing.PACKS.get(sp.invoice_payload)
    if not pack:
        return
    cred, _stars = pack
    is_new = billing.record_payment(
        sp.telegram_payment_charge_id, update.effective_user.id, sp.total_amount, cred
    )
    if is_new:
        _, bal = billing.status(update.effective_user.id)
        await update.message.reply_text(
            t(lang, "pay_thanks", n=cred, bal=bal), parse_mode="Markdown"
        )


# ================== НОТЫ ИЗ ЗАПИСИ (БЕТА) ==================
def trans_instrument_keyboard(lang):
    from transcribe import INSTRUMENTS

    keyboard, row = [], []
    for key in INSTRUMENTS:
        row.append(
            InlineKeyboardButton(instrument_label(key, lang), callback_data=f"ti_{key}")
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")])
    return InlineKeyboardMarkup(keyboard)


def _format_trans_report(res, label, lang):
    conf = res["confidence"]
    if conf >= 80:
        cmark = t(lang, "conf_high")
    elif conf >= 55:
        cmark = t(lang, "conf_mid")
    else:
        cmark = t(lang, "conf_low")
    lines = [
        t(lang, "trans_report_header") + "\n",
        t(lang, "trans_instrument", label=label),
        t(lang, "trans_notes", n=res["count"]),
        t(lang, "trans_conf", c=conf, mark=cmark) + "\n",
        t(lang, "trans_foot1"),
        t(lang, "trans_foot2"),
    ]
    return "\n".join(lines)


async def _handle_transcribe(update, context):
    """Транскрипция записи в ноты → MIDI + MusicXML + сохранение в «Мои ноты»."""
    lang = user_lang(context, update.effective_user)
    try:
        import transcribe as T
    except Exception as e:
        logger.error(f"transcribe не импортируется: {e}")
        await update.message.reply_text(t(lang, "trans_missing"))
        return

    key = context.user_data.get("trans_instr", "concert")
    _ru_label, offset = T.INSTRUMENTS.get(key, T.INSTRUMENTS["concert"])
    label = instrument_label(key, lang)

    await update.message.chat.send_action("typing")
    status = await update.message.reply_text(t(lang, "trans_recognizing"))
    wav, tmpdir = await _download_and_decode(update, context, status, lang)
    if wav is None:
        return
    try:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, T.transcribe, wav)
        if not res.get("ok"):
            reasons = {
                "too_short": t(lang, "trans_fail_short"),
                "no_pitch": t(lang, "trans_fail_nopitch"),
            }
            await status.edit_text(
                "🤔 " + reasons.get(res.get("reason"), t(lang, "fail_generic"))
            )
            return

        midi_bytes = T.render_midi(res["notes"], offset=offset)
        xml_text = T.render_musicxml(res["notes"], offset=offset, title="Транскрипция")
        title = t(
            lang,
            "trans_title_prefix",
            dt=datetime.datetime.now().strftime("%d.%m %H:%M"),
        )

        nid = mynotes.add(
            update.effective_user.id,
            title,
            label,
            res["confidence"],
            res["count"],
            midi_bytes,
            xml_text,
        )

        await status.edit_text(
            _format_trans_report(res, label, lang), parse_mode="Markdown"
        )
        base = f"{title}".replace(" ", "_").replace(":", "-")

        png = await loop.run_in_executor(None, T.render_png, xml_text)
        if png:
            await update.message.reply_photo(
                io.BytesIO(png), caption=f"🎼 {title} · {label}"
            )

        await update.message.reply_document(
            io.BytesIO(midi_bytes),
            filename=f"{base}.mid",
            caption=t(lang, "midi_caption"),
        )
        await update.message.reply_document(
            io.BytesIO(xml_text.encode("utf-8")),
            filename=f"{base}.musicxml",
            caption=t(lang, "xml_caption"),
        )
        context.user_data["awaiting_trans"] = False
        await update.message.reply_text(
            t(lang, "trans_saved", nid=nid),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")]]
            ),
        )
    except Exception as e:
        logger.error(f"Ошибка транскрипции: {e}")
        try:
            await status.edit_text(t(lang, "trans_error"))
        except Exception:
            pass
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ================== «МОИ НОТЫ» ==================
async def show_my_notes(query, lang):
    rows = mynotes.list_for(query.from_user.id)
    if not rows:
        await query.edit_message_text(
            t(lang, "mynotes_empty"),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")]]
            ),
        )
        return
    keyboard = []
    for nid, title, instrument, conf, n_notes, _created in rows:
        keyboard.append(
            [
                InlineKeyboardButton(
                    t(
                        lang,
                        "mynote_btn",
                        title=title,
                        instr=instrument,
                        n=n_notes,
                        c=conf,
                    ),
                    callback_data=f"mn_{nid}",
                )
            ]
        )
    keyboard.append([InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")])
    await query.edit_message_text(
        t(lang, "mynotes_title"),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def send_my_note(query, nid, lang):
    row = mynotes.get(query.from_user.id, nid)
    if not row:
        await query.message.reply_text(t(lang, "mynote_notfound"))
        return
    _id, title, instrument, conf, n_notes, midi_path, xml_path = row
    caption = t(
        lang, "mynote_caption", title=title, instr=instrument, n=n_notes, c=conf
    )

    if xml_path and os.path.exists(xml_path):
        try:
            import transcribe as T

            with open(xml_path, encoding="utf-8") as f:
                xml_text = f.read()
            loop = asyncio.get_running_loop()
            png = await loop.run_in_executor(None, T.render_png, xml_text)
            if png:
                await query.message.reply_photo(io.BytesIO(png), caption=caption)
        except Exception as e:
            logger.error(f"render_png (my note) failed: {e}")

    sent_any = False
    for path, cap in ((midi_path, caption), (xml_path, None)):
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                await query.message.reply_document(f, caption=cap)
            sent_any = True
    if not sent_any:
        await query.message.reply_text(t(lang, "mynote_nofiles"))
        return
    await query.message.reply_text(
        t(lang, "mynote_manage"),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        t(lang, "btn_delete"), callback_data=f"mndel_{nid}"
                    )
                ],
                [InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")],
            ]
        ),
    )


# ================== ГЛАВНОЕ МЕНЮ / ЯЗЫК ==================
def main_menu_keyboard(lang):
    rows = [
        [InlineKeyboardButton(t(lang, "btn_open_app"), web_app=WebAppInfo(HOME_URL))],
        [InlineKeyboardButton(t(lang, "btn_pieces"), callback_data="cat_piece")],
        [InlineKeyboardButton(t(lang, "btn_etudes"), callback_data="cat_etude")],
        [InlineKeyboardButton(t(lang, "btn_books"), callback_data="cat_book")],
        [InlineKeyboardButton(t(lang, "btn_search"), callback_data="smart_search")],
        [InlineKeyboardButton(t(lang, "btn_metro"), callback_data="metro")],
        [InlineKeyboardButton(t(lang, "btn_tuner"), web_app=WebAppInfo(TUNER_URL))],
        [InlineKeyboardButton(t(lang, "btn_perf"), callback_data="perf")],
        [InlineKeyboardButton(t(lang, "btn_trans"), callback_data="trans")],
        [InlineKeyboardButton(t(lang, "btn_mynotes"), callback_data="mynotes")],
        [InlineKeyboardButton(t(lang, "btn_suggest"), callback_data="suggest")],
    ]
    if BILLING_ENABLED:
        rows.append([InlineKeyboardButton(t(lang, "btn_buy"), callback_data="buy")])
    rows.append([InlineKeyboardButton(t(lang, "btn_lang"), callback_data="langmenu")])
    return InlineKeyboardMarkup(rows)


def lang_picker_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Русский 🇷🇺", callback_data="setlang_ru"),
                InlineKeyboardButton("English 🇬🇧", callback_data="setlang_en"),
            ]
        ]
    )


# Разделы, в которые умеет «прыгать» мини-аппа через deep-link /start go_<section>.
SECTION_GO = (
    "piece",
    "etude",
    "book",
    "search",
    "metro",
    "perf",
    "trans",
    "mynotes",
    "suggest",
    "buy",
)


async def open_section(
    update: Update, context: ContextTypes.DEFAULT_TYPE, section: str, lang: str
):
    """Открыть первый экран раздела НОВЫМ сообщением (для входа из мини-аппы по /start go_<section>).
    Намеренно изолировано от button_handler — рисует те же клавиатуры через reply_text, дальше работают обычные колбэки."""
    msg = update.message
    if section in ("piece", "etude", "book"):
        notes = load_notes()
        keyboard = []
        for key in LIBRARY_INSTRUMENTS:
            count = len(notes_for_instrument(notes, key, section))
            if count == 0:
                continue
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{instrument_label(key, lang)} · {count}",
                        callback_data=f"inst_{section}_{key}",
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")]
        )
        label = cat_label(section, lang)
        if len(keyboard) == 1:
            await msg.reply_text(
                t(lang, "picker_empty", cat=label),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await msg.reply_text(
                t(lang, "picker_title", cat=label),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
    elif section == "search":
        notes = load_notes()
        letters = sorted(set(n["composer"][0].upper() for n in notes if n["composer"]))
        keyboard, row = [], []
        for letter in letters:
            row.append(InlineKeyboardButton(letter, callback_data=f"letter_{letter}"))
            if len(row) == 4:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append(
            [InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")]
        )
        await msg.reply_text(
            t(lang, "search_title"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
    elif section == "metro":
        context.user_data["awaiting_metro_bpm"] = False
        await msg.reply_text(
            t(lang, "metro_text"),
            parse_mode="Markdown",
            reply_markup=metronome_keyboard(context, lang),
        )
    elif section == "perf":
        context.user_data["awaiting_perf"] = True
        await msg.reply_text(
            t(lang, "perf_text"),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")]]
            ),
        )
    elif section == "trans":
        await msg.reply_text(
            t(lang, "trans_text"),
            parse_mode="Markdown",
            reply_markup=trans_instrument_keyboard(lang),
        )
    elif section == "mynotes":
        rows = mynotes.list_for(update.effective_user.id)
        if not rows:
            await msg.reply_text(
                t(lang, "mynotes_empty"),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")]]
                ),
            )
        else:
            keyboard = [
                [
                    InlineKeyboardButton(
                        t(
                            lang,
                            "mynote_btn",
                            title=title,
                            instr=instrument,
                            n=n_notes,
                            c=conf,
                        ),
                        callback_data=f"mn_{nid}",
                    )
                ]
                for nid, title, instrument, conf, n_notes, _created in rows
            ]
            keyboard.append(
                [InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")]
            )
            await msg.reply_text(
                t(lang, "mynotes_title"),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
    elif section == "suggest":
        context.user_data["awaiting_suggestion"] = True
        await msg.reply_text(t(lang, "suggest_prompt"), parse_mode="Markdown")
    elif section == "buy":
        free_left, bal = billing.status(update.effective_user.id)
        await msg.reply_text(
            t(lang, "buy_status", free=free_left, bal=bal),
            parse_mode="Markdown",
            reply_markup=paywall_keyboard(lang),
        )


# ================== КОМАНДЫ ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = (
        context.args
    )  # deep-link: /start ru|en (язык с сайта)  или  /start go_<section> (из мини-аппы)
    context.user_data.clear()
    arg0 = args[0] if args else ""
    if arg0 in LANGS:
        lang = arg0  # пришёл с сайта — берём язык страницы
    else:
        lang = user_lang(context, user)  # сохранённый → язык Telegram-клиента → ru
    set_lang(
        context, user.id, lang
    )  # фиксируем выбор (стабильные локализованные команды)
    # Deep-link из мини-аппы: доставить конкретную партию (get_<instr>_<id>) — каталог листается в аппе, файл шлёт бот.
    if arg0.startswith("get_"):
        parts = arg0[4:].rsplit("_", 1)
        if len(parts) == 2 and parts[1].isdigit():
            instr, nid = parts[0], int(parts[1])
            note = next((n for n in load_notes() if n["id"] == nid), None)
            if note:
                await send_note(
                    update,
                    note,
                    instrument=(None if instr == "any" else instr),
                    lang=lang,
                )
                return
    # Deep-link из мини-аппы: сразу открыть нужный раздел, без промежуточного меню.
    if arg0.startswith("go_") and arg0[3:] in SECTION_GO:
        await open_section(update, context, arg0[3:], lang)
        return
    await update.message.reply_text(
        t(lang, "welcome"), parse_mode="Markdown", reply_markup=main_menu_keyboard(lang)
    )


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        t("ru", "lang_prompt"), reply_markup=lang_picker_keyboard()
    )


async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(context, update.effective_user)
    context.user_data.clear()
    context.user_data["lang"] = lang
    await update.message.reply_text(
        t(lang, "welcome"), parse_mode="Markdown", reply_markup=main_menu_keyboard(lang)
    )


async def random_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(context, update.effective_user)
    notes = load_notes()
    if not notes:
        await update.message.reply_text(t(lang, "random_empty"))
        return
    note = random.choice(notes)
    await send_note(update, note, lang=lang)


async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(context, update.effective_user)
    await update.message.reply_text(t(lang, "feedback"))


async def credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(context, update.effective_user)
    await update.message.reply_text(t(lang, "credits"), parse_mode="Markdown")


# ================== КАТЕГОРИИ (КЛИКАБЕЛЬНЫЕ КНОПКИ) ==================
def cat_label(category, lang):
    return t(lang, "cat_" + category) if ("cat_" + category) in TR["ru"] else category


async def show_instrument_picker(
    update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, lang: str
):
    """Экран выбора инструмента внутри раздела (произведения/этюды/книги)."""
    query = update.callback_query
    notes = load_notes()
    keyboard = []
    for key in LIBRARY_INSTRUMENTS:
        count = len(notes_for_instrument(notes, key, category))
        if count == 0:
            continue  # инструменты без материала в этом разделе не показываем
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{instrument_label(key, lang)} · {count}",
                    callback_data=f"inst_{category}_{key}",
                )
            ]
        )
    keyboard.append([InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")])
    label = cat_label(category, lang)
    if len(keyboard) == 1:  # только кнопка «домой» → материала нет
        await query.edit_message_text(
            t(lang, "picker_empty", cat=label),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
    await query.edit_message_text(
        t(lang, "picker_title", cat=label),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def show_instrument_pieces(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    category: str,
    instrument: str,
    lang: str,
    page: int = 0,
):
    """Список материала раздела с партией под выбранный инструмент (с пагинацией)."""
    query = update.callback_query
    notes = load_notes()
    filtered = notes_for_instrument(notes, instrument, category)
    if not filtered:
        await query.edit_message_text(
            t(lang, "pieces_empty", instr=instrument_label(instrument, lang)),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            t(lang, "btn_to_instruments"),
                            callback_data=f"cat_{category}",
                        )
                    ],
                    [InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")],
                ]
            ),
        )
        return

    start_idx = page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, len(filtered))
    keyboard = []
    for note in filtered[start_idx:end_idx]:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{note['title']} – {note.get('composer', '')}",
                    callback_data=f"pi_{category}_{instrument}_{note['id']}",
                )
            ]
        )

    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                t(lang, "btn_back"),
                callback_data=f"inst_{category}_{instrument}_{page - 1}",
            )
        )
    if end_idx < len(filtered):
        nav.append(
            InlineKeyboardButton(
                t(lang, "btn_next"),
                callback_data=f"inst_{category}_{instrument}_{page + 1}",
            )
        )
    if nav:
        keyboard.append(nav)
    keyboard.append(
        [
            InlineKeyboardButton(
                t(lang, "btn_other_instr"), callback_data=f"cat_{category}"
            )
        ]
    )
    keyboard.append([InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")])

    await query.edit_message_text(
        t(
            lang,
            "pieces_title",
            instr=instrument_label(instrument, lang),
            cat=cat_label(category, lang),
            a=start_idx + 1,
            b=end_idx,
            total=len(filtered),
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ================== УМНЫЙ ПОИСК ==================
async def smart_search_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str
):
    query = update.callback_query
    notes = load_notes()
    composers = sorted(set(n["composer"] for n in notes))
    letters = sorted(set(c[0].upper() for c in composers if c))

    keyboard, row = [], []
    for letter in letters:
        row.append(InlineKeyboardButton(letter, callback_data=f"letter_{letter}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")])
    await query.edit_message_text(
        t(lang, "search_title"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def show_composers_by_letter(
    update: Update, context: ContextTypes.DEFAULT_TYPE, letter: str, lang: str
):
    query = update.callback_query
    notes = load_notes()
    composers = sorted(
        set(n["composer"] for n in notes if n["composer"].upper().startswith(letter))
    )
    if not composers:
        await query.edit_message_text(t(lang, "no_composers_letter", l=letter))
        return
    keyboard = [
        [InlineKeyboardButton(comp, callback_data=f"composer_{comp}")]
        for comp in composers
    ]
    keyboard.append(
        [InlineKeyboardButton(t(lang, "btn_to_letters"), callback_data="smart_search")]
    )
    keyboard.append([InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")])
    await query.edit_message_text(
        t(lang, "composers_letter_title", l=letter),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def show_notes_by_composer(
    update: Update, context: ContextTypes.DEFAULT_TYPE, composer: str, lang: str
):
    query = update.callback_query
    notes = load_notes()
    filtered = [n for n in notes if n["composer"] == composer]
    if not filtered:
        await query.edit_message_text(t(lang, "no_pieces_composer", c=composer))
        return
    keyboard = [
        [InlineKeyboardButton(note["title"], callback_data=f"note_{note['id']}")]
        for note in filtered
    ]
    keyboard.append(
        [
            InlineKeyboardButton(
                t(lang, "btn_to_composers"), callback_data="smart_search"
            )
        ]
    )
    keyboard.append([InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")])
    await query.edit_message_text(
        t(lang, "pieces_composer_title", c=composer),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ================== ПРЕДЛОЖЕНИЯ ОТ ПОЛЬЗОВАТЕЛЕЙ ==================
def _is_audio_document(doc):
    if doc is None:
        return False
    if (doc.mime_type or "").startswith("audio/"):
        return True
    name = (doc.file_name or "").lower()
    return name.endswith(
        (".mp3", ".flac", ".m4a", ".wav", ".ogg", ".oga", ".aac", ".opus")
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(context, update.effective_user)
    # Аудиофайл (MP3/FLAC/…) в режиме «ноты из записи» или «анализ игры» → в тот же конвейер
    if context.user_data.get("awaiting_trans") or context.user_data.get(
        "awaiting_perf"
    ):
        if _is_audio_document(update.message.document):
            await handle_voice(update, context)
            return
        await update.message.reply_text(
            t(lang, "doc_send_audio"), parse_mode="Markdown"
        )
        return

    if context.user_data.get("awaiting_suggestion"):
        user = update.effective_user
        document = update.message.document
        if document.mime_type == "application/pdf":
            try:
                await context.bot.send_document(
                    chat_id=YOUR_USER_ID,
                    document=document.file_id,
                    caption=f"📝 PDF suggestion\n👤 {user.full_name}\n🆔 {user.id}\n📎 {document.file_name}",
                )
                await update.message.reply_text(t(lang, "suggest_sent_curator"))
            except Exception as e:
                await update.message.reply_text(t(lang, "suggest_fail"))
                logger.error(f"Ошибка отправки PDF: {e}")
        else:
            await update.message.reply_text(
                t(lang, "suggest_need_pdf"), parse_mode="Markdown"
            )
        context.user_data["awaiting_suggestion"] = False
        return


# ================== ОБРАБОТЧИКИ СООБЩЕНИЙ ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(context, update.effective_user)
    text = update.message.text.strip()
    if text.startswith("/"):
        return

    # ИИ-консультация по пьесе после разбора игры (ГС2) — платный гейт как у анализа
    if context.user_data.get("awaiting_question"):
        context.user_data["awaiting_question"] = False
        user_id = update.effective_user.id
        if BILLING_ENABLED and not billing.can_analyze(user_id):
            await update.message.reply_text(
                t(lang, "paywall_text"),
                parse_mode="Markdown",
                reply_markup=paywall_keyboard(lang),
            )
            return
        piece = context.user_data.get("perf_piece") or {}
        summary = context.user_data.get("perf_summary")
        await update.message.chat.send_action("typing")
        status = await update.message.reply_text(t(lang, "coach_thinking"))
        try:
            loop = asyncio.get_running_loop()
            answer = await loop.run_in_executor(
                None, _coach_answer, piece.get("title", ""), summary, text, lang
            )
        except Exception as e:
            logger.error(f"Ошибка ИИ-консультации: {e}")
            await status.edit_text(t(lang, "coach_error"))
            return
        if not answer:
            await status.edit_text(t(lang, "coach_unavailable"))
            return
        await status.edit_text(answer)
        if BILLING_ENABLED:
            billing.consume(user_id)  # списываем только при успешном ответе
        return

    if context.user_data.get("awaiting_trans"):
        low = text.lower()
        if "youtu" in low or low.startswith("http"):
            await update.message.reply_text(
                t(lang, "trans_link_warn"), parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                t(lang, "trans_send_audio"), parse_mode="Markdown"
            )
        return

    if context.user_data.get("awaiting_metro_bpm"):
        context.user_data["awaiting_metro_bpm"] = False
        digits = "".join(ch for ch in text if ch.isdigit())
        bpm = int(digits) if digits else 0
        if not (METRO_BPM_MIN <= bpm <= METRO_BPM_MAX):
            await update.message.reply_text(
                t(lang, "metro_bad_bpm", min=METRO_BPM_MIN, max=METRO_BPM_MAX)
            )
            return
        context.user_data["metro_bpm"] = bpm
        await update.message.reply_text(
            t(lang, "metro_size_prompt", bpm=bpm),
            reply_markup=metronome_size_keyboard(lang),
        )
        return

    if context.user_data.get("awaiting_suggestion"):
        user = update.effective_user
        try:
            await context.bot.send_message(
                chat_id=YOUR_USER_ID,
                text=f"📝 Suggestion\n👤 {user.full_name}\n🆔 {user.id}\n📌 {text}",
            )
            await update.message.reply_text(t(lang, "suggest_sent"))
        except Exception as e:
            await update.message.reply_text(t(lang, "suggest_fail"))
            logger.error(f"Ошибка отправки сообщения: {e}")
        context.user_data["awaiting_suggestion"] = False
        return

    # Обычный текстовый поиск
    notes = load_notes()
    results = [
        n
        for n in notes
        if text.lower() in n["title"].lower() or text.lower() in n["composer"].lower()
    ]
    if not results:
        await update.message.reply_text(t(lang, "search_none"), parse_mode="Markdown")
        return

    keyboard = []
    for note in results[:20]:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{note['title']} – {note['composer']}",
                    callback_data=f"note_{note['id']}",
                )
            ]
        )
    keyboard.append([InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")])
    await update.message.reply_text(
        t(lang, "search_results", q=text),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ================== ОБРАБОТЧИК КНОПОК ==================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = user_lang(context, query.from_user)

    if data.startswith("setlang_"):
        lang = data[len("setlang_") :]
        set_lang(context, query.from_user.id, lang)
        await query.edit_message_text(
            t(lang, "welcome"),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )

    elif data == "langmenu":
        await query.edit_message_text(
            t(lang, "lang_prompt"), reply_markup=lang_picker_keyboard()
        )

    elif data == "home":
        await query.edit_message_text(
            t(lang, "welcome"),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )

    elif data == "suggest":
        await query.edit_message_text(t(lang, "suggest_prompt"), parse_mode="Markdown")
        context.user_data["awaiting_suggestion"] = True

    elif data.startswith("perfpiece_"):
        nid = int(data[len("perfpiece_") :])
        note = next((n for n in load_notes() if n["id"] == nid), None)
        if not note:
            await query.message.reply_text(t(lang, "note_not_found"))
        else:
            context.user_data.clear()
            context.user_data["lang"] = lang
            context.user_data["perf_piece"] = {"id": nid, "title": note["title"]}
            context.user_data["awaiting_perf"] = True
            await query.message.reply_text(
                t(lang, "perfpiece_prompt", title=note["title"]),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")]]
                ),
            )

    elif data.startswith("askq_"):
        nid = int(data[len("askq_") :])
        note = next((n for n in load_notes() if n["id"] == nid), None)
        title = (
            note["title"]
            if note
            else context.user_data.get("perf_piece", {}).get("title", "")
        )
        context.user_data["perf_piece"] = {"id": nid, "title": title}
        context.user_data["awaiting_question"] = True
        await query.message.reply_text(
            t(lang, "askq_prompt", title=title), parse_mode="Markdown"
        )

    elif data == "perf":
        context.user_data.clear()
        context.user_data["lang"] = lang
        context.user_data["awaiting_perf"] = True
        await query.edit_message_text(
            t(lang, "perf_text"),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")]]
            ),
        )

    elif data == "buy":
        free_left, bal = billing.status(query.from_user.id)
        await query.edit_message_text(
            t(lang, "buy_status", free=free_left, bal=bal),
            parse_mode="Markdown",
            reply_markup=paywall_keyboard(lang),
        )

    elif data.startswith("buy_"):
        await send_analysis_invoice(update, context, data[4:])

    elif data == "trans":
        context.user_data.clear()
        context.user_data["lang"] = lang
        await query.edit_message_text(
            t(lang, "trans_text"),
            parse_mode="Markdown",
            reply_markup=trans_instrument_keyboard(lang),
        )

    elif data.startswith("ti_"):
        key = data[len("ti_") :]
        label = instrument_label(key, lang)
        context.user_data.clear()
        context.user_data["lang"] = lang
        context.user_data["trans_instr"] = key
        context.user_data["awaiting_trans"] = True
        await query.edit_message_text(
            t(lang, "trans_pick_prompt", label=label),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(t(lang, "btn_home"), callback_data="home")]]
            ),
        )

    elif data == "mynotes":
        await show_my_notes(query, lang)

    elif data.startswith("mndel_"):
        nid = int(data[len("mndel_") :])
        ok = mynotes.delete(query.from_user.id, nid)
        await query.edit_message_text(
            t(lang, "deleted") if ok else t(lang, "notfound_generic")
        )

    elif data.startswith("mn_"):
        nid = int(data[len("mn_") :])
        await send_my_note(query, nid, lang)

    elif data.startswith("cat_"):
        category = data.split("_")[1]
        await show_instrument_picker(update, context, category, lang)

    elif data.startswith("inst_"):
        parts = data[len("inst_") :].split("_")
        page = int(parts.pop()) if parts[-1].isdigit() else 0
        category, instrument = parts[0], parts[1]
        await show_instrument_pieces(update, context, category, instrument, lang, page)

    elif data.startswith("pi_"):
        parts = data[len("pi_") :].split("_")
        note_id = int(parts[-1])
        instrument = "_".join(parts[1:-1])
        notes = load_notes()
        note = next((n for n in notes if n["id"] == note_id), None)
        if note:
            await send_note(query, note, instrument=instrument, lang=lang)
        else:
            await query.message.reply_text(t(lang, "note_not_found"))

    elif data.startswith("aud_"):
        kind, nid = data[len("aud_") :].split("_", 1)  # play|minus, <id>
        note = next((n for n in load_notes() if n["id"] == int(nid)), None)
        if note:
            await send_audio_track(query, note, kind, lang)
        else:
            await query.message.reply_text(t(lang, "note_not_found"))

    elif data == "metro":
        context.user_data["awaiting_metro_bpm"] = False
        await query.edit_message_text(
            t(lang, "metro_text"),
            parse_mode="Markdown",
            reply_markup=metronome_keyboard(context, lang),
        )

    elif data == "metro_custom":
        context.user_data["awaiting_metro_bpm"] = True
        await query.edit_message_text(
            t(lang, "metro_custom_prompt", min=METRO_BPM_MIN, max=METRO_BPM_MAX),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(t(lang, "btn_back"), callback_data="metro")]]
            ),
        )

    elif data.startswith("metro_bpm_"):
        bpm = int(data[len("metro_bpm_") :])
        context.user_data["metro_bpm"] = bpm
        context.user_data["awaiting_metro_bpm"] = False
        await query.edit_message_text(
            t(lang, "metro_size_prompt", bpm=bpm),
            reply_markup=metronome_size_keyboard(lang),
        )

    elif data.startswith("metro_size_"):
        beats = int(data[len("metro_size_") :])
        bpm = context.user_data.get("metro_bpm", 120)
        await send_metronome(query, bpm, beats, lang)

    elif data == "smart_search":
        await smart_search_menu(update, context, lang)

    elif data.startswith("letter_"):
        letter = data.split("_")[1]
        await show_composers_by_letter(update, context, letter, lang)

    elif data.startswith("composer_"):
        composer = data[len("composer_") :]
        await show_notes_by_composer(update, context, composer, lang)

    elif data.startswith("note_"):
        note_id = int(data.split("_")[1])
        notes = load_notes()
        note = next((n for n in notes if n["id"] == note_id), None)
        if note:
            await send_note(query, note, lang=lang)
        else:
            await query.message.reply_text(t(lang, "note_not_found"))


# ================== ЗАПУСК ==================
# Локализованное меню команд Telegram (подсказки в «/» и кнопке меню).
COMMANDS = {
    "ru": [
        ("start", "Запуск / меню"),
        ("language", "Сменить язык 🌐"),
        ("metronome", "Метроном"),
        ("random", "Случайная пьеса"),
        ("feedback", "Связаться"),
        ("credits", "Источники нот"),
    ],
    "en": [
        ("start", "Start / menu"),
        ("language", "Change language 🌐"),
        ("metronome", "Metronome"),
        ("random", "Random piece"),
        ("feedback", "Contact"),
        ("credits", "Sources"),
    ],
}


async def post_init(app):
    """Регистрируем локализованные команды: en по умолчанию, ru для ru-клиентов."""
    try:
        await app.bot.set_my_commands([BotCommand(c, d) for c, d in COMMANDS["en"]])
        await app.bot.set_my_commands(
            [BotCommand(c, d) for c, d in COMMANDS["ru"]], language_code="ru"
        )
        logger.info("Команды бота зарегистрированы (ru/en).")
    except Exception as e:
        logger.error(f"Не удалось задать команды: {e}")
    # Синяя кнопка «Меню» открывает мини-аппу «домашний экран» в стиле сайта.
    try:
        await app.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="JazzTone", web_app=WebAppInfo(HOME_URL))
        )
        logger.info("Menu Button → мини-аппа JazzTone.")
    except Exception as e:
        logger.error(f"Не удалось задать Menu Button: {e}")


def main():
    if not TOKEN:
        raise SystemExit(
            "❌ Переменная окружения TOKEN не задана. Укажи её в /etc/trumpetbot.env"
        )
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    billing.init()  # таблицы биллинга (безопасно и при BILLING_ENABLED=False)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("home", home))
    app.add_handler(CommandHandler("random", random_note))
    app.add_handler(CommandHandler("metronome", metronome_command))
    app.add_handler(CommandHandler("feedback", feedback))
    app.add_handler(CommandHandler("credits", credits))
    app.add_handler(CommandHandler("buy", buy_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    # Telegram Stars: подтверждение перед оплатой + успешный платёж.
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, on_successful_payment))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🎺 Бот запущен и готов к работе!")
    app.run_polling()


if __name__ == "__main__":
    main()
