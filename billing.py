"""MVP-биллинг JazzTone: бесплатный месячный лимит на дорогой AI-разбор + расходуемые
Stars-кредиты. Отдельная SQLite (billing.db), не трогает mynotes/user_notes.db.

Монетизируем ТОЛЬКО дорогой сервис (анализ игры). Тюнер/метроном/библиотека/базовый
вердикт — бесплатны всегда (см. вывод council). Платёж — Telegram Stars (XTR).

Идемпотентность платежей — по telegram_payment_charge_id (повторный успех не дублирует
кредиты). Включается флагом BILLING_ENABLED в bot.py; сам модуль безопасен и без него.
"""

import sqlite3
import datetime
import os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "billing.db")

# --- Параметры модели (council: низкие цены, школьная аудитория, потолок на дорогой AI) ---
FREE_PER_MONTH = 3  # бесплатных глубоких разборов в календарный месяц на юзера

# Паки кредитов: payload -> (кол-во кредитов, цена в Stars). Якорь «чашка кофе».
PACKS = {
    "analysis_5": (5, 60),
    "analysis_15": (15, 150),
}

# --- Hit Study Pack (разовый учебный пакет по пьесе) ---
HSP_PRICE = 199  # один пакет (пьеса × инструмент)
HSP_BUNDLE_QTY = 5  # бандл: 5 пакетов на любые пьесы
HSP_BUNDLE_PRICE = 799
HSP_PRO_PRICE = 99  # Pro-апсейл: персональный AI-разбор (позже)

# payload одного пакета: 'hsp|<slug>|<instr>'; бандла: 'hspbundle'


def is_hsp_payload(payload):
    return bool(payload) and (payload.startswith("hsp|") or payload == "hspbundle")


def parse_hsp_payload(payload):
    """'hsp|slug|instr' -> ('single', slug, instr); 'hspbundle' -> ('bundle', None, None)."""
    if payload == "hspbundle":
        return ("bundle", None, None)
    parts = payload.split("|")
    if len(parts) == 3 and parts[0] == "hsp":
        return ("single", parts[1], parts[2])
    return (None, None, None)


def _conn():
    c = sqlite3.connect(DB)
    c.execute("PRAGMA journal_mode=WAL")
    return c


def init():
    with _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS usage ("
            "user_id INTEGER, month TEXT, free_used INTEGER DEFAULT 0,"
            "PRIMARY KEY (user_id, month))"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS credits ("
            "user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS payments ("
            "charge_id TEXT PRIMARY KEY, user_id INTEGER, stars INTEGER,"
            "credits INTEGER, created TEXT)"
        )


def _month():
    return datetime.date.today().strftime("%Y-%m")


def _free_used(c, user_id):
    row = c.execute(
        "SELECT free_used FROM usage WHERE user_id=? AND month=?", (user_id, _month())
    ).fetchone()
    return row[0] if row else 0


def _balance(c, user_id):
    row = c.execute(
        "SELECT balance FROM credits WHERE user_id=?", (user_id,)
    ).fetchone()
    return row[0] if row else 0


def status(user_id):
    """(сколько бесплатных осталось в этом месяце, баланс платных кредитов)."""
    with _conn() as c:
        return max(0, FREE_PER_MONTH - _free_used(c, user_id)), _balance(c, user_id)


def can_analyze(user_id):
    free_left, bal = status(user_id)
    return free_left > 0 or bal > 0


def consume(user_id):
    """Списать один разбор: сначала бесплатный лимит, потом платный кредит.
    Возвращает True если списано (т.е. разбор разрешён), False если нечего списать."""
    with _conn() as c:
        m = _month()
        if _free_used(c, user_id) < FREE_PER_MONTH:
            c.execute(
                "INSERT INTO usage(user_id, month, free_used) VALUES(?,?,1) "
                "ON CONFLICT(user_id, month) DO UPDATE SET free_used=free_used+1",
                (user_id, m),
            )
            return True
        if _balance(c, user_id) > 0:
            c.execute(
                "UPDATE credits SET balance=balance-1 WHERE user_id=?", (user_id,)
            )
            return True
        return False


def add_credits(user_id, n):
    with _conn() as c:
        c.execute(
            "INSERT INTO credits(user_id, balance) VALUES(?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET balance=balance+?",
            (user_id, n, n),
        )


def record_payment(charge_id, user_id, stars, credits):
    """Идемпотентно зафиксировать платёж и начислить кредиты.
    Возвращает True если это НОВЫЙ платёж (кредиты начислены), False если повтор."""
    with _conn() as c:
        exists = c.execute(
            "SELECT 1 FROM payments WHERE charge_id=?", (charge_id,)
        ).fetchone()
        if exists:
            return False
        c.execute(
            "INSERT INTO payments(charge_id, user_id, stars, credits, created) "
            "VALUES(?,?,?,?,?)",
            (
                charge_id,
                user_id,
                stars,
                credits,
                datetime.datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
    add_credits(user_id, credits)
    return True
