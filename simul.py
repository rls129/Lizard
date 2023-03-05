from entity import *
from arch import Architecture, Process, get_compile_value, Signal, Variable
from typing import Tuple, Optional
import heapq

class Simulation:
    def __init__(self):
        self.current_time = 0.
        self.to_run_till = 0.
    
    def perform_jump(self, archs: List[Architecture]):
        min = 0.
        for arch in archs:
            for w in arch.waiting_process:
                if min < w[1]:
                    min = w[1]
        self.current_time = (self.current_time + min)
        if self.current_time > self.to_run_till:
            self.current_time = self.to_run_till

simulation = Simulation()


def get_runtime_value(node, architecture: Architecture, symbol: List[Variable]) -> Tuple[str, str] | None:

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
            for sym in symbol:
                if sym.name == value.value:
                    return sym.value, sym.type
            for s in architecture.signals:
                if s.name == value.value:
                    return s.value, s.type
            for p in architecture.entity.ports:
                if p.name == value.value:
                    return p.value, p.type
    if isinstance(value, Tree):
        if value.data.value == "value":
            return get_runtime_value(value, architecture, symbol)
        if value.data.value == "literal":
            literal = value.children[0]
            return literal.value, literal.type

        if value.data.value == "binary_expression":
            v1, t1 = get_runtime_value(value.children[0], architecture, symbol)
            v2, t2 = get_runtime_value(value.children[2], architecture, symbol)
            
            op = value.children[1].value
            result = evaluate(op, v1, v2, t1)
            if op == '=' or op == '/=':
                t1 = 'bool'
            return result, t1



# def execute_sts(statements_node, arch: Architecture, symbols: List[Variable]):
#     success_flag = True
#     for statement in statements_node.children:
#         if execute_st(statement, arch, symbols) is None:
#             success_flag = None
#     return success_flag

def execute_st(statement, arch: Architecture, symbols: List[Variable]):
    
    
    # def get_condition_type(condition, signals, entity, symbols, lvalue):
    #     if len(condition.children) == 1:
    #         return get_compile_type(condition.children[0], signals, entity, symbols, lvalue)
    #     if isinstance(condition.children[0], Tree) and condition.children[0].data.value == "value":
    #         t1 = get_compile_type(condition.children[0], signals, entity, symbols, lvalue)
    #         t2 = get_compile_type(condition.children[2], signals, entity, symbols, lvalue)
            
    #         if t1 == t2 or cast_map[t1] == cast_map[t2]:
    #             return 'bool'
    #         else:
    #             cur = condition
    #             while isinstance(cur, Tree):
    #                 cur = cur.children[0]
    #             error.push_error(cur.line, cur.column, f"Type Mismatch {t1} and {t2}")
    #             return None

    #     for child in condition.children:
    #         if not isinstance(child, Tree):
    #             continue
    #         if child.data.value == "condition":
    #             if get_condition_type(child, signals, entity, symbols, lvalue)!='bool':
    #                 return None
    #     return 'bool'

            
    def get_lvalue_reference(lval):
        for p in arch.entity.ports:
            if p.name == lval.value:
                return p
        for s in arch.signals:
            if s.name == lval.value:
                return s
        for sym in symbols:
            if sym.name == lval.value:
                return sym
            
    if statement.data.value == "shorthandprocess":
        lvalue = get_lvalue_reference(statement.children[0])
        rvalue, _ = get_runtime_value(statement.children[1], arch, symbols)
        lvalue.future_buffer = rvalue
        if lvalue not in arch.signals_changed:
            arch.signals_changed.append(lvalue)
            return None
    elif statement.data.value == "variable_assignment":
        lvalue = get_lvalue_reference(statement.children[0])
        rvalue, _ = get_runtime_value(statement.children[1], arch, symbols)
        lvalue.value = rvalue
        return None
    elif statement.data.value == "wait":

        # TODO: Implement it
        return True
    elif statement.data.value == "report":
        # TODO: Implement it
        return True
    elif statement.data.value == "if_statement":
        # ifstatement = statement.children[0]
        # condition = ifstatement.children[0]
        # condition_type = get_condition_type(condition, signals, entity, symbols, False)
        # if condition_type != "bool":
        #     cur = ifstatement
        #     while isinstance(cur, Tree):
        #         cur = cur.children[0]
        #     error.push_error(cur.line, cur.column, "Value inside if condition is not boolean type.")
        #     return None
        # ifstatements = ifstatement.children[1]
        # if parse_sts(ifstatements, signals, entity, symbols, statements) is None:
        #     return None
        # for i in range(2, len(ifstatement.children)):
        #     child = ifstatement.children[i]
        #     if child.children[0].data.value == "condition":
        #         condition = child.children[0]
        #         condition_type = get_condition_type(condition, signals, entity, symbols, False)
        #         if condition_type != "bool":
        #             cur = child
        #             while isinstance(cur, Tree):
        #                 cur = cur.children[0]
        #             error.push_error(cur.line, cur.column, "Value inside elsif condition is not boolean type.")
        #             return None
        #     elstatements = child.children[-1]
        #     if parse_sts(elstatements, signals, entity, symbols, statements) is None:
        #         return None

        # # print()
        return None
    elif statement.data.value == "while_statement":
        # while_statement = statement.children[0]
        # condition = while_statement.children[0]
        # condition_type = get_condition_type(condition, signals, entity, symbols, False)
        # if condition_type != "bool":
        #     cur = while_statement
        #     while isinstance(cur, Tree):
        #         cur = cur.children[0]
        #     error.push_error(cur.line, cur.column, "Value inside elsif condition is not boolean type.")
        #     return None
        # statements_node = while_statement.children[1]
        # if parse_sts(statements_node, signals, entity, symbols, statements) is None:
        #     return None
        return None
    return None
            
def execute_process(process: Process, architecture: Architecture, waiting_process: bool) -> float | None:
    # Set waiting_process True for arch.waiting_process and False for inactive_process
    def execute_shorthandprocess(shprocess: Process): # WARNING: DO NOT REUSE FOR SHPROCESS INSIDE LONGFORM PROCESS!!!
        def get_lvalue_reference(lval):
            for p in architecture.entity.ports:
                if p.name == lval.value:
                    return p
            for s in architecture.signals:
                if s.name == lval.value:
                    return s
            
        statement = process.statements[0]
        lvalue = get_lvalue_reference(statement.children[0])
        rvalue, _ = get_compile_value(statement.children[1], architecture.signals, architecture.entity)
        lvalue.value = rvalue
        if lvalue not in architecture.signals_changed: #Intentional, replicate this
            architecture.signals_changed.append(lvalue)

    def execute_longformprocess(lfprocess: Process, arch: Architecture): # Make this return None if it encounters wait without times
        # wait breaks the execution and return queue_time
        for statement in lfprocess.statements:
            queue_time = execute_st(statement, arch, lfprocess.symbol_table)
            if queue_time is not None:
                break
        

        pass

    if process.name == "shorthandprocess":
        if waiting_process: # Only relevant for time 0
            execute_shorthandprocess(process)
            architecture.inactive_process.append(process)
            return None
        else:
            execute_shorthandprocess(process) 
            return None

    else:
        if waiting_process:
            queue_time = execute_longformprocess(process, architecture)
            if len(process.sensitivity_list) > 0: # Only relevant for time 0
                architecture.inactive_process.append(process)
                return None
            return queue_time
        else:
            execute_longformprocess(process, architecture)
            return None
        

def run_simulation(exec_time: float, architectures: List[Architecture]):
    simulation.to_run_till = simulation.current_time + exec_time

    # Yes, super intentional
    if simulation.current_time == 0.:
        for arch in architectures:
            arch.signals_changed.clear()
            arch.waiting_process.clear()
            arch.inactive_process.clear()
            for process in arch.processes:
                queue_time = execute_process(process, arch, True)
                if queue_time is not None:
                    arch.waiting_process.append((process, queue_time))
                
            for sig in arch.signals_changed: #Intentionally one block outside unlike below
                sig.value = sig.future_buffer if sig.future_buffer is not None else sig.value
                for pr in sig.linked_process:
                    execute_process(pr, arch, False) # Guaranteed to be inactive (aka sensitivity list)
                # arch.signals_changed.remove(sig) #should be removed once done with, but fucks up iterator so
            arch.signals_changed.clear()


    simulation.perform_jump(architectures)

    while(simulation.current_time < simulation.to_run_till):
        for arch in architectures:
            for process in arch.waiting_process:
                if process[1] == simulation.current_time:
                    queue_time = execute_process(process[0], arch, True)
                    arch.waiting_process.remove(process)
                    if queue_time is not None:
                            arch.waiting_process.append((process[0], queue_time))

            for sig in arch.signals_changed:
                sig.value = sig.future_buffer if sig.future_buffer is not None else sig.value
                for pr in sig.linked_process:
                    execute_process(pr, arch, False) # Guaranteed to be inactive (aka sensitivity list)
            # arch.signals_changed.remove(sig) #should be removed once done with, but fucks up iterator so
            arch.signals_changed.clear()


        simulation.perform_jump(architectures)
                                        
        pass