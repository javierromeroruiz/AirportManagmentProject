import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
import math

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


def _ensure_output_dir():
    if not os.path.exists("output"):
        os.makedirs("output")


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


class Aircraft:
    def __init__(
        self,
        id_code,
        airline,
        origin="",
        arrival="",
        destination="",
        departure="",
    ):
        self.id = id_code
        self.airline = airline
        self.airline_company = airline
        self.origin = origin
        self.arrival = arrival
        self.destination = destination
        self.departure = departure
        self.gate = ""


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

    with open("output/flights.kml", "w") as f:
        f.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        f.write("<Document>\n")

        for ac in aircraft:
            orig = ac.origin

            if orig in airports_db:
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
        orig = ac.origin

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
            total_co2_kg += 18 * dist
            cont_flights += 1

            if dist > 2000:
                long_distance_list.append(ac)

    total_tons = total_co2_kg / 1000
    med_tons = total_tons / cont_flights if cont_flights > 0 else 0.0

    return long_distance_list, total_tons, med_tons


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


def MergeMovements(arrivals, departures):
    if not arrivals or not departures:
        return -1

    merged_list = []
    i = 0
    while i < len(arrivals):
        merged_list.append(arrivals[i])
        i += 1

    j = 0
    while j < len(departures):
        dep = departures[j]
        found = False
        k = 0

        while k < len(merged_list) and not found:
            arr = merged_list[k]

            if arr.id == dep.id:
                if arr.arrival and dep.departure:
                    arr_time = arr.arrival.split(":")
                    dep_time = dep.departure.split(":")

                    arr_mins = (int(arr_time[0]) * 60) + int(arr_time[1])
                    dep_mins = (int(dep_time[0]) * 60) + int(dep_time[1])

                    if arr_mins < dep_mins:
                        arr.destination = dep.destination
                        arr.departure = dep.departure
                        found = True
            k += 1

        if not found:
            merged_list.append(dep)

        j += 1

    return merged_list


def NightAircraft(aircrafts):
    if not aircrafts:
        return -1

    night_list = []
    for plane in aircrafts:
        if plane.arrival == "" and plane.departure != "":
            night_list.append(plane)

    return night_list


def AssignNightGates(bcn, aircrafts):
    from src.LEBL import AssignGate

    if not aircrafts:
        return -1

    for plane in aircrafts:
        if plane.arrival == "" and plane.departure != "":
            AssignGate(bcn, plane)

    return 0


def FreeGate(bcn, id):
    found = False

    # Recorremos: Terminales --> Áreas --> Puertas
    i = 0
    while i < len(bcn.terminal) and not found:
        terminal = bcn.terminal[i]

        j = 0
        while j < len(terminal.areas) and not found:
            area = terminal.areas[j]

            k = 0
            while k < len(area.gates) and not found:
                gate = area.gates[k]

                # Comprobamos si es el avion que buscamos.
                if gate.aircraft_id == id:
                    gate.status = "free"
                    gate.aircraft_id = ""   # Limpiamos id
                    found = True
                k += 1
            j += 1
        i += 1
    if not found:
        return -1
    return 0


def AssignGatesAtTime(bcn, aircrafts, time):
    from src.LEBL import AssignGate

    # Convertimos la hora de control a min
    time_parts = time.split(":")
    current_hour_mins = (int(time_parts[0]) * 60) + int(time_parts[1])
    next_hour_mins = current_hour_mins + 60

    # 1. Liberar las puertas de aviones ya despegados
    i = 0
    while i < len(aircrafts):
        plane = aircrafts[i]

        if plane.departure != "":
            dep_parts = plane.departure.split(":")
            dep_mins = (int(dep_parts[0]) * 60) + int(dep_parts[1])

            if dep_mins <= next_hour_mins:
                FreeGate(bcn, plane.id)
        i += 1

    # 2. Asignar puertas a los que aterrizan
    not_assigned_count = 0

    j = 0
    while j < len(aircrafts):
        plane = aircrafts[j]

        if plane.arrival != "":
            arr_parts = plane.arrival.split(":")
            arr_mins = (int(arr_parts[0]) * 60) + int(arr_parts[1])

            if current_hour_mins <= arr_mins < next_hour_mins:
                success = AssignGate(bcn, plane)

                if success == -1 or success is False:
                    not_assigned_count += 1
        j += 1
    return not_assigned_count


def PlotDayOccupancy(bcn, aircrafts):
    _setup_plot_style()

    # Asignacion de la noche
    AssignNightGates(bcn, aircrafts)

    hours_labels = [f"{h:02d}" for h in range(24)]
    occupied_gates_per_hour = []
    rejected_per_hour = []

    # Simulamos el dia por horas
    h = 0
    while h < 24:
        str_time = f"{h:02d}:00"
        rejected = AssignGatesAtTime(bcn, aircrafts, str_time)
        rejected_per_hour.append(rejected)

        # Contamos numero de puertas ocupadas
        total_occ = 0

        i = 0
        while i < len(bcn.terminal):
            terminal = bcn.terminal[i]

            j = 0
            while j < len(terminal.areas):
                area = terminal.areas[j]

                k = 0
                while k < len(area.gates):
                    gate = area.gates[k]
                    if gate.status != "free":
                        total_occ += 1
                    k += 1
                j += 1
            i += 1
        occupied_gates_per_hour.append(total_occ)
        h += 1

    # Grafico:
    fig, ax = plt.subplots(figsize=(10.5, 5.0), facecolor=CHART["bg"])

    bars_occupied = ax.bar(
        hours_labels, occupied_gates_per_hour,
        color=CHART["primary_light"], edgecolor="white", width=0.45, label="Puertas Ocupadas", zorder=3
    )

    bars_rejected = ax.bar(
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


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    arrivals_path = os.path.join(BASE_DIR, "data", "Arrivals.txt")
    departures_path = os.path.join(BASE_DIR, "data", "Departures.txt")
    airports_path = os.path.join(BASE_DIR, "data", "Airports.txt")

    aircraft = LoadArrivals(arrivals_path)
    airports_db = LoadAirports(airports_path)

    from src.LEBL import BarcelonaAP
    bcn = BarcelonaAP("LEBL")

    PlotArrivals(aircraft)
    PlotAirlines(aircraft)
    PlotFlightsType(aircraft)

    departures, status = LoadDepartures(departures_path)

    if aircraft and departures:
        all_movements = MergeMovements(aircraft, departures)

        if all_movements != -1:
            PlotDayOccupancy(bcn, all_movements)
        else:
            print("ERROR: MergeMovements devolvió -1. Revisa la lógica interna del cruce.")
    else:
        print(f"ERROR DE CARGA: Arrivals tiene {len(aircraft)} vuelos y Departures tiene {len(departures)} vuelos. Uno de los dos está vacío.")

    vuelos_largos, co2, med_co2 = LongDistanceArrivals(aircraft, airports_db)

    print(f"Vuelos > 2000km detectados: {len(vuelos_largos)}")
    print(f"Impacto ambiental total: {co2:.2f} t/CO2")
    print(f"Impacto medio por vuelo: {med_co2:.2f} t/CO2")
