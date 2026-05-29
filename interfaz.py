import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Imports
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
    LoadArrivals,
    PlotArrivals,
    SaveFlights,
    PlotAirlines,
    PlotFlightsType,
    LoadAirports as LoadAirportsDB,
    MapFlights,
    LongDistanceArrivals,
)
from src.LEBL import LoadAirportStructure, GateOccupancy, AssignGate

# ===============================================================
#  ESTADO GLOBAL
# ===============================================================
airports = []
aircrafts = []
airports_db = {}
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

# Tema Forest-Light
try:
    app.tk.call("source", "forest-light.tcl")
    ttk.Style().theme_use("forest-light")
except tk.TclError:
    print("Aviso: forest-light.tcl no encontrado. Usando tema por defecto.")


# ===============================================================
#  PANEL DE GRÁFICOS EMBEBIDOS
# ===============================================================

def _clear_plot_widgets():
    global _plot_canvas, _plot_toolbar
    for child in plot_body.winfo_children():
        child.destroy()
    _plot_canvas = None
    _plot_toolbar = None


def close_plot_panel():
    """Cierra el gráfico y devuelve el espacio a los controles superiores."""
    global _plot_canvas, _plot_toolbar
    plt.close("all")
    _clear_plot_widgets()
    plot_frame.grid_remove()
    root_frame.rowconfigure(1, weight=0)
    _plot_canvas = None
    _plot_toolbar = None
    set_status("Gráfico cerrado.", "black")


def _show_plot_panel():
    plot_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
    root_frame.rowconfigure(1, weight=2)


def _render_figure(fig):
    """Muestra una figura de Matplotlib en el panel inferior."""
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
    """Sustituto de plt.show() para dibujar dentro de la ventana principal."""
    if plt.get_fignums():
        _render_figure(plt.gcf())
    return None


plt.show = _embedded_plt_show


def run_embedded_plot(plot_fn, *args):
    """Ejecuta una función de plot de src y la muestra en el panel inferior."""
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


# ===============================================================
#  HELPERS DE UX
# ===============================================================


def set_status(msg: str, color: str = "black"):
    """Actualiza la barra de estado inferior."""
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
    """
    Crea una fila compuesta por:  [Label]  [Entry]  [Botón 📂]
    Devuelve el widget Entry para que el caller pueda leerlo.
    """
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
    """Tooltip sencillo que aparece al hacer hover sobre un widget."""

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
#  LÓGICA DE LA APLICACIÓN
# ===============================================================


def update_listbox(items=None):
    """Refresca el listbox principal con los aeropuertos en memoria."""
    listbox.delete(0, tk.END)
    if items is None:
        items = airports
    for a in items:
        sch = "✔ Schengen" if a.schengen else "✘ No Schengen"
        listbox.insert(
            tk.END, f"{a.code:<6}  Lat: {a.lat:<10.4f}  Lon: {a.lon:<10.4f}  {sch}"
        )
    lbl_count.config(text=f"{len(airports)} aeropuerto(s) en memoria")


def update_gates_listbox():
    listbox.delete(0, tk.END)
    if not bcn_airport:
        set_status("⚠ Carga primero la estructura de LEBL.", "orange")
        return
    ocupacion = GateOccupancy(bcn_airport)
    if not ocupacion:
        listbox.insert(tk.END, "No se encontraron puertas en la estructura.")
        return
    for p in ocupacion:
        puerta = p["name"]
        estado = p["status"]
        avion = p["aircraft_id"]
        if estado in ("Occupied", "Ocupada"):
            listbox.insert(tk.END, f"🔴  {puerta:<14}  [OCUPADA]  →  {avion}")
        else:
            listbox.insert(tk.END, f"🟢  {puerta:<14}  [LIBRE]")
    lbl_count.config(text=f"{len(ocupacion)} puerta(s) cargadas")
    set_status("Vista actualizada: ocupación de puertas.")


# ---------- Pestaña 1: Base de datos ----------


def load_airports():
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
        update_listbox()
        set_status(
            f"✔ {len(airports)} aeropuertos cargados desde '{os.path.basename(filename)}'.",
            "green",
        )
    else:
        set_status("✘ No se pudieron cargar aeropuertos.", "red")
        messagebox.showerror(
            "Error de carga", f"No se pudo leer el archivo:\n{filename}"
        )


def apply_schengen():
    if not airports:
        set_status("⚠ No hay aeropuertos en memoria.", "orange")
        return
    for a in airports:
        SetSchengen(a)
    update_listbox()
    set_status(f"✔ Schengen aplicado a {len(airports)} aeropuertos.", "green")


def save_airports():
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
    if airports:
        run_embedded_plot(PlotAirports, airports)
    else:
        set_status("⚠ No hay aeropuertos.", "orange")


def map_data():
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


# ---------- Pestaña 2: Edición manual ----------


def add_airport():
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


# ---------- Pestaña 3: Vuelos ----------


def load_arrivals_data():
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


def plot_arrivals_data():
    if aircrafts:
        run_embedded_plot(PlotArrivals, aircrafts)
    else:
        set_status("⚠ Carga vuelos primero.", "orange")


def plot_airlines_data():
    if aircrafts:
        run_embedded_plot(PlotAirlines, aircrafts)
    else:
        set_status("⚠ Carga vuelos primero.", "orange")


def plot_flights_type_data():
    if aircrafts:
        run_embedded_plot(PlotFlightsType, aircrafts)
    else:
        set_status("⚠ Carga vuelos primero.", "orange")


def save_flights_data():
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


def map_flights_data():
    if aircrafts and airports_db:
        res = MapFlights(aircrafts, airports_db)
        if res == 0:
            set_status("✔ 'flights.kml' generado correctamente.", "green")
            messagebox.showinfo(
                "Mapa generado", "El mapa de vuelos se guardó en 'output/flights.kml'."
            )
        else:
            set_status("✘ Error al crear el mapa.", "red")
            messagebox.showerror(
                "Error", "Error al crear el mapa (¿falta LEBL en la base de datos?)"
            )
    else:
        set_status("⚠ Carga vuelos y aeropuertos primero.", "orange")


def show_long_distance():
    if aircrafts and airports_db:
        especiales, co2_total, co2_medio = LongDistanceArrivals(aircrafts, airports_db)
        set_status(f"✔ {len(especiales)} vuelos a más de 2000 km.", "green")
        messagebox.showinfo(
            "Larga Distancia",
            f"Vuelos a más de 2000 km: {len(especiales)}\n"
            f"CO₂ total: {co2_total:.2f} t\n"
            f"CO₂ medio por vuelo: {co2_medio:.2f} t",
        )
    else:
        set_status("⚠ Carga vuelos y aeropuertos primero.", "orange")


# ---------- Pestaña 4: LEBL ----------


def load_airports_estructure_ui():
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
    global bcn_airport, aircrafts
    if not bcn_airport:
        set_status("⚠ Carga la estructura de LEBL primero.", "orange")
        return
    if not aircrafts:
        set_status("⚠ No hay vuelos cargados para asignar.", "orange")
        return
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


# ===============================================================
#  LAYOUT PRINCIPAL
# ===============================================================

root_frame = ttk.Frame(app, padding=12)
root_frame.pack(fill="both", expand=True)
root_frame.rowconfigure(0, weight=1)
root_frame.rowconfigure(1, weight=0)
root_frame.columnconfigure(0, weight=1)

# ---------- Zona superior: controles + listbox ----------
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

right_frame = ttk.LabelFrame(top_frame, text="  Vista de Datos en Memoria  ", padding=10)
right_frame.grid(row=0, column=1, sticky="nsew")
right_frame.rowconfigure(1, weight=1)
right_frame.columnconfigure(0, weight=1)

lbl_count = ttk.Label(right_frame, text="Sin datos cargados", foreground="gray")
lbl_count.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

scrollbar_v = ttk.Scrollbar(right_frame, orient="vertical")
scrollbar_v.grid(row=1, column=1, sticky="ns")
scrollbar_h = ttk.Scrollbar(right_frame, orient="horizontal")
scrollbar_h.grid(row=2, column=0, sticky="ew")

listbox = tk.Listbox(
    right_frame,
    yscrollcommand=scrollbar_v.set,
    xscrollcommand=scrollbar_h.set,
    font=("Consolas", 10),
    selectmode="extended",
    activestyle="dotbox",
)
listbox.grid(row=1, column=0, sticky="nsew")
scrollbar_v.config(command=listbox.yview)
scrollbar_h.config(command=listbox.xview)

# ---------- Zona inferior: gráficos embebidos (oculta hasta que haya un gráfico) ----------
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
#  PESTAÑA 3: VUELOS (ARRIVALS)
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

ttk.Button(
    tab_vuelo,
    text="  Cargar vuelos  ",
    command=load_arrivals_data,
    style="Accent.TButton",
).grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 4))

ttk.Separator(tab_vuelo, orient="horizontal").grid(
    row=3, column=0, columnspan=3, sticky="ew", pady=8
)

ttk.Label(tab_vuelo, text="Análisis y gráficos:", font=("Segoe UI", 9, "bold")).grid(
    row=4, column=0, columnspan=3, sticky="w", pady=(0, 6)
)

btn_data = [
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
        row=5 + r, column=c, padx=4, pady=4, sticky="ew"
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
set_status("Listo. Selecciona una pestaña para comenzar.")
app.mainloop()

# Restaurar plt.show por si se importa este módulo desde otro script
plt.show = _original_plt_show
