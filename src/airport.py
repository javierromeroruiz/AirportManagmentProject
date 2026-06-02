# =============================================================================
# airport.py — Base de datos de aeropuertos
#
# Se gestionan aeropuertos: codigo ICAO, coordenadas y si pertenecen al espacio
# Schengen. Las funciones principales van arriba; al final hay ayudas para
# graficos y guardar archivos (EXTRA).
# =============================================================================

import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

CHART = {
    "primary": "#2d6a4f",
    "primary_light": "#52b788",
    "secondary": "#40916c",
    "accent": "#95d5b2",
    "schengen": "#2d6a4f",
    "non_schengen": "#e76f51",
    "neutral": "#6c757d",
    "bg": "#f8f9fa",
    "grid": "#dee2e6",
    "text": "#1b4332",
    "muted": "#6c757d",
}

SCHENGEN_PREFIXES = [
    "LO", "EB", "LK", "LC", "EK", "EE", "EF", "LF", "ED", "LG", "EH", "LH",
    "BI", "LI", "EV", "EY", "EL", "LM", "EN", "EP", "LP", "LZ", "LJ", "LE", "ES", "LS",
]


# ===============================================================
#  FUNCIONES PROYECTO
# ===============================================================


class Airport:
    """Representa un aeropuerto con codigo, latitud, longitud y bandera Schengen."""

    def __init__(self, code, lat, lon):
        self.code = code
        self.lat = lat
        self.lon = lon
        self.schengen = False


def IsSchengenAirport(code):
    """
    Mira las dos primeras letras del codigo del aeropuerto (por ejemplo LE de LEBL).
    Si esa pareja esta en la lista SCHENGEN_PREFIXES, el aeropuerto se considera Schengen.
    Si el codigo es corto o vacio, se devuelve falso.
    """
    if not code or len(code) < 2:
        return False
    return code[:2] in SCHENGEN_PREFIXES


def SetSchengen(airport):
    """
    Llama a IsSchengenAirport con el codigo del aeropuerto recibido
    y guarda el resultado en airport.schengen (verdadero o falso).
    """
    airport.schengen = IsSchengenAirport(airport.code)


def PrintAirport(airport):
    """Muestra por pantalla los datos basicos de un aeropuerto (pruebas)."""
    print("Code:", airport.code)
    print("Latitude:", airport.lat)
    print("Longitude:", airport.lon)
    print("Schengen:", airport.schengen)


def LoadAirports(filename):
    """
    Se abre el archivo indicado y se lee linea a linea.
    Cada linea valida tiene tres partes: codigo de 4 letras, latitud y longitud en texto
    (letra N/S o E/W mas grados, minutos y segundos pegados, por ejemplo N4138).
    Esas coordenadas se pasan a numeros decimales para guardarlas en el objeto Airport.
    La primera linea de cabecera (Code...) y las lineas mal formadas se ignoran.
    Si el archivo no existe, se devuelve una lista vacia.
    """
    if not os.path.exists(filename):
        return []

    airports = []

    with open(filename, "r") as file:
        line = file.readline()

        while line:
            parts = line.split()
            if len(parts) == 3 and parts[0] != "Code" and len(parts[0]) == 4:
                code = parts[0]
                lat_str = parts[1]
                lon_str = parts[2]

                try:
                    lat_dir = lat_str[0]
                    lat_deg = float(lat_str[1:-4])
                    lat_min = float(lat_str[-4:-2])
                    lat_sec = float(lat_str[-2:])

                    lat_dec = lat_deg + (lat_min / 60) + (lat_sec / 3600)
                    if lat_dir == "S":
                        lat_dec = -lat_dec

                    lon_dir = lon_str[0]
                    lon_deg = float(lon_str[1:-4])
                    lon_min = float(lon_str[-4:-2])
                    lon_sec = float(lon_str[-2:])

                    lon_dec = lon_deg + (lon_min / 60) + (lon_sec / 3600)
                    if lon_dir == "W":
                        lon_dec = -lon_dec

                    airports.append(Airport(code, lat_dec, lon_dec))

                except (ValueError, IndexError):
                    pass
            line = file.readline()

    return airports


def SaveSchengenAirports(airports, filename):
    """
    Se recorre la lista de aeropuertos y solo se escriben los que tienen schengen = verdadero.
    Cada linea del archivo nuevo lleva codigo y coordenadas en formato DMS (como al cargar).
    Primero se escribe la linea de cabecera CODE LAT LON.
    Devuelve 0 si el archivo se pudo crear; -1 si la lista estaba vacia o hubo error al escribir.
    """
    if not airports:
        return -1

    try:
        with open(filename, "w") as file:
            file.write("CODE LAT LON\n")

            for airport in airports:
                if airport.schengen:
                    lat_str = DecToDmsStr(airport.lat, is_latitude=True)
                    lon_str = DecToDmsStr(airport.lon, is_latitude=False)
                    file.write(f"{airport.code} {lat_str} {lon_str}\n")

        return 0

    except IOError:
        return -1


def AddAirport(airports, airport):
    """
    Se comprueba si ya hay un aeropuerto con el mismo codigo en la lista.
    Si no existe, se anade el nuevo al final; si ya existia, no se hace nada.
    """
    for existing in airports:
        if existing.code == airport.code:
            return
    airports.append(airport)


def RemoveAirport(airports, code):
    """
    Se busca en la lista el aeropuerto cuyo codigo coincide con el indicado.
    Si se encuentra, se elimina de la lista y se devuelve 0.
    Si se recorre toda la lista sin encontrarlo, se devuelve -1.
    """
    i = 0
    while i < len(airports):
        if airports[i].code == code:
            airports.pop(i)
            return 0
        i += 1
    return -1


def PlotAirports(airports):
    """
    Primero se cuentan cuantos aeropuertos tienen schengen verdadero y cuantos no.
    Con esos dos numeros se dibuja una sola columna apilada (abajo Schengen, arriba no Schengen).
    El grafico se guarda como airports_stacked_bar.png en output y se muestra.
    Si la lista esta vacia, solo se imprime un mensaje de error.
    """
    if not airports:
        print("Error: la lista de aeropuertos esta vacia, no se puede dibujar el grafico.")
        return

    count_schengen = 0
    count_no_schengen = 0
    i = 0
    while i < len(airports):
        if airports[i].schengen:
            count_schengen = count_schengen + 1
        else:
            count_no_schengen = count_no_schengen + 1
        i = i + 1

    SetupPlotStyle()
    fig, ax = plt.subplots(figsize=(7, 5), facecolor=CHART["bg"])

    ax.bar(
        ["Aeropuertos"],
        [count_schengen],
        label="Schengen",
        color=CHART["schengen"],
        edgecolor="white",
        width=0.5,
    )
    ax.bar(
        ["Aeropuertos"],
        [count_no_schengen],
        bottom=[count_schengen],
        label="No Schengen",
        color=CHART["non_schengen"],
        edgecolor="white",
        width=0.5,
    )

    ax.set_ylabel("Numero de aeropuertos")
    ax.set_title("Aeropuertos Schengen vs No Schengen (stacked bar)")
    ax.legend(loc="upper right")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis="y", alpha=0.4)
    fig.tight_layout()
    SaveAndShow(fig, "airports_stacked_bar.png")


def MapAirports(airports, filename):
    """
    Se crea un archivo de texto en formato KML (para Google Earth u otro visor de mapas).
    Por cada aeropuerto se escribe un punto con su nombre y coordenadas.
    Los Schengen llevan un color de pin y los no Schengen otro.
    Devuelve 0 si se escribio bien; -1 si no habia aeropuertos o fallo el guardado.
    """
    if not airports:
        return -1
    try:
        with open(filename, "w") as file:
            file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            file.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
            file.write("<Document>\n")

            for airport in airports:
                pin_color = "ffff0000" if airport.schengen else "ff0000ff"

                file.write("  <Placemark>\n")
                file.write(f"    <name>{airport.code}</name>\n")
                file.write("    <Style>")
                file.write("      <IconStyle>\n")
                file.write(f"        <color>{pin_color}</color>\n")
                file.write("      </IconStyle>\n")
                file.write("    </Style>")
                file.write("    <Point>\n")
                file.write(
                    f"      <coordinates>{airport.lon},{airport.lat}</coordinates>\n"
                )
                file.write("    </Point>\n")
                file.write("  </Placemark>\n")

            file.write("</Document>\n")
            file.write("</kml>\n")

        return 0
    except IOError:
        return -1


#  Que aporta el bloque EXTRA (resumen)
#
#  PlotAirports (barras Schengen / no Schengen) queda arriba. Las funciones de
#  abajo mejoran la presentacion: colores, guardar figuras en output/ y convertir
#  coordenadas decimales a texto DMS al exportar Schengen.

# ===============================================================
#  FUNCIONES EXTRAS
# ===============================================================


def EnsureOutputDir():
    """Si no existe la carpeta output en el proyecto, se crea en disco."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def SetupPlotStyle():
    """Define colores y fuentes por defecto para los graficos de airport.py (EXTRA)."""
    plt.rcParams.update(
        {
            "figure.facecolor": CHART["bg"],
            "axes.facecolor": "white",
            "axes.edgecolor": CHART["grid"],
            "axes.labelcolor": CHART["text"],
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "axes.labelweight": "medium",
            "xtick.color": CHART["muted"],
            "ytick.color": CHART["muted"],
            "grid.color": CHART["grid"],
            "grid.linestyle": "-",
            "grid.alpha": 0.55,
            "font.family": "sans-serif",
            "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial", "Helvetica"],
            "legend.framealpha": 0.95,
            "legend.edgecolor": CHART["grid"],
        }
    )


def StyleAxes(ax, *, title, subtitle=None, xlabel=None, ylabel=None):
    """Aplica titulo y etiquetas con estilo uniforme a un eje de matplotlib."""
    ax.set_title(title, loc="left", color=CHART["text"], pad=14, fontsize=13, fontweight="bold")
    if subtitle:
        ax.text(
            0.0, 1.02, subtitle,
            transform=ax.transAxes,
            fontsize=9, color=CHART["muted"], va="bottom",
        )
    if xlabel:
        ax.set_xlabel(xlabel, color=CHART["text"], labelpad=8)
    if ylabel:
        ax.set_ylabel(ylabel, color=CHART["text"], labelpad=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(CHART["grid"])
    ax.spines["bottom"].set_color(CHART["grid"])
    ax.tick_params(colors=CHART["muted"], labelsize=9)
    ax.set_axisbelow(True)


def BarValueLabels(ax, bars, fmt="{:.0f}", offset=0.03, horizontal=False):
    """Escribe el valor numerico sobre cada barra del grafico."""
    for bar in bars:
        if horizontal:
            value = bar.get_width()
            if value <= 0:
                continue
            span = ax.get_xlim()[1] or 1
            ax.text(
                value + span * offset,
                bar.get_y() + bar.get_height() / 2,
                fmt.format(value),
                ha="left", va="center",
                fontsize=8, color=CHART["text"], fontweight="medium",
            )
        else:
            value = bar.get_height()
            if value <= 0:
                continue
            span = ax.get_ylim()[1] or 1
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + span * offset,
                fmt.format(value),
                ha="center", va="bottom",
                fontsize=8, color=CHART["text"], fontweight="medium",
            )


def SaveAndShow(fig, filename):
    """Guarda la figura en output/ y la muestra con plt.show()."""
    EnsureOutputDir()
    fig.savefig(
        os.path.join(OUTPUT_DIR, filename),
        dpi=160,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    plt.show()


def DecToDmsStr(value, is_latitude):
    """
    Pasa grados decimales a texto DMS (N4138, E00204) para guardar en archivo.
    Se separa en grados enteros, minutos y segundos y se elige N/S o E/W segun el signo.
    """
    if is_latitude:
        if value >= 0:
            direction = "N"
        else:
            direction = "S"
            value = -value
        deg_width = 2
    else:
        if value >= 0:
            direction = "E"
        else:
            direction = "W"
            value = -value
        deg_width = 3

    degrees = int(value)
    temp = (value - degrees) * 60
    minutes = int(temp)
    seconds = int(round((temp - minutes) * 60))

    str_deg = str(degrees).zfill(deg_width)
    str_min = str(minutes).zfill(2)
    str_sec = str(seconds).zfill(2)
    return direction + str_deg + str_min + str_sec
