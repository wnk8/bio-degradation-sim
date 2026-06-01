"""Befüllt die literature_values-Tabelle mit Literaturwerten beim ersten Start."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "simulation.db")

LITERATURE_VALUES = [
    # PETase (Yoshida et al. 2016, Science)
    ("PETase", "Vmax", 0.026, "µmol/min/mg", "Yoshida et al. 2016 (Science 351:1196)"),
    ("PETase", "Km",   0.15,  "mM",          "Yoshida et al. 2016 (Science 351:1196)"),
    ("PETase", "Ea",   50000, "J/mol",        "Yoshida et al. 2016 (Science 351:1196)"),
    # MHETase (Tournier et al. 2020, Nature)
    ("MHETase", "Vmax", 0.083, "µmol/min/mg", "Tournier et al. 2020 (Nature 580:216)"),
    ("MHETase", "Km",   0.21,  "mM",          "Tournier et al. 2020 (Nature 580:216)"),
    ("MHETase", "Ea",   48000, "J/mol",        "Tournier et al. 2020 (Nature 580:216)"),
]


def seed_literature_values(db_path: str = DB_PATH) -> bool:
    """Fügt Literaturwerte in die Datenbank ein, wenn noch nicht vorhanden.

    Args:
        db_path: Pfad zur SQLite-Datei

    Returns:
        True wenn Seeds eingefügt wurden, False wenn bereits vorhanden
    """
    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM literature_values").fetchone()[0]
        if count > 0:
            return False

        conn.executemany(
            "INSERT INTO literature_values (enzyme, parameter_name, value, unit, source) "
            "VALUES (?,?,?,?,?)",
            LITERATURE_VALUES,
        )
        conn.commit()
        return True
    finally:
        conn.close()


if __name__ == "__main__":
    inserted = seed_literature_values()
    if inserted:
        print(f"Literaturwerte eingefügt: {len(LITERATURE_VALUES)} Einträge.")
    else:
        print("Literaturwerte bereits vorhanden, übersprungen.")
