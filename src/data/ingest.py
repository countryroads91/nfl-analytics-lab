"""
NFL Analytics Data Ingestion Pipeline
Reads all CSVs, builds canonical views, creates DuckDB database and Parquet files
Memory-optimized version using DuckDB for large files
"""

import os
import json
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import duckdb

# Configuration
NFL_DATA_DIR = "/sessions/clever-epic-galileo/mnt/NFL"
OUTPUT_DIR = "/sessions/clever-epic-galileo/nfl_analytics/data_processed"
DB_PATH = f"{OUTPUT_DIR}/nfl.duckdb"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


class NFLDataPipeline:
    """Main data ingestion and processing pipeline"""

    def __init__(self):
        """Initialize the pipeline"""
        self.data_dict = {}
        self.qa_report = {}
        self.conn = None

    def connect_db(self):
        """Create DuckDB connection"""
        # Remove existing DB if it exists
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        self.conn = duckdb.connect(DB_PATH)
        print(f"Connected to DuckDB: {DB_PATH}")

    def close_db(self):
        """Close DuckDB connection"""
        if self.conn:
            self.conn.close()

    def load_raw_tables(self):
        """Load all CSV files directly into DuckDB as raw tables"""
        print("\n=== LOADING RAW CSV TABLES ===")
        csv_files = sorted(glob.glob(f"{NFL_DATA_DIR}/*.csv"))

        for csv_file in csv_files:
            table_name = Path(csv_file).stem
            try:
                # Use read_csv with relaxed parsing for PLAY file
                if table_name == 'PLAY':
                    self.conn.execute(f"""
                        CREATE TABLE {table_name} AS
                        SELECT * FROM read_csv('{csv_file}', ignore_errors=true)
                    """)
                else:
                    self.conn.execute(f"""
                        CREATE TABLE {table_name} AS
                        SELECT * FROM read_csv_auto('{csv_file}')
                    """)

                # Get table stats
                result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchall()[0][0]
                print(f"✓ {table_name}: {result} rows")
            except Exception as e:
                print(f"✗ {table_name}: {e}")

    def build_data_dictionary(self):
        """Build comprehensive data dictionary for all tables"""
        print("\n=== BUILDING DATA DICTIONARY ===")

        # Get all table names from DuckDB
        tables = self.conn.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='main'
        """).fetchall()

        for (table_name,) in tables:
            try:
                # Get table info
                schema = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
                columns = [row[0] for row in schema]
                dtypes = {row[0]: row[1] for row in schema}

                # Row count
                row_count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchall()[0][0]

                # Missing percentage
                missing_count = 0
                total_cells = 0
                for col in columns:
                    null_count = self.conn.execute(
                        f"SELECT COUNT(*) FROM {table_name} WHERE {col} IS NULL"
                    ).fetchall()[0][0]
                    missing_count += null_count
                    total_cells += row_count

                missing_pct = (missing_count / total_cells * 100) if total_cells > 0 else 0

                # Season range
                season_range = None
                if 'seas' in columns:
                    try:
                        result = self.conn.execute(
                            f"SELECT MIN(seas), MAX(seas) FROM {table_name} WHERE seas IS NOT NULL"
                        ).fetchall()[0]
                        if result[0] is not None:
                            season_range = (int(result[0]), int(result[1]))
                    except:
                        pass

                # Missing by column
                missing_by_col = {}
                for col in columns:
                    null_pct = self.conn.execute(
                        f"SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE {col} IS NULL) / COUNT(*), 2) FROM {table_name}"
                    ).fetchall()[0][0]
                    missing_by_col[col] = null_pct

                self.data_dict[table_name] = {
                    "row_count": row_count,
                    "column_count": len(columns),
                    "columns": columns,
                    "dtypes": dtypes,
                    "missing_percentage": round(missing_pct, 2),
                    "missing_by_column": missing_by_col,
                    "season_range": season_range
                }

                print(f"✓ {table_name}: {row_count} rows, {missing_pct:.1f}% missing")
            except Exception as e:
                print(f"✗ {table_name}: {e}")

    def export_to_parquet(self):
        """Export all tables to Parquet format"""
        print("\n=== EXPORTING TO PARQUET ===")

        tables = self.conn.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='main'
        """).fetchall()

        for (table_name,) in tables:
            try:
                output_path = f"{OUTPUT_DIR}/{table_name}.parquet"
                self.conn.execute(f"""
                    COPY {table_name} TO '{output_path}' (FORMAT PARQUET, COMPRESSION SNAPPY)
                """)
                print(f"✓ {table_name}.parquet")
            except Exception as e:
                print(f"✗ {table_name}.parquet: {e}")

    def create_canonical_views(self):
        """Create canonical views and tables from raw tables"""
        print("\n=== CREATING CANONICAL VIEWS ===")

        views_created = 0

        # 1. GAMES view: GAME + SCHEDULE joined on gid
        try:
            # Check if GAME and SCHEDULE tables exist
            self.conn.execute("SELECT 1 FROM GAME LIMIT 1")
            self.conn.execute("SELECT 1 FROM SCHEDULE LIMIT 1")

            self.conn.execute("""
                CREATE TABLE games AS
                SELECT
                    g.gid, g.seas, g.wk, g.day, s.date,
                    g.v, g.h, g.stad, g.temp, g.humd, g.wspd, g.wdir, g.cond, g.surf,
                    g.ou, g.sprv, g.ptsv, g.ptsh
                FROM GAME g
                LEFT JOIN SCHEDULE s ON g.gid = s.gid
            """)
            print("✓ games")
            views_created += 1
        except Exception as e:
            if "does not exist" in str(e):
                print(f"⊘ games: GAME or SCHEDULE table not loaded")
            else:
                print(f"✗ games: {e}")

        # 2. PLAYS view: from PBP with key columns
        try:
            self.conn.execute("""
                CREATE TABLE plays AS
                SELECT
                    gid, pid, detail, off, def, type, dseq, len, qtr, min, sec,
                    ptso, ptsd, timo, timd, dwn, ytg, yfog, zone, yds, succ, fd, sg, nh, pts,
                    bc, kne, dir, psr, comp, spk, loc, trg, dfb, eps, epa
                FROM PBP
            """)
            print("✓ plays")
            views_created += 1
        except Exception as e:
            print(f"✗ plays: {e}")

        # 3. DRIVES view
        try:
            self.conn.execute("""
                CREATE TABLE drives AS
                SELECT
                    uid, gid, fpid, tname, drvn, obt, qtr, min, sec, yfog, plays,
                    succ, rfd, pfd, ofd, ry, ra, py, pa, pc, peyf, peya, net, res
                FROM DRIVE
            """)
            print("✓ drives")
            views_created += 1
        except Exception as e:
            print(f"✗ drives: {e}")

        # 4. PASSES view: PASS joined to PLAYS
        try:
            self.conn.execute("""
                CREATE TABLE passes AS
                SELECT
                    p.pid, p.psr, p.trg, p.loc, p.yds, p.comp, p.succ, p.spk, p.dfb,
                    pl.gid, pl.off, pl.def, pl.qtr, pl.min, pl.sec, pl.pts
                FROM PASS p
                LEFT JOIN plays pl ON p.pid = pl.pid
            """)
            print("✓ passes")
            views_created += 1
        except Exception as e:
            print(f"✗ passes: {e}")

        # 5. RUSHES view: RUSH joined to PLAYS
        try:
            self.conn.execute("""
                CREATE TABLE rushes AS
                SELECT
                    r.pid, r.bc, r.dir, r.yds, r.succ, r.kne,
                    pl.gid, pl.off, pl.def, pl.qtr, pl.min, pl.sec, pl.pts
                FROM RUSH r
                LEFT JOIN plays pl ON r.pid = pl.pid
            """)
            print("✓ rushes")
            views_created += 1
        except Exception as e:
            print(f"✗ rushes: {e}")

        # 6-23: Simple views from individual tables
        # Note: Some tables may not exist if they had load errors
        simple_views = [
            ("penalties", "SELECT uid, pid, ptm, pen, \"desc\", cat, pey, act FROM PENALTY", "PENALTY"),
            ("sacks", "SELECT uid, pid, qb, sk, value, ydsl FROM SACK", "SACK"),
            ("tackles", "SELECT uid, pid, tck, value FROM TACKLE", "TACKLE"),
            ("players", "SELECT * FROM PLAYER", "PLAYER"),
            ("offense_stats", "SELECT * FROM OFFENSE", "OFFENSE"),
            ("defense_stats", "SELECT * FROM DEFENSE", "DEFENSE"),
            ("injuries", "SELECT * FROM INJURY", "INJURY"),
            ("snaps", "SELECT * FROM SNAP", "SNAP"),
            ("redzone", "SELECT * FROM REDZONE", "REDZONE"),
            ("fgxp", "SELECT * FROM FGXP", "FGXP"),
            ("touchdowns", "SELECT * FROM TD", "TD"),
            ("fumbles", "SELECT * FROM FUMBLE", "FUMBLE"),
            ("interceptions", "SELECT * FROM INTERCPT", "INTERCPT"),
            ("kickoffs", "SELECT * FROM KOFF", "KOFF"),
            ("punts", "SELECT * FROM PUNT", "PUNT"),
            ("blocks", "SELECT * FROM BLOCK", "BLOCK"),
            ("conversions", "SELECT * FROM CONV", "CONV"),
            ("safeties", "SELECT * FROM SAFETY", "SAFETY"),
        ]

        for view_name, sql, source_table in simple_views:
            try:
                # Check if source table exists first
                try:
                    self.conn.execute(f"SELECT 1 FROM {source_table} LIMIT 1")
                    self.conn.execute(f"CREATE TABLE {view_name} AS {sql}")
                    print(f"✓ {view_name}")
                    views_created += 1
                except Exception as check_err:
                    if "does not exist" in str(check_err):
                        print(f"⊘ {view_name}: source table {source_table} not loaded")
                    else:
                        raise check_err
            except Exception as e:
                print(f"✗ {view_name}: {e}")

        print(f"\nTotal views created: {views_created}")

    def run_data_quality_checks(self):
        """Run comprehensive data quality checks"""
        print("\n=== RUNNING DATA QUALITY CHECKS ===")

        qa_results = {}

        # 1. GID uniqueness in games
        try:
            result = self.conn.execute("""
                SELECT COUNT(*) as total, COUNT(DISTINCT gid) as unique_gids
                FROM games
            """).fetchall()[0]
            qa_results['gid_uniqueness'] = {
                'total_games': result[0],
                'unique_gids': result[1],
                'status': 'PASS' if result[0] == result[1] else 'WARN'
            }
            print(f"✓ GID uniqueness: {result[1]} unique out of {result[0]} games")
        except Exception as e:
            if "does not exist" in str(e):
                print(f"⊘ GID uniqueness check: games table not available")
            else:
                print(f"✗ GID uniqueness check: {e}")

        # 2. PID uniqueness per gid in plays
        try:
            result = self.conn.execute("""
                SELECT COUNT(*) as total_plays,
                       COUNT(DISTINCT (gid, pid)) as unique_play_ids,
                       COUNT(DISTINCT gid) as unique_games
                FROM plays
            """).fetchall()[0]
            qa_results['pid_uniqueness'] = {
                'total_plays': result[0],
                'unique_play_ids': result[1],
                'unique_games': result[2],
                'status': 'PASS' if result[0] == result[1] else 'WARN'
            }
            print(f"✓ PID uniqueness: {result[1]} unique (gid, pid) out of {result[0]} plays")
        except Exception as e:
            print(f"✗ PID uniqueness check: {e}")

        # 3. Season range coverage per table
        try:
            season_coverage = {}
            for table in ['games', 'plays', 'drives', 'offense_stats', 'defense_stats']:
                try:
                    result = self.conn.execute(f"""
                        SELECT MIN(seas) as min_season, MAX(seas) as max_season,
                               COUNT(DISTINCT seas) as num_seasons
                        FROM {table}
                        WHERE seas IS NOT NULL
                    """).fetchall()[0]
                    if result[0] is not None:
                        season_coverage[table] = {
                            'min_season': int(result[0]),
                            'max_season': int(result[1]),
                            'num_seasons': int(result[2])
                        }
                except:
                    pass
            qa_results['season_coverage'] = season_coverage
            print(f"✓ Season coverage checked for {len(season_coverage)} tables")
        except Exception as e:
            print(f"✗ Season coverage check: {e}")

        # 4. Missingness report
        try:
            missing_report = {}
            for table_name, info in self.data_dict.items():
                missing_pct = info['missing_percentage']
                if missing_pct > 10:
                    missing_report[table_name] = missing_pct
            qa_results['high_missingness_tables'] = missing_report
            print(f"✓ Missingness report: {len(missing_report)} tables >10% missing")
        except Exception as e:
            print(f"✗ Missingness check: {e}")

        # 5. Sanity checks on yards, quarters, play types
        try:
            sanity_checks = {}

            # Yards sanity check
            yards_result = self.conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN yds < -100 OR yds > 100 THEN 1 ELSE 0 END) as suspicious_yards
                FROM plays
                WHERE yds IS NOT NULL
            """).fetchall()[0]
            sanity_checks['yards'] = {
                'total_plays_with_yds': yards_result[0],
                'suspicious_yards': yards_result[1],
                'status': 'PASS' if yards_result[1] == 0 else 'WARN'
            }

            # Quarter sanity check
            qtr_result = self.conn.execute("""
                SELECT COUNT(DISTINCT qtr) as unique_quarters,
                       MIN(qtr) as min_qtr,
                       MAX(qtr) as max_qtr
                FROM plays
                WHERE qtr IS NOT NULL
            """).fetchall()[0]
            sanity_checks['quarters'] = {
                'unique_quarters': qtr_result[0],
                'min_qtr': qtr_result[1] if qtr_result[1] is not None else 0,
                'max_qtr': qtr_result[2] if qtr_result[2] is not None else 0,
                'status': 'PASS' if (qtr_result[2] is None or qtr_result[2] <= 4) else 'WARN'
            }

            # Play type distribution
            type_result = self.conn.execute("""
                SELECT type, COUNT(*) as count
                FROM plays
                WHERE type IS NOT NULL
                GROUP BY type
                ORDER BY count DESC
            """).fetchall()
            sanity_checks['play_types'] = {row[0]: int(row[1]) for row in type_result}

            qa_results['sanity_checks'] = sanity_checks
            print(f"✓ Sanity checks: yards={sanity_checks['yards']['status']}, quarters={sanity_checks['quarters']['status']}")
        except Exception as e:
            print(f"✗ Sanity checks: {e}")

        # 6. Join integrity checks
        try:
            join_integrity = {}

            # PASS table join integrity
            try:
                pass_result = self.conn.execute("""
                    SELECT COUNT(*) as pass_records,
                           COUNT(CASE WHEN pl.pid IS NOT NULL THEN 1 END) as matched_to_plays,
                           ROUND(100.0 * COUNT(CASE WHEN pl.pid IS NOT NULL THEN 1 END) / COUNT(*), 2) as match_pct
                    FROM PASS p
                    LEFT JOIN plays pl ON p.pid = pl.pid
                """).fetchall()[0]
                join_integrity['PASS'] = {
                    'records': pass_result[0],
                    'matched_to_plays': pass_result[1],
                    'match_percentage': pass_result[2]
                }
            except:
                pass

            # RUSH table join integrity
            try:
                rush_result = self.conn.execute("""
                    SELECT COUNT(*) as rush_records,
                           COUNT(CASE WHEN pl.pid IS NOT NULL THEN 1 END) as matched_to_plays,
                           ROUND(100.0 * COUNT(CASE WHEN pl.pid IS NOT NULL THEN 1 END) / COUNT(*), 2) as match_pct
                    FROM RUSH r
                    LEFT JOIN plays pl ON r.pid = pl.pid
                """).fetchall()[0]
                join_integrity['RUSH'] = {
                    'records': rush_result[0],
                    'matched_to_plays': rush_result[1],
                    'match_percentage': rush_result[2]
                }
            except:
                pass

            # SACK table join integrity (if available)
            try:
                sack_result = self.conn.execute("""
                    SELECT COUNT(*) as sack_records,
                           COUNT(CASE WHEN pl.pid IS NOT NULL THEN 1 END) as matched_to_plays,
                           ROUND(100.0 * COUNT(CASE WHEN pl.pid IS NOT NULL THEN 1 END) / COUNT(*), 2) as match_pct
                    FROM SACK s
                    LEFT JOIN plays pl ON s.pid = pl.pid
                """).fetchall()[0]
                join_integrity['SACK'] = {
                    'records': sack_result[0],
                    'matched_to_plays': sack_result[1],
                    'match_percentage': sack_result[2]
                }
            except:
                pass

            qa_results['join_integrity'] = join_integrity
            print(f"✓ Join integrity checked for {len(join_integrity)} available tables")
            for table, stats in join_integrity.items():
                print(f"  {table}: {stats['match_percentage']}% matched to plays")
        except Exception as e:
            print(f"✗ Join integrity checks: {e}")

        self.qa_report = qa_results

    def verify_database(self):
        """Verify all tables and views in DuckDB"""
        print("\n=== VERIFYING DUCKDB DATABASE ===")

        try:
            result = self.conn.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema='main'
                ORDER BY table_name
            """).fetchall()

            tables = [row[0] for row in result]
            print(f"Tables in database: {len(tables)}")
            for table in sorted(tables):
                row_count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchall()[0][0]
                print(f"  ✓ {table}: {row_count} rows")

            return tables
        except Exception as e:
            print(f"✗ Error verifying database: {e}")
            return []

    def export_data_dictionary(self):
        """Export data dictionary to JSON"""
        print("\n=== EXPORTING DATA DICTIONARY ===")

        output_file = f"{OUTPUT_DIR}/data_dictionary.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(self.data_dict, f, indent=2)
            print(f"✓ Data dictionary saved to {output_file}")
        except Exception as e:
            print(f"✗ Failed to export data dictionary: {e}")

    def export_qa_report(self):
        """Export QA report to text file"""
        print("\n=== EXPORTING QA REPORT ===")

        output_file = f"{OUTPUT_DIR}/data_qa_report.txt"
        try:
            with open(output_file, 'w') as f:
                f.write("NFL ANALYTICS DATA PIPELINE - QA REPORT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")

                # Summary
                f.write("SUMMARY\n")
                f.write("-" * 80 + "\n")
                f.write(f"Total tables loaded: {len(self.data_dict)}\n")
                f.write(f"Total rows ingested: {sum(t['row_count'] for t in self.data_dict.values())}\n")
                f.write(f"Database location: {DB_PATH}\n\n")

                # Data Dictionary
                f.write("DATA DICTIONARY\n")
                f.write("-" * 80 + "\n")
                for table_name, info in sorted(self.data_dict.items()):
                    f.write(f"\n{table_name}:\n")
                    f.write(f"  Rows: {info['row_count']}\n")
                    f.write(f"  Columns: {info['column_count']}\n")
                    f.write(f"  Missing: {info['missing_percentage']}%\n")
                    if info['season_range']:
                        f.write(f"  Seasons: {info['season_range'][0]}-{info['season_range'][1]}\n")

                    # High missingness columns
                    high_missing = {col: pct for col, pct in info['missing_by_column'].items() if pct > 50}
                    if high_missing:
                        f.write(f"  High-missing columns (>50%):\n")
                        for col, pct in sorted(high_missing.items(), key=lambda x: -x[1])[:5]:
                            f.write(f"    - {col}: {pct}%\n")

                # QA Results
                f.write("\n\n")
                f.write("QA CHECK RESULTS\n")
                f.write("-" * 80 + "\n")

                if 'gid_uniqueness' in self.qa_report:
                    r = self.qa_report['gid_uniqueness']
                    f.write(f"\nGID Uniqueness: {r['status']}\n")
                    f.write(f"  Total: {r['total_games']}, Unique: {r['unique_gids']}\n")

                if 'pid_uniqueness' in self.qa_report:
                    r = self.qa_report['pid_uniqueness']
                    f.write(f"\nPID Uniqueness: {r['status']}\n")
                    f.write(f"  Total plays: {r['total_plays']}, Unique (gid, pid): {r['unique_play_ids']}\n")

                if 'season_coverage' in self.qa_report:
                    f.write(f"\nSeason Coverage:\n")
                    for table, coverage in sorted(self.qa_report['season_coverage'].items()):
                        f.write(f"  {table}: {coverage['min_season']}-{coverage['max_season']} ")
                        f.write(f"({coverage['num_seasons']} seasons)\n")

                if 'high_missingness_tables' in self.qa_report:
                    f.write(f"\nHigh Missingness Tables (>10%):\n")
                    for table, pct in sorted(self.qa_report['high_missingness_tables'].items(), key=lambda x: -x[1]):
                        f.write(f"  {table}: {pct}%\n")

                if 'sanity_checks' in self.qa_report:
                    f.write(f"\nSanity Checks:\n")
                    sc = self.qa_report['sanity_checks']
                    f.write(f"  Yards: {sc['yards']['status']} ({sc['yards']['suspicious_yards']} suspicious)\n")
                    f.write(f"  Quarters: {sc['quarters']['status']} (max={sc['quarters']['max_qtr']})\n")
                    f.write(f"  Play types: {len(sc['play_types'])} types detected\n")
                    for ptype, count in sorted(sc['play_types'].items(), key=lambda x: -x[1])[:10]:
                        f.write(f"    - {ptype}: {count}\n")

                if 'join_integrity' in self.qa_report:
                    f.write(f"\nJoin Integrity:\n")
                    for table, stats in self.qa_report['join_integrity'].items():
                        f.write(f"  {table}: {stats['match_percentage']}% of records matched to plays\n")

                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF REPORT\n")

            print(f"✓ QA report saved to {output_file}")
        except Exception as e:
            print(f"✗ Failed to export QA report: {e}")

    def run(self):
        """Run the complete pipeline"""
        print("\n" + "=" * 80)
        print("NFL ANALYTICS DATA INGESTION PIPELINE")
        print("=" * 80)

        try:
            # Connect to DuckDB
            self.connect_db()

            # Load raw CSV tables
            self.load_raw_tables()

            # Build data dictionary
            self.build_data_dictionary()

            # Export to Parquet
            self.export_to_parquet()

            # Create canonical views
            self.create_canonical_views()

            # Run QA checks
            self.run_data_quality_checks()

            # Verify database
            self.verify_database()

            # Export results
            self.export_data_dictionary()
            self.export_qa_report()

            print("\n" + "=" * 80)
            print("PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 80)
            print(f"Database: {DB_PATH}")
            print(f"Parquet files: {OUTPUT_DIR}/*.parquet")
            print(f"Data dictionary: {OUTPUT_DIR}/data_dictionary.json")
            print(f"QA report: {OUTPUT_DIR}/data_qa_report.txt")
            print("=" * 80 + "\n")

        except Exception as e:
            print(f"\nFATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close_db()


if __name__ == "__main__":
    pipeline = NFLDataPipeline()
    pipeline.run()
