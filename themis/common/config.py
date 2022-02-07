from dataclasses import dataclass, field
from serde import serialize, deserialize
from typing import List

@serialize
@deserialize
@dataclass
class Config:
    lib_dir: str
    bin_dir: str
    data_dir: str
    graph_dir: str
    traced_libcalls_file: str
    executable: str
    args: List[str]
    compareto: str
