import networkx as nx

from enum import Enum, auto
from typing import Tuple, List

from themis.modules.common.calls import CallsNode, Function, GraphFunc, IOCall, IODescFunc
from themis.modules.transforming.parser import CallParser


class EdgeType(Enum):
    FOLLOW = auto()
    NEST = auto()
    TIME = auto()




class Grapher:
    def __init__(
        self,
        parser: CallParser
    ) -> None:
    
        self._parser = parser
        self._graph = nx.DiGraph()
        self._i_o_descriptors = dict()  # fd_int : (IODesc, node_id) - node_id points to last event for particular fd
        self._init_graph()



    def _init_graph(
        self    
    ) -> None:
        
        self._graph.add_node("entry", call=CallsNode(call=IOCall(func=Function("entry", IODescFunc.NONE))))



    def _create_tree(
        self
    ) -> None:
        # NOTE: uncomment the lines if you want the time-structure to be seen as edges (without that it is encoded into node id-s) 

        #last_node = "entry"
        for call, action in self._parser.parse():

            self._graph.add_node(str(call.id), call=call)
            #self._graph.add_edge(last_node, str(call.id), type=EdgeType.TIME)
            #last_node = str(call.id)
            parent = "entry" if call.input_fd is None else self._i_o_descriptors.get(call.input_fd.fd, "entry")
            self._graph.add_edge(parent, str(call.id), type=EdgeType.FOLLOW)
            if call.input_fd is not None:
                self._i_o_descriptors[call.input_fd.fd] = str(call.id)
            if call.output_fd is not None:
                for fd in call.output_fd:
                    self._i_o_descriptors[fd.fd] = str(call.id)

            if action == GraphFunc.NONE:
                continue
            if action == GraphFunc.RESET_FD:
                self._i_o_descriptors[call.input_fd.fd] = "entry"
                if call.input_fd.internal is not None:
                    self._i_o_descriptors[call.input_fd.internal.fd] = "entry"
            if action == GraphFunc.RESET_STREAMS:
                pass  # TODO



    def _add_nesting_edges(
        self
    ) -> None:
    
        for start, end in self._parser.nesting_edges():
            self._graph.add_edge(start, end, type=EdgeType.NEST)



    def into_graph(
        self
    ) -> Tuple[nx.DiGraph, List]:
        
        self._create_tree()
        self._add_nesting_edges()

        return self._graph

