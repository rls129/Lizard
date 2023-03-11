#!/usr/bin/env python

from vhdl_ast import parse, Tree
from entity import get_entites, print_entities
from arch import get_architecture, print_architecture
from simul import run_simulation, simulation
import error
import vcd_dump
import diagram

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
    if len(error.errno) > 0:
        for err in error.errno:
            print (err.line, err.col, err.msg)
        return None
    vcd_dump.init_vcd("output.vcd", architectures)

    return architectures

def execute(architectures):
    simulation.current_time = 0
    simulation.to_run_till = 0
    run_simulation(5000., architectures)
    # print()
    # testbench_itr

def main():
    a = compile("main.vhdl")
    if a is not None:
        execute(a)
        for x in a:
            diagram.draw(x)
        print()

if __name__ == "__main__":
    main()