from lark import Tree, Token

def treerecursive(ast: Tree[Token]|Token, indent = 0):
    if isinstance(ast, Tree):
        print("___"*indent, "Tree", ast.data.type, ast.data.value)
        for c in ast.children:
            treerecursive(c, indent+1)
    elif isinstance(ast, Token):
        print("___"*indent, "Token", ast.type, ast.value)
    else:
        print("This cannot happen")

default_values = {
            "std_logic": 'u',
            "std_ulogic": 'u',
            "integer": 0,
            "boolean": "false",
            # TODO more default values
        }

cast_map = {
    "std_ulogic": "BIT_LITERAL",
    "std_logic" : "BIT_LITERAL" ,
    "BIT_LITERAL" :  "BIT_LITERAL",
    "BVALUE": "BVALUE",
    "OVALUE": "OVALUE",
    "XVALUE": "XVALUE",
    "integer": "integer",
    "STRING" : "STRING",
    "CHARACTER_LITERAL": "CHARACTER_LITERAL",

    None: None

}