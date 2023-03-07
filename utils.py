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
    "bool" : "bool",
    "INT" : "INT",

    None: None

}

def evaluate(operation, value1, value2, type_expn):
        if type_expn == "std_logic":
            if operation == "and":
                if value1 == 'l' or value2 == 'l':
                    return 'l'
                if value1 == 'h' and value2 == 'h':
                    return 'h'
                if value1 == 'u' or value2 == 'u':
                    return 'u'
                return 'x'
            if operation == "or":
                if value1 == 'h' or value2 == 'h':
                    return 'h'
                if value2 == 'l' and value2 == 'l':
                    return 'l'
                if value2 == 'u' or value2 == 'u':
                    return 'u'
                return 'x'
            if operation == "xor":
                if value1 == 'u' or value2 == 'u':
                    return 'u'
                if value1 != value2:
                    return 'h'
                elif value1 == value2:
                    return 'l'
                return 'x'
            if operation == "nor":
                if value2 == 'h' or value2 == 'h':
                    return 'l'
                if value2 == 'l' or value2 == 'l':
                    return 'h'
                if value1 == 'u' or value2 == 'u':
                    return 'u'
                return 'x'
            if operation == "nand":
                if value1 == 'h' and value2 == 'h':
                    return 'l'
                if value1 == 'l' or value2 == 'l':
                    return 'h'
                if value1 == 'u' or value2 == 'u':
                    return 'u'
                return 'x'
        if type_expn == "std_ulogic":
            pass
        if type_expn == "BIT_LITERAL":
            pass
        if type_expn == "INTEGER":
            pass