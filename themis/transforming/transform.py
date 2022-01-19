import networkx as nx
import matplotlib.pyplot as plt
import os 

from typing import Generator, List, Any

from themis.transforming.parser import CallParser
from themis.transforming.grapher import Grapher, EdgeType
from themis.common.config import Config


def transform(config: Config) -> nx.Graph:
    
    with open(f"{config.data_dir}/libcalls_{config.executable}_filtered.txt", "r") as callfile:
        
        parser = CallParser(callfile)
        grapher = Grapher(parser)
        graph = grapher.into_graph()
        persist(config, graph)
        to_gexf(config, graph)

        return graph


def reconstruct_from_conf(config: Config) -> nx.DiGraph:
    return reconstruct_one(path=f"{config.graph_dir}/{config.executable}_graph.pickle")

def reconstruct_one(path: str) -> nx.DiGraph:
    graph = nx.read_gpickle(path=path)
    return graph

def reconstruct_all(config: Config) -> Generator[nx.DiGraph, Any, Any]:
    with os.scandir(config.graph_dir) as graph_db:
        for pfile in filter(lambda entry: entry.is_file() and entry.name.endswith(".pickle"), graph_db):
            yield reconstruct_one(pfile.path)


def to_img(config: Config, graph: nx.Graph):
    labels = dict()
    for node in graph.nodes(data="call"):
        labels[node[0]] = node[1].call.func.funcname
    edge_colors = []
    for edge in graph.edges(data="type"):
        edge_colors.append("grey" if edge[2] == EdgeType.TIME else "green" if edge[2] == EdgeType.FOLLOW else "orange")

    nx.draw_kamada_kawai(graph, labels=labels, node_size=50, edge_color=edge_colors)
    plt.savefig(f"{config.data_dir}/{config.executable}_plt.png")


def persist(config: Config, graph: nx.Graph) -> None:
    nx.write_gpickle(graph, path=f"{config.graph_dir}/{config.executable}_graph.pickle")


def to_gexf(config: Config, graph: nx.Graph):
    from themis.transforming.gexf import write_gexf
    write_gexf(graph, path=f"{config.graph_dir}/{config.executable}.gexf")
