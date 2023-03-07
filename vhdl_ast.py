from lark import Lark, Tree, Token
import error

def parse(grammar: str, vhdl: str) -> Tree:
    grammar = open(grammar).read()
    vhdl_parser = Lark(grammar, start="root", regex=True, propagate_positions=True)

    vhdl = open(vhdl).read().lower()
    try:
        return vhdl_parser.parse(vhdl)
    except Exception as e:
        error.push_error(e.line, e.column, f"{e}")