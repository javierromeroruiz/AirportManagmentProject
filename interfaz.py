import tkinter as tk
from tkinter import filedialog, messagebox
from airport import (
    AddAirport,
    Airport,
    LoadAirports,
    MapAirports,
    PlotAirports,
    RemoveAirport,
    SaveSchengenAirports,
    SetSchengen,
)

# Creamos una lista vacia para guardar los aeropuertos con los que trabajaremos
airports = []

# Inicializamos la ventana principal de la interfaz grafica y le ponemos titulo
app = tk.Tk()
app.title("Interfaz de Aeropuertos")


def update_listbox():

    # Funcion que actualiza la lista que ve el usuario en pantalla.
    # Primero borra lo que haya en el cuadro de texto y luego añade uno a uno
    # los aeropuertos actualizados con su codigo, coordenadas y si es Schengen o no.

    listbox.delete(0, tk.END)

    # Este bucle recorre toda la lista de aeropuertos para mostrarlos en la pantalla
    i = 0
    while i < len(airports):
        a = airports[i]
        schengen_status = "Schengen" if a.schengen else "No schengen"
        listbox.insert(
            tk.END,
            f"{a.code} | Lat: {a.lat} | Lon: {a.lon} | {schengen_status}",
        )
        i += 1


def load_airports():

    # Funcion que lee el archivo de texto escrito por el usuario en la casilla.
    # Llama a la funcion encargada de cargar los datos y, si todo va bien,
    # actualiza la lista de la pantalla y muestra un aviso de exito.

    global airports
    filename = archivo_entry.get()
    loaded_data = LoadAirports(filename)

    # Comprobamos si el archivo se ha podido leer y contiene aeropuertos
    if loaded_data:
        airports = loaded_data
        update_listbox()
        messagebox.showinfo("INFO", "Aeropuertos cargados")
    else:
        messagebox.showerror("ERROR", "No se han cargado aeropuertos")


def add_airport():

    # Funcion para añadir manualmente un aeropuerto rellenando las casillas.
    # Comprueba que el codigo tenga 4 letras y que las coordenadas sean numeros validos.
    # Si todo es correcto, lo guarda, limpia las casillas y actualiza la pantalla.

    code = code_entry.get().upper()

    # Intentamos transformar las coordenadas introducidas a numeros decimales
    try:
        lat = float(lat_entry.get())
        lon = float(lon_entry.get())

        # Validamos que el codigo cumpla con el formato de 4 letras de los codigos ICAO
        if len(code) == 4 and code.isalpha():
            new_airport = Airport(code, lat, lon)
            AddAirport(airports, new_airport)
            update_listbox()

            # Vaciamos las casillas de texto para poder añadir otro aeropuerto comodamente
            code_entry.delete(0, tk.END)
            lat_entry.delete(0, tk.END)
            lon_entry.delete(0, tk.END)
        else:
            messagebox.showwarning(
                "Warning", "El Codigo ICAO debe de ser 4 letras."
            )
    except ValueError:
        messagebox.showerror(
            "Error", "La latitud y la longitud deben ser numeros"
        )


def delete_airport():

    # Funcion que busca un aeropuerto por su codigo en la casilla de borrar.
    # Si lo encuentra lo elimina del sistema, y si no, avisa con una ventana
    # de error de que ese codigo no existe en nuestra lista.

    code = del_entry.get().upper()
    result = RemoveAirport(airports, code)

    # Comprobamos si la funcion de borrado ha encontrado y eliminado el aeropuerto
    if result == 0:
        update_listbox()
        del_entry.delete(0, tk.END)
    else:
        messagebox.showerror(
            "Error", "No se ha encontrado el aeropuerto en la lista"
        )


def apply_schengen():

    # Funcion que revisa de golpe todos los aeropuertos cargados en la lista.
    # Identifica cuales pertenecen al espacio Schengen y cuales no, y luego
    # actualiza la informacion en la pantalla.

    # Este bucle pasa por cada aeropuerto de la lista para calcular su estado Schengen
    i = 0
    while i < len(airports):
        SetSchengen(airports[i])
        i += 1
    update_listbox()
    messagebox.showinfo("Success", "Schengen aplicado")


def save_airports():

    # Funcion que guarda en un nuevo archivo de texto los aeropuertos de la lista.
    # Solo se guardaran aquellos que previamente hayamos marcado como Schengen.

    filename = save_entry.get()
    result = SaveSchengenAirports(airports, filename)

    # Comprobamos si el archivo se ha guardado correctamente o si la lista estaba vacia
    if result == 0:
        messagebox.showinfo(
            "Success", f"Los aeropuertos se han guardado en: {filename}"
        )
    else:
        messagebox.showerror("Error", "La lista esta vacia")


def plot_data():

    # Funcion que abre la ventana con la grafica de barras, siempre y cuando
    # tengamos algun aeropuerto guardado en la lista para mostrar.

    if airports:
        PlotAirports(airports)
    else:
        messagebox.showwarning("Warning", "No hay aeropuertos")


def map_data():

    # Funcion que abre una ventana del sistema para elegir donde queremos guardar
    # el mapa. Genera un archivo KML con los pines de colores para verlo en Google Earth.

    if airports:
        # Abrimos el asistente para elegir el nombre y destino del archivo .kml
        filepath = filedialog.asksaveasfilename(
            defaultextension=".kml",
            filetypes=[("KML Files", "*.kml"), ("All Files", "*.*")],
            title="Guardar mapa en Google Earth",
        )

        # Si el usuario ha elegido una ruta valida, guardamos el mapa alli
        if filepath:
            result = MapAirports(airports, filepath)

            # Comprobamos si el mapa se ha escrito correctamente en el ordenador
            if result == 0:
                messagebox.showinfo(
                    "Success", f"El mapa se ha guardado en:\n{filepath}"
                )
            else:
                messagebox.showerror("Error", "No se ha podido guardar el mapa")
    else:
        messagebox.showwarning("Warning", "No hay aeropuertos que guardar")


# =====================================================================
# DISEÑO Y CONFIGURACION VISUAL DE LA INTERFAZ
# =====================================================================

# Seccion superior dedicada a escribir el nombre del archivo y cargarlo
frame_load = tk.Frame(app, bg="light blue")
frame_load.pack(pady=10)

tk.Label(frame_load, text="Nombre del archivo:", bg="lightblue").grid(
    row=0, column=0, padx=8, pady=5
)
archivo_entry = tk.Entry(frame_load, width=25)
archivo_entry.grid(row=0, column=1, padx=8, pady=5)
tk.Button(frame_load, text="Cargar Aeropuertos", command=load_airports).grid(
    row=0, column=2, padx=8, pady=5
)

# Cuadro de texto grande central donde se muestran las filas de aeropuertos
listbox = tk.Listbox(app, width=70, height=12)
listbox.pack(pady=10)

# Bloque central que agrupa los campos para añadir y borrar aeropuertos manualmente
frame_edit = tk.Frame(app, bg="light blue")
frame_edit.pack(pady=15)

# Casillas para los datos del nuevo aeropuerto a agregar
tk.Label(frame_edit, text="Codigo ICAO:", bg="light blue").grid(
    row=0, column=3, padx=10, pady=5
)
code_entry = tk.Entry(frame_edit)
code_entry.grid(row=0, column=4, padx=8, pady=5)

tk.Label(frame_edit, text="Lat:", bg="light blue").grid(
    row=1, column=3, padx=10, pady=5
)
lat_entry = tk.Entry(frame_edit)
lat_entry.grid(row=1, column=4, padx=8, pady=5)

tk.Label(frame_edit, text="Lon:", bg="light blue").grid(
    row=2, column=3, padx=10, pady=5
)
lon_entry = tk.Entry(frame_edit)
lon_entry.grid(row=2, column=4, padx=8, pady=5)

tk.Button(frame_edit, text="Agregar:", command=add_airport).grid(
    row=1, column=5, padx=8, pady=5
)

# Casilla para escribir el codigo del aeropuerto que se desea borrar
tk.Label(frame_edit, text="Codigo ICAO:", bg="light blue").grid(
    row=3, column=3, padx=10, pady=7
)
del_entry = tk.Entry(frame_edit)
del_entry.grid(row=3, column=4, padx=8, pady=7)
tk.Button(frame_edit, text="Borrar", command=delete_airport).grid(
    row=3, column=5, padx=8, pady=7
)

# Seccion inferior dedicada a los botones de utilidades y exportacion de datos
frame_utils = tk.Frame(app, bg="light blue")
frame_utils.pack(pady=15)

tk.Button(frame_utils, text="Poner Schengen", command=apply_schengen).grid(
    row=0, column=0, padx=8, pady=5
)
tk.Button(frame_utils, text="Grafico de Aeropuertos", command=plot_data).grid(
    row=0, column=1, padx=8, pady=5
)
tk.Button(frame_utils, text="Mostrar en Google Earth", command=map_data).grid(
    row=0, column=2, padx=8, pady=5
)

# Casilla e indicaciones finales para guardar el resultado en el disco
tk.Label(frame_utils, text="Guardar como:").grid(row=1, column=0, padx=8, pady=10)
save_entry = tk.Entry(frame_utils)
save_entry.grid(row=1, column=2, padx=8, pady=10)
tk.Button(
    frame_utils, text="Guardar Aeropuertos Schengen", command=save_airports
).grid(row=2, column=1, padx=8, pady=10)

# Activa el bucle principal de la aplicacion para que la ventana permanezca visible
app.mainloop()

print("Test")