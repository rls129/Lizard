import vcd
from typing import List, TextIO, Union
from arch import Architecture
import error

VcdWriter = None
current_time = 0
output: TextIO
variables = {}
variable_values: dict[str, Union[str, None]] = {}
values_over_time = []

def init_vcd(filename, architectures: List[Architecture]):
    global output
    global vcdWriter
    global variable_values
    output = open(filename, "w+")
    vcdWriter = vcd.VCDWriter(output, timescale="1 ns", date="today")

    for arch in architectures:
        for p in arch.entity.ports:
            try:
                typ = p.type
                if p.type == "std_logic":
                    typ = "reg"
                new_var = vcdWriter.register_var(f"{arch.name}.{arch.entity.name}", p.name, typ, 1) # 1 for the width as we havenot impled vector types
                variables[p.name] = new_var
            except vcd.VCDPhaseError as e:
                error.push_error(1,1, "Caanot Make a VCD with two signals of the same name")
        for s in arch.signals:
            try:
                new_var = vcdWriter.register_var(f"{arch.name}", s.name, 'reg', 1) # 1 for the width as we havenot impl'ed vector types
                variables[s.name] = new_var
            except vcd.VCDPhaseError as e:
                error.push_error(1,1, "Caanot Make a VCD with two signals of the same name")
    
    for v in variables.keys():
        variable_values[v] = None

    vcdWriter.flush()

def set_time(currtime: float):
    global current_time
    current_time = currtime
    if current_time != 0.0:
        output.write(f"#{current_time}\n") # because our lovely pyvcd is ass

    global variables
    global variable_values
    global values_over_time
    temp = []
    for v in variables.keys():
        temp.append(variable_values[v])
    values_over_time.append((currtime, temp))
    


def dump(name, value: str):
    global variables
    global vcdWriter
    global current_time
    global output
    var = variables[name]
    if current_time != 0.0:
        output.write(f"{value}{var.ident}\n")
    variable_values[name] = value
