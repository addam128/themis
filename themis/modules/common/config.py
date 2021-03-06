from dataclasses import dataclass, field
from serde import serialize, deserialize
from typing import List, Optional


@serialize
@deserialize
@dataclass
class Config:
    lib_dir: str
    bin_dir: str
    trace_dir: str
    trusted_graph_dir: str
    dirty_graph_dir: str
    result_dir: str
    img_dir: str
    sample_dir: str
    traced_libcalls_file: str
    executable: Optional[str]
    args: List[str]
    trust: bool = field(default=False)
