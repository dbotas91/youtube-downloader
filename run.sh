#!/usr/bin/env bash
# Script para iniciar a aplicação ativando automaticamente o ambiente virtual
cd "$(dirname "$0")"

# Garante acesso ao Node.js e ferramentas do Linuxbrew se instaladas
if [ -d "/home/linuxbrew/.linuxbrew/bin" ]; then
    export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
fi

source .venv/bin/activate
python3 main.py
