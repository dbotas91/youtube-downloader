#!/usr/bin/env bash
# Script para iniciar a aplicação ativando automaticamente o ambiente virtual
cd "$(dirname "$0")"

# Garante acesso ao Node.js e ferramentas do Linuxbrew se instaladas
if [ -d "/home/linuxbrew/.linuxbrew/bin" ]; then
    export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
fi

# Cria o ambiente virtual e instala dependências caso ainda não existam
if [ ! -f ".venv/bin/activate" ]; then
    echo "Ambiente virtual não detetado. A criar .venv e a instalar dependências..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

python3 main.py
