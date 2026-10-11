#!/usr/bin/with-contenv bashio
bashio::log.info "Starte Stapeljagd ..."
cd /app
exec python3 /app/server.py
