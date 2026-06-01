"""SQLite-Datenbankzugriff für den PET-Abbau-Simulator."""

import sqlite3
import os
from datetime import datetime
from typing import Any

DB_PATH = os.path.join(os.path.dirname(__file__), "simulation.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


class SQLiteManager:
    """Verwaltet alle Datenbankoperationen via sqlite3 (kein ORM).

    Args:
        db_path: Pfad zur SQLite-Datei (Default: data/simulation.db)
    """

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        """Legt Tabellen an, falls noch nicht vorhanden."""
        with open(SCHEMA_PATH, "r") as f:
            schema = f.read()
        with self._connect() as conn:
            conn.executescript(schema)

    def save_run(
        self,
        run_meta: dict[str, Any],
        params: dict[str, Any],
        results: dict[str, Any],
    ) -> int:
        """Speichert einen Simulations-Run in der Datenbank.

        Args:
            run_meta: Dict mit Keys temp (°C), ph, n_runs
            params: Dict mit Keys vmax_petase, km_petase, vmax_mhetase, km_mhetase
            results: Dict aus aggregate_results() mit Keys
                     mean_final_tpa, ci_95_lower, ci_95_upper, max_rate, mean_t_half

        Returns:
            ID des neu angelegten run-Eintrags (int)
        """
        ts = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO runs (timestamp, temp, ph, n_runs, created_at) VALUES (?,?,?,?,?)",
                (ts, run_meta["temp"], run_meta["ph"], run_meta["n_runs"], ts),
            )
            run_id = cur.lastrowid

            conn.execute(
                "INSERT INTO parameters (run_id, vmax_petase, km_petase, vmax_mhetase, km_mhetase) "
                "VALUES (?,?,?,?,?)",
                (
                    run_id,
                    params["vmax_petase"],
                    params["km_petase"],
                    params["vmax_mhetase"],
                    params["km_mhetase"],
                ),
            )

            conn.execute(
                "INSERT INTO results (run_id, mean_final_tpa, ci_lower, ci_upper, max_rate, mean_t_half) "
                "VALUES (?,?,?,?,?,?)",
                (
                    run_id,
                    results.get("mean_final_tpa"),
                    results.get("ci_95_lower"),
                    results.get("ci_95_upper"),
                    results.get("max_rate"),
                    results.get("mean_t_half"),
                ),
            )
            conn.commit()
        return run_id

    def get_runs(self, limit: int = 50) -> list[dict]:
        """Gibt die letzten N Simulations-Runs zurück.

        Args:
            limit: Maximale Anzahl Einträge (Default 50)

        Returns:
            Liste von Dicts mit run-Metadaten + Ergebnissen
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT r.id, r.timestamp, r.temp, r.ph, r.n_runs,
                       res.mean_final_tpa, res.ci_lower, res.ci_upper,
                       res.max_rate, res.mean_t_half
                FROM runs r
                LEFT JOIN results res ON res.run_id = r.id
                ORDER BY r.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def query_optimal(self) -> dict | None:
        """Gibt den Run mit der höchsten Degradationsrate zurück.

        Returns:
            Dict mit run-Metadaten + Ergebnissen, oder None wenn keine Runs vorhanden
        """
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT r.id, r.timestamp, r.temp, r.ph, r.n_runs,
                       res.mean_final_tpa, res.ci_lower, res.ci_upper,
                       res.max_rate, res.mean_t_half
                FROM runs r
                LEFT JOIN results res ON res.run_id = r.id
                WHERE res.max_rate IS NOT NULL
                ORDER BY res.max_rate DESC
                LIMIT 1
                """
            ).fetchone()
        return dict(row) if row else None

    def is_seeded(self) -> bool:
        """Prüft, ob literature_values bereits befüllt wurde."""
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM literature_values").fetchone()[0]
        return count > 0
