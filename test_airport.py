from airport import *
airportadd = Airport ("EGLL", 41.297445, 2.0832941)
airportremove = "BIKF"
"""SetSchengen(airport)
PrintAirport (airport)"""

filename = "Airports.txt"
filename2 = "SchengenAirports.txt"
airports_list = LoadAirports (filename)

i = 0
while i < len(airports_list):
    SetSchengen(airports_list[i])
    i += 1

SaveSchengenAirports (airports_list, filename2)
AddAirport(airports_list, airportadd)
RemoveAirport(airports_list, airportremove)

