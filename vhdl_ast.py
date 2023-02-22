from lark import Lark, Tree, Token

def parse(grammar: str, vhdl: str) -> Tree:
    grammar = open(grammar).read()
    vhdl_parser = Lark(grammar, start="root", regex=True, propagate_positions=True)

    vhdl = open(vhdl).read().lower()
    return vhdl_parser.parse(vhdl)