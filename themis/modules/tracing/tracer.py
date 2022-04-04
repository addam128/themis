from os import system

from themis.modules.common.config import Config
from themis.modules.tracing.frida_trace_wrap import Analyzer
from themis.modules.tracing.filter import filter_file


def trace(
    config: Config
) -> None:

    Analyzer(
        config
    ).extract_libcalls()

    filter_file(
        f"{config.trace_dir}/libcalls_{config.executable}.txt",
        f"{config.trace_dir}/libcalls_{config.executable}_filtered.txt"
    )

    system(f"rm {config.trace_dir}/libcalls_{config.executable}.txt")