from typing import Union, Optional, NamedTuple

from themis.modules.common.calls import DiffInfo




NodeID = Union[int, str]
BranchID = int




class NodeMatch(NamedTuple):
    d_node: Optional[NodeID]
    t_node: Optional[NodeID]
    score: float
    differences: Optional[DiffInfo]
