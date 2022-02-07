import networkx as nx
import time

from themis.common.config import Config
from themis.comparing.ged_match import compute_ged, compare_all

def compare(config: Config) -> None:

    compute_ged(config)
    #compare_all(config)

"""
    for subject in reconstruct_all(config):
        start = time.perf_counter_ns()
        ged = compute_ged(graph, subject)
        end = time.perf_counter_ns()

        print(f"Ged of graphs is {ged} ....... took {end-start} ns")
"""   
