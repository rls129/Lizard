from vhdl_ast import parse, Tree, Token
from utils import treerecursive
from entity import get_entites, print_entities
from architecture import get_architecture, print_architecture

def main():
    ast: Tree = parse("vhdl.lark", "main.vhdl")
    print(ast.pretty())
    entities = get_entites(ast)
    print_entities(entities)
    architectures = get_architecture(ast)
    # print_architecture(architectures)

main()