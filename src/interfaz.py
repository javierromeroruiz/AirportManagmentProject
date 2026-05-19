import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os

from src.airport import Airport, LoadAirports, AddAirport, RemoveAirport, SetSchengen, SaveSchengenAirports, \
    PlotAirports, \
    MapAirports
from src.aircraft import LoadArrivals, PlotArrivals, SaveFlights, PlotAirlines, PlotFlightsType, \
    LoadAirports as LoadAirportsDB, MapFlights, LongDistanceArrivals


from src.lebl import LoadAirportStructure, GateOccupancy, AssignGate

airports = []
aircrafts = []
airports_db = {}
bcn_airport = None

app = tk.Tk()
app.title("Sistema de Gestión de Aeropuertos y Vuelos - LEBL v4")
app.geometry("750x650")

# --- SISTEMA DE PESTAÑAS PARA MEJORAR EL ESPACIO VISUAL ---
notebook = ttk.Notebook(app)
notebook.pack(pady=10, fill="both", expand=True)

tab_aeropuertos = tk.Frame(notebook, bg="light blue")
tab_vuelos = tk.Frame(notebook, bg="light blue")
tab_puertas = tk.Frame(notebook, bg="light blue")  # NUEVA PESTAÑA V4

notebook.add(tab_aeropuertos, text="Gestión Aeropuertos")
notebook.add(tab_vuelos, text="Gestión Vuelos")
notebook.add(tab_puertas, text="Gestión Puertas (LEBL)")


# =====================================================================
# PESTAÑA 1: GESTIÓN DE AEROPUERTOS (Vuestro código original organizado)
# =====================================================================

def update_listbox():
    listbox.delete(0, tk.END)
    i = 0
    while i < len(airports):
        a = airports[i]
        schengen_status = "Schengen" if a.schengen else "No schengen"
        listbox.insert(tk.END, f"{a.code} | Lat: {a.lat} | Lon: {a.lon} | {schengen_status}")
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
        filepath = filedialog.asksaveasfilename(defaultextension=".kml", filetypes=[("KML Files", "*.kml")])
        if filepath:
            result = MapAirports(airports, filepath)
            if result == 0:
                messagebox.showinfo("Success", f"El mapa se ha guardado en:\n{filepath}")
            else:
                messagebox.showerror("Error", "No se ha podido guardar el mapa")
    else:
        messagebox.showwarning("Warning", "No hay aeropuertos que guardar")


# Maquetación Pestaña Aeropuertos
frame_load = tk.Frame(tab_aeropuertos, bg="light blue")
frame_load.pack(pady=10, fill="x")
tk.Label(frame_load, text="Archivo (Airports):", bg="lightblue").grid(row=0, column=0, padx=5)
archivo_entry = tk.Entry(frame_load, width=25)
archivo_entry.insert(0, "data/Airports.txt")  # Ruta por defecto sugerida
archivo_entry.grid(row=0, column=1, padx=5)
tk.Button(frame_load, text="Cargar", command=load_airports).grid(row=0, column=2, padx=5)

listbox = tk.Listbox(tab_aeropuertos, width=80, height=8)
listbox.pack(pady=5)

frame_edit = tk.Frame(tab_aeropuertos, bg="light blue")
frame_edit.pack(pady=5, fill="x")
tk.Label(frame_edit, text="Código:", bg="light blue").grid(row=0, column=0, padx=5)
code_entry = tk.Entry(frame_edit, width=8)
code_entry.grid(row=0, column=1, padx=5)
tk.Label(frame_edit, text="Lat:", bg="light blue").grid(row=0, column=2, padx=5)
lat_entry = tk.Entry(frame_edit, width=8)
lat_entry.grid(row=0, column=3, padx=5)
tk.Label(frame_edit, text="Lon:", bg="light blue").grid(row=0, column=4, padx=5)
lon_entry = tk.Entry(frame_edit, width=8)
lon_entry.grid(row=0, column=5, padx=5)
tk.Button(frame_edit, text="Añadir", command=add_airport).grid(row=0, column=6, padx=5)

frame_del = tk.Frame(tab_aeropuertos, bg="light blue")
frame_del.pack(pady=5, fill="x")
tk.Label(frame_del, text="Borrar Código:", bg="light blue").grid(row=0, column=0, padx=5)
del_entry = tk.Entry(frame_del, width=8)
del_entry.grid(row=0, column=1, padx=5)
tk.Button(frame_del, text="Borrar", command=delete_airport).grid(row=0, column=2, padx=5)

frame_utils = tk.Frame(tab_aeropuertos, bg="light blue")
frame_utils.pack(pady=10, fill="x")
tk.Button(frame_utils, text="Poner Schengen", command=apply_schengen).grid(row=0, column=0, padx=5)
tk.Button(frame_utils, text="Gráfico Mapa", command=plot_data).grid(row=0, column=1, padx=5)
tk.Button(frame_utils, text="Exportar KML", command=map_data).grid(row=0, column=2, padx=5)
tk.Label(frame_utils, text="Guardar como:", bg="light blue").grid(row=1, column=0, pady=5)
save_entry = tk.Entry(frame_utils, width=15)
save_entry.grid(row=1, column=1, pady=5)
tk.Button(frame_utils, text="Guardar Schengen", command=save_airports).grid(row=1, column=2, pady=5)


# =====================================================================
# PESTAÑA 2: GESTIÓN DE VUELOS (Vuestro código original organizado)
# =====================================================================

def load_arrivals_data():
    global aircrafts
    filename = arrivals_entry.get()
    loaded = LoadArrivals(filename)
    if loaded:
        aircrafts = loaded
        messagebox.showinfo("INFO", f"Se han cargado {len(aircrafts)} vuelos exitosamente.")
    else:
        messagebox.showerror("ERROR", "No se han podido cargar los vuelos.")


def plot_arrivals_data():
    if aircrafts:
        PlotArrivals(aircrafts)
    else:
        messagebox.showwarning("Warning", "Primero debes cargar los vuelos.")


def plot_airlines_data():
    if aircrafts:
        PlotAirlines(aircrafts)
    else:
        messagebox.showwarning("Warning", "Primero debes cargar los vuelos.")


def plot_flights_type_data():
    if aircrafts:
        PlotFlightsType(aircrafts)
    else:
        messagebox.showwarning("Warning", "Primero debes cargar los vuelos.")


def save_flights_data():
    if aircrafts:
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if filepath:
            res = SaveFlights(aircrafts, filepath)
            if res == 0:
                messagebox.showinfo("Success", "Vuelos guardados.")
            else:
                messagebox.showerror("Error", "Problema al guardar.")
    else:
        messagebox.showwarning("Warning", "No hay vuelos para guardar.")


def map_flights_data():
    if aircrafts and airports_db:
        res = MapFlights(aircrafts, airports_db)
        if res == 0:
            messagebox.showinfo("Success", "Mapa creado en 'flights.kml'")
        else:
            messagebox.showerror("Error", "Error al crear el mapa.")
    else:
        messagebox.showwarning("Warning", "Carga vuelos y aeropuertos primero.")


def show_long_distance():
    if aircrafts and airports_db:
        especiales, total, med = LongDistanceArrivals(aircrafts, airports_db)
        messagebox.showinfo("Larga Distancia",
                            f"Vuelos > 2000km: {len(especiales)}\nTotal CO2: {total:.2f} t\nMedio: {med:.2f} t")
    else:
        messagebox.showwarning("Warning", "Carga vuelos y aeropuertos primero.")


# Maquetación Pestaña Vuelos
frame_aircraft = tk.Frame(tab_vuelos, bg="light blue")
frame_aircraft.pack(pady=10, fill="x")
tk.Label(frame_aircraft, text="Archivo Llegadas:", bg="light blue").grid(row=0, column=0, padx=5)
arrivals_entry = tk.Entry(frame_aircraft, width=25)
arrivals_entry.insert(0, "data/Arrivals.txt")  # Ruta por defecto sugerida
arrivals_entry.grid(row=0, column=1, padx=5)
tk.Button(frame_aircraft, text="Cargar Vuelos", command=load_arrivals_data).grid(row=0, column=2, padx=5)

frame_vuelos_btn = tk.Frame(tab_vuelos, bg="light blue")
frame_vuelos_btn.pack(pady=10)
tk.Button(frame_vuelos_btn, text="Gráfico Horarios", width=20, command=plot_arrivals_data).pack(pady=2)
tk.Button(frame_vuelos_btn, text="Gráfico Aerolíneas", width=20, command=plot_airlines_data).pack(pady=2)
tk.Button(frame_vuelos_btn, text="Gráfico Schengen", width=20, command=plot_flights_type_data).pack(pady=2)
tk.Button(frame_vuelos_btn, text="Guardar en TXT", width=20, command=save_flights_data).pack(pady=2)
tk.Button(frame_vuelos_btn, text="Mapa KML (LEBL)", width=20, command=map_flights_data).pack(pady=2)
tk.Button(frame_vuelos_btn, text="Consultar > 2000km", width=20, command=show_long_distance).pack(pady=2)


# =====================================================================
# PESTAÑA 3: GESTIÓN DE PUERTAS - LEBL (NUEVAS FUNCIONES V4)
# =====================================================================

def load_airport_structure_ui():
    global bcn_airport
    filename = structure_entry.get()

    # Llamamos a vuestra función de carga de la estructura
    result = LoadAirportStructure(filename)

    if result != -1 and result is not None:
        bcn_airport = result
        update_gates_display()
        messagebox.showinfo("INFO", f"Estructura de {bcn_airport.code} cargada con éxito.")
    else:
        messagebox.showerror("ERROR", "No se pudo cargar el archivo del aeropuerto.")


def update_gates_display():
    """Actualiza la lista mostrando el estado de ocupación de las puertas"""
    gates_listbox.delete(0, tk.END)
    if not bcn_airport:
        return

    # Llamamos a vuestra función GateOccupancy
    ocupacion = GateOccupancy(bcn_airport)

    i = 0
    while i < len(ocupacion):
        puerta, estado, avion = ocupacion[i]
        if estado == "occupied":
            texto = f"Puerta: {puerta} 🔴 [OCUPADA] -> Avión: {avion}"
        else:
            texto = f"Puerta: {puerta} 🟢 [LIBRE]"
        gates_listbox.insert(tk.END, texto)
        i += 1


def assign_gates_automatically():
    """Asigna puertas a todos los aviones cargados en la pestaña 2"""
    global bcn_airport, aircrafts
    if not bcn_airport:
        messagebox.showwarning("Warning", "Primero debes cargar la estructura del aeropuerto (LEBL.txt).")
        return
    if not aircrafts:
        messagebox.showwarning("Warning", "No hay aviones cargados en el sistema (ve a la pestaña Vuelos).")
        return

    exitos = 0
    fallidos = 0
    i = 0
    while i < len(aircrafts):
        res = AssignGate(bcn_airport, aircrafts[i])
        if res == 0:
            exitos += 1
        else:
            fallidos += 1
        i += 1

    update_gates_display()
    messagebox.showinfo("Asignación de Puertas",
                        f"Proceso completado.\nPuertas asignadas: {exitos}\nVuelos sin puerta (Lleno/No opera): {fallidos}")


# Maquetación Pestaña Puertas (Diseño limpio y claro)
frame_structure = tk.Frame(tab_puertas, bg="light blue")
frame_structure.pack(pady=10, fill="x")

tk.Label(frame_structure, text="Archivo Estructura (LEBL):", bg="light blue").grid(row=0, column=0, padx=5)
structure_entry = tk.Entry(frame_structure, width=25)
structure_entry.insert(0, "data/LEBL.txt")  # Ruta por defecto sugerida
structure_entry.grid(row=0, column=1, padx=5)
tk.Button(frame_structure, text="Cargar Estructura", command=load_airport_structure_ui).grid(row=0, column=2, padx=5)

# Lista para el "Interesting Addition": Estado Visual de las puertas
tk.Label(tab_puertas, text="--- MONITOR DE OCUPACIÓN DE PUERTAS EN TIEMPO REAL ---", bg="light blue",
         font=("Arial", 10, "bold")).pack(pady=5)

# Añadimos Scrollbar para navegar de forma cómoda por las múltiples puertas del aeropuerto
frame_lista = tk.Frame(tab_puertas)
frame_lista.pack(pady=5)

scrollbar = tk.Scrollbar(frame_lista, orient="vertical")
gates_listbox = tk.Listbox(frame_lista, width=80, height=14, yscrollcommand=scrollbar.set, font=("Courier", 9))
scrollbar.config(command=gates_listbox.yview)

gates_listbox.pack(side="left")
scrollbar.pack(side="right", fill="y")

# Botón clave para disparar la asignación inteligente de la V4
tk.Button(tab_puertas, text="⚡ Asignar Puertas a los Aviones Cargados", bg="navy", fg="white",
          font=("Arial", 10, "bold"), command=assign_gates_automatically).pack(pady=10)

app.mainloop()