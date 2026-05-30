import os

from airport import *

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

airportadd = Airport ("EGLL", 41.297445, 2.0832941)
airportremove = "BIKF"
"""SetSchengen(airport)
PrintAirport (airport)"""

filename = os.path.join(DATA_DIR, "Airports.txt")
filename2 = os.path.join(OUTPUT_DIR, "SchengenAirports.txt")
airports_list = LoadAirports (filename)

i = 0
while i < len(airports_list):
    SetSchengen(airports_list[i])
    i += 1

SaveSchengenAirports (airports_list, filename2)
AddAirport(airports_list, airportadd)
RemoveAirport(airports_list, airportremove)

MapAirports(airports_list, os.path.join(OUTPUT_DIR, "Mapa.kml"))
