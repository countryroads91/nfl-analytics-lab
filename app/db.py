"""Database connection helper for the NFL Analytics app.

On first run (or when nfl.duckdb doesn't exist), this module automatically
builds the database from the .parquet files in data_processed/.

Self-contained: paths are resolved relative to __file__ so this module
works correctly regardless of working directory or sys.path order.
"""
import os
import glob
import threading
from pathlib import Path

import duckdb

# ── Resolve paths relative to this file ──────────────────────────────────────
_APP_DIR = Path(__file__).parent.resolve()
_PROJ_DIR = _APP_DIR.parent.resolve()
_DATA_DIR = _PROJ_DIR / "data_processed"

# On Linux (Streamlit Cloud) fall back to /tmp if the repo dir isn't writable.
# On Windows (dev) always use data_processed/ so the built DB is reused.
def _choose_db_path() -> str:
    candidate = str(_DATA_DIR / "nfl.duckdb")
    if os.name == "nt":          # Windows — always use the project path
        return candidate
    # Linux: prefer data_processed/ if writable; otherwise /tmp
    if os.access(str(_DATA_DIR), os.W_OK):
        return candidate
    return "/tmp/nfl.duckdb"

DB_PATH = _choose_db_path()
DATA_DIR = str(_DATA_DIR)

_build_lock = threading.Lock()


def _build_db_from_parquets(db_path: str, data_dir: str) -> None:
    """Build nfl.duckdb from parquet files when the DB doesn't exist."""
    import time
    t0 = time.time()
    print("⚙️  Building database from parquet files… (first-run only)")

    con = duckdb.connect(db_path)
    try:
        parquet_files = sorted(glob.glob(os.path.join(data_dir, "*.parquet")))
        if not parquet_files:
            raise FileNotFoundError(
                f"No .parquet files found in {data_dir!r}. "
                "Check that data_processed/ is committed to the repo."
            )

        for pf in parquet_files:
            table_name = Path(pf).stem
            # Use forward slashes — DuckDB requires them on all platforms
            safe_path = pf.replace("\\", "/")
            con.execute(
                f'CREATE TABLE IF NOT EXISTS "{table_name}" AS '
                f"SELECT * FROM read_parquet('{safe_path}')"
            )
            print(f"  ✅  Loaded {table_name}")

        # ── Canonical joined tables (mirrors ingest.py) ──────────────────────
        con.execute("""
            CREATE TABLE IF NOT EXISTS games AS
            SELECT g.gid, g.seas, g.wk, g.day, s.date,
                   g.v, g.h, g.stad, g.temp, g.humd, g.wspd, g.wdir, g.cond, g.surf,
                   g.ou, g.sprv, g.ptsv, g.ptsh
            FROM "GAME" g LEFT JOIN "SCHEDULE" s ON g.gid = s.gid
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS plays AS
            SELECT gid, pid, detail, off, def, type, dseq, len, qtr, min, sec,
                   ptso, ptsd, timo, timd, dwn, ytg, yfog, zone, yds, succ, fd,
                   sg, nh, pts, bc, kne, dir, psr, comp, spk, loc, trg, dfb, eps, epa
            FROM "PBP"
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS drives AS
            SELECT uid, gid, fpid, tname, drvn, obt, qtr, min, sec, yfog, plays,
                   succ, rfd, pfd, ofd, ry, ra, py, pa, pc, peyf, peya, net, res
            FROM "DRIVE"
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS passes AS
            SELECT p.pid, p.psr, p.trg, p.loc, p.yds, p.comp, p.succ, p.spk, p.dfb,
                   pl.gid, pl.off, pl.def, pl.qtr, pl.min, pl.sec, pl.pts
            FROM "PASS" p LEFT JOIN plays pl ON p.pid = pl.pid
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS rushes AS
            SELECT r.pid, r.bc, r.dir, r.yds, r.succ, r.kne,
                   pl.gid, pl.off, pl.def, pl.qtr, pl.min, pl.sec, pl.pts
            FROM "RUSH" r LEFT JOIN plays pl ON r.pid = pl.pid
        """)

        for view_name, sql in [
            ("penalties",     'SELECT uid, pid, ptm, pen, "desc", cat, pey, act FROM "PENALTY"'),
            ("sacks",         'SELECT uid, pid, qb, sk, value, ydsl FROM "SACK"'),
            ("tackles",       'SELECT uid, pid, tck, value FROM "TACKLE"'),
            ("players",       'SELECT * FROM "PLAYER"'),
            ("offense_stats", 'SELECT * FROM "OFFENSE"'),
            ("defense_stats", 'SELECT * FROM "DEFENSE"'),
            ("injuries",      'SELECT * FROM "INJURY"'),
            ("snaps",         'SELECT * FROM "SNAP"'),
            ("redzone",       'SELECT * FROM "REDZONE"'),
            ("fgxp",          'SELECT * FROM "FGXP"'),
            ("touchdowns",    'SELECT * FROM "TD"'),
            ("fumbles",       'SELECT * FROM "FUMBLE"'),
            ("interceptions", 'SELECT * FROM "INTERCPT"'),
            ("kickoffs",      'SELECT * FROM "KOFF"'),
            ("punts",         'SELECT * FROM "PUNT"'),
            ("blocks",        'SELECT * FROM "BLOCK"'),
            ("conversions",   'SELECT * FROM "CONV"'),
            ("safeties",      'SELECT * FROM "SAFETY"'),
        ]:
            con.execute(f"CREATE TABLE IF NOT EXISTS {view_name} AS {sql}")

        elapsed = round(time.time() - t0, 1)
        print(f"✅  Database ready ({elapsed}s)")
    except Exception as exc:
        con.close()
        try:
            os.remove(db_path)
        except OSError:
            pass
        raise RuntimeError(f"Failed to build DuckDB from parquets: {exc}") from exc
    con.close()


def _ensure_db() -> None:
    """Build DB if needed (thread-safe).  Called once at module import."""
    if not os.path.exists(DB_PATH):
        with _build_lock:
            if not os.path.exists(DB_PATH):
                _build_db_from_parquets(DB_PATH, DATA_DIR)


# Build at import time — no Streamlit UI calls here
_ensure_db()


# ── Public API ────────────────────────────────────────────────────────────────

def get_connection():
    """Return a fresh read-only DuckDB connection (caller must close it)."""
    return duckdb.connect(DB_PATH, read_only=True)


def query(sql: str, params=None):
    """Execute SQL and return a pandas DataFrame."""
    con = get_connection()
    try:
        if params:
            return con.execute(sql, params).fetchdf()
        return con.execute(sql).fetchdf()
    finally:
        con.close()


def query_polars(sql: str):
    """Execute SQL and return a Polars DataFrame."""
    import polars as pl
    con = get_connection()
    try:
        return pl.from_pandas(con.execute(sql).fetchdf())
    finally:
        con.close()
