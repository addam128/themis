import re

from typing import Generator, Optional, List, Any, Tuple, Union, Dict
from dataclasses import dataclass, field
from uuid import uuid4, UUID

from themis.transforming.calls import STDSTREAM_MANIPULATORS, CallsNode, IODescAndState, IOConstructType,\
     IODesc, IODescFunc, IODescState, CallsNodeAndFunc, IOCall, GraphFunc, Function
from themis.transforming.calls import CLOSERS, BINFILE_MANIPULATORS, MEMORY_MANIPULATORS,\
     STREAM_MANIPULATORS, SOCKET_MANIPULATORS, PIPE_MANIPULATORS, FIFIO_MANIPULATORS,\
          TMP_MANIPULATORS, LINK_MANIPULATORS, DIRECTORY_MANIPULATORS

CALL_REGEX = re.compile(r"(?P<offset>[\|\s]+)(?P<func>\w+)(?P<callpoint>::exit<\d{1,6}>|::enter<\d{1,6}>)?\((?P<args>[\w\s,+\d=/\"\.\%\:\_]+)\)")
CALLPOINT_REGEX = re.compile(r"::(?P<type>\w+)<(?P<id>\d+)>")


class CallParser:
    def __init__(self, infile):
        self._lines = infile
        self.call_index = 0
        self._edges: List[Tuple[str, str]] = list()
        self._last_of_level: Dict[int, str] = dict()  # int is offset
        self._open_iocall: Dict[int, CallsNode] = dict()  # int is identifier from frida
        self._open_iocall_stack = list()
        self._available_internal_fds = dict()
        self._iodesc: Dict[int, IODescAndState] = dict()

        self._iodesc[0x00] = IODescAndState(
            IODesc(typ=IOConstructType.STDIN, fd=0x00, desc="standard input, inherited"),
            IODescState.UNKNOWN
        )
        self._iodesc[0x01] = IODescAndState(
            IODesc(typ=IOConstructType.STDOUT, fd=0x01, desc="standard output, inherited"),
            IODescState.UNKNOWN
        )
        self._iodesc[0x02] = IODescAndState(
            IODesc(typ=IOConstructType.STDERR, fd=0x02, desc="standard error, inherited"),
            IODescState.UNKNOWN
        )

    def parse(self) -> Generator[CallsNodeAndFunc, Any, Any]:
        previous_offset = 2

        while True:
            line = self._next()
            if line is not None:
                offset, node = self._node_from_line(line)
                if offset > previous_offset:
                    self._edges.append((self._last_of_level[previous_offset], extract_uuid(node)))
                if isinstance(node, CallsNode) and  offset > 2 and node.func.funcname == "open":
                    self._available_internal_fds[self._open_iocall_stack[-1]] = node.output_fd[0]         

                previous_offset = offset
                self._last_of_level[offset] = extract_uuid(node)

                if isinstance(node, CallsNode):
                    func = self._postprocess_node(node)
                    yield CallsNodeAndFunc(call=node, func=func)
            else:
                return

    def nesting_edges(self) -> List[Tuple[str, str]]:
        return self._edges

    def _node_from_line(self, line: str) -> Optional[Tuple[int, Union[CallsNode, UUID]]]:  # int is offset

        mat = CALL_REGEX.match(line)

        if mat is None:
            print(f"could not match line {line}")
            return None

        func = mat.group("func")
        index = self.call_index
        self.call_index += 1
        args = mat.group("args")
        callpoint = mat.group("callpoint")
        offset = mat.group("offset")

        return offset.count('|'), self._create_node(func, index, args, callpoint)

    def _create_node(self, func: str, index: int, args: str, callpoint: Optional[str]) -> Union[CallsNode, UUID]:

        arg_dict = self._parse_args(args)
        in_fd = self._get_in_fd(arg_dict, func)
        out_fd = self._get_out_fd(arg_dict, func)

        func_obj = self._create_function(func)

        if callpoint is None:
            return CallsNode(call=IOCall(index, func_obj, in_fd, out_fd, arg_dict))

        mat = CALLPOINT_REGEX.match(callpoint)
        c_type = mat.group("type")
        c_id = mat.group("id")

        if c_type == "enter":
            call = CallsNode(call=IOCall(index, func_obj, in_fd, out_fd, arg_dict))
            self._open_iocall[int(c_id)] = call
            self._open_iocall_stack.append(call.id)
            return call.id
        if c_type == "exit":
            call = self._open_iocall.pop(int(c_id))
            self._open_iocall_stack.remove(call.id)
            call.call.out_fd = out_fd
            call.index = index

            if call.func.funcname == "fopen" and call.output_fd is not None:
                call.output_fd[0].internal = self._available_internal_fds.get(call.id, None)

            return call

    def _parse_args(self, args: str) -> Dict[str, Any]:
        arg_dict = dict()
        for name, value in map(lambda x: tuple(x.split("=")), args.split(", ")):
            arg_dict[name] = value
        return arg_dict

    def _get_in_fd(self, args: Dict[str, Any], func: str) -> Optional[IODesc]:
        key = None
        value = None
        for key, value in args.items():
            if key in ["fd", "sockfd", "stream", "oldfd"]:

                if value is None:
                    print(f"Function {func} takes no file descriptor")
                    return None
                same_fd = self._iodesc.get(int(value, base=16), None)
                if same_fd is None:
                    print(f"input fd {value} was never created")
                    return IODesc(typ=IOConstructType.UNKNOWN, fd=int(value, base=16))
                if same_fd.state == IODescState.CLOSED:
                    print(f"{func} using closed fd {value}")
                if same_fd.state == IODescState.FORGOTTEN:
                    print(f"{func} using forgotten fd {value}")

                return same_fd.iodesc
        return None

    def _get_out_fd(self, args: Dict[str, Any], func: str) -> Optional[List[IODesc]]:
        key = None
        value = None
        new_iodesc = []
        for key, value in args.items():
            if key in ["newfd", "retval"]:
                if value is None:
                    print(f"Function {func} gives no file descriptor")
                    continue
                if func == "fopen" and int(value, base=16) == 0x00:
                    print(f"fopen returned null")
                    continue
                same_fd = self._iodesc.get(int(value, base=16), None)
                if same_fd is not None and same_fd.state == IODescState.OPEN:
                    print(f"function {func} returned already open fd {value}")
                if same_fd is not None and same_fd.state == IODescState.FORGOTTEN:
                    print(f"function {func} returned forgotten fd {value}")

                new_iodesc.append(IODesc(typ=IOConstructType.UNKNOWN, fd=int(value, base=16)))

        for iodesc in new_iodesc:
            self._iodesc[int(value, base=16)] = IODescAndState(iodesc=iodesc, state=IODescState.OPEN)

        return new_iodesc if len(new_iodesc) > 0 else None

    def _next(self) -> Optional[str]:
        try:
            return next(self._lines)
        except StopIteration:
            None

    def _postprocess_node(self, node: CallsNode) -> GraphFunc:
        ret_func = None
        if node.func.funcname in CLOSERS:
            if node.input_fd.fd is not None:
                handle = self._iodesc.get(node.input_fd.fd)
                if handle is not None:
                    handle.state = IODescState.CLOSED
                ret_func = GraphFunc.RESET_FD


        if node.func.funcname == "fclose":
            if node.input_fd.internal is not None:
                self._iodesc[node.input_fd.internal.fd].state = IODescState.FORGOTTEN
            
        elif node.func.funcname == "fcloseall":
            ret_func = GraphFunc.RESET_STREAMS
            # TODO: changeall streams to closed + internals

        elif node.func.funcname == "dup" or node.func.funcname == "dup2":
            for fd in node.output_fd:
                fd.typ = node.input_fd.typ 

        else:
            # guess fd type by function
            # prefer more precise (like tmp over stream)
            # anything over binary file
            
            # IN FD
            if node.input_fd is not None:
                new_guess = guess_io_type(node.input_fd.typ, node.func)
                node.input_fd.typ = new_guess

            # OUT FD
            if node.output_fd is not None:
                for fd in node.output_fd:
                    new_guess = guess_io_type(fd.typ, node.func)
                    fd.typ = new_guess


        return ret_func

    def _create_function(self, func: str):
        return Function(funcname=func, effect=IODescFunc.NONE) # TODO: proper effect


def extract_uuid(node: Union[UUID, CallsNode]) -> str:
    if isinstance(node, CallsNode):
        return str(node.id)
    return str(node)

def guess_io_type(old_guess: IOConstructType, func: Function):
    new_guess = IOConstructType.UNKNOWN

    if func.funcname in SOCKET_MANIPULATORS:
        new_guess =  IOConstructType.SOCKET
    elif func.funcname in MEMORY_MANIPULATORS:
        new_guess = IOConstructType.MEMORY
    elif func.funcname in DIRECTORY_MANIPULATORS:
        new_guess = IOConstructType.DIRECTORY
    elif func.funcname in LINK_MANIPULATORS:
        new_guess = IOConstructType.LINK
    elif func.funcname in TMP_MANIPULATORS:
        new_guess = IOConstructType.TMP
    elif func.funcname in PIPE_MANIPULATORS:
        new_guess = IOConstructType.PIPE
    elif func.funcname in FIFIO_MANIPULATORS:
        new_guess = IOConstructType.FIFO
    elif func.funcname in STREAM_MANIPULATORS:
        new_guess = IOConstructType.STREAM
    elif func.funcname in STDSTREAM_MANIPULATORS:
        new_guess = IOConstructType.STDSTREAM
    elif func.funcname in BINFILE_MANIPULATORS:
        new_guess = IOConstructType.BINFILE

    return new_guess if new_guess > old_guess else old_guess

    
