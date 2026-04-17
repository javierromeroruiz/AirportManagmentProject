import tkinter as tk
from tkinter import messagebox, filedialog

from airport import Airport, LoadAirports, AddAirport, RemoveAirport, SetSchengen, SaveSchengenAirports, PlotAirports, \
    MapAirports

from aircraft import LoadArrivals, PlotArrivals, SaveFlights, PlotAirlines, PlotFlightsType, \
    LoadAirports as LoadAirportsDB, MapFlights, LongDistanceArrivals

airports = []
aircrafts = []
airports_db = {}

app = tk.Tk()
app.title("Interfaz de Aeropuertos y Vuelos")


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


frame_load = tk.Frame(app, bg="light blue")
frame_load.pack(pady=10, fill="x")

tk.Label(frame_load, text="Nombre del archivo (Airports):", bg="lightblue").grid(row=0, column=0, padx=8, pady=5)
archivo_entry = tk.Entry(frame_load, width=25)
archivo_entry.grid(row=0, column=1, padx=8, pady=5)
tk.Button(frame_load, text="Cargar Aeropuertos", command=load_airports).grid(row=0, column=2, padx=8, pady=5)

listbox = tk.Listbox(app, width=70, height=8)
listbox.pack(pady=5)

frame_edit = tk.Frame(app, bg="light blue")
frame_edit.pack(pady=10, fill="x")

tk.Label(frame_edit, text="Codigo ICAO:", bg="light blue").grid(row=0, column=3, padx=10, pady=5)
code_entry = tk.Entry(frame_edit)
code_entry.grid(row=0, column=4, padx=8, pady=5)

tk.Label(frame_edit, text="Lat:", bg="light blue").grid(row=1, column=3, padx=10, pady=5)
lat_entry = tk.Entry(frame_edit)
lat_entry.grid(row=1, column=4, padx=8, pady=5)

tk.Label(frame_edit, text="Lon:", bg="light blue").grid(row=2, column=3, padx=10, pady=5)
lon_entry = tk.Entry(frame_edit)
lon_entry.grid(row=2, column=4, padx=8, pady=5)

tk.Button(frame_edit, text="Agregar:", command=add_airport).grid(row=1, column=5, padx=8, pady=5)

tk.Label(frame_edit, text="Codigo ICAO:", bg="light blue").grid(row=3, column=3, padx=10, pady=7)
del_entry = tk.Entry(frame_edit)
del_entry.grid(row=3, column=4, padx=8, pady=7)
tk.Button(frame_edit, text="Borrar", command=delete_airport).grid(row=3, column=5, padx=8, pady=7)

frame_utils = tk.Frame(app, bg="light blue")
frame_utils.pack(pady=10, fill="x")

tk.Button(frame_utils, text="Poner Schengen", command=apply_schengen).grid(row=0, column=0, padx=8, pady=5)
tk.Button(frame_utils, text="Grafico de Aeropuertos", command=plot_data).grid(row=0, column=1, padx=8, pady=5)
tk.Button(frame_utils, text="Mostrar en Google Earth", command=map_data).grid(row=0, column=2, padx=8, pady=5)

tk.Label(frame_utils, text="Guardar como:", bg="light blue").grid(row=1, column=0, padx=8, pady=10)
save_entry = tk.Entry(frame_utils)
save_entry.grid(row=1, column=1, padx=8, pady=10)
tk.Button(frame_utils, text="Guardar Aeropuertos Schengen", command=save_airports).grid(row=1, column=2, padx=8,
                                                                                        pady=10)

frame_aircraft = tk.Frame(app, bg="light blue")
frame_aircraft.pack(pady=10, fill="x")



tk.Label(frame_aircraft, text="Archivo Llegadas (Arrivals):", bg="light blue").grid(row=1, column=0, padx=8, pady=5,
                                                                                     sticky="e")
arrivals_entry = tk.Entry(frame_aircraft, width=20)
arrivals_entry.grid(row=1, column=1, padx=8, pady=5)
tk.Button(frame_aircraft, text="Cargar Vuelos", command=load_arrivals_data).grid(row=1, column=2, padx=8, pady=5,
                                                                                 sticky="w")

tk.Button(frame_aircraft, text="Gráfico Llegadas", command=plot_arrivals_data).grid(row=2, column=0, padx=8, pady=5)
tk.Button(frame_aircraft, text="Gráfico Aerolíneas", command=plot_airlines_data).grid(row=2, column=1, padx=8, pady=5)
tk.Button(frame_aircraft, text="Gráfico Schengen/No", command=plot_flights_type_data).grid(row=2, column=2, padx=8,
                                                                                           pady=5)

tk.Button(frame_aircraft, text="Guardar Vuelos a TXT", command=save_flights_data).grid(row=3, column=0, padx=8, pady=10)
tk.Button(frame_aircraft, text="Mapear Vuelos a LEBL", command=map_flights_data).grid(row=3, column=1, padx=8, pady=10)
tk.Button(frame_aircraft, text="Consultar Vuelos > 2000km", command=show_long_distance).grid(row=3, column=2, padx=8,
                                                                                             pady=10)

app.mainloop()