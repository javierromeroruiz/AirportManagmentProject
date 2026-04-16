from aircraft import LoadArrivals, LoadAirports, MapFlights, PlotFlightsType

vuelos = LoadArrivals('Arrivals.txt')
db_aeropuertos = LoadAirports('Airports.txt')

resultado = MapFlights(vuelos, db_aeropuertos)

if resultado == 0:
    print("OK")
else:
    print("ERROR")

PlotFlightsType(vuelos)