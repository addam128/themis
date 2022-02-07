import networkx as nx
import gmatch4py as gm
import time

from themis.common.config import Config
from themis.transforming.transform import reconstruct_one_gexf, reconstruct_all_gexf


def compute_ged(config: Config):
    graph1 = reconstruct_one_gexf(f"{config.graph_dir}/{config.executable}.gexf")
    graph2 = reconstruct_one_gexf(f"{config.graph_dir}/{config.compareto}.gexf")
    compute_for_pair(graph1, graph2)

def compute_for_pair(graph1: nx.DiGraph, graph2: nx.DiGraph):
    start = time.perf_counter_ns()
    ged_compute = gm.GraphEditDistance(1,1,1,1)
    res_matrix = ged_compute.compare([graph1, graph2], [0, 1])
    end = time.perf_counter_ns()
    print(f"result is is\n {res_matrix},\n took {end-start} ns.")
    print(f"Similarity is\n {ged_compute.similarity(res_matrix)},\n took {end-start} ns.")
    print(f"Distance is is\n {ged_compute.distance(res_matrix)},\n took {end-start} ns.")

def compare_all(config: Config):

    graphs = list(reconstruct_all_gexf(config))

    start = time.perf_counter_ns()
    ged_compute = gm.GraphEditDistance(1,1,1,1)
    res_matrix = ged_compute.compare(graphs, None)
    end = time.perf_counter_ns()
    print(f"result is is\n {res_matrix},\n took {end-start} ns.")
    print(f"Similarity is\n {ged_compute.similarity(res_matrix)},\n took {end-start} ns.")
    print(f"Distance is is\n {ged_compute.distance(res_matrix)},\n took {end-start} ns.")