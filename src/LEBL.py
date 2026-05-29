import os

from airport import IsSchengenAirport


class BarcelonaAP:
    def __init__(self, code):
        self.code = code
        self.terminal: list[Terminal] = []

class Terminal:
    def __init__(self, name):
        self.name = name
        self.boarding_area: list[BoardingArea] = []
        self.airlines: list = []

class BoardingArea:
    def __init__(self, name, schengen):
        self.name = name
        self.schengen = schengen
        self.gate: list[Gate] = []

class Gate:
    def __init__(self, name):
        self.name = name
        self.occupancy = False
        self.aircraft_id = ""

def SetGates (area, init_gate, end_gate, prefix):
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

def LoadAirlines (terminal: Terminal, t_name):

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filename = os.path.join(BASE_DIR, "data", f"{t_name}_Airlines.txt")

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
                            if p.isdigit(): nums.append(int(p))
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

def IsAirlineInTerminal (terminal,name):
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

def SearchTerminal (bcn,name):
    i = 0
    while i< len(bcn.terminal):
        terminal = bcn.terminal[i]
        if IsAirlineInTerminal(terminal,name):
            return terminal.name
        i += 1
    return ""

def AssignGate (bcn, aircraft):
    terminal_name = SearchTerminal(bcn,aircraft.airline_company)
    if terminal_name == "":
        return ""
    aircraft_schengen = IsSchengenAirport(aircraft.origin_airport)

    i = 0
    while i < len(bcn.terminal):
        terminal = bcn.terminal[i]
        if terminal.name == terminal_name:

            j= 0
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
                        k +=1
                j +=1
        i+=1
    return ""




