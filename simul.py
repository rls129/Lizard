from entity import *
from arch import *
from typing import Tuple
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

    def execute_longformprocess(lfprocess: Process): # Make this return None if it encounters wait without times
        # wait breaks the execution and return queue_time

        pass

    if process.statements[0].data.value == "shorthandprocess":
        if waiting_process: # Only relevant for time 0
            execute_shorthandprocess(process)
            architecture.inactive_process.append(process)
            return None
        else:
            execute_shorthandprocess(process) 
            return None

    if process.statements[0].data.value == "longformprocess":
        if waiting_process:
            queue_time = execute_longformprocess(process)
            if len(process.sensitivity_list) > 0: # Only relevant for time 0
                architecture.inactive_process.append(process)
                return None
            return queue_time
        else:
            execute_longformprocess(process)
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