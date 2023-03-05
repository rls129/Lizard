#!/usr/bin/env python
from typing import List, Tuple

from vhdl_ast import parse, Tree, Token
from utils import treerecursive
from entity import get_entites, print_entities, Port
from arch import get_architecture, print_architecture, Process, Signal
from simul import simulation, run_simulation, heapq
import error

def main():
    ast: Tree = parse("vhdl.lark", "main.vhdl")
    entities = get_entites(ast)
    # testbench_intit
    print_entities(entities)
    print()
    architectures = get_architecture(ast, entities)
    print_architecture(architectures)
    print()
    for err in error.errno:
        print (err.line, err.col, err.msg)
    print(ast.pretty())
 
    run_simulation(100., architectures)
    print()
    # testbench_itr

main()