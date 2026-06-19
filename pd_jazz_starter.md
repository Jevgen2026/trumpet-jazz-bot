# PD-стартовый список джаз-репертуара для JazzTone

**Рамка PD:** сервер в Германии → **life + 70** → произведение public domain, если ВСЕ его композиторы (музыки) умерли **≤ 1955** (PD с 01.01.2026).
**Печатаем только МУЗЫКУ** (мелодию/тему). Тексты (lyrics) живущих поэтов — не печатаем, они нам и не нужны.
**Фильтр со-авторов:** если хоть один со-композитор МУЗЫКИ умер после 1955 — вещь НЕ PD (исключена ниже).
**Метод добавления:** НЕ нарезаем чужие издания. Берём ВЫВЕРЕННУЮ мелодию (MusicXML/MIDI/подтверждённые ноты) → `gen_parts.generate_work()` генерит свежую гравировку + партии под строй каждого инструмента. Композитор по автору ТЕМЫ (music-expert Правило №2).

## 🟢 ОСНОВНОЙ ИСТОЧНИК MusicXML — Public Domain Song Anthology
**Berger & Israels (UVA Aperio Press, 2020), 348 песен, открытый доступ.** PDF + **MusicXML** + Sibelius по каждой песне на UVA Dataverse: `doi:10.18130/V3/C4RD06`. Гармонизации (modern jazz + traditional) открыто лицензированы. **Это легальный конвейер выверенных MusicXML под `gen_parts`** — снимает блокер «нет источника мелодии».
> ⚠️ **US-PD ≠ German-PD.** Антология отобрана по **US public domain** (публикация до ~1925). Наш сервер в Германии = **life+70** → по КАЖДОЙ песне всё равно проверяем: умер ли композитор музыки ≤1955. US-PD-вещи с поздними авторами (Handy †1958, Berlin †1989, Sp.Williams †1965, Sh.Brooks †1975, LaRocca †1961, Schoebel †1970, T.Layton †1978 и др.) — в Германии ещё НЕ PD, не берём.
> Берём из антологии только записи, прошедшие German-фильтр (Hanley †1942, C.Smith †1949, Hickman †1930, V.Rose †1944, Fisher †1942, Silvers †1954, Donaldson †1947, Bowman †1949, Braham †1934, Joplin, Morton + все традиционные).
> LOC National Jukebox (pre-1923 аудио) — чисто для США; для немецкого сервера смежные права исполнителей в ЕС иные → аудио-референсы пока придерживаем, идём через ноты.

Легенда: ✅ чисто · ⚠️ нюанс (читать примечание) · 🎵 контрафакт (мелодия PD; см. блок Паркера).

---

## 1. George Gershwin †1937 — музыка PD (Ira Gershwin lyrics не печатаем)
Самое ядро джазовых стандартов, надёжнейшая атрибуция, единоличный автор музыки.

| Тема | Год | Стиль | Прим. |
|---|---|---|---|
| Summertime | 1935 | standard/ballad | ✅ из Porgy & Bess |
| I Got Rhythm | 1930 | standard (rhythm changes!) | ✅ база для контрафактов |
| Oh, Lady Be Good | 1924 | standard/swing | ✅ |
| Fascinating Rhythm | 1924 | swing | ✅ |
| Embraceable You | 1930 | ballad | ✅ |
| The Man I Love | 1924 | ballad | ✅ |
| But Not for Me | 1930 | standard | ✅ |
| A Foggy Day | 1937 | standard | ✅ |
| They Can't Take That Away From Me | 1937 | standard | ✅ |
| Someone to Watch Over Me | 1926 | ballad | ✅ |
| Nice Work If You Can Get It | 1937 | standard | ✅ |
| Love Is Here to Stay | 1938 | standard | ✅ посм. публикация, музыка Гершвина |
| 'S Wonderful | 1927 | standard | ✅ |

## 2. Jerome Kern †1945 — музыка PD
| Тема | Год | Стиль | Прим. |
|---|---|---|---|
| All the Things You Are | 1939 | standard | ✅ топ джем-стандарт |
| The Way You Look Tonight | 1936 | standard | ✅ |
| Yesterdays | 1933 | ballad | ✅ |
| Smoke Gets in Your Eyes | 1933 | ballad | ✅ |
| A Fine Romance | 1936 | swing | ✅ |
| Pick Yourself Up | 1936 | swing | ✅ |
| Long Ago and Far Away | 1944 | ballad | ✅ |
| The Song Is You | 1932 | standard | ✅ |
| Ol' Man River | 1927 | standard | ✅ |

## 3. Jelly Roll Morton †1941 — единоличный автор
| Тема | Стиль | Прим. |
|---|---|---|
| King Porter Stomp | early jazz | ✅ |
| Black Bottom Stomp | early jazz | ✅ |
| The Pearls | early jazz | ✅ |
| Jelly Roll Blues | early jazz/blues | ✅ (1915) |
| Grandpa's Spells | early jazz | ✅ |
| Dead Man Blues | early jazz | ⚠️ возможно уже в каталоге — проверить дубль |

## 4. Fats Waller †1943 — только ЕДИНОЛИЧНАЯ музыка (у многих хитов есть со-композитор!)
| Тема | Стиль | Прим. |
|---|---|---|
| Honeysuckle Rose | 1929 | swing | ✅ музыка Waller (Razaf — текст) |
| Jitterbug Waltz | 1942 | swing/jazz waltz | ✅ единоличный |
| Keepin' Out of Mischief Now | 1932 | swing | ✅ музыка Waller |
| Blue Turning Grey Over You | 1929 | ballad | ⚠️ проверить (Waller/Razaf — музыка Waller) |

> ❌ ИСКЛЮЧЕНЫ у Waller (со-композитор музыки умер после 1955): **Ain't Misbehavin'** и **Black and Blue** (Harry Brooks †1970), **The Joint Is Jumpin'** (J.C. Johnson †1981), **Squeeze Me** (Clarence Williams †1965).

## 5. James P. Johnson †1955 — PD с 01.01.2026
| Тема | Стиль | Прим. |
|---|---|---|
| Charleston | 1923 | early jazz/swing | ✅ музыка J.P.J. (Cecil Mack — текст †1944) |
| Carolina Shout | 1921 | stride | ✅ единоличный |
| Snowy Morning Blues | blues | ✅ |
| If I Could Be With You | 1926 | ballad | ✅ музыка J.P.J. |

## 6. Charlie Parker †1955 — PD с 01.01.2026 🎵
**Нюанс контрафакта:** мелодия (тема) Паркера — PD. Но многие бибоп-головы написаны НА ГАРМОНИЮ чужих песен. Поэтому:
- **Блюзы** (12-тактовый блюз — форма не охраняется) и **rhythm changes** (гармония = «I Got Rhythm» Гершвина, PD) → **полностью чисто** (и мелодия, и гармония PD).
- Темы на чужую гармонию (Cherokee, How High the Moon и т.п.) — печатаем только МЕЛОДИЮ; аккорды чужой песни не выкладываем.
**Берём только ЕДИНОЛИЧНЫЕ темы Паркера** (со-авторские исключены).

| Тема | Основа | Прим. |
|---|---|---|
| Confirmation | оригинальная гармония | ✅ чисто |
| Now's the Time | блюз | ✅ чисто |
| Billie's Bounce | блюз | ✅ чисто |
| Au Privave | блюз | ✅ чисто |
| Bloomdido | блюз | ✅ чисто |
| Cool Blues | блюз | ✅ чисто |
| Barbados | блюз | ✅ чисто |
| Cheryl | блюз | ✅ чисто |
| Relaxin' at Camarillo | блюз | ✅ чисто |
| Parker's Mood | блюз | ✅ чисто |
| Chi Chi | блюз | ✅ чисто |
| Scrapple from the Apple | A=Honeysuckle Rose(PD)/B=rhythm changes(PD) | ✅ чисто целиком |
| Moose the Mooche | rhythm changes (PD) | ✅ чисто целиком |
| Yardbird Suite | оригинальная гармония | ✅ чисто |
| Ah-Leu-Cha | оригинальная | ✅ |

> ❌ ИСКЛЮЧЕНЫ у Паркера (со-композитор жив после 1955 или спорно): **Anthropology** (Dizzy Gillespie †1993), **Ornithology** (Benny Harris †1975), **Donna Lee** (спорно Miles Davis †1991), **Ko-Ko** (на «Cherokee» Ray Noble †1978).

## 7. Прочие PD-композиторы (надёжная атрибуция)
| Тема | Композитор | Прим. |
|---|---|---|
| In a Mist | Bix Beiderbecke †1931 | ✅ |
| Twelfth Street Rag | Euday L. Bowman †1949 | ✅ jazz/ragtime |
| Trouble in Mind | Richard M. Jones †1945 | ✅ ранний блюз-стандарт |
| West End Blues | King Oliver †1938 | ⚠️ музыка Oliver (инстр. тема) — проверить |

## 8. Традиционные / спиричуэлс / ранний блюз (PD по возрасту, нет охраняемого авторства)
Все — public domain. Отлично ложатся в диксиленд/нью-орлеан-репертуар трубы.

When the Saints Go Marching In (✅ уже id 83) · Down by the Riverside · Just a Closer Walk with Thee · Swing Low, Sweet Chariot · Nobody Knows the Trouble I've Seen · Go Down Moses · Sometimes I Feel Like a Motherless Child · Wade in the Water · Deep River · Careless Love · Frankie and Johnny · Make Me a Pallet on the Floor

---

## ❌ ЧЁТКО ИСКЛЮЧЕНО (НЕ PD в Германии)
- **W.C. Handy †1958** (St. Louis Blues, Memphis Blues) — PD только с 2029.
- **Sidney Bechet †1959** (Petite Fleur) — с 2030.
- **Spencer Williams †1965** (Basin Street Blues, I Ain't Got Nobody).
- **Nick LaRocca †1961** (Tiger Rag, ODJB).
- **Kid Ory †1973** (Muskrat Ramble), **Turner Layton †1978** (After You've Gone, Way Down Yonder).
- **Shelton Brooks †1975** (Some of These Days, Darktown Strutters' Ball).
- Ellington †1974, Monk †1982, Cole Porter †1964, Rodgers †1979, Arlen †1986, Carmichael †1981, Kenny Dorham †1972, Sonny Rollins (жив) — весь поздний songbook/бибоп с живыми/недавними авторами.
- **St. James Infirmary** — спорно (рег. «Joe Primrose» = Irving Mills †1985); мелодия трад., но регистрация претендует → пока не берём.

---

## Итого к заведению (без дублей с текущим каталогом)
**≈ 55 безопасных позиций** в ядре: Gershwin 13 · Kern 9 · Morton 5–6 · Waller 3–4 · J.P. Johnson 4 · Parker 15 · прочие 4 · традиционные 11.
Для старта — **взять топ-30**: все Gershwin + All The Things You Are/The Way You Look Tonight/Smoke Gets in Your Eyes (Kern) + Confirmation/Now's the Time/Billie's Bounce/Scrapple/Yardbird Suite (Parker) + King Porter Stomp (Morton) + Honeysuckle Rose (Waller) + Down by the Riverside/Just a Closer Walk (трад).

**Дальше:** по каждой позиции нужен ВЫВЕРЕННЫЙ источник мелодии (MusicXML/MIDI из MuseScore или подтверждение нот) → `gen_parts` → партии под трубу/тромбон/сакс/кларнет/ф-но. Ноты «из головы» не выдумываем (Правило №1).
