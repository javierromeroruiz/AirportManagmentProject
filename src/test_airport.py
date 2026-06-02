# =============================================================================
# test_airport.py — Pruebas rapidas del modulo airport.py
#
# Se ejecuta este archivo directamente para comprobar carga, Schengen y KML.
# =============================================================================

import os

from airport import *

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print("========== test_airport.py ==========")

print("\n--- Airport + SetSchengen + PrintAirport ---")
airport = Airport("LEBL", 41.297445, 2.0832941)
SetSchengen(airport)
PrintAirport(airport)

airport2 = Airport("KJFK", 40.639751, -73.778925)
SetSchengen(airport2)
PrintAirport(airport2)

print("IsSchengenAirport(LEBL):", IsSchengenAirport("LEBL"))
print("IsSchengenAirport(KJFK):", IsSchengenAirport("KJFK"))
print("IsSchengenAirport(''):", IsSchengenAirport(""))

print("\n--- LoadAirports ---")
filename = os.path.join(DATA_DIR, "Airports.txt")
airports_list = LoadAirports(filename)
print("aeropuertos cargados:", len(airports_list))

print("\n--- SetSchengen en lista ---")
i = 0
while i < len(airports_list):
    SetSchengen(airports_list[i])
    i += 1

print("\n--- SaveSchengenAirports ---")
schengen_file = os.path.join(OUTPUT_DIR, "SchengenAirports_test.txt")
res = SaveSchengenAirports(airports_list, schengen_file)
print("SaveSchengenAirports:", res)

print("\n--- AddAirport / RemoveAirport ---")
nuevo = Airport("ZZZZ", 0.0, 0.0)
AddAirport(airports_list, nuevo)
print("tras AddAirport ZZZZ:", len(airports_list))
RemoveAirport(airports_list, "ZZZZ")
print("tras RemoveAirport ZZZZ:", len(airports_list))

print("\n--- MapAirports ---")
kml_out = os.path.join(OUTPUT_DIR, "Mapa_test.kml")
res = MapAirports(airports_list, kml_out)
print("MapAirports:", res, "->", kml_out)

print("\nFin test_airport.py")
