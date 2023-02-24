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

from entity import Entity
from lark import Tree, Token
from typing import List, Any
from utils import default_values, cast_map
import error

class Signal:
    def __init__(self, n: str, vtype: str, value: str):
        self.name:str = n
        self.type: str = vtype
        self.value: str = value # TODO: for first iteration, set future value instead of this?
        self.future_buffer: str = 'None'


class Variable:
    def __init__(self, name, vhdl_type, value) -> None:
        self.name = name
        self.type = vhdl_type
        self.value = value

class Process:
    def __init__(self, n: str, nodes: List[Tree], signals: List[Signal], symbols: List[Variable]):
        self.name: str = n
        self.statements: List[Tree] = nodes # shotahand len == 1; longform len > 1
        self.sensitivity_list: List[Signal] = signals
        self.symbol_table = symbols


class Architecture:
    def __init__(self, name: str, e: Entity, s: List[Signal], p: List[Process]):
        self.name: str = name
        self.entity: Entity = e
        self.signals: List[Signal] = s
        self.miscellaneous: List[Any] = []
        self.processes: List[Process] = p

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
        if value.data.value == "literal":
            literal = value.children[0]
            return literal.value, literal.type

        if value.data.value == "binary_expression":
            v1, t1 = get_compile_value(value.children[0], signals, entity)
            v2, t2 = get_compile_value(value.children[2], signals, entity)
            
            if t1 == t2 or cast_map[t1] == cast_map[t2]: # TODO: Cast Map Maybe??
                op = value.children[1]
                result = evaluate(op, v1, v2, t1)
                return result, t1
            else:
                assert(0)

        pass
    pass

def get_architecture(ast: Tree, entities: List[Entity]) -> List[Architecture]|None:
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
    
    def get_arch_signal(node: Tree, entity: Entity) -> List[Signal]|None:
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
                            continue
                        if cast_map[value_type] == cast_map[type_of_expn] or value_type == type_of_expn:
                            default_value = value
                        else:
                            if isinstance(signal.children[2], Token):
                                error.push_error(signal.children[2].line, signal.children[2].column, f"")
                            else:
                                error.push_error()
                    
                    signals.append(Signal(name, value_type, default_value))
        return signals


    def get_arch_processes(node, entity: Entity, signals: List[Signal]) -> List[Process]|None:
        print()
        processes = []
        
        def get_shorthandprocess(sprocess: Tree) -> Process:
            lvalue = sprocess.children[0].value
            pass

        def get_longformprocess(lprocess: Tree, entity: Entity, signals: List[Signal]) -> Process:
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
                            if s.name == symbol.value:
                                flag = True
                        for s in entity.ports:
                            if s.name == symbol.value:
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
                                error.push_error(token.children[1].line, token.children[1].column, f"Unmathced variable and value type {vhdl_type} {vhdl_type2}")
                                continue
                        
                        symbols.append(Variable(name, vhdl_type, value))
                        
                    if token.data.value == "statements":
                        pass

            return Process(pname, statements, sensitivity_list, symbols)

        for child in node.children:
            if isinstance(child, Tree):
                if child.data.value == "archdefination":
                    for process in child.children:
                        if process.children[0].data.value == "shorthandprocess":
                            shorthandprocess = process.children[0]
                            processes.append(get_shorthandprocess(shorthandprocess))
                        elif process.children[0].data.value == "longformprocess":
                            lfprocess = process.children[0]
                            processes.append(get_longformprocess(lfprocess, entity, signals))       
            
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
            architectures.append(Architecture(name, entity, signals, processes))

    return architectures

def print_architecture(arch: List[Architecture]):
    pass