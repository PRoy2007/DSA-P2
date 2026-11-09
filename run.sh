#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but was not found."
    echo "Please install Python 3 and python3-venv."
    exit 1
fi

python3 launcher.py