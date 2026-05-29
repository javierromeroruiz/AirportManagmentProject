import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch

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


class Airport:
    def __init__(self, code, lat, lon):
        self.code = code
        self.lat = lat
        self.lon = lon
        self.schengen = False


def IsSchengenAirport(code):
    if not code or len(code) < 2:
        return False
    return code[:2] in SCHENGEN_PREFIXES


def SetSchengen(airport):
    airport.schengen = IsSchengenAirport(airport.code)


def PrintAirport(airport):
    print("Code:", airport.code)
    print("Latitude:", airport.lat)
    print("Longitude:", airport.lon)
    print("Schengen:", airport.schengen)


def LoadAirports(filename):
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


def _dec_to_dms_str(value, is_latitude):
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


def SaveSchengenAirports(airports, filename):
    if not airports:
        return -1

    try:
        with open(filename, "w") as file:
            file.write("CODE LAT LON\n")

            for airport in airports:
                if airport.schengen:
                    lat_str = _dec_to_dms_str(airport.lat, is_latitude=True)
                    lon_str = _dec_to_dms_str(airport.lon, is_latitude=False)
                    file.write(f"{airport.code} {lat_str} {lon_str}\n")

        return 0

    except IOError:
        return -1


def AddAirport(airports, airport):
    for existing in airports:
        if existing.code == airport.code:
            return
    airports.append(airport)


def RemoveAirport(airports, code):
    i = 0
    while i < len(airports):
        if airports[i].code == code:
            airports.pop(i)
            return 0
        i += 1
    return -1


def PlotAirports(airports):
    if not airports:
        return

    _setup_plot_style()

    schengen_pts = [a for a in airports if a.schengen]
    other_pts = [a for a in airports if not a.schengen]
    count_schengen = len(schengen_pts)
    count_no_schengen = len(other_pts)
    total = len(airports)

    fig = plt.figure(figsize=(10.5, 7.2), facecolor=CHART["bg"])
    gs = fig.add_gridspec(2, 2, height_ratios=[1.35, 1], hspace=0.38, wspace=0.28)
    ax_map = fig.add_subplot(gs[0, :])
    ax_pie = fig.add_subplot(gs[1, 0])
    ax_bar = fig.add_subplot(gs[1, 1])

    if schengen_pts:
        ax_map.scatter(
            [a.lon for a in schengen_pts],
            [a.lat for a in schengen_pts],
            c=CHART["schengen"],
            s=42,
            alpha=0.85,
            edgecolors="white",
            linewidths=0.6,
            label="Schengen",
            zorder=3,
        )
    if other_pts:
        ax_map.scatter(
            [a.lon for a in other_pts],
            [a.lat for a in other_pts],
            c=CHART["non_schengen"],
            s=42,
            alpha=0.85,
            edgecolors="white",
            linewidths=0.6,
            label="No Schengen",
            zorder=3,
        )

    _style_axes(
        ax_map,
        title="Mapa 2D de aeropuertos",
        subtitle=f"{total} aeropuertos · verde = Schengen · naranja = fuera de Schengen",
        xlabel="Longitud (°)",
        ylabel="Latitud (°)",
    )
    ax_map.grid(True, zorder=0)
    ax_map.legend(loc="upper right", fontsize=9, frameon=True)

    if total:
        sizes = [count_schengen, count_no_schengen]
        labels = ["Espacio Schengen", "Fuera de Schengen"]
        colors = [CHART["schengen"], CHART["non_schengen"]]

        wedges, texts, autotexts = ax_pie.pie(
            sizes,
            labels=labels,
            colors=colors,
            explode=(0.03, 0.03),
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

        ax_pie.set_title(
            "Distribución Schengen",
            loc="left",
            color=CHART["text"],
            fontweight="bold",
            pad=10,
        )

        categories = labels
        x_pos = range(len(categories))
        bars = ax_bar.bar(
            x_pos,
            sizes,
            color=colors,
            edgecolor="white",
            linewidth=1.0,
            width=0.55,
            zorder=3,
        )
        ax_bar.set_xticks(x_pos)
        ax_bar.set_xticklabels(categories, fontsize=9)
        _style_axes(
            ax_bar,
            title="Comparativa absoluta",
            subtitle="Recuerda aplicar Schengen antes del gráfico",
            ylabel="Número de aeropuertos",
        )
        ax_bar.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax_bar.grid(axis="y", zorder=0)
        _bar_value_labels(ax_bar, bars)

        legend_handles = [
            Patch(facecolor=CHART["schengen"], edgecolor="white", label="Schengen"),
            Patch(facecolor=CHART["non_schengen"], edgecolor="white", label="No Schengen"),
        ]
        fig.legend(
            handles=legend_handles,
            loc="lower center",
            ncol=2,
            bbox_to_anchor=(0.5, -0.01),
            fontsize=9,
        )

    fig.suptitle(
        "Análisis de la red de aeropuertos",
        x=0.02,
        y=0.98,
        ha="left",
        fontsize=12,
        fontweight="bold",
        color=CHART["text"],
    )
    fig.subplots_adjust(left=0.07, right=0.98, top=0.90, bottom=0.14, hspace=0.48, wspace=0.30)
    _save_and_show(fig, "airports_overview.png")


def MapAirports(airports, filename):
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
