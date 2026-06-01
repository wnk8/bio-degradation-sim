"""CLI-Einstieg für den PET-Abbau-Simulator.

Aufruf:
    python main.py --temp 30 --ph 7.0 --runs 500
"""

import argparse
import sys
import os

# Projektpfad in sys.path aufnehmen, damit alle Module importierbar sind
sys.path.insert(0, os.path.dirname(__file__))

from core.ode_solver import solve_degradation
from simulation.monte_carlo import run_monte_carlo
from simulation.parameter_space import generate_parameter_grid
from simulation.results import aggregate_results
from data.db import SQLiteManager
from data.seeds import seed_literature_values

DEFAULT_PARAMS = {
    "vmax_petase": 0.026,
    "km_petase": 0.15,
    "ea_petase": 50000,
    "vmax_mhetase": 0.083,
    "km_mhetase": 0.21,
    "ea_mhetase": 48000,
    "mhet0": 0.0,
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="PET-Abbau-Simulator: PETase/MHETase-Kinetik mit Monte-Carlo"
    )
    p.add_argument("--temp",  type=float, default=30.0,  help="Temperatur in °C (Default: 30)")
    p.add_argument("--ph",    type=float, default=7.0,   help="pH-Wert (Default: 7.0)")
    p.add_argument("--pet0",  type=float, default=1.0,   help="Anfangskonzentration PET in mM (Default: 1.0)")
    p.add_argument("--runs",  type=int,   default=500,   help="Anzahl Monte-Carlo-Runs (Default: 500)")
    p.add_argument("--no-db", action="store_true",        help="Ergebnis nicht in Datenbank speichern")
    p.add_argument("--no-grid", action="store_true",      help="Parameter-Grid-Suche überspringen")
    return p


def find_optimal_conditions(base_params: dict) -> tuple[float, float, float]:
    """Sucht optimale Temp/pH-Kombination via Parameter-Grid.

    Args:
        base_params: Basis-Parameterdict

    Returns:
        Tuple (optimal_temp_celsius, optimal_ph, max_rate)
    """
    temps = list(range(15, 75, 5))
    phs = [5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0]
    grid = generate_parameter_grid(temps, phs, base_params=base_params)

    best_temp = base_params["temp_celsius"]
    best_ph = base_params.get("ph", 7.0)
    best_rate = 0.0

    for entry in grid:
        params = {**entry, "pet0": base_params["pet0"]}
        try:
            mc_df = run_monte_carlo(params, n_runs=30)
            agg = aggregate_results(mc_df)
            rate = agg.get("mean_max_rate", 0.0) or 0.0
            if rate > best_rate:
                best_rate = rate
                best_temp = entry["grid_temp"]
                best_ph = entry["grid_ph"]
        except Exception:
            continue

    return best_temp, best_ph, best_rate


def print_summary(
    temp: float,
    ph: float,
    pet0: float,
    n_runs: int,
    agg: dict,
    opt_temp: float,
    opt_ph: float,
    opt_rate: float,
) -> None:
    """Gibt die formatierte Ergebnis-Zusammenfassung auf stdout aus."""
    w = 56
    line = "═" * w

    def row(label: str, value: str) -> str:
        return f"║  {label:<26}{value:<{w - 30}}║"

    def fmt(v, unit=""):
        if v is None or (isinstance(v, float) and v != v):
            return "n/a"
        return f"{v:.4e} {unit}".strip()

    print(f"\n╔{line}╗")
    print(f"║{'PET-Abbau Simulation — Zusammenfassung':^{w}}║")
    print(f"╠{line}╣")
    print(row("Simulation", f"T={temp}°C  pH={ph}  [PET]₀={pet0} mM"))
    print(row("Monte-Carlo Runs", f"{n_runs} ({agg.get('n_valid', '?')} gültig)"))
    print(f"╠{line}╣")
    print(row("Finale TPA (Mittel)", fmt(agg.get("mean_final_tpa"), "mM")))
    print(row("95%-KI finale TPA", f"[{fmt(agg.get('ci_95_lower'))}, {fmt(agg.get('ci_95_upper'))}] mM"))
    print(row("Max. Degradationsrate", fmt(agg.get("max_rate"), "µmol/min/mg")))
    print(row("Mittl. Rate (MC)", fmt(agg.get("mean_max_rate"), "µmol/min/mg")))
    print(row("Mittl. Halbwertszeit", fmt(agg.get("mean_t_half"), "min")))
    print(f"╠{line}╣")
    print(row("Optimale Temperatur", f"{opt_temp:.1f} °C"))
    print(row("Optimaler pH", f"{opt_ph:.1f}"))
    print(row("Max. Rate (Grid)", fmt(opt_rate, "µmol/min/mg")))
    print(f"╚{line}╝\n")
    print("Frontend starten: python frontend/server.py")
    print("Tests ausführen:  python -m pytest tests/ -v\n")


def main() -> None:
    args = build_parser().parse_args()

    print(f"PET-Abbau-Simulator gestartet (T={args.temp}°C, pH={args.ph}, Runs={args.runs})")

    # Datenbank initialisieren und Seeds einfügen
    db = SQLiteManager()
    if not db.is_seeded():
        seed_literature_values()
        print("Literaturwerte in DB eingefügt.")

    params = {
        **DEFAULT_PARAMS,
        "temp_celsius": args.temp,
        "ph": args.ph,
        "pet0": args.pet0,
    }

    # Monte-Carlo
    print(f"Monte-Carlo: {args.runs} Runs werden berechnet…")
    mc_df = run_monte_carlo(params, n_runs=args.runs)
    agg = aggregate_results(mc_df)

    # Optimale Bedingungen via Parameter-Grid
    if args.no_grid:
        opt_temp, opt_ph, opt_rate = args.temp, args.ph, agg.get("mean_max_rate", 0.0) or 0.0
    else:
        print("Parameter-Grid-Suche (Temp × pH)…")
        opt_temp, opt_ph, opt_rate = find_optimal_conditions(params)

    # In DB speichern
    if not args.no_db:
        run_id = db.save_run(
            run_meta={"temp": args.temp, "ph": args.ph, "n_runs": args.runs},
            params={
                "vmax_petase":  params["vmax_petase"],
                "km_petase":    params["km_petase"],
                "vmax_mhetase": params["vmax_mhetase"],
                "km_mhetase":   params["km_mhetase"],
            },
            results=agg,
        )
        print(f"Ergebnis gespeichert (Run-ID: {run_id}).")

    print_summary(
        temp=args.temp,
        ph=args.ph,
        pet0=args.pet0,
        n_runs=args.runs,
        agg=agg,
        opt_temp=opt_temp,
        opt_ph=opt_ph,
        opt_rate=opt_rate,
    )


if __name__ == "__main__":
    main()
