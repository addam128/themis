from cmath import inf
import networkx as nx
import itertools

from typing import Dict, List, Tuple, Optional
from ortools.linear_solver import pywraplp

from themis.modules.comparing.primitives import NodeID, NodeMatch
from themis.modules.comparing.error import AssignmentSolverException
from themis.modules.common.calls import IOCall




class BranchComparator:
    def __init__(
        self,
        branch_d: Optional[nx.Graph],
        branch_t: Optional[nx.Graph]
    ) -> None:
        
        self._branch_d = branch_d
        self._branch_t = branch_t



    def _assign(
        self,
        distances: Dict[Tuple[NodeID, NodeID], int]
    ) -> Tuple[int, List[Tuple[NodeID, NodeID]]]:

        solver = pywraplp.Solver.CreateSolver('SCIP')

        assignments = dict((pair, solver.IntVar(0, 1, '')) for pair in distances.keys())
        
        for node_d in self._branch_d.nodes:
            solver.Add(solver.Sum([assignments[(node_d, node_t)] for node_t in self._branch_t.nodes]) <= 1)

        for node_t in self._branch_t.nodes:
            solver.Add(solver.Sum([assignments[(node_d, node_t)] for node_d in self._branch_d.nodes]) <= 1)

        objective = list()
        for pair in distances.keys():
            objective.append(distances[pair] * assignments[pair])

        #for pair_1, pair_2 in itertools.combinations(distances.keys(), 2):
         #   objective.append(-1 * assignments[pair_1] * self._structural_penalty([pair_1, pair_2]) * assignments[pair_2])
            # sadly we cant do multiplication on two IntVars, and thus cant combine the structural penalty into the optimization
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



    def _structural_penalty(
        self,
        assignment: List[Tuple[NodeID, NodeID]]
    ) -> int:
        
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



    def compare(
        self
    ) -> Tuple[float, List[NodeMatch]]:

        node_match_avg = 0
        node_assignments = list()
        structural_penalty = inf

        if self._branch_d is not None and self._branch_t is not None:
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
        nodes_d = set(self._branch_d.nodes) if self._branch_d is not None else set()
        nodes_t = set(self._branch_t.nodes) if self._branch_t is not None else set()
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
                    differences=IOCall.compare(self._branch_d.nodes[node]["call"], None)[1],
                    score=0
                )
            )

        for node in nodes_t:
            result.append(
                NodeMatch(
                    d_node=None,
                    t_node=node,
                    differences=IOCall.compare(None, self._branch_t.nodes[node]["call"])[1],
                    score=0
                )
            )

        return node_match_avg - structural_penalty, result