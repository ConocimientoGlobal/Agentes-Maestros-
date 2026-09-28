#!/data/data/com.termux/files/usr/bin/bash
# Lanzar Hermes Gateway con Telegram configurado

export TELEGRAM_ALLOWED_USERS="-1004495266986,6040085088"
export HERMES_ACCEPT_HOOKS="1"
export HERMES_SKIN="kemur-ai"

cd /data/data/com.termux/files/home
exec hermes gateway run 2>&1
