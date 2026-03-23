import tkinter as tk
from airport import Airport, LoadAirports, AddAirport, RemoveAirport, SetSchengen, SaveSchengenAirports, PlotAirports, \
    MapAirports
from tkinter import messagebox, filedialog

airports = []

app = tk.Tk()


def update_listbox():
    listbox.delete(0, tk.END)
    i = 0
    while i < len(airports):
        a = airports[i]
        schengen_status = "Schengen" if a.schengen else "No schengen"
        listbox.insert(tk.END, f"{a.code} | Lat: {a.lat} | Lon: {a.lon} | {schengen_status}")
        i += 1


def load_airports():
    global airports
    filename = archivo_entry.get()
    loaded_data = LoadAirports(filename)

    if loaded_data:
        airports = loaded_data
        update_listbox()
        messagebox.showinfo("INFO", "Aeropuertos cargados")
    else:
        messagebox.showerror("ERROR", "No se han cargado aeropuertos")


def add_airport():
    code = code_entry.get().upper()
    try:
        lat = float(lat_entry.get())
        lon = float(lon_entry.get())

        if len(code) == 4:
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


frame_load = tk.Frame(app)
frame_load.pack()

tk.Label(frame_load, text="Nombre del archivo:").pack()
archivo_entry = tk.Entry(frame_load)
archivo_entry.pack()
tk.Button(frame_load, text="Cargar Aeropuertos", command=load_airports).pack()

listbox = tk.Listbox(app)
listbox.pack()

frame_edit = tk.Frame(app)
frame_edit.pack()

tk.Label(frame_edit, text="Codigo ICAO:").pack()
code_entry = tk.Entry(frame_edit)
code_entry.pack()

tk.Label(frame_edit, text="Lat:").pack()
lat_entry = tk.Entry(frame_edit)
lat_entry.pack()

tk.Label(frame_edit, text="Lon:").pack()
lon_entry = tk.Entry(frame_edit)
lon_entry.pack()

tk.Button(frame_edit, text="Agregar:", command=add_airport).pack()

tk.Label(frame_edit, text="Codigo ICAO:").pack()
del_entry = tk.Entry(frame_edit)
del_entry.pack()
tk.Button(frame_edit, text="Borrar", command=delete_airport).pack()

frame_utils = tk.Frame(app)
frame_utils.pack()

tk.Button(frame_utils, text="Poner Schengen", command=apply_schengen).pack()
tk.Button(frame_utils, text="Grafico de Aeropuertos", command=plot_data).pack()
tk.Button(frame_utils, text="Mostrar en Google Earth", command=map_data).pack()

tk.Label(frame_utils, text="Guardar como:").pack()
save_entry = tk.Entry(frame_utils)
save_entry.pack()
tk.Button(frame_utils, text="Guardar Aeropuertos Schengen", command=save_airports).pack()

app.mainloop()