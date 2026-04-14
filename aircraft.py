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





