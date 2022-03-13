import networkx as nx
import gmatch4py as gm
import os

from vptree import VPTree
from abc import ABC, abstractmethod, abstractstaticmethod, abstractclassmethod
from typing import  Generic, TypeVar, List, Optional

from themis.common.config import Config
from themis.transforming.transform import reconstruct_all_gexf, reconstruct_one_gexf


Path = str
Data = TypeVar('Data', Path, gm.graph.Graph)




class Comparator(ABC, Generic[Data]):
        
    @abstractmethod
    def distance(self, item1: Data, item2: Data) -> int:
        pass




class NormalizedGraphComparator(Comparator[gm.graph.Graph]):
    
    def distance(self, item1: gm.graph.Graph, item2: gm.graph.Graph) -> float:
        ged_compute = gm.GraphEditDistance(1,1,1,1)
        res1 = ged_compute.distance_ged(item1, item2)
        res2 = ged_compute.distance_ged(item2, item1)
        if res2 == 0.0:
            return 0.0
        #print(abs(1 - res1/res2))
        return abs(1 - res1/res2)




class RawGraphComparator(Comparator[gm.graph.Graph]):
    
    def distance(self, item1: gm.graph.Graph, item2: gm.graph.Graph) -> float:
        ged_compute = gm.GraphEditDistance(1, 1, 1, 1)
        ged_compute.set_attr_graph_used("func", "")
        res1 = ged_compute.distance_ged(item1, item2)
        #print(res1)
        return res1




class HaussdorfGraphComparator(Comparator[gm.graph.Graph]):
    
    def distance(self, item1: gm.graph.Graph, item2: gm.graph.Graph) -> float:
        ged_compute = gm.HED(1,1,1,1)
        res1 = ged_compute.compare([item1, item2], None)
        #print(res1)
        return res1




class ExperimentalGraphComparator(Comparator[gm.graph.Graph]):
    
    def distance(self, item1: gm.graph.Graph, item2: gm.graph.Graph) -> float:
        ged_compute = gm.GraphEditDistance(1,1,1,1)
        res1 = ged_compute.distance_ged(item1, item2)
        res2 = ged_compute.distance_ged(item2, item1)
        #print(abs(res1-res2))
        return abs(res1-res2)




class TrialGraphComparator(Comparator[gm.graph.Graph]):

    def distance(self, item1: gm.graph.Graph, item2: gm.graph.Graph) -> float:
        ged_compute = gm.GraphEditDistance(1,1,1,1)
        res = ged_compute.compare([item1, item2], None)
        print("Result\n", res)
        print("Similarity\n", ged_compute.similarity(res))
        print("Distance\n", ged_compute.distance(res))

        return 0.0




class FileComparator(Comparator[Path]):
    def __init__(self, internal: Comparator) -> None:
        self._internal = internal



    def distance(self, item1: Path, item2: Path) -> int:
        graph1 = reconstruct_one_gexf(item1)
        graph2 = reconstruct_one_gexf(item2)
        pygraphs = gm.helpers.general.parsenx2graph([graph1, graph2])
        #print(item1, item2)

        #return self._internal.distance(graph1, graph2)
        return self._internal.distance(pygraphs[0], pygraphs[1])




class VPTreeWrapper(ABC, Generic[Data]):
    def __init__(self, config: Config, comparator: Comparator[Data]):
        self._config = config
        datapoints = self.get_datapoints()
        self._tree = VPTree(datapoints, comparator.distance)



    @abstractmethod
    def get_datapoints(self) -> List[Data]:
        pass



    def query_k_nearest(self, item: Data, k: int):
        return self._tree.get_n_nearest_neighbors(item, k)




class IOIntensiveVPTreeWrapper(VPTreeWrapper[Path]):
    def __init__(self, config):
        super().__init__(config, FileComparator(RawGraphComparator()))



    def get_datapoints(self) -> List[Path]:  
        with os.scandir(self._config.trusted_graph_dir) as graph_db:
            files = filter(lambda entry: entry.is_file() and entry.name.endswith(".gexf"), graph_db)
            return list(map(lambda entry: f"{self._config.trusted_graph_dir}/{entry.name}", files))




class InMemoryVPTreeWrapper(VPTreeWrapper[gm.graph.Graph]):
    def __init__(self, config: Config):
        super().__init__(config, RawGraphComparator())



    def get_datapoints(self) -> List[nx.Graph]:
        return reconstruct_all_gexf(self._config)
