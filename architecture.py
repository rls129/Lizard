from lark import Token, Tree
from typing import List
from dataclasses import dataclass
from entity import Entity
import error

class Graph:
    def __init__(self, op: str|None, children, v, t):
        self.operator: str|None = op
        self.operands: List[Graph] = children
        self.value = v
        self.type = t

class Architecture:
    def __init__(self, token: Tree, entities: List[Entity]) -> None:
        self.name = token.children[0].value
        self.entity = None
        for e in entities:
            if e.name == token.children[1].value:
                self.entity = e

        if self.entity is None:
            error.push_error(token.children[1].line, token.children[1].column, f"No entity named {token.children[1].value} found")
            return
                
        self.processes = []
        self.symbols = []
        for i in range(2,len(token.children)):
            if isinstance(token.children[i], Tree) and token.children[i].data.value == "archdefination":
                for process in token.children[i].children:
                    if process.data.value == "process":
                        if process.children[0].data.value == "shorthandprocess":
                            shorthandprocess = process.children[0]
                            lvalue = shorthandprocess.children[0].value
                            rvalue = shorthandprocess.children[1]
                            x = get_value(rvalue)
                            self.processes.append(Graph("assignemnt", [Graph(None, None, lvalue, "IDENTIFIER"), x], None, None))

                        if process.children[0].data.value == "longformprocess":
                            lfprocess = process.children[0]
                            name = lfprocess.children[0].value
                            if isinstance(i, Tree):
                                for i in range(1, len(lfprocess.children)):
                                    if i.data.value == "sensitivity_list":
                                        # make a sensitivity lsit
                                    elif i.data.value == "variables":
                                        pass
                                    elif i.data.value == "shorthandprocess":
                                        pass
                                    elif i.data.value == "variable_assignment":
                                        pass
                                    elif i.data.value == "wait":
                                        pass
                                    elif i.data.value == "report":
                                        pass
                                pass
                            print()
            if isinstance(token.children[i], Tree) and token.children[i].data.value == "archsignal":
                self.symbols.append((token.children[i].children[0].value, token.children[i].children[1].value, "signal"))
                pass
        return

def get_architecture(ast: Tree|Token, entities: List[Entity]) -> List[Architecture]:
    architectures = []
    for node in ast.children:
        if node.data.value == "architechture":
            arch = Architecture(node, entities)
            if arch.entity is not None:
                architectures.append(Architecture(node, entities))
    return architectures

def print_architecture(arch: List[Architecture]):
    pass

def get_value(node: Tree):
    node_type = node.children[0]
    v = None
    if isinstance(node_type, Token) and node_type.type == "IDENTIFIER":
        v = Graph(None, None, node_type.value, node_type.type)
    elif isinstance(node_type, Tree)  and node_type.data.value == "literal":
        literal = node_type.children[0]
        v = Graph(None, None, literal.children[0].value, literal.data.value)
    elif isinstance(node_type, Tree) and node_type.data.value == "binary_expression":
        v1 = get_value(node_type.children[0])
        v2 = get_value(node_type.children[2])
        binary_operator = node_type.children[1].value
        v = Graph(binary_operator, [v1, v2], None, "binary_expression")
    return v