"""MusicXML → PNG/PDF через LilyPond (переход с verovio).

Путь: MusicXML --(musicxml2ly)--> .ly --(lilypond)--> PNG/PDF (bytes).
Если lilypond/musicxml2ly не установлены или рендер не удался — возвращает None,
и вызывающий код (transcribe.render_png/pdf) откатывается на verovio.
"""

import os
import re
import shutil
import subprocess
import tempfile

_MUSICXML2LY = shutil.which("musicxml2ly")
_LILYPOND = shutil.which("lilypond")


def available() -> bool:
    return bool(_MUSICXML2LY and _LILYPOND)


def _tidy_ly(ly_text: str, scale: int, hide_accidentals: bool = False) -> str:
    """Чистка вывода musicxml2ly: убрать tagline, размер стана, починить аккорды.
    scale у verovio был ~40 (дефолт). Маппим в staff-size: 40 -> 20 (дефолт LilyPond)."""
    # musicxml2ly мажорное трезвучие <kind>major</kind> пишет как "c4:5" → LilyPond
    # рисует "C⁵" (power-chord). Нам нужен чистый "C": срезаем артефакт :5 у трезвучий.
    ly_text = re.sub(r":5(?=[\s|}])", "", ly_text)
    staff_size = max(12, min(26, round(scale / 2)))
    inject = f"\n\\paper {{ tagline = ##f }}\n#(set-global-staff-size {staff_size})\n"
    if hide_accidentals:
        # slash-сетка аккордов: slash-ноты сидят на B, и в бемольных тональностях
        # LilyPond рисует лишний ♮ на каждой доле. Гасим знаки во всём стане
        # (в сетке нет реальных высот — терять нечего; верно повторяет verovio).
        inject += "\\layout { \\context { \\Staff \\omit Accidental } }\n"
    # вставляем сразу после строки \version "..."
    m = re.search(r'\\version\s+"[^"]+"\s*\n', ly_text)
    if m:
        return ly_text[: m.end()] + inject + ly_text[m.end() :]
    return '\\version "2.24.0"\n' + inject + ly_text


def render(
    musicxml: str,
    fmt: str = "png",
    scale: int = 40,
    resolution: int = 200,
    hide_accidentals: bool = False,
):
    """MusicXML-строка → bytes (PNG или PDF) либо None.
    hide_accidentals=True — для slash-сеток аккордов (без реальных высот)."""
    if not available() or fmt not in ("png", "pdf"):
        return None
    tmp = tempfile.mkdtemp(prefix="lily_")
    try:
        xml_path = os.path.join(tmp, "score.xml")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(musicxml)

        ly_path = os.path.join(tmp, "score.ly")
        subprocess.run(
            [_MUSICXML2LY, "-o", ly_path, xml_path],
            capture_output=True,
            timeout=90,
            cwd=tmp,
        )
        if not os.path.exists(ly_path):
            return None

        with open(ly_path, "r", encoding="utf-8") as f:
            ly_text = f.read()
        with open(ly_path, "w", encoding="utf-8") as f:
            f.write(_tidy_ly(ly_text, scale, hide_accidentals))

        out_base = os.path.join(tmp, "out")
        # -dcrop обрезает страницу по нотному контенту (даёт out.cropped.png/pdf),
        # заменяя verovio adjustPageHeight — иначе вокруг нот пустая A4.
        cmd = [_LILYPOND, "-dno-point-and-click", "-dcrop", "-s", "-o", out_base]
        if fmt == "png":
            cmd += ["--png", f"-dresolution={resolution}"]
        else:
            cmd += ["--pdf"]
        cmd.append(ly_path)
        subprocess.run(cmd, capture_output=True, timeout=180, cwd=tmp)

        # предпочитаем обрезанный файл; затем обычный; затем многостраничный
        for cand in (
            out_base + ".cropped." + fmt,
            out_base + "." + fmt,
            out_base + "-page1." + fmt,
        ):
            if os.path.exists(cand):
                with open(cand, "rb") as f:
                    return f.read()
        return None
    except Exception:
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
