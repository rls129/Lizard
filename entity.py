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
        self, name: str, ports: List[Port]
    ):
        self.name = name
        self.ports = ports


def get_entites(ast: Tree) -> List[Entity]:
    entities = []
    for tokens in ast.children:
        if tokens.data.value == "entity":
            if len(tokens.children) > 2:
                assert (
                    tokens.children[0].children[0].value
                    == tokens.children[-1].children[0].value
                )
            ports = get_ports(tokens)

            entities.append(
                Entity(tokens.children[0].children[0].value, ports)
            )
    return entities


def get_ports(entity: Tree):
    ports = []
    for prop in entity.children:
        if prop.data.value == "portdecl":
            for port in prop.children:
                assert port.data.value == "port"
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
        for ii in i.ports:
            print(ii.type, ii.dirn, ii.name)
