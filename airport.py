import os #Importamos la libreria OS

class Airport:

    # Creamos la Clase Airport que nos definiran los atributos
    # codigo, latitud, longitud y schengen). Esta clase solo requirira al
    # usuario entrar un codigo, la latitud y la longitud

    def __init__(self, code, lat, lon):
        self.code = code
        self.lat = lat
        self.lon = lon
        self.schengen = False

def IsSchengenAirport(code):

    # Devolvera True or False basado en el codigo ICAO dado por el usuario, comparandolo
    # en base a una lista predeterminada de aeropuertos Schengen. Primeramente se comprobara
    # si existe un codigo en el input del usuario, si no hay codigo devolvera
    #  que no es Schengen (False)

    if not code:
        return False

    schengen_prefixes = [
        'LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH',
        'BI', 'LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS'
    ]

    prefix = code[:2]
    return prefix in schengen_prefixes

def SetSchengen(airport):

    # Cambiara el atributo de schengen en el objeto airport basado en la funcion 'IsSchengenAirport'

    airport.schengen = IsSchengenAirport(airport.code)

def PrintAirport(airport):

    # Imprime por consola las variables dadas por el usuario una vez
    # calculado si el aerpuerto es Schengen o no

    print("Code:", airport.code)
    print("Latitude:", airport.lat)
    print("Longitude:", airport.lon)
    print("Schengen:", airport.schengen)

def LoadAirports(filename):

    # Funcion que carga una lista de codigos y coordenadas de un archivo

    if not os.path.exists(filename): # Detecta si el archivo existe dentro de la carpeta del proyecto
        return []

    airports = []

    with open(filename, 'r') as file: #Carga el archivo en question

        line = file.readline()

        # Este bucle hace que para cada linia del archivo divida la linia en 3 partes
        # (codigo, latitud, longitud). Para las latitudes y longitudes hace el calculo
        # para transformarlo a degrees. Una vez calculado agrega a la lista airports el
        # aeropuerto utilizando la clase Airports. Al final de la funcion devuelve la
        # lista airports completa


        while line:
            parts = line.split()
            if len(parts) == 3 and parts[0] != 'Code' and len(parts[0]) == 4:
                code = parts[0]
                lat_str = parts[1]
                lon_str = parts[2]

                try:
                    lat_dir = lat_str[0]
                    lat_deg = float(lat_str[1:-4])
                    lat_min = float(lat_str[-4:-2])
                    lat_sec = float(lat_str[-2:])

                    lat_dec = lat_deg + (lat_min /60) + (lat_sec / 3600)
                    if lat_dir == 'S':
                        lat_dec = -lat_dec

                    lon_dir = lon_str[0]
                    lon_deg = float(lon_str[1:-4])
                    lon_min = float(lon_str[-4:-2])
                    lon_sec = float(lon_str[-2:])

                    lon_dec = lon_deg + (lon_min / 60) + (lon_sec / 3600)
                    if lon_dir == 'S':
                        lon_dec = -lon_dec

                    airport = Airport(code, lat_deg, lon_dec)
                    airports.append(airport)

                except ValueError:
                    pass
            line = file.readline()

    return airports

def SaveSchengenAirports(airports, filename):

    if not airports:
        return -1

    try:
        with open(filename, 'w') as file:
            file.write ('CODE LAT LON')

        i = 0
        while i < len(airports):
            airport = airports[i]

            if airport.schengen:
                lat_dec = airport.lat
                if lat_dec >= 0:
                    lat_dir = "N"
                else:
                    lat_dir = "S"
                    lat_dec = -lat_dec

                lat_deg = int(lat_dec)
                lat_temp = (lat_dec-lat_deg)*60
                lat_min = int(lat_temp)
                lat_sec = int(round((lat_temp-lat_min)*60))

                str_lat_deg = str(lat_deg)
                while len(str_lat_deg) < 2:
                    str_lat_deg = '0' + str_lat_deg

                str_lat_min = str(lat_min)
                while len(str_lat_min) < 2:
                    str_lat_min = '0' + str_lat_min

                str_lat_sec = str(lat_sec)
                while len(str_lat_sec) < 2:
                    str_lat_sec = '0' + str_lat_sec

                lat_str = lat_dir + str_lat_deg + str_lat_min + str_lat_sec

                lon_dec = airport.lon
                if lon_dec >= 0:
                    lon_dir = "E"
                else:
                    lon_dir = "W"
                    lon_dec = -lon_dec

                lon_deg = int(lon_dec)
                lon_temp = (lon_dec-lon_deg)*60
                lon_min = int(lon_temp)
                lon_sec = int(round((lon_temp-lon_min)*60))

                str_lon_deg = str(lon_deg)
                while len(str_lon_deg) < 3:
                    str_lon_deg = '0' + str_lon_deg

                str_lon_min = str(lon_min)
                while len(str_lon_min) < 2:
                    str_lon_min = '0' + str_lon_min

                str_lon_sec = str(lon_sec)
                while len(str_lon_sec) < 2:
                    str_lon_sec = '0' + str_lon_sec

                lon_str = lon_dir + str_lon_deg + str_lon_min + str_lon_sec

                line = airport.code + " " + lat_str + " " + lon_str + "\n"
                file.write(line)

            i += 1

        return 0

    except IOError:
        return -1

def AddAirport(airports, airport):
     i = 0
     found = False
     while i < len(airports) and not found:
         if airports[i].code == airport.code:
             found = True
         i += 1

     if not found:
        airports.append(airport)

def RemoveAirport(airports, code):
    i = 0
    while i < len(airports):
        if airports[i].code == code:
            airports.pop(i)
            return 0
        i += 1

    return -1