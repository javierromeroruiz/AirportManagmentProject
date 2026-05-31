import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
import math
import time
import heapq
import re
import random
import copy
import xml.etree.ElementTree as ET
from collections import defaultdict
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


# ===============================================================
#  FUNCIONES EXTRAS — Utilidades internas (graficos / salida)
#  No aparecen en el enunciado del proyecto
# ===============================================================

def _tests_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _output_dir():
    return os.path.join(_tests_project_root(), "output")


def _ensure_output_dir():
    out = _output_dir()
    if not os.path.exists(out):
        os.makedirs(out)
    return out


def _flights_kml_path():
    return os.path.join(_output_dir(), "flights.kml")


def _setup_plot_style():
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


def _style_axes(ax, *, title, subtitle=None, xlabel=None, ylabel=None):
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


def _bar_value_labels(ax, bars, fmt="{:.0f}", offset=0.03, horizontal=False):
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


def _save_and_show(fig, filename):
    _ensure_output_dir()
    fig.savefig(
        f"output/{filename}",
        dpi=160,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    plt.show()


# ===============================================================
#  FUNCIONES PROYECTO — aircraft.py (enunciado V2 + V4)
#  V2 — Clase Aircraft; LoadArrivals, PlotArrivals, SaveFlights, PlotAirlines,
#       PlotFlightsType, MapFlights, LongDistanceArrivals
#  V4 — LoadDepartures, MergeMovements, NightAircraft, AssignNightGates,
#       FreeGate, AssignGatesAtTime, PlotDayOccupancy
# ===============================================================

class Aircraft:
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


def LoadArrivals(filename):
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
    _setup_plot_style()

    rangos = [0] * 24
    for ac in aircraft:
        if ac.arrival:
            rangos[int(ac.arrival.split(":")[0])] += 1

    total = sum(rangos)
    peak_h = max(range(24), key=lambda h: rangos[h]) if total else 0
    horas_labels = [f"{h:02d}h" for h in range(24)]

    fig, ax = plt.subplots(figsize=(10.5, 4.8), facecolor=CHART["bg"])
    colors = [
        CHART["primary"] if v == max(rangos) and v > 0 else CHART["primary_light"]
        for v in rangos
    ]
    bars = ax.bar(
        horas_labels, rangos, color=colors,
        edgecolor="white", linewidth=0.8, width=0.78, zorder=3,
    )

    _style_axes(
        ax,
        title="Distribución de llegadas por hora",
        subtitle=f"LEBL · {total} vuelos · pico a las {peak_h:02d}:00 ({rangos[peak_h]} llegadas)" if total else "Sin datos de llegada",
        xlabel="Franja horaria (UTC local)",
        ylabel="Número de vuelos",
    )
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis="y", zorder=0)
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f"{h:02d}h" for h in range(0, 24, 2)])
    if total:
        _bar_value_labels(ax, [b for b in bars if b.get_height() == max(rangos)])

    fig.text(0.99, 0.02, "Fuente: datos de llegadas cargados", ha="right", fontsize=7, color=CHART["muted"])
    fig.tight_layout()
    _save_and_show(fig, "arrivals_distribution.png")


def SaveFlights(aircraft, filename):
    if not aircraft:
        return -1
    try:
        with open(filename, "w") as file:
            file.write("AIRCRAFT ORIGIN ARRIVAL AIRLINE\n")

            for ac in aircraft:
                aircraft_id = ac.id or "-"
                airline_company = ac.airline or "-"
                origin_airport = ac.origin or "-"
                time_of_landing = ac.arrival or "-"

                file.write(
                    f"{aircraft_id} {origin_airport} {time_of_landing} {airline_company}\n"
                )

        return 0

    except IOError:
        return -1


def PlotAirlines(aircraft):
    if not aircraft:
        return -1

    _setup_plot_style()

    airlines = {}
    for ac in aircraft:
        if ac.airline:
            airlines[ac.airline] = airlines.get(ac.airline, 0) + 1

    ranked = sorted(airlines.items(), key=lambda item: item[1], reverse=True)
    names = [name for name, _ in ranked]
    counts = [count for _, count in ranked]
    total = sum(counts)

    n = len(names)
    horizontal = n > 6
    fig_h = max(4.2, min(8.0, 0.38 * n + 2.2)) if horizontal else 5.0
    fig, ax = plt.subplots(
        figsize=(10.5, fig_h if horizontal else 5.0),
        facecolor=CHART["bg"],
    )

    cmap = plt.cm.Greens
    norm_counts = [c / max(counts) for c in counts]
    bar_colors = [cmap(0.35 + 0.55 * t) for t in norm_counts]

    if horizontal:
        bars = ax.barh(names, counts, color=bar_colors, edgecolor="white", linewidth=0.8, height=0.72)
        ax.invert_yaxis()
        _style_axes(
            ax,
            title="Vuelos por aerolínea",
            subtitle=f"{n} aerolíneas · {total} vuelos en total",
            xlabel="Número de vuelos",
        )
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.grid(axis="x", zorder=0)
        _bar_value_labels(ax, bars, horizontal=True)
    else:
        bars = ax.bar(names, counts, color=bar_colors, edgecolor="white", linewidth=0.8, width=0.65)
        _style_axes(
            ax,
            title="Vuelos por aerolínea",
            subtitle=f"{n} aerolíneas · {total} vuelos en total",
            xlabel="Aerolínea (código IATA)",
            ylabel="Número de vuelos",
        )
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.grid(axis="y", zorder=0)
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        _bar_value_labels(ax, bars)

    fig.tight_layout()
    _save_and_show(fig, "cantidad_airlines.png")
    return 0


def PlotFlightsType(aircraft):
    if not aircraft:
        return -1

    _setup_plot_style()

    count_schengen = 0
    count_no_schengen = 0

    for ac in aircraft:
        if not ac.origin:
            continue
        if str(ac.origin[:2]) in SCHENGEN_PREFIXES:
            count_schengen += 1
        else:
            count_no_schengen += 1

    total = count_schengen + count_no_schengen
    if total == 0:
        return -1

    sizes = [count_schengen, count_no_schengen]
    labels = ["Espacio Schengen", "Fuera de Schengen"]
    colors = [CHART["schengen"], CHART["non_schengen"]]
    explode = (0.03, 0.03)

    fig, (ax_pie, ax_bar) = plt.subplots(
        1, 2, figsize=(10.5, 4.6), facecolor=CHART["bg"],
        gridspec_kw={"width_ratios": [1.05, 1]},
    )

    wedges, texts, autotexts = ax_pie.pie(
        sizes,
        labels=labels,
        colors=colors,
        explode=explode,
        autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct * total / 100))})",
        startangle=90,
        counterclock=False,
        wedgeprops={"linewidth": 1.2, "edgecolor": "white"},
        textprops={"fontsize": 9, "color": CHART["text"]},
        pctdistance=0.72,
    )
    for t in autotexts:
        t.set_fontsize(8)
        t.set_fontweight("bold")
        t.set_color("white")

    ax_pie.set_title("Origen de los vuelos", loc="left", color=CHART["text"], fontweight="bold", pad=10)

    categories = labels
    x_pos = range(len(categories))
    bars = ax_bar.bar(
        x_pos, sizes, color=colors,
        edgecolor="white", linewidth=1.0, width=0.55, zorder=3,
    )
    ax_bar.set_xticks(x_pos)
    ax_bar.set_xticklabels(categories, fontsize=9)
    _style_axes(
        ax_bar,
        title="Comparativa absoluta",
        subtitle=f"{total} vuelos con origen conocido",
        ylabel="Número de vuelos",
    )
    ax_bar.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax_bar.grid(axis="y", zorder=0)
    _bar_value_labels(ax_bar, bars)

    legend_handles = [
        Patch(facecolor=CHART["schengen"], edgecolor="white", label="Schengen"),
        Patch(facecolor=CHART["non_schengen"], edgecolor="white", label="No Schengen"),
    ]
    fig.legend(
        handles=legend_handles, loc="lower center", ncol=2,
        bbox_to_anchor=(0.5, -0.02), fontsize=9,
    )

    fig.suptitle(
        "Clasificación Schengen de aeropuertos de origen",
        x=0.02, y=0.98, ha="left", fontsize=12, fontweight="bold", color=CHART["text"],
    )
    fig.subplots_adjust(left=0.08, right=0.98, top=0.86, bottom=0.16, wspace=0.32)
    _save_and_show(fig, "schengen_distribution.png")
    return 0


# --- Extra auxiliar: dict ICAO→coordenadas para MapFlights (no en enunciado) ---

def LoadAirports(filename):
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


def MapFlights(aircraft, airports_db):
    if "LEBL" not in airports_db:
        return -1

    lat_dest, lon_dest = airports_db["LEBL"]

    _ensure_output_dir()
    kml_path = _flights_kml_path()
    routes = 0

    with open(kml_path, "w", encoding="utf-8") as f:
        f.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        f.write("<Document>\n")

        for ac in aircraft:
            orig = (ac.origin or ac.origin_airport or "").strip()
            if _blank_movement_time(orig):
                continue

            if orig in airports_db:
                routes += 1
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
                    + "</color><width>2</width></LineStyle></Style>\n"
                )
                f.write("   <LineString>\n")
                f.write("   <coordinates>\n")
                f.write(f"   {lon_orig},{lat_orig},0 ")
                f.write(f"{lon_dest},{lat_dest},0\n")
                f.write("   </coordinates>\n")
                f.write("   </LineString>\n")
                f.write("   </Placemark>\n")

        f.write("</Document>\n")
        f.write("</kml>\n")

    if routes == 0:
        return -1
    return 0


def LongDistanceArrivals(aircraft, airports_db):
    long_distance_list = []
    total_co2_kg = 0.0
    cont_flights = 0

    if "LEBL" not in airports_db:
        return long_distance_list, 0.0, 0.0

    lat_dest, lon_dest = airports_db["LEBL"]
    R = 6371.0

    for ac in aircraft:
        orig = (ac.origin or ac.origin_airport or "").strip()
        if _blank_movement_time(orig):
            continue

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

            if dist > 2000:
                long_distance_list.append(ac)
                total_co2_kg += 18 * dist
                cont_flights += 1

    total_tons = total_co2_kg / 1000
    med_tons = total_tons / cont_flights if cont_flights > 0 else 0.0

    return long_distance_list, total_tons, med_tons


# --- Version 4 (enunciado): salidas, merge, puertas nocturnas, ocupacion ---

def LoadDepartures(filename):
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


def _blank_movement_time(value):
    return value in ("", "-", None)


def _time_to_minutes(hhmm):
    if not hhmm or ":" not in hhmm:
        return None
    parts = hhmm.strip().split(":")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]) * 60 + int(parts[1])
    except ValueError:
        return None


# Umbral para emparejar pernocta (llegada tarde + salida madrugada al dia siguiente)
_OVERNIGHT_ARR_FROM = 18 * 60   # llegada desde las 18:00
_OVERNIGHT_DEP_UNTIL = 9 * 60   # salida madrugada hasta las 09:00 (dia siguiente)


def _overnight_pair_compatible(arr_m, dep_m):
    """Salida al dia siguiente: en reloj 24h la hora de salida es menor que la de llegada."""
    return arr_m > dep_m and arr_m >= _OVERNIGHT_ARR_FROM and dep_m < _OVERNIGHT_DEP_UNTIL


def MergeMovements(arrivals, departures):
    """
    Combina llegadas y salidas con el mismo id cuando los horarios son compatibles
    (hora de llegada anterior a la de salida en el mismo dia).

    Puede haber varios movimientos del mismo avion en un dia; cada llegada se empareja
    con la salida compatible mas temprana aun no usada. Las pernoctas (llegada tarde y
    salida madrugada) se fusionan en un segundo paso. Quedan sin pareja los que solo
    tienen llegada o solo salida en el dia (night aircraft).
    Devuelve -1 si alguna lista de entrada esta vacia.
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
            key=lambda a: _time_to_minutes(a.arrival) if _time_to_minutes(a.arrival) is not None else -1,
        )
        deps = sorted(
            dep_by_id.get(ac_id, []),
            key=lambda d: _time_to_minutes(d.departure) if _time_to_minutes(d.departure) is not None else -1,
        )
        used_dep = [False] * len(deps)
        id_merged = []

        # Paso 1: mismo dia (llegada < salida)
        for arr in arrs:
            merged = copy.copy(arr)
            arr_m = _time_to_minutes(arr.arrival)

            if arr_m is not None:
                best_j = -1
                best_dep_m = None
                j = 0
                while j < len(deps):
                    if not used_dep[j]:
                        dep_m = _time_to_minutes(deps[j].departure)
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

        # Paso 2: pernocta (llegada tarde + salida madrugada del dia siguiente)
        for merged in id_merged:
            if not _blank_movement_time(merged.departure):
                continue
            arr_m = _time_to_minutes(merged.arrival)
            if arr_m is None:
                continue

            best_j = -1
            best_dep_m = None
            j = 0
            while j < len(deps):
                if not used_dep[j]:
                    dep_m = _time_to_minutes(deps[j].departure)
                    if dep_m is not None and _overnight_pair_compatible(arr_m, dep_m):
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
    Aviones que pernoctan en LEBL: solo llegada, solo salida, o llegada+salida con
    salida al dia siguiente (hora de salida <= hora de llegada en reloj 24h).
    """
    if not aircrafts:
        return -1

    night_list = []
    for plane in aircrafts:
        arr_blank = _blank_movement_time(plane.arrival)
        dep_blank = _blank_movement_time(plane.departure)

        if arr_blank and not dep_blank:
            night_list.append(plane)
            continue
        if not arr_blank and dep_blank:
            night_list.append(plane)
            continue

        arr_m = _time_to_minutes(plane.arrival)
        dep_m = _time_to_minutes(plane.departure)
        if arr_m is not None and dep_m is not None and dep_m <= arr_m:
            night_list.append(plane)

    return night_list


def AssignNightGates(bcn, aircrafts):
    from src.LEBL import AssignGate

    if not aircrafts:
        return -1

    nights = NightAircraft(aircrafts)
    if nights == -1:
        return -1
    for plane in nights:
        AssignGate(bcn, plane)

    return 0


def FreeGate(bcn, id):
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
    from src.LEBL import AssignGate

    # 1. Liberar las puertas de aviones que despegan
    i = 0
    while i < len(aircrafts):
        plane = aircrafts[i]

        if plane.departure != "-":
            dep_parts = plane.departure.split(":")
            dep_mins = (int(dep_parts[0]) * 60) + int(dep_parts[1])

            if dep_mins == current_mins:
                FreeGate(bcn, plane.id)
        i += 1

    # 2. Asignar puertas a los que aterrizan
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
    _setup_plot_style()

    # Asignacion de la noche
    AssignNightGates(bcn, aircrafts)

    hours_labels = [f"{h:02d}" for h in range(24)]
    occupied_gates_per_hour = [0] * 24
    rejected_per_hour = [0] * 24

    # Simulamos el dia por horas
    m = 0
    total_occ = 0
    while m < 1440:
        hour_index = m // 60

        rejected = AssignGatesAtTime(bcn, aircrafts, m)
        rejected_per_hour[hour_index] += rejected

        # Contamos numero de puertas ocupadas
        if m % 60 == 59:
            total_occ = 0

            i = 0
            while i < len(bcn.terminal):
                terminal = bcn.terminal[i]

                j = 0
                while j < len(terminal.boarding_area):
                    area = terminal.boarding_area[j]

                    k = 0
                    while k < len(area.gate):
                        gate = area.gate[k]

                        if gate.occupancy == True:
                            total_occ += 1
                        k += 1  # <-- Mantenido dentro del bucle de puertas
                    j += 1  # <-- Mantenido dentro del bucle de áreas
                i += 1  # <-- Mantenido dentro del bucle de terminales

            occupied_gates_per_hour[hour_index] = total_occ
        else:
            occupied_gates_per_hour[hour_index] = total_occ
        m += 1

    fig, ax = plt.subplots(figsize=(10.5, 5.0), facecolor=CHART["bg"])

    ax.bar(
        hours_labels, occupied_gates_per_hour,
        color=CHART["primary_light"], edgecolor="white", width=0.45, label="Puertas Ocupadas", zorder=3
    )
    ax.bar(
        hours_labels, rejected_per_hour,
        bottom=occupied_gates_per_hour,
        color=CHART["non_schengen"], edgecolor="white", width=0.45, label="Aviones No Asignados", zorder=3
    )

    _style_axes(
        ax,
        title="Ocupación de Puertas y Saturación del Aeropuerto",
        subtitle="Evolución del tráfico diario en Barcelona-El Prat",
        xlabel="Franja horaria simulada",
        ylabel="Número de aviones"
    )
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis="y", zorder=0)
    ax.legend(loc="upper right")

    fig.tight_layout()
    _save_and_show(fig, "day_occupancy_simulation.png")


# ===============================================================
#  FUNCIONES EXTRAS — Animacion LEBL, rutas taxi, formato ampliado
# ===============================================================

# ── Rutas ────────────────────────────────────────────────────────────────────
def _lebl_aip_path():     return os.path.join(_tests_project_root(), "data", "lebl_pdc_aip.txt")
def _lebl_txl_path():     return os.path.join(_tests_project_root(), "data", "LEBL_Taxiways.txl")

def _lebl_load_aip_text_stand(path):
    if not os.path.exists(path): raise FileNotFoundError(f"No se encontro el archivo AIP: {path}")
    with open(path, encoding="utf-8") as f: return f.read()

# ── Catálogos de stands ───────────────────────────────────────────────────────
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

def _lebl_dms_to_decimal(d, m, s): return float(d) + float(m)/60 + float(s)/3600

def _lebl_normalize_stand_id(raw):
    raw = raw.strip().upper()
    if raw.startswith("X"): return raw
    m = re.fullmatch(r"(\d+)([A-Z]?)", raw)
    if not m: return raw
    num, suf = m.groups()
    return f"{num.zfill(2) if len(num) <= 2 else num}{suf}"

def _lebl_extract_max_acft(tail):
    t = tail.split()
    if not t: return ""
    i = 1 if t[0] in ("R","–","-") else 0
    return t[i].upper() if i < len(t) else ""

def _lebl_classify_stand(sid, max_acft="", ramp=""):
    if sid in PASSENGER_AIRLINE_STANDS: return "airline"
    if sid in AUXILIARY_STANDS:         return "auxiliary"
    if sid in RAMP32_STANDS or ramp == "R32": return "ramp32"
    if sid in GA_STANDS:                return "ga"
    if sid in CARGO_STANDS:             return "cargo"
    if max_acft in GA_AIRCRAFT_TYPES:   return "ga"
    return "other"

def parse_aip_stands(texto, categories=None):
    stands, seen = [], set()
    for linea in texto.splitlines():
        m = AIP_LINE_PATTERN.match(linea)
        if not m: continue
        raw_id, ramp, *dms, tail = m.groups()
        lat_d, lat_m, lat_s, lon_d, lon_m, lon_s = dms
        sid = _lebl_normalize_stand_id(raw_id)
        max_acft = _lebl_extract_max_acft(tail)
        cat = _lebl_classify_stand(sid, max_acft, ramp.upper())
        if (categories and cat not in categories) or sid in seen: continue
        stands.append({"id": sid, "lat": _lebl_dms_to_decimal(lat_d, lat_m, lat_s),
                        "lon": _lebl_dms_to_decimal(lon_d, lon_m, lon_s),
                        "category": cat, "ramp": ramp.upper(), "max_acft": max_acft})
        seen.add(sid)
    return sorted(stands, key=lambda s: (s["category"], re.sub(r"[A-Z]","",s["id"]).zfill(4), s["id"]))

def parse_txl_paths(file_path):
    paths = []
    for el in ET.parse(file_path).iter("SerializablePath"):
        coords = [[float(p.findtext("Position/Latitude")), float(p.findtext("Position/Longitude"))]
                  for p in el.findall(".//SerializableTaxiPt")
                  if p.find("Position") is not None and p.findtext("Position/Latitude")]
        if len(coords) >= 2:
            paths.append({"name": (el.findtext("Name") or "").strip(),
                           "type": (el.findtext("Type") or "Unknown").strip(), "coords": coords})
    return paths

# ── Vuelos ────────────────────────────────────────────────────────────────────
VALID_RUNWAYS = {"07L","07R","25L","25R","02","20"}
RUNWAY_OPPOSITE = {"07L":"25R","25R":"07L","07R":"25L","25L":"07R","02":"20","20":"02"}
TIME_RE = re.compile(r"^\d{2}:\d{2}$")
HEADER_SKIP = {"AIRCRAFT","ORIGIN","DESTINATION"}

@dataclass
class FlightRecord:
    aircraft: str; origin: str; arrival: str; departure: str
    airline: str; arr_runway: str; dep_runway: str; gate: str; destination: str = ""

    def _mins(self, t):
        if t in ("-",""): return None
        h, m = map(int, t.split(":")); return h*60+m

    @property
    def arrival_mins(self):   return self._mins(self.arrival)
    @property
    def departure_mins(self): return self._mins(self.departure)

def _parse_time(v): return bool(TIME_RE.match(v)) and bool(datetime.strptime(v, "%H:%M") if True else True)

def _deterministic_gate(stands, aircraft):
    if not stands: return "217"
    return sorted(stands)[sum(ord(c) for c in aircraft) % len(stands)]

def _random_runway():     return random.choice(list(VALID_RUNWAYS))

def _infer_departure_runway(arr, aircraft="", arrival=""):
    arr = (arr or "").upper()
    if arr in RUNWAY_OPPOSITE: return RUNWAY_OPPOSITE[arr]
    pool = sorted(r for r in VALID_RUNWAYS if r != arr) or sorted(VALID_RUNWAYS)
    return pool[sum(ord(c) for c in f"{aircraft}|{arrival}|dep") % len(pool)]

def _complete_missing_fields(f, stands):
    arr, dep = f.arrival, f.departure
    arr_rwy, dep_rwy, gate = f.arr_runway, f.dep_runway, f.gate
    has_arr = arr not in ("-",""); has_dep = dep not in ("-","")
    if has_arr and arr_rwy in ("-",""):  arr_rwy = _random_runway()
    if has_dep and dep_rwy in ("-",""):
        dep_rwy = _infer_departure_runway(arr_rwy, f.aircraft, f.arrival) if has_arr else _random_runway()
    if gate in ("-","") or (stands and gate not in stands):
        gate = _deterministic_gate(stands, f.aircraft)
    return FlightRecord(f.aircraft, f.origin, arr, dep, f.airline, arr_rwy, dep_rwy, gate, f.destination)

def parse_flights_file(path, available_stands=None, default_arr_runway="25R",
                       default_dep_runway="07L"):
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
        if len(p) >= 7 and _parse_time(p[2]) and _parse_time(p[3]):
            arr_rwy = p[5].upper() if p[5].upper() in VALID_RUNWAYS else _random_runway()
            dep_rwy = p[6].upper() if p[6].upper() in VALID_RUNWAYS else _random_runway()
            gate = p[7] if len(p) >= 8 else _deterministic_gate(stands, p[0])
            flights.append(FlightRecord(p[0],p[1],p[2],p[3],p[4],arr_rwy,dep_rwy,gate))
        elif len(p) == 4 and _parse_time(p[2]):
            if is_dep_legacy:
                flights.append(FlightRecord(p[0],"-","-",p[2],p[3],"-","-","-",destination=p[1]))
            else:
                flights.append(FlightRecord(p[0],p[1],p[2],"-",p[3],"-","-","-"))
    return [_complete_missing_fields(f, stands) for f in flights]

def merge_arrivals_departures(arrivals_path, departures_path, available_stands=None):
    stands = available_stands or []
    arr_list = sorted([f for f in parse_flights_file(arrivals_path, stands) if f.arrival not in ("-","")],
                      key=lambda f: f.arrival_mins)
    dep_pool = defaultdict(list)
    for d in parse_flights_file(departures_path, stands):
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
                dep_rwy = _infer_departure_runway(a.arr_runway, a.aircraft, a.arrival)
            merged.append(FlightRecord(a.aircraft, a.origin, a.arrival, dep_match.departure,
                                       a.airline or dep_match.airline, a.arr_runway, dep_rwy,
                                       a.gate if a.gate not in ("-","") else dep_match.gate,
                                       dep_match.destination))
        else:
            merged.append(a)
    for pool in dep_pool.values(): merged.extend(pool)
    return [_complete_missing_fields(f, stands) for f in merged]

# ── Geometría y tiempos ──────────────────────────────────────────────────────
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

def haversine_m(p1, p2):
    return math.hypot((p2[0]-p1[0])*111_320, (p2[1]-p1[1])*111_320*math.cos(math.radians(41.3)))

def cumulative_distances(pts):
    d = [0.0]
    for i in range(1, len(pts)): d.append(d[-1] + haversine_m(pts[i-1], pts[i]))
    return d

def assign_times_const(pts, speed):
    if not pts: return []
    out, t = [{"lat": pts[0][0], "lon": pts[0][1], "t": 0.0}], 0.0
    for i in range(1, len(pts)):
        t += haversine_m(pts[i-1], pts[i]) / speed * REAL_SEC_TO_SIM_MS
        out.append({"lat": pts[i][0], "lon": pts[i][1], "t": t})
    return out

def _assign_times_profile(pts, total_s, profile):
    if not pts: return []
    dists = cumulative_distances(pts); total_d = dists[-1]
    def frac_to_t(frac):
        if profile == "accel":   return math.sqrt(frac) * total_s * REAL_SEC_TO_SIM_MS
        if profile == "decel":   return (1 - math.sqrt(max(0.0, 1-frac))) * total_s * REAL_SEC_TO_SIM_MS
        return frac * total_s * REAL_SEC_TO_SIM_MS
    return [{"lat": p[0], "lon": p[1],
             "t": frac_to_t(dists[i]/total_d if total_d > 1e-6 else 0.0)}
            for i, p in enumerate(pts)]

def assign_times_accel(pts, total_s):  return _assign_times_profile(pts, total_s, "accel")
def assign_times_decel(pts, total_s):  return _assign_times_profile(pts, total_s, "decel")
def assign_times_decel_from_initial_speed(pts, v0):
    if not pts: return []
    d = cumulative_distances(pts)[-1]
    return assign_times_decel(pts, 2*d/v0 if d > 1e-6 else 1.0)

_MODE_SPEED = {"taxi": (TAXI_SPEED_MPS,"const"), "turnaround": (TURNAROUND_MPS,"const"),
               "approach": (APPROACH_SPEED_MPS,"const"), "runway_backtrack": (RUNWAY_BACKTRACK_MPS,"const")}

def merge_timed_segments(segments):
    result, offset = [], 0.0
    for pts, mode in segments:
        if not pts: continue
        if mode in _MODE_SPEED:
            speed, _ = _MODE_SPEED[mode]; timed = assign_times_const(pts, speed)
        elif mode == "runway_accel": timed = assign_times_accel(pts, TAKEOFF_ROLL_S)
        elif mode == "runway_decel": timed = assign_times_decel_from_initial_speed(pts, APPROACH_SPEED_MPS)
        else: timed = assign_times_const(pts, TAXI_SPEED_MPS)
        for j, pt in enumerate(timed):
            t = pt["t"] + offset
            if j == 0 and result and abs(result[-1]["lat"]-pt["lat"]) < 1e-9 and abs(result[-1]["lon"]-pt["lon"]) < 1e-9:
                result[-1]["t"] = t; continue
            result.append({"lat": pt["lat"], "lon": pt["lon"], "t": t})
        if result: offset = result[-1]["t"]
    return result

def densify_path(pts, step=0.000012):
    if len(pts) < 2: return pts
    dense = [pts[0]]
    for i in range(len(pts)-1):
        a, b = pts[i], pts[i+1]
        dx, dy = b[0]-a[0], b[1]-a[1]
        n = max(1, int(math.hypot(dx,dy)/step))
        dense.extend([[a[0]+dx*j/n, a[1]+dy*j/n] for j in range(1, n+1)])
    return dense

def runway_coords(txl_paths, name):
    for s in txl_paths:
        if s["type"] == "Runway" and s["name"] == name: return s["coords"]
    raise ValueError(f"Pista no encontrada: {name}")

def runway_ends(coords):
    return (coords[0], coords[1]) if coords[0][1] <= coords[1][1] else (coords[1], coords[0])

def runway_number(name):
    d = "".join(c for c in name if c.isdigit()); return int(d[:2]) if d else 25

def lands_from_east(name): return runway_number(name) >= 13

def extend_runway_axis(west, east, beyond, distance):
    ref = east if beyond == "east" else west
    opp = west if beyond == "east" else east
    dx, dy = ref[0]-opp[0], ref[1]-opp[1]
    L = math.hypot(dx,dy)
    if L < 1e-12: return ref
    return [ref[0]+dx/L*distance, ref[1]+dy/L*distance]

def merged_strip_endpoints(txl_paths, rwy):
    pts = runway_coords(txl_paths, rwy) + runway_coords(txl_paths, RUNWAY_OPPOSITE.get(rwy, rwy))
    return min(pts, key=lambda p:(p[1],p[0])), max(pts, key=lambda p:(p[1],p[0]))

def runway_threshold(west, east, name): return east if lands_from_east(name) else west

def point_along_strip(west, east, start, toward, dist_m):
    end = west if toward == "west" else east
    seg = haversine_m(start, end)
    if seg < 1e-6: return start
    frac = min(1.0, dist_m/seg)
    return [start[0]+(end[0]-start[0])*frac, start[1]+(end[1]-start[1])*frac]

def approach_spawn(west, east, name):
    return extend_runway_axis(west, east, "east" if lands_from_east(name) else "west", RUNWAY_APPROACH_EXTRA)

def departure_exit(west, east, name):
    return extend_runway_axis(west, east, "west" if runway_number(name) < 13 else "east", RUNWAY_EXIT_EXTRA)

def u_turn_at_end(end, west, east, roll_toward_west):
    dx, dy = east[0]-west[0], east[1]-west[1]; L = math.hypot(dx,dy)
    if L < 1e-12: return [end, end]
    ux, uy = dx/L, dy/L; nx, ny = -uy*0.00045, ux*0.00045
    if roll_toward_west:
        pts = [end,[end[0]+nx*.35,end[1]+ny*.35],[end[0]+nx,end[1]+ny],
               [end[0]+nx*.4-ux*.00025,end[1]+ny*.4-uy*.00025],[end[0]-ux*.0002,end[1]-uy*.0002]]
    else:
        pts = [end,[end[0]-nx*.35,end[1]-ny*.35],[end[0]-nx,end[1]-ny],
               [end[0]-nx*.4+ux*.00025,end[1]-ny*.4+uy*.00025],[end[0]+ux*.0002,end[1]+uy*.0002]]
    return densify_path(pts, step=0.000008)

# ── TaxiGraph ─────────────────────────────────────────────────────────────────
class TaxiGraph:
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
    def _dist(a, b): return haversine_m([a[0],a[1]], [b[0],b[1]])

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

def _taxi_route(graph, start, end):
    nodes = graph.shortest_path(start, end)
    raw = [[start[0],start[1]]] + [[n[0],n[1]] for n in nodes] + [[end[0],end[1]]]
    return densify_path(raw)

def build_arrival_path(graph, txl_paths, runway_name, gate_lat, gate_lon):
    west, east = merged_strip_endpoints(txl_paths, runway_name)
    spawn = approach_spawn(west, east, runway_name)
    thr   = runway_threshold(west, east, runway_name)
    vacate = point_along_strip(west, east, thr, "west" if lands_from_east(runway_name) else "east",
                               LANDING_ROLL_METERS)
    return merge_timed_segments([
        (densify_path([spawn, thr]),   "approach"),
        (densify_path([thr, vacate])[1:], "runway_decel"),
        (_taxi_route(graph,(vacate[0],vacate[1]),(gate_lat,gate_lon))[1:], "taxi"),
    ])

def build_departure_path(graph, txl_paths, runway_name, gate_lat, gate_lon):
    west, east = merged_strip_endpoints(txl_paths, runway_name)
    dep_num = runway_number(runway_name)
    turn_end = east if dep_num < 13 else west
    roll_toward_west = dep_num < 13
    taxi  = _taxi_route(graph, (gate_lat,gate_lon), (turn_end[0],turn_end[1]))
    uturn = u_turn_at_end(turn_end, west, east, roll_toward_west)
    roll_from = uturn[-1]
    roll_pts = densify_path([roll_from, west if roll_toward_west else east,
                             departure_exit(west, east, runway_name)])
    return merge_timed_segments([(taxi,"taxi"),(uturn[1:],"turnaround"),(roll_pts[1:],"runway_accel")])

# ── Asignación de gates y conflictos ─────────────────────────────────────────
def _lebl_mins_to_ms(mins, base): return max(0, (mins-base)*MS_PER_SIM_MINUTE)

def find_nearest_free_gate(at_ms, stand_by_id, gate_free_at, ref_lat, ref_lon):
    best_id, best_d = None, float("inf")
    for sid, s in stand_by_id.items():
        if gate_free_at.get(sid,0) > at_ms: continue
        d = haversine_m([ref_lat,ref_lon],[s["lat"],s["lon"]])
        if d < best_d: best_d, best_id = d, sid
    return best_id

def resolve_gate_conflicts(ops, stand_by_id, graph, txl_paths):
    gate_free_at, gate_occupant = {}, {}
    FAR = 365*24*60*MS_PER_SIM_MINUTE

    def _redirect_paths(op, assigned, dep_start, has_arr):
        s = stand_by_id[assigned]
        if has_arr:
            ap = build_arrival_path(graph, txl_paths, op["arrRunway"], s["lat"], s["lon"])
            op["arrivalPath"] = ap; op["arrivalDurationMs"] = int(ap[-1]["t"])
        if dep_start is not None and op["depRunway"]:
            dp = build_departure_path(graph, txl_paths, op["depRunway"], s["lat"], s["lon"])
            op["departurePath"] = dp; op["departureDurationMs"] = int(dp[-1]["t"])

    def _process(op, at_ms, free_at):
        req = op["gate"]
        assigned, redirected, occupied_by = req, False, None
        if gate_free_at.get(req,0) > at_ms:
            occupied_by = gate_occupant.get(req)
            alt = find_nearest_free_gate(at_ms, stand_by_id, gate_free_at,
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

# ── Clasificación y selección ─────────────────────────────────────────────────
def _classify_animation_flight(f):
    ha, hd = f.arrival_mins is not None, f.departure_mins is not None
    return "normal" if ha and hd else "arrival_only" if ha else "departure_only" if hd else "skip"

def select_flights_for_animation(flights, limit):
    if not flights or not limit or len(flights) <= limit: return flights
    def _ev(f): return f.arrival_mins or f.departure_mins or 0
    ordered = sorted(flights, key=_ev); n = len(ordered)
    idx = sorted({min(int(round(i*(n-1)/max(1,limit-1))),n-1) for i in range(limit)})
    return [ordered[i] for i in idx]

def decimate_timed_path(path, max_points=50):
    if not path or len(path) <= max_points: return path
    n = len(path)
    return [path[int(i*(n-1)/(max_points-1))] for i in range(max_points)]

# ── Preparación de operaciones ────────────────────────────────────────────────
def prepare_operations(flights, stands, txl_paths, limit=None):
    graph = TaxiGraph(txl_paths)
    stand_by_id = {s["id"]: s for s in stands}
    by_kind = defaultdict(list)
    for f in flights:
        if f.gate not in stand_by_id: continue
        k = _classify_animation_flight(f)
        if k != "skip": by_kind[k].append(f)

    pool = by_kind["normal"] + by_kind["arrival_only"] + by_kind["departure_only"]
    if not pool: raise ValueError("No hay vuelos con gate valido para animar")
    if limit and len(pool) > limit:
        sel = select_flights_for_animation(pool, limit)
        by_kind = defaultdict(list)
        for f in sel: by_kind[_classify_animation_flight(f)].append(f)

    event_mins = [f.arrival_mins for f in by_kind["normal"]+by_kind["arrival_only"] if f.arrival_mins] + \
                 [f.departure_mins for f in by_kind["normal"]+by_kind["departure_only"] if f.departure_mins]
    base_mins = min(event_mins)
    ops = []

    def _make_op(f, kind):
        s = stand_by_id[f.gate]; ms = lambda m: _lebl_mins_to_ms(m, base_mins) if m else None
        arr_path = build_arrival_path(graph, txl_paths, f.arr_runway, s["lat"], s["lon"]) if f.arrival_mins else []
        dep_path = build_departure_path(graph, txl_paths, f.dep_runway, s["lat"], s["lon"]) \
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

    ops = resolve_gate_conflicts(ops, stand_by_id, graph, txl_paths)
    return ops, max(0, base_mins-5)

# ── Canvas helpers ────────────────────────────────────────────────────────────
def _stand_numeric_id(sid):
    d = "".join(c for c in sid if c.isdigit()); return int(d[:3]) if d else 0

def _t1_aip_pool(ids): return sorted(s for s in ids if 200 <= _stand_numeric_id(s) <= 340)
def _t2_aip_pool(ids): return sorted(s for s in ids if  20 <= _stand_numeric_id(s) <= 150)

def lebl_gate_to_aip_stand(gate_name, stand_ids):
    m = re.match(r"T(\d)BA([A-Z]+)(\d+)", gate_name or "")
    if not m: return None
    terminal, gate_num = int(m.group(1)), int(m.group(3))
    pool = _t1_aip_pool(stand_ids) if terminal == 1 else _t2_aip_pool(stand_ids)
    if not pool: return stand_ids[0] if stand_ids else None
    return pool[(gate_num-1) % len(pool)]

def _flight_gate_key(aircraft, arrival): return (aircraft, arrival)
def _flight_record_gate_key(f):
    return _flight_gate_key(f.aircraft, f.arrival if f.arrival not in ("-","") else f.departure)

def _free_lebl_gate(bcn, gate_name):
    if not gate_name or bcn is None: return
    for t in bcn.terminal:
        for a in t.boarding_area:
            for g in a.gate:
                if g.name == gate_name: g.occupancy = False; g.aircraft_id = ""; return

def build_gate_assignments_from_bcn(bcn, stand_ids):
    from src.LEBL import GateOccupancy
    return {gi["aircraft_id"]: lebl_gate_to_aip_stand(gi["name"], stand_ids)
            for gi in GateOccupancy(bcn)
            if gi["status"] in ("Occupied","Ocupada") and gi.get("aircraft_id")
            and lebl_gate_to_aip_stand(gi["name"], stand_ids)}

def build_gate_assignments_for_flights(bcn, flights, stand_ids):
    from src.LEBL import AssignGate
    bcn_work = copy.deepcopy(bcn); assignments = {}
    for f in flights:
        if f.arrival in ("-",""): continue
        ac = Aircraft(f.aircraft, f.airline, f.origin, f.arrival)
        ac.departure = f.departure if f.departure not in ("-","") else "-"
        gate_name = AssignGate(bcn_work, ac)
        if not gate_name: continue
        stand = lebl_gate_to_aip_stand(gate_name, stand_ids)
        if stand: assignments[_flight_gate_key(f.aircraft, f.arrival)] = stand
        _free_lebl_gate(bcn_work, gate_name)
    return assignments

def _default_stand_for_airline(bcn, airline, stand_ids, aircraft="", arrival=""):
    from src.LEBL import SearchTerminal
    pool = (_t1_aip_pool if SearchTerminal(bcn,airline)=="T1" else _t2_aip_pool)(stand_ids) or sorted(stand_ids) or ["217"]
    key = f"{airline}|{arrival}" if arrival not in ("-","") else aircraft
    return pool[sum(ord(c) for c in key) % len(pool)]

# ── Visualización canvas ──────────────────────────────────────────────────────
LEBL_ANIM_PATH_MAX_POINTS = 50
LEBL_ANIM_FLIGHT_LIMIT    = None
LEBL_SPEED_SIM_SEC = {1:1, 2:5, 4:120, 8:900, 16:3600}

def _path_bearing_deg(lat1, lon1, lat2, lon2):
    r = math.pi/180; y = math.sin((lon2-lon1)*r)*math.cos(lat2*r)
    x = math.cos(lat1*r)*math.sin(lat2*r)-math.sin(lat1*r)*math.cos(lat2*r)*math.cos((lon2-lon1)*r)
    return (math.degrees(math.atan2(y,x))+360)%360

def move_along_timed_path(path, elapsed_ms):
    if not path: return None,None,0.0,True
    if elapsed_ms >= path[-1]["t"]:
        l,p = path[-1], path[-2] if len(path)>1 else path[-1]
        return l["lat"],l["lon"],_path_bearing_deg(p["lat"],p["lon"],l["lat"],l["lon"]),True
    i = 0
    while i+1<len(path) and path[i+1]["t"]<=elapsed_ms: i+=1
    a,b = path[i],path[i+1]; frac=(elapsed_ms-a["t"])/max(1.0,b["t"]-a["t"])
    return a["lat"]+frac*(b["lat"]-a["lat"]),a["lon"]+frac*(b["lon"]-a["lon"]),\
           _path_bearing_deg(a["lat"],a["lon"],b["lat"],b["lon"]),False

def _segment_in_bounds(coords, min_lat, max_lat, min_lon, max_lon):
    return any(min_lat<=lat<=max_lat and min_lon<=lon<=max_lon for lat,lon in coords)

def _compute_lebl_view_bounds(stands, txl_paths=None, operations=None, margin=0.04):
    lats = [s["lat"] for s in stands]; lons = [s["lon"] for s in stands]
    c_lat,c_lon = (min(lats)+max(lats))/2,(min(lons)+max(lons))/2
    lat_h = max((max(lats)-min(lats))*.58,.011)*(1+margin)
    lon_h = max((max(lons)-min(lons))*.58,.014)*(1+margin)
    b = [c_lat-lat_h, c_lat+lat_h, c_lon-lon_h, c_lon+lon_h]
    if txl_paths:
        for seg in txl_paths:
            if seg["type"]!="Runway" or not _segment_in_bounds(seg["coords"],b[0],b[1],b[2],b[3]): continue
            for lat,lon in seg["coords"]:
                b[0]=min(b[0],lat);b[1]=max(b[1],lat);b[2]=min(b[2],lon);b[3]=max(b[3],lon)
        pl,pn=(b[1]-b[0])*.02 or .0002,(b[3]-b[2])*.02 or .0002
        b[0]-=pl;b[1]+=pl;b[2]-=pn;b[3]+=pn
    return tuple(b)

def _make_map_projector(min_lat, max_lat, min_lon, max_lon, w, h, pad=6):
    lat_span,lon_span = max_lat-min_lat or .001, max_lon-min_lon or .001
    cos_lat = math.cos(math.radians((min_lat+max_lat)/2))
    scale = min((w-2*pad)/(lon_span*cos_lat),(h-2*pad)/lat_span)
    cw,ch = lon_span*cos_lat*scale, lat_span*scale
    ox,oy = (w-cw)/2, (h-ch)/2
    def to_xy(lat,lon): return ox+(lon-min_lon)*cos_lat*scale, oy+(max_lat-lat)*scale
    return to_xy

def _plane_triangle_xy(x, y, brg, size=9.0):
    r=math.radians(brg); fx,fy=math.sin(r),-math.cos(r); px,py=-fy,fx
    nx,ny=x+fx*size,y+fy*size
    lx=x-fx*size*.55+px*size*.4; ly=y-fy*size*.55+py*size*.4
    rx=x-fx*size*.55-px*size*.4; ry=y-fy*size*.55-py*size*.4
    return [nx,ny,lx,ly,rx,ry]

def simplify_txl_for_display(txl_paths, view_bounds=None, max_per_seg=22):
    out = []
    for seg in txl_paths:
        coords = seg["coords"]
        if len(coords)<2: continue
        if view_bounds and seg["type"]!="Runway" and not _segment_in_bounds(coords,*view_bounds[:2],*view_bounds[2:]): continue
        if len(coords)>max_per_seg:
            step=max(1,len(coords)//max_per_seg); coords=coords[::step]
            if coords[-1]!=seg["coords"][-1]: coords=coords+[seg["coords"][-1]]
        out.append({"type":seg["type"],"coords":coords})
    return out

def create_lebl_animation_widget(parent, data):
    import tkinter as tk
    from tkinter import ttk
    ops,stands,txl_paths,sim_start_mins = data["operations"],data["stands"],data["txl_paths"],data["sim_start_mins"]
    stand_by_id = {s["id"]:s for s in stands}
    active_gates = {op.get("assignedGate") or op["gate"] for op in ops}
    bounds = data.get("view_bounds") or _compute_lebl_view_bounds(stands)
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
        to_xy=_make_map_projector(min_lat,max_lat,min_lon,max_lon,w,h); st["to_xy"]=to_xy
        for seg in txl_paths:
            c=seg["coords"]
            if len(c)<2 or not _segment_in_bounds(c,min_lat,max_lat,min_lon,max_lon): continue
            pts=[coord for lat,lon in c for coord in to_xy(lat,lon)]
            kw=dict(fill="#1a252f",width=5,capstyle=tk.ROUND) if seg["type"]=="Runway" else dict(fill="#2471a3",width=2)
            cv.create_line(*pts,tags="static",**kw)
        st["gate_items"]={}
        for s in stands:
            gid=s["id"]
            if gid not in active_gates and not _segment_in_bounds([[s["lat"],s["lon"]]],min_lat,max_lat,min_lon,max_lon): continue
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
            pid=cv.create_polygon(*_plane_triangle_xy(x,y,0,11),fill="#555",outline="#333",
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
                lat,lon,brg,done=move_along_timed_path(op["arrivalPath"],sim_ms-ps["phase_start_sim"])
                x,y=to_xy(lat,lon); cv.coords(pid,*_plane_triangle_xy(x,y,brg,11))
                if done: ps["phase"]="parked"; set_gate(gate,True)
            if ps["phase"]=="parked" and dep_s is not None and sim_ms>=dep_s:
                ps["phase"]="departing"; ps["phase_start_sim"]=sim_ms; set_gate(gate,False)
            if ps["phase"]=="departing":
                lat,lon,brg,done=move_along_timed_path(op["departurePath"],sim_ms-ps["phase_start_sim"])
                x,y=to_xy(lat,lon); cv.coords(pid,*_plane_triangle_xy(x,y,brg,11))
                if done: ps["phase"]="gone"; cv.itemconfigure(pid,state=tk.HIDDEN)
            if ps["phase"]=="parked":
                s2=stand_by_id.get(gate,stands[0]); x,y=to_xy(s2["lat"],s2["lon"])
                cv.coords(pid,*_plane_triangle_xy(x,y,0,11)); cv.itemconfigure(pid,state=tk.NORMAL); set_gate(gate,True)

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
                x,y=to_xy(stand["lat"],stand["lon"]); cv.coords(pid,*_plane_triangle_xy(x,y,0,11))
                cv.itemconfigure(pid,state=tk.NORMAL); set_gate(gate,True)
            def _dep(start_ms):
                ps["phase"]="departing"
                if ps["phase_start_sim"]<=0: ps["phase_start_sim"]=start_ms
                lat,lon,brg,_=move_along_timed_path(op["departurePath"],sim_ms-start_ms)
                x,y=to_xy(lat,lon); cv.coords(pid,*_plane_triangle_xy(x,y,brg,11)); cv.itemconfigure(pid,state=tk.NORMAL)
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
                lat,lon,brg,_=move_along_timed_path(op["arrivalPath"],sim_ms-ps["phase_start_sim"])
                x,y=to_xy(lat,lon); cv.coords(pid,*_plane_triangle_xy(x,y,brg,11)); cv.itemconfigure(pid,state=tk.NORMAL)
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

# ── Entry point ───────────────────────────────────────────────────────────────
def GenerateLEBLAnimation(arrivals_path, limit=None,
                           gate_assignments=None, bcn_airport=None, departures_path=None):
    aip_text = _lebl_load_aip_text_stand(_lebl_aip_path())
    stands = parse_aip_stands(aip_text, categories={"airline"})
    stand_ids = sorted(PASSENGER_AIRLINE_STANDS & {s["id"] for s in stands})
    stand_set = set(stand_ids)
    txl_paths = parse_txl_paths(_lebl_txl_path())

    flights = (merge_arrivals_departures(arrivals_path, departures_path, stand_ids)
               if departures_path and os.path.isfile(departures_path)
               else parse_flights_file(arrivals_path, stand_ids))
    if not flights: raise ValueError("No hay vuelos validos en el archivo de llegadas.")

    if gate_assignments is None and bcn_airport is not None:
        gate_assignments = build_gate_assignments_for_flights(bcn_airport, flights, stand_ids)

    if gate_assignments or bcn_airport is not None:
        enriched = []
        for f in flights:
            assigned = (gate_assignments or {}).get(_flight_record_gate_key(f))
            if not assigned and bcn_airport is not None:
                assigned = _default_stand_for_airline(bcn_airport, f.airline, stand_ids, f.aircraft, f.arrival)
            enriched.append(
                FlightRecord(f.aircraft,f.origin,f.arrival,f.departure,f.airline,
                             f.arr_runway,f.dep_runway,assigned,f.destination)
                if assigned and assigned in stand_set
                else _complete_missing_fields(f, stand_ids)
            )
        flights = enriched

    ops, sim_start = prepare_operations(flights, stands, txl_paths, limit=limit)
    for op in ops:
        op["arrivalPath"] = decimate_timed_path(op["arrivalPath"])
        if op["departurePath"]: op["departurePath"] = decimate_timed_path(op["departurePath"])

    view_bounds = _compute_lebl_view_bounds(stands, txl_paths)
    valid_flights = [f for f in flights if f.gate in stand_set and _classify_animation_flight(f)!="skip"]
    return {
        "operations": ops, "stands": stands, "sim_start_mins": sim_start, "view_bounds": view_bounds,
        "txl_paths": simplify_txl_for_display(txl_paths, view_bounds),
        "total_flights": len(flights), "valid_flights": len(valid_flights),
        "departures_from_file": bool(departures_path and os.path.isfile(departures_path)),
    }

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    arrivals_path   = os.path.join(BASE_DIR,"data","Arrivals.txt")
    departures_path = os.path.join(BASE_DIR,"data","Departures.txt")
    airports_path   = os.path.join(BASE_DIR,"data","Airports.txt")
    structure_path  = os.path.join(BASE_DIR,"data","Terminals.txt")

    aircraft    = LoadArrivals(arrivals_path)
    airports_db = LoadAirports(airports_path)
    if aircraft:
        PlotArrivals(aircraft); PlotAirlines(aircraft); PlotFlightsType(aircraft); plt.show()
    from src.LEBL import LoadAirportStructure
    bcn = LoadAirportStructure(structure_path)
    departures, status = LoadDepartures(departures_path)
    all_movements = MergeMovements(aircraft, departures)
    PlotDayOccupancy(bcn, all_movements); plt.show()
    LongDistanceArrivals(aircraft, airports_db)