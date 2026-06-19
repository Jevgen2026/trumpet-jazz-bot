#!/bin/bash
# Server-side bootstrap for Jazz Trumpet Library bot. Runs entirely on the server.
set -e
cd /root
rm -rf trumpet-jazz-bot
echo "STEP clone"
git clone --depth 1 https://github.com/GrooveMaitre/trumpet-jazz-bot.git
cd /root/trumpet-jazz-bot
echo "STEP move-pdfs-into-notes"
mkdir -p notes
mv *.pdf notes/ 2>/dev/null || true
echo "STEP download-public-domain"
curl -sL --max-time 300 -o "notes/Arban - Complete Method (Cornet_Trumpet, 1893).pdf" "https://archive.org/download/ArbansCompleteCelebratedMethodForTheCornet1893/Arban%27s%20Complete%20Celebrated%20Method%20for%20the%20Cornet%20%281893%29.pdf"
curl -sL --max-time 300 -o "notes/Saint-Jacome - Grand Method for Cornet_Trumpet.pdf" "https://archive.org/download/newmoderngrandme00sain/newmoderngrandme00sain.pdf"
curl -sL --max-time 300 -o "notes/Pares - Daily Exercises and Scales (Trumpet).pdf" "https://archive.org/download/dailyexercisessc00pars/dailyexercisessc00pars.pdf"
curl -sL --max-time 300 -o "notes/Kopprasch - 60 Selected Studies (Trombone).pdf" "https://archive.org/download/sixtystudiesfort00kopp/sixtystudiesfort00kopp.pdf"
curl -sL --max-time 300 -o "notes/Rochut-Bordogni - Melodious Etudes for Trombone.pdf" "https://archive.org/download/melodious-etudes-for-trombone-selected-f/Melodious_etudes_for_trombone_selected_f.pdf"
echo "STEP requirements"
printf 'python-telegram-bot==21.9\n' > requirements.txt
echo "STEP venv"
python3 -m venv .venv
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt
echo "STEP systemd-unit"
cat > /etc/systemd/system/trumpetbot.service <<'UNIT'
[Unit]
Description=Jazz Trumpet Library Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/root/trumpet-jazz-bot
ExecStart=/root/trumpet-jazz-bot/.venv/bin/python /root/trumpet-jazz-bot/bot.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
echo "STEP verify"
echo "pdf_count=$(ls -1 notes/*.pdf 2>/dev/null | wc -l)"
echo "valid_pdfs=$(file notes/*.pdf | grep -c 'PDF document')"
./.venv/bin/python -c "import telegram,json;print('ptb',telegram.__version__,'notes',len(json.load(open('notes.json'))))"
echo "DEPLOY_DONE"
