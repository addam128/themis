import networkx as nx
import time

from themis.common.config import Config
from themis.comparing.ged import compute_ged
from themis.transforming.transform import reconstruct_all

def compare(config: Config, graph: nx.DiGraph) -> None:

    for subject in reconstruct_all(config):
        start = time.perf_counter_ns()
        ged = compute_ged(graph, subject)
        end = time.perf_counter_ns()

        print(f"Ged of graphs is {ged} ....... took {end-start} ns")
        
