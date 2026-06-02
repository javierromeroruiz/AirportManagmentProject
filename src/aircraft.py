# =============================================================================
# aircraft.py — Gestion de vuelos, mapas y aeropuerto de Barcelona (LEBL)
#
# Se gestionan llegadas, salidas, graficos, mapas KML, union de movimientos,
# aviones nocturnos y simulacion de puertas. Al final hay funciones EXTRA:
# animacion del mapa con taxiways y stands.
# =============================================================================

import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
import math
import copy
from collections import defaultdict

import time
import heapq
import re
import random
import xml.etree.ElementTree as ET
from dataclasses import dataclass

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

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "output")


# ===============================================================
#  FUNCIONES PROYECTO
# ===============================================================

class Aircraft:
    """
    Guarda la informacion de un vuelo en un solo objeto.
    Incluye nombres de campos completos (id, origin, arrival, destination...)
    y alias cortos (aircraft_id, airline_company, time_of_landing...) usados
    en graficos y al guardar archivos.
    """

    def __init__(
        self,
        id_code,
        airline,
        origin="-",
        arrival="-",
        destination="-",
        departure="-",
    ):
        self.id = id_code
        self.airline = airline
        self.origin = origin if origin else "-"
        self.arrival = arrival if arrival else "-"
        self.destination = destination if destination else "-"
        self.departure = departure if departure else "-"
        self.gate = "-"
        self.aircraft_id = id_code
        self.airline_company = airline
        self.origin_airport = self.origin
        self.time_of_landing = self.arrival


def LoadArrivals(filename):
    """
    Se abre el archivo de llegadas linea a linea.
    Se buscan filas con cuatro datos: matricula, origen, hora de llegada y aerolinea.
    Si la hora no tiene formato HH:MM o faltan datos, esa linea se descarta.
    Al terminar se devuelve la lista de aviones creados.
    """
    if not os.path.exists(filename):
        return []

    aircraft = []

    with open(filename, "r") as file:
        line = file.readline()

        while line:
            parts = line.split()
            if parts and parts[0] != "AIRCRAFT" and len(parts) == 4:
                if len(parts[0]) in (5, 6) and len(parts[1]) == 4:
                    try:
                        datetime.strptime(parts[2], "%H:%M")
                        if len(parts[3]) == 3:
                            aircraft.append(
                                Aircraft(parts[0], parts[3], parts[1], parts[2])
                            )
                    except ValueError:
                        pass

            line = file.readline()

    return aircraft


def PlotArrivals(aircraft):
    """
    Primero se cuenta cuantos aviones llegan en cada hora del dia (0 a 23).
    Luego se dibuja un grafico de barras con esas cantidades.
    El resultado se guarda en output y se muestra en pantalla.
    """
    i = 0
    rangos = [0] * 24

    while i < len(aircraft):
        time = aircraft[i].time_of_landing
        if time and time != "-":
            hora = int(time.split(":")[0])
            rangos[hora] += 1
        i += 1

    horas_labels = [f"{h:02d}:00" for h in range(24)]

    plt.bar(horas_labels, rangos, color="skyblue", edgecolor="navy")
    plt.xlabel("Franja Horaria")
    plt.ylabel("Cantidad de Aviones")
    plt.title("Distribución de Llegadas por Hora")
    plt.xticks(rotation=45)
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    plt.tight_layout()
    plt.savefig(V2OutputPath("arrivals_distribution.png"))
    plt.show()


def SaveFlights(aircraft, filename):
    """
    Si la lista esta vacia, no se escribe nada y se devuelve error.
    Si hay vuelos, se crea un archivo con cabecera y una linea por avion.
    Los campos vacios se guardan como guion. Devuelve 0 si todo fue bien.
    """
    if not aircraft:
        return -1
    try:
        with open(filename, "w") as file:
            file.write("AIRCRAFT ORIGIN ARRIVAL AIRLINE\n")

            i = 0
            while i < len(aircraft):
                ac = aircraft[i]

                if ac.aircraft_id:
                    aircraft_id = ac.aircraft_id
                else:
                    aircraft_id = "-"
                if ac.airline_company:
                    airline_company = ac.airline_company
                else:
                    airline_company = "-"
                if ac.origin_airport:
                    origin_airport = ac.origin_airport
                else:
                    origin_airport = "-"
                if ac.time_of_landing:
                    time_of_landing = ac.time_of_landing
                else:
                    time_of_landing = "-"

                file.write(
                    f"{aircraft_id} {origin_airport} {time_of_landing} {airline_company}\n"
                )
                i += 1

        return 0
    except IOError:
        return -1


def PlotAirlines(aircraft):
    """
    Se recorre la lista y se cuenta cuantos vuelos tiene cada aerolinea.
    Con esos numeros se hace un grafico de barras y se guarda en output.
    """
    if not aircraft:
        return -1
    airlines = {}

    i = 0
    while i < len(aircraft):
        ac = aircraft[i]
        airline = ac.airline_company
        if airline:
            if airline in airlines:
                airlines[airline] += 1
            else:
                airlines[airline] = 1
        i += 1

    x = list(airlines.keys())
    y = list(airlines.values())

    plt.bar(x, y)
    plt.xlabel("airlines")
    plt.ylabel("Cantidad de Aviones")
    plt.title("Cantidad de aviones por Airline")
    plt.xticks(rotation=45)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(V2OutputPath("cantidad_airlines.png"))
    plt.show()

    return 0


def PlotFlightsType(aircraft):
    """
    Para cada vuelo se miran las dos primeras letras del aeropuerto de origen.
    Si estan en la lista Schengen, suma uno; si no, suma al otro grupo.
    Se dibuja una barra apilada con ambos totales.
    """
    schengen_prefixes = [
        "LO", "EB", "LK", "LC", "EK", "EE", "EF", "LF", "ED", "LG", "EH", "LH",
        "BI", "LI", "EV", "EY", "EL", "LM", "EN", "EP", "LP", "LZ", "LJ", "LE", "ES", "LS",
    ]
    if not aircraft:
        return -1

    count_schengen = 0
    count_no_schengen = 0

    i = 0
    while i < len(aircraft):
        origin = aircraft[i].origin_airport
        codigo = str(origin[:2])

        if codigo in schengen_prefixes:
            count_schengen += 1
        else:
            count_no_schengen += 1
        i += 1

    x_label = ["Origin"]
    plt.bar(x_label, [count_schengen], color="blue", label="Schengen")
    plt.bar(
        x_label,
        [count_no_schengen],
        bottom=[count_schengen],
        color="red",
        label="No Schengen",
    )
    plt.title("Schengen origin")
    plt.ylim(0, count_schengen + count_no_schengen + 10)
    plt.legend()
    plt.show()

    return 0


def MapFlights(aircraft, airports_db):
    """
    Hace falta tener Barcelona (LEBL) en el diccionario de coordenadas.
    Por cada vuelo cuyo origen este en la base, se escribe una linea en un archivo KML
    desde el origen hasta Barcelona. Color distinto si el origen es Schengen o no.
    """
    if "LEBL" not in airports_db:
        return -1

    lat_dest, lon_dest = airports_db["LEBL"]

    if not os.path.exists(_OUTPUT_DIR):
        os.makedirs(_OUTPUT_DIR)

    kml_path = os.path.join(_OUTPUT_DIR, "flights.kml")
    f = open(kml_path, "w")

    f.write("<?xml version='1.0' encoding='UTF-8'?>\n")
    f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
    f.write("<Document>\n")

    i = 0
    while i < len(aircraft):
        ac = aircraft[i]
        orig = ac.origin_airport

        if orig in airports_db:
            lat_orig, lon_orig = airports_db[orig]

            codigo = str(orig[:2])
            if codigo in SCHENGEN_PREFIXES:
                color = "ffff0000"
            else:
                color = "ff0000ff"

            f.write("   <Placemark>\n")
            f.write("   <name>" + str(ac.aircraft_id) + "</name>\n")
            f.write(
                "   <Style><LineStyle><color>"
                + color
                + "</color><width>2</width></LineStyle></Style>\n"
            )
            f.write("   <LineString>\n")
            f.write("   <coordinates>\n")
            f.write("   " + str(lon_orig) + "," + str(lat_orig) + ",0 ")
            f.write(str(lon_dest) + "," + str(lat_dest) + ",0\n")
            f.write("   </coordinates>\n")
            f.write("   </LineString>\n")
            f.write("   </Placemark>\n")

        i = i + 1

    f.write("</Document>\n")
    f.write("</kml>\n")
    f.close()

    return 0


def LongDistanceArrivals(aircraft, airports_db):
    """
    Con las coordenadas de origen y de Barcelona se calcula la distancia en km.
    A cada vuelo valido se le suma CO2 (18 kg por km) al total general.
    Los que pasan de 2000 km se guardan en una lista aparte.
    Se devuelve esa lista, el CO2 total en toneladas y la media por vuelo.
    """
    long_distance_list = []
    total_co2_kg = 0.0
    cont_flights = 0

    if "LEBL" not in airports_db:
        return long_distance_list, 0.0, 0.0

    lat_dest, lon_dest = airports_db["LEBL"]
    R = 6371.0

    i = 0
    while i < len(aircraft):
        ac = aircraft[i]
        orig = ac.origin_airport

        if orig in airports_db:
            lat_orig, lon_orig = airports_db[orig]

            lat_rad_orig = lat_orig * math.pi / 180
            lat_rad_dest = lat_dest * math.pi / 180
            diff_lat = (lat_dest - lat_orig) * math.pi / 180
            diff_lon = (lon_dest - lon_orig) * math.pi / 180

            a = (
                math.sin(diff_lat / 2) ** 2
                + math.cos(lat_rad_orig)
                * math.cos(lat_rad_dest)
                * math.sin(diff_lon / 2) ** 2
            )
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist = R * c

            total_co2_kg = (18 * dist) + total_co2_kg
            cont_flights = cont_flights + 1

            if dist > 2000:
                long_distance_list.append(ac)

        i = i + 1

    total_tons = total_co2_kg / 1000

    if cont_flights > 0:
        med_tons = total_tons / cont_flights
    else:
        med_tons = 0.0

    return long_distance_list, total_tons, med_tons


def LoadDepartures(filename):
    """
    Lee el archivo de salidas: matricula, destino, hora de salida y aerolinea.
    Cada linea valida crea un objeto Aircraft con destino y salida rellenados.
    Devuelve la lista y 0 si fue bien, o lista vacia y -1 si hubo error.
    """
    if not os.path.exists(filename):
        return [], -1

    aircrafts = []

    try:
        with open(filename, "r") as file:
            line = file.readline()

            while line:
                parts = line.split()
                if len(parts) == 4 and parts[0] != "AIRCRAFT":
                    ac_id = parts[0]
                    dest = parts[1]
                    dep_time = parts[2]
                    airline = parts[3]

                    plane = Aircraft(ac_id, airline, "", "", dest, dep_time)
                    aircrafts.append(plane)

                line = file.readline()

        return aircrafts, 0

    except IOError:
        return [], -1


def MergeMovements(arrivals, departures):
    """
    Se agrupan llegadas y salidas por la misma matricula.
    Para cada avion se empareja cada llegada con la salida mas temprana que sea despues.
    Si queda llegada sin salida el mismo dia, se intenta emparejar pernocta (tarde + manana).
    Las salidas que no se usaron se anaden solas al resultado.
    """
    if not arrivals or not departures:
        return -1

    arr_by_id = defaultdict(list)
    for ac in arrivals:
        arr_by_id[ac.id].append(ac)

    dep_by_id = defaultdict(list)
    for ac in departures:
        dep_by_id[ac.id].append(ac)

    merged_list = []
    all_ids = sorted(set(arr_by_id.keys()) | set(dep_by_id.keys()))

    for ac_id in all_ids:
        arrs = sorted(
            arr_by_id.get(ac_id, []),
            key=lambda a: TimeToMinutes(a.arrival) if TimeToMinutes(a.arrival) is not None else -1,
        )
        deps = sorted(
            dep_by_id.get(ac_id, []),
            key=lambda d: TimeToMinutes(d.departure) if TimeToMinutes(d.departure) is not None else -1,
        )
        used_dep = [False] * len(deps)
        id_merged = []

        for arr in arrs:
            merged = copy.copy(arr)
            arr_m = TimeToMinutes(arr.arrival)

            if arr_m is not None:
                best_j = -1
                best_dep_m = None
                j = 0
                while j < len(deps):
                    if not used_dep[j]:
                        dep_m = TimeToMinutes(deps[j].departure)
                        if dep_m is not None and arr_m < dep_m:
                            if best_j < 0 or dep_m < best_dep_m:
                                best_j = j
                                best_dep_m = dep_m
                    j += 1

                if best_j >= 0:
                    dep = deps[best_j]
                    used_dep[best_j] = True
                    merged.destination = dep.destination
                    merged.departure = dep.departure

            id_merged.append(merged)


        for merged in id_merged:
            if not BlankMovementTime(merged.departure):
                continue
            arr_m = TimeToMinutes(merged.arrival)
            if arr_m is None:
                continue

            best_j = -1
            best_dep_m = None
            j = 0
            while j < len(deps):
                if not used_dep[j]:
                    dep_m = TimeToMinutes(deps[j].departure)
                    if dep_m is not None and OvernightPairCompatible(arr_m, dep_m):
                        if best_j < 0 or dep_m < best_dep_m:
                            best_j = j
                            best_dep_m = dep_m
                j += 1

            if best_j >= 0:
                dep = deps[best_j]
                used_dep[best_j] = True
                merged.destination = dep.destination
                merged.departure = dep.departure

        merged_list.extend(id_merged)

        j = 0
        while j < len(deps):
            if not used_dep[j]:
                merged_list.append(copy.copy(deps[j]))
            j += 1

    return merged_list


def NightAircraft(aircrafts):
    """
    Se revisa cada movimiento: solo llegada, solo salida, o ambas horas.
    Si la salida es igual o anterior a la llegada en el mismo dia, el avion pernocta.
    Se devuelve la lista de esos aviones, o -1 si no habia datos.
    """

    if not aircrafts:
        return -1

    night_list = []
    for plane in aircrafts:
        arr_blank = BlankMovementTime(plane.arrival)
        dep_blank = BlankMovementTime(plane.departure)

        if arr_blank and not dep_blank:
            night_list.append(plane)
            continue
        if not arr_blank and dep_blank:
            night_list.append(plane)
            continue

        arr_m = TimeToMinutes(plane.arrival)
        dep_m = TimeToMinutes(plane.departure)
        if arr_m is not None and dep_m is not None and dep_m <= arr_m:
            night_list.append(plane)

    return night_list


def AssignNightGates(bcn, aircrafts):
    """
    Primero se obtiene la lista de aviones nocturnos con NightAircraft.
    Para cada uno se llama a AssignGate del modulo LEBL para ocupar una puerta.
    """
    try:
        from src.LEBL import AssignGate
    except ImportError:
        from LEBL import AssignGate

    if not aircrafts:
        return -1

    nights = NightAircraft(aircrafts)
    if nights == -1:
        return -1
    for plane in nights:
        AssignGate(bcn, plane)

    return 0


def FreeGate(bcn, id):
    """
    Se recorren todas las terminales, areas y puertas del aeropuerto.
    Cuando se encuentra la puerta con esa matricula, se marca libre y se borra el avion.
    Devuelve 0 si se encontro; -1 si no.
    """
    found = False

    i = 0
    while i < len(bcn.terminal) and not found:
        terminal = bcn.terminal[i]

        j = 0
        while j < len(terminal.boarding_area):
            area = terminal.boarding_area[j]

            k = 0
            while k < len(area.gate):
                gate = area.gate[k]

                if gate.aircraft_id == id:
                    gate.occupancy = False
                    gate.aircraft_id = ""
                    found = True
                    break
                k += 1
            if found: break
            j += 1
        i += 1
    return 0 if found else -1


def AssignGatesAtTime(bcn, aircrafts, current_mins):
    """
    En el minuto indicado del dia (0 = medianoche): primero se liberan puertas
    de aviones cuya hora de salida coincide; despues se asigna puerta a los que aterrizan.
    Devuelve cuantos aterrizajes no pudieron tener puerta.
    """
    try:
        from src.LEBL import AssignGate
    except ImportError:
        from LEBL import AssignGate

    i = 0
    while i < len(aircrafts):
        plane = aircrafts[i]

        if plane.departure != "-":
            dep_parts = plane.departure.split(":")
            dep_mins = (int(dep_parts[0]) * 60) + int(dep_parts[1])

            if dep_mins == current_mins:
                FreeGate(bcn, plane.id)
        i += 1

    not_assigned_count = 0

    j = 0
    while j < len(aircrafts):
        plane = aircrafts[j]

        if plane.arrival != "-":
            arr_parts = plane.arrival.split(":")
            arr_mins = (int(arr_parts[0]) * 60) + int(arr_parts[1])

            if arr_mins == current_mins:
                gate_assigned = AssignGate(bcn, plane)

                if gate_assigned == "":
                    not_assigned_count += 1
        j += 1
    return not_assigned_count


def PlotDayOccupancy(bcn, aircrafts):
    """
    Al inicio se asignan puertas a los aviones que ya pernoctaban.
    Se simula cada minuto del dia: asignar y liberar puertas.
    Al cerrar cada hora se cuenta cuantas puertas estan ocupadas por terminal.
    Al final se dibuja un grafico apilado por hora (ocupadas + no asignados).
    """

    SetupPlotStyle()

    AssignNightGates(bcn, aircrafts)

    hours_labels = [f"{h:02d}" for h in range(24)]
    rejected_per_hour = [0] * 24

    occ_por_terminal = {}
    t = 0
    while t < len(bcn.terminal):
        occ_por_terminal[bcn.terminal[t].name] = [0] * 24
        t = t + 1


    m = 0
    while m < 1440:
        hour_index = m // 60

        rejected = AssignGatesAtTime(bcn, aircrafts, m)
        rejected_per_hour[hour_index] = rejected_per_hour[hour_index] + rejected

        if m % 60 == 59:
            ti = 0
            while ti < len(bcn.terminal):
                terminal = bcn.terminal[ti]
                cuenta = 0
                j = 0
                while j < len(terminal.boarding_area):
                    area = terminal.boarding_area[j]
                    k = 0
                    while k < len(area.gate):
                        if area.gate[k].occupancy == True:
                            cuenta = cuenta + 1
                        k = k + 1
                    j = j + 1
                occ_por_terminal[terminal.name][hour_index] = cuenta
                ti = ti + 1
        m = m + 1


    fig, ax = plt.subplots(figsize=(12, 5.5), facecolor=CHART["bg"])

    term_names = []
    ti = 0
    while ti < len(bcn.terminal):
        term_names.append(bcn.terminal[ti].name)
        ti = ti + 1

    colores_term = [CHART["primary_light"], CHART["secondary"], CHART["accent"]]
    bottom = [0] * 24
    leg = 0
    while leg < len(term_names):
        nombre = term_names[leg]
        datos = occ_por_terminal[nombre]
        color_t = colores_term[leg % len(colores_term)]
        ax.bar(
            hours_labels,
            datos,
            bottom=bottom,
            label=nombre + " ocupadas",
            color=color_t,
            edgecolor="white",
            width=0.7,
        )
        h = 0
        while h < 24:
            bottom[h] = bottom[h] + datos[h]
            h = h + 1
        leg = leg + 1

    ax.bar(
        hours_labels,
        rejected_per_hour,
        bottom=bottom,
        label="No asignados",
        color=CHART["non_schengen"],
        edgecolor="white",
        width=0.7,
    )

    ax.set_xlabel("Hora del dia")
    ax.set_ylabel("Numero de puertas / aviones")
    ax.set_title("Ocupacion por terminal cada hora (stacked bar)")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis="y", alpha=0.4)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    SaveAndShow(fig, "day_occupancy_simulation.png")


#  Que aporta el bloque EXTRA (resumen)
#
#  Arriba estan las funciones pedidas en el proyecto: vuelos, graficos, KML,
#  union de movimientos, nocturnos y puertas. Lo de abajo amplia y complementa:
#
#  - Dos juegos de nombres en Aircraft (campos completos y alias cortos).
#  - CO2 calculado para todos los vuelos con origen en la base; la lista larga
#    sigue siendo solo la de mas de 2000 km.
#  - Varios movimientos por matricula el mismo dia y emparejado de pernoctas.
#  - Mas criterios de avion nocturno y simulacion de puertas minuto a minuto.
#  - Grafico de ocupacion por terminal con mejor presentacion.
#  - Diccionario de coordenadas para mapas, KML solo de larga distancia,
#    rutas de guardado en output/ y animacion del mapa LEBL (AIP, taxiways, reloj).

# ===============================================================
#  FUNCIONES EXTRAS
# ===============================================================

def V2OutputPath(filename):
    """Se comprueba que exista la carpeta output del proyecto.
    Se devuelve la ruta completa uniendo output/ con el nombre de archivo del grafico."""
    if not os.path.exists(_OUTPUT_DIR):
        os.makedirs(_OUTPUT_DIR)
    return os.path.join(_OUTPUT_DIR, filename)

def BlankMovementTime(value):
    """Sirve para saber si un vuelo no tiene hora de llegada o de salida.
    Devuelve verdadero cuando el valor es vacio, guion o None."""
    return value in ("", "-", None)


def TimeToMinutes(hhmm):
    """Recibe una hora como texto (por ejemplo 09:45).
    Se separa horas y minutos y se calcula cuantos minutos han pasado desde medianoche.
    Si el formato no es valido, se devuelve None."""
    if not hhmm or ":" not in hhmm:
        return None
    parts = hhmm.strip().split(":")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]) * 60 + int(parts[1])
    except ValueError:
        return None


_OVERNIGHT_ARR_FROM = 18 * 60
_OVERNIGHT_DEP_UNTIL = 9 * 60


def OvernightPairCompatible(arr_m, dep_m):
    """Comprueba si una llegada y una salida pueden ser pernocta:
    la llegada debe ser a partir de las 18:00, la salida antes de las 09:00 del dia siguiente,
    y en el reloj la salida va despues de la llegada (cruzando medianoche)."""
    return arr_m > dep_m and arr_m >= _OVERNIGHT_ARR_FROM and dep_m < _OVERNIGHT_DEP_UNTIL


def TestsProjectRoot():
    """Desde la carpeta src/ se sube un nivel y se obtiene la raiz del proyecto
    (donde esta interfaz.py y las carpetas data y output)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def OutputDir():
    """Devuelve la ruta de la carpeta output dentro del proyecto."""
    return os.path.join(TestsProjectRoot(), "output")


def EnsureOutputDir():
    """Si la carpeta output no existe en disco, se crea.
    Se devuelve la ruta por si otras funciones la necesitan."""
    out = OutputDir()
    if not os.path.exists(out):
        os.makedirs(out)
    return out


def FlightsKmlPath():
    """Indica donde se guarda por defecto el KML de todos los vuelos (flights.kml)."""
    return os.path.join(OutputDir(), "flights.kml")


def SetupPlotStyle():
    """Se configuran colores de fondo, rejilla y fuentes de matplotlib
    para que los graficos EXTRA se vean parecidos entre si."""
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
    """Recibe un eje de grafico y le pone titulo, subtitulo opcional y etiquetas
    con los colores definidos en CHART."""
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
    """Escribe el valor sobre cada barra del grafico (EXTRA)."""
    """Recorre las barras de un grafico y escribe encima el numero
    (altura o anchura) para leerlo sin mirar el eje."""
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
    """Primero se asegura que exista output; luego se guarda la figura en PNG
    y se llama a plt.show() para mostrarla."""
    EnsureOutputDir()
    fig.savefig(
        f"output/{filename}",
        dpi=160,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    plt.show()


def LoadAirports(filename):
    """
    Se lee Airports.txt igual que en airport.py pero el resultado es un diccionario:
    clave = codigo ICAO, valor = par (latitud, longitud) en decimal.
    Asi MapFlights y LongDistanceArrivals pueden buscar coordenadas rapido.
    """

    airports_db = {}
    if os.path.exists(filename):
        with open(filename, "r") as f:
            f.readline()
            for line in f:
                parts = line.strip().split()
                if len(parts) == 3:
                    code = parts[0]
                    lat = parts[1]
                    lon = parts[2]

                    deg_lat = int(lat[1:3])
                    min_lat = int(lat[3:5])
                    sec_lat = int(lat[5:7])

                    lat_val = deg_lat + min_lat / 60 + sec_lat / 3600
                    if lat[0] == "S":
                        lat_val = -lat_val

                    deg_lon = int(lon[1:4])
                    min_lon = int(lon[4:6])
                    sec_lon = int(lon[6:8])

                    lon_val = deg_lon + min_lon / 60 + sec_lon / 3600
                    if lon[0] == "W":
                        lon_val = -lon_val

                    airports_db[code] = (lat_val, lon_val)

    return airports_db


def LongDistanceKmlPath():
    """Devuelve la ruta del archivo KML solo de vuelos largos
    (long_distance_flights.kml en output)."""
    return os.path.join(OutputDir(), "long_distance_flights.kml")


def MapLongDistanceFlights(aircraft, airports_db, filename=None):
    """
    Primero se llama a LongDistanceArrivals para saber que vuelos superan 2000 km.
    Solo esos se escriben en un KML como lineas hacia Barcelona (EXTRA del proyecto).
    """

    lista_larga, _, _ = LongDistanceArrivals(aircraft, airports_db)
    if not lista_larga:
        return -1
    if "LEBL" not in airports_db:
        return -1

    lat_dest, lon_dest = airports_db["LEBL"]
    if filename is None or filename == "":
        filename = LongDistanceKmlPath()

    routes = 0
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("<?xml version='1.0' encoding='UTF-8'?>\n")
            f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
            f.write("<Document>\n")

            j = 0
            while j < len(lista_larga):
                ac = lista_larga[j]
                orig = (ac.origin or ac.origin_airport or "").strip()
                if orig in airports_db:
                    routes = routes + 1
                    lat_orig, lon_orig = airports_db[orig]
                    codigo = str(orig[:2])
                    if codigo in SCHENGEN_PREFIXES:
                        color = "ffff0000"
                    else:
                        color = "ff0000ff"

                    f.write("   <Placemark>\n")
                    f.write(f"   <name>{ac.id}</name>\n")
                    f.write(
                        "   <Style><LineStyle><color>"
                        + color
                        + "</color><width>3</width></LineStyle></Style>\n"
                    )
                    f.write("   <LineString>\n")
                    f.write("   <coordinates>\n")
                    f.write(f"   {lon_orig},{lat_orig},0 ")
                    f.write(f"{lon_dest},{lat_dest},0\n")
                    f.write("   </coordinates>\n")
                    f.write("   </LineString>\n")
                    f.write("   </Placemark>\n")
                j = j + 1

            f.write("</Document>\n")
            f.write("</kml>\n")
    except IOError:
        return -1

    if routes == 0:
        return -1
    return 0


def LeblAipPath():
    """Devuelve la ruta del archivo de texto con posiciones de stands (data/lebl_pdc_aip.txt)."""
    return os.path.join(TestsProjectRoot(), "data", "lebl_pdc_aip.txt")


def LeblTxlPath():
    """Devuelve la ruta del archivo con el mapa de calles del aeropuerto (data/LEBL_Taxiways.txl)."""
    return os.path.join(TestsProjectRoot(), "data", "LEBL_Taxiways.txl")


def LeblLoadAipTextStand(path):
    """Abre el archivo de stands y devuelve todo su contenido como un solo texto."""
    if not os.path.exists(path): raise FileNotFoundError(f"No se encontro el archivo AIP: {path}")
    with open(path, encoding="utf-8") as f: return f.read()

GA_STANDS = {"01","02","03","04","11","12","13","14","15","21","22","23","24","25","26",
             "31","32","33","34","35","36","37","38","40","41","42","43","44","44A","45",
             "46","46A","47","48","48A","49"}
CARGO_STANDS = {"131","132","133","133A","134","134A","135","136","137","138","138A","139",
                "141","141A","142","142A","143","143A","144","151","151A","152","152A","153",
                "154","154A","155","155A","156","157","157A","161","162","163","164","165",
                "171","172","173","174","175","181","182","183","184","185"}
RAMP32_STANDS = {"900","901","902","904","905","906","908","910","912","914","916","917","918"}
AUXILIARY_STANDS = {"X1","X2","X3"}
GA_AIRCRAFT_TYPES = {"C560","CL60","F50","GLF4","GLEX","EC25","S76","E120","BH2","CRJ","CRJX"}
PASSENGER_AIRLINE_STANDS = {
    "100","101","101A","102","103","104","105","106","107","108","109","110","111","112","113",
    "113A","114","115","116","117","118","119","119A","120","121","121A","122","124","124A",
    "125","126","126A","127","128","128A","129","51","52","53","54","55","56","57","61","62","63",
    "71","72","81","81A","82","83","83A","84","85","86","87","91","92","93","94","95","96",
    "200","202","204","206","208","210","212","214","216","217","218","220","221","222","224",
    "226","228","230","232","234","236","238","240","242","244","245","246","247","248","250",
    "252","254","256","258","260","262","264","266","268","270","272","273","274","276","277",
    "278","280","281","282","284","285","286","287","288","290","291","292","294","295","296",
    "300","302","310","312","314","320","322","330","332","334","340","342",
    "400","410","412","414","420","421","422","425",
}

AIP_LINE_PATTERN = re.compile(
    r"^\s*([A-Z]?\d{1,3}[A-Z]?)\s+(R\d+)\s+(\d{2})(\d{2})(\d{2}\.\d+)N"
    r"\s+(\d{3})(\d{2})(\d{2}\.\d+)E\s+(.*)$", re.IGNORECASE)

def LeblDmsToDecimal(d, m, s):
    """Convierte grados, minutos y segundos por separado a un solo numero decimal.
    Por ejemplo 41 grados, 18 minutos y 30 segundos pasan a 41.308... grados."""
    return float(d) + float(m)/60 + float(s)/3600

def LeblNormalizeStandId(raw):
    """
    Unifica el id del stand: mayusculas, ceros a la izquierda en numeros cortos,
    y los auxiliares X1, X2 se dejan tal cual.
    """
    raw = raw.strip().upper()
    if raw.startswith("X"): return raw
    m = re.fullmatch(r"(\d+)([A-Z]?)", raw)
    if not m: return raw
    num, suf = m.groups()
    return f"{num.zfill(2) if len(num) <= 2 else num}{suf}"

def LeblExtractMaxAcft(tail):
    """
    De la cola de texto de una linea del AIP se saca el codigo
    del tipo de avion maximo permitido en ese stand.
    """
    t = tail.split()
    if not t: return ""
    i = 1 if t[0] in ("R","–","-") else 0
    return t[i].upper() if i < len(t) else ""

def LeblClassifyStand(sid, max_acft="", ramp=""):
    """Segun el numero de stand y el tipo de avion se etiqueta como
    airline, cargo, ga, ramp32, auxiliary u other usando listas fijas del aeropuerto."""
    if sid in PASSENGER_AIRLINE_STANDS: return "airline"
    if sid in AUXILIARY_STANDS:         return "auxiliary"
    if sid in RAMP32_STANDS or ramp == "R32": return "ramp32"
    if sid in GA_STANDS:                return "ga"
    if sid in CARGO_STANDS:             return "cargo"
    if max_acft in GA_AIRCRAFT_TYPES:   return "ga"
    return "other"

def ParseAipStands(texto, categories=None):
    """
    Se buscan lineas con formato de stand del AIP (numero, coordenadas, etc.).
    Cada stand valido se guarda con id, latitud, longitud y tipo (pasajeros, carga...).
    Si se pide categories, solo se incluyen los tipos indicados (ej. airline).
    """
    stands, seen = [], set()
    for linea in texto.splitlines():
        m = AIP_LINE_PATTERN.match(linea)
        if not m: continue
        raw_id, ramp, *dms, tail = m.groups()
        lat_d, lat_m, lat_s, lon_d, lon_m, lon_s = dms
        sid = LeblNormalizeStandId(raw_id)
        max_acft = LeblExtractMaxAcft(tail)
        cat = LeblClassifyStand(sid, max_acft, ramp.upper())
        if (categories and cat not in categories) or sid in seen: continue
        stands.append({"id": sid, "lat": LeblDmsToDecimal(lat_d, lat_m, lat_s),
                        "lon": LeblDmsToDecimal(lon_d, lon_m, lon_s),
                        "category": cat, "ramp": ramp.upper(), "max_acft": max_acft})
        seen.add(sid)
    return sorted(stands, key=lambda s: (s["category"], re.sub(r"[A-Z]","",s["id"]).zfill(4), s["id"]))

def ParseTxlPaths(file_path):
    """
    El archivo TXL describe tramos del aeropuerto como listas de coordenadas.
    Se devuelve una lista de polilineas para dibujar taxiways y pistas en el mapa.
    """
    paths = []
    for el in ET.parse(file_path).iter("SerializablePath"):
        coords = [[float(p.findtext("Position/Latitude")), float(p.findtext("Position/Longitude"))]
                  for p in el.findall(".//SerializableTaxiPt")
                  if p.find("Position") is not None and p.findtext("Position/Latitude")]
        if len(coords) >= 2:
            paths.append({"name": (el.findtext("Name") or "").strip(),
                           "type": (el.findtext("Type") or "Unknown").strip(), "coords": coords})
    return paths

VALID_RUNWAYS = {"07L","07R","25L","25R","02","20"}
RUNWAY_OPPOSITE = {"07L":"25R","25R":"07L","07R":"25L","25L":"07R","02":"20","20":"02"}
TIME_RE = re.compile(r"^\d{2}:\d{2}$")
HEADER_SKIP = {"AIRCRAFT","ORIGIN","DESTINATION"}

@dataclass
class FlightRecord:
    """Fila de vuelo para la animacion: matricula, origen, horas, pistas y puerta.
    Las propiedades arrival_mins y departure_mins convierten las horas a minutos del dia."""
    aircraft: str; origin: str; arrival: str; departure: str
    airline: str; arr_runway: str; dep_runway: str; gate: str; destination: str = ""

    def _mins(self, t):
        if t in ("-",""): return None
        h, m = map(int, t.split(":")); return h*60+m

    @property
    def arrival_mins(self):   return self._mins(self.arrival)
    @property
    def departure_mins(self): return self._mins(self.departure)

def ParseTime(v):
    """Comprueba si un texto tiene forma de hora HH:MM valida."""
    return bool(TIME_RE.match(v)) and bool(datetime.strptime(v, "%H:%M") if True else True)

def DeterministicGate(stands, aircraft):
    """Si falta puerta en los datos, se elige una de la lista de stands disponibles
    de forma fija segun la matricula (siempre la misma matricula -> misma puerta)."""
    if not stands: return "217"
    return sorted(stands)[sum(ord(c) for c in aircraft) % len(stands)]

def RandomRunway():
    """Devuelve una pista al azar entre las permitidas cuando falta en los datos."""
    return random.choice(list(VALID_RUNWAYS))

def InferDepartureRunway(arr, aircraft="", arrival=""):
    """
    Si se conoce la pista de llegada, la de salida suele ser la opuesta del par.
    Si no, se elige otra pista valida distinta de forma determinista segun matricula y hora.
    """
    arr = (arr or "").upper()
    if arr in RUNWAY_OPPOSITE: return RUNWAY_OPPOSITE[arr]
    pool = sorted(r for r in VALID_RUNWAYS if r != arr) or sorted(VALID_RUNWAYS)
    return pool[sum(ord(c) for c in f"{aircraft}|{arrival}|dep") % len(pool)]

def CompleteMissingFields(f, stands):
    arr, dep = f.arrival, f.departure
    """Rellena pista de llegada, pista de salida y puerta cuando vienen en guion.
    Devuelve un FlightRecord nuevo con todos los campos listos para la animacion."""
    arr_rwy, dep_rwy, gate = f.arr_runway, f.dep_runway, f.gate
    has_arr = arr not in ("-",""); has_dep = dep not in ("-","")
    if has_arr and arr_rwy in ("-",""):  arr_rwy = RandomRunway()
    if has_dep and dep_rwy in ("-",""):
        dep_rwy = InferDepartureRunway(arr_rwy, f.aircraft, f.arrival) if has_arr else RandomRunway()
    if gate in ("-","") or (stands and gate not in stands):
        gate = DeterministicGate(stands, f.aircraft)
    return FlightRecord(f.aircraft, f.origin, arr, dep, f.airline, arr_rwy, dep_rwy, gate, f.destination)

def ParseFlightsFile(path, available_stands=None, default_arr_runway="25R",
                       default_dep_runway="07L"):
    """
    Lee un archivo de vuelos con mas columnas que el formato basico de cuatro campos.
    Se detecta si es solo llegadas o mezcla con salidas; se rellenan pistas y puertas
    que falten con valores por defecto o aleatorios dentro de lo permitido.
    """
    with open(str(path), encoding="utf-8") as f: text = f.read()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines: return []
    header = lines[0].split()
    is_dep_legacy = "DESTINATION" in header and "ORIGIN" not in header
    stands = available_stands or []
    flights = []
    for line in lines[1:]:
        p = line.split()
        if len(p) < 4 or p[0] in HEADER_SKIP: continue
        if len(p) >= 7 and ParseTime(p[2]) and ParseTime(p[3]):
            arr_rwy = p[5].upper() if p[5].upper() in VALID_RUNWAYS else RandomRunway()
            dep_rwy = p[6].upper() if p[6].upper() in VALID_RUNWAYS else RandomRunway()
            gate = p[7] if len(p) >= 8 else DeterministicGate(stands, p[0])
            flights.append(FlightRecord(p[0],p[1],p[2],p[3],p[4],arr_rwy,dep_rwy,gate))
        elif len(p) == 4 and ParseTime(p[2]):
            if is_dep_legacy:
                flights.append(FlightRecord(p[0],"-","-",p[2],p[3],"-","-","-",destination=p[1]))
            else:
                flights.append(FlightRecord(p[0],p[1],p[2],"-",p[3],"-","-","-"))
    return [CompleteMissingFields(f, stands) for f in flights]

def MergeArrivalsDepartures(arrivals_path, departures_path, available_stands=None):
    """
    Se cargan dos archivos y se unen los vuelos por matricula para la animacion,
    usando la misma logica de emparejar horas que MergeMovements.
    """
    stands = available_stands or []
    arr_list = sorted([f for f in ParseFlightsFile(arrivals_path, stands) if f.arrival not in ("-","")],
                      key=lambda f: f.arrival_mins)
    dep_pool = defaultdict(list)
    for d in ParseFlightsFile(departures_path, stands):
        if d.departure not in ("-",""): dep_pool[d.aircraft].append(d)
    for ac in dep_pool: dep_pool[ac].sort(key=lambda f: f.departure_mins or 0)

    def _turnaround(arr_m, dep_m):
        diff = dep_m - arr_m; return diff if diff >= 0 else diff + 24*60

    merged = []
    for a in arr_list:
        pool = dep_pool.get(a.aircraft, [])
        best_diff, dep_match, pick_idx = 24*60, None, -1
        for i, d in enumerate(pool):
            if d.departure_mins is None: continue
            diff = _turnaround(a.arrival_mins, d.departure_mins)
            if 20 <= diff < best_diff: best_diff, dep_match, pick_idx = diff, d, i
        if pick_idx >= 0: pool.pop(pick_idx)
        if dep_match:
            dep_rwy = dep_match.dep_runway
            if dep_rwy in ("-","") or dep_match.arrival in ("-",""):
                dep_rwy = InferDepartureRunway(a.arr_runway, a.aircraft, a.arrival)
            merged.append(FlightRecord(a.aircraft, a.origin, a.arrival, dep_match.departure,
                                       a.airline or dep_match.airline, a.arr_runway, dep_rwy,
                                       a.gate if a.gate not in ("-","") else dep_match.gate,
                                       dep_match.destination))
        else:
            merged.append(a)
    for pool in dep_pool.values(): merged.extend(pool)
    return [CompleteMissingFields(f, stands) for f in merged]

RUNWAY_APPROACH_EXTRA = 0.028
RUNWAY_EXIT_EXTRA     = 0.035
TAXI_SPEED_MPS        = 7.0
APPROACH_SPEED_MPS    = 72.0
RUNWAY_BACKTRACK_MPS  = 11.0
TURNAROUND_MPS        = 3.5
TAKEOFF_ROLL_S        = 22.0
LANDING_ROLL_METERS   = 2200.0
MS_PER_SIM_MINUTE     = 800
REAL_SEC_TO_SIM_MS    = MS_PER_SIM_MINUTE / 60.0

def HaversineM(p1, p2):
    """Calcula una distancia aproximada en metros entre dos puntos del mapa
    (latitud y longitud), usando una formula simple adaptada a la zona de Barcelona."""
    return math.hypot((p2[0]-p1[0])*111_320, (p2[1]-p1[1])*111_320*math.cos(math.radians(41.3)))

def CumulativeDistances(pts):
    d = [0.0]
    """Dado una lista de puntos seguidos, devuelve cuanto metros hay
    desde el inicio hasta cada punto (sumando tramo a tramo)."""
    for i in range(1, len(pts)): d.append(d[-1] + HaversineM(pts[i-1], pts[i]))
    return d

def AssignTimesConst(pts, speed):
    """A cada punto de una ruta se le asigna un instante de tiempo
    suponiendo velocidad constante entre puntos (taxi, giro, etc.)."""
    if not pts: return []
    out, t = [{"lat": pts[0][0], "lon": pts[0][1], "t": 0.0}], 0.0
    for i in range(1, len(pts)):
        t += HaversineM(pts[i-1], pts[i]) / speed * REAL_SEC_TO_SIM_MS
        out.append({"lat": pts[i][0], "lon": pts[i][1], "t": t})
    return out

def AssignTimesProfile(pts, total_s, profile):
    """Igual que AssignTimesConst pero la velocidad no es uniforme:
    puede acelerar, frenar o ir a ritmo constante segun el perfil indicado."""
    if not pts: return []
    dists = CumulativeDistances(pts); total_d = dists[-1]
    def frac_to_t(frac):
        if profile == "accel":   return math.sqrt(frac) * total_s * REAL_SEC_TO_SIM_MS
        if profile == "decel":   return (1 - math.sqrt(max(0.0, 1-frac))) * total_s * REAL_SEC_TO_SIM_MS
        return frac * total_s * REAL_SEC_TO_SIM_MS
    return [{"lat": p[0], "lon": p[1],
             "t": frac_to_t(dists[i]/total_d if total_d > 1e-6 else 0.0)}
            for i, p in enumerate(pts)]

def AssignTimesAccel(pts, total_s):
    """Atajo: AssignTimesProfile con perfil de aceleracion (despegue)."""
    return AssignTimesProfile(pts, total_s, "accel")
def AssignTimesDecel(pts, total_s):
    """Atajo: AssignTimesProfile con perfil de frenada (aterrizaje)."""
    return AssignTimesProfile(pts, total_s, "decel")
def AssignTimesDecelFromInitialSpeed(pts, v0):
    """Calcula cuanto tarda en frenar desde una velocidad inicial
    y aplica perfil de deceleracion a la lista de puntos."""
    if not pts: return []
    d = CumulativeDistances(pts)[-1]
    return AssignTimesDecel(pts, 2*d/v0 if d > 1e-6 else 1.0)

_MODE_SPEED = {"taxi": (TAXI_SPEED_MPS,"const"), "turnaround": (TURNAROUND_MPS,"const"),
               "approach": (APPROACH_SPEED_MPS,"const"), "runway_backtrack": (RUNWAY_BACKTRACK_MPS,"const")}

def MergeTimedSegments(segments):
    result, offset = [], 0.0
    """Varios trozos de ruta (taxi, pista, giro) se unen en una sola lista
    de puntos con tiempo creciente, sin duplicar el ultimo punto del tramo anterior."""
    for pts, mode in segments:
        if not pts: continue
        if mode in _MODE_SPEED:
            speed, _ = _MODE_SPEED[mode]; timed = AssignTimesConst(pts, speed)
        elif mode == "runway_accel": timed = AssignTimesAccel(pts, TAKEOFF_ROLL_S)
        elif mode == "runway_decel": timed = AssignTimesDecelFromInitialSpeed(pts, APPROACH_SPEED_MPS)
        else: timed = AssignTimesConst(pts, TAXI_SPEED_MPS)
        for j, pt in enumerate(timed):
            t = pt["t"] + offset
            if j == 0 and result and abs(result[-1]["lat"]-pt["lat"]) < 1e-9 and abs(result[-1]["lon"]-pt["lon"]) < 1e-9:
                result[-1]["t"] = t; continue
            result.append({"lat": pt["lat"], "lon": pt["lon"], "t": t})
        if result: offset = result[-1]["t"]
    return result

def DensifyPath(pts, step=0.000012):
    """Entre dos puntos muy separados se insertan puntos intermedios
    para que el avion se mueva suave en el mapa y no a saltos."""
    if len(pts) < 2: return pts
    dense = [pts[0]]
    for i in range(len(pts)-1):
        a, b = pts[i], pts[i+1]
        dx, dy = b[0]-a[0], b[1]-a[1]
        n = max(1, int(math.hypot(dx,dy)/step))
        dense.extend([[a[0]+dx*j/n, a[1]+dy*j/n] for j in range(1, n+1)])
    return dense

def RunwayCoords(txl_paths, name):
    """Busca en la lista de tramos TXL el que es pista (Runway) con el nombre pedido
    y devuelve sus coordenadas. Si no existe, lanza error."""
    for s in txl_paths:
        if s["type"] == "Runway" and s["name"] == name: return s["coords"]
    raise ValueError(f"Pista no encontrada: {name}")

def RunwayEnds(coords):
    """De los dos extremos de una pista, devuelve el mas al oeste y el mas al este
    (ordenados por longitud)."""
    return (coords[0], coords[1]) if coords[0][1] <= coords[1][1] else (coords[1], coords[0])

def RunwayNumber(name):
    """Saca el numero de pista del nombre (por ejemplo 25 de 25R)."""
    d = "".join(c for c in name if c.isdigit()); return int(d[:2]) if d else 25

def LandsFromEast(name):
    """Las pistas con numero 13 o mayor se consideran aterrizaje por el lado este."""
    return RunwayNumber(name) >= 13

def ExtendRunwayAxis(west, east, beyond, distance):
    """Desde un extremo de pista se alarga la linea unos metros hacia fuera
    (punto de aproximacion o de salida del mapa)."""
    ref = east if beyond == "east" else west
    opp = west if beyond == "east" else east
    dx, dy = ref[0]-opp[0], ref[1]-opp[1]
    L = math.hypot(dx,dy)
    if L < 1e-12: return ref
    return [ref[0]+dx/L*distance, ref[1]+dy/L*distance]

def MergedStripEndpoints(txl_paths, rwy):
    """Une las coordenadas de una pista y su opuesta para tener
    el tramo completo y devuelve el punto mas al oeste y el mas al este."""
    pts = RunwayCoords(txl_paths, rwy) + RunwayCoords(txl_paths, RUNWAY_OPPOSITE.get(rwy, rwy))
    return min(pts, key=lambda p:(p[1],p[0])), max(pts, key=lambda p:(p[1],p[0]))

def RunwayThreshold(west, east, name):
    """Devuelve el extremo de pista por donde aterriza ese nombre de pista
    (este u oeste segun LandsFromEast)."""
    return east if LandsFromEast(name) else west

def PointAlongStrip(west, east, start, toward, dist_m):
    """Desde un punto sobre la pista se avanza una distancia en metros
    hacia el oeste o el este a lo largo del eje de la pista."""
    end = west if toward == "west" else east
    seg = HaversineM(start, end)
    if seg < 1e-6: return start
    frac = min(1.0, dist_m/seg)
    return [start[0]+(end[0]-start[0])*frac, start[1]+(end[1]-start[1])*frac]

def ApproachSpawn(west, east, name):
    """Punto en el mapa donde aparece el avion antes de entrar en pista (fuera del aeropuerto)."""
    return ExtendRunwayAxis(west, east, "east" if LandsFromEast(name) else "west", RUNWAY_APPROACH_EXTRA)

def DepartureExit(west, east, name):
    """Punto donde termina la salida por pista al alejarse del aeropuerto."""
    return ExtendRunwayAxis(west, east, "west" if RunwayNumber(name) < 13 else "east", RUNWAY_EXIT_EXTRA)

def UTurnAtEnd(end, west, east, roll_toward_west):
    dx, dy = east[0]-west[0], east[1]-west[1]; L = math.hypot(dx,dy)
    """Genera una curva en U al final de pista para cambiar de sentido antes del despegue."""
    if L < 1e-12: return [end, end]
    ux, uy = dx/L, dy/L; nx, ny = -uy*0.00045, ux*0.00045
    if roll_toward_west:
        pts = [end,[end[0]+nx*.35,end[1]+ny*.35],[end[0]+nx,end[1]+ny],
               [end[0]+nx*.4-ux*.00025,end[1]+ny*.4-uy*.00025],[end[0]-ux*.0002,end[1]-uy*.0002]]
    else:
        pts = [end,[end[0]-nx*.35,end[1]-ny*.35],[end[0]-nx,end[1]-ny],
               [end[0]-nx*.4+ux*.00025,end[1]-ny*.4+uy*.00025],[end[0]+ux*.0002,end[1]+uy*.0002]]
    return DensifyPath(pts, step=0.000008)

class TaxiGraph:
    """Grafo de nodos en intersecciones de taxiways.
    Permite calcular el camino mas corto entre dos puntos del aeropuerto para las rutas de rodaje."""
    SNAP = 0.00004

    def __init__(self, txl_paths):
        self.graph = defaultdict(list)
        for seg in txl_paths:
            if seg["type"] != "Taxi": continue
            coords = seg["coords"]
            for i in range(len(coords)-1):
                ka, kb = self._key(*coords[i]), self._key(*coords[i+1])
                d = self._dist(ka, kb)
                self.graph[ka].append((kb,d)); self.graph[kb].append((ka,d))

    def _key(self, lat, lon): return (round(lat/self.SNAP)*self.SNAP, round(lon/self.SNAP)*self.SNAP)
    @staticmethod
    def _dist(a, b): return HaversineM([a[0],a[1]], [b[0],b[1]])

    def nearest_node(self, lat, lon):
        return min(self.graph, key=lambda n: self._dist(n,(lat,lon)))

    def shortest_path(self, start, end):
        if not self.graph: return [start, end]
        s, t = self.nearest_node(*start), self.nearest_node(*end)
        if s == t: return [start, end]
        pq, prev, seen = [(0.0,s)], {}, set()
        while pq:
            du, u = heapq.heappop(pq)
            if u in seen: continue
            seen.add(u)
            if u == t: break
            for v, w in self.graph[u]:
                if v in seen: continue
                nd = du + w
                if v not in prev or nd < prev[v][0]: prev[v]=(nd,u); heapq.heappush(pq,(nd,v))
        if t not in prev and t != s: return [start, end]
        path, cur = [t], t
        while cur != s: cur = prev[cur][1]; path.append(cur)
        return list(reversed(path))

def TaxiRoute(graph, start, end):
    """Usa el grafo de taxiways para ir del punto de inicio al stand (o al reves):
    calcula el camino mas corto y lo densifica con mas puntos."""
    nodes = graph.shortest_path(start, end)
    raw = [[start[0],start[1]]] + [[n[0],n[1]] for n in nodes] + [[end[0],end[1]]]
    return DensifyPath(raw)

def BuildArrivalPath(graph, txl_paths, runway_name, gate_lat, gate_lon):
    """Monta la secuencia completa de un aterrizaje: aproximacion, rodaje por pista,
    taxi hasta la puerta, con tiempos en cada tramo."""
    west, east = MergedStripEndpoints(txl_paths, runway_name)
    spawn = ApproachSpawn(west, east, runway_name)
    thr   = RunwayThreshold(west, east, runway_name)
    vacate = PointAlongStrip(west, east, thr, "west" if LandsFromEast(runway_name) else "east",
                               LANDING_ROLL_METERS)
    return MergeTimedSegments([
        (DensifyPath([spawn, thr]),   "approach"),
        (DensifyPath([thr, vacate])[1:], "runway_decel"),
        (TaxiRoute(graph,(vacate[0],vacate[1]),(gate_lat,gate_lon))[1:], "taxi"),
    ])

def BuildDeparturePath(graph, txl_paths, runway_name, gate_lat, gate_lon):
    """Monta la secuencia de salida: desde la puerta por taxi, pista, despegue
    y salida del mapa, con tiempos en cada tramo."""
    west, east = MergedStripEndpoints(txl_paths, runway_name)
    dep_num = RunwayNumber(runway_name)
    turn_end = east if dep_num < 13 else west
    roll_toward_west = dep_num < 13
    taxi  = TaxiRoute(graph, (gate_lat,gate_lon), (turn_end[0],turn_end[1]))
    uturn = UTurnAtEnd(turn_end, west, east, roll_toward_west)
    roll_from = uturn[-1]
    roll_pts = DensifyPath([roll_from, west if roll_toward_west else east,
                             DepartureExit(west, east, runway_name)])
    return MergeTimedSegments([(taxi,"taxi"),(uturn[1:],"turnaround"),(roll_pts[1:],"runway_accel")])

def LeblMinsToMs(mins, base):
    """Pasa minutos del reloj de simulacion a milisegundos de animacion,
    restando la hora de inicio del dia simulado."""
    return max(0, (mins-base)*MS_PER_SIM_MINUTE)

def FindNearestFreeGate(at_ms, stand_by_id, gate_free_at, ref_lat, ref_lon):
    """En un instante dado, busca el stand libre mas cercano a unas coordenadas
    (cuando hay conflicto de dos aviones por la misma puerta)."""
    best_id, best_d = None, float("inf")
    for sid, s in stand_by_id.items():
        if gate_free_at.get(sid,0) > at_ms: continue
        d = HaversineM([ref_lat,ref_lon],[s["lat"],s["lon"]])
        if d < best_d: best_d, best_id = d, sid
    return best_id

def ResolveGateConflicts(ops, stand_by_id, graph, txl_paths):
    """Si dos operaciones quieren el mismo stand a la vez, se retrasa una
    o se le asigna otro stand libre y se recalculan sus rutas."""
    gate_free_at, gate_occupant = {}, {}
    FAR = 365*24*60*MS_PER_SIM_MINUTE

    def _redirect_paths(op, assigned, dep_start, has_arr):
        s = stand_by_id[assigned]
        if has_arr:
            ap = BuildArrivalPath(graph, txl_paths, op["arrRunway"], s["lat"], s["lon"])
            op["arrivalPath"] = ap; op["arrivalDurationMs"] = int(ap[-1]["t"])
        if dep_start is not None and op["depRunway"]:
            dp = BuildDeparturePath(graph, txl_paths, op["depRunway"], s["lat"], s["lon"])
            op["departurePath"] = dp; op["departureDurationMs"] = int(dp[-1]["t"])

    def _process(op, at_ms, free_at):
        req = op["gate"]
        assigned, redirected, occupied_by = req, False, None
        if gate_free_at.get(req,0) > at_ms:
            occupied_by = gate_occupant.get(req)
            alt = FindNearestFreeGate(at_ms, stand_by_id, gate_free_at,
                                         stand_by_id[req]["lat"], stand_by_id[req]["lon"])
            if alt and alt != req:
                assigned, redirected = alt, True
                has_arr = not op.get("startParked")
                _redirect_paths(op, alt, op["departureStartMs"], has_arr)
                if has_arr:
                    free_at = op["arrivalStartMs"] + op["arrivalDurationMs"]
        op.update(requestedGate=req, assignedGate=assigned, gate=assigned,
                  redirected=redirected, occupiedBy=occupied_by,
                  redirectAtMs=free_at if redirected else None)
        gate_free_at[assigned] = op["departureStartMs"] if op["departureStartMs"] else FAR
        gate_occupant[assigned] = op["aircraft"]

    for op in sorted([o for o in ops if o.get("startParked")],  key=lambda o: o.get("departureStartMs") or 0):
        _process(op, 0, op.get("departureStartMs") or FAR)
    for op in sorted([o for o in ops if not o.get("startParked")], key=lambda o: o["arrivalStartMs"]):
        park_ms = op["arrivalStartMs"] + op["arrivalDurationMs"]
        _process(op, park_ms, op["departureStartMs"] or FAR)
    return ops

def ClassifyAnimationFlight(f):
    """Decide si el vuelo solo llega, solo sale, hace ida y vuelta en el dia
    o debe ignorarse en la animacion."""
    ha, hd = f.arrival_mins is not None, f.departure_mins is not None
    return "normal" if ha and hd else "arrival_only" if ha else "departure_only" if hd else "skip"

def SelectFlightsForAnimation(flights, limit):
    """Si hay demasiados vuelos, se limita la lista al maximo indicado
    para no saturar la animacion."""
    if not flights or not limit or len(flights) <= limit: return flights
    def _ev(f): return f.arrival_mins or f.departure_mins or 0
    ordered = sorted(flights, key=_ev); n = len(ordered)
    idx = sorted({min(int(round(i*(n-1)/max(1,limit-1))),n-1) for i in range(limit)})
    return [ordered[i] for i in idx]

def DecimateTimedPath(path, max_points=50):
    """Reduce el numero de puntos de una ruta si hay demasiados,
    manteniendo inicio, fin y reparto uniforme, para dibujar mas rapido."""
    if not path or len(path) <= max_points: return path
    n = len(path)
    return [path[int(i*(n-1)/(max_points-1))] for i in range(max_points)]

def PrepareOperations(flights, stands, txl_paths, limit=None):
    """
    Para cada vuelo se calcula la ruta de llegada por taxiway hasta el stand
    y, si tiene salida, la ruta de vuelta a pista. Se resuelven conflictos si
    dos aviones quieren el mismo stand a la vez. Devuelve la lista de operaciones
    y la hora de inicio de la simulacion.
    """

    graph = TaxiGraph(txl_paths)
    stand_by_id = {s["id"]: s for s in stands}
    by_kind = defaultdict(list)
    for f in flights:
        if f.gate not in stand_by_id: continue
        k = ClassifyAnimationFlight(f)
        if k != "skip": by_kind[k].append(f)

    pool = by_kind["normal"] + by_kind["arrival_only"] + by_kind["departure_only"]
    if not pool: raise ValueError("No hay vuelos con gate valido para animar")
    if limit and len(pool) > limit:
        sel = SelectFlightsForAnimation(pool, limit)
        by_kind = defaultdict(list)
        for f in sel: by_kind[ClassifyAnimationFlight(f)].append(f)

    event_mins = [f.arrival_mins for f in by_kind["normal"]+by_kind["arrival_only"] if f.arrival_mins] + \
                 [f.departure_mins for f in by_kind["normal"]+by_kind["departure_only"] if f.departure_mins]
    base_mins = min(event_mins)
    ops = []

    def _make_op(f, kind):
        s = stand_by_id[f.gate]; ms = lambda m: LeblMinsToMs(m, base_mins) if m else None
        arr_path = BuildArrivalPath(graph, txl_paths, f.arr_runway, s["lat"], s["lon"]) if f.arrival_mins else []
        dep_path = BuildDeparturePath(graph, txl_paths, f.dep_runway, s["lat"], s["lon"]) \
                   if f.departure_mins and f.dep_runway not in ("","-") else []
        arr_start = ms(f.arrival_mins) if f.arrival_mins else (-1 if kind == "departure_only" else 0)
        return {
            "animKind": kind, "startParked": kind == "departure_only",
            "aircraft": f.aircraft, "airline": f.airline, "origin": f.origin,
            "gate": f.gate, "arrRunway": f.arr_runway, "depRunway": f.dep_runway,
            "arrivalLabel": f.arrival if f.arrival_mins else "-",
            "departureLabel": f.departure if f.departure_mins else "-",
            "arrivalStartMs": arr_start,
            "arrivalDurationMs": int(arr_path[-1]["t"]) if arr_path else 0,
            "departureStartMs": ms(f.departure_mins),
            "departureDurationMs": int(dep_path[-1]["t"]) if dep_path else 0,
            "arrivalPath": arr_path, "departurePath": dep_path,
        }

    for kind in ("departure_only","normal","arrival_only"):
        key_fn = lambda f: f.departure_mins or 0 if kind == "departure_only" else f.arrival_mins or 0
        for f in sorted(by_kind[kind], key=key_fn): ops.append(_make_op(f, kind))

    ops = ResolveGateConflicts(ops, stand_by_id, graph, txl_paths)
    return ops, max(0, base_mins-5)

def StandNumericId(sid):
    """Extrae la parte numerica del id de stand para ordenar y filtrar (T1/T2)."""
    d = "".join(c for c in sid if c.isdigit()); return int(d[:3]) if d else 0

def T1AipPool(ids):
    """Devuelve los stands de pasajeros cuyo numero esta en el rango de la terminal 1."""
    return sorted(s for s in ids if 200 <= StandNumericId(s) <= 340)
def T2AipPool(ids):
    """Devuelve los stands de pasajeros cuyo numero esta en el rango de la terminal 2."""
    return sorted(s for s in ids if  20 <= StandNumericId(s) <= 150)

def LeblGateToAipStand(gate_name, stand_ids):
    """Traduce un nombre de puerta del Terminals.txt (ej. T1BAG12)
    al id de stand del AIP (ej. 112) si existe en la lista."""
    m = re.match(r"T(\d)BA([A-Z]+)(\d+)", gate_name or "")
    if not m: return None
    terminal, gate_num = int(m.group(1)), int(m.group(3))
    pool = T1AipPool(stand_ids) if terminal == 1 else T2AipPool(stand_ids)
    if not pool: return stand_ids[0] if stand_ids else None
    return pool[(gate_num-1) % len(pool)]

def FlightGateKey(aircraft, arrival):
    """Crea una clave unica para buscar puerta asignada: matricula mas hora de llegada."""
    return (aircraft, arrival)
def FlightRecordGateKey(f):
    """Igual que FlightGateKey pero desde un FlightRecord
    (usa llegada o salida si falta la otra)."""
    return FlightGateKey(f.aircraft, f.arrival if f.arrival not in ("-","") else f.departure)

def FreeLeblGate(bcn, gate_name):
    """Marca libre una puerta del objeto BarcelonaAP por su nombre
    (ocupancy falso y sin matricula)."""
    if not gate_name or bcn is None: return
    for t in bcn.terminal:
        for a in t.boarding_area:
            for g in a.gate:
                if g.name == gate_name: g.occupancy = False; g.aircraft_id = ""; return

def BuildGateAssignmentsFromBcn(bcn, stand_ids):
    """
    Recorre las puertas ya ocupadas en bcn_airport tras AssignGate
    y devuelve un diccionario matricula+hora -> stand AIP para la animacion.
    """
    try:
        from src.LEBL import GateOccupancy
    except ImportError:
        from LEBL import GateOccupancy
    return {gi["aircraft_id"]: LeblGateToAipStand(gi["name"], stand_ids)
            for gi in GateOccupancy(bcn)
            if gi["status"] in ("Occupied","Ocupada") and gi.get("aircraft_id")
            and LeblGateToAipStand(gi["name"], stand_ids)}

def BuildGateAssignmentsForFlights(bcn, flights, stand_ids):
    """
    Para cada vuelo de la lista intenta AssignGate en bcn
    y guarda que stand AIP le toco.
    """
    try:
        from src.LEBL import AssignGate
    except ImportError:
        from LEBL import AssignGate
    bcn_work = copy.deepcopy(bcn); assignments = {}
    for f in flights:
        if f.arrival in ("-",""): continue
        ac = Aircraft(f.aircraft, f.airline, f.origin, f.arrival)
        ac.departure = f.departure if f.departure not in ("-","") else "-"
        gate_name = AssignGate(bcn_work, ac)
        if not gate_name: continue
        stand = LeblGateToAipStand(gate_name, stand_ids)
        if stand: assignments[FlightGateKey(f.aircraft, f.arrival)] = stand
        FreeLeblGate(bcn_work, gate_name)
    return assignments

def DefaultStandForAirline(bcn, airline, stand_ids, aircraft="", arrival=""):
    """
    Si no hay puerta asignada, busca un stand de pasajeros coherente
    con la terminal de la aerolinea.
    """
    try:
        from src.LEBL import SearchTerminal
    except ImportError:
        from LEBL import SearchTerminal
    pool = (T1AipPool if SearchTerminal(bcn,airline)=="T1" else T2AipPool)(stand_ids) or sorted(stand_ids) or ["217"]
    key = f"{airline}|{arrival}" if arrival not in ("-","") else aircraft
    return pool[sum(ord(c) for c in key) % len(pool)]

LEBL_ANIM_PATH_MAX_POINTS = 50
LEBL_ANIM_FLIGHT_LIMIT    = None
LEBL_SPEED_SIM_SEC = {1:1, 2:5, 4:120, 8:900, 16:3600}

def PathBearingDeg(lat1, lon1, lat2, lon2):
    """Angulo en grados de la direccion entre dos puntos del mapa
    (para orientar el triangulo del avion)."""
    r = math.pi/180; y = math.sin((lon2-lon1)*r)*math.cos(lat2*r)
    x = math.cos(lat1*r)*math.sin(lat2*r)-math.sin(lat1*r)*math.cos(lat2*r)*math.cos((lon2-lon1)*r)
    return (math.degrees(math.atan2(y,x))+360)%360

def MoveAlongTimedPath(path, elapsed_ms):
    """Dado cuantos milisegundos han pasado en la animacion, devuelve
    en que punto de la ruta esta el avion, si ya llego al final y el rumbo."""
    if not path: return None,None,0.0,True
    if elapsed_ms >= path[-1]["t"]:
        l,p = path[-1], path[-2] if len(path)>1 else path[-1]
        return l["lat"],l["lon"],PathBearingDeg(p["lat"],p["lon"],l["lat"],l["lon"]),True
    i = 0
    while i+1<len(path) and path[i+1]["t"]<=elapsed_ms: i+=1
    a,b = path[i],path[i+1]; frac=(elapsed_ms-a["t"])/max(1.0,b["t"]-a["t"])
    return a["lat"]+frac*(b["lat"]-a["lat"]),a["lon"]+frac*(b["lon"]-a["lon"]),\
           PathBearingDeg(a["lat"],a["lon"],b["lat"],b["lon"]),False

def SegmentInBounds(coords, min_lat, max_lat, min_lon, max_lon):
    """Comprueba si algun punto de un tramo cae dentro del rectangulo visible del mapa."""
    return any(min_lat<=lat<=max_lat and min_lon<=lon<=max_lon for lat,lon in coords)

def ComputeLeblViewBounds(stands, txl_paths=None, operations=None, margin=0.04):
    """Calcula el rectangulo minimo de lat/lon que engloba stands,
    taxiways y rutas de vuelos, con un margen, para encuadrar el mapa."""
    lats = [s["lat"] for s in stands]; lons = [s["lon"] for s in stands]
    c_lat,c_lon = (min(lats)+max(lats))/2,(min(lons)+max(lons))/2
    lat_h = max((max(lats)-min(lats))*.58,.011)*(1+margin)
    lon_h = max((max(lons)-min(lons))*.58,.014)*(1+margin)
    b = [c_lat-lat_h, c_lat+lat_h, c_lon-lon_h, c_lon+lon_h]
    if txl_paths:
        for seg in txl_paths:
            if seg["type"]!="Runway" or not SegmentInBounds(seg["coords"],b[0],b[1],b[2],b[3]): continue
            for lat,lon in seg["coords"]:
                b[0]=min(b[0],lat);b[1]=max(b[1],lat);b[2]=min(b[2],lon);b[3]=max(b[3],lon)
        pl,pn=(b[1]-b[0])*.02 or .0002,(b[3]-b[2])*.02 or .0002
        b[0]-=pl;b[1]+=pl;b[2]-=pn;b[3]+=pn
    return tuple(b)

def MakeMapProjector(min_lat, max_lat, min_lon, max_lon, w, h, pad=6):
    """Convierte coordenadas geograficas a pixeles del canvas
    segun el tamano de la ventana y el rectangulo visible."""
    lat_span,lon_span = max_lat-min_lat or .001, max_lon-min_lon or .001
    cos_lat = math.cos(math.radians((min_lat+max_lat)/2))
    scale = min((w-2*pad)/(lon_span*cos_lat),(h-2*pad)/lat_span)
    cw,ch = lon_span*cos_lat*scale, lat_span*scale
    ox,oy = (w-cw)/2, (h-ch)/2
    def to_xy(lat,lon): return ox+(lon-min_lon)*cos_lat*scale, oy+(max_lat-lat)*scale
    return to_xy

def PlaneTriangleXy(x, y, brg, size=9.0):
    """Calcula las tres esquinas de un triangulo pequeno que representa el avion
    en pantalla, mirando hacia el rumbo indicado."""
    r=math.radians(brg); fx,fy=math.sin(r),-math.cos(r); px,py=-fy,fx
    nx,ny=x+fx*size,y+fy*size
    lx=x-fx*size*.55+px*size*.4; ly=y-fy*size*.55+py*size*.4
    rx=x-fx*size*.55-px*size*.4; ry=y-fy*size*.55-py*size*.4
    return [nx,ny,lx,ly,rx,ry]

def SimplifyTxlForDisplay(txl_paths, view_bounds=None, max_per_seg=22):
    out = []
    """Quita puntos de mas de los taxiways para dibujar el mapa
    sin ralentizar, opcionalmente solo lo visible."""
    for seg in txl_paths:
        coords = seg["coords"]
        if len(coords)<2: continue
        if view_bounds and seg["type"]!="Runway" and not SegmentInBounds(coords,*view_bounds[:2],*view_bounds[2:]): continue
        if len(coords)>max_per_seg:
            step=max(1,len(coords)//max_per_seg); coords=coords[::step]
            if coords[-1]!=seg["coords"][-1]: coords=coords+[seg["coords"][-1]]
        out.append({"type":seg["type"],"coords":coords})
    return out

def CreateLEBLAnimationWidget(parent, data):
    """
    En el frame de la interfaz se crea un lienzo (canvas) con el mapa del aeropuerto,
    un reloj que avanza segun la velocidad elegida y triangulos que son los aviones.
    Cada cierto tiempo se actualiza la posicion segun la ruta calculada antes.
    Devuelve funciones para parar la animacion y reiniciar el dibujo.
    """
    import tkinter as tk
    from tkinter import ttk
    ops,stands,txl_paths,sim_start_mins = data["operations"],data["stands"],data["txl_paths"],data["sim_start_mins"]
    stand_by_id = {s["id"]:s for s in stands}
    active_gates = {op.get("assignedGate") or op["gate"] for op in ops}
    bounds = data.get("view_bounds") or ComputeLeblViewBounds(stands)
    min_lat,max_lat,min_lon,max_lon = bounds

    toolbar = ttk.Frame(parent); toolbar.pack(fill="x",padx=4,pady=2)
    clock_lbl = ttk.Label(toolbar, text="00:00:00", font=("Consolas",12,"bold")); clock_lbl.pack(side="left",padx=8)
    ttk.Label(toolbar,text="Velocidad:").pack(side="right",padx=(8,2))
    map_frame = ttk.Frame(parent); map_frame.pack(fill="both",expand=True)
    cv = tk.Canvas(map_frame, bg="#eef2f3", highlightthickness=0); cv.pack(fill="both",expand=True)

    st = {"speed":2,"anchor_wall":None,"anchor_sim_ms":0.0,"running":True,"map_ready":False,
          "to_xy":None,"gate_items":{},"plane_items":[],"after_id":None,"init_after_id":None,
          "resize_after_id":None,"last_size":(0,0),
          "plane_states":[{"phase":"parked" if op.get("startParked") else "hidden","phase_start_sim":0.0}
                          for op in ops]}

    def fmt(ms):
        t=sim_start_mins*60+(ms/MS_PER_SIM_MINUTE)*60
        return f"{int(t//3600)%24:02d}:{int(t%3600//60):02d}:{int(t%60):02d}"

    def rate(): return (LEBL_SPEED_SIM_SEC[st["speed"]]/60)*MS_PER_SIM_MINUTE/1000

    def get_sim():
        w=time.time()*1000
        if st["anchor_wall"] is None: st["anchor_wall"]=w; st["anchor_sim_ms"]=0.0; return 0.0
        return st["anchor_sim_ms"]+(w-st["anchor_wall"])*rate()

    def set_speed(s):
        w=time.time()*1000
        if st["anchor_wall"]: st["anchor_sim_ms"]=get_sim(); st["anchor_wall"]=w
        st["speed"]=s

    def gate_style(occ): return ("#e74c3c","#c0392b") if occ else ("#2ecc71","#27ae60")

    def set_gate(gid, occ):
        items=st["gate_items"].get(gid)
        if items: fill,out=gate_style(occ); cv.itemconfigure(items["oval"],fill=fill,outline=out)

    def draw_map(w,h):
        cv.delete("static","plane")
        to_xy=MakeMapProjector(min_lat,max_lat,min_lon,max_lon,w,h); st["to_xy"]=to_xy
        for seg in txl_paths:
            c=seg["coords"]
            if len(c)<2 or not SegmentInBounds(c,min_lat,max_lat,min_lon,max_lon): continue
            pts=[coord for lat,lon in c for coord in to_xy(lat,lon)]
            kw=dict(fill="#1a252f",width=5,capstyle=tk.ROUND) if seg["type"]=="Runway" else dict(fill="#2471a3",width=2)
            cv.create_line(*pts,tags="static",**kw)
        st["gate_items"]={}
        for s in stands:
            gid=s["id"]
            if gid not in active_gates and not SegmentInBounds([[s["lat"],s["lon"]]],min_lat,max_lat,min_lon,max_lon): continue
            x,y=to_xy(s["lat"],s["lon"])
            oval=cv.create_oval(x-7,y-7,x+7,y+7,fill="#2ecc71",outline="#27ae60",width=1,tags="static")
            if gid in active_gates: cv.create_text(x,y-10,text=gid,fill="#1a5276",font=("Segoe UI",8,"bold"),tags="static")
            st["gate_items"][gid]={"oval":oval}
        st["plane_items"]=[]
        for i,op in enumerate(ops):
            gate=op.get("assignedGate") or op["gate"]
            ap=op.get("arrivalPath")
            lat0,lon0=(ap[0]["lat"],ap[0]["lon"]) if ap else (stand_by_id.get(gate,stands[0])["lat"],stand_by_id.get(gate,stands[0])["lon"])
            x,y=to_xy(lat0,lon0)
            hidden=not op.get("startParked")
            pid=cv.create_polygon(*PlaneTriangleXy(x,y,0,11),fill="#555",outline="#333",
                                   state=tk.HIDDEN if hidden else tk.NORMAL,tags="plane")
            st["plane_items"].append(pid)
            if op.get("startParked"): st["plane_states"][i]["phase"]="parked"; set_gate(gate,True)
        st["map_ready"]=True; st["last_size"]=(w,h)

    def _alive():
        try: return bool(st["running"] and cv.winfo_exists())
        except tk.TclError: return False

    def _update(sim_ms):
        if not st["map_ready"] or not st["to_xy"]: return
        to_xy=st["to_xy"]
        for i,op in enumerate(ops):
            ps=st["plane_states"][i]; pid=st["plane_items"][i]
            gate=op.get("assignedGate") or op["gate"]
            arr_s=op.get("arrivalStartMs",-1); dep_s=op.get("departureStartMs")
            if ps["phase"]=="hidden" and arr_s>=0 and sim_ms>=arr_s:
                ps["phase"]="arriving"; ps["phase_start_sim"]=sim_ms; cv.itemconfigure(pid,state=tk.NORMAL)
            if ps["phase"]=="arriving":
                lat,lon,brg,done=MoveAlongTimedPath(op["arrivalPath"],sim_ms-ps["phase_start_sim"])
                x,y=to_xy(lat,lon); cv.coords(pid,*PlaneTriangleXy(x,y,brg,11))
                if done: ps["phase"]="parked"; set_gate(gate,True)
            if ps["phase"]=="parked" and dep_s is not None and sim_ms>=dep_s:
                ps["phase"]="departing"; ps["phase_start_sim"]=sim_ms; set_gate(gate,False)
            if ps["phase"]=="departing":
                lat,lon,brg,done=MoveAlongTimedPath(op["departurePath"],sim_ms-ps["phase_start_sim"])
                x,y=to_xy(lat,lon); cv.coords(pid,*PlaneTriangleXy(x,y,brg,11))
                if done: ps["phase"]="gone"; cv.itemconfigure(pid,state=tk.HIDDEN)
            if ps["phase"]=="parked":
                s2=stand_by_id.get(gate,stands[0]); x,y=to_xy(s2["lat"],s2["lon"])
                cv.coords(pid,*PlaneTriangleXy(x,y,0,11)); cv.itemconfigure(pid,state=tk.NORMAL); set_gate(gate,True)

    def _sync(sim_ms):
        if not st["to_xy"]: return
        to_xy=st["to_xy"]
        for i,op in enumerate(ops):
            ps=st["plane_states"][i]; pid=st["plane_items"][i]
            gate=op.get("assignedGate") or op["gate"]
            dep_ms=op.get("departureStartMs"); arr_s=op.get("arrivalStartMs",-1)
            arr_e=arr_s+op["arrivalDurationMs"] if arr_s>=0 else -1
            stand=stand_by_id.get(gate,stands[0])
            def _park():
                ps["phase"]="parked"; ps["phase_start_sim"]=0.0
                x,y=to_xy(stand["lat"],stand["lon"]); cv.coords(pid,*PlaneTriangleXy(x,y,0,11))
                cv.itemconfigure(pid,state=tk.NORMAL); set_gate(gate,True)
            def _dep(start_ms):
                ps["phase"]="departing"
                if ps["phase_start_sim"]<=0: ps["phase_start_sim"]=start_ms
                lat,lon,brg,_=MoveAlongTimedPath(op["departurePath"],sim_ms-start_ms)
                x,y=to_xy(lat,lon); cv.coords(pid,*PlaneTriangleXy(x,y,brg,11)); cv.itemconfigure(pid,state=tk.NORMAL)
            def _gone(): ps["phase"]="gone"; cv.itemconfigure(pid,state=tk.HIDDEN)
            if op.get("startParked"):
                if dep_ms is not None and sim_ms>=dep_ms:
                    dep_end=dep_ms+op.get("departureDurationMs",0)
                    _dep(dep_ms) if sim_ms<dep_end else _gone()
                    if sim_ms<dep_end: set_gate(gate,False)
                else: _park()
                continue
            if arr_s<0 or sim_ms<arr_s: ps["phase"]="hidden"; ps["phase_start_sim"]=0.0; cv.itemconfigure(pid,state=tk.HIDDEN); continue
            if arr_e>=0 and sim_ms<arr_e:
                ps["phase"]="arriving"
                if ps["phase_start_sim"]<=0: ps["phase_start_sim"]=op["arrivalStartMs"]
                lat,lon,brg,_=MoveAlongTimedPath(op["arrivalPath"],sim_ms-ps["phase_start_sim"])
                x,y=to_xy(lat,lon); cv.coords(pid,*PlaneTriangleXy(x,y,brg,11)); cv.itemconfigure(pid,state=tk.NORMAL)
                continue
            if dep_ms is None or sim_ms<dep_ms: _park(); continue
            dep_end=dep_ms+op["departureDurationMs"]
            if sim_ms<dep_end: _dep(dep_ms); set_gate(gate,False)
            else: _gone()

    def _sched_resize(w,h):
        lw,lh=st["last_size"]
        if abs(w-lw)<6 and abs(h-lh)<6: return
        rid=st.get("resize_after_id")
        if rid:
            try: cv.after_cancel(rid)
            except: pass
        def _do():
            st["resize_after_id"]=None
            if not _alive(): return
            cv.update_idletasks(); cw,ch=cv.winfo_width(),cv.winfo_height()
            if cw<80 or ch<80: return
            draw_map(cw,ch); _sync(get_sim())
        st["resize_after_id"]=cv.after(120,_do)

    def try_init():
        if not _alive() or st["map_ready"]: return
        cv.update_idletasks(); w,h=cv.winfo_width(),cv.winfo_height()
        if w>=80 and h>=80: draw_map(w,h); _update(get_sim()); return
        st["init_after_id"]=cv.after(100,try_init)

    def tick():
        if not _alive(): stop(); return
        try:
            sim_ms=get_sim(); clock_lbl.config(text=fmt(sim_ms)); _update(sim_ms)
        except tk.TclError: stop(); return
        st["after_id"]=cv.after(33,tick)

    def stop():
        st["running"]=False
        for k in ("after_id","init_after_id","resize_after_id"):
            if st.get(k):
                try: cv.after_cancel(st[k])
                except: pass
                st[k]=None
        try: cv.unbind("<Configure>"); map_frame.unbind("<Configure>")
        except: pass

    spd_btns=[]
    def mark_speed(s):
        for b,v in spd_btns: b.state(["pressed"] if v==s else ["!pressed"])
    def on_speed(s): set_speed(s); mark_speed(s)
    for s,lbl in [(1,"x1"),(2,"x2"),(4,"x4"),(8,"x8"),(16,"x16")]:
        b=ttk.Button(toolbar,text=lbl,width=3,command=lambda s=s:on_speed(s))
        b.pack(side="right",padx=1); spd_btns.append((b,s))
    mark_speed(2)

    def _on_conf(e):
        w,h=e.width,e.height
        if w<80 or h<80: return
        if not st["map_ready"]: draw_map(w,h); _update(get_sim()); return
        _sched_resize(w,h)
    def _on_dest(_=None): stop()
    cv.bind("<Configure>",_on_conf); cv.bind("<Destroy>",_on_dest,add="+")
    map_frame.bind("<Destroy>",_on_dest,add="+")
    cv.after(50,try_init); tick()
    return {"stop":stop,"canvas":cv,"init":try_init}

def GenerateLEBLAnimation(arrivals_path, limit=None,
                           gate_assignments=None, bcn_airport=None, departures_path=None):
    """
    Se cargan los archivos AIP y TXL, los vuelos de llegada (y salida si hay),
    y opcionalmente las puertas ya asignadas desde LEBL.
    Con PrepareOperations se calculan trayectos y tiempos de cada avion.
    Se devuelve un diccionario con operaciones, stands, limites del mapa y contadores
    para que la interfaz pueda dibujar la animacion.
    """
    aip_text = LeblLoadAipTextStand(LeblAipPath())
    stands = ParseAipStands(aip_text, categories={"airline"})
    stand_ids = sorted(PASSENGER_AIRLINE_STANDS & {s["id"] for s in stands})
    stand_set = set(stand_ids)
    txl_paths = ParseTxlPaths(LeblTxlPath())

    flights = (MergeArrivalsDepartures(arrivals_path, departures_path, stand_ids)
               if departures_path and os.path.isfile(departures_path)
               else ParseFlightsFile(arrivals_path, stand_ids))
    if not flights: raise ValueError("No hay vuelos validos en el archivo de llegadas.")

    if gate_assignments is None and bcn_airport is not None:
        gate_assignments = BuildGateAssignmentsForFlights(bcn_airport, flights, stand_ids)

    if gate_assignments or bcn_airport is not None:
        enriched = []
        for f in flights:
            assigned = (gate_assignments or {}).get(FlightRecordGateKey(f))
            if not assigned and bcn_airport is not None:
                assigned = DefaultStandForAirline(bcn_airport, f.airline, stand_ids, f.aircraft, f.arrival)
            enriched.append(
                FlightRecord(f.aircraft,f.origin,f.arrival,f.departure,f.airline,
                             f.arr_runway,f.dep_runway,assigned,f.destination)
                if assigned and assigned in stand_set
                else CompleteMissingFields(f, stand_ids)
            )
        flights = enriched

    ops, sim_start = PrepareOperations(flights, stands, txl_paths, limit=limit)
    for op in ops:
        op["arrivalPath"] = DecimateTimedPath(op["arrivalPath"])
        if op["departurePath"]: op["departurePath"] = DecimateTimedPath(op["departurePath"])

    view_bounds = ComputeLeblViewBounds(stands, txl_paths)
    valid_flights = [f for f in flights if f.gate in stand_set and ClassifyAnimationFlight(f)!="skip"]
    return {
        "operations": ops, "stands": stands, "sim_start_mins": sim_start, "view_bounds": view_bounds,
        "txl_paths": SimplifyTxlForDisplay(txl_paths, view_bounds),
        "total_flights": len(flights), "valid_flights": len(valid_flights),
        "departures_from_file": bool(departures_path and os.path.isfile(departures_path)),
    }


# Pruebas rapidas al ejecutar este archivo directamente
if __name__ == "__main__":
    BASE_DIR = TestsProjectRoot()
    DATA = os.path.join(BASE_DIR, "data")
    OUT = os.path.join(BASE_DIR, "output")
    if not os.path.exists(OUT):
        os.makedirs(OUT)

    arrivals_path = os.path.join(DATA, "Arrivals.txt")
    departures_path = os.path.join(DATA, "Departures.txt")
    airports_path = os.path.join(DATA, "Airports.txt")
    structure_path = os.path.join(DATA, "Terminals.txt")

    print("--- LoadArrivals ---")
    aircraft = LoadArrivals(arrivals_path)
    print("vuelos cargados:", len(aircraft))

    print("--- LoadAirports (dict) ---")
    airports_db = LoadAirports(airports_path)
    print("aeropuertos en db:", len(airports_db))

    if aircraft:
        print("--- PlotArrivals / PlotAirlines / PlotFlightsType ---")
        PlotArrivals(aircraft)
        PlotAirlines(aircraft)
        PlotFlightsType(aircraft)

        print("--- SaveFlights ---")
        res = SaveFlights(aircraft, os.path.join(OUT, "salida_test.txt"))
        print("SaveFlights devolvio:", res)

        print("--- MapFlights ---")
        res = MapFlights(aircraft, airports_db)
        print("MapFlights devolvio:", res)

        print("--- LongDistanceArrivals ---")
        largos, co2, medio = LongDistanceArrivals(aircraft, airports_db)
        print("larga distancia:", len(largos), "co2 total:", co2, "medio:", medio)

        print("--- MapLongDistanceFlights ---")
        res = MapLongDistanceFlights(aircraft, airports_db)
        print("MapLongDistanceFlights devolvio:", res)

    print("--- LoadDepartures ---")
    departures, st = LoadDepartures(departures_path)
    print("salidas:", len(departures), "status:", st)

    if aircraft and departures:
        print("--- MergeMovements ---")
        all_movements = MergeMovements(aircraft, departures)
        if all_movements != -1:
            print("movimientos:", len(all_movements))
            print("--- NightAircraft ---")
            noches = NightAircraft(all_movements)
            print("nocturnos:", len(noches) if noches != -1 else noches)

            try:
                from src.LEBL import LoadAirportStructure
            except ImportError:
                from LEBL import LoadAirportStructure

            bcn = LoadAirportStructure(structure_path)
            if bcn != -1:
                print("--- PlotDayOccupancy ---")
                PlotDayOccupancy(bcn, all_movements)
                print("--- AssignNightGates ---")
                print("AssignNightGates:", AssignNightGates(bcn, all_movements))

    plt.show()
    print("Fin tests aircraft.py")