from typing import NamedTuple, Optional, List, Any, Dict
from enum import Enum, auto
from dataclasses import dataclass, field
from uuid import uuid4, UUID

CLOSERS = [
    "fclose",
    "fcloseall",
    "close",
    "close_range",
    "closefrom",
    "closedir",
    "pclose",
    "shutdown",
]


class IOConstructType(Enum):
    FILE = auto()
    SOCKET = auto()
    STREAM = auto()
    MEMORY = auto()
    PIPE = auto()
    FIFO = auto()
    STDIN = auto()
    STDOUT = auto()
    STDERR = auto()
    UNKNOWN = auto()
    INVALID = auto()


@dataclass
class IODesc:
    typ: IOConstructType = field(default=IOConstructType.INVALID)
    fd: Optional[int] = field(default=None)
    desc: Optional[str] = field(default=None)
    internal: Optional['IODesc'] = field(default=None)


class IODescFunc(Enum):
    OPEN = auto()
    USE = auto()
    CLOSE = auto()
    CHANGE = auto()
    NONE = auto()

@dataclass
class Function:
    funcname: str
    effect: IODescFunc


@dataclass
class IOCall:
    index: int = field(default=-1)  # order in input file
    func: Function = field(default=Function("nop", IODescFunc.NONE))
    in_fd: Optional[IODesc] = field(default=None)
    out_fd: Optional[List[IODesc]] = field(default=None)
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallsNode:
    id: UUID = field(default_factory=uuid4)
    call: IOCall = field(default=IOCall())

    @property
    def index(self) -> int:
        return self.call.index

    @index.setter
    def index(self, value: int) -> None:
        self.call.index = value

    @property
    def func(self) -> Function:
        return self.call.func

    @property
    def input_fd(self) -> Optional[IODesc]:
        return self.call.in_fd

    @property
    def output_fd(self) -> Optional[List[IODesc]]:
        return self.call.out_fd

    @property
    def args(self) -> Dict[str, Any]:
        return self.call.args


class IODescState(Enum):
    OPEN = auto()
    CLOSED = auto()
    FORGOTTEN = auto()  # internal fd for a stream, after stream is closed but close was not directly called


@dataclass
class IODescAndState:
    iodesc: IODesc
    state: IODescState


class GraphFunc(Enum):
    RESET_FD = auto()
    RESET_STREAMS = auto()
    NONE = auto()


class CallsNodeAndFunc(NamedTuple):
    call: CallsNode
    func: Optional[GraphFunc]
