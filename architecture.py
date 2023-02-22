from lark import Token, Tree
from typing import List

class Architecture:
    def __init__(self, token: Tree) -> None:
        self.name = token.children[0].children[0].value
        self.entity = token.children[1].children[0].value
        self.processes = []
        
        for i in range(2,len(token.children)):
            if token.children[i].data.value == "archdefination":
                for process in token.children[i].children:
                    if process.data.value == "process":
                        for p in process.children:
                            if p.data.value == "shorthandprocess":
                                print(p.children[0].children[0].value)
                                if p.children[1].children[0].data.value == "identifier":
                                    print(p.children[1].children[0].children[0].value)
                                elif p.children[1].children[0].data.value == "literal":
                                    print(p.children[1].children[0].children[0].value)
                                elif p.children[1].children[0].data.value == "binary_expression":
                                    print("Parse Binary Expn")
                                

        pass

def get_architecture(ast: Tree|Token) -> List[Architecture]:
    architectures = []
    for i in ast.children:
        if i.data.value == "architechture":
            architectures.append(Architecture(i))
    return architectures

def print_architecture(arch: Architecture):
    pass