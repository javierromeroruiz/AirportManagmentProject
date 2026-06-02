# =============================================================================
# interfaz.py — Ventana grafica del proyecto
#
# Se enlazan las funciones de airport.py, aircraft.py y LEBL.py con botones
# y campos de texto. Los datos cargados se guardan en variables globales.
# =============================================================================

import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import sys
import re
import copy
import threading
import queue

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from src.airport import (
    Airport,
    LoadAirports,
    AddAirport,
    RemoveAirport,
    SetSchengen,
    SaveSchengenAirports,
    PlotAirports,
    MapAirports,
)
from src.aircraft import (
    Aircraft,
    LoadArrivals,
    PlotArrivals,
    SaveFlights,
    PlotAirlines,
    PlotFlightsType,
    LoadAirports as LoadAirportsDB,
    MapFlights,
    MapLongDistanceFlights,
    LongDistanceArrivals,
    FlightsKmlPath,
    LongDistanceKmlPath,
    LoadDepartures,
    MergeMovements,
    NightAircraft,
    AssignNightGates,
    FreeGate,
    AssignGatesAtTime,
    PlotDayOccupancy
)
from src.aircraft import GenerateLEBLAnimation, CreateLEBLAnimationWidget, LEBL_ANIM_FLIGHT_LIMIT
from src.LEBL import LoadAirportStructure, GateOccupancy, AssignGate

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ===============================================================
#  ESTADO GLOBAL — datos en memoria tras cada carga desde archivo
# ===============================================================
airports = []
aircrafts = []
airports_db = {}
departures = []
all_movements = []
night_aircrafts = []
bcn_airport = None

_plot_canvas = None
_plot_toolbar = None
_original_plt_show = plt.show

# ===============================================================
#  VENTANA PRINCIPAL
# ===============================================================
app = tk.Tk()
app.title("Gestor de Aeropuertos y Vuelos — LEBL")

window_width, window_height = 1100, 980
sw, sh = app.winfo_screenwidth(), app.winfo_screenheight()
app.geometry(
    f"{window_width}x{window_height}+{(sw - window_width) // 2}+{(sh - window_height) // 2}"
)
app.minsize(900, 750)

try:
    theme_tcl = os.path.join(DATA_DIR, "forest-light.tcl")
    app.tk.call("source", theme_tcl)
    ttk.Style().theme_use("forest-light")
except tk.TclError as e:
    print(f"Aviso: no se pudo cargar forest-light ({e}). Usando tema por defecto.")


# ===============================================================
#  FUNCIONES PROYECTO — interfaz.py
# ===============================================================


def update_listbox(items=None):
    """
    Se vacia la lista del panel derecho y se vuelve a llenar linea a linea.
    Por defecto se muestran los aeropuertos de la variable global airports,
    con codigo, coordenadas y si son Schengen. Tambien se actualiza el contador superior.
    """
    listbox.delete(0, tk.END)
    if items is None:
        items = airports
    for a in items:
        sch = "✔ Schengen" if a.schengen else "✘ No Schengen"
        listbox.insert(
            tk.END, f"{a.code:<6}  Lat: {a.lat:<10.4f}  Lon: {a.lon:<10.4f}  {sch}"
        )
    lbl_count.config(text=f"{len(airports)} aeropuerto(s) en memoria")


def _reset_bcn_gate_occupancy(bcn):
    """Antes de una nueva asignacion o simulacion, se recorren
    todas las puertas de bcn_airport y se marcan libres (sin matricula)."""
    for terminal in bcn.terminal:
        for area in terminal.boarding_area:
            for gate in area.gate:
                gate.occupancy = False
                gate.aircraft_id = ""


def _prepare_lebl_gate_operations(require_movements=False):
    """
    Punto comun para botones de LEBL: comprueba que Terminals.txt este cargado,
    sincroniza vuelos desde la pestaña LEBL (Arrivals y opcionalmente Departures)
    y, si se pide, exige que ya existan movimientos combinados.
    """
    if not bcn_airport:
        return False, "Carga primero la estructura de LEBL (Terminals.txt)."
    ok, msg = _sync_lebl_flight_data()
    if not ok:
        return False, msg
    if require_movements and not all_movements:
        return (
            False,
            "No hay movimientos combinados. Comprueba Arrivals.txt y Departures.txt.",
        )
    return True, msg


def _focus_dialog_listbox():
    """Cambia la pestana derecha a «Cuadro dialogo» para que se vea la lista de resultados."""
    try:
        right_notebook.select(tab_dialog)
    except Exception:
        pass


def update_gates_listbox():
    """
    Lista el estado de cada puerta de Barcelona: ocupada o libre,
    con la matricula del avion si corresponde.
    """
    if not bcn_airport:
        set_status("⚠ Carga primero la estructura de LEBL.", "orange")
        messagebox.showwarning(
            "Estructura LEBL",
            "Carga primero la estructura con «Cargar estructura LEBL».",
        )
        return
    ocupacion = GateOccupancy(bcn_airport)
    _focus_dialog_listbox()
    listbox.delete(0, tk.END)
    if not ocupacion:
        listbox.insert(tk.END, "No se encontraron puertas en la estructura.")
        lbl_count.config(text="0 puerta(s)")
        messagebox.showwarning(
            "Ocupación de puertas",
            "No se encontraron puertas en la estructura cargada.",
        )
        return
    n_occ = 0
    for p in ocupacion:
        puerta = p["name"]
        estado = p["status"]
        avion = p["aircraft_id"]
        if estado in ("Occupied", "Ocupada"):
            n_occ += 1
            listbox.insert(tk.END, f"🔴  {puerta:<14}  [OCUPADA]  →  {avion}")
        else:
            listbox.insert(tk.END, f"🟢  {puerta:<14}  [LIBRE]")
    listbox.see(0)
    n_free = len(ocupacion) - n_occ
    lbl_count.config(text=f"{len(ocupacion)} puerta(s): {n_occ} ocupadas, {n_free} libres")
    set_status("Vista actualizada: ocupación de puertas.", "green")
    messagebox.showinfo(
        "Ocupación de puertas",
        f"{len(ocupacion)} puertas en total.\n"
        f"Ocupadas: {n_occ}\n"
        f"Libres: {n_free}\n\n"
        f"Detalle en el panel derecho → pestaña «Cuadro dialogo».",
    )


def load_airports():
    """
    Se lee la ruta del campo «Archivo de aeropuertos» (debe ser Airports.txt, no Terminals).
    LoadAirports rellena la lista; LoadAirportsDB el diccionario para mapas y distancias.
    Si no hay datos validos, se muestra un aviso que explica el formato esperado.
    """
    global airports, airports_db
    filename = archivo_entry.get().strip()
    if not filename:
        set_status("⚠ Selecciona un archivo primero.", "orange")
        return
    loaded_data = LoadAirports(filename)
    loaded_db = LoadAirportsDB(filename)
    if loaded_data:
        airports = loaded_data
        if loaded_db:
            airports_db = loaded_db
        elif not airports_db:
            airports_db = LoadAirportsDB(filename)
        update_listbox()
        set_status(
            f"✔ {len(airports)} aeropuertos cargados desde '{os.path.basename(filename)}'.",
            "green",
        )
    else:
        set_status("✘ No se pudieron cargar aeropuertos.", "red")
        if os.path.isfile(filename):
            hint = (
                "\n\nEl archivo existe pero no tiene filas CODE LAT LON "
                "(formato de Airports.txt).\n"
                "Si es Terminals.txt, usa la pestaña LEBL → «Cargar estructura»."
            )
        else:
            hint = "\n\nComprueba la ruta o el nombre del archivo."
        messagebox.showerror(
            "Error de carga", f"No se pudieron cargar aeropuertos desde:\n{filename}{hint}"
        )


def apply_schengen():
    """
    Marca cada aeropuerto cargado como Schengen o no Schengen
    segun las dos primeras letras de su codigo ICAO.
    """
    if not airports:
        set_status("⚠ No hay aeropuertos en memoria.", "orange")
        return
    for a in airports:
        SetSchengen(a)
    update_listbox()
    set_status(f"✔ Schengen aplicado a {len(airports)} aeropuertos.", "green")


def save_airports():
    """
    Guarda solo los aeropuertos Schengen en un archivo de texto.
    Si no se ha indicado ruta, abre el explorador para elegir dónde guardar.
    """
    filename = save_entry.get().strip()
    if not filename:
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")],
            title="Guardar aeropuertos Schengen",
        )
        if not filename:
            return
        save_entry.delete(0, tk.END)
        save_entry.insert(0, filename)
    result = SaveSchengenAirports(airports, filename)
    if result == 0:
        set_status(f"✔ Guardado en '{os.path.basename(filename)}'.", "green")
        messagebox.showinfo("Guardado", f"Aeropuertos guardados en:\n{filename}")
    else:
        set_status("✘ Lista vacía, nada que guardar.", "red")
        messagebox.showerror("Error", "La lista está vacía.")


def plot_data():
    """Muestra un gráfico 2D con la posición de todos los aeropuertos cargados."""
    if airports:
        run_embedded_plot(PlotAirports, airports)
    else:
        set_status("⚠ No hay aeropuertos.", "orange")


def map_data():
    """
    Exporta los aeropuertos a un archivo KML que se puede abrir con Google Earth.
    Pregunta al usuario dónde quiere guardar el archivo.
    """
    if not airports:
        set_status("⚠ No hay aeropuertos.", "orange")
        return
    filepath = filedialog.asksaveasfilename(
        defaultextension=".kml",
        filetypes=[("KML Files", "*.kml"), ("Todos", "*.*")],
        title="Exportar a Google Earth",
    )
    if filepath:
        result = MapAirports(airports, filepath)
        if result == 0:
            set_status(f"✔ Mapa KML guardado en '{os.path.basename(filepath)}'.", "green")
            messagebox.showinfo("Exportado", f"Mapa guardado en:\n{filepath}")
        else:
            set_status("✘ Error al guardar el mapa.", "red")


def add_airport():
    """
    Añade un aeropuerto nuevo a la lista usando los datos del formulario.
    Comprueba que el código sea de 4 letras y que las coordenadas sean números.
    """
    code = code_entry.get().upper().strip()
    try:
        lat = float(lat_entry.get())
        lon = float(lon_entry.get())
        if len(code) == 4 and code.isalpha():
            AddAirport(airports, Airport(code, lat, lon))
            update_listbox()
            code_entry.delete(0, tk.END)
            lat_entry.delete(0, tk.END)
            lon_entry.delete(0, tk.END)
            set_status(f"✔ Aeropuerto {code} añadido.", "green")
        else:
            messagebox.showwarning(
                "Código inválido", "El código ICAO debe tener exactamente 4 letras."
            )
    except ValueError:
        messagebox.showerror("Error", "Latitud y longitud deben ser números.")


def delete_airport():
    """Elimina un aeropuerto de la lista buscándolo por su código ICAO."""
    code = del_entry.get().upper().strip()
    if not code:
        return
    result = RemoveAirport(airports, code)
    if result == 0:
        update_listbox()
        del_entry.delete(0, tk.END)
        set_status(f"✔ Aeropuerto {code} eliminado.", "green")
    else:
        set_status(f"✘ No se encontró '{code}'.", "red")
        messagebox.showerror(
            "No encontrado", f"No existe el aeropuerto con código {code}."
        )


def load_arrivals_data():
    """
    Se lee la ruta del campo de llegadas y se llama a LoadArrivals.
    Los aviones quedan en la variable global aircrafts y se actualiza la lista derecha.
    Si el archivo esta vacio o mal formado, se muestra error.
    """
    global aircrafts
    filename = arrivals_entry.get().strip()
    if not filename:
        set_status("⚠ Selecciona un archivo de vuelos.", "orange")
        return
    loaded = LoadArrivals(filename)
    if loaded:
        aircrafts = loaded
        set_status(f"✔ {len(aircrafts)} vuelos cargados.", "green")
        messagebox.showinfo(
            "Vuelos cargados", f"Se cargaron {len(aircrafts)} vuelos correctamente."
        )
    else:
        set_status("✘ No se pudieron cargar los vuelos.", "red")
        messagebox.showerror("Error", "No se pudo leer el archivo de llegadas.")

def load_departures_data():
    """Carga el archivo de salidas y guarda los vuelos en la lista 'departures'."""
    global departures
    filename = departures_entry.get().strip()
    if not filename:
        set_status("⚠ Selecciona un archivo de vuelos.", "orange")
        return
    loaded, status = LoadDepartures(filename)
    if loaded:
        departures = loaded
        set_status(f"✔ {len(departures)} vuelos cargados.", "green")
        messagebox.showinfo("Vuelos cargados", f"Se cargaron {len(departures)} vuelos correctamente.")
    else:
        set_status("✘ No se pudieron cargar los vuelos.", "red")
        messagebox.showerror("Error", "No se pudo leer el archivo de salidas.")


def plot_arrivals_data():

    if aircrafts:
        run_embedded_plot(PlotArrivals, aircrafts)
    else:
        set_status("⚠ Carga vuelos primero.", "orange")


def plot_airlines_data():
    """Muestra un gráfico con cuántos vuelos tiene cada aerolínea."""
    if aircrafts:
        run_embedded_plot(PlotAirlines, aircrafts)
    else:
        set_status("⚠ Carga vuelos primero.", "orange")


def plot_flights_type_data():
    """Muestra un gráfico dividiendo los vuelos en Schengen y No Schengen."""
    if aircrafts:
        run_embedded_plot(PlotFlightsType, aircrafts)
    else:
        set_status("⚠ Carga vuelos primero.", "orange")


def save_flights_data():
    """
    Guarda la lista de vuelos en un archivo de texto.
    Pide al usuario que elija dónde guardarlo.
    """
    if not aircrafts:
        set_status("⚠ No hay vuelos en memoria.", "orange")
        return
    filepath = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")],
        title="Guardar vuelos",
    )
    if filepath:
        res = SaveFlights(aircrafts, filepath)
        if res == 0:
            set_status(f"✔ Vuelos guardados en '{os.path.basename(filepath)}'.", "green")
            messagebox.showinfo("Guardado", f"Vuelos guardados en:\n{filepath}")
        else:
            set_status("✘ Error al guardar vuelos.", "red")


def _ensure_airports_db_for_flights():
    """Si aun no hay diccionario de aeropuertos o falta LEBL,
    se carga Airports.txt desde el campo de la pestaña Base de datos."""
    global airports_db, airports
    if airports_db and "LEBL" in airports_db:
        return True
    path = archivo_entry.get().strip()
    if not path or not os.path.isfile(path):
        messagebox.showwarning(
            "Base de aeropuertos",
            "Carga Airports.txt en la pestaña «Base de Datos»\n"
            "(o deja la ruta por defecto en data/Airports.txt).",
        )
        return False
    db = LoadAirportsDB(path)
    if not db or "LEBL" not in db:
        messagebox.showerror(
            "Base de aeropuertos",
            f"No se pudo leer la base o falta LEBL:\n{path}",
        )
        return False
    airports_db = db
    if not airports:
        airports = LoadAirports(path)
    return True


def _ensure_arrivals_for_flights():
    """Si aircrafts esta vacio, se intenta cargar Arrivals.txt
    desde el campo de la pestaña Vuelos sin pedir al usuario que pulse otra vez."""
    global aircrafts
    if aircrafts:
        return True
    path = arrivals_entry.get().strip()
    if not path or not os.path.isfile(path):
        messagebox.showwarning(
            "Vuelos",
            "Carga Arrivals.txt en la pestaña «Vuelos» primero.",
        )
        return False
    loaded = LoadArrivals(path)
    if not loaded:
        messagebox.showerror("Vuelos", f"No se pudieron leer llegadas:\n{path}")
        return False
    aircrafts = loaded
    set_status(f"✔ {len(aircrafts)} vuelos cargados.", "green")
    return True


def map_flights_data():
    """
    Crea un archivo KML con las rutas de todos los vuelos para verlos en Google Earth.
    Necesita tener cargados tanto los vuelos como los aeropuertos.
    """
    if not _ensure_arrivals_for_flights() or not _ensure_airports_db_for_flights():
        set_status("⚠ Carga vuelos y aeropuertos primero.", "orange")
        return
    res = MapFlights(aircrafts, airports_db)
    kml_path = FlightsKmlPath()
    if res == 0:
        set_status("✔ 'flights.kml' generado correctamente.", "green")
        messagebox.showinfo(
            "Mapa generado",
            f"El mapa de vuelos se guardó en:\n{kml_path}",
        )
    else:
        set_status("✘ Error al crear el mapa.", "red")
        messagebox.showerror(
            "Error",
            "No se pudo crear el KML.\n"
            "Comprueba que Airports.txt incluya LEBL y los origenes de tus vuelos.",
        )


def show_long_distance():
    """
    Se comprueba que haya vuelos y base de aeropuertos cargados.
    LongDistanceArrivals calcula distancias, CO2 total y lista de vuelos > 2000 km.
    Se muestra el resumen en un cuadro y, si aplica, se genera un KML solo con rutas largas (EXTRA).
    """
    if not _ensure_arrivals_for_flights() or not _ensure_airports_db_for_flights():
        set_status("⚠ Carga vuelos y aeropuertos primero.", "orange")
        return
    especiales, co2_total, co2_medio = LongDistanceArrivals(aircrafts, airports_db)
    res_kml = MapLongDistanceFlights(aircrafts, airports_db)
    kml_ld = LongDistanceKmlPath()
    if res_kml == 0:
        set_status(f"✔ {len(especiales)} vuelos largos + KML generado.", "green")
        msg_kml = f"\nKML larga distancia:\n{kml_ld}"
    else:
        set_status(f"✔ {len(especiales)} vuelos largos (sin KML).", "green")
        msg_kml = "\n(No se pudo crear el KML de larga distancia.)"
    messagebox.showinfo(
        "Larga Distancia",
        f"Vuelos a más de 2000 km: {len(especiales)}\n"
        f"CO₂ total (solo esos vuelos): {co2_total:.2f} t\n"
        f"CO₂ medio por vuelo largo: {co2_medio:.2f} t"
        + msg_kml,
    )


def merge_movements_ui():
    """
    Se cargan llegadas y salidas si aun no estan en memoria.
    MergeMovements une por matricula y guarda el resultado en all_movements.
    La lista del panel derecho muestra el resumen de cada movimiento combinado.
    """
    global all_movements
    if not aircrafts:
        set_status("⚠ Carga primero las llegadas.", "orange")
        messagebox.showwarning("Faltan llegadas", "Primero hay que cargar el archivo de llegadas.")
        return
    if not departures:
        set_status("⚠ Carga primero las salidas.", "orange")
        messagebox.showwarning("Faltan salidas", "Primero hay que cargar el archivo de salidas.")
        return
    result = MergeMovements(aircrafts, departures)
    if result == -1:
        set_status("✘ No se pudieron combinar los movimientos.", "red")
        messagebox.showerror(
            "Error",
            "No se pudieron combinar llegadas y salidas."
        )
        return
    all_movements = result
    set_status(
        f"✔ Movimientos combinados: {len(all_movements)} aviones.",
        "green"
    )
    messagebox.showinfo(
        "Movimientos combinados",
        f"Se han combinado llegadas y salidas correctamente.\n\n"
        f"Total de movimientos: {len(all_movements)}"
    )

def night_aircraft_ui():
    """
    Hace falta tener movimientos combinados (llegadas + salidas).
    NightAircraft filtra los que pernoctan y los guarda en night_aircrafts.
    La lista del panel derecho muestra matricula, origen y horas de cada uno.
    """
    global night_aircrafts
    if not aircrafts:
        set_status("⚠ Carga primero las llegadas.", "orange")
        messagebox.showwarning(
            "Night Aircraft",
            "Carga el archivo de llegadas (Arrivals.txt) en esta pestaña.",
        )
        return
    if not departures:
        set_status("⚠ Carga primero las salidas.", "orange")
        messagebox.showwarning(
            "Night Aircraft",
            "Carga el archivo de salidas (Departures.txt) en esta pestaña.",
        )
        return
    if not all_movements:
        merge_movements_ui()
        if not all_movements:
            return
    result = NightAircraft(all_movements)
    if result == -1:
        set_status("✘ No se pudieron obtener los aviones nocturnos.", "red")
        messagebox.showerror("Night Aircraft", "No hay movimientos para analizar.")
        return
    night_aircrafts = result
    _focus_dialog_listbox()
    listbox.delete(0, tk.END)
    for ac in night_aircrafts:
        arr = ac.arrival if ac.arrival not in ("", "-") else "—"
        dep = ac.departure if ac.departure not in ("", "-") else "—"
        listbox.insert(
            tk.END,
            f"🌙  {ac.id:<8}  llegada {arr:<6}  salida {dep:<6}  {ac.airline}",
        )
    listbox.see(0)
    lbl_count.config(text=f"{len(night_aircrafts)} avion(es) nocturno(s)")
    set_status(
        f"✔ {len(night_aircrafts)} aviones nocturnos encontrados.",
        "green",
    )
    messagebox.showinfo(
        "Night Aircraft",
        f"Se encontraron {len(night_aircrafts)} aviones que pernoctan.\n\n"
        f"Lista en el panel derecho → «Cuadro dialogo».",
    )


def load_airports_estructure_ui():
    """
    Se usa el archivo del campo de estructura (Terminals.txt) en la pestaña LEBL.
    LoadAirportStructure crea el objeto con terminales, areas y puertas en bcn_airport.
    Si va bien, se actualiza la lista de puertas y un mensaje de confirmacion.
    """
    global bcn_airport
    filename = structure_entry.get().strip()
    if not filename:
        set_status("⚠ Selecciona el archivo de estructura.", "orange")
        return
    result = LoadAirportStructure(filename)
    if result is not None and result != -1:
        bcn_airport = result
        update_gates_listbox()
        set_status("✔ Estructura de LEBL cargada.", "green")
        messagebox.showinfo(
            "Estructura cargada", "Estructura del aeropuerto cargada correctamente."
        )
    else:
        set_status("✘ No se pudo cargar la estructura.", "red")
        messagebox.showerror("Error", "No se pudo cargar el archivo de estructura.")


def assign_gates_ui():
    """
    Primero se comprueba que exista estructura LEBL y vuelos en Arrivals.
    Se dejan todas las puertas libres y, para cada llegada, se llama a AssignGate.
    Al terminar se muestra cuantas puertas se asignaron y cuantas no tuvieron sitio.
    """
    global bcn_airport, aircrafts
    ok, msg = _prepare_lebl_gate_operations()
    if not ok:
        set_status(f"⚠ {msg}", "orange")
        messagebox.showwarning("Asignación de puertas", msg)
        return
    _reset_bcn_gate_occupancy(bcn_airport)
    exitos = fallidos = 0
    for ac in aircrafts:
        if AssignGate(bcn_airport, ac) != "":
            exitos += 1
        else:
            fallidos += 1
    update_gates_listbox()
    set_status(
        f"✔ Asignación completada: {exitos} puertas asignadas, {fallidos} sin espacio.",
        "green",
    )
    messagebox.showinfo(
        "Asignación terminada",
        f"Puertas asignadas: {exitos}\nSin espacio disponible: {fallidos}",
    )

def assign_night_gates_ui():
    """
    Se comprueba estructura y movimientos combinados (llegadas + salidas).
    AssignNightGates asigna puerta a cada avion que pernocta, distinto de la asignacion
    hora a hora del dia. Al terminar se actualiza la lista de puertas.
    """
    ok, msg = _prepare_lebl_gate_operations(require_movements=True)
    if not ok:
        set_status(f"⚠ {msg}", "orange")
        messagebox.showwarning("Puertas nocturnas", msg)
        return
    _reset_bcn_gate_occupancy(bcn_airport)
    result = AssignNightGates(bcn_airport, all_movements)
    if result == 0:
        update_gates_listbox()
        set_status("✔ Puertas asignadas a aviones nocturnos.", "green")
    else:
        set_status("✘ No se pudieron asignar puertas nocturnas.", "red")

def plot_day_occupancy_ui():
    """
    Se comprueba estructura LEBL y movimientos combinados.
    Se llama a PlotDayOccupancy, que simula minuto a minuto y abre el grafico de ocupacion.
    """
    ok, msg = _prepare_lebl_gate_operations(require_movements=True)
    if not ok:
        set_status(f"⚠ {msg}", "orange")
        messagebox.showwarning("Simulación diaria", msg)
        return
    try:

        bcn_sim = copy.deepcopy(bcn_airport)
        PlotDayOccupancy(bcn_sim, all_movements)
        set_status(
            "✔ Simulación diaria completada.",
            "green"
        )
    except Exception as e:
        set_status(
            "✘ Error en la simulación.",
            "red"
        )
        print(e)


#  Que aporta el bloque EXTRA (resumen)
#
#  Arriba estan los botones y pestañas del proyecto (aeropuertos, vuelos, LEBL,
#  movimientos, nocturnos, puertas). Lo de abajo mejora la experiencia de uso:
#  graficos dentro de la misma ventana, barra de estado, carga automatica de
#  Airports.txt o Arrivals.txt cuando hace falta para mapas o KML, sincronizacion
#  de vuelos desde la pestaña LEBL y animacion del aeropuerto en el panel derecho
#  (mapa, reloj, velocidad).

# ===============================================================
#  FUNCIONES EXTRAS
# ===============================================================

def _clear_plot_widgets():
    """Destruye el canvas y la barra de herramientas del panel de graficos
    para poder dibujar otro grafico nuevo."""
    global _plot_canvas, _plot_toolbar
    if _plot_canvas is not None:
        try:
            _plot_canvas.get_tk_widget().destroy()
        except Exception:
            pass
    if _plot_toolbar is not None:
        try:
            _plot_toolbar.destroy()
        except Exception:
            pass
    for child in plot_body.winfo_children():
        try:
            child.destroy()
        except Exception:
            pass
    _plot_canvas = None
    _plot_toolbar = None


def close_plot_panel():
    """Oculta el panel inferior de graficos y limpia los widgets de matplotlib."""
    global _plot_canvas, _plot_toolbar
    plt.close("all")
    _clear_plot_widgets()
    plot_frame.grid_remove()
    root_frame.rowconfigure(1, weight=0)
    _plot_canvas = None
    _plot_toolbar = None
    set_status("Gráfico cerrado.", "black")


def _show_plot_panel():
    """Muestra el panel de graficos en la parte inferior de la ventana."""
    plot_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
    root_frame.rowconfigure(1, weight=2)


def _render_figure(fig):
    """Toma una figura de matplotlib y la incrusta en el panel con barra de zoom/guardar."""
    global _plot_canvas, _plot_toolbar
    _show_plot_panel()
    _clear_plot_widgets()

    _plot_canvas = FigureCanvasTkAgg(fig, master=plot_body)
    _plot_canvas.draw()
    _plot_canvas.get_tk_widget().pack(fill="both", expand=True)

    toolbar_row = ttk.Frame(plot_body)
    toolbar_row.pack(fill="x")
    _plot_toolbar = NavigationToolbar2Tk(_plot_canvas, toolbar_row)
    _plot_toolbar.update()


def _embedded_plt_show(block=None):
    """Sustituto de plt.show: en lugar de ventana nueva, redirige al panel embebido."""
    if plt.get_fignums():
        _render_figure(plt.gcf())
    return None


plt.show = _embedded_plt_show


def run_embedded_plot(plot_fn, *args):
    """
    EXTRA: en lugar de abrir una ventana aparte de matplotlib, se ejecuta la funcion
    de grafico (PlotArrivals, PlotAirports, etc.) y el resultado se incrusta abajo en la app.
    """
    plt.close("all")
    try:
        plot_fn(*args)
    except Exception as exc:
        set_status(f"✘ Error al generar el gráfico: {exc}", "red")
        messagebox.showerror("Error de gráfico", str(exc))
        return

    if plt.get_fignums():
        _render_figure(plt.gcf())
        set_status("Gráfico actualizado en el panel inferior.", "green")
    else:
        set_status("⚠ La función no generó ningún gráfico.", "orange")


def set_status(msg: str, color: str = "black"):
    """Actualiza el mensaje de la barra de estado."""
    status_var.set(f"  {msg}")
    status_label.config(foreground=color)


def make_file_row(
    parent,
    label_text: str,
    filetypes=None,
    row: int = 0,
    save_mode: bool = False,
    default_ext: str = ".txt",
):
    """Crea una fila con etiqueta, campo de texto y boton Examinar para elegir archivos."""
    if filetypes is None:
        filetypes = [("Todos los archivos", "*.*")]

    ttk.Label(parent, text=label_text).grid(
        row=row, column=0, padx=(0, 6), pady=4, sticky="e"
    )

    entry = ttk.Entry(parent, width=22)
    entry.grid(row=row, column=1, padx=4, pady=4, sticky="ew")

    def browse():
        if save_mode:
            path = filedialog.asksaveasfilename(
                defaultextension=default_ext,
                filetypes=filetypes,
                title=f"Guardar — {label_text}",
            )
        else:
            path = filedialog.askopenfilename(
                filetypes=filetypes, title=f"Abrir — {label_text}"
            )
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    btn = ttk.Button(parent, text="📂", width=3, command=browse)
    btn.grid(row=row, column=2, padx=(2, 0), pady=4)
    Tooltip(btn, "Explorar archivos")
    parent.columnconfigure(1, weight=1)
    return entry


class Tooltip:
    """Clase EXTRA: al pasar el raton sobre un widget muestra un texto de ayuda flotante."""
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tw = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _=None):
        x, y, _, cy = (
            self.widget.bbox("insert") if hasattr(self.widget, "bbox") else (0, 0, 0, 0)
        )
        x += self.widget.winfo_rootx() + 28
        y += self.widget.winfo_rooty() + cy + 20
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.tw,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
        ).pack()

    def _hide(self, _=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


# ===============================================================
#  LAYOUT PRINCIPAL
# ===============================================================

root_frame = ttk.Frame(app, padding=12)
root_frame.pack(fill="both", expand=True)
root_frame.rowconfigure(0, weight=1)
root_frame.rowconfigure(1, weight=0)
root_frame.columnconfigure(0, weight=1)

top_frame = ttk.Frame(root_frame)
top_frame.grid(row=0, column=0, sticky="nsew")
top_frame.columnconfigure(0, weight=0)
top_frame.columnconfigure(1, weight=1)
top_frame.rowconfigure(0, weight=1)

left_frame = ttk.Frame(top_frame)
left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

notebook = ttk.Notebook(left_frame)
notebook.pack(fill="both", expand=True)

tab_db = ttk.Frame(notebook, padding=12)
tab_edit = ttk.Frame(notebook, padding=12)
tab_vuelo = ttk.Frame(notebook, padding=12)
tab_lebl = ttk.Frame(notebook, padding=12)

notebook.add(tab_db, text="  🗄 Base de Datos  ")
notebook.add(tab_edit, text="  ✏ Edición  ")
notebook.add(tab_vuelo, text="  ✈ Vuelos  ")
notebook.add(tab_lebl, text="  🏗 LEBL  ")

right_frame = ttk.LabelFrame(top_frame, text="  Panel derecho  ", padding=10)
right_frame.grid(row=0, column=1, sticky="nsew")
right_frame.rowconfigure(1, weight=1)
right_frame.columnconfigure(0, weight=1)

lbl_count = ttk.Label(right_frame, text="Sin datos cargados", foreground="gray")
lbl_count.grid(row=0, column=0, sticky="w", pady=(0, 6))

right_notebook = ttk.Notebook(right_frame)
right_notebook.grid(row=1, column=0, sticky="nsew")

tab_dialog = ttk.Frame(right_notebook, padding=4)
tab_animation = ttk.Frame(right_notebook, padding=0)
right_notebook.add(tab_dialog, text="  Cuadro dialogo  ")
right_notebook.add(tab_animation, text="  Animacion  ")

tab_dialog.rowconfigure(0, weight=1)
tab_dialog.columnconfigure(0, weight=1)

scrollbar_v = ttk.Scrollbar(tab_dialog, orient="vertical")
scrollbar_v.grid(row=0, column=1, sticky="ns")
scrollbar_h = ttk.Scrollbar(tab_dialog, orient="horizontal")
scrollbar_h.grid(row=1, column=0, sticky="ew")

listbox = tk.Listbox(
    tab_dialog,
    yscrollcommand=scrollbar_v.set,
    xscrollcommand=scrollbar_h.set,
    font=("Consolas", 10),
    selectmode="extended",
    activestyle="dotbox",
)
listbox.grid(row=0, column=0, sticky="nsew")
scrollbar_v.config(command=listbox.yview)
scrollbar_h.config(command=listbox.xview)

plot_frame = ttk.LabelFrame(root_frame, text="  Gráficos  ", padding=8)
plot_frame.columnconfigure(0, weight=1)
plot_frame.rowconfigure(1, weight=1)

plot_header = ttk.Frame(plot_frame)
plot_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
plot_header.columnconfigure(0, weight=1)

ttk.Label(plot_header, text="Vista de gráfico activo", font=("Segoe UI", 9, "bold")).grid(
    row=0, column=0, sticky="w"
)
btn_close_plot = ttk.Button(
    plot_header,
    text="✕",
    width=3,
    command=close_plot_panel,
)
btn_close_plot.grid(row=0, column=1, sticky="e")
Tooltip(btn_close_plot, "Cerrar gráfico")

plot_body = ttk.Frame(plot_frame)
plot_body.grid(row=1, column=0, sticky="nsew")
plot_body.rowconfigure(0, weight=1)
plot_body.columnconfigure(0, weight=1)

# ===============================================================
#  PESTAÑA 1: BASE DE DATOS
# ===============================================================

ttk.Label(tab_db, text="Archivo de aeropuertos:", font=("Segoe UI", 9, "bold")).grid(
    row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
)

archivo_entry = make_file_row(
    tab_db,
    "Archivo:",
    filetypes=[("Archivos de texto", "*.txt"), ("CSV", "*.csv"), ("Todos", "*.*")],
    row=1,
)

ttk.Button(
    tab_db,
    text="  Cargar aeropuertos  ",
    command=load_airports,
    style="Accent.TButton",
).grid(row=2, column=0, columnspan=3, pady=(10, 6), sticky="ew")

ttk.Separator(tab_db, orient="horizontal").grid(
    row=3, column=0, columnspan=3, sticky="ew", pady=8
)

ttk.Label(tab_db, text="Herramientas:", font=("Segoe UI", 9, "bold")).grid(
    row=4, column=0, columnspan=3, sticky="w", pady=(0, 6)
)

ttk.Button(tab_db, text="🌍 Aplicar Schengen", command=apply_schengen).grid(
    row=5, column=0, columnspan=3, sticky="ew", pady=3
)
ttk.Button(tab_db, text="📊 Gráfico 2D", command=plot_data).grid(
    row=6, column=0, columnspan=3, sticky="ew", pady=3
)
ttk.Button(tab_db, text="🗺 Exportar Google Earth (.kml)", command=map_data).grid(
    row=7, column=0, columnspan=3, sticky="ew", pady=3
)

ttk.Separator(tab_db, orient="horizontal").grid(
    row=8, column=0, columnspan=3, sticky="ew", pady=8
)

ttk.Label(tab_db, text="Exportar aeropuertos Schengen:", font=("Segoe UI", 9, "bold")).grid(
    row=9, column=0, columnspan=3, sticky="w", pady=(0, 4)
)

save_entry = make_file_row(
    tab_db,
    "Destino:",
    filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")],
    row=10,
    save_mode=True,
)

ttk.Button(tab_db, text="💾 Guardar Schengen", command=save_airports).grid(
    row=11, column=0, columnspan=3, sticky="ew", pady=(6, 0)
)

tab_db.columnconfigure(1, weight=1)

# ===============================================================
#  PESTAÑA 2: EDICIÓN MANUAL
# ===============================================================

frm_add = ttk.LabelFrame(tab_edit, text=" ➕ Añadir aeropuerto ", padding=10)
frm_add.pack(fill="x", pady=(0, 10))

ttk.Label(frm_add, text="Código ICAO (4 letras):").grid(
    row=0, column=0, sticky="e", padx=5, pady=3
)
code_entry = ttk.Entry(frm_add, width=10)
code_entry.grid(row=0, column=1, sticky="w", padx=5, pady=3)

ttk.Label(frm_add, text="Latitud:").grid(row=1, column=0, sticky="e", padx=5, pady=3)
lat_entry = ttk.Entry(frm_add, width=10)
lat_entry.grid(row=1, column=1, sticky="w", padx=5, pady=3)

ttk.Label(frm_add, text="Longitud:").grid(row=2, column=0, sticky="e", padx=5, pady=3)
lon_entry = ttk.Entry(frm_add, width=10)
lon_entry.grid(row=2, column=1, sticky="w", padx=5, pady=3)

ttk.Button(
    frm_add,
    text="Añadir aeropuerto",
    command=add_airport,
    style="Accent.TButton",
).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

frm_del = ttk.LabelFrame(tab_edit, text=" 🗑 Eliminar aeropuerto ", padding=10)
frm_del.pack(fill="x")

ttk.Label(frm_del, text="Código ICAO:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
del_entry = ttk.Entry(frm_del, width=10)
del_entry.grid(row=0, column=1, sticky="w", padx=5, pady=3)

ttk.Button(frm_del, text="Eliminar aeropuerto", command=delete_airport).grid(
    row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0)
)

# ===============================================================
#  PESTAÑA 3: VUELOS
# ===============================================================

ttk.Label(tab_vuelo, text="Archivo de llegadas:", font=("Segoe UI", 9, "bold")).grid(
    row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
)

arrivals_entry = make_file_row(
    tab_vuelo,
    "Archivo:",
    filetypes=[("Archivos de texto", "*.txt"), ("CSV", "*.csv"), ("Todos", "*.*")],
    row=1,
)
ttk.Label(tab_vuelo, text="Archivo de salidas:", font=("Segoe UI", 9, "bold")).grid(
    row=2, column=0, columnspan=3, sticky="w", pady=(0, 4)
)
departures_entry = make_file_row(
    tab_vuelo,
    "Salidas:",
    filetypes=[("Archivos de texto", "*.txt"), ("CSV", "*.csv"), ("Todos", "*.*")],
    row=3,
)

ttk.Button(
    tab_vuelo,
    text="  Cargar vuelos  ",
    command=load_arrivals_data,
    style="Accent.TButton",
).grid(row=4, column=0, columnspan=3, sticky="ew", pady=(8, 4))

ttk.Button(
    tab_vuelo,
    text="Cargar salidas",
    command=load_departures_data,
    style="Accent.TButton",
).grid(row=5, column=0, columnspan=3, sticky="ew", pady=(4, 4))

ttk.Separator(tab_vuelo, orient="horizontal").grid(
    row=6, column=0, columnspan=3, sticky="ew", pady=8
)

ttk.Label(tab_vuelo, text="Análisis y gráficos:", font=("Segoe UI", 9, "bold")).grid(
    row=7, column=0, columnspan=3, sticky="w", pady=(0, 6)
)

btn_data = [
    ("🔁 Combinar llegadas y salidas", merge_movements_ui),
    ("🌙 Night Aircraft", night_aircraft_ui),
    ("📈 Gráfico de llegadas", plot_arrivals_data),
    ("🏢 Aerolíneas", plot_airlines_data),
    ("✔/✘ Schengen/No", plot_flights_type_data),
    ("🗺 Mapear vuelos (KML)", map_flights_data),
    ("📏 Vuelos > 2000 km", show_long_distance),
    ("💾 Guardar vuelos (.txt)", save_flights_data),
]
for idx, (label, cmd) in enumerate(btn_data):
    r, c = divmod(idx, 2)
    ttk.Button(tab_vuelo, text=label, command=cmd).grid(
        row=9 + r, column=c, padx=4, pady=4, sticky="ew"
    )

tab_vuelo.columnconfigure(0, weight=1)
tab_vuelo.columnconfigure(1, weight=1)

# ===============================================================
#  PESTAÑA 4: ESTRUCTURA LEBL
# ===============================================================

ttk.Label(tab_lebl, text="Archivo de estructura:", font=("Segoe UI", 9, "bold")).grid(
    row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
)

structure_entry = make_file_row(
    tab_lebl,
    "Archivo:",
    filetypes=[("Archivos de texto", "*.txt"), ("XML", "*.xml"), ("Todos", "*.*")],
    row=1,
)

ttk.Button(
    tab_lebl,
    text="  Cargar estructura LEBL  ",
    command=load_airports_estructure_ui,
    style="Accent.TButton",
).grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 4))

ttk.Separator(tab_lebl, orient="horizontal").grid(
    row=3, column=0, columnspan=3, sticky="ew", pady=8
)

ttk.Label(tab_lebl, text="Gestión de puertas:", font=("Segoe UI", 9, "bold")).grid(
    row=4, column=0, columnspan=3, sticky="w", pady=(0, 6)
)

ttk.Button(
    tab_lebl, text="🚦 Asignación automática de puertas", command=assign_gates_ui
).grid(row=5, column=0, columnspan=3, sticky="ew", pady=4)

ttk.Button(tab_lebl, text="🔍 Ver ocupación actual", command=update_gates_listbox).grid(
    row=6, column=0, columnspan=3, sticky="ew", pady=4
)

ttk.Button(
    tab_lebl,
    text="🌙 Asignar puertas nocturnas",
    command=assign_night_gates_ui
).grid(row=7, column=0, columnspan=3, sticky="ew", pady=4)

ttk.Button(
    tab_lebl,
    text="📊 Simular ocupación diaria",
    command=plot_day_occupancy_ui
).grid(row=8, column=0, columnspan=3, sticky="ew", pady=4)

ttk.Separator(tab_lebl, orient="horizontal").grid(
    row=9, column=0, columnspan=3, sticky="ew", pady=8
)

ttk.Label(tab_lebl, text="Animacion LEBL:", font=("Segoe UI", 9, "bold")).grid(
    row=10, column=0, columnspan=3, sticky="w", pady=(0, 4)
)

lebl_arrivals_entry = make_file_row(
    tab_lebl,
    "Arrivals:",
    filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")],
    row=11,
)

btn_animate_lebl = ttk.Button(
    tab_lebl,
    text="  Animar Llegadas Y Salidas  ",
    style="Accent.TButton",
)
btn_animate_lebl.grid(row=12, column=0, columnspan=3, sticky="ew", pady=(8, 4))

tab_lebl.columnconfigure(1, weight=1)

# ===============================================================
#  BARRA DE ESTADO INFERIOR
# ===============================================================
ttk.Separator(app, orient="horizontal").pack(side="bottom", fill="x")

status_bar = ttk.Frame(app, relief="sunken")
status_bar.pack(side="bottom", fill="x")

status_var = tk.StringVar(value="  Listo.")
status_label = ttk.Label(
    status_bar, textvariable=status_var, anchor="w", font=("Segoe UI", 9)
)
status_label.pack(side="left", fill="x", expand=True, padx=4, pady=2)

# ===============================================================
#  ARRANQUE
# ===============================================================
archivo_entry.insert(0, os.path.join(DATA_DIR, "Airports.txt"))
arrivals_entry.insert(0, os.path.join(DATA_DIR, "Arrivals.txt"))
departures_entry.insert(0, os.path.join(DATA_DIR, "Departures.txt"))
structure_entry.insert(0, os.path.join(DATA_DIR, "Terminals.txt"))
lebl_arrivals_entry.insert(0, os.path.join(DATA_DIR, "Arrivals.txt"))
save_entry.insert(0, os.path.join(OUTPUT_DIR, "SchengenAirports.txt"))

_default_airports = os.path.join(DATA_DIR, "Airports.txt")
if os.path.isfile(_default_airports):
    _db = LoadAirportsDB(_default_airports)
    if _db:
        airports_db = _db
        _airport_list = LoadAirports(_default_airports)
        if _airport_list:
            airports = _airport_list

set_status("Listo. Selecciona una pestaña para comenzar.")


# ===============================================================
#  FUNCIONES EXTRAS — Animacion del aeropuerto (mapa con aviones, reloj, taxi)
# ===============================================================


_lebl_anim_refs = {"controller": None}
_anim_prep_queue = queue.Queue()
_anim_prep_poll_id = None
_anim_prep_generation = 0
_anim_prep_busy = False
_app_shutting_down = False


def _stop_lebl_animation():
    """Detiene el bucle de la animacion y libera el controlador del canvas."""
    global _lebl_anim_refs
    ctrl = _lebl_anim_refs.get("controller")
    if ctrl:
        try:
            ctrl["stop"]()
        except Exception:
            pass
    _lebl_anim_refs = {"controller": None}


def _stop_animation_prep_poll():
    """Cancela el temporizador que comprueba si la animacion ya esta preparada."""
    global _anim_prep_poll_id
    if _anim_prep_poll_id is not None:
        try:
            app.after_cancel(_anim_prep_poll_id)
        except Exception:
            pass
        _anim_prep_poll_id = None


def _poll_animation_prep():
    """Cada 150 ms mira si el hilo en segundo plano termino de cargar datos de animacion."""
    global _anim_prep_poll_id, _anim_prep_busy, _anim_prep_generation

    if _app_shutting_down:
        _anim_prep_poll_id = None
        return

    try:
        gen, kind, payload = _anim_prep_queue.get_nowait()
    except queue.Empty:
        _anim_prep_poll_id = app.after(150, _poll_animation_prep)
        return

    _anim_prep_poll_id = None

    if gen != _anim_prep_generation:
        if _anim_prep_busy:
            _anim_prep_poll_id = app.after(150, _poll_animation_prep)
        return

    _anim_prep_busy = False
    btn_animate_lebl.configure(state="normal")

    if kind == "ok":
        _on_animation_ready(payload, None)
    else:
        _on_animation_ready(None, payload)


def _on_animation_ready(anim_data, error):
    """
    Se llama cuando el hilo termina de preparar la animacion.
    Si hubo error, se muestra un mensaje; si no, se crea el canvas con el mapa y los aviones.
    """
    if error:
        messagebox.showerror("Error al animar", str(error))
        set_status(f"Error animacion LEBL: {error}", "red")
        for child in tab_animation.winfo_children():
            child.destroy()
        return
    if _show_lebl_canvas_animation(anim_data):
        total = anim_data.get("total_flights", len(anim_data["operations"]))
        valid = anim_data.get("valid_flights", total)
        n = len(anim_data["operations"])
        skipped = valid - n
        msg = (
            f"Animacion LEBL: {n} de {valid} vuelos validos "
            f"({anim_data['operations'][0]['arrivalLabel']}–"
            f"{max(anim_data['operations'], key=lambda o: o['arrivalStartMs'])['arrivalLabel']})"
        )
        if skipped > 0 and LEBL_ANIM_FLIGHT_LIMIT is not None:
            msg += f" | {skipped} no incluidos (limite {LEBL_ANIM_FLIGHT_LIMIT})"
        if not anim_data.get("departures_from_file"):
            msg += " | solo llegadas (sin Departures.txt)"
        set_status(msg, "green")


def _show_animation_loading():
    """Muestra mensaje de «cargando» en el panel de animacion mientras se preparan datos."""
    for child in tab_animation.winfo_children():
        child.destroy()
    right_notebook.select(tab_animation)
    ttk.Label(
        tab_animation,
        text="Preparando animacion...\n(calculando rutas, un momento)",
        font=("Segoe UI", 11),
        justify="center",
    ).pack(expand=True, pady=40)


def _show_lebl_canvas_animation(anim_data):
    """
    Se vacia la pestana Animacion, se llama a CreateLEBLAnimationWidget con los datos
  ya calculados y se guarda el controlador para poder detener la animacion al cerrar.
    """
    _stop_lebl_animation()

    for child in tab_animation.winfo_children():
        child.destroy()

    right_notebook.select(tab_animation)
    tab_animation.update_idletasks()

    try:
        controller = CreateLEBLAnimationWidget(tab_animation, anim_data)
    except Exception as exc:
        messagebox.showerror("Error al mostrar animacion", str(exc))
        return False

    tab_animation.update_idletasks()

    _lebl_anim_refs = {"controller": controller}
    return True


def _load_aircrafts_for_lebl(arrivals_path):
    """
    Primero se intenta el formato basico de cuatro columnas con LoadArrivals.
    Si no hay resultados, se lee el AIP, se obtienen stands y se usa ParseFlightsFile
    para el formato ampliado de llegadas.
    """
    acs = LoadArrivals(arrivals_path)
    if acs:
        return acs

    from src.aircraft import (
        ParseFlightsFile,
        LeblLoadAipTextStand,
        LeblAipPath,
        ParseAipStands,
        PASSENGER_AIRLINE_STANDS,
    )

    aip_text = LeblLoadAipTextStand(LeblAipPath())
    stands = ParseAipStands(aip_text, categories={"airline"})
    stand_ids = sorted(PASSENGER_AIRLINE_STANDS & {s["id"] for s in stands})
    flights = ParseFlightsFile(arrivals_path, stand_ids)

    acs = []
    for f in flights:
        if f.arrival in ("-", ""):
            continue
        ac = Aircraft(f.aircraft, f.airline, f.origin, f.arrival)
        ac.departure = f.departure if f.departure not in ("-", "") else "-"
        ac.destination = f.destination or "-"
        ac.gate = f.gate
        acs.append(ac)
    return acs


def _sync_lebl_flight_data():
    """
    Lee Arrivals (y Departures si hay ruta) desde los campos de la pestaña LEBL.
    Rellena aircrafts, departures, all_movements y night_aircrafts para puertas y animacion.
    Devuelve (True, mensaje) o (False, motivo del fallo).
    """
    global aircrafts, departures, all_movements, night_aircrafts

    arrivals_path = lebl_arrivals_entry.get().strip()
    if not arrivals_path or not os.path.exists(arrivals_path):
        return False, "Indica un archivo Arrivals.txt valido en la pestaña LEBL."

    aircrafts = _load_aircrafts_for_lebl(arrivals_path)
    if not aircrafts:
        return False, "No se encontraron vuelos en el archivo Arrivals (formato legado 4 columnas)."

    dep_path = departures_entry.get().strip()
    if dep_path and os.path.exists(dep_path):
        departures, status = LoadDepartures(dep_path)
        if status != -1 and departures:
            all_movements = MergeMovements(aircrafts, departures)
        else:
            all_movements = list(aircrafts)
    else:
        departures = []
        all_movements = list(aircrafts)

    night_aircrafts = NightAircraft(all_movements)
    if night_aircrafts == -1:
        night_aircrafts = []

    return True, f"{len(aircrafts)} llegadas sincronizadas."


def _build_gate_assignments_from_bcn():
    """Tras asignar puertas en LEBL, traduce nombres de puerta a ids de stand AIP."""
    if not bcn_airport:
        return {}
    from src.aircraft import (
        BuildGateAssignmentsFromBcn,
        ParseAipStands,
        LeblLoadAipTextStand,
        LeblAipPath,
        PASSENGER_AIRLINE_STANDS,
    )
    aip_text = LeblLoadAipTextStand(LeblAipPath())
    stands = ParseAipStands(aip_text, categories={"airline"})
    stand_ids = sorted(PASSENGER_AIRLINE_STANDS & {s["id"] for s in stands})
    return BuildGateAssignmentsFromBcn(bcn_airport, stand_ids)


def _resolve_departures_path_for_animation():
    """
    Decide que archivo de salidas usar para la animacion (campo Departures).
    Si no hay archivo, se puede preguntar al usuario o continuar solo con llegadas.
    Devuelve la ruta y un indicador de si faltan salidas.
    """
    dep_path = departures_entry.get().strip()
    if dep_path and os.path.isfile(dep_path):
        return dep_path, False

    msg = (
        "No se encontro Departures.txt.\n\n"
        "Sin el, la animacion usara solo Arrivals.txt:\n"
        "  • Todos los aviones llegaran y se quedaran aparcados\n"
        "  • No habra salidas ni aviones ya aparcados al inicio\n"
        "  • No se inventaran horas de salida\n\n"
        "¿Quieres seleccionar un archivo de salidas ahora?"
    )
    if messagebox.askyesno("Salidas no cargadas", msg):
        chosen = filedialog.askopenfilename(
            title="Seleccionar Departures.txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")],
            initialdir=DATA_DIR,
        )
        if chosen:
            departures_entry.delete(0, tk.END)
            departures_entry.insert(0, chosen)
            return chosen, False
    return None, True


def animate_lebl_operations_ui():
    """
    Flujo del boton Animar Llegadas Y Salidas (mapa + reloj en panel Animacion).
    La animacion usa Arrivals+Departures y data/LEBL_Taxiways.txl via GenerateLEBLAnimation.
    """
    global _anim_prep_generation, _anim_prep_busy

    if _app_shutting_down:
        return
    if _anim_prep_busy:
        set_status("⚠ Ya se esta preparando una animacion.", "orange")
        return

    ok, msg = _sync_lebl_flight_data()
    if not ok:
        messagebox.showwarning("Atencion", msg)
        set_status(f"⚠ {msg}", "orange")
        return

    set_status(f"✔ {msg}", "green")

    if not bcn_airport:
        messagebox.showwarning(
            "Estructura LEBL",
            "Sin estructura LEBL cargada se usaran puertas por defecto en el mapa.\n"
            "Puedes cargar Terminals.txt y usar los botones de puertas aparte.",
        )

    arrivals_path = lebl_arrivals_entry.get().strip()
    departures_path, no_departures = _resolve_departures_path_for_animation()
    bcn_snapshot = bcn_airport

    _stop_lebl_animation()
    _stop_animation_prep_poll()
    while not _anim_prep_queue.empty():
        try:
            _anim_prep_queue.get_nowait()
        except queue.Empty:
            break

    _anim_prep_generation += 1
    my_generation = _anim_prep_generation
    _anim_prep_busy = True

    _show_animation_loading()
    limit_label = "todos" if LEBL_ANIM_FLIGHT_LIMIT is None else str(LEBL_ANIM_FLIGHT_LIMIT)
    dep_note = " (solo llegadas, sin Departures)" if no_departures else ""
    set_status(f"Preparando animacion ({limit_label} los vuelos validos){dep_note}...", "orange")
    btn_animate_lebl.configure(state="disabled")

    def _worker():
        try:
            anim_data = GenerateLEBLAnimation(
                arrivals_path,
                limit=LEBL_ANIM_FLIGHT_LIMIT,
                bcn_airport=bcn_snapshot,
                departures_path=departures_path,
            )
            _anim_prep_queue.put((my_generation, "ok", anim_data))
        except Exception as exc:
            _anim_prep_queue.put((my_generation, "err", exc))

    threading.Thread(target=_worker, daemon=True).start()
    _anim_prep_poll_id = app.after(150, _poll_animation_prep)
    return


btn_animate_lebl.configure(command=animate_lebl_operations_ui)


def _shutdown_application():
    """Al cerrar la app: para animacion, graficos y cola de preparacion de forma ordenada."""
    global _app_shutting_down, _anim_prep_busy, _anim_prep_generation

    if _app_shutting_down:
        return
    _app_shutting_down = True
    _anim_prep_busy = False
    _anim_prep_generation += 1

    _stop_lebl_animation()
    _stop_animation_prep_poll()

    while not _anim_prep_queue.empty():
        try:
            _anim_prep_queue.get_nowait()
        except queue.Empty:
            break

    try:
        close_plot_panel()
    except Exception:
        try:
            plt.close("all")
            _clear_plot_widgets()
        except Exception:
            pass

    try:
        if app.winfo_exists():
            for child in list(tab_animation.winfo_children()):
                try:
                    child.destroy()
                except Exception:
                    pass
    except Exception:
        pass

    try:
        plt.close("all")
    except Exception:
        pass

    try:
        if app.winfo_exists():
            app.withdraw()
            app.update_idletasks()
            app.quit()
    except Exception:
        pass


def _on_app_close():
    """Manejador del boton X de la ventana: llama a _shutdown_application y cierra."""
    _shutdown_application()
    try:
        app.quit()
    except Exception:
        os._exit(0)


app.protocol("WM_DELETE_WINDOW", _on_app_close)

try:
    app.mainloop()
except KeyboardInterrupt:
    _shutdown_application()
finally:
    plt.show = _original_plt_show
    os._exit(0)