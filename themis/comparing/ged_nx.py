import networkx as nx

from typing import Dict, Optional, List

from themis.transforming.calls import CallsNode, Function, IODesc



def compute_ged(graph1: nx.DiGraph, graph2: nx.DiGraph):
    return nx.graph_edit_distance(
        graph1,
        graph2,
        node_comparator,
        roots=('entry', 'entry')
    )


def node_comparator(node1: Dict[str, CallsNode], node2: Dict[str, CallsNode]) -> bool:
    calls_node1 = node1["call"]
    calls_node2 = node2["call"]

    if compare_func(calls_node1.func, calls_node2.func):
        return False

    if compare_descriptors(calls_node1.input_fd, calls_node2.input_fd):
        return False

    if compare_descriptor_lists(calls_node1.output_fd, calls_node2.output_fd):
        return False

    
    return True


def compare_func(func1: Function, func2: Function) -> bool:
    if func1.effect != func2.effect:  # pretty low effort, we should not consider differences s.a write/writev
        return False

    # TODO : more fine grained comparison, this is too harsh
    if func1.funcname != func2.funcname:
        return False

    return True


def compare_descriptors(desc1: Optional[IODesc], desc2: Optional[IODesc]) -> bool:

    if desc1 is None and desc2 is not None:
        return False
    if desc2 is None and desc1 is not None:
        return False
    if desc1 is None and desc2 is None:
        return True

    if desc1.typ != desc2.typ:
        return False

    return True

def compare_descriptor_lists(desc1: Optional[List[IODesc]], desc2: Optional[List[IODesc]]) -> bool:

    if desc1 is None and desc2 is not None:
        return False
    if desc2 is None and desc1 is not None:
        return False
    if desc1 is None and desc2 is None:
        return True

    if len(desc1) != len(desc2):
        return False 

    if len(desc1) == 1 and len(desc2) == 1:
        return compare_descriptors(desc1[0], desc2[0])

    # TODO: compare multiple out fds, where ordering might not be preserved

    return True