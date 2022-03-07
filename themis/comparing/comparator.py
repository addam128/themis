import networkx as nx

from typing import Union, List, Dict, Iterable, Tuple, Optional, NamedTuple, Any

from themis.transforming.transform import reconstruct_one_pickle 
from themis.common.config import Config
from themis.transforming.calls import CallsNode, IOConstructType


NodeID = Union[int, str]


class NodeMatch(NamedTuple):
    a_node: NodeID
    b_node: NodeID
    differences: Dict[str, Tuple[Any, Any]]


class BranchComparator:
    def __init__(self, graph_a: nx.Graph, graph_b: nx.Graph) -> None:
        self._graph_a = graph_a
        self._graph_b = graph_b

    def compare(self) -> Tuple(int, List[NodeMatch]):
        pass


class DeepGraphComparator:
    def __init__(self, config: Config, dirty_exec: str, trusted_exec: str) -> None:
        self._dirty_graph: nx.Graph = reconstruct_one_pickle(f"{config.dirty_graph_dir}/{dirty_exec}_graph.pickle")
        self._trusted_graph: nx.Graph = reconstruct_one_pickle(f"{config.trusted_graph_dir}/{trusted_exec}_graph.pickle")
        self._dirty_nodes = self._dirty_graph.nodes(data=True)
        self._trusted_nodes = self._trusted_graph.nodes(data=True)

        self._branches = self._get_branches()

    @staticmethod
    def _guess_io_type(call: CallsNode) -> IOConstructType:
        type_hints = []
        if call.input_fd is not None:
            type_hints.append(call.input_fd.typ)
        if call.output_fd is not None:
            for fd in call.output_fd:
                type_hints.append(fd.typ)

        io_type = sorted(type_hints, reverse=True)[0] if len(type_hints) > 0 else IOConstructType.UNKNOWN
        return io_type

    @staticmethod
    def _get_subgraphs(children: Iterable[NodeID], graph:nx.Graph) -> Dict[IOConstructType, nx.Graph]:
        res = dict()
        for child in children:
            io_type = DeepGraphComparator._guess_io_type(graph.nodes[child]["call"])
            if res.get(io_type, None) is None:
                res[io_type] = []
            res[io_type].append(graph.subgraph(DeepGraphComparator._traverse(child, graph)))
        return res

    @staticmethod
    def _traverse(node: NodeID, graph: nx.Graph) -> List[Union[int, str]]:
        res = [node]
        for successor in graph.neighbors(node):
            res.extend(DeepGraphComparator._traverse(successor, graph))
        return res

    def _get_branches(self) -> Tuple[Dict[IOConstructType, nx.Graph]]:
        dirty_idx = "entry"
        trusted_idx = "entry"
        dirty_children = self._dirty_graph.neighbors(dirty_idx)
        trusted_children = self._trusted_graph.neighbors(trusted_idx)

        return self._get_subgraphs(dirty_children, self._dirty_graph), \
            self._get_subgraphs(trusted_children, self._trusted_graph)


    def compare(self) -> None:
        dirty_branches, trusted_branches = self._get_branches()
        print(dirty_branches)
        print(trusted_branches)



