# Gestión de Aeropuertos y Vuelos — LEBL

Aplicación académica para gestionar bases de datos de aeropuertos, analizar vuelos de llegada y salida, y simular la asignación de puertas en el aeropuerto **LEBL** (Barcelona-El Prat). Incluye interfaz gráfica (Tkinter), gráficos con Matplotlib y exportación a Google Earth (KML).

## Requisitos

- **Python 3.x**
- **matplotlib** — gráficos y exportación PNG
- **tkinter** — interfaz gráfica (suele venir con Python en Windows)

Instalación de dependencias (si hace falta):

```bash
pip install matplotlib
```

## Estructura del proyecto

```
AirportManagmentProject-Version-4/
├── README.md
├── .gitignore
├── interfaz.py          # Punto de entrada de la aplicación (GUI)
├── forest-light.tcl     # Tema visual de la interfaz
├── src/                 # Módulos Python
│   ├── airport.py       # Aeropuertos, Schengen, mapas 2D
│   ├── aircraft.py      # Vuelos, gráficos, KML de rutas, simulación
│   ├── LEBL.py          # Estructura del aeropuerto y puertas
│   └── test_airport.py  # Script de prueba (legacy)
├── data/                # Ficheros de entrada (no modificar en ejecución normal)
│   ├── Airports.txt
│   ├── Arrivals.txt
│   ├── Departures.txt
│   ├── Terminals.txt
│   ├── T1_Airlines.txt
│   └── T2_Airlines.txt
└── output/              # Artefactos generados por la aplicación
    ├── .gitkeep
    ├── flights.kml      # Mapa de vuelos (generado por MapFlights)
    └── …                # PNG, exportaciones de usuario, etc.
```

| Carpeta / archivo | Uso |
|-------------------|-----|
| `data/` | Datos de entrada oficiales del proyecto |
| `output/` | Gráficos PNG, KML y exportaciones guardadas |
| `src/` | Lógica de negocio; no guardar salidas aquí |

## Cómo ejecutar la aplicación

**Importante:** hay que ejecutar siempre desde la **raíz del proyecto**. El código crea `output/` y carga `forest-light.tcl` respecto al directorio de trabajo actual.

```bash
cd AirportManagmentProject-Version-4
python interfaz.py
```

Si se ejecuta desde otra carpeta, los gráficos y el KML pueden generarse en rutas incorrectas y el tema visual puede no cargarse.

### Uso recomendado en la GUI

1. **Base de datos:** cargar `data/Airports.txt` → aplicar Schengen → gráficos o exportar KML.
2. **Vuelos:** cargar `data/Arrivals.txt` y `data/Departures.txt` → combinar movimientos → análisis y mapas.
3. **LEBL:** cargar `data/Terminals.txt` → asignar puertas y simular ocupación diaria.

Al guardar ficheros desde los diálogos, conviene usar la carpeta `output/`.

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

Listas de aerolíneas (códigos ICAO) asociadas a cada terminal; se cargan automáticamente al leer `Terminals.txt`.

## Salidas automáticas en `output/`

Al generar gráficos desde la aplicación, se guardan PNG en `output/`:

| Archivo | Función |
|---------|---------|
| `airports_overview.png` | Mapa 2D y distribución Schengen de aeropuertos |
| `arrivals_distribution.png` | Llegadas por hora |
| `cantidad_airlines.png` | Vuelos por aerolínea |
| `schengen_distribution.png` | Origen Schengen / no Schengen |
| `day_occupancy_simulation.png` | Simulación de ocupación de puertas en LEBL |
| `flights.kml` | Rutas de vuelos hacia LEBL (Google Earth) |

Las exportaciones manuales (Schengen, vuelos, KML de aeropuertos) se guardan en la ruta que elijas en el diálogo; se recomienda `output/`.

## Tests

El script `src/test_airport.py` espera `Airports.txt` en el directorio desde el que se ejecuta. Para ejecutarlo:

```bash
cd src
python test_airport.py
```

Necesitas una copia de `data/Airports.txt` como `src/Airports.txt` (puedes copiarla desde `data/` si no existe). El test puede generar `SchengenAirports.txt` y `Mapa.kml` en `src/`; conviene moverlos a `output/` después de ejecutarlo.

## Módulos

| Módulo | Responsabilidad |
|--------|-----------------|
| `interfaz.py` | Ventana principal, pestañas y enlace con el resto de módulos |
| `src/airport.py` | Clase `Airport`, carga/guardado, Schengen, gráficos y KML de aeropuertos |
| `src/aircraft.py` | Clase `Aircraft`, llegadas/salidas, fusión de movimientos, KML de vuelos, simulación diaria |
| `src/LEBL.py` | Estructura de terminales, áreas y puertas; asignación de gates |

## Limitaciones conocidas

- Las rutas `output/` y `forest-light.tcl` son **relativas al directorio de trabajo**; la aplicación debe lanzarse desde la raíz del proyecto.
- `MapFlights` escribe siempre en `output/flights.kml` (ruta fija en el código).
- `LEBL.py` usa `from airport import …` (pensado para ejecutar tests desde `src/`), mientras que la GUI importa `from src.airport import …`.

## Licencia / autoría

Proyecto académico de gestión aeroportuaria. Consulta la documentación del curso para requisitos de entrega.
