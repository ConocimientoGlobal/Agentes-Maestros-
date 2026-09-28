#!/data/data/com.termux/files/usr/bin/bash
# Arranca o Hermes gateway de Telegram no boot con skin kemur-ai
# Mata calquera instancia previa para non duplicar
pkill -f "hermes gateway run" 2>/dev/null
sleep 3

export HERMES_SKIN="kemur-ai"
export HERMES_ACCEPT_HOOKS="1"
export TELEGRAM_ALLOWED_USERS="-1004495266986,6040085088"

# Esperar a que o sistema de ficheiros estea listo (Android)
sleep 5

cd ~/.hermes/logs 2>/dev/null || mkdir -p ~/.hermes/logs
nohup hermes gateway run --replace >> gateway.log 2>&1 &
