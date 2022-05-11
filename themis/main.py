import argparse

from serde.toml import from_toml

from themis.modules.common.config import Config


def get_argparser(

) -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser("themis")
    
    subparsers = parser.add_subparsers(title="actions")


    trace_parser = subparsers.add_parser(
        "trace",
        description="Trace binaries with the help of Frida (frida.re)"
    )
    trace_parser.add_argument(
        "executable",
        help="Name of executable. The path to its directory has to be set in the a config file."
    )
    trace_parser.add_argument(
        "--set-ptrace-scope-to-zero",
        action="store_true",
        default=False,
        help="You might need to set this for frida to work."
    )
    trace_parser.set_defaults(func=trace_entry)


    transform_parser = subparsers.add_parser(
        "transform",
        description="Transform frida-traces into graphs."
    )
    transform_parser.add_argument(
        "executable",
        help="Name of the executable, for which a trace file has already been created."
    )
    transform_parser.add_argument(
        "--img",
        default=False,
        help="Save graphs as png.",
        action="store_true"
    )
    transform_parser.add_argument(
        "--trusted",
        default=False,
        action="store_true",
        help="Indicate whether this binary is trusted"
    )
    transform_parser.add_argument(
        "--save",
        default=False,
        action="store_true",
        help="Indicate whether this graph should be saved\
            in pickle and gexf formats. If the flag trusted is also used,\
            it will populate the valid graphs used for comparison."
        )
    transform_parser.set_defaults(func=transform_entry)


    search_parser = subparsers.add_parser(
        "search",
        description="Search for most similar trusted binaries."
    )
    search_parser.add_argument(
        "executable",
        help="Name of the executable, for which a graph has been already created,\
            and closest neighbours should be find.")
    search_parser.add_argument(
        "-k",
        default='1',
        help="Number of neighbours to find. Default is 1.",
        choices=['1', '2', '3', '4', '5', '6', '7', '8']
    )
    search_parser.set_defaults(func=search_entry)


    list_action = subparsers.add_parser(
        "list",
        help="Show all accumulated trusted binaries."
    )
    list_action.set_defaults(func=list_entry)


    compare_action = subparsers.add_parser(
        "compare",
        description="Compare two graphs in a more fine-grained way, and\
            receive a combined graph with differences. Due to some heuristics \
            in this module, we suggest to run this module multiple times."
    )
    compare_action.add_argument(
        "unknown_exec",
        help="Name of the executable, for which a graph has been already created,\
            and is meant to be compared to a valid program."
    )
    compare_action.add_argument(
        "trusted_exec",
        help="Name of the executable, for which a graph has been already created,\
                the valid program to compare to."
    )
    compare_action.add_argument(
        "--img",
        default=False,
        help="Save difference graphs as png. This is just a really simplified visualization, further work is needed.",
        action="store_true"
    )
    compare_action.set_defaults(func=compare_entry)


    collect_action = subparsers.add_parser(
        "collect",
        description="Collect suspicious binary with all its dependencies"
    )
    collect_action.add_argument(
        "path",
        help="Path to suspicious binary."
    )
    collect_action.add_argument(
        "--zipname",
        required=True,
        type=str,
        help="Make ZipFile under this name."
    )
    collect_action.set_defaults(func=collect_entry)


    parser.add_argument(
        "--conf",
        type=str,
        default="./themis/config.toml",
        help="Set different config file.")
    
    return parser


def prefix():
    from colorama import Fore, Style
    print(Fore.CYAN, "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n", Style.RESET_ALL)

def suffix():
    from colorama import Fore, Style
    print(Fore.CYAN, "===============================================\n", Style.RESET_ALL)

def intermediate():
    from colorama import Fore, Style
    print(Fore.CYAN, "-----------------------------------------------", Style.RESET_ALL)




def trace_entry(
    config: Config,
    args
) -> None:
    
    import os
    from themis.modules.tracing.tracer import trace

    config.executable = args.executable

    if args.set_ptrace_scope_to_zero:
        print("Setting up kernel for tracing...")
        print("sudo sysctl kernel.yama.ptrace_scope=0")
        os.system("sudo sysctl kernel.yama.ptrace_scope=0")

    trace(config)



def transform_entry(
    config: Config,
    args
) -> None:

    from themis.modules.transforming.transform import transform, to_img

    config.executable = args.executable
    config.trust = args.trusted

    graph = transform(config, args.save)

    if args.img:
        to_img(config, graph)



def search_entry(
    config: Config,
    args
) -> None:
    
    import colorama
    from themis.modules.searching.indexing import IOIntensiveVPTreeWrapper
    from pathlib import Path
    from colorama import Fore, Style
    
    colorama.init()
    prefix()
    config.executable = args.executable

    index = IOIntensiveVPTreeWrapper(config)
    res = index.query_k_nearest(f"{config.dirty_graph_dir}/{config.executable}.gexf", int(args.k))
    print(Fore.GREEN, f'{"Distance": <32}', "Program name", Style.RESET_ALL)
    intermediate()
    for dist, file in res:
        print(Fore.BLUE, f"{dist: <32}", Path(file).name[:-5], Style.RESET_ALL)
        intermediate()

    suffix()


def list_entry(
    config: Config,
    args
) -> None:
    
    import os
    
    with os.scandir(config.trusted_graph_dir) as graph_db:
        for item in  map(
                        lambda entry: os.path.splitext(entry.name)[0],
                        filter(
                            lambda entry: entry.is_file() and entry.name.endswith(".gexf"),
                            graph_db
                        )
                    ):
            print(item)
            


def stats_entry(
    config: Config,
    args
) -> None:

    from themis.modules.searching.indexing import FileComparator, TrialGraphComparator

    FileComparator(TrialGraphComparator()).distance(
        f"{config.dirty_graph_dir}/{args.executable1}.gexf",
        f"{config.dirty_graph_dir}/{args.executable2}.gexf"
    )



def compare_entry(
    config: Config,
    args
) -> None:
    
    import colorama

    from themis.modules.comparing.graph_comparator import DeepGraphComparator
    from colorama import Fore, Style
    
    colorama.init()
    prefix()
    metric, ofile, graph = DeepGraphComparator(config, args.unknown_exec, args.trusted_exec).compare()
    color = None
    if metric >= 90:
        color = Fore.GREEN
    elif metric > 70:
        color = Fore.YELLOW
    else:
        color = Fore.RED

    print("Match Score: ", color, metric, Style.RESET_ALL)
    print("Difference graph is being serialized to: ", Fore.MAGENTA, ofile, Style.RESET_ALL)
    suffix()

    if args.img:
        graph.show(f"{config.result_dir}/img/{args.unknown_exec}_vs_{args.trusted_exec}.png")


def collect_entry(
    config: Config,
    args
) -> None:

    from themis.modules.collecting.collector import Collector

    Collector(config, args.path, args.zipname).collect().archive()



def main():

    parser = get_argparser() 
    args = parser.parse_args()

    conf_path = args.conf

    with open(conf_path, "r") as config_file:
        config = from_toml(Config, config_file.read())
 
    args.func(config, args)
        

        

if __name__ == '__main__':
    main()

