from typing import NamedTuple, Optional, List, Any, Dict
from enum import Enum, auto, IntFlag
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

STREAM_MANIPULATORS = [
    "fopen",
    "freopen",
    "fclose",
    "fcloseall",
    "fputc",
    "fputwc",
    "fputc_unlocked",
    "fputwc_unlocked",
    "fputs",
    "fputws",
    "fputs_unlocked",
    "fputws_unlocked",
    "fgetc",
    "fgetwc",
    "fgetc_unlocked",
    "fgetwc_unlocked",
    "getline",
    "getdelim",
    "fgets",
    "fgetws",
    "fgets_unlocked",
    "fgetws_unlocked",
    "fread",
    "fread_unlocked",
    "fwrite",
    "fwrite_unlocked",
    "printf",
    "wprintf",
    "fprintf",
    "fwprintf",
    "sprintf",
    "swprintf",
    "snprintf",
    "fscanf",
    "fwscanf",
    "sscanf",
    "swscanf"
]

BINFILE_MANIPULATORS = [
    "open",
    "creat",
    "close",
    "close_range",
    "closefrom",
    "read",
    "pread",
    "write",
    "pwrite",
    "readv",
    "writev",
    "preadv",
    "pwritev",
    "preadv2",
    "pwritev2",
    "copy_file_range",
    "remove",
    "rename"
]

MEMORY_MANIPULATORS = [
    "mmap",
    "munmap",
    "msync",
    "mremap",
    "madvise"
]

DIRECTORY_MANIPULATORS = [
    "getcwd",
    "chdir",
    "fchdir",
    "opendir",
    "fdopendir",
    "dirfd",
    "readdir",
    "readdir_r",
    "closedir",
    "scandir",
    "rmdir",
    "mkdir"
]

LINK_MANIPULATORS = [
    "link",
    "linkat",
    "symlink",
    "readlink",
    "realpath"
]

TMP_MANIPULATORS = [
    "tmpfile",
    "tmpnam",
    "tmpnam_r",
    "tempnam",
    "mktemp",
    "mkstemp",
    "mkdtemp"
]

SOCKET_MANIPULATORS = [
    "socket",
    "shutdown",
    "socketpair",
    "connect",
    "listen",
    "accept",
    "send",
    "recv",
    "sendto",
    "recvfrom",
    "getsockopt",
    "setsockopt",
    "bind"
]

PIPE_MANIPULATORS = [
    "pipe",
    "popen",
    "pclose",
]

FIFIO_MANIPULATORS = [
    "mkfifo",
    "mkfifoat"
]

class IOConstructType(IntFlag):
    UNKNOWN = 0
    INVALID = 1
    STDIN = 2
    STDOUT = 3
    STDERR = 4
    BINFILE = 5
    STREAM = 6
    MEMORY = 7
    DIRECTORY = 8
    LINK = 9
    TMP = 10
    PIPE = 11
    FIFO = 12
    SOCKET = 13


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
    UNKNOWN = auto()  #  for inherited fds, when we dont know their state for sure


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
