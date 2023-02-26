#!/usr/bin/env python

from vhdl_ast import parse, Tree, Token
from utils import treerecursive
from entity import get_entites, print_entities
from arch import get_architecture, print_architecture
import error

def main():
    ast: Tree = parse("vhdl.lark", "main.vhdl")
    entities = get_entites(ast)
    # testbench_intit
    print_entities(entities)
    architectures = get_architecture(ast, entities)
    print_architecture(architectures)
    for err in error.errno:
        print (err.line, err.col, err.msg)
    print(ast.pretty())
    print()
    # testbench_itr

main()