from lark import Token, Tree


from arch import Architecture
from base import Process, Variable
from utils import evaluate
from typing import Tuple, List

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
        self.current_time = min
        if self.current_time > self.to_run_till:
            self.current_time = self.to_run_till

simulation = Simulation()


def get_runtime_value(node, architecture: Architecture, symbol: List[Variable]) -> Tuple[str, str] | None:
    '''
    Binary Expression Tree
    Literal Tree
    Identifier Token

    Return: Value, Type
    '''
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



def execute_st(arch: Architecture, symbols: List[Variable], process: Process):
    
    stack = process.statements.stack    #copy reference only
            
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

    def evaluateCondition(condition: Tree) -> bool:
        if isinstance(condition.children[0], Token) and condition.children[0].value == "(":
            return evaluateCondition(condition.children[1])
        elif isinstance(condition.children[1], Token) and condition.children[1].value == "and":
            assert(isinstance(condition.children[0], Tree) and isinstance(condition.children[2], Tree))
            return evaluateCondition(condition.children[0]) and evaluateCondition(condition.children[2])
        elif isinstance(condition.children[1], Token) and condition.children[1].value == "or":
            assert(isinstance(condition.children[0], Tree) and isinstance(condition.children[2], Tree))
            return evaluateCondition(condition.children[0]) or evaluateCondition(condition.children[2])
        elif isinstance(condition.children[0], Token) and condition.children[0].value == "not":
            assert(isinstance(condition.children[1], Tree))
            return not evaluateCondition(condition.children[1])
        assert(isinstance(condition.children[0], Tree) and isinstance(condition.children[2], Tree) and isinstance(condition.children[1], Token))
        lvalue = get_runtime_value(condition.children[0], arch, symbols)[0]
        rvalue = get_runtime_value(condition.children[2], arch, symbols)[0]
        if condition.children[1].value == "=":
            if lvalue == rvalue:
                return True
            return False
        elif condition.children[1].value == "/=":
            if lvalue != rvalue:
                return True
            return False
        return False
            
    def fill_sts(stack, sts):
        for st in reversed(sts.children):
            stack.append(st.children[0])

    while stack:
        statement = stack[-1]
        if statement.data.value == "shorthandprocess":
            stack.pop()
            lvalue = get_lvalue_reference(statement.children[0])
            rvalue, _ = get_runtime_value(statement.children[1], arch, symbols)
            lvalue.future_buffer = rvalue
            if lvalue not in arch.signals_changed:
                arch.signals_changed.append(lvalue)
        elif statement.data.value == "variable_assignment":
            stack.pop()
            lvalue = get_lvalue_reference(statement.children[0])
            rvalue, _ = get_runtime_value(statement.children[1], arch, symbols)
            lvalue.value = rvalue
        elif statement.data.value == "wait":
            stack.pop()
            if len(statement.children) == 0:
                return simulation.to_run_till
            else:
                def convert_to_nano(unit: str):
                    if unit == "ns":
                        return 1
                    elif unit == "us":
                        return 1_000
                    elif unit == "ms":
                        return 1_000_000
                    else: #"s"
                        return 1_000_000_000
                
                value = int(statement.children[0])
                unit  = statement.children[1]
                return value * convert_to_nano(unit)
        elif statement.data.value == "report":
            # TODO: Implement it
            stack.pop()
            return True
        elif statement.data.value == "if_statement":
            stack.pop()
            condition = statement.children[0]
            if(evaluateCondition(condition)):
                # assert(isinstance(statement.children[1], Tree))
                fill_sts(stack, statement.children[1])
            else:
                for i in range(2, len(statement.children)):
                    child = statement.children[i]
                    if child.data.value == "elsif":
                        childcondition = child.children[0]
                        if evaluateCondition(childcondition):
                            fill_sts(stack, child.children[1])
                            break
                    if child.data.value == "else":
                        fill_sts(stack, child.children[0])
        elif statement.data.value == "while_statement":
            condition = statement.children[0]
            if evaluateCondition(condition):
                fill_sts(stack, statement.children[1])
            else:
                stack.pop()
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
        rvalue, _ = get_runtime_value(statement.children[1], architecture, [])
        lvalue.value = rvalue
        if lvalue not in architecture.signals_changed: #Intentional, replicate this
            architecture.signals_changed.append(lvalue)
        return None

    def execute_longformprocess(lfprocess: Process, arch: Architecture): # Make this return None if it encounters wait without times
        # wait breaks the execution and return queue_time
        if len(lfprocess.statements.stack) == 0:
            for st in reversed(lfprocess.statements.statements):
                lfprocess.statements.stack.append(st)
        
        queue_time = execute_st(arch, lfprocess.symbol_table, lfprocess)
        if queue_time is not None:
            return queue_time
        # for i in range(lfprocess.statements.pc, len(lfprocess.statements.statements)):
        #     queue_time = execute_st(lfprocess.statements[i], arch, lfprocess.symbol_table, lfprocess)
        #     if queue_time is not None:
        #         return queue_time
        


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
        
def vcd_data(architectures: List[Architecture]):
    print(f"At {simulation.current_time}")
    for arch in architectures:
        for p in arch.entity.ports:
            print(p.name, p.value)
        for s in arch.signals:
            print(s.name, s.value)
        for proc in arch.processes:
            for v in proc.symbol_table:
                print(v.name, v.value)



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
                
            for sig in arch.signals_changed: 
                sig.value = sig.value if sig.future_buffer is None or sig.future_buffer == 'None' else sig.future_buffer
                for pr in sig.linked_process:
                    execute_process(pr, arch, False) # Guaranteed to be inactive (aka sensitivity list)
            arch.signals_changed.clear()

    vcd_data(architectures)
    simulation.perform_jump(architectures)

    while(simulation.current_time < simulation.to_run_till):
        for arch in architectures:
            temp_process: List[Tuple[Process, float]] = []
            for process in arch.waiting_process:
                if process[1] == simulation.current_time:
                    queue_time = execute_process(process[0], arch, True)
                    if queue_time is not None:
                            temp_process.append((process[0], simulation.current_time + queue_time))
            arch.waiting_process.clear()
            arch.waiting_process.extend(temp_process)
            for sig in arch.signals_changed:
                sig.value = sig.value if sig.future_buffer is None or sig.future_buffer == 'None' else sig.future_buffer
                for pr in sig.linked_process:
                    execute_process(pr, arch, False) # Guaranteed to be inactive (aka sensitivity list)
            # arch.signals_changed.remove(sig) #should be removed once done with, but fucks up iterator so
            arch.signals_changed.clear()


        vcd_data(architectures)                         
        simulation.perform_jump(architectures)
        pass