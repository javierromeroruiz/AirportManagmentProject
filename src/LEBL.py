class BarcelonaAP:
    def __init__(self, code):
        self.code = code
        self.terminal = list[Terminal] = []

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






