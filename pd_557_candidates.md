# PD-подмножество из «557 Jazz Standards» — рабочий список

**Юридическая рамка.** Сборник 557 Jazz Standards — копирайтный фейкбук; используем его
ТОЛЬКО как список названий (названия не охраняются). Берём в библиотеку лишь произведения,
**музыку** которых написал композитор, умерший достаточно давно, чтобы вещь была в public
domain по немецкому праву (сервер в Германии, **life + 70**). На 2026 г. это композиторы,
умершие **в 1955 г. или раньше** (произведение становится PD 1 января года смерти + 71).

**Что именно льём.** Не страницу фейкбука, а **свой чистый engraving мелодии** (lead/тема)
из легального источника (наш MusicXML, IMSLP/CC0). Партии под инструменты — **транспозиционным
генератором** (`transcribe.render_musicxml` + таблица `INSTRUMENTS`), один источник → N версий.

**Про соавторов/текст.** Для инструментальной партии воспроизводится только МУЗЫКА. Если
музыку написал PD-композитор, а текст — ещё живой/недавний автор (напр. Ira Gershwin †1983,
Hammerstein †1960), это не мешает: текст мы не печатаем. Важна дата смерти **композитора музыки**.

**Исключения (НЕ брать, не PD в Германии):** W.C. Handy †1958 (St. Louis/Memphis Blues —
PD только в США, у нас до 2029), Hoagy Carmichael †1981 (Stardust), Ellington †1974,
Cole Porter †1964, Rodgers †1979, Arlen †1986, Spencer Williams †1965, Turner Layton †1978.

**Антидрейф.** В библиотеке уже 15 рэгтаймов Joplin — рэгтайм больше НЕ добавляем. Этот
список намеренно смещён в сторону настоящих джазовых стандартов под трубу.

---

## Ядро (атрибуция и год смерти надёжны) — приоритет на сорсинг

### George Gershwin †1937 — PD в Германии с 2008
- Summertime
- I Got Rhythm *(rhythm changes — отличная база для бибоп-практики на трубе)*
- But Not for Me
- Embraceable You
- Oh, Lady Be Good
- Someone to Watch Over Me
- A Foggy Day
- Nice Work If You Can Get It
- 'S Wonderful
- They Can't Take That Away from Me
- Love Is Here to Stay *(издана посмертно 1938, но музыка Дж. Гершвина → срок по нему)*

### Jerome Kern †1945 — PD с 2016
- All the Things You Are
- The Way You Look Tonight
- Smoke Gets in Your Eyes
- Yesterdays
- A Fine Romance
- The Song Is You
- Pick Yourself Up
- Long Ago and Far Away

### Fats Waller †1943 — PD с 2014
- Ain't Misbehavin'
- Honeysuckle Rose
- Jitterbug Waltz
- Black and Blue

### Jelly Roll Morton †1941 — PD с 2012  *(уже есть Dead Man Blues + книга Blues and Stomps)*
- King Porter Stomp
- Wolverine Blues
- Black Bottom Stomp

### James P. Johnson †1955 — PD только что (с 1 января 2026)
- Charleston
- If I Could Be with You (One Hour Tonight) *(соавтор Henry Creamer †1930 — тоже PD)*

### Bix Beiderbecke †1931 — PD с 2002
- In a Mist *(фортепианная, но историчная; для трубы — опционально)*

---

## ⚠️ Проверить перед включением (Правило №1 — не выдавать за факт)
Уточнить дату смерти КОМПОЗИТОРА МУЗЫКИ (а не исполнителя) и год до коммита:
- After You've Gone — муз. Turner Layton †1978 → **скорее НЕ PD**, перепроверить.
- If Dreams Come True / ранний свинг 1930-х — частые соавторы, проверять каждого.
- Любая вещь, где на обложке стоит только исполнитель/аранжировщик — найти автора темы.

---

## Конвейер на каждую отобранную вещь (следующий шаг)
1. Найти/набрать ЧИСТЫЙ источник мелодии (MusicXML/MIDI), не страницу фейкбука.
2. `transcribe.render_musicxml(notes, offset=INSTRUMENTS[instr][1], title=...)` → партия под
   каждый инструмент репертуара (труба B♭ +2, тенор +14, альт +9, кларнет +2, к-бас/гитара
   −окт., тромбон/ф-но concert 0). PNG/PDF — `render_png`.
3. Добавить в `notes.json` новой схемой: `work + key_concert + style + versions[]`
   (см. helpers `versions_of`/`version_for`/`notes_for_instrument` в bot.py).
4. id/file_path существующих 82 записей НЕ трогать (file_id-кэш Telegram).
