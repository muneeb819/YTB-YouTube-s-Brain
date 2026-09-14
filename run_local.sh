#!/usr/bin/env bash
set -e
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
mkdir -p data workspace
uvicorn ytb.main:app --host 0.0.0.0 --port 8000
