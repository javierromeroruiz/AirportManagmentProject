import os
from datetime import datetime
import matplotlib.pyplot as plt
import math


class Aircraft:
    # Creamos la clase Aircraft para guardar los datos de cada avion
    # que llega (su identificador, aerolinea, aeropuerto de origen y hora de llegada)
    def __init__(self, aircraft_id, airline_company, origin_airport, time_of_landing):
        self.aircraft_id = aircraft_id
        self.airline_company = airline_company
        self.origin_airport = origin_airport
        self.time_of_landing = time_of_landing


def LoadArrivals(filename):
    # Funcion que lee el archivo de vuelos de llegada y extrae la informacion.
    # Comprueba que los datos esten en el formato correcto (longitud de textos y horas validas).
    # Al final, devuelve una lista llena con los objetos de tipo Aircraft creados.

    if not os.path.exists(filename):
        return []

    aircraft = []

    with open(filename, 'r') as file:
        line = file.readline()

        # Recorremos el archivo linea por linea saltandonos la cabecera
        while line:
            parts = line.split()
            if parts[0] != 'AIRCRAFT' and len(parts) == 4:
                if len(parts[0]) == 5 or len(parts[0]) == 6:
                    if len(parts[1]) == 4:
                        # Intentamos comprobar si la hora tiene el formato HH:MM correcto
                        try:
                            datetime.strptime(parts[2], '%H:%M')
                            if len(parts[3]) == 3:
                                # Si todo es correcto, guardamos el nuevo avion en la lista
                                aircraft.append(Aircraft(parts[0], parts[3], parts[1], parts[2]))
                        except ValueError:
                            pass

            line = file.readline()

    return aircraft


def PlotArrivals(aircraft):
    # Funcion que cuenta cuantos aviones llegan en cada hora del dia (de 0 a 23).
    # Con estos datos, dibuja y guarda un grafico de barras para ver la distribucion de los vuelos.

    i = 0
    rangos = [0] * 24

    # Recorremos todos los aviones para agruparlos segun su hora de llegada
    while i < len(aircraft):
        time = aircraft[i].time_of_landing
        hora = int(time.split(':')[0])
        rangos[hora] += 1
        i += 1

    # Creamos las etiquetas de texto para las 24 horas del dia
    horas_labels = [f"{h:02d}:00" for h in range(24)]

    # Configuramos el diseño del grafico de barras
    plt.bar(horas_labels, rangos, color='skyblue', edgecolor='navy')
    plt.xlabel('Franja Horaria')
    plt.ylabel('Cantidad de Aviones')
    plt.title('Distribución de Llegadas por Hora')
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Ajustamos el tamaño y guardamos la imagen en la carpeta output
    plt.tight_layout()
    plt.savefig('../output/arrivals_distribution.png')
    plt.show()


def SaveFlights(aircraft, filename):
    # Funcion que guarda la lista de aviones actual en un nuevo archivo de texto.
    # Si algun dato del avion falta o esta vacio, escribe un guion en su lugar.

    if not aircraft:
        return -1
    try:
        with open(filename, 'w') as file:
            file.write('AIRCRAFT ORIGIN ARRIVAL AIRLINE\n')

            # Recorremos la lista para escribir los datos linea por linea en el archivo
            i = 0
            while i < len(aircraft):
                ac = aircraft[i]

                # Comprobamos campo por campo si hay datos o si ponemos un guion por defecto
                if ac.aircraft_id:
                    aircraft_id = ac.aircraft_id
                else:
                    aircraft_id = "-"
                if ac.airline_company:
                    airline_company = ac.airline_company
                else:
                    airline_company = "-"
                if ac.origin_airport:
                    origin_airport = ac.origin_airport
                else:
                    origin_airport = "-"
                if ac.time_of_landing:
                    time_of_landing = ac.time_of_landing
                else:
                    time_of_landing = "-"

                file.write(f"{aircraft_id} {origin_airport} {time_of_landing} {airline_company}\n")
                i += 1

        return 0
    except IOError:
        return -1


def PlotAirlines(aircraft):
    # Funcion que cuenta la cantidad de aviones que tiene cada aerolinea diferente.
    # Despues, genera un grafico de barras para comparar de forma visual que compañias operan mas.

    if not aircraft:
        return -1
    airlines = {}

    # Recorremos los aviones y usamos un diccionario para ir sumando las unidades por aerolinea
    i = 0
    while i < len(aircraft):
        ac = aircraft[i]
        airline = ac.airline_company
        if airline:
            if airline in airlines:
                airlines[airline] += 1
            else:
                airlines[airline] = 1
            i += 1

    # Separamos los nombres de las aerolineas y sus totales en dos listas para el grafico
    x = list(airlines.keys())
    y = list(airlines.values())

    # Diseñamos y guardamos el grafico de barras correspondiente
    plt.bar(x, y)
    plt.xlabel('airlines')
    plt.ylabel('Cantidad de Aviones')
    plt.title('Cantidad de aviones por Airline')
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('../output/cantidad_airlines.png')
    plt.show()

    return 0


def PlotFlightsType(aircraft):
    # Funcion que clasifica las llegadas de los aviones segun si proceden de un
    # aeropuerto del espacio Schengen o de fuera, dibujando un grafico de barras apiladas.

    schengen_prefixes = [
        'LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH',
        'BI', 'LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS'
    ]
    if not aircraft:
        return -1

    count_schengen = 0
    count_no_schengen = 0

    # Recorremos la lista de aviones mirando las dos primeras letras de su aeropuerto de origen
    i = 0
    while i < len(aircraft):
        origin = aircraft[i].origin_airport
        codigo = str(origin[:2])

        # Si las letras estan en la lista predeterminada es Schengen, si no, se cuenta como No Schengen
        if codigo in schengen_prefixes:
            count_schengen += 1
        else:
            count_no_schengen += 1
        i += 1

    # Dibujamos una barra apilada colocando los No Schengen justo encima de los Schengen
    x_label = ['Origin']
    plt.bar(x_label, [count_schengen], color='blue', label='Schengen')
    plt.bar(x_label, [count_no_schengen], bottom=[count_schengen], color='red', label='No Schengen')
    plt.title('Schengen origin')
    plt.ylim(0, count_schengen + count_no_schengen + 10)
    plt.legend()
    plt.show()

    return 0


def LoadAirports(filename):
    # Funcion que lee un archivo con la base de datos de aeropuertos del mundo.
    # Transforma las coordenadas que vienen en texto a grados decimales calculando minutos y segundos.
    # Guarda el resultado en un diccionario usando el codigo de cada aeropuerto como clave.

    airports_db = {}
    if os.path.exists(filename):
        f = open(filename, 'r')
        f.readline()

        # Procesamos linea por linea calculando la latitud y longitud real
        for line in f:
            parts = line.strip().split()
            if len(parts) == 3:
                code = parts[0]
                lat = parts[1]
                lon = parts[2]

                # Descomponemos el texto de la latitud en grados, minutos y segundos
                deg_lat = int(lat[1:3])
                min_lat = int(lat[3:5])
                sec_lat = int(lat[5:7])

                lat_val = deg_lat + min_lat / 60 + sec_lat / 3600
                if lat[0] == "S":
                    lat_val = -lat_val

                # Descomponemos el texto de la longitud en grados, minutos y segundos
                deg_lon = int(lon[1:4])
                min_lon = int(lon[4:6])
                sec_lon = int(lon[6:8])

                lon_val = deg_lon + min_lon / 60 + sec_lon / 3600
                if lon[0] == "W":
                    lon_val = -lon_val

                # Añadimos las coordenadas finales calculadas al diccionario
                airports_db[code] = (lat_val, lon_val)

        f.close()
    return airports_db


def MapFlights(aircraft, airports_db):
    # Funcion que crea un archivo en formato KML para poder ver en Google Earth
    # las rutas de vuelo desde los aeropuertos de origen hasta Barcelona (LEBL).
    # Las lineas seran rojas para vuelos Schengen y azules para el resto.

    schengen_prefixes = [
        'LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH',
        'BI', 'LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS'
    ]
    if "LEBL" not in airports_db:
        return -1

    # Obtenemos las coordenadas del aeropuerto de destino (Barcelona)
    lat_dest, lon_dest = airports_db["LEBL"]

    if not os.path.exists("output"):
        os.makedirs("output")

    f = open("output/flights.kml", "w")

    # Escribimos las cabeceras del documento KML
    f.write("<?xml version='1.0' encoding='UTF-8'?>\n")
    f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
    f.write("<Document>\n")

    # Recorremos la lista de aviones para dibujar la linea de su trayectoria de viaje
    i = 0
    while i < len(aircraft):
        ac = aircraft[i]
        orig = ac.origin_airport

        # Si el aeropuerto de origen existe en nuestra base de datos, pintamos la ruta
        if orig in airports_db:
            lat_orig, lon_orig = airports_db[orig]

            # Decidimos el color de la linea dependiendo de su region Schengen
            codigo = str(orig[:2])
            if codigo in schengen_prefixes:
                color = "ffff0000"
            else:
                color = "ff0000ff"

            # Escribimos las etiquetas del trayecto con las coordenadas de origen y destino
            f.write("   <Placemark>\n")
            f.write("   <name>" + str(ac.aircraft_id) + "</name>\n")
            f.write("   <Style><LineStyle><color>" + color + "</color><width>2</width></LineStyle></Style>\n")
            f.write("   <LineString>\n")
            f.write("   <coordinates>\n")

            f.write("   " + str(lon_orig) + "," + str(lat_orig) + ",0 ")
            f.write(str(lon_dest) + "," + str(lat_dest) + ",0\n")
            f.write("   </coordinates>\n")
            f.write("   </LineString>\n")
            f.write("   </Placemark>\n")

        i = i + 1

    # Cerramos las etiquetas finales del documento
    f.write("</Document>\n")
    f.write("</kml>\n")
    f.close()

    return 0


def LongDistanceArrivals(aircraft, airports_db):
    # Funcion que calcula la distancia real entre los origenes y Barcelona usando la formula de Haversine.
    # Filtra los vuelos de mas de 2000km y calcula las toneladas totales y medias de CO2 emitidas.

    long_distance_list = []
    total_co2_kg = 0.0
    cont_flights = 0

    if "LEBL" not in airports_db:
        return long_distance_list

    lat_dest, lon_dest = airports_db["LEBL"]
    R = 6371.0  # Radio de la Tierra en kilometros

    # Recorremos los aviones para calcular las distancias matematicas en base a su posicion esferica
    i = 0
    while i < len(aircraft):
        ac = aircraft[i]
        orig = ac.origin_airport

        if orig in airports_db:
            lat_orig, lon_orig = airports_db[orig]

            # Pasamos las coordenadas de grados a radianes
            lat_rad_orig = lat_orig * math.pi / 180
            lat_rad_dest = lat_dest * math.pi / 180
            diff_lat = (lat_dest - lat_orig) * math.pi / 180
            diff_lon = (lon_dest - lon_orig) * math.pi / 180

            # Aplicamos la formula matematica para hallar la distancia de arco en la Tierra
            a = math.sin(diff_lat / 2) ** 2 + math.cos(lat_rad_orig) * math.cos(lat_rad_dest) * math.sin(
                diff_lon / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist = R * c

            # Sumamos el CO2 estimado producido en el trayecto y contamos el vuelo valido
            total_co2_kg = (18 * dist) + total_co2_kg
            cont_flights = cont_flights + 1

            # Si el trayecto supera los 2000 kilometros, guardamos el objeto en la lista especial
            if dist > 2000:
                long_distance_list.append(ac)

        i = i + 1

    # Convertimos los kilogramos de CO2 calculados a toneladas metricas finales
    total_tons = total_co2_kg / 1000

    # Calculamos la media de contaminacion dividiendo el total acumulado entre el numero de vuelos procesados
    if cont_flights > 0:
        med_tons = total_tons / cont_flights
    else:
        med_tons = 0.0

    return long_distance_list, total_tons, med_tons


# Bloque de pruebas principal para ejecutar las funciones y mostrar los resultados en la consola
if __name__ == "__main__":
    aircraft = LoadArrivals("../data/Arrivals.txt")
    airports_db = LoadAirports("../data/Airports.txt")

    PlotArrivals(aircraft)
    PlotAirlines(aircraft)
    PlotFlightsType(aircraft)