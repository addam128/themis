from typing import NamedTuple, Optional, List, Any, Dict, Tuple
from enum import Enum, auto, IntFlag
from dataclasses import dataclass, field

from themis.common.errors import InvalidUseException

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
    "wprintf",
    "fprintf",
    "fwprintf",
    "fscanf",
    "fwscanf",
    "putc",
    "putwc",
    "putc_unlocked",
    "putwc_unlocked",
    "putchar",
    "putwchar",
    "putchar_unlocked",
    "putwchar_unlocked",
    "getc",
    "getwc",
    "getc_unlocked",
    "getwc_unlocked",
    "getw"
]

STDSTREAM_MANIPULATORS = [
    "puts",
    "putw",
    "getchar",
    "getwchar",
    "getchar_unlocked",
    "getwchar_unlocked",
    "gets",
    "printf",
    "wprintf"
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
    "madvise",
    "sprintf",
    "swprintf",
    "snprintf",
    "sscanf",
    "swscanf",
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
    BINFILE = 2
    STDSTREAM = 3
    STREAM = 4
    MEMORY = 5
    DIRECTORY = 6
    LINK = 7
    TMP = 8
    PIPE = 9
    FIFO = 10
    SOCKET = 11




class NodeCounter:
    oid = 1

    @classmethod
    def next(cls) -> int:
        res = cls.oid
        cls.oid += 1
        return res




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
    TWEAK = auto()
    NONE = auto()




@dataclass
class Function:
    funcname: str
    effect: IODescFunc




class FunctionComparisonResult(Enum):
    EQUAL = auto()
    EQUIV_CLASS = auto()
    DIFFERENT = auto()




class FunctionComparator:
    equivalence_classes = [
        ["read", "readv"],
        ["write", "writev"],
        ["pwrite", "pwritev", "pwritev2"],
        ["pread", "preadv", "preadv2"],
        ["fputc", "fputwc", "fputc_unlocked", "fputwc_unlocked", "putc", "putwc", "putc_unlocked", "putwc_unlocked"],
        ["putchar", "putwchar", "putchar_unlocked", "putwchar_unlocked"],
        ["puts", "putw"],
        ["fgetc", "fgetwc", "fgetc_unlocked", "fgetwc_unlocked", "getc", "getwc", "getw", "getc_unlocked", "getwc_unlocked"],
        ["getchar", "getwchar", "getchar_unlocked", "getwchar_unlocked"],
        ["fgets", "fgetws", "fgets_unlocked", "fgetws_unlocked"],
        ["fputs", "fputws"],
        ["printf", "wprintf"],
        ["sprintf", "swsprintf", "snprintf"],
        ["scanf", "wscanf"],
        ["fprintf", "fwprintf"],
        ["fscanf", "fwscanf"],
        ["swscanf", "sscanf"],
        ["chdir", "fchdir"],
        ["opendir", "fdopendir"],
        ["scandir", "scandirat"],
        ["link", "linkat"],
        ["tmpnam", "tmpnam_r", "tempnam"],
        ["mktemp", "mkstemp", "mkostemp"],
        ["mkstemps", "mkostemps"],
        ["send", "sendto", "sendmsg"],
        ["recv", "recvfrom"]
    ]



    @classmethod
    def compare(cls, fname1: str, fname2: str) -> FunctionComparisonResult:
        if fname1 == fname2:
            return FunctionComparisonResult.EQUAL
        for ec in cls.equivalence_classes:
            if fname1 in ec:
                if fname2 in ec:
                    return FunctionComparisonResult.EQUIV_CLASS
        return FunctionComparisonResult.DIFFERENT
    



class ArgStatus(Enum):
    MISSING = auto()
    EXCESSIVE = auto()
    VALUE_MISMATCH = auto()
    MATCHING = auto()




class ArgsComparator:
    args_to_exclude = [
        "buf",
        "iov",
        "optval",
        "ptr",
        "stream",
        "lineptr",
        "n",
        "retval",
        "dest_addr",
        "n",
        "fd" 
    ]



    @classmethod
    def compare(cls, args1: Dict[str, Any], args2: Dict[str, Any]) -> Tuple[int, Dict[str, Tuple[ArgStatus, Any, Any]]]:
        penalty = 0
        args1_filtered = dict((key, val) for key, val in args1.items() if key not in cls.args_to_exclude)
        args2_filtered = dict((key, val) for key, val in args2.items() if key not in cls.args_to_exclude)
        differences = dict()

        for key, val in args1_filtered.items():
            if key not in args2_filtered.keys():
                differences[key] = (ArgStatus.EXCESSIVE, val, None)
                penalty += 4
            else:
                if (val2 := args2_filtered[key]) == val:
                    differences[key] = (ArgStatus.MATCHING, val, None)
                else:
                    differences[key] = (ArgStatus.VALUE_MISMATCH, val, val2)
                    penalty += 2
        
        for key, val in args2_filtered.items():
            if key not in args1_filtered.keys():
                differences[key] = (ArgStatus.MISSING, None, val)
                penalty += 4

        return penalty, differences




@dataclass
class DiffInfo:
    func_diff: Tuple[Optional[str], Optional[str], FunctionComparisonResult]
    idx_diff: Tuple[int, int] 
    args_diff: Dict[str, Tuple[ArgStatus, Any, Any]]




@dataclass
class IOCall:
    index: int = field(default=-1)  # order in input file
    func: Function = field(default=Function("nop", IODescFunc.NONE))
    in_fd: Optional[IODesc] = field(default=None)
    out_fd: Optional[List[IODesc]] = field(default=None)
    args: Dict[str, Any] = field(default_factory=dict)



    @staticmethod
    def compare(call1: Optional['IOCall'], call2: Optional['IOCall']) -> Tuple[int, DiffInfo]:

        if call1 is None and call2 is None:
            raise InvalidUseException("IOCall comparison with both args being None.")

        if call2 is None:
            _, args_diff = ArgsComparator.compare(call1.args, dict())
            return 0, DiffInfo(
                func_diff=(call1.func.funcname, None, FunctionComparisonResult.DIFFERENT),
                idx_diff=(call1.index, -1),
                args_diff=args_diff
            )

        if call1 is None:
            _, args_diff = ArgsComparator.compare(dict(), call2.args)
            return 0, DiffInfo(
                func_diff=(None, call2.func.funcname, FunctionComparisonResult.DIFFERENT),
                idx_diff=(-1, call2.index),
                args_diff=args_diff
            )

        res = 100

        # func
        func_match = FunctionComparator.compare(call1.func.funcname, call2.func.funcname)
        if func_match == FunctionComparisonResult.EQUIV_CLASS:
            res -= 15
        elif func_match == FunctionComparisonResult.DIFFERENT:
            res -= 55
        # EQUAL doesn't change the result

        # index
        res -= (1 if call1.index != call2.index else 0)
        res -= (abs(call1.index - call2.index) // 3) * 3

        # args
        penalty, arg_diffs = ArgsComparator.compare(call1.args, call2.args)
        res -= penalty

        return res, DiffInfo(
            func_diff=(call1.func.funcname, call2.func.funcname, func_match),
            idx_diff=(call1.index, call2.index),
            args_diff= arg_diffs
        )




@dataclass
class CallsNode:
    id: int = field(init=False, default_factory=NodeCounter.next)
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
