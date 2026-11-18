#!/usr/bin/env bash
# Script para iniciar a aplicação ativando automaticamente o ambiente virtual
cd "$(dirname "$0")"
source .venv/bin/activate
python3 main.py
