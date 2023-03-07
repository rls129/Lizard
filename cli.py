#!/usr/bin/env python
from typing import List, Tuple

from vhdl_ast import parse, Tree, Token
from utils import treerecursive
from entity import get_entites, print_entities, Port
from arch import get_architecture, print_architecture, Process, Signal
from simul import simulation, run_simulation, heapq
import error

def compile(filename):
    ast: Tree = parse("vhdl.lark", filename)
    if len(error.errno) > 0:
        for err in error.errno:
            print (err.line, err.col, err.msg)
        return None

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
    # assert(len(error.errno) == 0)
    return architectures

def execute(architectures):
    run_simulation(100., architectures)
    # print()
    # testbench_itr

def main():
    a = compile("main.vhdl")
    if a is not None:
        execute(a)

if __name__ == "__main__":
    main()