import networkx as nx
import matplotlib.pyplot as plt

from typing import List

from themis.transforming.parser import CallParser
from themis.transforming.grapher import Grapher, EdgeType
from themis.common.config import Config


def transform(config: Config) -> nx.Graph:
    
    with open(f"{config.data_dir}/libcalls_{config.executable}_filtered.txt", "r") as callfile:
        
        parser = CallParser(callfile)
        grapher = Grapher(parser)
        graph, labels = grapher.into_graph()
        persist(config, graph)

        return graph

def reconstruct(config: Config):
    graph = nx.nx_pydot.read_dot(path=f"{config.data_dir}/{config.executable}_graph.dot")
    return graph


def to_img(config: Config, graph: nx.Graph):
    labels = dict()
    for node in graph.nodes(data="call"):
        labels[node[0]] = node[1].call.func
    edge_colors = []
    for edge in graph.edges(data="type"):
        edge_colors.append("grey" if edge[2] == EdgeType.TIME else "green" if edge[2] == EdgeType.FOLLOW else "orange")

    nx.draw_kamada_kawai(graph, labels=labels, node_size=50, edge_color=edge_colors)
    plt.savefig(f"{config.data_dir}/{config.executable}_plt.png")


def persist(config: Config, graph: nx.Graph) -> None:
    
    nx.nx_pydot.write_dot(graph, path=f"{config.data_dir}/{config.executable}_graph.dot")
