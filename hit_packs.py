"""
Хранилище покупок Hit Study Pack (за Telegram Stars).

Отдельная SQLite (hit_packs.db) — не трогает billing.db / mynotes.
Покупка = entitlement на (пьеса × инструмент): юзер владеет пакетом навсегда,
может пере-скачать в «Мои паки». Готовые файлы (PDF + минусовка) кешируются на
диск, чтобы повторная выдача была мгновенной (не гонять Claude/рендер заново).

bundle-5 → pack_credits: 5 «жетонов» на любые 5 пьес.
Идемпотентность платежей — по telegram_payment_charge_id.
"""

import os
import sqlite3
import time

DB = os.environ.get(
    "HITPACKS_DB",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "hit_packs.db"),
)
FILES_DIR = os.environ.get(
    "HITPACKS_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "hit_packs_files"),
)


def _conn():
    c = sqlite3.connect(DB)
    c.execute("PRAGMA journal_mode=WAL")
    return c


def init():
    with _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS entitlements ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, tune TEXT,"
            "instrument TEXT, title TEXT, charge_id TEXT,"
            "pdf_path TEXT, minus_path TEXT, created TEXT,"
            "UNIQUE(user_id, tune, instrument))"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS pack_credits ("
            "user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS hsp_payments ("
            "charge_id TEXT PRIMARY KEY, user_id INTEGER, stars INTEGER, created TEXT)"
        )


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def owns(user_id, tune, instrument):
    """Entitlement-row (id,user_id,tune,instrument,title,charge_id,pdf,minus,created) или None."""
    with _conn() as c:
        return c.execute(
            "SELECT id,user_id,tune,instrument,title,charge_id,pdf_path,minus_path,created "
            "FROM entitlements WHERE user_id=? AND tune=? AND instrument=?",
            (user_id, tune, instrument),
        ).fetchone()


def owns_any(user_id, tune):
    """Владеет ли юзер пакетом по пьесе хотя бы в одном инструменте (минус
    инструмент-независим — общий для всех версий пакета)."""
    with _conn() as c:
        return (
            c.execute(
                "SELECT 1 FROM entitlements WHERE user_id=? AND tune=? LIMIT 1",
                (user_id, tune),
            ).fetchone()
            is not None
        )


def grant(user_id, tune, instrument, title, charge_id=None):
    """Выдать (или вернуть существующий) entitlement. Возвращает id."""
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO entitlements"
            "(user_id,tune,instrument,title,charge_id,created) VALUES(?,?,?,?,?,?)",
            (user_id, tune, instrument, title, charge_id, _now()),
        )
        row = c.execute(
            "SELECT id FROM entitlements WHERE user_id=? AND tune=? AND instrument=?",
            (user_id, tune, instrument),
        ).fetchone()
        return row[0]


def set_files(ent_id, pdf_path, minus_path):
    with _conn() as c:
        c.execute(
            "UPDATE entitlements SET pdf_path=?, minus_path=? WHERE id=?",
            (pdf_path, minus_path, ent_id),
        )


def list_for(user_id, limit=30):
    with _conn() as c:
        return c.execute(
            "SELECT id,tune,instrument,title FROM entitlements WHERE user_id=? "
            "ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()


def get(user_id, ent_id):
    with _conn() as c:
        return c.execute(
            "SELECT id,user_id,tune,instrument,title,charge_id,pdf_path,minus_path,created "
            "FROM entitlements WHERE user_id=? AND id=?",
            (user_id, ent_id),
        ).fetchone()


# ---- bundle pack-credits ----
def credits(user_id):
    with _conn() as c:
        row = c.execute(
            "SELECT balance FROM pack_credits WHERE user_id=?", (user_id,)
        ).fetchone()
        return row[0] if row else 0


def add_credits(user_id, n):
    with _conn() as c:
        c.execute(
            "INSERT INTO pack_credits(user_id,balance) VALUES(?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET balance=balance+?",
            (user_id, n, n),
        )


def spend_credit(user_id):
    """Списать один pack-credit. True если списано."""
    with _conn() as c:
        row = c.execute(
            "SELECT balance FROM pack_credits WHERE user_id=?", (user_id,)
        ).fetchone()
        if not row or row[0] <= 0:
            return False
        c.execute(
            "UPDATE pack_credits SET balance=balance-1 WHERE user_id=?", (user_id,)
        )
        return True


def record_payment(charge_id, user_id, stars):
    """Идемпотентно зафиксировать платёж. True если НОВЫЙ (можно выдавать товар)."""
    with _conn() as c:
        if c.execute(
            "SELECT 1 FROM hsp_payments WHERE charge_id=?", (charge_id,)
        ).fetchone():
            return False
        c.execute(
            "INSERT INTO hsp_payments(charge_id,user_id,stars,created) VALUES(?,?,?,?)",
            (charge_id, user_id, stars, _now()),
        )
    return True


def files_dir(user_id):
    d = os.path.join(FILES_DIR, str(user_id))
    os.makedirs(d, exist_ok=True)
    return d
