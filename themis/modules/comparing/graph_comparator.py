import networkx as nx
import itertools
from numpy import diff

from ortools.linear_solver import pywraplp
from typing import Union, List, Dict, Iterable, Tuple

from themis.modules.comparing.branch_comparator import BranchComparator
from themis.modules.comparing.primitives import BranchID, NodeID, NodeMatch
from themis.modules.transforming.transform import reconstruct_one_pickle 
from themis.modules.common.config import Config
from themis.modules.common.calls import CallsNode, IOConstructType
from themis.modules.comparing.error import AssignmentSolverException
from themis.modules.comparing.difference_graph import DiffGraph




class DeepGraphComparator:
    def __init__(
        self,
        config: Config,
        dirty_exec: str,
        trusted_exec: str
    ) -> None:
        
        self._dirty_graph: nx.Graph = reconstruct_one_pickle(f"{config.dirty_graph_dir}/{dirty_exec}_graph.pickle")
        self._trusted_graph: nx.Graph = reconstruct_one_pickle(f"{config.trusted_graph_dir}/{trusted_exec}_graph.pickle")
        self._dirty_nodes = self._dirty_graph.nodes(data=True)
        self._trusted_nodes = self._trusted_graph.nodes(data=True)
        self._outpath = f"{config.result_dir}/{dirty_exec}_vs_{trusted_exec}.json"

        self._branches = self._get_branches()



    @staticmethod
    def _guess_io_type(
        call: CallsNode
    ) -> IOConstructType:
        
        type_hints = list()
        if call.input_fd is not None:
            type_hints.append(call.input_fd.typ)
        if call.output_fd is not None:
            for fd in call.output_fd:
                type_hints.append(fd.typ)

        io_type = sorted(type_hints, reverse=True)[0] if len(type_hints) > 0 else IOConstructType.UNKNOWN
        return io_type



    @staticmethod
    def _guess_branch_io_type(
        indexes: List[NodeID],
        graph: nx.Graph
    ) -> IOConstructType:
       
        guesses = set()
        for idx in indexes:
            guesses.add(DeepGraphComparator._guess_io_type(graph.nodes[idx]["call"]))

        io_type = sorted(guesses, reverse=True)[0] if len(guesses) > 0 else IOConstructType.UNKNOWN

        return io_type



    @staticmethod
    def _get_subgraphs(
        children: Iterable[NodeID],
        graph:nx.Graph
    ) -> Dict[IOConstructType, Dict[BranchID, nx.Graph]]:
        
        counter = 0
        res = dict()
        for child in children:
            indexes = DeepGraphComparator._traverse(child, graph)
            io_type = DeepGraphComparator._guess_branch_io_type(indexes, graph)
            if res.get(io_type, None) is None:
                res[io_type] = dict()
            res[io_type][counter] = graph.subgraph(indexes)
            counter += 1
        return res



    @staticmethod
    def _traverse(
        node: NodeID,
        graph: nx.Graph
    ) -> List[Union[int, str]]:
        
        res = [node]
        for successor in graph.neighbors(node):
            res.extend(DeepGraphComparator._traverse(successor, graph))
        return res



    def _get_branches(
        self
    ) -> Tuple[Dict[IOConstructType, Dict[BranchID, nx.Graph]]]:
       
        dirty_idx = "entry"
        trusted_idx = "entry"
        dirty_children = self._dirty_graph.neighbors(dirty_idx)
        trusted_children = self._trusted_graph.neighbors(trusted_idx)

        return self._get_subgraphs(dirty_children, self._dirty_graph), \
            self._get_subgraphs(trusted_children, self._trusted_graph)



    @staticmethod
    def _assign(
        distances: Dict[Tuple[BranchID, BranchID], float]
    ) -> List[Tuple[BranchID, BranchID]]:
        
        solver = pywraplp.Solver.CreateSolver('SCIP')

        assignments = dict((pair, solver.IntVar(0, 1, '')) for pair in distances.keys())

        branches_d = set(map(lambda x: x[0], distances.keys()))
        branches_t = set(map(lambda x: x[1], distances.keys()))

        for branch_d in branches_d:
            solver.Add(solver.Sum([assignments[(branch_d, branch_t)] for branch_t in branches_t]) <= 1)

        for branch_t in branches_t:
            solver.Add(solver.Sum([assignments[(branch_d, branch_t)] for branch_d in branches_d]) <= 1)

        objective = list()
        for pair in distances.keys():
            objective.append(distances[pair] * assignments[pair])

        solver.Maximize(solver.Sum(objective))
        status = solver.Solve() # status is 0, check what that means

        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            result = []
            for pair, state in assignments.items():
                if state.solution_value() > 0.5:
                    result.append(pair)
            return result
        else:
            raise AssignmentSolverException()



    @staticmethod
    def _assign_branch_sets(
        branches_d: Dict[BranchID, nx.Graph],
        branches_t: Dict[BranchID, nx.Graph]
    ) -> List[Tuple[BranchID, BranchID, float, List[NodeMatch]]]:
        
        costs = dict()
        differences = dict()
        for id_d, graph_d in branches_d.items():
            for id_t, graph_t in branches_t.items():
                costs[id_d, id_t], differences[id_d, id_t] = BranchComparator(graph_d, graph_t).compare()

        assignments = DeepGraphComparator._assign(costs)

        used = set(map(lambda a: a[0], assignments))
        for branch in branches_d:
            if branch not in used:
                assignments.append((branch, None))

        used = set(map(lambda a: a[1], assignments))
        for branch in branches_t:
            if branch not in used:
                assignments.append((None, branch))
        
        return [(
            a1,
            a2,
            costs.get((a1, a2), None),
            differences.get((a1, a2),
                            BranchComparator(
                                branches_d.get(a1, None),
                                branches_t.get(a2, None)
                            ).compare()[1])
            )
            for a1, a2 in assignments
        ]



    def _get_branch_assignments(
        self
    ) -> List[Tuple[BranchID, BranchID, float, List[NodeMatch]]]:
        
        dirty_branches, trusted_branches = self._get_branches()

        remainder_d = dict()
        remainder_t = dict()

        assignments = list()

        for iotype in trusted_branches:
            if iotype not in dirty_branches.keys():
                branches = trusted_branches[iotype]
                for branch_id, graph in branches.items():
                    remainder_t[branch_id] = graph 

        for iotype in dirty_branches:
            if iotype not in trusted_branches.keys():
                branches = dirty_branches[iotype]
                for branch_id, graph in branches.items():
                    remainder_d[branch_id] = graph
            else:
                set_assignments = self._assign_branch_sets(dirty_branches[iotype], trusted_branches[iotype])
                for assignment in set_assignments:
                    if assignment[0] is None:
                        remainder_t[assignment[1]] = trusted_branches[iotype][assignment[1]]
                    elif assignment[1] is None:
                        remainder_d[assignment[0]] = dirty_branches[iotype][assignment[0]]
                    else:
                        assignments.append(assignment)

        leftover_assignments = self._assign_branch_sets(remainder_d, remainder_t)
        for assignment in leftover_assignments:
            assignments.append(assignment)

        return assignments




    def compare(
        self
    ) -> Tuple[float, str]:

        assignments = self._get_branch_assignments()
        self._sum = sum(filter(lambda x: x is not None, map(lambda x: x[2], assignments)))
        #print(f"Using assignment with branch-similarity-score sum {self._sum}.")
        average = self._sum / len(assignments)
        graph = DiffGraph(self._dirty_graph, self._trusted_graph, assignments).compute()
        graph.serialize(self._outpath)

        return average, self._outpath




