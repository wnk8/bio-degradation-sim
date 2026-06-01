# PET-Abbau-Simulator — Claude-Kontext

## Projektübersicht
Lokaler wissenschaftlicher Simulator für den enzymatischen Abbau von PET-Plastik
durch PETase und MHETase. Basiert auf gekoppelten Michaelis-Menten-ODEs mit
Arrhenius-Temperaturkorrektur und Monte-Carlo-Analyse (N=500).

## Wissenschaftliche Grundlage
- Literaturwerte: Yoshida et al. 2016 (Science), Tournier et al. 2020 (Nature)
- PETase:  Vmax=0.026 µmol/min/mg, Km=0.15 mM, Ea=50000 J/mol
- MHETase: Vmax=0.083 µmol/min/mg, Km=0.21 mM, Ea=48000 J/mol
- ODE-System: PET → MHET → TPA (Terephthalat)
- Massenerhalt muss stets gewährleistet sein: PET+MHET+TPA ≈ const (±1%)

## Reaktionsschema
```
Reaktion 1 (PETase):  PET  --[PETase]-->  MHET
Reaktion 2 (MHETase): MHET --[MHETase]--> TPA + EG

d[PET]/dt  = -v1
d[MHET]/dt =  v1 - v2
d[TPA]/dt  =  v2

v1 = (Vmax_PETase  * [PET])  / (Km_PETase  + [PET])  * f_Arrhenius(T)
v2 = (Vmax_MHETase * [MHET]) / (Km_MHETase + [MHET]) * f_Arrhenius(T)
f(T) = exp(-Ea / (R * T)),  T in Kelvin, R = 8.314 J/mol·K
```

## Architektur-Regeln
- `core/` — reine Funktionen, keine Seiteneffekte, keine I/O
- `simulation/` — baut auf `core/` auf, gibt pandas DataFrames zurück
- `data/` — nur sqlite3, kein ORM, alle SQL-Statements explizit in db.py
- `frontend/` — kein Build-Tool, reines HTML/JS mit Chart.js CDN
- `tests/` — pytest, keine Mocks für numerische Berechnungen

## Entwicklungsrichtlinien
- Alle Funktionen haben Type Hints und Docstrings mit Parametereinheiten
- Keine externen Cloud-APIs — alles lokal, 0 € Kosten
- Temperatur intern immer in Kelvin (Eingabe °C, Konvertierung in arrhenius.py)
- pH-Effekt: Gauss-Kurve mit Optimum bei pH 7.0, sigma=1.0
  `f_pH = exp(-0.5 * ((pH - 7.0) / 1.0)**2)`
- Monte-Carlo-Streuung: numpy.random.normal mit ±15% (sigma = 0.15 * mu)
- Konfidenzintervalle: scipy.stats.norm.interval(0.95, loc=mean, scale=sem)

## Standardparameter
```python
DEFAULT_PARAMS = {
    "vmax_petase":  0.026,   # µmol/min/mg
    "km_petase":    0.15,    # mM
    "ea_petase":    50000,   # J/mol
    "vmax_mhetase": 0.083,   # µmol/min/mg
    "km_mhetase":   0.21,    # mM
    "ea_mhetase":   48000,   # J/mol
    "temp_celsius": 30.0,    # °C
    "ph":           7.0,
    "pet0":         1.0,     # mM (Anfangskonzentration PET)
    "mhet0":        0.0,     # mM
}
```

## Abhängigkeiten
numpy, scipy, matplotlib, pandas — alle via pip, keine kommerziellen Pakete.
sqlite3 ist Python-stdlib, kein separater Install nötig.

## CLI-Einstieg
```bash
cd bio-degradation-sim
pip install -r requirements.txt
python main.py --temp 30 --ph 7.0 --runs 500
python frontend/server.py        # http://localhost:8765
python -m pytest tests/ -v
```

## Bekannte Grenzen
- pH-Modell ist vereinfacht (empirische Gauss-Kurve, kein Henderson-Hasselbalch)
- Enzymkonzentration wird als konstant angenommen (keine Produktinhibierung)
- ODE-Löser: RK45 mit scipy.integrate.solve_ivp, t_span=(0, 120) Minuten
- EG (Ethylenglykol) wird nicht separat verfolgt (nur TPA als Endprodukt)
