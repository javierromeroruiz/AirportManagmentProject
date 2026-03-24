import tkinter as tk
from airport import Airport, LoadAirports, AddAirport, RemoveAirport, SetSchengen, SaveSchengenAirports, PlotAirports, MapAirports
from tkinter import messagebox, filedialog

airports = []

app = tk.Tk()
app.title("Interfaz de Aeropuertos")


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


frame_load = tk.Frame(app, bg="light blue")
frame_load.pack(pady=10)

tk.Label(frame_load, text="Nombre del archivo:", bg = "lightblue").grid(row=0 , column=0 , padx=8 , pady=5)

archivo_entry = tk.Entry(frame_load, width=25)
archivo_entry.grid(row=0, column=1, padx=8, pady=5)

tk.Button(frame_load, text="Cargar Aeropuertos", command=load_airports).grid(row=0, column=2, padx=8, pady=5)

listbox = tk.Listbox(app, width=70, height=12)
listbox.pack(pady=10)

frame_edit = tk.Frame(app, bg="light blue")
frame_edit.pack(pady=15)

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
frame_utils.pack(pady=15)

tk.Button(frame_utils, text="Poner Schengen", command=apply_schengen).grid(row=0, column=0, padx=8, pady=5)
tk.Button(frame_utils, text="Grafico de Aeropuertos", command=plot_data).grid(row=0, column=1, padx=8, pady=5)
tk.Button(frame_utils, text="Mostrar en Google Earth", command=map_data).grid(row=0, column=2, padx=8, pady=5)

tk.Label(frame_utils, text="Guardar como:").grid(row=1, column=0, padx=8, pady=10)
save_entry = tk.Entry(frame_utils)
save_entry.grid(row=1, column=2, padx=8, pady=10)
tk.Button(frame_utils, text="Guardar Aeropuertos Schengen", command=save_airports).grid(row=2, column=1, padx=8, pady=10)

app.mainloop()

print("Test")