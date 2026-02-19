#!/bin/bash
export PATH="$HOME/.local/bin:$PATH"
cd "$(dirname "$0")"
streamlit run app/Home.py --server.port 8501 --server.headless true --theme.base dark
