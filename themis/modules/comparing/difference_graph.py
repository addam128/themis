import itertools
import networkx as nx
import json

from enum import Enum, auto
from typing import List, Tuple, Mapping, Any
from themis.modules.common.calls import ArgStatus, FunctionComparisonResult

from themis.modules.comparing.primitives import BranchID, NodeMatch




class NodeType(Enum):
    MATCHING = auto()
    MISCELLANEOUS_MISMATCH = auto()
    FUNCTION_MISMATCH_WEAK = auto()
    FUNCTION_MISMATCH_STRONG = auto()
    MISSING = auto()
    EXCESSIVE = auto()




class EdgeType(Enum):
    MATCHING = auto()
    TYPE_MISMATCH = auto()
    MISSING = auto()
    EXCESSIVE = auto()




class DiffGraph:
    def __init__(
        self,
        dirty_graph: nx.DiGraph,
        trusted_graph: nx.DiGraph,
        assignments: List[Tuple[BranchID, BranchID, float, List[NodeMatch]]]
    ) -> None:
        
        self._dirty_graph = dirty_graph
        self._trusted_graph = trusted_graph
        self._assignments = assignments
        self._result_graph = nx.DiGraph()
        self._result_graph.add_node(("entry", "entry"))




    def _extract_node_args(
        self,
        match: NodeMatch
    ) -> Mapping[Any, Any]:

        stringify = lambda tup: (tup[0], tup[1], str(tup[2]))

        res = dict()
        res["type"] = str(self._get_node_type(match))
        res["func"] = stringify(match.differences.func_diff)
        res["time"] = match.differences.idx_diff
        res["score"] = match.score
        res["args"] = dict((key, stringify(value)) for key, value in match.differences.args_diff.items())

        return res

        
    def _get_node_type(
        self,
        match: NodeMatch
    ) -> Tuple[str, NodeType]:
        
        if match.d_node is None:
            return NodeType.MISSING
        if match.t_node is None:
            return NodeType.EXCESSIVE
        if match.differences.func_diff[2] == FunctionComparisonResult.EQUIV_CLASS:
            return NodeType.FUNCTION_MISMATCH_WEAK
        if match.differences.func_diff[2] == FunctionComparisonResult.DIFFERENT:
            return NodeType.FUNCTION_MISMATCH_STRONG
        if match.differences.idx_diff[0] != match.differences.idx_diff[0]:
            return NodeType.MISCELLANEOUS_MISMATCH
        if len(
            list(
                filter(
                    lambda s: s != ArgStatus.MATCHING,
                    map(lambda v: v[2], match.differences.args_diff.values())
                    )
                )
            ) != 0:
            return NodeType.MISCELLANEOUS_MISMATCH

        return NodeType.MATCHING


    
    def _add_edges(
        self
    ) -> None:

        for n1, n2 in itertools.permutations(self._result_graph.nodes, 2):
            d_edge = self._dirty_graph.has_edge(n1[0], n2[0])
            t_edge = self._dirty_graph.has_edge(n1[1], n2[1])

            if not d_edge and not t_edge:
                continue
            elif d_edge and not t_edge:
                edge_role = self._dirty_graph.get_edge_data(n1[0], n2[0], default=dict()).get("type", None)
                self._result_graph.add_edge(n1, n2, type=str(EdgeType.EXCESSIVE), role=str(edge_role))
            elif not d_edge and t_edge:
                edge_role = self._trusted_graph.get_edge_data(n1[1], n2[1], default=dict()).get("type", None)
                self._result_graph.add_edge(n1, n2, type=str(EdgeType.MISSING), role=str(edge_role))
            else:
                edge_role_d = self._dirty_graph.get_edge_data(n1[0], n2[0], default=dict()).get("type", None)
                edge_role_t = self._trusted_graph.get_edge_data(n1[1], n2[1], default=dict()).get("type", None)

                edge_type = EdgeType.MATCHING if edge_role_d == edge_role_t else EdgeType.TYPE_MISMATCH

                self._result_graph.add_edge(n1, n2, type=str(edge_type),
                 role=(str(edge_role_d), str(edge_role_t)) if edge_type == EdgeType.TYPE_MISMATCH else str(edge_role_d))



    def compute(
        self
    ) -> 'DiffGraph':
        
        for _, _, _, matches in self._assignments:
            for node in matches: 
                self._result_graph.add_node(
                    (node.d_node, node.t_node),
                    **self._extract_node_args(node)
                )
        self._add_edges()

        return self



    def serialize(
        self,
        path: str
    ) -> None:
        
        data = nx.readwrite.json_graph.node_link_data(self._result_graph)
        
        with open(path, "w") as outfile:
            json.dump(data, fp=outfile, indent=4)






