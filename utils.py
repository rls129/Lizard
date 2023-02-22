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