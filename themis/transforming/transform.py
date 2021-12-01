import networkx as nx
import matplotlib.pyplot as plt

from themis.transforming.parser import CallParser
from themis.transforming.grapher import Grapher, EdgeType
from themis.common.config import Config


def transform(config: Config):
    
    with open(f"{config.data_dir}/libcalls_{config.executable}_filtered.txt", "r") as callfile:
        
        parser = CallParser(callfile)
        grapher = Grapher(parser)
        graph, labels = grapher.into_graph()
        edge_colors = []
        for edge in graph.edges(data="type"):
            edge_colors.append("grey" if edge[2] == EdgeType.TIME else "green" if edge[2] == EdgeType.FOLLOW else "orange")

        nx.draw_kamada_kawai(graph, labels=labels, node_size=50, edge_color=edge_colors)

        plt.show()
