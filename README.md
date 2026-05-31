# Gestión de Aeropuertos y Vuelos — LEBL

Programa para gestionar bases de datos de aeropuertos, analizar vuelos de llegada y salida y simular la asignación de puertas en el aeropuerto **LEBL** (Barcelona-El Prat). Incluye interfaz gráfica, gráficos embebidos, exportación a Google Earth y animación de operaciones en el mapa del aeropuerto.

Basado en el enunciado del proyecto (*ProjectoAeropuerto.pdf*), organizado en cuatro versiones (V1–V4).

## Requisitos

- **Python 3.x**
- **matplotlib** — gráficos y exportación PNG
- **tkinter** — interfaz gráfica (suele venir con Python en Windows)

```bash
pip install matplotlib
```

## Estructura del proyecto

```
tests/
├── README.md
├── .gitignore
├── interfaz.py              # Punto de entrada (GUI)
├── src/
│   ├── airport.py           # V1 — Aeropuertos, Schengen, mapas 2D/KML
│   ├── aircraft.py          # V2 + V4 — Vuelos, merge, puertas, animación LEBL
│   ├── LEBL.py              # V3 — Estructura del aeropuerto y puertas
│   └── test_airport.py      # Script de prueba manual (legacy)
├── data/                    # Ficheros de entrada
│   ├── Airports.txt
│   ├── Arrivals.txt
│   ├── Departures.txt
│   ├── Terminals.txt
│   ├── T1_Airlines.txt
│   ├── T2_Airlines.txt
│   ├── forest-light.tcl     # Tema visual de la interfaz
│   ├── lebl_pdc_aip.txt     # Datos AIP de stands LEBL (animación)
│   └── LEBL_Taxiways.txl     # Rutas de taxiways (animación)
└── output/                  # Artefactos generados
    ├── flights.kml
    └── *.png
```

| Carpeta / archivo | Uso |
|-------------------|-----|
| `data/` | Datos de entrada oficiales del proyecto |
| `output/` | Gráficos PNG, KML y exportaciones |
| `src/` | Lógica del proyecto (módulos Python) |

## Cómo ejecutar

Ejecutar siempre desde la **raíz del proyecto** (`tests/`):

```bash
cd tests
python interfaz.py
```

Al arrancar, la aplicación precarga las rutas por defecto de `data/` (`Airports.txt`, `Arrivals.txt`, `Departures.txt`, `Terminals.txt`) y carga la base de aeropuertos en memoria si el fichero existe.

### Uso recomendado en la GUI

1. **Base de datos (V1):** cargar `data/Airports.txt` → aplicar Schengen → gráficos o exportar KML.
2. **Vuelos (V2):** cargar `data/Arrivals.txt` y `data/Departures.txt` → gráficos, KML de rutas, vuelos > 2000 km.
3. **LEBL (V3):** cargar `data/Terminals.txt` → ver ocupación de puertas → asignar gates.
4. **Simulación (V4):** combinar movimientos → aviones nocturnos → asignar puertas nocturnas → gráfico de ocupación diaria.
5. **Animación (extra):** en la pestaña LEBL, pulsar **Animar Llegadas Y Salidas**. La animación se muestra en Canvas dentro de la pestaña *Animación* (requiere estructura LEBL + `Arrivals.txt`; `Departures.txt` opcional).

Al guardar ficheros desde los diálogos, conviene usar la carpeta `output/`.

## Organización del código

Cada módulo principal está dividido en dos bloques con comentarios de sección:

| Sección | Contenido |
|---------|-----------|
| **FUNCIONES PROYECTO** | Clases y funciones exigidas en el enunciado (PDF) |
| **FUNCIONES EXTRAS** | Utilidades internas, gráficos embebidos, animación LEBL, helpers de la GUI |

### V1 — `src/airport.py`

| Tipo | Nombre |
|------|--------|
| Clase | `Airport` |
| Funciones | `IsSchengenAirport`, `SetSchengen`, `PrintAirport`, `LoadAirports`, `SaveSchengenAirports`, `AddAirport`, `RemoveAirport`, `PlotAirports`, `MapAirports` |

### V2 — `src/aircraft.py`

| Tipo | Nombre |
|------|--------|
| Clase | `Aircraft` |
| Funciones | `LoadArrivals`, `PlotArrivals`, `SaveFlights`, `PlotAirlines`, `PlotFlightsType`, `MapFlights`, `LongDistanceArrivals` |

### V3 — `src/LEBL.py`

| Tipo | Nombre |
|------|--------|
| Clases | `BarcelonaAP`, `Terminal`, `BoardingArea`, `Gate` |
| Funciones | `SetGates`, `LoadAirlines`, `LoadAirportStructure`, `GateOccupancy`, `IsAirlineInTerminal`, `SearchTerminal`, `AssignGate` |

### V4 — `src/aircraft.py`

| Funciones |
|-----------|
| `LoadDepartures`, `MergeMovements`, `NightAircraft`, `AssignNightGates`, `FreeGate`, `AssignGatesAtTime`, `PlotDayOccupancy` |

### Interfaz — `interfaz.py`

Conecta la GUI con las funciones anteriores. Las **FUNCIONES EXTRAS** incluyen el panel de gráficos embebidos, tooltips, carga automática de datos, animación LEBL y cierre limpio de la aplicación.

Principales extras en `src/aircraft.py`: `GenerateLEBLAnimation`, `create_lebl_animation_widget`, `prepare_operations`, `merge_arrivals_departures`, `TaxiGraph`, `FlightRecord`, y la variante `LoadAirports` que devuelve un diccionario ICAO→coordenadas (soporte de `MapFlights`).

## Formato de los ficheros en `data/`

### `Airports.txt`

```
CODE LAT LON
EBBR N505405 E0042904
...
```

- **CODE:** código ICAO de 4 letras.
- **LAT / LON:** coordenadas en formato DMS (dirección + grados + minutos + segundos).

### `Arrivals.txt` y `Departures.txt`

```
AIRCRAFT ORIGIN ARRIVAL AIRLINE
ECMKV LYBE 00:04 VLG
...
```

- **AIRCRAFT:** matrícula (5–6 caracteres).
- **ORIGIN / DESTINATION:** aeropuerto ICAO de origen o destino.
- **ARRIVAL / DEPARTURE:** hora `HH:MM`.
- **AIRLINE:** código de aerolínea.

### `Terminals.txt`

Describe la estructura de LEBL: terminales (T1, T2), áreas Schengen / non-Schengen y rangos de puertas.

### `T1_Airlines.txt` y `T2_Airlines.txt`

Listas de aerolíneas asociadas a cada terminal; se cargan automáticamente al leer `Terminals.txt`.

## Salidas en `output/`

| Archivo | Origen |
|---------|--------|
| `airports_overview.png` | `PlotAirports` |
| `arrivals_distribution.png` | `PlotArrivals` |
| `cantidad_airlines.png` | `PlotAirlines` |
| `schengen_distribution.png` | `PlotFlightsType` |
| `day_occupancy_simulation.png` | `PlotDayOccupancy` |
| `flights.kml` | `MapFlights` |
| `SchengenAirports.txt` | Exportación manual desde la GUI |

Las exportaciones manuales (Schengen, vuelos, KML de aeropuertos) se guardan en la ruta elegida en el diálogo.

## Tests

Script manual en `src/test_airport.py`:

```bash
cd src
python test_airport.py
```

Usa `data/Airports.txt` y escribe en `output/`. Pensado para probar las funciones de V1 de forma aislada.

## Limitaciones conocidas

- La aplicación debe lanzarse desde la raíz del proyecto para que `data/` y `output/` resuelvan correctamente.
- `MapFlights` escribe siempre en `output/flights.kml`.
- `MergeMovements` empareja llegadas y salidas del mismo día y también pares nocturnos (llegada ≥ 18:00, salida ≤ 09:00).
- La animación LEBL no forma parte del enunciado; se renderiza en Canvas (tkinter) con `lebl_pdc_aip.txt` y `LEBL_Taxiways.txl` en `data/`.
- Sin `Departures.txt`, la animación muestra solo llegadas (no genera salidas aleatorias).
