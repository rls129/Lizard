#!/usr/bin/env python

from vhdl_ast import parse, Tree, Token
from utils import treerecursive
from entity import get_entites, print_entities
from architecture import get_architecture, print_architecture
import error

def main():
    ast: Tree = parse("vhdl.lark", "main.vhdl")
    print(ast.pretty())
    entities = get_entites(ast)
    print_entities(entities)
    print(error.errno)
    architectures = get_architecture(ast, entities)

main()