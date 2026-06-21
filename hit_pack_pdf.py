"""
PDF-бандл Hit Study Pack.

Страницы:
  1. Обложка (название, инструмент, состав пакета, легал-строка).
  2. Аккордовая СЕТКА — slash-нотация (verovio→cairosvg). Это «ноты» пакета.
  3. Гайд-тоны (3/7 по аккордам) — таблица.
  4+ Разбор от Claude (гарм. анализ, chord-scale, лики, targeting, план, чек-лист).

Текст рисуется через PIL (reportlab/weasyprint на сервере нет), нотная страница —
через ту же связку verovio→cairosvg, что у библиотечных PDF. Сборка многостраничного
PDF — средствами PIL (Image.save save_all).
"""

import io
import os
import re

from PIL import Image, ImageDraw, ImageFont

import hit_study_pack as hsp

# ---------- геометрия / стиль ----------
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
PAGE_W, PAGE_H = 1240, 1754  # A4 @ ~150 dpi
MX, MY = 100, 110  # поля
INK = (26, 26, 26)
MUTE = (122, 122, 130)
ACCENT = (43, 49, 120)
RULE = (223, 223, 228)
SLASH_BG = (250, 250, 252)


def _f(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def _fonts():
    return {
        "title": _f("DejaVuSans-Bold.ttf", 58),
        "h1": _f("DejaVuSans-Bold.ttf", 40),
        "h2": _f("DejaVuSans-Bold.ttf", 30),
        "body": _f("DejaVuSans.ttf", 25),
        "bold": _f("DejaVuSans-Bold.ttf", 25),
        "italic": _f("DejaVuSerif.ttf", 24),
        "mono": _f("DejaVuSansMono.ttf", 25),
        "monobold": _f("DejaVuSansMono-Bold.ttf", 25),
        "small": _f("DejaVuSans.ttf", 20),
        "mute": _f("DejaVuSerif.ttf", 21),
    }


def _pretty(sym):
    """Имя ноты из music21 ('-'/'#') → красивый '♭'/'♯'. Только для нот, не прозы!"""
    return sym.replace("-", "♭").replace("#", "♯") if sym else sym


def _pretty_chord(sym):
    """Аккорд-символ из каталога ('Bb7','Em7b5','F#m7') → '♭'/'♯'. 'b'=флэт всегда."""
    return sym.replace("b", "♭").replace("#", "♯").replace("-", "♭") if sym else sym


# ---------- многостраничный холст с авто-переносом ----------
class Canvas:
    def __init__(self):
        self.F = _fonts()
        self.pages = []
        self.img = None
        self.d = None
        self.y = 0
        self._new_page()

    def _new_page(self):
        self.img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        self.d = ImageDraw.Draw(self.img)
        self.pages.append(self.img)
        self.y = MY

    def _ensure(self, h):
        if self.y + h > PAGE_H - MY:
            self._new_page()

    def gap(self, h=14):
        self.y += h

    def rule(self, color=RULE, pad=8):
        self.y += pad
        self.d.line([(MX, self.y), (PAGE_W - MX, self.y)], fill=color, width=2)
        self.y += pad

    def _wrap(self, runs, font_reg, font_bold, max_w):
        """runs=[(text,bold)] → строки [[(word,bold)...]] жадным переносом по словам."""
        lines, cur, w = [], [], 0
        space = self.d.textlength(" ", font=font_reg)
        for text, bold in runs:
            f = font_bold if bold else font_reg
            for word in text.split(" "):
                if word == "":
                    continue
                ww = self.d.textlength(word, font=f)
                if cur and w + space + ww > max_w:
                    lines.append(cur)
                    cur, w = [], 0
                cur.append((word, bold))
                w += (space if w else 0) + ww
        if cur:
            lines.append(cur)
        return lines or [[]]

    def para(self, text, indent=0, color=INK, lead=10, reg="body", bold="bold"):
        if "\n" in text:
            for ln in text.split("\n"):
                self.para(ln or " ", indent, color, lead, reg, bold)
            return
        fr, fb = self.F[reg], self.F[bold]
        line_h = fr.size + lead
        runs = _runs(text)
        max_w = PAGE_W - MX - MX - indent
        space = self.d.textlength(" ", font=fr)
        for line in self._wrap(runs, fr, fb, max_w):
            self._ensure(line_h)
            x = MX + indent
            for word, b in line:
                f = fb if b else fr
                self.d.text((x, self.y), word, font=f, fill=color)
                x += self.d.textlength(word, font=f) + space
            self.y += line_h

    def bullet(self, text):
        fr = self.F["body"]
        line_h = fr.size + 10
        self._ensure(line_h)
        self.d.ellipse(
            [MX + 8, self.y + fr.size // 2 - 3, MX + 16, self.y + fr.size // 2 + 5],
            fill=ACCENT,
        )
        self.para(text, indent=40)

    def h1(self, text, color=ACCENT):
        self.gap(8)
        self._ensure(self.F["h1"].size + 24)
        self.d.text((MX, self.y), text, font=self.F["h1"], fill=color)
        self.y += self.F["h1"].size + 10
        self.rule(color=ACCENT, pad=4)
        self.gap(8)

    def h2(self, text, color=INK):
        self.gap(14)
        self._ensure(self.F["h2"].size + 14)
        self.d.text((MX, self.y), text, font=self.F["h2"], fill=color)
        self.y += self.F["h2"].size + 6
        self.gap(4)

    def paste_image(self, png_bytes):
        """Вклеить PNG (нотная страница) во весь блок ширины, новую страницу."""
        im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        avail_w = PAGE_W - 2 * MX
        scale = min(avail_w / im.width, 1.6)
        nw, nh = int(im.width * scale), int(im.height * scale)
        im = im.resize((nw, nh), Image.LANCZOS)
        # на отдельной странице (или нескольких, если высокая)
        self._new_page()
        if nh <= PAGE_H - 2 * MY:
            self.img.paste(im, ((PAGE_W - nw) // 2, self.y))
            self.y += nh
        else:
            # разрезать по высоте на страницы
            top = 0
            while top < nh:
                if top > 0:
                    self._new_page()
                chunk = min(PAGE_H - 2 * MY, nh - top)
                crop = im.crop((0, top, nw, top + chunk))
                self.img.paste(crop, ((PAGE_W - nw) // 2, self.y))
                self.y += chunk
                top += chunk

    def to_pdf(self):
        buf = io.BytesIO()
        self.pages[0].save(
            buf,
            format="PDF",
            save_all=True,
            append_images=self.pages[1:],
            resolution=150.0,
        )
        return buf.getvalue()


def _runs(text):
    parts = re.split(r"(\*\*.+?\*\*)", text)
    out = []
    for p in parts:
        if len(p) >= 4 and p.startswith("**") and p.endswith("**"):
            out.append((p[2:-2], True))
        elif p:
            out.append((p, False))
    return out or [("", False)]


# ---------- markdown-разделы Claude → страницы ----------
def _render_markdown(cv, md):
    in_code = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            cv.para(
                line or " ", reg="mono", bold="monobold", indent=20, color=(60, 60, 70)
            )
            continue
        s = line.strip()
        # ВАЖНО: прозу НЕ прогоняем через _pretty — он бы съел дефисы
        # ('ii-V-I', 'chord-scale', '12-тактовый'). Claude уже пишет ноты как нужно.
        if not s:
            cv.gap(10)
        elif set(s) <= {"-", "*", "_", " "} and len(s) >= 3:
            cv.rule()  # горизонтальная линия (--- / ***)
        elif s.startswith("## "):
            cv.h2(s[3:])
        elif s.startswith("# "):
            cv.h2(s[2:])
        elif s.startswith("### "):
            cv.para(s[4:], bold="bold", reg="bold", color=ACCENT)
        elif s.startswith(">"):
            cv.para(
                s.lstrip("> ").strip() or " ",
                indent=24,
                color=MUTE,
                reg="mute",
                bold="italic",
            )
        elif s[:2] in ("- ", "* "):
            cv.bullet(s[2:])
        elif re.match(r"^\d+\.\s", s):
            cv.para(s, indent=24)
        else:
            cv.para(s)


# ---------- MusicXML: slash-нотация сетки ----------
_KEY_FIFTHS = {
    "C": 0,
    "G": 1,
    "D": 2,
    "A": 3,
    "E": 4,
    "B": 5,
    "F#": 6,
    "F": -1,
    "Bb": -2,
    "Eb": -3,
    "Ab": -4,
    "Db": -5,
    "Gb": -6,
}


def _suffix(sym):
    """Аккорд-суффикс (после корня) для подписи: 'Bbmaj7' → 'maj7'."""
    return re.sub(r"^[A-G][#b]?", "", sym.strip())


def _xml_esc(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def changes_to_musicxml(tune, beats_per_bar=4):
    """Сетка → MusicXML slash-лист (chord-символы + ритм-слэши, без мелодии)."""
    fifths = _KEY_FIFTHS.get(tune.get("key", "C"), 0)
    title = _xml_esc(tune.get("title", ""))
    composer = _xml_esc(tune.get("composer", ""))
    bars = tune["changes"]

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" '
        '"http://www.musicxml.org/dtds/partwise.dtd">',
        '<score-partwise version="3.1">',
        f"<work><work-title>{title}</work-title></work>",
        f'<identification><creator type="composer">{composer}</creator></identification>',
        '<part-list><score-part id="P1"><part-name>Chart</part-name></score-part></part-list>',
        '<part id="P1">',
    ]

    for i, bar in enumerate(bars, 1):
        m = [f'<measure number="{i}">']
        if i == 1:
            m.append(
                "<attributes><divisions>1</divisions>"
                f"<key><fifths>{fifths}</fifths></key>"
                "<time><beats>4</beats><beat-type>4</beat-type></time>"
                "<clef><sign>G</sign><line>2</line></clef></attributes>"
            )
        if i > 1 and (i - 1) % 4 == 0:
            m.append('<print new-system="yes"/>')
        cells = bar if bar else ["%"]
        n = len(cells)
        # доли на каждый аккорд (целочисленно, остаток последнему)
        each = [beats_per_bar // n] * n
        each[-1] += beats_per_bar - sum(each)
        prev = None
        for ch, beats in zip(cells, each):
            sym = ch if ch not in ("%", "/") else prev
            if sym:
                prev = sym
                try:
                    cs = hsp.chord_symbol(sym)
                    root = cs.root()
                    kind = getattr(cs, "chordKind", None) or "major"
                except Exception:
                    root, kind = None, None
                if root is not None:
                    alter = int(root.alter)
                    ra = f"<root-alter>{alter}</root-alter>" if alter else ""
                    m.append(
                        "<harmony><root>"
                        f"<root-step>{root.step}</root-step>{ra}</root>"
                        f'<kind text="{_xml_esc(_suffix(sym))}">{kind}</kind></harmony>'
                    )
            for _ in range(beats):
                m.append(
                    "<note><pitch><step>B</step><octave>4</octave></pitch>"
                    "<duration>1</duration><type>quarter</type>"
                    "<stem>none</stem><notehead>slash</notehead></note>"
                )
        m.append("</measure>")
        parts.append("".join(m))

    parts.append("</part></score-partwise>")
    return "\n".join(parts)


# SMuFL csym-аккцидентали (Leipzig) → Unicode. cairosvg не знает Leipzig →
# флэт/диез в аккордах выходили пустым квадратом. Меняем на ♭/♯ в DejaVu Sans.


_SMUFL_ACC = {
    "\uea64": "\u266d",  # csymAccidentalFlat  -> flat
    "\ue260": "\u266d",  # accidentalFlat      -> flat
    "\uea66": "\u266f",  # csymAccidentalSharp -> sharp
    "\ue262": "\u266f",  # accidentalSharp     -> sharp
    "\uea65": "\u266e",  # csymAccidentalNatural -> natural
    "\ue261": "\u266e",  # accidentalNatural   -> natural
}


def _fix_chord_accidentals(svg):
    def repl(m):
        glyph = m.group("g")
        uni = _SMUFL_ACC.get(glyph)
        if not uni:
            return m.group(0)
        try:
            sz = int(round(float(re.findall(r"[\d.]+", m.group("sz"))[0]) * 0.6))
        except Exception:
            sz = 420
        return f'<tspan font-family="DejaVu Sans" font-size="{sz}px">{uni}</tspan>'

    return re.sub(
        r'<tspan font-family="Leipzig" font-size="(?P<sz>[^"]+)">(?P<g>.)</tspan>',
        repl,
        svg,
    )


def _render_chart_png(tune, scale=42):
    """Нотная сетка → PNG bytes (LilyPond; fallback verovio+cairosvg)."""
    try:
        import lily_render
        _b = lily_render.render(changes_to_musicxml(tune), "png", scale, hide_accidentals=True)
        if _b:
            return _b
    except Exception:
        pass
    try:
        import verovio
        import cairosvg
    except Exception:
        return None
    try:
        xml = changes_to_musicxml(tune)
        tk = verovio.toolkit()
        tk.setOptions(
            {
                "pageWidth": 2100,
                "pageHeight": 2970,
                "scale": scale,
                "adjustPageHeight": True,
                "header": "none",
                "footer": "none",
                "pageMarginTop": 80,
                "pageMarginLeft": 60,
                "pageMarginRight": 60,
            }
        )
        if not tk.loadData(xml):
            return None
        svg = _fix_chord_accidentals(tk.renderToSVG(1))
        return cairosvg.svg2png(
            bytestring=svg.encode("utf-8"), background_color="white"
        )
    except Exception:
        return None


# ---------- сборка ----------
PACK_CONTENTS = [
    "Аккордовая сетка пьесы (slash-лист)",
    "Гармонический разбор по функциям",
    "Гайд-тоны (3/7) для голосоведения",
    "Chord-scale карта (какие гаммы над чем)",
    "5 оригинальных ликов над ключевыми ii–V–I",
    "Targeting-упражнения на аккордовые тоны",
    "План освоения на неделю + чек-лист",
    "Минусовка (3 хоруса) — отдельным файлом",
]


def _cover(cv, tune, instrument_label):
    cv.gap(40)
    cv.d.text((MX, cv.y), "HIT STUDY PACK", font=cv.F["small"], fill=ACCENT)
    cv.y += 50
    cv.d.text((MX, cv.y), _pretty(tune["title"]), font=cv.F["title"], fill=INK)
    cv.y += cv.F["title"].size + 16
    cv.d.text(
        (MX, cv.y),
        f"{tune.get('composer', '')}  ·  {tune.get('style', '')}",
        font=cv.F["italic"],
        fill=MUTE,
    )
    cv.y += 44
    cv.d.text(
        (MX, cv.y),
        f"Инструмент: {instrument_label}   ·   Тональность: {_pretty_chord(tune.get('key', ''))}"
        f"   ·   Форма: {tune.get('form', '')}",
        font=cv.F["small"],
        fill=INK,
    )
    cv.y += 40
    cv.rule()
    cv.gap(18)
    cv.h2("Что внутри")
    for item in PACK_CONTENTS:
        cv.bullet(item)
    cv.gap(30)
    cv.rule()
    cv.gap(10)
    cv.para(
        "Учебный материал построен на **аккордовой сетке** пьесы (гармоническая "
        "последовательность не охраняется авторским правом). Оригинальная мелодия "
        "не цитируется и не нотируется. Все примеры — оригинальные.",
        color=MUTE,
        reg="mute",
        bold="italic",
    )


def _guide_tone_page(cv, tune):
    cv.h1("Гайд-тоны (3 / 7)")
    cv.para(
        "Скелет голосоведения: 3-я и 7-я ступени каждого аккорда. Веди их плавно — "
        "это «правильные ноты», на которые садится соло.",
        color=MUTE,
        reg="mute",
        bold="italic",
    )
    cv.gap(12)
    gts = hsp.guide_tones(tune["changes"])
    fb, fm = cv.F["bold"], cv.F["mono"]
    col = [MX, MX + 110, MX + 360, MX + 560]
    cv._ensure(40)
    for x, head in zip(col, ["Такт", "Аккорд", "3-я", "7-я"]):
        cv.d.text((x, cv.y), head, font=cv.F["small"], fill=ACCENT)
    cv.y += 34
    cv.rule()
    for g in gts:
        cv._ensure(36)
        cv.d.text((col[0], cv.y), str(g["bar"]), font=fm, fill=MUTE)
        cv.d.text((col[1], cv.y), _pretty_chord(g["chord"]), font=fb, fill=INK)
        cv.d.text((col[2], cv.y), _pretty(g["third"] or "—"), font=fm, fill=INK)
        cv.d.text((col[3], cv.y), _pretty(g["seventh"] or "—"), font=fm, fill=INK)
        cv.y += 36


def build_pack_pdf(
    tune,
    instrument="trumpet",
    instrument_label="Труба",
    level="medium",
    lang="ru",
    sections=None,
):
    """Полный PDF-бандл (bytes). sections — markdown от Claude (или None → без разбора)."""
    cv = Canvas()
    _cover(cv, tune, instrument_label)

    chart_png = _render_chart_png(tune)
    if chart_png:
        cv.paste_image(chart_png)
        cv._new_page()
    cv.h1("Аккордовая сетка (текст)")
    cv.para(
        _pretty_chord(hsp.changes_to_chart(tune["changes"])),
        reg="mono",
        bold="monobold",
    )

    cv._new_page()
    _guide_tone_page(cv, tune)

    if sections:
        cv._new_page()
        _render_markdown(cv, sections)
    else:
        cv._new_page()
        cv.h1("Разбор")
        cv.para(
            "Текстовый разбор (гармония, chord-scale, лики, targeting, план недели) "
            "генерируется отдельно. Базовый пакет — сетка + гайд-тоны + минусовка.",
            color=MUTE,
            reg="mute",
            bold="italic",
        )

    return cv.to_pdf()
