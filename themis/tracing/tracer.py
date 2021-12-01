from os import system

from themis.common.config import Config
from themis.tracing.frida_trace_wrap import Analyzer
from themis.tracing.filter import filter_file


def trace(config: Config):
    Analyzer(
        config
    ).extract_libcalls()

    filter_file(
        f"{config.data_dir}/libcalls_{config.executable}.txt",
        f"{config.data_dir}/libcalls_{config.executable}_filtered.txt"
    )

    system(f"rm {config.data_dir}/libcalls_{config.executable}.txt")