"""
«Мои ноты» — персональные транскрипции пользователя.
SQLite (метаданные) + файлы user_notes/<user_id>/<id>.{mid,musicxml}.
ОТДЕЛЬНО от публичной библиотеки (notes.json) — личная генерация ≠ публикация.
"""
import os
import sqlite3
import time

DB_PATH = os.environ.get("MYNOTES_DB", "user_notes.db")
FILES_DIR = os.environ.get("MYNOTES_DIR", "user_notes")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("""CREATE TABLE IF NOT EXISTS user_notes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        instrument TEXT,
        confidence INTEGER,
        n_notes INTEGER,
        midi_path TEXT,
        xml_path TEXT,
        created INTEGER)""")
    return c


def add(user_id, title, instrument, confidence, n_notes, midi_bytes, xml_text):
    c = _conn()
    cur = c.execute(
        "INSERT INTO user_notes(user_id,title,instrument,confidence,n_notes,created) "
        "VALUES(?,?,?,?,?,?)",
        (user_id, title, instrument, confidence, n_notes, int(time.time())),
    )
    nid = cur.lastrowid
    udir = os.path.join(FILES_DIR, str(user_id))
    os.makedirs(udir, exist_ok=True)
    midi_path = os.path.join(udir, f"{nid}.mid")
    xml_path = os.path.join(udir, f"{nid}.musicxml")
    with open(midi_path, "wb") as f:
        f.write(midi_bytes)
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_text)
    c.execute("UPDATE user_notes SET midi_path=?, xml_path=? WHERE id=?",
              (midi_path, xml_path, nid))
    c.commit()
    c.close()
    return nid


def list_for(user_id, limit=20):
    c = _conn()
    rows = c.execute(
        "SELECT id,title,instrument,confidence,n_notes,created FROM user_notes "
        "WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
    c.close()
    return rows


def get(user_id, nid):
    c = _conn()
    row = c.execute(
        "SELECT id,title,instrument,confidence,n_notes,midi_path,xml_path FROM user_notes "
        "WHERE user_id=? AND id=?", (user_id, nid)).fetchone()
    c.close()
    return row


def delete(user_id, nid):
    row = get(user_id, nid)
    if not row:
        return False
    for p in (row[5], row[6]):
        try:
            os.remove(p)
        except OSError:
            pass
    c = _conn()
    c.execute("DELETE FROM user_notes WHERE user_id=? AND id=?", (user_id, nid))
    c.commit()
    c.close()
    return True
