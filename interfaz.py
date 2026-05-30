import tkinter as tk
from tkinter import messagebox, filedialog
# Importamos las funciones logicas que creamos en aircraft.py
from src.aircraft import (
    Aircraft,
    LoadArrivals,
    PlotArrivals,
    SaveFlights,
    PlotAirlines,
    PlotFlightsType,
    LoadAirports,
    MapFlights,
    LongDistanceArrivals
)


# Creamos la lista donde guardaremos todos los aviones que procesemos
aircraft_list = []
# Cargamos la base de datos de aeropuertos del mundo para tener las coordenadas listas
airports_db = LoadAirports("../data/Airports.txt")

# Configuramos la ventana principal de nuestra aplicacion de gestion de vuelos
app = tk.Tk()
app.title("Gestión de Vuelos y Aeronaves")
app.geometry("800x650")


def update_aircraft_listbox():
    # Funcion que limpia el cuadro de texto de la pantalla y lo vuelve a llenar
    # con la informacion actualizada de cada avion (ID, origen y compañia).

    listbox.delete(0, tk.END)

    # Este bucle recorre todos los aviones guardados para mostrarlos en la lista visual
    i = 0
    while i < len(aircraft_list):
        ac = aircraft_list[i]
        listbox.insert(tk.END, f"{ac.aircraft_id} | Origen: {ac.origin_airport} | Compañía: {ac.airline_company}")
        i += 1


def load_arrivals_ui():
    # Funcion que lee el nombre del archivo de llegadas escrito por el usuario.
    # Llama a la funcion de carga y, si encuentra datos, actualiza la lista de la pantalla.

    global aircraft_list
    filename = archivo_entry.get()

    # Intentamos cargar los aviones desde el archivo de texto indicado
    data = LoadArrivals(filename)
    if data:
        aircraft_list = data
        update_aircraft_listbox()
        messagebox.showinfo("Éxito", "Vuelos de llegada cargados correctamente.")
    else:
        messagebox.showerror("Error", "No se pudo cargar el archivo o está vacío.")


def save_flights_ui():
    # Funcion para guardar la lista de aviones actual en un archivo nuevo.
    # Pide al usuario un nombre para el archivo y confirma si se ha guardado bien.

    filename = save_entry.get()
    if not filename:
        messagebox.showwarning("Atención", "Escribe un nombre para el archivo de guardado.")
        return

    # Ejecutamos la funcion de guardado y comprobamos si ha funcionado
    result = SaveFlights(aircraft_list, filename)
    if result == 0:
        messagebox.showinfo("Éxito", f"Vuelos guardados en {filename}")
    else:
        messagebox.showerror("Error", "No hay vuelos para guardar.")


def show_arrivals_plot():
    # Funcion que comprueba si hay aviones cargados y, en ese caso,
    # abre la ventana con el grafico de llegadas por franja horaria.

    if aircraft_list:
        PlotArrivals(aircraft_list)
    else:
        messagebox.showwarning("Atención", "Primero debes cargar los vuelos.")


def show_airlines_plot():
    # Funcion que abre el grafico para ver que compañias aereas
    # tienen mas presencia en nuestra lista de vuelos.

    if aircraft_list:
        PlotAirlines(aircraft_list)
    else:
        messagebox.showwarning("Atención", "Primero debes cargar los vuelos.")


def show_types_plot():
    # Funcion que muestra el grafico comparativo entre vuelos procedentes
    # de aeropuertos Schengen y vuelos internacionales.

    if aircraft_list:
        PlotFlightsType(aircraft_list)
    else:
        messagebox.showwarning("Atención", "Primero debes cargar los vuelos.")


def generate_kml_ui():
    # Funcion que abre un explorador de archivos para elegir donde guardar el mapa.
    # Crea un archivo KML con las rutas de los aviones para verlo en Google Earth.

    if not aircraft_list:
        messagebox.showwarning("Atención", "No hay vuelos para mapear.")
        return

    # Abrimos la ventana para que el usuario elija nombre y destino del mapa
    filepath = filedialog.asksaveasfilename(
        defaultextension=".kml",
        filetypes=[("Archivos KML", "*.kml")],
        title="Guardar rutas en Google Earth"
    )

    if filepath:
        # Si la ruta es valida, generamos el archivo KML con las lineas de colores
        result = MapFlights(aircraft_list, airports_db)
        if result == 0:
            messagebox.showinfo("Éxito", "Mapa KML generado correctamente.")
        else:
            messagebox.showerror("Error", "Error al generar el mapa (comprueba LEBL en Airports.txt).")


def calculate_co2_ui():
    # Funcion que calcula la distancia de los vuelos y muestra el impacto ambiental.
    # Nos dice cuantos vuelos son de larga distancia y cuanta contaminacion de CO2 generan.

    if not aircraft_list:
        messagebox.showwarning("Atención", "Primero carga los vuelos.")
        return

    # Obtenemos los datos calculados de distancias y toneladas de gas emitidas
    vuelos_largos, total_co2, media_co2 = LongDistanceArrivals(aircraft_list, airports_db)

    # Mostramos los resultados finales en una ventana emergente para el usuario
    mensaje = (
        f"Vuelos de larga distancia (>2000km): {len(vuelos_largos)}\n"
        f"Contaminación total: {total_co2:.2f} toneladas de CO2\n"
        f"Media por vuelo: {media_co2:.2f} toneladas de CO2"
    )
    messagebox.showinfo("Análisis Ambiental", mensaje)


# =====================================================================
# DISEÑO VISUAL DE LA INTERFAZ (Botones, Casillas y Cuadros)
# =====================================================================

# Zona superior para cargar los archivos de vuelos
frame_top = tk.Frame(app, bg="lightgreen", pady=10)
frame_top.pack(fill="x")

tk.Label(frame_top, text="Archivo de llegadas (ej: ../data/Arrivals.txt):", bg="lightgreen").pack(side="left", padx=5)
archivo_entry = tk.Entry(frame_top, width=30)
archivo_entry.pack(side="left", padx=5)
tk.Button(frame_top, text="Cargar Vuelos", command=load_arrivals_ui).pack(side="left", padx=5)

# Lista central donde se ven los aviones cargados
listbox = tk.Listbox(app, width=80, height=15)
listbox.pack(pady=20)

# Zona de botones para graficos y analisis estadistico
frame_buttons = tk.Frame(app)
frame_buttons.pack(pady=10)

tk.Button(frame_buttons, text="Gráfico Horario", command=show_arrivals_plot, width=20).grid(row=0, column=0, padx=5,
                                                                                            pady=5)
tk.Button(frame_buttons, text="Gráfico Aerolíneas", command=show_airlines_plot, width=20).grid(row=0, column=1, padx=5,
                                                                                               pady=5)
tk.Button(frame_buttons, text="Gráfico Schengen", command=show_types_plot, width=20).grid(row=0, column=2, padx=5,
                                                                                          pady=5)

# Zona de utilidades avanzadas (Mapa e Impacto Ambiental)
frame_extra = tk.Frame(app)
frame_extra.pack(pady=10)

tk.Button(frame_extra, text="Ver en Google Earth", command=generate_kml_ui, bg="skyblue", width=30).grid(row=0,
                                                                                                         column=0,
                                                                                                         padx=5)
tk.Button(frame_extra, text="Calcular Impacto CO2", command=calculate_co2_ui, bg="orange", width=30).grid(row=0,
                                                                                                          column=1,
                                                                                                          padx=5)

# Zona inferior para guardar los datos procesados en un archivo
frame_save = tk.Frame(app, pady=20)
frame_save.pack()

tk.Label(frame_save, text="Guardar lista como:").pack(side="left", padx=5)
save_entry = tk.Entry(frame_save, width=20)
save_entry.pack(side="left", padx=5)
tk.Button(frame_save, text="Guardar Vuelos", command=save_flights_ui).pack(side="left", padx=5)

# Mantenemos la ventana abierta para que el usuario pueda interactuar
app.mainloop()