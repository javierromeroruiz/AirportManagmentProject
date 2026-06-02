# =============================================================================
# LEBL.py — Aeropuerto de Barcelona (LEBL)
#
# Se modela el aeropuerto: terminales, areas Schengen o no, puertas de embarque
# y asignacion de puertas a vuelos segun aerolinea y origen del avion.
# =============================================================================

import os

try:
    from src.airport import IsSchengenAirport
except ImportError:
    from airport import IsSchengenAirport

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


# ===============================================================
#  CLASES DEL PROYECTO
# ===============================================================


class BarcelonaAP:
    """Aeropuerto completo: codigo ICAO (p. ej. LEBL) y lista de terminales."""

    def __init__(self, code):
        self.code = code
        self.terminal: list[Terminal] = []


class Terminal:
    """Terminal T1 o T2: areas de embarque y aerolineas que operan en ella."""

    def __init__(self, name):
        self.name = name
        self.boarding_area: list[BoardingArea] = []
        self.airlines: list = []


class BoardingArea:
    """Zona de embarque (letra A, B, M...) con bandera Schengen y sus puertas."""

    def __init__(self, name, schengen):
        self.name = name
        self.schengen = schengen
        self.gate: list[Gate] = []


class Gate:
    """Puerta de embarque: nombre, si esta ocupada y matricula del avion asignado."""

    def __init__(self, name):
        self.name = name
        self.occupancy = False
        self.aircraft_id = ""


# ===============================================================
#  FUNCIONES DEL PROYECTO
# ===============================================================


def SetGates (area, init_gate, end_gate, prefix):
    """
    Se vacia la lista de puertas del area y se crean nuevas desde init_gate hasta end_gate-1.
    Cada puerta recibe un nombre: el prefijo (ej. T1BAG) mas el numero.
    Si end_gate es menor o igual que init_gate, el rango no tiene sentido y se devuelve -1.
    Si todo va bien, se devuelve 0.
    """
    if end_gate <= init_gate:
        return -1
    area.gate = []
    i = init_gate
    while i < end_gate:
        name = str(prefix) + str(i)
        gate = Gate(name)
        area.gate.append(gate)
        i += 1
    return 0


def LoadAirlines(terminal: Terminal, t_name):
    """
    Segun el nombre de terminal (T1 o T2) se abre el archivo T1_Airlines.txt o T2_Airlines.txt.
    Cada linea aporta un codigo de aerolinea (ultima columna o ultima palabra).
    Esos codigos se guardan en terminal.airlines para saber que companias operan ahi.
    Si falta el archivo, se avisa y se devuelve -1.
    """
    filename = os.path.join(DATA_DIR, f"{t_name}_Airlines.txt")

    if not os.path.exists(filename):
        print("File not found")
        return -1

    try:
        terminal.airlines = []
        with open(filename, "r") as file:
            line = file.readline()
            while line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    icao_code = parts[-1].strip()
                    terminal.airlines.append(icao_code)
                else:
                    parts = line.split()
                    if parts:
                        terminal.airlines.append(parts[-1].strip())
                line = file.readline()
    except FileNotFoundError:
        return -1

    return 0


def LoadAirportStructure(filename):
    """
    Se lee todo Terminals.txt y se parte en palabras (tokens).
    La primera palabra es el codigo del aeropuerto (LEBL).
    Cuando aparece la palabra Terminal, se crea una terminal nueva y se cargan sus aerolineas.
    Cuando aparece Area, se lee si es Schengen o non-Schengen y el rango de puertas (Gates 1-57).
    Con SetGates se crean los objetos Gate en esa area.
    Al final se devuelve el objeto BarcelonaAP listo; -1 si no habia archivo o estaba vacio.
    """
    if not os.path.exists(filename):
        return -1

    with open(filename, "r", encoding="utf-8") as file:
        content = file.read()

    tokens = content.split()
    if not tokens:
        return -1

    icao_code = tokens[0]
    bcn = BarcelonaAP(icao_code)

    current_terminal = None
    i = 0

    while i < len(tokens):
        if tokens[i] == "Terminal" and i + 1 < len(tokens):
            t_name = tokens[i + 1]
            current_terminal = Terminal(t_name)

            LoadAirlines(current_terminal, t_name)
            bcn.terminal.append(current_terminal)

            i += 2
            continue

        if tokens[i] == "Area" and i + 1 < len(tokens):
            area_name = tokens[i + 1]
            i += 2

            is_schengen = True
            if i < len(tokens):
                if tokens[i] == "non-Schengen":
                    is_schengen = False
                    i += 1
                elif tokens[i] == "Schengen":
                    is_schengen = True
                    i += 1

            while i < len(tokens) and tokens[i] != "Gates":
                i += 1

            if i < len(tokens) and tokens[i] == "Gates":
                i += 1
                nums = []

                while i < len(tokens) and (tokens[i].isdigit() or "-" in tokens[i]):
                    if "-" in tokens[i]:
                        parts = tokens[i].split("-")
                        for p in parts:
                            if p.isdigit():
                                nums.append(int(p))
                    elif tokens[i].isdigit():
                        nums.append(int(tokens[i]))
                    i += 1

                if len(nums) >= 2:
                    init_gate = nums[0]
                    end_gate = nums[-1]
                elif len(nums) == 1:
                    init_gate = nums[0]
                    end_gate = nums[0]
                else:
                    init_gate = 1
                    end_gate = 1

                area = BoardingArea(area_name, is_schengen)

                prefix = f"{current_terminal.name}BA{area_name}G"

                SetGates(area, init_gate, end_gate + 1, prefix)

                if current_terminal:
                    current_terminal.boarding_area.append(area)
            continue

        i += 1

    return bcn


def GateOccupancy(bcn):
    """
    Se recorren todas las terminales, areas y puertas del aeropuerto en memoria.
    Por cada puerta se anade un diccionario con nombre, estado (Free u Occupied)
    y la matricula del avion si la puerta esta ocupada.
    Sirve para mostrar el estado en la interfaz o en pruebas.
    """
    gate_info = []

    for terminal in bcn.terminal:
        for area in terminal.boarding_area:
            for gate in area.gate:
                gate_info.append({
                    "name": gate.name,
                    "status": "Occupied" if gate.occupancy else "Free",
                    "aircraft_id": gate.aircraft_id
                })

    return gate_info


def IsAirlineInTerminal(terminal, name):
    """
    Se mira la lista terminal.airlines cargada desde el archivo de aerolineas.
    Si el codigo de aerolinea buscado coincide con alguno de la lista, se devuelve verdadero.
    Si el nombre esta vacio o la lista no tiene datos, se devuelve falso.
    """
    if name == "":
        return False
    if terminal.airlines == []:
        return False
    i = 0
    while i < len(terminal.airlines):
        if terminal.airlines[i] == name:
            return True
        i += 1
    return False


def SearchTerminal(bcn, name):
    """
    Se prueba cada terminal del aeropuerto con IsAirlineInTerminal.
    La primera terminal donde aparezca esa aerolinea determina la respuesta (T1, T2, etc.).
    Si no opera en ninguna, se devuelve cadena vacia.
    """
    i = 0
    while i < len(bcn.terminal):
        terminal = bcn.terminal[i]
        if IsAirlineInTerminal(terminal, name):
            return terminal.name
        i += 1
    return ""


def AssignGate(bcn, aircraft):
    """
    Paso 1: con la aerolinea del vuelo se busca en que terminal opera (SearchTerminal).
    Paso 2: con el aeropuerto de origen se decide si el vuelo es Schengen (IsSchengenAirport).
    Paso 3: en esa terminal solo se miran areas con la misma condicion Schengen.
    Paso 4: se toma la primera puerta libre (occupancy falsa), se marca ocupada
    y se guarda la matricula del avion.
    Si no hay terminal, area o puerta libre, se devuelve cadena vacia.
    """
    terminal_name = SearchTerminal(bcn, aircraft.airline_company)
    if terminal_name == "":
        return ""
    aircraft_schengen = IsSchengenAirport(aircraft.origin_airport)

    i = 0
    while i < len(bcn.terminal):
        terminal = bcn.terminal[i]
        if terminal.name == terminal_name:

            j = 0
            while j < len(terminal.boarding_area):
                area = terminal.boarding_area[j]
                if area.schengen == aircraft_schengen:
                    k = 0
                    while k < len(area.gate):
                        gate = area.gate[k]
                        if gate.occupancy == False:
                            gate.occupancy = True
                            gate.aircraft_id = aircraft.aircraft_id

                            return gate.name
                        k += 1
                j += 1
        i += 1
    return ""


# Pruebas rapidas al ejecutar este archivo directamente
if __name__ == "__main__":
    structure_path = os.path.join(DATA_DIR, "Terminals.txt")
    print("--- LoadAirportStructure ---")
    bcn = LoadAirportStructure(structure_path)
    if bcn == -1:
        print("ERROR: no se pudo cargar Terminals.txt")
    else:
        print("Aeropuerto:", bcn.code, "terminales:", len(bcn.terminal))

        print("--- GateOccupancy (todas libres al inicio) ---")
        gates = GateOccupancy(bcn)
        print("puertas totales:", len(gates))

        print("--- SearchTerminal / IsAirlineInTerminal ---")
        t_vlg = SearchTerminal(bcn, "VLG")
        print("VLG va a terminal:", t_vlg)

        print("--- SetGates prueba error ---")
        area_prueba = BoardingArea("Z", True)
        err = SetGates(area_prueba, 5, 3, "TEST")
        print("SetGates con fin<=inicio debe dar -1:", err)

        print("--- AssignGate (necesita Aircraft) ---")
        try:
            from src.aircraft import Aircraft
        except ImportError:
            from aircraft import Aircraft

        avion = Aircraft("ECMKV", "VLG", "LYBE", "10:30")
        avion.airline_company = "VLG"
        avion.origin_airport = "LYBE"
        avion.aircraft_id = "ECMKV"
        puerta = AssignGate(bcn, avion)
        print("puerta asignada:", puerta)

        print("--- GateOccupancy despues de asignar ---")
        gates2 = GateOccupancy(bcn)
        ocupadas = 0
        g = 0
        while g < len(gates2):
            if gates2[g]["status"] == "Occupied":
                ocupadas = ocupadas + 1
            g = g + 1
        print("puertas ocupadas:", ocupadas)

    print("Fin tests LEBL.py")
