-- PET-Abbau-Simulator Datenbankschema

CREATE TABLE IF NOT EXISTS runs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp  TEXT    NOT NULL,
    temp       REAL    NOT NULL,   -- °C
    ph         REAL    NOT NULL,
    n_runs     INTEGER NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS parameters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    vmax_petase     REAL NOT NULL,   -- µmol/min/mg
    km_petase       REAL NOT NULL,   -- mM
    vmax_mhetase    REAL NOT NULL,   -- µmol/min/mg
    km_mhetase      REAL NOT NULL    -- mM
);

CREATE TABLE IF NOT EXISTS results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    mean_final_tpa  REAL,   -- mM
    ci_lower        REAL,   -- mM
    ci_upper        REAL,   -- mM
    max_rate        REAL,   -- µmol/min/mg
    mean_t_half     REAL    -- min
);

CREATE TABLE IF NOT EXISTS literature_values (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    enzyme         TEXT NOT NULL,   -- z.B. 'PETase', 'MHETase'
    parameter_name TEXT NOT NULL,   -- z.B. 'Vmax', 'Km', 'Ea'
    value          REAL NOT NULL,
    unit           TEXT NOT NULL,   -- z.B. 'µmol/min/mg', 'mM', 'J/mol'
    source         TEXT NOT NULL    -- z.B. 'Yoshida et al. 2016'
);
