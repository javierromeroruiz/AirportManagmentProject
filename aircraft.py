import os
from datetime import datetime
import matplotlib.pyplot as plt
import math

class Aircraft:
    def __init__(self, aircraft_id,airline_company,origin_airport,time_of_landing ):
        self.aircraft_id = aircraft_id
        self.airline_company = airline_company
        self.origin_airport = origin_airport
        self.time_of_landing = time_of_landing

def LoadArrivals (filename):
    if not os.path.exists(filename):
        return []

    aircraft = []

    with open(filename,'r') as file:
        line = file.readline()

        while line:
            parts = line.split()
            if parts[0] != 'AIRCRAFT' and len(parts) == 4:
                if len(parts[0]) == 5 or len(parts[0]) == 6:
                    if len(parts[1]) == 4:
                        try:
                            datetime.strptime(parts[2],'%H:%M')
                            if len(parts[3]) == 3:
                                aircraft.append(Aircraft(parts[0],parts[3],parts[1],parts[2]))
                        except ValueError:
                            pass

            line = file.readline()

    return aircraft


def PlotArrivals(aircraft):
    i = 0
    rangos = [0]*24
    while i < len(aircraft):
        time = aircraft[i].time_of_landing
        hora = int(time.split(':')[0])
        rangos[hora] += 1
        i += 1

    horas_labels = [f"{h:02d}:00" for h in range(24)]

    plt.bar(horas_labels, rangos, color='skyblue', edgecolor='navy')
    plt.xlabel('Franja Horaria')
    plt.ylabel('Cantidad de Aviones')
    plt.title('Distribución de Llegadas por Hora')
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)


    plt.tight_layout()
    plt.savefig('arrivals_distribution.png')
    plt.show()

def SaveFlights (aircraft, filename):
    if not aircraft:
        return -1
    try:
        with open(filename,'w') as file:
            file.write('AIRCRAFT ORIGIN ARRIVAL AIRLINE\n')

            i=0
            while i < len(aircraft):
                ac = aircraft[i]
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

                i +=1

        return 0

    except IOError:
        return -1

def PlotAirlines (aircraft):
    if not aircraft:
        return -1
    airlines = {}
    i = 0
    while i < len(aircraft):
        ac = aircraft[i]
        airline = ac.airline_company
        if airline:
            if airline in airlines:
                airlines [airline] += 1
            else:
                airlines [airline] = 1
            i+=1
    x = list(airlines.keys())
    y = list(airlines.values())

    plt.bar(x, y)
    plt.xlabel('airlines')
    plt.ylabel('Cantidad de Aviones')
    plt.title('Cantidad de aviones por Airline')
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('cantidad_airlines.png')
    plt.show()

    return 0


def PlotFlightsType (aircraft):
    schengen_prefixes = [
        'LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH',
        'BI', 'LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS'
    ]
    if not aircraft:
        return -1

    count_schengen = 0
    count_no_schengen = 0

    i = 0
    while i < len(aircraft):
        origin = aircraft[i].origin_airport
        codigo = str(origin[:2])
        if codigo in schengen_prefixes:
            count_schengen += 1
        else:
            count_no_schengen += 1
        i +=1
    x_label = ['Origin']
    plt.bar(x_label, [count_schengen], color='blue', label='Schengen')
    plt.bar(x_label, [count_no_schengen], bottom=[count_schengen], color='red', label='No Schengen')
    plt.title('Schengen origin')
    plt.ylabel = ['Count']
    plt.ylim(0, count_schengen + count_no_schengen + 10)
    plt.legend()
    plt.show()

    return 0


def LoadAirports (filename):
    airports_db = {}
    if os.path.exists(filename):
        f = open(filename, 'r')
        f.readline()
        for line in f:
            parts = line.strip().split()
            if len(parts) == 3:
                code = parts[0]
                lat = (parts[1])
                lon = (parts[2])

                deg_lat = int(lat[1:3])
                min_lat = int(lat[3:5])
                sec_lat = int(lat[5:7])

                lat_val = deg_lat + min_lat/60 + sec_lat/3600
                if lat[0] == "S":
                    lat_val = -lat_val

                deg_lon = int(lon[1:4])
                min_lon = int(lon[4:6])
                sec_lon = int(lon[6:8])

                lon_val = deg_lon + min_lon/60 + sec_lon/3600
                if lon[0] == "W":
                    lon_val = -lon_val

                airports_db[code] = (lat_val, lon_val)

        f.close()
    return airports_db


def MapFlights (aircraft, airports_db):
    schengen_prefixes = [
        'LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH',
        'BI', 'LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS'
    ]
    if "LEBL" not in airports_db:
        return -1

    lat_dest, lon_dest = airports_db["LEBL"]

    f = open("flights.kml", "w")

    f.write("<?xml version='1.0' encoding='UTF-8'?>\n")
    f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
    f.write("<Document>\n")

    i = 0
    while i < len(aircraft):
        ac = aircraft[i]
        orig = ac.origin_airport

        if orig in airports_db:
            lat_orig, lon_orig = airports_db[orig]

            codigo = str(orig[:2])
            if codigo in schengen_prefixes:
                color = "ffff0000"
            else:
                color = "ff0000ff"

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
    f.write("</Document>\n")
    f.write("</kml>\n")
    f.close()

    return 0


def LongDistanceArrivals(aircraft, airports_db):
    long_distance_list = []

    if "LEBL" not in airports_db:
        return long_distance_list

    lat_dest, lon_dest = airports_db["LEBL"]
    R = 6371.0

    i = 0
    while i < len(aircraft):
        ac = aircraft[i]
        orig = ac.origin_airport

        if orig in airports_db:
            lat_orig, lon_orig = airports_db[orig]

            lat_rad_orig = lat_orig * math.pi/180
            lat_rad_dest = lat_dest * math.pi/180
            diff_lat = (lat_dest - lat_orig) * math.pi/180
            diff_lon = (lon_dest - lon_orig) * math.pi/180

            a = math.sin(diff_lat/2)**2 + math.cos(lat_rad_orig) * math.cos(lat_rad_dest) * math.sin(diff_lon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            dist = R * c

            if dist > 2000:
                long_distance_list.append(ac)

        i = i + 1

    return long_distance_list



if __name__ == "__main__":
    aircraft = LoadArrivals("Arrivals.txt")
    airports_db = LoadAirports("Airports.txt")

    PlotArrivals(aircraft)
    PlotAirlines(aircraft)
    PlotFlightsType(aircraft)

    SaveFlights(aircraft, "salida_test.txt")
    MapFlights(aircraft, airports_db)

    especiales = LongDistanceArrivals(aircraft, airports_db)
    print("Vuelos>2000km: ", len(especiales))