import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os

from src.airport import Airport, LoadAirports, AddAirport, RemoveAirport, SetSchengen, SaveSchengenAirports, PlotAirports, \
    MapAirports

from src.aircraft import LoadArrivals, PlotArrivals, SaveFlights, PlotAirlines, PlotFlightsType, \
    LoadAirports as LoadAirportsDB, MapFlights, LongDistanceArrivals

airports = []
aircrafts = []
airports_db = {}

app = tk.Tk()
app.title("Gestor de Aeropuertos y Vuelos")

# --- Centrar la ventana inicialmente ---
window_width = 1050
window_height = 700
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()
x_cordinate = int((screen_width/2) - (window_width/2))
y_cordinate = int((screen_height/2) - (window_height/2))
app.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

# --- Cargar el tema ---
try:
    app.tk.call('source', 'forest-light.tcl')
    ttk.Style().theme_use('forest-light')
except tk.TclError:
    print("Aviso: No se encontró el archivo forest-light.tcl. Usando tema por defecto.")

# ================= FUNCIONES LÓGICAS (Intactas) =================
def update_listbox():
    listbox.delete(0, tk.END)
    i = 0
    while i < len(airports):
        a = airports[i]
        schengen_status = "Schengen" if a.schengen else "No schengen"
        # Usamos formato para tabular visualmente (requiere fuente monoespaciada como Consolas)
        texto = f"{a.code:<6} | Lat: {a.lat:<8} | Lon: {a.lon:<8} | {schengen_status}"
        listbox.insert(tk.END, texto)
        i += 1

def load_airports():
    global airports, airports_db
    filename = archivo_entry.get()
    loaded_data = LoadAirports(filename)
    loaded_db = LoadAirportsDB(filename)
    if loaded_data:
        airports = loaded_data
        if loaded_db:
            airports_db = loaded_db
        update_listbox()
        messagebox.showinfo("INFO", "Aeropuertos cargados")
    else:
        messagebox.showerror("ERROR", "No se han cargado aeropuertos")

def add_airport():
    code = code_entry.get().upper()
    try:
        lat = float(lat_entry.get())
        lon = float(lon_entry.get())
        if len(code) == 4 and code.isalpha():
            new_airport = Airport(code, lat, lon)
            AddAirport(airports, new_airport)
            update_listbox()
            code_entry.delete(0, tk.END)
            lat_entry.delete(0, tk.END)
            lon_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", "El Codigo ICAO debe de ser 4 letras.")
    except ValueError:
        messagebox.showerror("Error", "La latitud y la longitud deben ser numeros")

def delete_airport():
    code = del_entry.get().upper()
    result = RemoveAirport(airports, code)
    if result == 0:
        update_listbox()
        del_entry.delete(0, tk.END)
    else:
        messagebox.showerror("Error", "No se ha encontrado el aeropuerto en la lista")

def apply_schengen():
    i = 0
    while i < len(airports):
        SetSchengen(airports[i])
        i += 1
    update_listbox()
    messagebox.showinfo("Success", "Schengen aplicado")

def save_airports():
    filename = save_entry.get()
    result = SaveSchengenAirports(airports, filename)
    if result == 0:
        messagebox.showinfo("Success", f"Los aeropuertos se han guardado en: {filename}")
    else:
        messagebox.showerror("Error", "La lista esta vacia")

def plot_data():
    if airports:
        PlotAirports(airports)
    else:
        messagebox.showwarning("Warning", "No hay aeropuertos")

def map_data():
    if airports:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".kml",
            filetypes=[("KML Files", "*.kml"), ("All Files", "*.*")],
            title="Guardar mapa en Google Earth"
        )
        if filepath:
            result = MapAirports(airports, filepath)
            if result == 0:
                messagebox.showinfo("Success", f"El mapa se ha guardado en:\n{filepath}")
            else:
                messagebox.showerror("Error", "No se ha podido guardar el mapa")
    else:
        messagebox.showwarning("Warning", "No hay aeropuertos que guardar")

def load_arrivals_data():
    global aircrafts
    filename = arrivals_entry.get()
    loaded = LoadArrivals(filename)
    if loaded:
        aircrafts = loaded
        messagebox.showinfo("INFO", f"Se han cargado {len(aircrafts)} vuelos exitosamente.")
    else:
        messagebox.showerror("ERROR", "No se han podido cargar los vuelos. Revisa el archivo.")

def plot_arrivals_data():
    if aircrafts:
        PlotArrivals(aircrafts)
    else:
        messagebox.showwarning("Warning", "Primero debes cargar los vuelos (Arrivals).")

def plot_airlines_data():
    if aircrafts:
        PlotAirlines(aircrafts)
    else:
        messagebox.showwarning("Warning", "Primero debes cargar los vuelos (Arrivals).")

def plot_flights_type_data():
    if aircrafts:
        PlotFlightsType(aircrafts)
    else:
        messagebox.showwarning("Warning", "Primero debes cargar los vuelos (Arrivals).")

def save_flights_data():
    if aircrafts:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Guardar Vuelos"
        )
        if filepath:
            res = SaveFlights(aircrafts, filepath)
            if res == 0:
                messagebox.showinfo("Success", f"Vuelos guardados en:\n{filepath}")
            else:
                messagebox.showerror("Error", "Hubo un problema al guardar los vuelos.")
    else:
        messagebox.showwarning("Warning", "No hay vuelos para guardar.")

def map_flights_data():
    if aircrafts and airports_db:
        res = MapFlights(aircrafts, airports_db)
        if res == 0:
            messagebox.showinfo("Success", "El mapa de vuelos se ha guardado en 'flights.kml'")
        else:
            messagebox.showerror("Error", "Error al crear el mapa (¿Falta el aeropuerto LEBL en la base de datos?)")
    else:
        messagebox.showwarning("Warning", "Debes cargar los vuelos Y los aeropuertos primero.")

def show_long_distance():
    if aircrafts and airports_db:
        especiales = LongDistanceArrivals(aircrafts, airports_db)
        messagebox.showinfo("Larga Distancia", f"Número de vuelos a más de 2000km: {len(especiales)}")
    else:
        messagebox.showwarning("Warning", "Debes cargar los vuelos Y los aeropuertos primero.")


# ================= INTERFAZ GRÁFICA (UI) MEJORADA =================

# Contenedor principal
main_container = ttk.Frame(app, padding=15)
main_container.pack(fill="both", expand=True)

# ---> ESTRUCTURA DE DOS COLUMNAS <---
# Panel izquierdo (Herramientas). Le decimos que ocupe todo el alto (fill="y")
left_panel = ttk.Frame(main_container)
left_panel.pack(side="left", fill="y", padx=(0, 15))

# Panel derecho (Visualización). Le decimos que se expanda para llenar todo lo demás (expand=True)
right_panel = ttk.LabelFrame(main_container, text=" Vista de Aeropuertos en Memoria ", padding=10)
right_panel.pack(side="right", fill="both", expand=True)

# ----------------- PANEL DERECHO (LISTBOX) -----------------
# Al estar en el panel derecho con expand=True, si maximizas la pantalla, la lista crecerá.
scrollbar = ttk.Scrollbar(right_panel)
scrollbar.pack(side="right", fill="y")
listbox = tk.Listbox(right_panel, yscrollcommand=scrollbar.set, font=("Consolas", 10))
listbox.pack(side="left", fill="both", expand=True)
scrollbar.config(command=listbox.yview)

# ----------------- PANEL IZQUIERDO (CONTROLES) -----------------

# --- 1. SECCIÓN: CARGA DE AEROPUERTOS ---
frame_load = ttk.LabelFrame(left_panel, text=" 1. Base de Datos ", padding=10)
frame_load.pack(fill="x", pady=(0, 10))

ttk.Label(frame_load, text="Archivo:").grid(row=0, column=0, padx=5, sticky="e")
archivo_entry = ttk.Entry(frame_load, width=20)
archivo_entry.grid(row=0, column=1, padx=5)
ttk.Button(frame_load, text="Cargar", command=load_airports, style="Accent.TButton").grid(row=0, column=2, padx=5)

# --- 2. SECCIÓN: EDICIÓN ---
frame_edit = ttk.LabelFrame(left_panel, text=" 2. Edición Manual ", padding=10)
frame_edit.pack(fill="x", pady=10)

# Inputs de Agregar
ttk.Label(frame_edit, text="ICAO:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
code_entry = ttk.Entry(frame_edit, width=12)
code_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")

ttk.Label(frame_edit, text="Latitud:").grid(row=1, column=0, padx=5, pady=2, sticky="e")
lat_entry = ttk.Entry(frame_edit, width=12)
lat_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")

ttk.Label(frame_edit, text="Longitud:").grid(row=2, column=0, padx=5, pady=2, sticky="e")
lon_entry = ttk.Entry(frame_edit, width=12)
lon_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")

ttk.Button(frame_edit, text="Agregar Aeropuerto", command=add_airport).grid(row=3, column=0, columnspan=2, pady=(10,0))

# Separador
ttk.Separator(frame_edit, orient="vertical").grid(row=0, column=2, rowspan=4, sticky="ns", padx=15)

# Inputs de Borrar
ttk.Label(frame_edit, text="Borrar (ICAO):").grid(row=0, column=3, padx=5, sticky="w")
del_entry = ttk.Entry(frame_edit, width=12)
del_entry.grid(row=1, column=3, padx=5, pady=(0,10))
ttk.Button(frame_edit, text="Eliminar", command=delete_airport).grid(row=2, column=3, pady=5)

# --- 3. SECCIÓN: UTILIDADES ---
frame_utils = ttk.LabelFrame(left_panel, text=" 3. Herramientas ", padding=10)
frame_utils.pack(fill="x", pady=10)

ttk.Button(frame_utils, text="Aplicar Schengen", command=apply_schengen).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
ttk.Button(frame_utils, text="Gráfico 2D", command=plot_data).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
ttk.Button(frame_utils, text="Exp. Google Earth", command=map_data).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

ttk.Separator(frame_utils, orient="horizontal").grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)

ttk.Label(frame_utils, text="Exportar archivo Schengen:").grid(row=2, column=0, columnspan=2, sticky="w", padx=5)
save_entry = ttk.Entry(frame_utils, width=15)
save_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5)
ttk.Button(frame_utils, text="Guardar", command=save_airports).grid(row=3, column=2, padx=5)

# --- 4. SECCIÓN: VUELOS ---
frame_aircraft = ttk.LabelFrame(left_panel, text=" 4. Análisis de Vuelos (Arrivals) ", padding=10)
frame_aircraft.pack(fill="x", pady=10)

ttk.Label(frame_aircraft, text="Archivo:").grid(row=0, column=0, padx=5, sticky="e")
arrivals_entry = ttk.Entry(frame_aircraft, width=15)
arrivals_entry.grid(row=0, column=1, padx=5)
ttk.Button(frame_aircraft, text="Cargar Vuelos", command=load_arrivals_data, style="Accent.TButton").grid(row=0, column=2, padx=5)

# Organizar botones de vuelos en una sub-cuadrícula para que no se estiren feo
btn_grid = ttk.Frame(frame_aircraft)
btn_grid.grid(row=1, column=0, columnspan=3, pady=10)

ttk.Button(btn_grid, text="Gráfico Llegadas", command=plot_arrivals_data).grid(row=0, column=0, padx=3, pady=3, sticky="ew")
ttk.Button(btn_grid, text="Aerolíneas", command=plot_airlines_data).grid(row=0, column=1, padx=3, pady=3, sticky="ew")
ttk.Button(btn_grid, text="Schengen/No", command=plot_flights_type_data).grid(row=0, column=2, padx=3, pady=3, sticky="ew")
ttk.Button(btn_grid, text="Mapear LEBL", command=map_flights_data).grid(row=1, column=0, padx=3, pady=3, sticky="ew")
ttk.Button(btn_grid, text="> 2000km", command=show_long_distance).grid(row=1, column=1, padx=3, pady=3, sticky="ew")
ttk.Button(btn_grid, text="Guardar TXT", command=save_flights_data).grid(row=1, column=2, padx=3, pady=3, sticky="ew")

app.mainloop()