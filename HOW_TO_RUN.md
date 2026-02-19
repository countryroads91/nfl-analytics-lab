# How to Run the NFL Betting Analytics Lab

## Prerequisites: Python

You need Python 3.8 or higher installed.
- **Download:** https://www.python.org/downloads/
- During installation, **check the box** that says **"Add Python to PATH"**

To check if you already have Python:
- Open Command Prompt and type: `python --version`
- If you see something like `Python 3.11.0`, you're ready.

---

## Running the App (Windows)

### Option 1 — Double-click (easiest)
1. Open the `nfl_analytics` folder
2. Double-click **`run.bat`**
3. A terminal window will appear, install dependencies, then launch the app
4. Your browser will open automatically at **http://localhost:8501**

### Option 2 — Command Prompt
1. Open Command Prompt (`Win + R` → type `cmd` → Enter)
2. Navigate to this folder:
   ```
   cd "C:\Users\bmisa\OneDrive\Documents\P&B Concepts\NFL\WORK\nfl_analytics"
   ```
3. Install dependencies (first time only):
   ```
   python -m pip install duckdb polars pyarrow streamlit plotly pandas numpy scipy scikit-learn
   ```
4. Launch the app:
   ```
   python -m streamlit run app\Home.py
   ```
5. Open your browser to **http://localhost:8501**

---

## Stopping the App
- Press **Ctrl + C** in the terminal window, or just close it.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` not recognized | Install Python and check "Add to PATH", then restart terminal |
| `pip` not recognized | Use `python -m pip` instead |
| App opens but shows errors | Run `python -m pip install --upgrade streamlit plotly duckdb` |
| Browser doesn't open | Manually go to http://localhost:8501 |
| Port already in use | Change `8501` to `8502` in the command |
