import os
from datetime import datetime
import matplotlib.pyplot as plt

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

