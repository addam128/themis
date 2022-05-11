


from pyparsing import with_class
from serde.toml import from_toml
from themis.modules.common.config import Config
from themis.modules.comparing.graph_comparator import DeepGraphComparator
from themis.modules.searching.indexing import FileComparator, RawGraphComparator
from itertools import combinations, permutations, product

import pandas


def ged_compare():
    conf_path = "./themis/config.toml"
    with open(conf_path, "r") as config_file:
        config = from_toml(Config, config_file.read())


    import os
    with open("./legit_ged.txt", "w") as ofile:
        with os.scandir(config.trusted_graph_dir) as graph_db:
            for item1, item2 in  product(
                            filter(
                                lambda entry: entry.is_file() and entry.name.endswith(".gexf"),
                                graph_db
                        ), repeat=2):

                #print(item1, item2)
                metric = FileComparator(RawGraphComparator()).distance(item1, item2)
                print(os.path.splitext(item1.name)[0], os.path.splitext(item2.name)[0], metric, sep=";")

                ofile.write(f"{os.path.splitext(item1.name)[0]};{os.path.splitext(item2.name)[0]};{metric}\n")


def compare():
    conf_path = "./themis/config.toml"
    with open(conf_path, "r") as config_file:
        config = from_toml(Config, config_file.read())


    import os
    with open("./legit_comparisons.txt", "w") as ofile:
        with os.scandir(config.trusted_graph_dir) as graph_db:
            for item1, item2 in  product(map(
                            lambda entry: os.path.splitext(entry.name)[0],
                            filter(
                                lambda entry: entry.is_file() and entry.name.endswith(".gexf"),
                                graph_db
                            )
                        ), repeat=2):

                #print(item1, item2)
                metric, _, _ = DeepGraphComparator(config, item1, item2).compare()
                print(item1, item2, metric, sep=";")

                ofile.write(f"{item1};{item2};{metric}\n")


versions = ["ssh-6.0","ssh-6.1","ssh-6.2","ssh-6.3","ssh-6.4","ssh-6.5","ssh-6.6p1","ssh-6.7p1","ssh-centos7","ssh-6.8","ssh-6.9","ssh-7.0","ssh-7.1p1","ssh-7.2p1","ssh-ubuntu16.04","ssh-7.2p2","ssh-7.3","ssh-7.4","ssh-7.5","ssh-7.6", "ssh_debian_stretch","ssh-ubuntu18.04","ssh-7.7","ssh-7.8","ssh_debian_buster", "ssh_debian_bullseye","ssh-7.9","ssh-8.0","ssh-8.1","ssh-8.2","ssh-8.3","ssh-8.4","ssh-8.5","ssh-8.6","ssh-8.7","ssh-8.8","ssh-8.9","ssh-9.0","ssh_debian_bookworm", "dbclient"]

def transform_and_show():
    values = dict()
    with open("./legit_comparison.txt", "r") as ofile:
        for line in ofile.readlines():
            lparts = line.split(";")
            values[(lparts[0], lparts[1])] = int(float(lparts[2].strip()))

        #for v in versions:
         #   values[(v, v)] = 100

    #print(values.keys())

    df = dict()
    for v in versions:
        df[v] = [values[(v, x)] for x in versions]


    rdf = pandas.DataFrame.from_dict(data=df, orient="index", columns=versions)

    print(rdf)
    with open("./version_comp.csv", "w") as csvfile:
        rdf.to_csv(csvfile)

    show(rdf)


def show(data: pandas.DataFrame):
    import seaborn
    import matplotlib.pyplot as plt
    seaborn.set_theme()
    plt.figure(figsize=(17,17))
    #hmap = seaborn.heatmap(data, xticklabels=True, yticklabels=True, cmap="RdYlGn", linewidths=.5)
    #grayscale
    hmap = seaborn.heatmap(data, xticklabels=True, yticklabels=True, cmap="gray", linewidths=.5)
    hmap.figure.savefig("./heatmap.png")
    
    plt.clf()
    plt.figure(figsize=(17,12))
    plt.xticks(rotation=90)
    plt.bar(versions, data["ssh-ubuntu16.04"])
    plt.savefig("./barplot-ubu16.png")


def transform_and_show_ged():
    values = dict()
    with open("./legit_ged.txt", "r") as ofile:
        for line in ofile.readlines():
            lparts = line.split(";")
            values[(lparts[0], lparts[1])] = int(float(lparts[2].strip()))

        #for v in versions:
         #   values[(v, v)] = 100

    #print(values.keys())

    df = dict()
    for v in versions:
        df[v] = [values[(v, x)] for x in versions]


    rdf = pandas.DataFrame.from_dict(data=df, orient="index", columns=versions)

    print(rdf)
    with open("./version_comp_ged.csv", "w") as csvfile:
        rdf.to_csv(csvfile)

    show_ged(rdf)

def show_ged(data: pandas.DataFrame):
    import seaborn
    import matplotlib.pyplot as plt
    seaborn.set_theme()
    plt.figure(figsize=(17,17))
    #hmap = seaborn.heatmap(data, xticklabels=True, yticklabels=True, cmap="RdYlGn_r", linewidths=.5)
    # greyscale
    hmap = seaborn.heatmap(data, xticklabels=True, yticklabels=True, cmap="gray_r", linewidths=.5)
    hmap.figure.savefig("./heatmap_ged.png")


def compare_all():
    conf_path = "./themis/config.toml"
    with open(conf_path, "r") as config_file:
        config = from_toml(Config, config_file.read())


    import os
    with open("./all_comparisons.txt", "w") as ofile:
        with os.scandir(config.dirty_graph_dir) as graph_db:
            for item1, item2 in  product(
                            filter(
                                lambda entry: entry.is_file() and entry.name.endswith(".gexf"),
                                graph_db
                        ), repeat=2):

                #print(item1, item2)
                metric = FileComparator(RawGraphComparator()).distance(item1, item2)
                #print(item1, item2, metric, sep=";")

                ofile.write(f"{os.path.splitext(item1.name)[0]};{os.path.splitext(item2.name)[0]};{metric}\n")





def visualize_mspace():
    import networkx as nx
    import matplotlib.pyplot as plt

    graph = nx.Graph()
    edge_colors = []
    with open("./all_comparisons.txt", "r") as datafile:
        for line in datafile.readlines():
            lparts = line.split(";")
            lparts[2] = 400 - int(float(lparts[2].strip()))
            graph.add_node(lparts[0])
            graph.add_node(lparts[1])
            graph.add_edge(lparts[0], lparts[1], len=lparts[2])
            edge_colors.append('white')


    pos = nx.spring_layout(graph, weight="len")
    nx.draw(graph, pos, with_labels=True, edge_color=edge_colors, node_size=30, font_size=8)
    plt.savefig("metric_space.png")




if __name__ == '__main__':
    #compare()
    #ged_compare()
    #transform_and_show()
    #transform_and_show_ged()
    #compare_all()
    #visualize_mspace()

    import random
    for v in versions:
        flip = random.randint(0, 100)
        if flip > 70:
            print(v)
    pass

# >>>

"""
ssh-6.1
ssh-6.3
ssh-6.7p1
ssh-6.8
ssh-6.9
ssh-7.4
ssh-7.6
ssh-ubuntu18.04
ssh_debian_buster
ssh-8.1
ssh-8.3
ssh-8.4
ssh-8.7
ssh-8.8
ssh_debian_bookworm
"""       
            