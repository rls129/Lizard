from typing import List, Optional
from lark import Tree, Token
from entity import Entity, Port
from copy import deepcopy
from utils import cast_map, default_values
import error

class Signal:
    def __init__(self, n: str, vtype: str, value: str):
        self.name:str = n
        self.type: str = vtype
        self.value: str = value
        self.future_buffer: str = 'None'
        self.linked_process: List[Process] = []


class Variable:
    def __init__(self, name, vhdl_type, value) -> None:
        self.name = name
        self.type = vhdl_type
        self.value = value

class Statements:
    def __init__(self, stmts: List[Tree]):
        self.statements = stmts
        self.pc = 0
        self.stack = []

    def __getitem__(self, i):
        return self.statements[i]
    
class Process:
    def __init__(self, n: str, sts: Statements | List[Tree], signals: List[Signal], symbols: List[Variable]):
        self.name: str = n
        self.statements = sts # shotahand len == 1; longform len > 1
        self.sensitivity_list: List[Signal] = signals
        self.symbol_table = symbols

def check_valid_symbol(symbol: Token, signals: List[Signal], entity: Entity, p_symbols: List[Variable], lvalue: bool, check_direction = False, isVariableAssignment: bool | None = None):
        '''
        '''
        for s in signals:
            if s.name == symbol.value:
                if isVariableAssignment == True:
                    error.push_error(symbol.line, symbol.column, f"Can't assign to Signal {symbol.value} in a variable assignment statement")
                    return None
                return s.type

        for p in entity.ports:
            if p.name == symbol.value:
                if lvalue:
                    if isVariableAssignment == True:
                        error.push_error(symbol.line, symbol.column, f"Can't assign to Port {symbol.value} in a variable assignment statement")
                        return None
                    if p.dirn == "in" and check_direction:
                        error.push_error(symbol.line, symbol.column, f"Can't drive input Signal {symbol.value} in a process")
                        return None
                else:
                    if  p.dirn == "out" and check_direction:
                        error.push_error(symbol.line, symbol.column, f"Can't feed output Signal {symbol.value} to drive a process")
                        return None
                return p.type
        for psym in p_symbols:
            if psym.name == symbol.value:
                if isVariableAssignment == False:
                    error.push_error(symbol.line, symbol.column, f"Can't assign to Variable {symbol.value} in a signal assignment statement")
                    return None
                return psym.type
        
        error.push_error(symbol.line, symbol.column, f"Undefined Symbol {symbol.value}")
        return None

def get_compile_value(node, signals: List[Signal], entity: Entity):
    '''
    Used to calculate the value of assignments necessary to be calculated in compile time

    Binary Expression Tree
    Literal Tree
    Identifier Token

    Return: Value, Type
    '''

    value = node.children[0]
    if isinstance(value, Token):
        if value.type == "IDENTIFIER":
            for s in signals:
                if s.name == value.value:
                    return s.value, s.type
            for p in entity.ports:
                if p.name == value.value:
                    if p.dirn == "out":
                        error.push_error(value.line, value.column, "The port is not readable")
                        return None, None
                    return p.value, p.type
    if isinstance(value, Tree):
        if value.data.value == "value":
            return get_compile_value(value, signals, entity)
        if value.data.value == "literal":
            literal = value.children[0]
            return literal.value, literal.type

        if value.data.value == "binary_expression":
            v1, t1 = get_compile_value(value.children[0], signals, entity)
            v2, t2 = get_compile_value(value.children[2], signals, entity)
            
            if t1 == t2 or cast_map[t1] == cast_map[t2]:
                op = value.children[1].value
                result = evaluate(op, v1, v2, t1)
                if op == '=' or op == '/=':
                    t1 = 'bool'
                return result, t1
            else:
                cur = value
                while isinstance(cur, Tree):
                    node = node.children[0]
                error.push_error(cur.line, cur.column, f"Type Mismatch {t1} and {t2}")
                return None, None

def get_compile_type(node: Tree, signals: List[Signal], entity: Entity, p_symbols: List[Variable], lvalue: bool, check_direction = False, isVariableAssignment: bool | None = None):
        '''
        Used to extract type information of identifiers/literals for any kind of statements during compilation
        Return: Type Information
        '''
        if isinstance(node, Token):
            if node.type == "IDENTIFIER":
                return check_valid_symbol(node, signals, entity, p_symbols, lvalue, check_direction, isVariableAssignment)
                
        if isinstance(node, Tree):
            if node.data.value == "literal":
                literal = node.children[0]
                return literal.type

            if node.data.value == "binary_expression":
                t1 = get_compile_type(node.children[0], signals, entity, p_symbols, lvalue)
                t2 = get_compile_type(node.children[2], signals, entity, p_symbols, lvalue)
                
                if t1 == t2 or cast_map[t1] == cast_map[t2]:
                    op = node.children[1].value
                    if op == '=' or op == '/=':
                        return 'bool'
                    return t1
                else:
                    cur = node
                    while isinstance(cur, Tree):
                        cur = cur.children[0]
                    error.push_error(cur.line, cur.column, f"Type Mismatch {t1} and {t2}")
                    return None
            if node.data.value == "unary_expression":
                # TODO
                pass
            if node.data.value == "value":
                return get_compile_type(node.children[0], signals, entity, p_symbols, lvalue)

def get_shorthandprocess(sprocess: Tree, entity: Entity, signals: List[Signal]) -> Process:
        # print()
        pname = "shorthandprocess"
        senitivity_list = []
        statements = [] # len == 1 or 0
        symbols = [] # always none

        def get_type(node: Tree|Token, lvalue: bool):
            if lvalue:
                for s in signals:
                    if s.name == node.value:
                        return s.type
                for p in entity.ports:
                    if p.name == node.value:
                        if lvalue and p.dirn == "in":
                            error.push_error(node.line, node.column, f"cannot read from an outport {node.value}")
                            return None
                        return p.type
                error.push_error(node.line, node.column, f"no such symbol available {node.value}")
                return None
            if not lvalue:
                # node is of type value
                node = node.children[0]
                if isinstance(node, Tree):
                    if node.data.value == "binary_expression":
                        v1 = get_type(node.children[0], False)
                        v2 = get_type(node.children[2], False)
                        if v1 == None or v2 == None:
                            error.push_error(node.children[1].line, node.children[1].column, f"Type Mismatch or Bad Type {v1} {v2}")
                            return None
                        if v1 == v2 or cast_map[v1] == cast_map[v2]:
                            return v1
                        else:
                            error.push_error(node.children[1].line, node.children[1].column, f"Type Mismatch {v1} {v2}")
                            return None
                    if node.data.value == "literal":
                        return node.children[0].type
                    if node.data.value == "value":
                        return get_type(node, lvalue)
                if isinstance(node, Token):
                    if node.type == "IDENTIFIER":
                        for s in signals:
                            if s.name == node.value:
                                return s.type
                        for p in entity.ports:
                            if p.name == node.value:
                                if p.dirn == "out":
                                    error.push_error(node.line, node.column, f"cannot read from an outport {node.value}")
                                    return None
                                return p.type
                        error.push_error(node.line, node.column, f"no such symbol available {node.value}")
                        return None
        
        def get_sensitivity_list(node: Tree|Token):
            node = node.children[0] # node is of type value
            if isinstance(node, Tree):
                if node.data.value == "binary_expression":
                    v1 = get_sensitivity_list(node.children[0])
                    v2 = get_sensitivity_list(node.children[2])
                if node.data.value == "literal":
                    pass
                if node.data.value == "value":
                    get_sensitivity_list(node)
            if isinstance(node, Token):
                if node.type == "IDENTIFIER":
                    for s in signals:
                        if s.name == node.value:
                            if s not in senitivity_list:
                                senitivity_list.append(s)
                    for s in entity.ports:
                        if s.name == node.value:
                            if s not in senitivity_list:
                                senitivity_list.append(s)

        lvalue = get_type(sprocess.children[0], True)
        rvalue = get_type(sprocess.children[1], False)
        if lvalue != rvalue and cast_map[lvalue] != cast_map[rvalue]:
            error.push_error(sprocess.children[0].line, sprocess.children[0].column, f"Type Mismatch {lvalue} {rvalue}")
    
        get_sensitivity_list(sprocess.children[1])
        statements.append(deepcopy(sprocess))

        return Process(pname, statements, senitivity_list, symbols)



def get_longformprocess(lfprocess: Tree, entity: Entity, signals: List[Signal]) -> Process:
    pname = None
    sensitivity_list = []
    statements = []
    symbols = []
    for token in lfprocess.children:
        if isinstance(token, Token):
            if token.type == "IDENTIFIER":
                pname = token.value
        if isinstance(token, Tree):
            if token.data.value == "sensitivity_list":
                for symbol in token.children:
                    flag_sensitivity_list = False
                    for s in signals:
                        if s.name == symbol.value:
                            sensitivity_list.append(s)
                            flag_sensitivity_list = True
                            continue
                    for s in entity.ports:
                        if s.name == symbol.value:
                            sensitivity_list.append(s)
                            flag_sensitivity_list = True
                            continue
                    if flag_sensitivity_list:
                        continue
                    # should not reach this point
                    error.push_error(token.children[0].line, token.children[0].column, f"Use of undeclared symbol {symbol.value}")
            if token.data.value == "variables":
                name = token.children[0].value
                flag = False
                for s in signals:
                    if s.name == name:
                        flag = True
                for s in entity.ports:
                    if s.name == name:
                        flag = True

                if flag:
                    error.push_error(token.children[0].line, token.children[0].column, f"Redefination of symbol {name}")
                    continue 

                vhdl_type = token.children[1].value
                if vhdl_type not in default_values.keys():
                    error.push_error(token.children[1].line, token.children[1].column, f"Undeclared type {token.children[1].value}")
                    continue
                value = default_values[vhdl_type]
                if len(token.children) == 3:
                    value, vhdl_type2 = get_compile_value(token.children[2], signals, entity)
                    if cast_map[vhdl_type] != cast_map[vhdl_type2]:
                        error.push_error(token.children[1].line, token.children[1].column, f"Unmatched variable and value type {vhdl_type} {vhdl_type2}")
                        continue
                
                symbols.append(Variable(name, vhdl_type, value))
                
            if token.data.value == "statements":
                for statement in token.children:
                    def update_statements_type(st: Tree):
                        for iter, i_st in enumerate(st.children):
                            if (isinstance(i_st, Tree)):
                                if i_st.data.value == "statements":
                                    st.children[iter] = Statements(i_st)
                                update_statements_type(i_st)
                                
                                    
                    if isinstance(statement, Tree):
                        if parse_st(statement, signals, entity,symbols, statements) is None:
                            continue
                    push_ready_statement = deepcopy(statement.children[0]) # To avoid references and/or edits to ast 
                    # update_statements_type(push_ready_statement)
                    statements.append(push_ready_statement)
                pass

    return Process(pname, Statements(statements), sensitivity_list, symbols)  

def get_arch_processes(node, entity: Entity, signals: List[Signal]) -> List[Process]:
    # print()
    processes = []
    
    
    for child in node.children:
        if isinstance(child, Tree):
            if child.data.value == "archdefination":
                for process in child.children:
                    if process.children[0].data.value == "shorthandprocess":
                        shorthandprocess = process.children[0]
                        r = get_shorthandprocess(shorthandprocess, entity, signals)
                        if r is not None:
                            processes.append(r)
                    elif process.children[0].data.value == "longformprocess":
                        lfprocess = process.children[0]
                        r = get_longformprocess(lfprocess, entity, signals)
                        if not None:
                            processes.append(r)       
        
    return processes



def parse_sts(statements_node, signals: List[Signal], entity: Entity, symbols: List[Variable], statements: List[Tree]):
    success_flag = True
    for statement in statements_node.children:
        if parse_st(statement, signals, entity, symbols, statements) is None:
            success_flag = None
    return success_flag

def get_condition_type(condition, signals, entity, symbols, lvalue):
    if len(condition.children) == 1:
        return get_compile_type(condition.children[0], signals, entity, symbols, lvalue)
    if isinstance(condition.children[0], Tree) and condition.children[0].data.value == "value":
        t1 = get_compile_type(condition.children[0], signals, entity, symbols, lvalue)
        t2 = get_compile_type(condition.children[2], signals, entity, symbols, lvalue)
        
        if t1 == t2 or cast_map[t1] == cast_map[t2]:
            return 'bool'
        else:
            cur = condition
            while isinstance(cur, Tree):
                cur = cur.children[0]
            error.push_error(cur.line, cur.column, f"Type Mismatch {t1} and {t2}")
            return None

    for child in condition.children:
        if not isinstance(child, Tree):
            continue
        if child.data.value == "condition":
            if get_condition_type(child, signals, entity, symbols, lvalue)!='bool':
                return None
    return 'bool'

def parse_st(statement, signals: List[Signal], entity: Entity, symbols: List[Variable], statements: List[Tree]):

    if statement.children[0].data.value == "shorthandprocess":
        shprocess = statement.children[0]
        lvalue = get_compile_type(shprocess.children[0], signals, entity, symbols, True, True, False)
        rvalue = get_compile_type(shprocess.children[1], signals, entity, symbols, False, True)

        if cast_map[lvalue] != cast_map[rvalue] or lvalue == None or rvalue == None:
            cur = shprocess
            while isinstance(cur, Tree):
                cur = cur.children[0]
            unrecognized = "Unrecognized Type"
            error.push_error(cur.line, cur.column, f"Type Mismatch {lvalue if lvalue!= None else unrecognized} and {rvalue if rvalue!= None else unrecognized}")
            return None
        return True
    elif statement.children[0].data.value == "variable_assignment":
        shprocess = statement.children[0]
        lvalue = get_compile_type(shprocess.children[0], signals, entity, symbols, True, True, True)
        rvalue = get_compile_type(shprocess.children[1], signals, entity, symbols, False, True)
        if cast_map[lvalue] != cast_map[rvalue] or lvalue == None or rvalue == None:
            cur = shprocess
            while isinstance(cur, Tree):
                cur = cur.children[0]
            unrecognized = "Unrecognized Type"
            error.push_error(cur.line, cur.column, f"Type Mismatch {lvalue if lvalue!= None else unrecognized} and {rvalue if rvalue!= None else unrecognized}")
            return None
        return True
    elif statement.children[0].data.value == "wait":
        if len(statement.children[0].children) > 0:
            try:
                value = int(statement.children[0].children[0])
            except:
                error.push_error(statement.children[0].children[0].line, statement.children[0].children[0].column, f"Non-integer value for wait time")
                return None
        return True
    elif statement.children[0].data.value == "report":
        # TODO: Implement it
        return True
    elif statement.children[0].data.value == "if_statement":
        ifstatement = statement.children[0]
        condition = ifstatement.children[0]
        condition_type = get_condition_type(condition, signals, entity, symbols, False)
        if condition_type != "bool":
            cur = ifstatement
            while isinstance(cur, Tree):
                cur = cur.children[0]
            error.push_error(cur.line, cur.column, "Value inside if condition is not boolean type.")
            return None
        ifstatements = ifstatement.children[1]
        if parse_sts(ifstatements, signals, entity, symbols, statements) is None:
            return None
        for i in range(2, len(ifstatement.children)):
            child = ifstatement.children[i]
            if child.children[0].data.value == "condition":
                condition = child.children[0]
                condition_type = get_condition_type(condition, signals, entity, symbols, False)
                if condition_type != "bool":
                    cur = child
                    while isinstance(cur, Tree):
                        cur = cur.children[0]
                    error.push_error(cur.line, cur.column, "Value inside elsif condition is not boolean type.")
                    return None
            elstatements = child.children[-1]
            if parse_sts(elstatements, signals, entity, symbols, statements) is None:
                return None

        # print()
        return True
    elif statement.children[0].data.value == "while_statement":
        while_statement = statement.children[0]
        condition = while_statement.children[0]
        condition_type = get_condition_type(condition, signals, entity, symbols, False)
        if condition_type != "bool":
            cur = while_statement
            while isinstance(cur, Tree):
                cur = cur.children[0]
            error.push_error(cur.line, cur.column, "Value inside elsif condition is not boolean type.")
            return None
        statements_node = while_statement.children[1]
        if parse_sts(statements_node, signals, entity, symbols, statements) is None:
            return None
        return True
    return None