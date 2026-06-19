# JazzTone — Jazz Trumpet Library bot

Коммерческий AI-тренажёр для духовых + библиотека нот (public-domain). Telegram-бот
**@JazzTrumpetLibraryBot**, домен **jazztone.app**. ~190 нот, 9 инструментов.

## Структура
- `bot.py` — точка входа Telegram-бота (python-telegram-bot 21.9). Это то, что гоняет systemd.
- `app.py` — веб/бэкенд мини-аппы.
- `billing.py` — оплата через Telegram Stars.
- `analysis.py`, `transcribe.py`, `midi_melody.py`, `gen_parts.py` — музыкальный/аудио пайплайн.
- `notes.json` — каталог нот (источник истины для библиотеки). Менять через скрипты `ingest_*.py`, не руками.
- `miniapp/`, `web/` — фронт мульти-страничной мини-аппы.
- `notes/` — PDF нот (на сервере догружаются в `deploy_trumpet.sh`, в гит не коммитятся).
- `deploy_trumpet.sh` — **полный bootstrap** сервера (свежий clone + PDF + venv + systemd). НЕ для обычных обновлений.

## Деплой (важно)
- Прод крутится на сервере **Hetzner 65.109.34.151** (alias `tuman` в `~/.ssh/config`), путь `/root/trumpet-jazz-bot`, systemd-юнит **`trumpetbot.service`**.
- Обычное обновление = push в GitHub → на сервере `git pull` + `systemctl restart trumpetbot`. Для этого есть скилл **`deploy-jazztone`**.
- Полный пересбор (новые PDF/зависимости) = `bash deploy_trumpet.sh` на сервере.
- venv: `./.venv/bin/python`, зависимости в `requirements.txt`.

## Правила
- Сервер в Финляндии, есть хайрпин-нюанс — мини-аппа вынесена на отдельный домен через Cloudflare-туннель (см. память проекта). НЕ привязывай мини-аппу к IP сервера.
- Не коммить секреты (токен бота, ключи) — они на сервере/в окружении.
- Музыкальные правки (репертуар, тональности, аранжировки) — через скилл `music-expert`.
- Git remote: `github.com/GrooveMaitre/trumpet-jazz-bot`.

## Проверка после деплоя
```
ssh tuman "systemctl is-active trumpetbot && journalctl -u trumpetbot -n 20 --no-pager"
```
