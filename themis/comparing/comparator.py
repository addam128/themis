import networkx as nx
import itertools
from numpy import reciprocal

from ortools.linear_solver import pywraplp
from typing import Union, List, Dict, Iterable, Tuple, NamedTuple, Optional

from themis.transforming.transform import reconstruct_one_pickle 
from themis.common.config import Config
from themis.transforming.calls import CallsNode, DiffInfo, IOCall, IOConstructType
from themis.comparing.error import AssignmentSolverException


NodeID = Union[int, str]




class NodeMatch(NamedTuple):
    d_node: Optional[NodeID]
    t_node: Optional[NodeID]
    score: int
    differences: Optional[DiffInfo]




class BranchComparator:
    def __init__(self, branch_d: nx.Graph, branch_t: nx.Graph) -> None:
        self._branch_d = branch_d
        self._branch_t = branch_t



    def _assign(self, distances: Dict[Tuple[NodeID, NodeID], int]) -> Tuple[int, List[Tuple[NodeID, NodeID]]]:

        solver = pywraplp.Solver.CreateSolver('SCIP')

        assignments = dict((pair, solver.IntVar(0, 1, '')) for pair in distances.keys())
        
        for node_d in self._branch_d.nodes:
            solver.Add(solver.Sum([assignments[(node_d, node_t)] for node_t in self._branch_t.nodes]) <= 1)

        for node_t in self._branch_t.nodes:
            solver.Add(solver.Sum([assignments[(node_d, node_t)] for node_d in self._branch_d.nodes]) <= 1)

        objective = list()
        for pair in distances.keys():
            objective.append( distances[pair] * assignments[pair])

        solver.Maximize(solver.Sum(objective))
        status = solver.Solve()
        
        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            match_avg = solver.Objective().Value() / max(self._branch_d.number_of_nodes(), self._branch_t.number_of_nodes())
            result = []
            for pair, state in assignments.items():
                if state.solution_value() > 0.5:
                    result.append(pair)
            return match_avg, result
        else:
            raise AssignmentSolverException()



    def _structural_penalty(self, assignment: List[Tuple[NodeID, NodeID]]) -> int:
        accumulator = 0
        for a1, a2 in itertools.combinations(assignment, 2):
            accumulator += abs(
                nx.shortest_path_length(
                    self._branch_d.to_undirected(reciprocal=False, as_view=True),
                    source=a1[0],
                    target=a2[0],
                    weight=None
                ) 
                -
                nx.shortest_path_length(
                    self._branch_t.to_undirected(reciprocal=False, as_view=True),
                    source=a1[1],
                    target=a2[1],
                    weight=None
                )
            ) * 2

        return accumulator



    def compare(self) -> Tuple[int, List[NodeMatch]]:
        diffs = dict()
        distances = dict()

        for node_d, data_d in self._branch_d.nodes(data="call"):
            for node_t, data_t in self._branch_t.nodes(data="call"):
                val, diff = IOCall.compare(data_d, data_t)
                distances[(node_d, node_t)] = val
                diffs[(node_d, node_t)] = diff

        node_match_avg, node_assignments = self._assign(distances)
        structural_penalty = self._structural_penalty(node_assignments)

        #print(f"Node match AVG is {node_match_avg}, assignments are as follows: {node_assignments}\n",
            #f"structural penalty: {structural_penalty}")
        nodes_d = set(self._branch_d.nodes)
        nodes_t = set(self._branch_t.nodes)
        result = list()

        for pair in node_assignments:
            result.append(
                NodeMatch(
                    d_node=pair[0],
                    t_node=pair[1],
                    differences=diffs[pair],
                    score=distances[pair]
                )
            )
            nodes_d.remove(pair[0])
            nodes_t.remove(pair[1])

        for node in nodes_d:
            result.append(
                NodeMatch(
                    d_node=node,
                    t_node=None,
                    differences=IOCall.compare(self._branch_d.nodes[node]["call"], None),
                    score=0
                )
            )

        for node in nodes_t:
            result.append(
                NodeMatch(
                    d_node=None,
                    t_node=node,
                    differences=IOCall.compare(None, self._branch_t.nodes[node]["call"]),
                    score=0
                )
            )

        return node_match_avg - structural_penalty, result





class DeepGraphComparator:
    def __init__(self, config: Config, dirty_exec: str, trusted_exec: str) -> None:
        self._dirty_graph: nx.Graph = reconstruct_one_pickle(f"{config.dirty_graph_dir}/{dirty_exec}_graph.pickle")
        self._trusted_graph: nx.Graph = reconstruct_one_pickle(f"{config.trusted_graph_dir}/{trusted_exec}_graph.pickle")
        self._dirty_nodes = self._dirty_graph.nodes(data=True)
        self._trusted_nodes = self._trusted_graph.nodes(data=True)

        self._branches = self._get_branches()



    @staticmethod
    def _guess_io_type(call: CallsNode) -> IOConstructType:
        type_hints = list()
        if call.input_fd is not None:
            type_hints.append(call.input_fd.typ)
        if call.output_fd is not None:
            for fd in call.output_fd:
                type_hints.append(fd.typ)

        io_type = sorted(type_hints, reverse=True)[0] if len(type_hints) > 0 else IOConstructType.UNKNOWN
        return io_type



    @staticmethod
    def _guess_branch_io_type(indexes: List[NodeID], graph: nx.Graph) -> IOConstructType:
        guesses = set()
        for idx in indexes:
            guesses.add(DeepGraphComparator._guess_io_type(graph.nodes[idx]["call"]))

        io_type = sorted(guesses, reverse=True)[0] if len(guesses) > 0 else IOConstructType.UNKNOWN

        return io_type



    @staticmethod
    def _get_subgraphs(children: Iterable[NodeID], graph:nx.Graph) -> Dict[IOConstructType, List[nx.Graph]]:
        res = dict()
        for child in children:
            indexes = DeepGraphComparator._traverse(child, graph)
            io_type = DeepGraphComparator._guess_branch_io_type(indexes, graph)
            if res.get(io_type, None) is None:
                res[io_type] = []
            res[io_type].append(graph.subgraph(indexes))
        return res



    @staticmethod
    def _traverse(node: NodeID, graph: nx.Graph) -> List[Union[int, str]]:
        res = [node]
        for successor in graph.neighbors(node):
            res.extend(DeepGraphComparator._traverse(successor, graph))
        return res



    def _get_branches(self) -> Tuple[Dict[IOConstructType, List[nx.Graph]]]:
        dirty_idx = "entry"
        trusted_idx = "entry"
        dirty_children = self._dirty_graph.neighbors(dirty_idx)
        trusted_children = self._trusted_graph.neighbors(trusted_idx)

        return self._get_subgraphs(dirty_children, self._dirty_graph), \
            self._get_subgraphs(trusted_children, self._trusted_graph)



    def compare(self) -> None:
        dirty_branches, trusted_branches = self._get_branches()

        


        pass # TODO: compare all relevant branches, + solve those which might not be under same IOtype but could match
        # Choose best assignment - ortools again 



