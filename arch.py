from lark import Tree, Token
from copy import deepcopy
from typing import List, Any, Tuple

from entity import Entity, Port
from base import Process, Signal, get_arch_processes
from utils import default_values, cast_map, evaluate
import error


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


def get_arch_signals(node: Tree, entity: Entity) -> List[Signal]:
    '''
    Input: Tree(Lark) with the architecture data, parsed entity from architecture tree
    '''
    signals: List[Signal] = []

    for child in node.children:
        if isinstance(child, Tree):
            if child.data.value == "archsignal":
                signal = child
                signal_name = signal.children[0].value
                value_type = signal.children[1].value

                unique = True
                for port in entity.ports:
                    if port.name == signal_name:
                        error.push_error(signal.children[0].line, signal.children[0].column, f"Declaration with designator {signal_name} already exists in this region.")
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
                
                signals.append(Signal(signal_name, value_type, default_value))
    return signals


def get_architecture(ast: Tree, entities: List[Entity]) -> List[Architecture]:
    '''
    Input: Tree(Lark) with root which has entity and architecture
    '''
    architectures: List[Architecture] = []
    def get_arch_name(node):
        '''
        Input: Tree(Lark) with the architecture data
        Output: Name of architecture as string
        '''
        name = node.children[0].value
        if isinstance(node.children[-1], Token) and node.children[-1].type == "IDENTIFIER":
            '''
            Ensuring both name(X) matches if 
            architecture X 

            end architecture X
            convention is used

            If unmatched, error is pushed, but the node is further parsed to find as much errors as possible during compilation.
            '''
            if node.children[-1].value != name:
                error.push_error(node.children[-1].line, node.children[-1].column, f"Unmatched Closing Identifier {name}")
        return name

    def get_arch_entity(node: Tree, entities: List[Entity]) -> Entity|None:
        '''
        Input: Tree(Lark) with the architecture data, all parsed entities so far
        Output: Name of entity in the architecture as string, None if valid entity doesn't exist
        '''
        entity = node.children[1]
        for e in entities:
            if e.name == entity.value:
                return e
        error.push_error(entity.line, entity.column, f"No Entity named {entity.value}")
        return None
    

    for node in ast.children:
        if node.data.value == "architechture":
            name      = get_arch_name(node)
            entity    = get_arch_entity(node, entities)


            if entity is None:
                '''If the entity in architecture is invalid, skip further evaluation'''
                continue

            '''
            Ensuring (architecture_name, entity) pair is unique
            '''
            for arch in architectures:
                if (name, entity.name) == (arch.name, arch.entity.name):
                    error.push_error(node.children[0].line, node.children[0].column, f"Redefination of a Entity-Architecture Pair {(name, entity.name)}")
                    continue

            signals   = get_arch_signals(node, entity)            
            processes = get_arch_processes(node, entity, signals)


            '''
            Updating the signals with the links to processes that have given signal in their sensitivity lists
            '''
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