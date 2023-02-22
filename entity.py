from lark import Token, Tree
from enum import Enum
from typing import List


class Port:
    def __init__(self, name, dirn, ptype):
        self.name = name
        self.dirn = dirn
        self.type = ptype


class Entity:
    def __init__(
        self, name: str, iports: List[Port], oports: List[Port], ioports: List[Port]
    ):
        self.name = name
        self.iports = iports
        self.oports = oports
        self.ioports = ioports


def get_entites(ast: Tree) -> List[Entity]:
    entities = []
    for tokens in ast.children:
        if tokens.data.value == "entity":
            if len(tokens.children) > 2:
                assert (
                    tokens.children[0].children[0].value
                    == tokens.children[-1].children[0].value
                )
            iports = get_ports(tokens, "in")
            oports = get_ports(tokens, "out")
            ioports = get_ports(tokens, "inout")
            entities.append(
                Entity(tokens.children[0].children[0].value, iports, oports, ioports)
            )
    return entities


def get_ports(entity: Tree, typ: str):
    ports = []
    for prop in entity.children:
        if prop.data.value == "portdecl":
            for port in prop.children:
                assert port.data.value == "port"
                if port.children[1].value == typ:
                    ports.append(
                        Port(
                            port.children[0].children[0].value,
                            port.children[1].value,
                            port.children[2].value,
                        )
                    )
    return ports


def print_entities(ent: List[Entity]):
    for i in ent:
        print(i.name)
        for ii in i.iports:
            print("IPort", ii.name)
        for ii in i.oports:
            print("Oport", ii.name)
        for ii in i.ioports:
            print("IOport", ii.name)
