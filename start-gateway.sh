#!/data/data/com.termux/files/usr/bin/bash
# start-gateway.sh — Lanzador de Hermes Gateway con Telegram
#
# Configura variables de entorno y ejecuta el gateway.
# Edita TELEGRAM_ALLOWED_USERS e HERMES_SKIN según tu setup.
#
# Uso: ./start-gateway.sh

export TELEGRAM_ALLOWED_USERS="-10044952666986,6040085088"
export HERMES_ACCEPT_HOOKS="1"
export HERMES_SKIN="kemur-ai"

cd /data/data/com.termux/files/home
exec hermes gateway run 2>&1