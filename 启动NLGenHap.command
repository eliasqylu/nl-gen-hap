#!/bin/zsh
cd "${0:A:h}"
exec "$PWD/.venv/bin/python" -m streamlit run "$PWD/app/main.py" \
  --server.address 127.0.0.1 --server.port 8520
