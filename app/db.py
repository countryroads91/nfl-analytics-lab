"""Database connection helper for the NFL Analytics app.

On first run (or when nfl.duckdb doesn't exist), this module automatically
builds the database from the .parquet files in data_processed/.
"""
import os
import glob
from pathlib import Path

import duckdb
from app.config import DB_PATH, DATA_DIR


def _build_db_from_parquets(db_path: str, data_dir: str) -> None:
    """Build nfl.duckdb from parquet files when the DB doesn't exist."""
    import time
    t0 = time.time()
    print("⚙️ Building database from parquet files… (first-run only)")

    con = duckdb.connect(db_path)
    try:
        # ── Step 1: Load each parquet file as a raw table ──────────────────
        parquet_files = sorted(glob.glob(os.path.join(data_dir, "*.parquet")))
        for pf in parquet_files:
            table_name = Path(pf).stem
            safe_path = pf.replace("\\", "/")
            con.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" AS SELECT * FROM read_parquet(\'{safe_path}\')')
            print(f"  ✅ Loaded {table_name}")

        # ── Step 2: Create canonical joined tables (mirrors ingest.py) ─────

        con.execute("""
            CREATE TABLE IF NOT EXISTS games AS
            SELECT
                g.gid, g.seas, g.wk, g.day, s.date,
                g.v, g.h, g.stad, g.temp, g.humd, g.wspd, g.wdir, g.cond, g.surf,
                g.ou, g.sprv, g.ptsv, g.ptsh
            FROM "GAME" g
            LEFT JOIN "SCHEDULE" s ON g.gid = s.gid
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS plays AS
            SELECT
                gid, pid, detail, off, def, type, dseq, len, qtr, min, sec,
                ptso, ptsd, timo, timd, dwn, ytg, yfog, zone, yds, succ, fd, sg, nh, pts,
                bc, kne, dir, psr, comp, spk, loc, trg, dfb, eps, epa
            FROM "PBP"
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS drives AS
            SELECT
                uid, gid, fpid, tname, drvn, obt, qtr, min, sec, yfog, plays,
                succ, rfd, pfd, ofd, ry, ra, py, pa, pc, peyf, peya, net, res
            FROM "DRIVE"
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS passes AS
            SELECT
                p.pid, p.psr, p.trg, p.loc, p.yds, p.comp, p.succ, p.spk, p.dfb,
                pl.gid, pl.off, pl.def, pl.qtr, pl.min, pl.sec, pl.pts
            FROM "PASS" p
            LEFT JOIN plays pl ON p.pid = pl.pid
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS rushes AS
            SELECT
                r.pid, r.bc, r.dir, r.yds, r.succ, r.kne,
                pl.gid, pl.off, pl.def, pl.qtr, pl.min, pl.sec, pl.pts
            FROM "RUSH" r
            LEFT JOIN plays pl ON r.pid = pl.pid
        """)

        _simple = [
            ("penalties",      'SELECT uid, pid, ptm, pen, "desc", cat, pey, act FROM "PENALTY"'),
            ("sacks",          'SELECT uid, pid, qb, sk, value, ydsl FROM "SACK"'),
            ("tackles",        'SELECT uid, pid, tck, value FROM "TACKLE"'),
            ("players",        'SELECT * FROM "PLAYER"'),
            ("offense_stats",  'SELECT * FROM "OFFENSE"'),
            ("defense_stats",  'SELECT * FROM "DEFENSE"'),
            ("injuries",       'SELECT * FROM "INJURY"'),
            ("snaps",          'SELECT * FROM "SNAP"'),
            ("redzone",        'SELECT * FROM "REDZONE"'),
            ("fgxp",           'SELECT * FROM "FGXP"'),
            ("touchdowns",     'SELECT * FROM "TD"'),
            ("fumbles",        'SELECT * FROM "FUMBLE"'),
            ("interceptions",  'SELECT * FROM "INTERCPT"'),
            ("kickoffs",       'SELECT * FROM "KOFF"'),
            ("punts",          'SELECT * FROM "PUNT"'),
            ("blocks",         'SELECT * FROM "BLOCK"'),
            ("conversions",    'SELECT * FROM "CONV"'),
            ("safeties",       'SELECT * FROM "SAFETY"'),
        ]
        for view_name, sql in _simple:
            con.execute(f"CREATE TABLE IF NOT EXISTS {view_name} AS {sql}")

        elapsed = round(time.time() - t0, 1)
        print(f"✅ Database ready ({elapsed}s)")
    except Exception as exc:
        con.close()
        try:
            os.remove(db_path)
        except OSError:
            pass
        raise RuntimeError(f"Failed to build DuckDB from parquets: {exc}") from exc

    con.close()


def _ensure_db():
    """Build DB if it doesn't exist. Called once before caching the connection."""
    if not os.path.exists(DB_PATH):
        _build_db_from_parquets(DB_PATH, DATA_DIR)


# Build outside the cached function so no st.* calls happen inside cache
_ensure_db()


def get_connection():
    """Return a read-only DuckDB connection."""
    if not hasattr(get_connection, "_con") or get_connection._con is None:
        get_connection._con = duckdb.connect(DB_PATH, read_only=True)
    return get_connection._con


def query(sql: str, params=None):
    """Execute SQL and return a pandas DataFrame."""
    con = get_connection()
    if params:
        return con.execute(sql, params).fetchdf()
    return con.execute(sql).fetchdf()


def query_polars(sql: str):
    """Execute SQL and return a Polars DataFrame."""
    import polars as pl
    con = get_connection()
    return pl.from_pandas(con.execute(sql).fetchdf())
