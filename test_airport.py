from airport import *
airportadd = Airport ("LKHK", 41.297445, 2.0832941)
airportremove = ""
"""SetSchengen(airport)
PrintAirport (airport)"""

filename = "Airports.txt"
filename2 = "SchengenAirports.txt"
airports_list = LoadAirports (filename)
RemoveAirport(airports_list, airportremove)
"""AddAirport(airports_list, airportadd)"""

i = 0
while i < len(airports_list):
    SetSchengen(airports_list[i])
    i += 1

SaveSchengenAirports (airports_list, filename2)
PlotAirports(airports_list)
MapAirports(airports_list, "Mapa.kml")

