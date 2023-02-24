from lark import Token, Tree
from typing import List
from dataclasses import dataclass
from entity import Entity
import error

class Graph:
    def __init__(self, op: str|None, children, v, t):
        self.operator: str|None = op
        self.operands: List[Graph] = children
        self.value = v
        self.type = t

class Process:
    def __init__(self, sensitivity_list:List[str], variables:List, statements:Tree):
        self.sensitivity_list = sensitivity_list
        self.variables = variables[:]
        self.statements = statements


class Architecture:
    def __init__(self, token: Tree, entities: List[Entity]) -> None:
        self.name = token.children[0].value
        self.entity = None
        for e in entities:
            if e.name == token.children[1].value:
                self.entity = e

        if self.entity is None:
            error.push_error(token.children[1].line, token.children[1].column, f"No entity named {token.children[1].value} found")
            return
                
        if isinstance(token.children[-1], Token) and token.children[-1].type == "IDENTIFIER":
            if token.children[-1].value != self.name:
                error.push_error(token.children[-1].line, token.children[-1].column, f"Unmatched Closing Identifier {self.name}")
                self.entity = None #Temporary fix
                return #Probably need changing
                
        self.processes = []
        self.symbols = [] # format: tuple of (name, type, vhdl_type, value) type: variable, signal
        self.variables = [] # ahile execute gariraheko process ko variables, reinitialize every time process executes
        for i in range(2,len(token.children)):
            if isinstance(token.children[i], Tree) and token.children[i].data.value == "archdefination":
                for process in token.children[i].children:
                    if process.data.value == "process":
                        if process.children[0].data.value == "shorthandprocess":
                            shorthandprocess = process.children[0]
                            self.execute_shorthandprocess(shorthandprocess)


                        if process.children[0].data.value == "longformprocess":
                            lfprocess = process.children[0]
                            self.execute_longformprocess(lfprocess)
                            
            if isinstance(token.children[i], Tree) and token.children[i].data.value == "archsignal":
                if len(token.children[i].children) == 2:
                    self.symbols.append((token.children[i].children[0].value, token.children[i].children[1].value, "signal", None))
                if len(token.children[i].children) == 3:
                    self.symbols.append((token.children[i].children[0].value, token.children[i].children[1].value, "signal", token.children[i].children[2].value))
                pass
        return

    def execute_longformprocess(self, lfprocess: Tree):
        slist = []
        stnode = lfprocess.children[-1]
        if isinstance(lfprocess.children[0], Token) and lfprocess.children[0].type == "IDENTIFIER":
            name = lfprocess.children[0].value
            for i in lfprocess.children:
                if isinstance(i, Tree):
                    if i.data.value == "sensitivity_list":
                        slist = self.execute_sensitivity_list(i)

                    elif i.data.value == "variables":
                        self.variables = []
                        self.execute_variable_assignment(i)

                    elif i.data.value == "statements":
                        self.executeStatements(i)
                        pass
            pass
            print()
        p = Process(slist, self.variables, stnode)
        self.processes.append(p)
        pass

    def execute_sensitivity_list(self, sslist: Tree):
        slist = []
        for i in sslist.children:
            # append to process sensitivity list
            # 
            pass
        return slist

    def execute_variable_assignment(self, varassign: Tree):
        
        # format: tuple of (name, type, vhdl_type, value) vhdl_type: variable, signal type: std_logic etc
        if len(varassign.children) == 2:
            self.variables.append((varassign.children[0].value, varassign.children[1].value, "variable", None))
        if len(varassign.children) == 3:
            # NOTE FIXME
            # this has a bug
            self.variables.append((varassign.children[0].value, varassign.children[1].value, "variable", get_value(varassign.children[2])))
        return

    def execute_shorthandprocess(self, shorthandprocess: Tree):
        lvalue = shorthandprocess.children[0].value
        rvalue = shorthandprocess.children[1]
        x = get_value(rvalue)
        self.processes.append(Graph("assignment", [Graph(None, None, lvalue, "IDENTIFIER"), x], None, None))

    def executeStatements(self, node: Tree):
        for statement in node.children:
            self.executeStatement(statement)
    
    def executeStatement(self, node:Tree):
        statement = node.children[0]
        if isinstance(statement, Tree): # sanity check
            if statement.data.value == "if_statement":
                condition = statement.children[0]
                if(self.evaluateCondition(condition)):
                    self.executeStatements(statement.children[1])
                else:
                    for i in range(2, len(statement.children)):
                        child = statement.children[i]
                        if child.data.value == "elsif_statement":
                            childcondition = child.children[0]
                            if self.evaluateCondition(childcondition):
                                self.executeStatements(child.children[1])
                                break
                        if child.data.value == "else_statement":
                            self.executeStatements(child.children[0])
                
            if statement.data.value == "while_statement":
                condition = statement.children[0]
                while(self.evaluateCondition(condition)):
                    self.executeStatements(statement.children[1])

            if statement.data.value == "shorthandprocess":
                self.execute_shorthandprocess(statement)
                
            if statement.data.value == "variable_assignment":
                pass

            if statement.data.value == "wait":
                pass

            if statement.data.value == "report":
                pass

    def evaluateCondition(self, condition: Tree) -> bool:
        if isinstance(condition.children[0], Token) and condition.children[0].value == "(":
            return self.evaluateCondition(condition.children[1])
        elif isinstance(condition.children[1], Token) and condition.children[1].value == "and":
            assert(isinstance(condition.children[0], Tree) and isinstance(condition.children[2], Tree))
            return self.evaluateCondition(condition.children[0]) and self.evaluateCondition(condition.children[2])
        elif isinstance(condition.children[1], Token) and condition.children[1].value == "or":
            assert(isinstance(condition.children[0], Tree) and isinstance(condition.children[2], Tree))
            return self.evaluateCondition(condition.children[0]) or self.evaluateCondition(condition.children[2])
        elif isinstance(condition.children[0], Token) and condition.children[0].value == "not":
            assert(isinstance(condition.children[1], Tree))
            return not self.evaluateCondition(condition.children[1])
        assert(isinstance(condition.children[0], Tree) and isinstance(condition.children[2], Tree) and isinstance(condition.children[1], Token))
        lvalue = self.evaluateValue(get_value(condition.children[0]))
        rvalue = self.evaluateValue(get_value(condition.children[2]))
        if condition.children[1].value == "=":
            if lvalue == rvalue:
                return True
            return False
        elif condition.children[1].value == "/=":
            if lvalue != rvalue:
                return True
            return False
        return False
        
        
    def evaluateValue(self, value:Graph):
        pass


def get_architecture(ast: Tree|Token, entities: List[Entity]) -> List[Architecture]:
    architectures = []
    for node in ast.children:
        if node.data.value == "architechture":
            arch = Architecture(node, entities)
            if arch.entity is not None:
                architectures.append(Architecture(node, entities))
    return architectures

def print_architecture(arch: List[Architecture]):
    pass

def get_value(node: Tree) -> Graph:
    node_type = node.children[0]
    v = Graph(None, None, None, None)
    if isinstance(node_type, Token) and node_type.type == "IDENTIFIER":
        v = Graph(None, None, node_type.value, node_type.type)
    elif isinstance(node_type, Tree)  and node_type.data.value == "literal":
        literal = node_type.children[0]
        v = Graph(None, None, literal.children[0].value, literal.data.value)
    elif isinstance(node_type, Tree) and node_type.data.value == "binary_expression":
        v1 = get_value(node_type.children[0])
        v2 = get_value(node_type.children[2])
        binary_operator = node_type.children[1].value
        v = Graph(binary_operator, [v1, v2], None, "binary_expression")
    return v