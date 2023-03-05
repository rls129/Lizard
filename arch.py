# [architecture]
# 
# architecture = {
#     name: str
#     entity: Entity
#     signals: Signal
#     miscellaneous: Any
#     processes: Process
# }
# 
# Signal = {
#     name:str
#     type**: Any = type
#     value: type**
#     future_buffer: type** = None
# }
# 
# Process = {
#     name: str
#     statements: Tree[] # shotahand len == 1; longform len > 1
#     sensitivity_list: &Signal[]
# }

from lark import Tree, Token
from copy import deepcopy
from typing import List, Any, Optional, Tuple

from entity import Entity, Port
from utils import default_values, cast_map
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

    def __getitem__(self, i):
        return self.statements[i]
class Process:
    def __init__(self, n: str, sts: Statements | List[Tree], signals: List[Signal], symbols: List[Variable]):
        self.name: str = n
        self.statements = sts # shotahand len == 1; longform len > 1
        self.sensitivity_list: List[Signal] = signals
        self.symbol_table = symbols


class Architecture:
    def __init__(self, name: str, e: Entity, s: List[Signal], p: List[Process]):
        self.name: str = name
        self.entity: Entity = deepcopy(e) #Each architecture has its own copy of entity when fabricated
        self.signals: List[Signal] = s
        self.miscellaneous: List[Any] = []
        self.processes: List[Process] = p
        self.signals_changed: List[Signal | Port] = []
        self.waiting_process  : List[Tuple[Process, float]] = []  # For processes encountering waits
        self.inactive_process : List[Process] = []  # For processes with sensitivity list
        # for port in self.entity.ports:
        #     self.signals_changed.append(port)
        # for signal in self.signals:
        #     self.signals_changed.append(signal)
        # for proc in self.processes:
        #     self.waiting_process.append((proc, 0.))

def get_compile_value(node, signals: List[Signal], entity: Entity):
    '''
    Binary Expression Tree
    Literal Tree
    Identifier Token

    Return: Value, Type
    '''
    
    def evaluate(operation, value1, value2, type_expn):
        if type_expn == "std_logic":
            if operation == "and":
                if value1 == 'l' or value2 == 'l':
                    return 'l'
                if value2 == 'h' and value2 == 'h':
                    return 'h'
                if value2 == 'u' or value2 == 'u':
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
                if value1 == 'h' or value2 == 'l':
                    return 'h'
                if value1 == 'l' and value2 == 'h':
                    return 'h'
                if value1 == 'h' and value2 == 'l':
                    return 'h'
                if value1 == 'h' and value2 == 'h':
                    return 'l'
                if value1 == 'l' and value2 == 'l':
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
                
        pass
    pass

def parse_sts(statements_node, signals: List[Signal], entity: Entity, symbols: List[Variable], statements: List[Tree]):
    success_flag = True
    for statement in statements_node.children:
        if parse_st(statement, signals, entity, symbols, statements) is None:
            success_flag = None
    return success_flag

def parse_st(statement, signals: List[Signal], entity: Entity, symbols: List[Variable], statements: List[Tree]):
    def check_valid_symbol(symbol: Token, signals: List[Signal], entity: Optional[Entity], p_symbols: List[Variable], lvalue: bool, check_direction = False):
        '''
        Only used for evaluation of rvalue in shorthand process
        '''
        for s in signals:
            if s.name == symbol.value:
                return s.type
        if entity is not None:
            for p in entity.ports:
                if p.name == symbol.value:
                    if lvalue:
                        if p.dirn == "in" and check_direction:
                            error.push_error(symbol.line, symbol.column, f"Can't drive input signal {symbol.value} in a process")
                            return None
                    else:
                        if  p.dirn == "out" and check_direction:
                            error.push_error(symbol.line, symbol.column, f"Can't feed output signal {symbol.value} to drive a process")
                            return None
                    return p.type
        for psym in p_symbols:
            if psym.name == symbol.value:
                return psym.type
        
        error.push_error(symbol.line, symbol.column, f"Undefined Symbol {symbol.value}")
        return None
    def get_compile_type(node: Tree, signals: List[Signal], entity: Optional[Entity], p_symbols: List[Variable], lvalue: bool, check_direction = False):
        '''
        Only used for evaluation of values in shorthand process
        '''
        if isinstance(node, Token):
            if node.type == "IDENTIFIER":
                return check_valid_symbol(node, signals, entity, p_symbols, lvalue, check_direction)
                
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

    if statement.children[0].data.value == "shorthandprocess":
        shprocess = statement.children[0]
        lvalue = get_compile_type(shprocess.children[0], signals, entity,      [], True, True)
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
        lvalue = get_compile_type(shprocess.children[0],      [], None, symbols, True, True)
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
        pass
    return None






def get_architecture(ast: Tree, entities: List[Entity]) -> List[Architecture]:
    architectures: List[Architecture] = []
    def get_arch_name(node):
        name = node.children[0].value
        if isinstance(node.children[-1], Token) and node.children[-1].type == "IDENTIFIER":
            if node.children[-1].value != name:
                error.push_error(node.children[-1].line, node.children[-1].column, f"Unmatched Closing Identifier {name}")
        return name

    def get_arch_entity(node: Tree, entities: List[Entity]) -> Entity|None:
        entity = node.children[1]
        for e in entities:
            if e.name == entity.value:
                return e
        error.push_error(entity.line, entity.column, f"No Entity named {entity.value}")
        return None
    
    def get_arch_signal(node: Tree, entity: Entity) -> List[Signal]:
        signals: List[Signal] = []

        for child in node.children:
            if isinstance(child, Tree):
                if child.data.value == "archsignal":
                    signal = child
                    name = signal.children[0].value
                    value_type = signal.children[1].value

                    unique = True
                    for port in entity.ports:
                        if port.name == name:
                            error.push_error(signal.children[0].line, signal.children[0].column, f"Declaration with designator {name} already exists in this region.")
                            unique = False
                    
                    if not unique:
                        continue

                    if value_type not in default_values.keys():
                        error.push_error(signal.children[1].data.line, signal.children[1].data.column, f"No such type available {value_type}")
                        continue

                    default_value = default_values[value_type]
                    if len(signal.children) == 3:
                        value, type_of_expn = get_compile_value(signal.children[2], signals, entity)
                        if type_of_expn is None:
                            # Error handled already
                            continue
                        if cast_map[value_type] == cast_map[type_of_expn] or value_type == type_of_expn:
                            default_value = value
                        else:
                            if isinstance(signal.children[2], Token):
                                error.push_error(signal.children[2].line, signal.children[2].column, f"Type Mismatch {value_type} and {type_of_expn}")
                            else:
                                curr = signal.children[2]
                                while isinstance(curr, Tree):
                                    curr = curr.children[0]
                                error.push_error(curr.line, curr.column, f"Expression was not evaluated")
                    
                    signals.append(Signal(name, value_type, default_value))
        return signals


    def get_arch_processes(node, entity: Entity, signals: List[Signal]) -> List[Process]:
        # print()
        processes = []
        
        def get_shorthandprocess(sprocess: Tree) -> Process:
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
                            update_statements_type(push_ready_statement)
                            statements.append(push_ready_statement)
                        pass

            return Process(pname, Statements(statements), sensitivity_list, symbols)  

        for child in node.children:
            if isinstance(child, Tree):
                if child.data.value == "archdefination":
                    for process in child.children:
                        if process.children[0].data.value == "shorthandprocess":
                            shorthandprocess = process.children[0]
                            r = get_shorthandprocess(shorthandprocess)
                            if r is not None:
                                processes.append(r)
                        elif process.children[0].data.value == "longformprocess":
                            lfprocess = process.children[0]
                            r = get_longformprocess(lfprocess, entity, signals)
                            if not None:
                                processes.append(r)       
            
        return processes


    for node in ast.children:
        if node.data.value == "architechture":
            name      = get_arch_name(node)
            entity    = get_arch_entity(node, entities)
            
            # Handle name errors
            # 1. No such entity exists
            # 2. check (name, entity) pair is unique
            if entity is None:
                continue
            for arch in architectures:
                if (name, entity.name) == (arch.name, arch.entity.name):
                    error.push_error(node.children[0].line, node.children[0].column, f"Redefination of a Entity-Architecture Pair {(name, entity.name)}")
                    continue

            signals   = get_arch_signal(node, entity)            
            
            processes = get_arch_processes(node, entity, signals)
            for proc in processes:
                for sl in proc.sensitivity_list:
                    sl.linked_process.append(proc)
            architectures.append(Architecture(name, entity, signals, processes))

    return architectures

def print_architecture(archs: List[Architecture]):
    for arch in archs:
        print(f"Architecture - {arch.name}")
        print(f"\tEntity - {arch.entity.name}")
        print("\tSignals")
        for s in arch.signals:
            print(f"\t\t{s.name} {s.type}")
        print("\tProcesses")
        for p in arch.processes:
            print(f"\t\t{p.name}:", end="")
            print(f" Sensitivity List {[n.name for n in p.sensitivity_list]}")
