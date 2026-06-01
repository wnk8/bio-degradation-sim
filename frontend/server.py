"""Lokaler JSON-API-Server auf Port 8765 für das PET-Abbau-Dashboard."""

import sys
import os
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.ode_solver import solve_degradation
from simulation.monte_carlo import run_monte_carlo
from simulation.parameter_space import generate_parameter_grid
from simulation.results import aggregate_results

FRONTEND_DIR = os.path.dirname(__file__)
PORT = 8765

DEFAULT_PARAMS = {
    "vmax_petase": 0.026,
    "km_petase": 0.15,
    "ea_petase": 50000,
    "vmax_mhetase": 0.083,
    "km_mhetase": 0.21,
    "ea_mhetase": 48000,
    "pet0": 1.0,
    "mhet0": 0.0,
}


def _parse_query(query_string: str) -> dict:
    return {k: v[0] for k, v in urllib.parse.parse_qs(query_string).items()}


def _simulate_endpoint(query: dict) -> dict:
    temp = float(query.get("temp", 30.0))
    ph = float(query.get("ph", 7.0))
    runs = int(query.get("runs", 500))
    pet0 = float(query.get("pet0", 1.0))

    params = {**DEFAULT_PARAMS, "temp_celsius": temp, "ph": ph, "pet0": pet0}

    ode_result = solve_degradation(params)

    mc_df = run_monte_carlo(params, n_runs=runs)
    agg = aggregate_results(mc_df)

    return {
        "ode": {
            "t": ode_result["t"].tolist(),
            "PET": ode_result["PET"].tolist(),
            "MHET": ode_result["MHET"].tolist(),
            "TPA": ode_result["TPA"].tolist(),
        },
        "monte_carlo": {
            "mean_final_tpa": agg["mean_final_tpa"],
            "ci_95_lower": agg["ci_95_lower"],
            "ci_95_upper": agg["ci_95_upper"],
            "max_rate": agg["max_rate"],
            "mean_max_rate": agg["mean_max_rate"],
            "mean_t_half": agg["mean_t_half"],
            "n_valid": agg["n_valid"],
        },
        "params": {"temp": temp, "ph": ph, "runs": runs, "pet0": pet0},
    }


def _heatmap_endpoint(query: dict) -> dict:
    runs = int(query.get("runs", 50))
    temps = list(range(20, 65, 5))   # 20,25,...,60 °C
    phs = [5.0, 6.0, 7.0, 8.0, 9.0]

    grid = generate_parameter_grid(temps, phs, base_params=DEFAULT_PARAMS)

    heatmap = []
    for entry in grid:
        params = {**entry, "pet0": 1.0, "mhet0": 0.0}
        try:
            mc_df = run_monte_carlo(params, n_runs=runs)
            agg = aggregate_results(mc_df)
            rate = agg["mean_max_rate"]
        except Exception:
            rate = 0.0
        heatmap.append({
            "temp": entry["grid_temp"],
            "ph": entry["grid_ph"],
            "rate": rate if rate == rate else 0.0,  # NaN → 0
        })

    return {"heatmap": heatmap, "temps": temps, "phs": phs}


class SimHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Unterdrückt Standard-Zugriffslog

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: str, content_type: str) -> None:
        try:
            with open(path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_error(404, "Not Found")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = _parse_query(parsed.query)

        if path == "/" or path == "/index.html":
            self._send_file(os.path.join(FRONTEND_DIR, "index.html"), "text/html; charset=utf-8")
        elif path == "/sim.js":
            self._send_file(os.path.join(FRONTEND_DIR, "sim.js"), "application/javascript")
        elif path == "/api/simulate":
            try:
                result = _simulate_endpoint(query)
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
        elif path == "/api/heatmap":
            try:
                result = _heatmap_endpoint(query)
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
        else:
            self.send_error(404, "Not Found")


def run_server(port: int = PORT) -> None:
    """Startet den lokalen Simulationsserver.

    Args:
        port: TCP-Port (Default 8765)
    """
    server = HTTPServer(("localhost", port), SimHandler)
    print(f"PET-Abbau-Dashboard: http://localhost:{port}")
    print("Stoppen mit Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer gestoppt.")
        server.server_close()


if __name__ == "__main__":
    run_server()
