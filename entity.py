from lark import Tree
from typing import List
from utils import default_values, cast_map, resolution_table
import error

class Port:
    def __init__(self, name, dirn, ptype):
        self.name = name
        self.dirn = dirn
        self.type = ptype
        self.value = default_values[ptype]
        self.future_buffer = None
        self.linked_process = []

    def update_future_buffer(self, value: str):
        if self.future_buffer is None or self.future_buffer == 'None':
            self.future_buffer = value
            return
        
        if self.type == 'std_logic' or self.type == 'std_ulogic':
            self.future_buffer = resolution_table[(self.future_buffer,value)]
            return
        
        self.future_buffer = value # For every other types
        return

class Entity:
    def __init__(
        self, name: str, ports: List[Port]
    ):
        self.name = name
        self.ports = ports


def get_entites(ast: Tree) -> List[Entity]:
    entities = []
    for tokens in ast.children:
        if tokens.data.value == "entity":
            if len(tokens.children) > 2:
                if (
                    tokens.children[0].value
                    != tokens.children[-1].value
                ):
                    error.push_error(tokens.children[-1].line, tokens.children[-1].column, 
                                     f"Unmatched Closing Identifier {tokens.children[0].value}")
                    continue
            ports = get_ports(tokens)
            entity_name = tokens.children[0]

            unique = True
            for e in entities:
                if e.name == entity_name.value:
                    error.push_error(entity_name.line, entity_name.column, f"Redefination of entity {e.name}")
                    unique = False
            if unique:
                entities.append(
                    Entity(tokens.children[0].value, ports)
                )
    return entities


def get_ports(entity: Tree):
    ports: List[Port] = []
    for prop in entity.children:
        if isinstance(prop, Tree) and prop.data.value == "portdecl":
            for port in prop.children:
                assert port.data.value == "port"
                port_name = port.children[0].value
                port_direction = port.children[1].value
                port_type = port.children[2].value
                check_unique = True
                for p in ports:
                    if p.name == port_name:
                        error.push_error(port.children[0].line, port.children[0].column, f"Port with name {port_name} already exists in this context")
                        check_unique = False
                if check_unique:
                    ports.append(
                        Port(
                            port_name,
                            port_direction,
                            port_type,
                        )
                )
    return ports


def print_entities(ent: List[Entity]):
    for i in ent:
        print(f"Entity - {i.name}")
        print("\tSignals:")
        for ii in i.ports:
            print("\t\t", ii.type, ii.dirn, ii.name)
