
import tkinter as tk
from airport import LoadAirports
airports = []

app = tk.Tk()

#Funciones
#Actualizar lo que se ve en la list de la interfaz
def update_listbox():
    listbox.delete(0, tk.END)
    for airport in airports:
        listbox.insert(tk.END, f"{airport.code} {airport.lat}{airport.lon}")

def load_airports():
    global airports # Permite cargar la variable airports de fuera de la funcion sin volver a definirla
    filename = archivo_entry.get()
    airports = LoadAirports (filename)
    update_listbox()

#Definimos las características de la interfaz
app.configure(background='light blue')
app.title('Airport Project')

# Widgets para que el usuario introduzca su lista de aeropuertos
# Texto para que el usuario sepa que aqui debe escribir el nombre del archivo
#con los aeropuertos

tk.Label (app, text = "Nombre del archivo: ", bg = 'light blue').pack()

#Definimos la entrada donde el usuario escribira el nombre del archivo
archivo_entry = tk.Entry(app)
archivo_entry.pack()

#Boton para que se guarde el archivo en nuestra funcion LoadAirports
tk.Button (app, text = 'Load', command = load_airports).pack()

#Mostramos los aeropuertos en una lista
listbox = tk.Listbox(app, width = 50)
listbox.pack()

#Widgets para que introduzca code, lat, lon, para añadir un nuevo aeropuerto
code_entry = tk.Entry(app)
code_entry.pack()
lat_entry = tk.Entry(app)
lat_entry.pack()
lon_entry = tk.Entry(app)
lon_entry.pack()






app.mainloop()