import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os

# Imports de las funciones que creamos en los otros archivos
from src.airport import Airport, LoadAirports, AddAirport, RemoveAirport, SetSchengen, SaveSchengenAirports, \
    PlotAirports, \
    MapAirports

from src.aircraft import LoadArrivals, PlotArrivals, SaveFlights, PlotAirlines, PlotFlightsType, \
    LoadAirports as LoadAirportsDB, MapFlights, LongDistanceArrivals

from src.LEBL import LoadAirportStructure, GateOccupancy, AssignGate

# Variables globales para guardar los datos en memoria
airports = []
aircrafts = []
airports_db = {}
bcn_airport = None  # Aqui guardaremos el objeto del aeropuerto de Barcelona

app = tk.Tk()
app.title("Gestor de Aeropuertos y Vuelos")

# --- Configuración y Centrado de Ventana ---
window_width = 1050
window_height = 750
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()
x_cordinate = int((screen_width / 2) - (window_width / 2))
y_cordinate = int((screen_height / 2) - (window_height / 2))
app.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

# --- Cargar el tema visual ---
try:
    app.tk.call('source', 'forest-light.tcl')
    ttk.Style().theme_use('forest-light')
except tk.TclError:
    print("Aviso: No se encontró el archivo forest-light.tcl. Usando tema por defecto.")


# ================= FUNCIONES LÓGICAS =================

def update_listbox():
    # Limpia la lista de la pantalla y mete los aeropuertos actualizados
    listbox.delete(0, tk.END)
    i = 0
    while i < len(airports):
        a = airports[i]
        schengen_status = "Schengen" if a.schengen else "No schengen"
        # Ajustamos el texto en columnas fijas para que quede alineado y bonito
        texto = f"{a.code:<6} | Lat: {a.lat:<8} | Lon: {a.lon:<8} | {schengen_status}"
        listbox.insert(tk.END, texto)
        i += 1


def update_gates_listbox():
    # Muestra en el cuadro central el estado de las puertas (si estan libres u ocupadas)
    listbox.delete(0, tk.END)
    if not bcn_airport:
        messagebox.showwarning("Warning", "Primero debes cargar la estructura de LEBL.")
        return

    # Sacamos la lista de diccionarios con el estado de las puertas
    ocupacion = GateOccupancy(bcn_airport)
    if not ocupacion:
        listbox.insert(tk.END, "No se encontraron puertas cargadas en la estructura.")
        return

    i = 0
    while i < len(ocupacion):
        puerta_dict = ocupacion[i]
        puerta = puerta_dict["name"]
        estado = puerta_dict["status"]
        avion = puerta_dict["aircraft_id"]

        # Si esta ocupada pone el codigo del avion, si no, la marca como LIBRE
        if estado == "Occupied" or estado == "Ocupada":
            listbox.insert(tk.END, f"Puerta: {puerta:<12}   |   [OCUPADA] -> Avión: {avion}")
        else:
            listbox.insert(tk.END, f"Puerta: {puerta:<12}    |   [LIBRE]")
        i += 1


def load_airports():
    # Controla el boton de cargar la lista de aeropuertos desde el txt
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
    # Lee los campos de texto para añadir un aeropuerto nuevo a mano
    code = code_entry.get().upper()
    try:
        lat = float(lat_entry.get())
        lon = float(lon_entry.get())
        if len(code) == 4 and code.isalpha():
            new_airport = Airport(code, lat, lon)
            AddAirport(airports, new_airport)
            update_listbox()
            # Limpiamos los cuadros de texto despues de añadirlo
            code_entry.delete(0, tk.END)
            lat_entry.delete(0, tk.END)
            lon_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", "El Codigo ICAO debe de ser 4 letras.")
    except ValueError:
        messagebox.showerror("Error", "La latitud y la longitud deben ser numeros")


def delete_airport():
    # Toma el codigo escrito y lo borra de la lista si existe
    code = del_entry.get().upper()
    result = RemoveAirport(airports, code)
    if result == 0:
        update_listbox()
        del_entry.delete(0, tk.END)
    else:
        messagebox.showerror("Error", "No se ha encontrado el aeropuerto en la lista")


def apply_schengen():
    # Aplica la comprobacion Schengen a toda la lista cargada
    i = 0
    while i < len(airports):
        SetSchengen(airports[i])
        i += 1
    update_listbox()
    messagebox.showinfo("Success", "Schengen aplicado")


def save_airports():
    # Guarda los aeropuertos procesados en un archivo nuevo
    filename = save_entry.get()
    result = SaveSchengenAirports(airports, filename)
    if result == 0:
        messagebox.showinfo("Success", f"Los aeropuertos se han guardado en: {filename}")
    else:
        messagebox.showerror("Error", "La lista esta vacia")


def plot_data():
    # Muestra el grafico 2D de los aeropuertos del mundo
    if airports:
        PlotAirports(airports)
    else:
        messagebox.showwarning("Warning", "No hay aeropuertos")


def map_data():
    # Abre la ventana para guardar el mapa de aeropuertos en KML
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
    # Carga el archivo de los aviones que van a llegar (Arrivals.txt)
    global aircrafts
    filename = arrivals_entry.get()
    loaded = LoadArrivals(filename)
    if loaded:
        aircrafts = loaded
        messagebox.showinfo("INFO", f"Se han cargado {len(aircrafts)} vuelos exitosamente.")
    else:
        messagebox.showerror("ERROR", "No se han podido cargar los vuelos. Revisa el archivo.")


def plot_arrivals_data():
    # Grafico de barras con los aviones por hora
    if aircrafts:
        PlotArrivals(aircrafts)
    else:
        messagebox.showwarning("Warning", "Primero debes cargar los vuelos (Arrivals).")


def plot_airlines_data():
    # Grafico de que aerolineas vuelan mas
    if aircrafts:
        PlotAirlines(aircrafts)
    else:
        messagebox.showwarning("Warning", "Primero debes cargar los vuelos (Arrivals).")


def plot_flights_type_data():
    # Grafico para comparar vuelos Schengen vs Internacionales
    if aircrafts:
        PlotFlightsType(aircrafts)
    else:
        messagebox.showwarning("Warning", "Primero debes cargar los vuelos (Arrivals).")


def save_flights_data():
    # Guarda la lista de aviones en un archivo de texto seleccionado
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
    # Genera el mapa KML con las lineas de las rutas hacia Barcelona
    if aircrafts and airports_db:
        res = MapFlights(aircrafts, airports_db)
        if res == 0:
            messagebox.showinfo("Success", "El mapa de vuelos se ha guardado en 'flights.kml'")
        else:
            messagebox.showerror("Error", "Error al crear el mapa (¿Falta el aeropuerto LEBL en la base de datos?)")
    else:
        messagebox.showwarning("Warning", "Debes cargar los vuelos Y los aeropuertos primero.")


def show_long_distance():
    # Cuenta y dice en un aviso los vuelos de mas de 2000km de distancia
    if aircrafts and airports_db:
        especiales = LongDistanceArrivals(aircrafts, airports_db)
        messagebox.showinfo("Larga Distancia", f"Número de vuelos a más de 2000km: {len(especiales)}")
    else:
        messagebox.showwarning("Warning", "Debes cargar los vuelos Y los aeropuertos primero.")


def load_airports_estructure_ui():
    # Carga el mapa de terminales y puertas de Barcelona (LEBL.txt)
    global bcn_airport
    filename = structure_entry.get()
    result = LoadAirportStructure(filename)
    if result != -1 and result is not None:
        bcn_airport = result
        update_gates_listbox()
        messagebox.showinfo("Info", "Estructura cargada correctamente.")
    else:
        messagebox.showerror("Error", "No se pudo cargar el archivo.")


def assign_gates_ui():
    # Ejecuta el bucle para aparcar de golpe cada avion en la puerta libre que le toque
    global bcn_airport, aircrafts
    if not bcn_airport:
        messagebox.showwarning("Warning", "Primero debes cargar la estructura del aeropuerto.")
        return
    if not aircrafts:
        messagebox.showwarning("Warning", "No hay aviones cargados para asignar.")
        return

    exitos = 0
    fallidos = 0
    i = 0

    # Recorremos los aviones y llamamos a la funcion de asignar
    while i < len(aircrafts):
        gate_assigned = AssignGate(bcn_airport, aircrafts[i])
        if gate_assigned != "":
            exitos += 1
        else:
            fallidos += 1
        i += 1

    # Actualizamos la pantalla para ver el resultado de la asignacion
    update_gates_listbox()
    messagebox.showinfo("Asignación", f"Proceso terminado.\nPuertas asignadas: {exitos}\nSin espacios: {fallidos}.")


# ================= MAQUETACIÓN DE LA INTERFAZ GRÁFICA =================

# Contenedor principal de la aplicacion
main_container = ttk.Frame(app, padding=15)
main_container.pack(fill="both", expand=True)

# Panel izquierdo para meter los botones y entradas de texto
left_panel = ttk.Frame(main_container)
left_panel.pack(side="left", fill="y", padx=(0, 15))

# Panel derecho para meter el cuadro grande de visualizacion
right_panel = ttk.LabelFrame(main_container, text=" Vista de Datos en Memoria (Aeropuertos / Puertas) ", padding=10)
right_panel.pack(side="right", fill="both", expand=True)

# --- Elementos de la lista del panel derecho ---
scrollbar = ttk.Scrollbar(right_panel)
scrollbar.pack(side="right", fill="y")
listbox = tk.Listbox(right_panel, yscrollcommand=scrollbar.set, font=("Consolas", 10))
listbox.pack(side="left", fill="both", expand=True)
scrollbar.config(command=listbox.yview)

# --- Bloques de control del panel izquierdo ---

# Bloque 1: Carga de aeropuertos mundiales
frame_load = ttk.LabelFrame(left_panel, text=" 1. Base de Datos ", padding=10)
frame_load.pack(fill="x", pady=(0, 5))

ttk.Label(frame_load, text="Archivo:").grid(row=0, column=0, padx=5, sticky="e")
archivo_entry = ttk.Entry(frame_load, width=20)
archivo_entry.grid(row=0, column=1, padx=5)
ttk.Button(frame_load, text="Cargar", command=load_airports, style="Accent.TButton").grid(row=0, column=2, padx=5)

# Bloque 2: Añadir o quitar aeropuertos a mano
frame_edit = ttk.LabelFrame(left_panel, text=" 2. Edición Manual ", padding=10)
frame_edit.pack(fill="x", pady=5)

ttk.Label(frame_edit, text="ICAO:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
code_entry = ttk.Entry(frame_edit, width=12)
code_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")

ttk.Label(frame_edit, text="Latitud:").grid(row=1, column=0, padx=5, pady=2, sticky="e")
lat_entry = ttk.Entry(frame_edit, width=12)
lat_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")

ttk.Label(frame_edit, text="Longitud:").grid(row=2, column=0, padx=5, pady=2, sticky="e")
lon_entry = ttk.Entry(frame_edit, width=12)
lon_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")

ttk.Button(frame_edit, text="Agregar Aeropuerto", command=add_airport).grid(row=3, column=0, columnspan=2, pady=(10, 0))

# Linea vertical de separacion interna
ttk.Separator(frame_edit, orient="vertical").grid(row=0, column=2, rowspan=4, sticky="ns", padx=15)

ttk.Label(frame_edit, text="Borrar (ICAO):").grid(row=0, column=3, padx=5, sticky="w")
del_entry = ttk.Entry(frame_edit, width=12)
del_entry.grid(row=1, column=3, padx=5, pady=(0, 10))
ttk.Button(frame_edit, text="Eliminar", command=delete_airport).grid(row=2, column=3, pady=5)

# Bloque 3: Herramientas analiticas de aeropuertos
frame_utils = ttk.LabelFrame(left_panel, text=" 3. Herramientas ", padding=10)
frame_utils.pack(fill="x", pady=5)

ttk.Button(frame_utils, text="Aplicar Schengen", command=apply_schengen).grid(row=0, column=0, padx=5, pady=5,
                                                                              sticky="ew")
ttk.Button(frame_utils, text="Gráfico 2D", command=plot_data).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
ttk.Button(frame_utils, text="Exp. Google Earth", command=map_data).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

ttk.Separator(frame_utils, orient="horizontal").grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)

ttk.Label(frame_utils, text="Exportar archivo Schengen:").grid(row=2, column=0, columnspan=2, sticky="w", padx=5)
save_entry = ttk.Entry(frame_utils, width=15)
save_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5)
ttk.Button(frame_utils, text="Guardar", command=save_airports).grid(row=3, column=2, padx=5)

# Bloque 4: Seccion de analisis y graficos de aviones
frame_aircraft = ttk.LabelFrame(left_panel, text=" 4. Análisis de Vuelos (Arrivals) ", padding=10)
frame_aircraft.pack(fill="x", pady=5)

ttk.Label(frame_aircraft, text="Archivo:").grid(row=0, column=0, padx=5, sticky="e")
arrivals_entry = ttk.Entry(frame_aircraft, width=15)
arrivals_entry.grid(row=0, column=1, padx=5)
ttk.Button(frame_aircraft, text="Cargar Vuelos", command=load_arrivals_data, style="Accent.TButton").grid(row=0,
                                                                                                          column=2,
                                                                                                          padx=5)

# Bloque 5: Seccion del simulador de puertas de Barcelona
frame_LEBL = ttk.LabelFrame(left_panel, text=" 5. Estructura y puertas LEBL  ", padding=10)
frame_LEBL.pack(fill="x", pady=5)

ttk.Label(frame_LEBL, text="Estructura:").grid(row=0, column=0, padx=5, sticky="e")
structure_entry = ttk.Entry(frame_LEBL, width=15)
structure_entry.grid(row=0, column=1, padx=5)
ttk.Button(frame_LEBL, text="Cargar", command=load_airports_estructure_ui, style="Accent.TButton").grid(row=0, column=2,
                                                                                                        padx=5)

# Distribucion interna de las rejillas de botones inferiores
btn_grid = ttk.Frame(frame_aircraft)
btn_grid.grid(row=1, column=0, columnspan=3, pady=10)
btn_LEBL_grid = ttk.Frame(frame_LEBL)
btn_LEBL_grid.grid(row=1, column=0, columnspan=3, pady=10)

ttk.Button(btn_grid, text="Gráfico Llegadas", command=plot_arrivals_data).grid(row=0, column=0, padx=3, pady=3,
                                                                               sticky="ew")
ttk.Button(btn_grid, text="Aerolíneas", command=plot_airlines_data).grid(row=0, column=1, padx=3, pady=3, sticky="ew")
ttk.Button(btn_grid, text="Schengen/No", command=plot_flights_type_data).grid(row=0, column=2, padx=3, pady=3,
                                                                              sticky="ew")
ttk.Button(btn_grid, text="Mapear LEBL", command=map_flights_data).grid(row=1, column=0, padx=3, pady=3, sticky="ew")
ttk.Button(btn_grid, text="> 2000km", command=show_long_distance).grid(row=1, column=1, padx=3, pady=3, sticky="ew")
ttk.Button(btn_grid, text="Guardar TXT", command=save_flights_data).grid(row=1, column=2, padx=3, pady=3, sticky="ew")

ttk.Button(btn_LEBL_grid, text="Asignar puertas (Auto)", command=assign_gates_ui).grid(row=0, column=0, padx=5, pady=3)
ttk.Button(btn_LEBL_grid, text="Ver Ocupación", command=update_gates_listbox).grid(row=0, column=1, padx=5, pady=3)

# Abre la interfaz gráfica
app.mainloop()